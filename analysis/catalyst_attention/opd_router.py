"""Shadow-only on-policy distillation support for catalyst expert routing.

The numerical catalyst models remain authoritative for property prediction.
This module lets a causal-language-model student learn a target-label-free
routing policy from a white-box teacher.  It deliberately separates three
surfaces:

* :class:`RouterState` is the only information admitted to an LLM prompt;
* :class:`RouterDecision` is a strict, fail-closed JSON contract;
* :func:`opd_rollout_loss` implements student-rollout reverse-KL distillation.

No target outcome, oracle expert choice, or target performance metric is an
allowed prompt field.  Existing programme outcomes are evaluation-only.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor

if TYPE_CHECKING:
    from .data import CatalystSample
    from .expert_router import ExpertRouterOutput


DESIGN_VERSION = "catalyst-opd-router-shadow-v1"

_TASK_KINDS = frozenset({"catalyst_prediction", "catalyst_ranking"})
_EXPERTS = frozenset({"standard", "mhar", "ensemble"})
_ACTIONS = frozenset({"predict", "rank", "abstain"})
_REASON_CODES = frozenset(
    {
        "source_supported",
        "experts_agree",
        "high_disagreement",
        "standard_closer",
        "mhar_closer",
        "high_uncertainty",
        "out_of_support",
        "missing_state",
        "low_source_skill",
        "invalid_output",
    }
)


def decision_to_json(decision: RouterDecision) -> str:
    """Serialize one valid decision as the canonical SFT completion."""

    if not decision.valid:
        raise ValueError("fail-closed decisions are not valid SFT targets")
    return json.dumps(
        {
            "expert": decision.expert,
            "action": decision.action,
            "confidence": decision.confidence,
            "reason_codes": list(decision.reason_codes),
        },
        separators=(",", ":"),
    )


def _finite_float(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


@dataclass(frozen=True)
class RouterState:
    """Target-label-free state presented to the language-model router."""

    task_kind: str
    source_sample_count: int
    target_candidate_count: int
    source_validation_spearman: float
    curve_available: bool
    surface_available: bool
    condition_observed_fraction: float
    standard_predictive_std: float
    mhar_predictive_std: float
    normalized_expert_disagreement: float
    standard_domain_share: float
    composition_support: float

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RouterState:
        allowed = set(cls.__dataclass_fields__)
        received = set(payload)
        missing = allowed - received
        extra = received - allowed
        if missing or extra:
            raise ValueError(
                "router state schema mismatch: "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        task_kind = payload["task_kind"]
        if task_kind not in _TASK_KINDS:
            raise ValueError(f"unsupported task_kind: {task_kind!r}")
        for name in ("curve_available", "surface_available"):
            if not isinstance(payload[name], bool):
                raise TypeError(f"{name} must be boolean")

        values = {
            "source_validation_spearman": _finite_float(
                "source_validation_spearman",
                payload["source_validation_spearman"],
            ),
            "condition_observed_fraction": _finite_float(
                "condition_observed_fraction",
                payload["condition_observed_fraction"],
            ),
            "standard_predictive_std": _finite_float(
                "standard_predictive_std", payload["standard_predictive_std"]
            ),
            "mhar_predictive_std": _finite_float(
                "mhar_predictive_std", payload["mhar_predictive_std"]
            ),
            "normalized_expert_disagreement": _finite_float(
                "normalized_expert_disagreement",
                payload["normalized_expert_disagreement"],
            ),
            "standard_domain_share": _finite_float(
                "standard_domain_share", payload["standard_domain_share"]
            ),
            "composition_support": _finite_float(
                "composition_support", payload["composition_support"]
            ),
        }
        if not -1.0 <= values["source_validation_spearman"] <= 1.0:
            raise ValueError("source_validation_spearman must be in [-1, 1]")
        for name in (
            "condition_observed_fraction",
            "standard_domain_share",
            "composition_support",
        ):
            if not 0.0 <= values[name] <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        for name in (
            "standard_predictive_std",
            "mhar_predictive_std",
            "normalized_expert_disagreement",
        ):
            if values[name] < 0.0:
                raise ValueError(f"{name} must be non-negative")

        return cls(
            task_kind=task_kind,
            source_sample_count=_positive_int(
                "source_sample_count", payload["source_sample_count"]
            ),
            target_candidate_count=_positive_int(
                "target_candidate_count", payload["target_candidate_count"]
            ),
            curve_available=payload["curve_available"],
            surface_available=payload["surface_available"],
            **values,
        )

    def to_prompt(self) -> str:
        state_json = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return (
            "You are a conservative catalyst transfer router. You may only use "
            "the target-label-free diagnostics in ROUTER_STATE. Do not infer a "
            "hidden outcome. Select one frozen expert and one action. Return "
            "exactly one JSON object with no prose and these keys: expert, "
            "action, confidence, reason_codes. expert is standard, mhar, or "
            "ensemble. action is predict, rank, or abstain. confidence is in "
            "[0,1]. reason_codes is a non-empty list chosen from "
            "source_supported, experts_agree, high_disagreement, "
            "standard_closer, mhar_closer, high_uncertainty, out_of_support, "
            "missing_state, low_source_skill.\n"
            f"ROUTER_STATE={state_json}\n"
            "DECISION="
        )


@dataclass(frozen=True)
class RouterPromptExample:
    example_id: str
    split_group: str
    state: RouterState

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RouterPromptExample:
        allowed = {"example_id", "split_group", "state"}
        if set(payload) != allowed:
            raise ValueError(
                "prompt example schema mismatch: "
                f"expected={sorted(allowed)}, received={sorted(payload)}"
            )
        example_id = payload["example_id"]
        split_group = payload["split_group"]
        if not isinstance(example_id, str) or not example_id.strip():
            raise ValueError("example_id must be a non-empty string")
        if not isinstance(split_group, str) or not split_group.strip():
            raise ValueError("split_group must be a non-empty string")
        state_payload = payload["state"]
        if not isinstance(state_payload, Mapping):
            raise TypeError("state must be an object")
        return cls(
            example_id=example_id,
            split_group=split_group,
            state=RouterState.from_mapping(state_payload),
        )


def load_router_prompt_jsonl(path: str | Path) -> list[RouterPromptExample]:
    """Load a bounded, exact-schema prompt set with no outcome fields."""

    source = Path(path)
    if source.is_symlink():
        raise ValueError("prompt file may not be a symlink")
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("prompt file exceeds the 10 MiB pilot limit")

    examples: list[RouterPromptExample] = []
    identifiers: set[str] = set()
    for line_number, line in enumerate(
        source.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"invalid JSON on prompt line {line_number}: {error.msg}"
            ) from error
        if not isinstance(payload, Mapping):
            raise TypeError(f"prompt line {line_number} must be an object")
        example = RouterPromptExample.from_mapping(payload)
        if example.example_id in identifiers:
            raise ValueError(f"duplicate example_id: {example.example_id}")
        identifiers.add(example.example_id)
        examples.append(example)
    if not examples:
        raise ValueError("prompt set is empty")
    return examples


def prompt_set_manifest(
    path: str | Path, examples: Sequence[RouterPromptExample]
) -> dict[str, Any]:
    source = Path(path)
    return {
        "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "bytes": source.stat().st_size,
        "examples": len(examples),
        "split_groups": sorted({example.split_group for example in examples}),
        "contains_target_outcomes": False,
    }


@dataclass(frozen=True)
class RouterDecision:
    expert: str
    action: str
    confidence: float
    reason_codes: tuple[str, ...]
    valid: bool = True

    @classmethod
    def fail_closed(cls, reason: str = "invalid_output") -> RouterDecision:
        if reason not in _REASON_CODES:
            reason = "invalid_output"
        return cls(
            expert="ensemble",
            action="abstain",
            confidence=0.0,
            reason_codes=(reason,),
            valid=False,
        )

    @classmethod
    def from_text(cls, text: str) -> RouterDecision:
        """Parse one exact JSON object; any prose or schema drift abstains."""

        stripped = text.strip()
        if not stripped.startswith("{") or not stripped.endswith("}"):
            return cls.fail_closed()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return cls.fail_closed()
        if not isinstance(payload, Mapping):
            return cls.fail_closed()
        if set(payload) != {"expert", "action", "confidence", "reason_codes"}:
            return cls.fail_closed()
        expert = payload["expert"]
        action = payload["action"]
        if expert not in _EXPERTS or action not in _ACTIONS:
            return cls.fail_closed()
        try:
            confidence = _finite_float("confidence", payload["confidence"])
        except ValueError:
            return cls.fail_closed()
        if not 0.0 <= confidence <= 1.0:
            return cls.fail_closed()
        reasons = payload["reason_codes"]
        if (
            not isinstance(reasons, list)
            or not reasons
            or len(reasons) > 4
            or any(
                reason not in _REASON_CODES - {"invalid_output"} for reason in reasons
            )
            or len(set(reasons)) != len(reasons)
        ):
            return cls.fail_closed()
        return cls(
            expert=expert,
            action=action,
            confidence=confidence,
            reason_codes=tuple(reasons),
            valid=True,
        )


def deterministic_target_free_decision(state: RouterState) -> RouterDecision:
    """Frozen, outcome-free policy used only to cold-start JSON behaviour.

    The policy deliberately uses coarse, interpretable thresholds.  It is a
    baseline and SFT label generator, not an oracle and not promotion evidence.
    ``standard_domain_share`` is a closeness share: values above 0.5 favour the
    Standard expert and values below 0.5 favour MHAR.
    """

    if state.standard_predictive_std <= 1e-12 or state.mhar_predictive_std <= 1e-12:
        return RouterDecision(
            expert="ensemble",
            action="abstain",
            confidence=0.95,
            reason_codes=("missing_state",),
        )
    if state.source_validation_spearman < 0.5:
        return RouterDecision(
            expert="ensemble",
            action="abstain",
            confidence=0.9,
            reason_codes=("low_source_skill",),
        )
    if state.composition_support < 0.15:
        return RouterDecision(
            expert="ensemble",
            action="abstain",
            confidence=0.9,
            reason_codes=("out_of_support",),
        )

    disagreement = state.normalized_expert_disagreement
    standard_share = state.standard_domain_share
    standard_more_certain = (
        state.standard_predictive_std <= 0.9 * state.mhar_predictive_std
    )
    mhar_more_certain = state.mhar_predictive_std <= 0.9 * state.standard_predictive_std

    if disagreement <= 0.5:
        expert = "ensemble"
        reasons = ["experts_agree"]
    elif standard_share >= 0.55 and not mhar_more_certain:
        expert = "standard"
        reasons = ["standard_closer"]
    elif standard_share <= 0.45 and not standard_more_certain:
        expert = "mhar"
        reasons = ["mhar_closer"]
    elif standard_more_certain:
        expert = "standard"
        reasons = ["standard_closer"]
    elif mhar_more_certain:
        expert = "mhar"
        reasons = ["mhar_closer"]
    else:
        expert = "ensemble"
        reasons = ["high_disagreement"]

    if disagreement > 1.5 and "high_disagreement" not in reasons:
        reasons.append("high_disagreement")
    if state.source_validation_spearman >= 0.65:
        reasons.insert(0, "source_supported")

    cautious = (
        state.composition_support < 0.35
        or disagreement > 2.5
        or state.source_validation_spearman < 0.65
    )
    return RouterDecision(
        expert=expert,
        action="rank" if cautious else "predict",
        confidence=0.65 if cautious else 0.8,
        reason_codes=tuple(reasons[:4]),
    )


def tokenizer_fingerprint(tokenizer: Any) -> str:
    """Hash special tokens and probe encodings to detect tokenizer drift."""

    probes = (
        "catalyst transfer",
        '{"expert":"ensemble","action":"abstain"}',
        "Fe0.4Co0.6 OER pH=7",
    )
    encodings = []
    for probe in probes:
        encoded = tokenizer(probe, add_special_tokens=False)
        input_ids = encoded["input_ids"]
        if input_ids and isinstance(input_ids[0], list):
            input_ids = input_ids[0]
        encodings.append([int(token) for token in input_ids])
    payload = {
        "class": tokenizer.__class__.__name__,
        "vocab_size": len(tokenizer),
        "bos_token_id": tokenizer.bos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
        "chat_template": getattr(tokenizer, "chat_template", None),
        "encodings": encodings,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()


def require_compatible_tokenizers(
    student_tokenizer: Any, teacher_tokenizer: Any
) -> str:
    student_fingerprint = tokenizer_fingerprint(student_tokenizer)
    teacher_fingerprint = tokenizer_fingerprint(teacher_tokenizer)
    if student_fingerprint != teacher_fingerprint:
        raise ValueError(
            "teacher and student tokenizers are incompatible; OPD is fail-closed"
        )
    return student_fingerprint


def render_instruction_prompt(tokenizer: Any, prompt: str) -> str:
    """Use a model's chat template when present, otherwise preserve raw text."""

    if not isinstance(prompt, str) or not prompt:
        raise ValueError("prompt must be a non-empty string")
    chat_template = getattr(tokenizer, "chat_template", None)
    if not chat_template or not hasattr(tokenizer, "apply_chat_template"):
        return prompt
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    if not isinstance(rendered, str) or not rendered:
        raise ValueError("chat template returned an invalid prompt")
    return rendered


def response_token_mask(
    sequences: Tensor,
    *,
    prompt_width: int,
    eos_token_id: int | None,
    pad_token_id: int | None,
) -> Tensor:
    """Mark generated tokens through the first EOS, excluding prompt/padding."""

    if sequences.ndim != 2:
        raise ValueError("sequences must have shape [batch, length]")
    if prompt_width <= 0 or prompt_width >= sequences.shape[1]:
        raise ValueError("prompt_width must leave at least one response token")
    mask = torch.zeros_like(sequences, dtype=torch.bool)
    mask[:, prompt_width:] = True
    for row_index in range(sequences.shape[0]):
        response = sequences[row_index, prompt_width:]
        stop: int | None = None
        if eos_token_id is not None:
            locations = torch.nonzero(response == eos_token_id, as_tuple=False)
            if len(locations):
                stop = int(locations[0, 0]) + 1
        if stop is not None:
            mask[row_index, prompt_width + stop :] = False
        elif pad_token_id is not None:
            mask[row_index, prompt_width:] &= response != pad_token_id
    return mask


def reverse_kl_loss(
    student_logits: Tensor,
    teacher_logits: Tensor,
    token_mask: Tensor,
    *,
    temperature: float = 1.0,
    teacher_top_k: int | None = None,
) -> tuple[Tensor, dict[str, float]]:
    """Exact token-level reverse KL on student-visited prefixes.

    ``teacher_top_k`` optionally renormalizes both distributions over the
    teacher's local top-k support.  Full-vocabulary KL is the default.
    """

    if student_logits.shape != teacher_logits.shape:
        raise ValueError("teacher and student logits must have identical shapes")
    if student_logits.ndim != 3:
        raise ValueError("logits must have shape [batch, tokens, vocabulary]")
    if token_mask.shape != student_logits.shape[:2]:
        raise ValueError("token mask is not aligned with logits")
    if not token_mask.any():
        raise ValueError("OPD loss requires at least one response token")
    if temperature <= 0.0:
        raise ValueError("temperature must be positive")

    student = student_logits.float() / temperature
    teacher = teacher_logits.float() / temperature
    vocabulary = student.shape[-1]
    if teacher_top_k is not None:
        if teacher_top_k <= 1 or teacher_top_k > vocabulary:
            raise ValueError("teacher_top_k must be in [2, vocabulary]")
        indices = torch.topk(teacher, teacher_top_k, dim=-1).indices
        student = torch.gather(student, dim=-1, index=indices)
        teacher = torch.gather(teacher, dim=-1, index=indices)

    student_log_prob = F.log_softmax(student, dim=-1)
    teacher_log_prob = F.log_softmax(teacher, dim=-1)
    student_prob = student_log_prob.exp()
    token_kl = torch.sum(student_prob * (student_log_prob - teacher_log_prob), dim=-1)
    loss = token_kl[token_mask].mean() * (temperature**2)

    with torch.no_grad():
        student_entropy = -torch.sum(student_prob * student_log_prob, dim=-1)[
            token_mask
        ].mean()
        teacher_prob = teacher_log_prob.exp()
        teacher_entropy = -torch.sum(teacher_prob * teacher_log_prob, dim=-1)[
            token_mask
        ].mean()
        agreement = (
            (student.argmax(dim=-1)[token_mask] == teacher.argmax(dim=-1)[token_mask])
            .float()
            .mean()
        )
    return loss, {
        "loss": float(loss.detach()),
        "response_tokens": int(token_mask.sum()),
        "student_entropy": float(student_entropy),
        "teacher_entropy": float(teacher_entropy),
        "top1_agreement": float(agreement),
    }


def _module_device(module: torch.nn.Module) -> torch.device:
    try:
        return next(module.parameters()).device
    except StopIteration as error:
        raise ValueError("language model has no parameters") from error


def opd_rollout_loss(
    student: torch.nn.Module,
    teacher: torch.nn.Module,
    input_ids: Tensor,
    attention_mask: Tensor,
    *,
    max_new_tokens: int,
    temperature: float = 1.0,
    top_p: float = 0.95,
    teacher_top_k: int | None = None,
    eos_token_id: int | None = None,
    pad_token_id: int | None = None,
) -> tuple[Tensor, dict[str, float], Tensor]:
    """Generate from the current student and score those prefixes with teacher."""

    if max_new_tokens <= 0:
        raise ValueError("max_new_tokens must be positive")
    if not 0.0 < top_p <= 1.0:
        raise ValueError("top_p must be in (0, 1]")
    if input_ids.shape != attention_mask.shape or input_ids.ndim != 2:
        raise ValueError("input_ids and attention_mask must be aligned matrices")

    student_device = _module_device(student)
    teacher_device = _module_device(teacher)
    input_ids = input_ids.to(student_device)
    attention_mask = attention_mask.to(student_device)
    prompt_width = input_ids.shape[1]

    was_training = student.training
    student.eval()
    with torch.no_grad():
        sequences = student.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
            eos_token_id=eos_token_id,
            pad_token_id=pad_token_id,
        )
    student.train(was_training)

    response_mask = response_token_mask(
        sequences,
        prompt_width=prompt_width,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
    )
    sequence_attention = torch.cat(
        [
            attention_mask,
            response_mask[:, prompt_width:].to(attention_mask.dtype),
        ],
        dim=1,
    )
    student_output = student(
        input_ids=sequences,
        attention_mask=sequence_attention,
    )
    student_logits = student_output.logits[:, :-1]

    teacher_sequences = sequences.to(teacher_device)
    teacher_attention = sequence_attention.to(teacher_device)
    teacher.eval()
    with torch.no_grad():
        teacher_logits = teacher(
            input_ids=teacher_sequences,
            attention_mask=teacher_attention,
        ).logits[:, :-1]
    teacher_logits = teacher_logits.to(student_device)
    causal_mask = response_mask[:, 1:]
    loss, metrics = reverse_kl_loss(
        student_logits,
        teacher_logits,
        causal_mask,
        temperature=temperature,
        teacher_top_k=teacher_top_k,
    )
    metrics["prompt_tokens"] = int(attention_mask.sum())
    return loss, metrics, sequences.detach()


@dataclass(frozen=True)
class OPDTrainingConfig:
    steps: int = 20
    batch_size: int = 1
    learning_rate: float = 1e-5
    weight_decay: float = 0.0
    max_prompt_tokens: int = 512
    max_new_tokens: int = 96
    temperature: float = 1.0
    top_p: float = 0.95
    teacher_top_k: int | None = None
    gradient_clip: float = 1.0
    seed: int = 20260809

    def validate(self) -> None:
        if self.steps <= 0 or self.batch_size <= 0:
            raise ValueError("steps and batch_size must be positive")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("invalid optimizer configuration")
        if self.max_prompt_tokens <= 0 or self.max_new_tokens <= 0:
            raise ValueError("token limits must be positive")
        if self.temperature <= 0.0 or not 0.0 < self.top_p <= 1.0:
            raise ValueError("invalid rollout sampling configuration")
        if self.gradient_clip <= 0.0:
            raise ValueError("gradient_clip must be positive")


@dataclass(frozen=True)
class SFTTrainingConfig:
    steps: int = 80
    batch_size: int = 2
    learning_rate: float = 2e-4
    weight_decay: float = 0.0
    max_sequence_tokens: int = 512
    decision_token_weight: float = 1.0
    gradient_clip: float = 1.0
    seed: int = 20260812

    def validate(self) -> None:
        if self.steps <= 0 or self.batch_size <= 0:
            raise ValueError("steps and batch_size must be positive")
        if self.learning_rate <= 0.0 or self.weight_decay < 0.0:
            raise ValueError("invalid optimizer configuration")
        if (
            self.max_sequence_tokens <= 0
            or self.decision_token_weight < 1.0
            or self.gradient_clip <= 0.0
        ):
            raise ValueError("token limit and gradient clip must be positive")


def _encode_sft_example(
    tokenizer: Any,
    state: RouterState,
    decision: RouterDecision,
    *,
    max_sequence_tokens: int,
    decision_token_weight: float,
) -> tuple[list[int], list[int], list[float]]:
    prompt = render_instruction_prompt(tokenizer, state.to_prompt())
    completion = decision_to_json(decision)
    prompt_ids = list(tokenizer(prompt, add_special_tokens=False)["input_ids"])
    completion_encoding = tokenizer(completion, add_special_tokens=False)
    completion_ids = list(completion_encoding["input_ids"])
    completion_weights = [1.0] * len(completion_ids)
    if decision_token_weight > 1.0:
        try:
            offset_encoding = tokenizer(
                completion,
                add_special_tokens=False,
                return_offsets_mapping=True,
            )
            offsets = offset_encoding["offset_mapping"]
        except (KeyError, TypeError, ValueError, NotImplementedError):
            offsets = None
        if offsets is not None and len(offsets) == len(completion_ids):
            values = [
                decision.expert,
                decision.action,
                str(decision.confidence),
                *decision.reason_codes,
            ]
            spans = []
            for value in values:
                start = completion.find(value)
                if start >= 0:
                    spans.append((start, start + len(value)))
            for index, (token_start, token_end) in enumerate(offsets):
                if any(
                    token_start < span_end and token_end > span_start
                    for span_start, span_end in spans
                ):
                    completion_weights[index] = decision_token_weight
    eos_token_id = tokenizer.eos_token_id
    if eos_token_id is None:
        raise ValueError("SFT tokenizer requires an EOS token")
    completion_ids.append(int(eos_token_id))
    completion_weights.append(1.0)
    if len(completion_ids) >= max_sequence_tokens:
        raise ValueError("SFT completion exceeds the sequence-token limit")
    prompt_budget = max_sequence_tokens - len(completion_ids)
    prompt_ids = prompt_ids[-prompt_budget:]
    input_ids = [*prompt_ids, *completion_ids]
    labels = [-100] * len(prompt_ids) + completion_ids
    loss_weights = [0.0] * len(prompt_ids) + completion_weights
    return input_ids, labels, loss_weights


def _collate_sft_batch(
    rows: Sequence[tuple[list[int], list[int], list[float]]], pad_token_id: int
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    width = max(len(input_ids) for input_ids, _, _ in rows)
    input_batch = []
    label_batch = []
    attention_batch = []
    weight_batch = []
    for input_ids, labels, loss_weights in rows:
        padding = width - len(input_ids)
        input_batch.append(input_ids + [pad_token_id] * padding)
        label_batch.append(labels + [-100] * padding)
        attention_batch.append([1] * len(input_ids) + [0] * padding)
        weight_batch.append(loss_weights + [0.0] * padding)
    return (
        torch.tensor(input_batch, dtype=torch.long),
        torch.tensor(attention_batch, dtype=torch.long),
        torch.tensor(label_batch, dtype=torch.long),
        torch.tensor(weight_batch, dtype=torch.float32),
    )


def supervised_fine_tune_router(
    model: torch.nn.Module,
    tokenizer: Any,
    examples: Sequence[tuple[RouterState, RouterDecision]],
    config: SFTTrainingConfig,
    *,
    optimizer: torch.optim.Optimizer | None = None,
    progress: Callable[[int, Mapping[str, float]], None] | None = None,
) -> dict[str, Any]:
    """Cold-start a router on exact, outcome-free deterministic decisions."""

    config.validate()
    if not examples:
        raise ValueError("SFT requires at least one example")
    if tokenizer.pad_token_id is None:
        raise ValueError("SFT tokenizer requires a padding token")
    encoded = [
        _encode_sft_example(
            tokenizer,
            state,
            decision,
            max_sequence_tokens=config.max_sequence_tokens,
            decision_token_weight=config.decision_token_weight,
        )
        for state, decision in examples
    ]
    trainable = [
        parameter for parameter in model.parameters() if parameter.requires_grad
    ]
    if not trainable:
        raise ValueError("SFT model has no trainable parameters")
    if optimizer is None:
        optimizer = torch.optim.AdamW(
            trainable,
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

    randomizer = random.Random(config.seed)
    torch.manual_seed(config.seed)
    device = _module_device(model)
    model.train()
    history: list[dict[str, float]] = []
    for step in range(1, config.steps + 1):
        batch = [
            encoded[randomizer.randrange(len(encoded))]
            for _ in range(config.batch_size)
        ]
        input_ids, attention_mask, labels, loss_weights = _collate_sft_batch(
            batch, int(tokenizer.pad_token_id)
        )
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)
        labels = labels.to(device)
        loss_weights = loss_weights.to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        shift_logits = output.logits[:, :-1].contiguous()
        shift_labels = labels[:, 1:].contiguous()
        shift_weights = loss_weights[:, 1:].contiguous()
        token_loss = F.cross_entropy(
            shift_logits.reshape(-1, shift_logits.shape[-1]),
            shift_labels.reshape(-1),
            ignore_index=-100,
            reduction="none",
        ).reshape_as(shift_labels)
        weight_sum = shift_weights.sum()
        if weight_sum <= 0:
            raise ValueError("SFT batch has no supervised token weight")
        loss = (token_loss * shift_weights).sum() / weight_sum
        if not torch.isfinite(loss):
            raise FloatingPointError("non-finite SFT loss")
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, config.gradient_clip)
        optimizer.step()
        row = {
            "step": step,
            "loss": float(loss.detach()),
            "gradient_norm": float(gradient_norm),
            "supervised_tokens": float((labels != -100).sum()),
            "weighted_token_mass": float(loss_weights.sum()),
        }
        history.append(row)
        if progress is not None:
            progress(step, row)
    return {
        "design_version": DESIGN_VERSION,
        "status": "sft-cold-start-complete-scientific-effect-unverified",
        "config": asdict(config),
        "example_count": len(examples),
        "trainable_parameters": sum(parameter.numel() for parameter in trainable),
        "history": history,
        "final": history[-1],
    }


def train_on_policy_distillation(
    student: torch.nn.Module,
    teacher: torch.nn.Module,
    tokenizer: Any,
    prompts: Sequence[str],
    config: OPDTrainingConfig,
    *,
    optimizer: torch.optim.Optimizer | None = None,
    progress: Callable[[int, Mapping[str, float]], None] | None = None,
) -> dict[str, Any]:
    """Run a small auditable OPD loop over target-label-free prompts."""

    config.validate()
    if not prompts:
        raise ValueError("OPD training requires at least one prompt")
    if any(not isinstance(prompt, str) or not prompt for prompt in prompts):
        raise ValueError("all prompts must be non-empty strings")
    randomizer = random.Random(config.seed)
    torch.manual_seed(config.seed)

    for parameter in teacher.parameters():
        parameter.requires_grad_(False)
    teacher.eval()
    trainable = [
        parameter for parameter in student.parameters() if parameter.requires_grad
    ]
    if not trainable:
        raise ValueError("student has no trainable parameters")
    if optimizer is None:
        optimizer = torch.optim.AdamW(
            trainable,
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

    history: list[dict[str, float]] = []
    device = _module_device(student)
    for step in range(1, config.steps + 1):
        batch = [
            prompts[randomizer.randrange(len(prompts))]
            for _ in range(config.batch_size)
        ]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=config.max_prompt_tokens,
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        optimizer.zero_grad(set_to_none=True)
        loss, row, _ = opd_rollout_loss(
            student,
            teacher,
            input_ids,
            attention_mask,
            max_new_tokens=config.max_new_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            teacher_top_k=config.teacher_top_k,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
        loss.backward()
        gradient_norm = torch.nn.utils.clip_grad_norm_(trainable, config.gradient_clip)
        optimizer.step()
        row = {
            **row,
            "step": step,
            "gradient_norm": float(gradient_norm),
        }
        history.append(row)
        if progress is not None:
            progress(step, row)

    return {
        "design_version": DESIGN_VERSION,
        "status": "algorithm-complete-scientific-effect-unverified",
        "config": asdict(config),
        "prompt_count": len(prompts),
        "trainable_parameters": sum(parameter.numel() for parameter in trainable),
        "history": history,
        "final": history[-1],
    }


def generate_router_decision(
    model: torch.nn.Module,
    tokenizer: Any,
    state: RouterState,
    *,
    max_new_tokens: int = 96,
) -> tuple[RouterDecision, str]:
    """Generate one deterministic decision and parse it fail-closed."""

    device = _module_device(model)
    prompt = render_instruction_prompt(tokenizer, state.to_prompt())
    encoded = tokenizer(prompt, return_tensors="pt")
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    with torch.no_grad():
        output = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )
    completion = tokenizer.decode(
        output[0, input_ids.shape[1] :], skip_special_tokens=True
    )
    return RouterDecision.from_text(completion), completion


def router_states_from_expert_output(
    output: ExpertRouterOutput,
    samples: Sequence[CatalystSample],
    *,
    source_sample_count: int,
    source_validation_spearman: float,
    composition_support: Sequence[float],
    task_kind: str = "catalyst_ranking",
) -> list[RouterState]:
    """Convert current expert diagnostics without reading sample targets."""

    count = len(samples)
    arrays = (
        output.standard_std,
        output.mhar_std,
        output.disagreement,
        output.domain_distance_ratio,
        np.asarray(composition_support, dtype=float),
    )
    if any(len(array) != count for array in arrays):
        raise ValueError("expert diagnostics and samples are not aligned")
    states = []
    for index, sample in enumerate(samples):
        condition_fraction = float(np.mean(sample.condition_mask > 0))
        states.append(
            RouterState.from_mapping(
                {
                    "task_kind": task_kind,
                    "source_sample_count": source_sample_count,
                    "target_candidate_count": count,
                    "source_validation_spearman": source_validation_spearman,
                    "curve_available": bool(len(sample.curve_axis)),
                    "surface_available": bool(len(sample.surface_elements)),
                    "condition_observed_fraction": condition_fraction,
                    "standard_predictive_std": float(output.standard_std[index]),
                    "mhar_predictive_std": float(output.mhar_std[index]),
                    "normalized_expert_disagreement": float(output.disagreement[index]),
                    "standard_domain_share": float(
                        1.0 - output.domain_distance_ratio[index]
                    ),
                    "composition_support": float(composition_support[index]),
                }
            )
        )
    return states
