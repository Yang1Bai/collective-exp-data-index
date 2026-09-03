#!/usr/bin/env python3
"""Gated SFT cold start followed by OPD for the catalyst router.

Synthetic states teach only the frozen target-free policy and exact JSON
contract.  Real transfer outcomes remain evaluation-only.  Even a passing run
is retrospective shadow evidence, never model-promotion evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import secrets
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.opd_router import (
    OPDTrainingConfig,
    RouterDecision,
    RouterPromptExample,
    RouterState,
    SFTTrainingConfig,
    deterministic_target_free_decision,
    generate_router_decision,
    render_instruction_prompt,
    require_compatible_tokenizers,
    supervised_fine_tune_router,
    train_on_policy_distillation,
)

DESIGN = ROOT / "analysis" / "catalyst_opd_sft_cold_start_v2_design.json"
REAL_STATES = ROOT / "analysis" / "results" / "opd_router_real_states.json"
DEFAULT_OUTPUT = (
    ROOT / "analysis" / "results" / "catalyst_opd_sft_cold_start_v2_checkpoint"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _device(name: str) -> torch.device:
    if name != "auto":
        return torch.device(name)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_tokenizer(model_name: str, *, allow_download: bool) -> Any:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        local_files_only=not allow_download,
        trust_remote_code=False,
    )
    if tokenizer.eos_token_id is None:
        raise ValueError(f"model tokenizer has no EOS token: {model_name}")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    tokenizer.truncation_side = "left"
    return tokenizer


def _load_model(
    model_name: str,
    *,
    allow_download: bool,
    device: torch.device,
) -> torch.nn.Module:
    from transformers import AutoModelForCausalLM

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        local_files_only=not allow_download,
        trust_remote_code=False,
        dtype=torch.float32,
    )
    model.to(device)
    return model


def _apply_lora(model: torch.nn.Module, rank: int) -> torch.nn.Module:
    from peft import LoraConfig, TaskType, get_peft_model

    if rank <= 0:
        raise ValueError("LoRA rank must be positive")
    return get_peft_model(
        model,
        LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=rank,
            lora_alpha=2 * rank,
            lora_dropout=0.05,
            target_modules="all-linear",
        ),
    )


def _synthetic_examples(
    count: int, *, seed: int, prefix: str
) -> list[RouterPromptExample]:
    strata = (
        "ensemble:abstain",
        "ensemble:predict",
        "ensemble:rank",
        "standard:predict",
        "standard:rank",
        "mhar:predict",
        "mhar:rank",
    )
    quotas = {stratum: count // len(strata) for stratum in strata}
    for stratum in strata[: count % len(strata)]:
        quotas[stratum] += 1
    rng = random.Random(seed)
    examples: list[RouterPromptExample] = []
    seen: set[str] = set()
    counts: Counter[str] = Counter()
    while len(examples) < count:
        state = RouterState.from_mapping(
            {
                "task_kind": rng.choice(["catalyst_prediction", "catalyst_ranking"]),
                "source_sample_count": rng.choice([64, 128, 256, 512, 1024]),
                "target_candidate_count": rng.choice([32, 64, 128, 256, 512]),
                "source_validation_spearman": rng.choice(
                    [-0.1, 0.25, 0.49, 0.55, 0.7, 0.9, 0.9]
                ),
                "curve_available": rng.choice([False, True]),
                "surface_available": rng.choice([False, True]),
                "condition_observed_fraction": rng.choice([0.0, 0.25, 0.5, 0.75, 1.0]),
                "standard_predictive_std": rng.choice([0.0, 0.05, 0.2, 0.8, 2.0, 2.0]),
                "mhar_predictive_std": rng.choice([0.0, 0.05, 0.2, 0.8, 2.0, 2.0]),
                "normalized_expert_disagreement": rng.choice(
                    [0.1, 0.4, 0.8, 1.6, 2.6, 4.0]
                ),
                "standard_domain_share": rng.choice([0.1, 0.35, 0.5, 0.65, 0.9]),
                "composition_support": rng.choice(
                    [0.05, 0.14, 0.2, 0.34, 0.5, 0.8, 1.0, 1.0]
                ),
            }
        )
        key = json.dumps(asdict(state), sort_keys=True)
        if key in seen:
            continue
        decision = deterministic_target_free_decision(state)
        stratum = f"{decision.expert}:{decision.action}"
        if counts[stratum] >= quotas.get(stratum, 0):
            continue
        seen.add(key)
        counts[stratum] += 1
        index = len(examples)
        examples.append(
            RouterPromptExample(
                example_id=f"{prefix}-{index:04d}",
                split_group=prefix,
                state=state,
            )
        )
    return examples


def _decision_record(
    example: RouterPromptExample,
    decision: RouterDecision,
    raw: str,
    expected: RouterDecision,
) -> dict[str, Any]:
    return {
        "example_id": example.example_id,
        "decision": asdict(decision),
        "expected": asdict(expected),
        "expert_action_match": (
            decision.expert == expected.expert and decision.action == expected.action
        ),
        "raw_completion": raw,
    }


def _evaluate(
    model: torch.nn.Module,
    tokenizer: Any,
    examples: Sequence[RouterPromptExample],
    *,
    max_new_tokens: int,
) -> dict[str, Any]:
    model.eval()
    rows = []
    for example in examples:
        expected = deterministic_target_free_decision(example.state)
        decision, raw = generate_router_decision(
            model,
            tokenizer,
            example.state,
            max_new_tokens=max_new_tokens,
        )
        rows.append(_decision_record(example, decision, raw, expected))
    return {
        "examples": len(rows),
        "strict_json_valid_fraction": float(
            np.mean([row["decision"]["valid"] for row in rows])
        ),
        "expert_action_agreement_with_frozen_policy": float(
            np.mean([row["expert_action_match"] for row in rows])
        ),
        "rows": rows,
    }


def _load_real_examples(
    path: Path,
) -> tuple[list[RouterPromptExample], dict[str, dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    examples = []
    realized = {}
    for row in payload["rows"]:
        examples.append(
            RouterPromptExample.from_mapping(
                {
                    "example_id": row["example_id"],
                    "split_group": row["split_group"],
                    "state": row["state"],
                }
            )
        )
        realized[row["example_id"]] = row["evaluation"]
    return examples, realized


def _real_score(
    evaluation: dict[str, Any], realized: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    routed = []
    harmful = 0
    for row in evaluation["rows"]:
        decision = row["decision"]
        if not decision["valid"] or decision["action"] == "abstain":
            rho = 0.0
        else:
            rho = float(realized[row["example_id"]][f"{decision['expert']}_spearman"])
        routed.append(rho)
        harmful += int(rho < 0.0)
    frozen = {
        expert: float(
            np.median([values[f"{expert}_spearman"] for values in realized.values()])
        )
        for expert in ("standard", "mhar", "ensemble")
    }
    best_name, best_median = max(frozen.items(), key=lambda item: item[1])
    routed_median = float(np.median(routed))
    return {
        "routed_median_spearman": routed_median,
        "best_frozen_single_expert": {
            "name": best_name,
            "median": best_median,
        },
        "median_gain": routed_median - best_median,
        "harmful_transfer_rate": harmful / len(routed),
        "routed_spearman": routed,
    }


def _class_counts(examples: Sequence[RouterPromptExample]) -> dict[str, int]:
    counts = Counter(
        f"{decision.expert}:{decision.action}"
        for decision in (
            deterministic_target_free_decision(example.state) for example in examples
        )
    )
    return dict(sorted(counts.items()))


def _evaluation_agreement(left: dict[str, Any], right: dict[str, Any]) -> float:
    right_by_id = {row["example_id"]: row["decision"] for row in right["rows"]}
    matches = []
    for row in left["rows"]:
        other = right_by_id[row["example_id"]]
        matches.append(
            row["decision"]["expert"] == other["expert"]
            and row["decision"]["action"] == other["action"]
        )
    return float(np.mean(matches))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--teacher-model", default="HuggingFaceTB/SmolLM2-360M-Instruct"
    )
    parser.add_argument(
        "--student-model", default="HuggingFaceTB/SmolLM2-135M-Instruct"
    )
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--real-states", type=Path, default=REAL_STATES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--teacher-lora-rank", type=int, default=8)
    parser.add_argument("--student-lora-rank", type=int, default=8)
    parser.add_argument("--sft-steps", type=int)
    parser.add_argument("--sft-batch-size", type=int)
    parser.add_argument("--sft-learning-rate", type=float)
    parser.add_argument("--opd-steps", type=int)
    parser.add_argument("--opd-learning-rate", type=float, default=5e-5)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()

    if args.output_dir.is_symlink():
        raise ValueError("output directory may not be a symlink")
    design = json.loads(args.design.read_text(encoding="utf-8"))
    seed = (
        args.seed
        if args.seed is not None
        else int(design["synthetic_state_generation"]["seed"])
    )
    sft_steps = args.sft_steps or int(design["teacher"]["steps"])
    sft_batch_size = args.sft_batch_size or int(design["teacher"]["batch_size"])
    sft_learning_rate = args.sft_learning_rate or float(
        design["teacher"]["learning_rate"]
    )
    opd_steps = args.opd_steps or int(design["opd_handoff"]["steps"])
    decision_token_weight = float(
        design["training_information"].get("decision_token_weight", 1.0)
    )
    train_count = design["synthetic_state_generation"]["train_examples"]
    held_out_count = design["synthetic_state_generation"]["held_out_examples"]
    train_examples = _synthetic_examples(
        train_count, seed=seed, prefix="synthetic-train"
    )
    held_out_examples = _synthetic_examples(
        held_out_count, seed=seed + 1, prefix="synthetic-held-out"
    )
    train_keys = {
        json.dumps(asdict(row.state), sort_keys=True) for row in train_examples
    }
    held_out_keys = {
        json.dumps(asdict(row.state), sort_keys=True) for row in held_out_examples
    }
    if train_keys & held_out_keys:
        raise RuntimeError("synthetic train/held-out state overlap")

    real_examples, realized = _load_real_examples(args.real_states)
    device = _device(args.device)
    print(f"Loading teacher {args.teacher_model} on {device}", flush=True)
    teacher_tokenizer = _load_tokenizer(
        args.teacher_model, allow_download=args.allow_download
    )
    teacher = _apply_lora(
        _load_model(
            args.teacher_model,
            allow_download=args.allow_download,
            device=device,
        ),
        args.teacher_lora_rank,
    )
    if hasattr(teacher.config, "use_cache"):
        teacher.config.use_cache = False

    preflight_subset = held_out_examples[:12]
    teacher_before = _evaluate(
        teacher,
        teacher_tokenizer,
        preflight_subset,
        max_new_tokens=args.max_new_tokens,
    )
    print(
        "Teacher before SFT: "
        f"valid={teacher_before['strict_json_valid_fraction']:.3f} "
        "agreement="
        f"{teacher_before['expert_action_agreement_with_frozen_policy']:.3f}",
        flush=True,
    )

    sft_targets = [
        (example.state, deterministic_target_free_decision(example.state))
        for example in train_examples
    ]

    def sft_progress(step: int, row: dict[str, float]) -> None:
        if step == 1 or step % 10 == 0:
            print(
                f"SFT step={step:03d} loss={row['loss']:.5f} "
                f"grad={row['gradient_norm']:.3f}",
                flush=True,
            )

    sft = supervised_fine_tune_router(
        teacher,
        teacher_tokenizer,
        sft_targets,
        SFTTrainingConfig(
            steps=sft_steps,
            batch_size=sft_batch_size,
            learning_rate=sft_learning_rate,
            max_sequence_tokens=512,
            decision_token_weight=decision_token_weight,
            seed=seed,
        ),
        progress=sft_progress,
    )
    teacher_held_out = _evaluate(
        teacher,
        teacher_tokenizer,
        held_out_examples,
        max_new_tokens=args.max_new_tokens,
    )
    teacher_real = _evaluate(
        teacher,
        teacher_tokenizer,
        real_examples,
        max_new_tokens=args.max_new_tokens,
    )
    teacher_real_score = _real_score(teacher_real, realized)
    teacher_gate = (
        teacher_held_out["strict_json_valid_fraction"] >= 0.95
        and teacher_held_out["expert_action_agreement_with_frozen_policy"] >= 0.90
    )
    print(
        "Teacher held-out: "
        f"valid={teacher_held_out['strict_json_valid_fraction']:.3f} "
        "agreement="
        f"{teacher_held_out['expert_action_agreement_with_frozen_policy']:.3f} "
        f"gate={'PASS' if teacher_gate else 'FAIL'}",
        flush=True,
    )

    base_report = {
        "design_version": design["design_version"],
        "design_path": str(args.design),
        "design_sha256": _sha256(args.design),
        "real_states_sha256": _sha256(args.real_states),
        "scientific_effect_verified": False,
        "evidence_boundary": design["evidence_boundary"],
        "device": str(device),
        "models": {
            "teacher": args.teacher_model,
            "student": args.student_model,
            "teacher_lora_rank": args.teacher_lora_rank,
            "student_lora_rank": args.student_lora_rank,
        },
        "synthetic_data": {
            "train_examples": len(train_examples),
            "held_out_examples": len(held_out_examples),
            "train_class_counts": _class_counts(train_examples),
            "held_out_class_counts": _class_counts(held_out_examples),
            "train_held_out_overlap": 0,
            "target_outcomes_present": False,
        },
        "teacher_before": teacher_before,
        "teacher_sft": sft,
        "teacher_held_out": teacher_held_out,
        "teacher_gate_passed": teacher_gate,
        "teacher_real": teacher_real,
        "teacher_real_score": teacher_real_score,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    teacher.save_pretrained(args.output_dir / "teacher")
    teacher_tokenizer.save_pretrained(args.output_dir / "teacher")
    _write_json(args.output_dir / "report.json", base_report)
    if not teacher_gate:
        print("Teacher gate failed; OPD handoff stopped.", flush=True)
        return

    print(f"Loading student {args.student_model} on {device}", flush=True)
    student_tokenizer = _load_tokenizer(
        args.student_model, allow_download=args.allow_download
    )
    tokenizer_fingerprint = require_compatible_tokenizers(
        student_tokenizer, teacher_tokenizer
    )
    student = _apply_lora(
        _load_model(
            args.student_model,
            allow_download=args.allow_download,
            device=device,
        ),
        args.student_lora_rank,
    )
    if student.config.vocab_size != teacher.config.vocab_size:
        raise ValueError("teacher and student vocabulary widths differ")
    if hasattr(student.config, "use_cache"):
        student.config.use_cache = False

    student_before = _evaluate(
        student,
        student_tokenizer,
        preflight_subset,
        max_new_tokens=args.max_new_tokens,
    )
    prompts = [
        render_instruction_prompt(student_tokenizer, example.state.to_prompt())
        for example in train_examples
    ]

    def opd_progress(step: int, row: dict[str, float]) -> None:
        if step == 1 or step % 5 == 0:
            print(
                f"OPD step={step:03d} loss={row['loss']:.5f} "
                f"top1={row['top1_agreement']:.3f}",
                flush=True,
            )

    opd = train_on_policy_distillation(
        student,
        teacher,
        student_tokenizer,
        prompts,
        OPDTrainingConfig(
            steps=opd_steps,
            batch_size=1,
            learning_rate=args.opd_learning_rate,
            max_prompt_tokens=512,
            max_new_tokens=args.max_new_tokens,
            teacher_top_k=64,
            seed=seed,
        ),
        progress=opd_progress,
    )
    student_held_out = _evaluate(
        student,
        student_tokenizer,
        held_out_examples,
        max_new_tokens=args.max_new_tokens,
    )
    student_real = _evaluate(
        student,
        student_tokenizer,
        real_examples,
        max_new_tokens=args.max_new_tokens,
    )
    student_real_score = _real_score(student_real, realized)
    student_teacher_agreement = _evaluation_agreement(
        student_held_out, teacher_held_out
    )
    student_gate = (
        student_held_out["strict_json_valid_fraction"] >= 0.95
        and student_teacher_agreement >= 0.90
    )
    report = {
        **base_report,
        "tokenizer_fingerprint": tokenizer_fingerprint,
        "opd": opd,
        "student_before": student_before,
        "student_held_out": student_held_out,
        "student_held_out_expert_action_agreement_with_teacher": (
            student_teacher_agreement
        ),
        "student_gate_passed": student_gate,
        "student_real": student_real,
        "student_real_score": student_real_score,
        "status": (
            "opd-student-gate-passed-shadow-only"
            if student_gate
            else "opd-student-gate-failed-shadow-only"
        ),
    }
    student.save_pretrained(args.output_dir / "student")
    student_tokenizer.save_pretrained(args.output_dir / "student")
    _write_json(args.output_dir / "report.json", report)
    print(
        "Student held-out: "
        f"valid={student_held_out['strict_json_valid_fraction']:.3f} "
        "agreement="
        f"{student_held_out['expert_action_agreement_with_frozen_policy']:.3f} "
        f"gate={'PASS' if student_gate else 'FAIL'}",
        flush=True,
    )
    print(f"Wrote {args.output_dir / 'report.json'}", flush=True)


if __name__ == "__main__":
    main()
