"""Run a white-box on-policy-distillation shadow pilot for expert routing.

The runner is deliberately offline by default. Pass --allow-download only when
model acquisition is an explicit, audited action. Scientific use also requires
a teacher that passes the strict JSON and held-out advantage preflight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.opd_router import (
    OPDTrainingConfig,
    RouterDecision,
    RouterPromptExample,
    generate_router_decision,
    load_router_prompt_jsonl,
    prompt_set_manifest,
    render_instruction_prompt,
    require_compatible_tokenizers,
    train_on_policy_distillation,
)

DESIGN_PATH = ROOT / "analysis" / "catalyst_opd_router_design.json"
DEFAULT_PROMPTS = ROOT / "analysis" / "catalyst_opd_router_smoke_prompts.jsonl"
DEFAULT_OUTPUT = ROOT / "analysis" / "results" / "catalyst_opd_router_checkpoint"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _dtype(name: str, device: torch.device) -> torch.dtype:
    if name == "float32":
        return torch.float32
    if name == "float16":
        return torch.float16
    if name == "bfloat16":
        return torch.bfloat16
    if device.type == "cuda":
        return torch.float16
    return torch.float32


def _load_tokenizer(model_name: str, *, allow_download: bool) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as error:
        raise RuntimeError(
            "transformers is required; install requirements-opd.txt"
        ) from error
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
    dtype: torch.dtype,
) -> torch.nn.Module:
    try:
        from transformers import AutoModelForCausalLM
    except ImportError as error:
        raise RuntimeError(
            "transformers is required; install requirements-opd.txt"
        ) from error
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        local_files_only=not allow_download,
        trust_remote_code=False,
        dtype=dtype,
    )
    model.to(device)
    return model


def _maybe_apply_lora(student: torch.nn.Module, rank: int) -> torch.nn.Module:
    if rank == 0:
        return student
    if rank < 0:
        raise ValueError("lora_rank may not be negative")
    try:
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as error:
        raise RuntimeError("peft is required when --lora-rank is non-zero") from error
    config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=rank,
        lora_alpha=2 * rank,
        lora_dropout=0.05,
        target_modules="all-linear",
    )
    return get_peft_model(student, config)


def _decision_row(
    example: RouterPromptExample, decision: RouterDecision, raw: str
) -> dict:
    return {
        "example_id": example.example_id,
        "split_group": example.split_group,
        "decision": asdict(decision),
        "raw_completion": raw,
    }


def _evaluate_policy(
    model: torch.nn.Module,
    tokenizer: Any,
    examples: Sequence[RouterPromptExample],
    *,
    max_new_tokens: int,
) -> dict[str, Any]:
    rows = []
    for example in examples:
        decision, raw = generate_router_decision(
            model,
            tokenizer,
            example.state,
            max_new_tokens=max_new_tokens,
        )
        rows.append(_decision_row(example, decision, raw))
    valid = sum(bool(row["decision"]["valid"]) for row in rows)
    return {
        "strict_json_valid_fraction": valid / len(rows),
        "abstain_fraction": sum(row["decision"]["action"] == "abstain" for row in rows)
        / len(rows),
        "rows": rows,
    }


def _policy_agreement(left: MappingLike, right: MappingLike) -> float:
    right_by_id = {row["example_id"]: row["decision"] for row in right["rows"]}
    agreements = []
    for row in left["rows"]:
        other = right_by_id[row["example_id"]]
        agreements.append(
            row["decision"]["expert"] == other["expert"]
            and row["decision"]["action"] == other["action"]
        )
    return sum(agreements) / len(agreements)


MappingLike = dict[str, Any]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Shadow-only OPD catalyst expert-router pilot"
    )
    parser.add_argument("--student-model", required=True)
    parser.add_argument("--teacher-model", required=True)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="auto")
    parser.add_argument(
        "--dtype",
        choices=("auto", "float32", "float16", "bfloat16"),
        default="auto",
    )
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--max-prompt-tokens", type=int, default=512)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--teacher-top-k", type=int)
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=20260809)
    parser.add_argument("--lora-rank", type=int, default=8)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help="allow Hugging Face model downloads (offline is the default)",
    )
    parser.add_argument(
        "--allow-unqualified-teacher",
        action="store_true",
        help="algorithm smoke only: train even if teacher JSON preflight fails",
    )
    args = parser.parse_args()

    if args.output_dir.is_symlink():
        raise ValueError("output directory may not be a symlink")
    examples = load_router_prompt_jsonl(args.prompts)
    device = _device(args.device)
    dtype = _dtype(args.dtype, device)

    print(f"Loading student {args.student_model!r} on {device} ({dtype})")
    student_tokenizer = _load_tokenizer(
        args.student_model, allow_download=args.allow_download
    )
    student = _load_model(
        args.student_model,
        allow_download=args.allow_download,
        device=device,
        dtype=dtype,
    )
    print(f"Loading teacher {args.teacher_model!r} on {device} ({dtype})")
    teacher_tokenizer = _load_tokenizer(
        args.teacher_model, allow_download=args.allow_download
    )
    teacher = _load_model(
        args.teacher_model,
        allow_download=args.allow_download,
        device=device,
        dtype=dtype,
    )
    tokenizer_fingerprint = require_compatible_tokenizers(
        student_tokenizer, teacher_tokenizer
    )
    prompts = [
        render_instruction_prompt(student_tokenizer, example.state.to_prompt())
        for example in examples
    ]
    if student.config.vocab_size != teacher.config.vocab_size:
        raise ValueError("teacher and student vocabulary widths differ")

    student = _maybe_apply_lora(student, args.lora_rank)
    if hasattr(student.config, "use_cache"):
        student.config.use_cache = False

    print("Running teacher and pre-training student preflight")
    teacher_evaluation = _evaluate_policy(
        teacher,
        teacher_tokenizer,
        examples,
        max_new_tokens=args.max_new_tokens,
    )
    before_evaluation = _evaluate_policy(
        student,
        student_tokenizer,
        examples,
        max_new_tokens=args.max_new_tokens,
    )

    preflight_passed = teacher_evaluation["strict_json_valid_fraction"] >= 0.95
    base_report = {
        "status": "preflight-complete",
        "scientific_effect_verified": False,
        "design": {
            "path": str(DESIGN_PATH),
            "sha256": _sha256(DESIGN_PATH),
        },
        "prompt_set": prompt_set_manifest(args.prompts, examples),
        "models": {
            "student": args.student_model,
            "teacher": args.teacher_model,
            "tokenizer_fingerprint": tokenizer_fingerprint,
            "vocab_size": int(student.config.vocab_size),
            "lora_rank": args.lora_rank,
        },
        "teacher_preflight": teacher_evaluation,
        "student_before": before_evaluation,
        "teacher_preflight_passed": preflight_passed,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "report.json", base_report)
    if not preflight_passed and not args.allow_unqualified_teacher:
        raise RuntimeError(
            "teacher failed the 0.95 strict-JSON gate; report written and "
            "training stopped. Use --allow-unqualified-teacher only for an "
            "algorithm smoke test."
        )

    config = OPDTrainingConfig(
        steps=args.steps,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_prompt_tokens=args.max_prompt_tokens,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        teacher_top_k=args.teacher_top_k,
        gradient_clip=args.gradient_clip,
        seed=args.seed,
    )

    def progress(step: int, row: dict[str, float]) -> None:
        print(
            f"step={step:04d} loss={row['loss']:.6f} "
            f"agreement={row['top1_agreement']:.3f} "
            f"tokens={int(row['response_tokens'])}"
        )

    training = train_on_policy_distillation(
        student,
        teacher,
        student_tokenizer,
        prompts,
        config,
        progress=progress,
    )
    after_evaluation = _evaluate_policy(
        student,
        student_tokenizer,
        examples,
        max_new_tokens=args.max_new_tokens,
    )
    report = {
        **base_report,
        "status": "algorithm-complete-scientific-effect-unverified",
        "training": training,
        "student_after": after_evaluation,
        "decision_agreement_with_teacher": {
            "before": _policy_agreement(before_evaluation, teacher_evaluation),
            "after": _policy_agreement(after_evaluation, teacher_evaluation),
        },
        "evidence_boundary": (
            "Synthetic or previously inspected prompts validate only the OPD "
            "implementation. A held-out teacher advantage and sealed external "
            "programme are required for a scientific claim."
        ),
    }
    student.save_pretrained(args.output_dir / "student")
    student_tokenizer.save_pretrained(args.output_dir / "student")
    _write_json(args.output_dir / "report.json", report)
    print(f"Wrote {args.output_dir / 'report.json'}")


if __name__ == "__main__":
    main()
