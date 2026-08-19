from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.opd_router import (
    OPDTrainingConfig,
    RouterDecision,
    RouterState,
    SFTTrainingConfig,
    decision_to_json,
    deterministic_target_free_decision,
    load_router_prompt_jsonl,
    opd_rollout_loss,
    render_instruction_prompt,
    require_compatible_tokenizers,
    response_token_mask,
    reverse_kl_loss,
    router_states_from_expert_output,
    supervised_fine_tune_router,
    train_on_policy_distillation,
)


def valid_state() -> dict:
    return {
        "task_kind": "catalyst_ranking",
        "source_sample_count": 462,
        "target_candidate_count": 126,
        "source_validation_spearman": 0.86,
        "curve_available": True,
        "surface_available": False,
        "condition_observed_fraction": 0.75,
        "standard_predictive_std": 0.2,
        "mhar_predictive_std": 0.3,
        "normalized_expert_disagreement": 0.4,
        "standard_domain_share": 0.45,
        "composition_support": 0.8,
    }


class TinyTokenizer:
    """Small deterministic tokenizer supporting the pilot's HF-like surface."""

    def __init__(self, offset: int = 0) -> None:
        self.offset = offset
        self.bos_token_id = 1
        self.eos_token_id = 2
        self.pad_token_id = 0
        self.padding_side = "left"
        self.truncation_side = "left"
        self.vocab_size = 67

    def __len__(self) -> int:
        return self.vocab_size

    def _encode(self, text: str) -> list[int]:
        return [
            3 + ((ord(char) + self.offset) % (self.vocab_size - 3)) for char in text
        ]

    def __call__(
        self,
        text: str | list[str],
        *,
        add_special_tokens: bool = True,
        padding: bool = False,
        truncation: bool = False,
        max_length: int | None = None,
        return_tensors: str | None = None,
    ) -> dict:
        rows = [text] if isinstance(text, str) else text
        encoded = [self._encode(row) for row in rows]
        if add_special_tokens:
            encoded = [[self.bos_token_id, *row] for row in encoded]
        if truncation and max_length is not None:
            encoded = [row[-max_length:] for row in encoded]
        width = max(len(row) for row in encoded)
        if padding or len(encoded) > 1:
            encoded = [
                [self.pad_token_id] * (width - len(row)) + row for row in encoded
            ]
        masks = [[int(token != self.pad_token_id) for token in row] for row in encoded]
        if return_tensors == "pt":
            return {
                "input_ids": torch.tensor(encoded, dtype=torch.long),
                "attention_mask": torch.tensor(masks, dtype=torch.long),
            }
        result_ids: list[int] | list[list[int]] = encoded
        if isinstance(text, str):
            result_ids = encoded[0]
        return {"input_ids": result_ids, "attention_mask": masks}


class TinyChatTokenizer(TinyTokenizer):
    chat_template = "synthetic"

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
    ) -> str:
        self.last_template_args = (tokenize, add_generation_prompt)
        return f"<user>{messages[0]['content']}</user><assistant>"


class TinyCausalLM(nn.Module):
    def __init__(self, vocab_size: int, seed: int) -> None:
        super().__init__()
        generator = torch.Generator().manual_seed(seed)
        self.embedding = nn.Embedding(vocab_size, 12)
        self.projection = nn.Linear(12, vocab_size)
        with torch.no_grad():
            self.embedding.weight.copy_(
                torch.randn(self.embedding.weight.shape, generator=generator) * 0.1
            )
            self.projection.weight.copy_(
                torch.randn(self.projection.weight.shape, generator=generator) * 0.1
            )
            self.projection.bias.zero_()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ):
        del attention_mask
        logits = self.projection(self.embedding(input_ids))
        loss = None
        if labels is not None:
            loss = F.cross_entropy(
                logits[:, :-1].reshape(-1, logits.shape[-1]),
                labels[:, 1:].reshape(-1),
                ignore_index=-100,
            )
        return SimpleNamespace(logits=logits, loss=loss)

    def generate(
        self,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        do_sample: bool,
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_new_tokens: int,
        eos_token_id: int | None,
        pad_token_id: int | None,
    ) -> torch.Tensor:
        del attention_mask, top_p, eos_token_id, pad_token_id
        sequence = input_ids
        for _ in range(max_new_tokens):
            logits = self(sequence).logits[:, -1] / temperature
            if do_sample:
                token = torch.multinomial(F.softmax(logits, dim=-1), 1)
            else:
                token = logits.argmax(dim=-1, keepdim=True)
            sequence = torch.cat([sequence, token], dim=1)
        return sequence


F = torch.nn.functional


class RouterContractTests(unittest.TestCase):
    def test_state_rejects_any_extra_or_outcome_field(self) -> None:
        payload = valid_state()
        payload["target_outcome"] = 0.91
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            RouterState.from_mapping(payload)

    def test_prompt_is_canonical_and_contains_no_programme_shortcut(self) -> None:
        prompt = RouterState.from_mapping(valid_state()).to_prompt()
        self.assertIn("ROUTER_STATE=", prompt)
        self.assertNotIn("target_outcome", prompt)
        self.assertNotIn("specgen_C", prompt)

    def test_decision_parser_is_strict_and_fails_closed(self) -> None:
        valid = RouterDecision.from_text(
            json.dumps(
                {
                    "expert": "standard",
                    "action": "rank",
                    "confidence": 0.8,
                    "reason_codes": ["source_supported", "standard_closer"],
                }
            )
        )
        self.assertTrue(valid.valid)
        invalid = RouterDecision.from_text(
            "Decision: "
            + json.dumps(
                {
                    "expert": "mhar",
                    "action": "predict",
                    "confidence": 0.9,
                    "reason_codes": ["mhar_closer"],
                }
            )
        )
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.action, "abstain")
        self.assertEqual(invalid.confidence, 0.0)

    def test_jsonl_loader_rejects_label_side_channel(self) -> None:
        row = {
            "example_id": "one",
            "split_group": "programme-one",
            "state": valid_state(),
            "oracle_expert": "mhar",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompts.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema mismatch"):
                load_router_prompt_jsonl(path)

    def test_tokenizer_mismatch_fails_closed(self) -> None:
        fingerprint = require_compatible_tokenizers(TinyTokenizer(), TinyTokenizer())
        self.assertEqual(len(fingerprint), 64)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            require_compatible_tokenizers(TinyTokenizer(), TinyTokenizer(offset=1))

    def test_chat_template_is_used_when_available(self) -> None:
        tokenizer = TinyChatTokenizer()
        rendered = render_instruction_prompt(tokenizer, "route this")
        self.assertEqual(rendered, "<user>route this</user><assistant>")
        self.assertEqual(tokenizer.last_template_args, (False, True))

    def test_expert_conversion_does_not_read_target(self) -> None:
        output = SimpleNamespace(
            standard_std=np.asarray([0.2]),
            mhar_std=np.asarray([0.3]),
            disagreement=np.asarray([0.4]),
            domain_distance_ratio=np.asarray([0.45]),
        )
        first = SimpleNamespace(
            target=1.0,
            curve_axis=np.asarray([1.0]),
            surface_elements=np.asarray([]),
            condition_mask=np.asarray([1.0, 0.0]),
        )
        second = SimpleNamespace(
            target=999.0,
            curve_axis=np.asarray([1.0]),
            surface_elements=np.asarray([]),
            condition_mask=np.asarray([1.0, 0.0]),
        )
        kwargs = {
            "source_sample_count": 100,
            "source_validation_spearman": 0.7,
            "composition_support": [0.8],
        }
        one = router_states_from_expert_output(output, [first], **kwargs)
        two = router_states_from_expert_output(output, [second], **kwargs)
        self.assertEqual(one, two)
        self.assertAlmostEqual(one[0].standard_domain_share, 0.55)

    def test_deterministic_cold_start_policy_is_target_free_and_canonical(self) -> None:
        supported = RouterState.from_mapping(valid_state())
        decision = deterministic_target_free_decision(supported)
        self.assertTrue(decision.valid)
        self.assertEqual(decision.action, "predict")
        self.assertTrue(RouterDecision.from_text(decision_to_json(decision)).valid)

        low_skill = valid_state()
        low_skill["source_validation_spearman"] = 0.2
        abstain = deterministic_target_free_decision(
            RouterState.from_mapping(low_skill)
        )
        self.assertEqual(abstain.action, "abstain")
        self.assertEqual(abstain.reason_codes, ("low_source_skill",))

        missing = valid_state()
        missing["standard_predictive_std"] = 0.0
        self.assertEqual(
            deterministic_target_free_decision(
                RouterState.from_mapping(missing)
            ).reason_codes,
            ("missing_state",),
        )


class OPDAlgorithmTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(9)
        self.tokenizer = TinyTokenizer()

    def test_response_mask_stops_after_first_eos(self) -> None:
        sequence = torch.tensor([[1, 5, 6, 7, 2, 0]])
        mask = response_token_mask(
            sequence,
            prompt_width=3,
            eos_token_id=2,
            pad_token_id=0,
        )
        self.assertEqual(mask.tolist(), [[False, False, False, True, True, False]])

    def test_reverse_kl_is_zero_for_identical_logits_and_positive_otherwise(
        self,
    ) -> None:
        logits = torch.randn(2, 3, 7, requires_grad=True)
        mask = torch.tensor([[True, True, False], [False, True, False]])
        equal_loss, equal_metrics = reverse_kl_loss(logits, logits.detach(), mask)
        self.assertAlmostEqual(float(equal_loss.detach()), 0.0, places=6)
        shifted = logits.detach().clone()
        shifted[..., 0] += 2.0
        different_loss, metrics = reverse_kl_loss(logits, shifted, mask)
        self.assertGreater(float(different_loss.detach()), 0.0)
        different_loss.backward()
        self.assertIsNotNone(logits.grad)
        self.assertEqual(equal_metrics["response_tokens"], 3)
        self.assertGreaterEqual(metrics["top1_agreement"], 0.0)

    def test_rollout_uses_student_tokens_and_backpropagates(self) -> None:
        student = TinyCausalLM(len(self.tokenizer), seed=1)
        teacher = TinyCausalLM(len(self.tokenizer), seed=2)
        batch = self.tokenizer(["router prompt"], padding=True, return_tensors="pt")
        loss, metrics, sequence = opd_rollout_loss(
            student,
            teacher,
            batch["input_ids"],
            batch["attention_mask"],
            max_new_tokens=4,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        self.assertEqual(sequence.shape[1], batch["input_ids"].shape[1] + 4)
        self.assertEqual(metrics["response_tokens"], 4)
        loss.backward()
        self.assertTrue(
            any(parameter.grad is not None for parameter in student.parameters())
        )
        self.assertTrue(
            all(parameter.grad is None for parameter in teacher.parameters())
        )

    def test_two_step_training_smoke_records_audit_history(self) -> None:
        student = TinyCausalLM(len(self.tokenizer), seed=3)
        teacher = TinyCausalLM(len(self.tokenizer), seed=4)
        report = train_on_policy_distillation(
            student,
            teacher,
            self.tokenizer,
            [RouterState.from_mapping(valid_state()).to_prompt()],
            OPDTrainingConfig(
                steps=2,
                batch_size=1,
                learning_rate=1e-3,
                max_prompt_tokens=128,
                max_new_tokens=3,
                seed=11,
            ),
        )
        self.assertEqual(
            report["status"], "algorithm-complete-scientific-effect-unverified"
        )
        self.assertEqual(len(report["history"]), 2)
        self.assertEqual(report["final"]["step"], 2)
        self.assertGreater(report["trainable_parameters"], 0)

    def test_two_step_sft_cold_start_masks_prompt_and_updates_model(self) -> None:
        model = TinyCausalLM(len(self.tokenizer), seed=5)
        state = RouterState.from_mapping(valid_state())
        target = deterministic_target_free_decision(state)
        report = supervised_fine_tune_router(
            model,
            self.tokenizer,
            [(state, target)],
            SFTTrainingConfig(
                steps=2,
                batch_size=1,
                learning_rate=1e-3,
                max_sequence_tokens=128,
                seed=13,
            ),
        )
        self.assertEqual(
            report["status"],
            "sft-cold-start-complete-scientific-effect-unverified",
        )
        self.assertEqual(len(report["history"]), 2)
        self.assertGreater(report["final"]["supervised_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
