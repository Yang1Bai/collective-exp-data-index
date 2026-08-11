#!/usr/bin/env python3
"""Teacher preflight + downstream scientific-gate evaluation for OPD router.

The design contract (catalyst_opd_router_design.json) requires, before any
scientific claim:

* implementation gate: teacher strict-JSON fraction >= 0.95 on real
  programme-held-out prompts;
* scientific gate: median routed Spearman >= best frozen single expert
  median + 0.02, with no direction regression and no increase in harmful
  transfer rate.

This runner loads a white-box teacher, generates one decision per real
edge in ``opd_router_real_states.jsonl``, then scores the routed
downstream Spearman against the realized expert outcomes in
``opd_router_real_states.json``. Training (on-policy distillation into a
student) is a separate step; this is the gate the teacher must clear
first.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.opd_router import (  # noqa: E402
    RouterDecision,
    RouterPromptExample,
    generate_router_decision,
    load_router_prompt_jsonl,
    render_instruction_prompt,
    require_compatible_tokenizers,
)

RESULTS = ROOT / "analysis" / "results"
STATES_JSON = RESULTS / "opd_router_real_states.json"
STATES_JSONL = RESULTS / "opd_router_real_states.jsonl"


def _load_tokenizer(model_name: str, *, allow_download: bool) -> Any:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(
        model_name, local_files_only=not allow_download, trust_remote_code=False
    )
    if tok.eos_token_id is None:
        raise ValueError(f"no EOS token: {model_name}")
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"
    tok.truncation_side = "left"
    return tok


def _load_model(model_name: str, *, allow_download: bool, device: torch.device, dtype: torch.dtype):
    from transformers import AutoModelForCausalLM
    m = AutoModelForCausalLM.from_pretrained(
        model_name, local_files_only=not allow_download, trust_remote_code=False, dtype=dtype
    )
    m.to(device)
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--teacher-model", default="HuggingFaceTB/SmolLM2-360M-Instruct")
    parser.add_argument("--student-model", default="HuggingFaceTB/SmolLM2-135M-Instruct")
    parser.add_argument("--prompts", type=Path, default=STATES_JSONL)
    parser.add_argument("--states", type=Path, default=STATES_JSON)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--out", default=str(RESULTS / "opd_router_evaluation.json"))
    args = parser.parse_args()

    device = (
        torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "auto" else torch.device(args.device)
    )
    dtype = torch.float32

    examples = load_router_prompt_jsonl(args.prompts)
    states_payload = json.loads(args.states.read_text())
    realized = {r["example_id"]: r["evaluation"] for r in states_payload["rows"]}
    print(f"{len(examples)} prompts, {len(realized)} realized outcomes", flush=True)

    print(f"Loading teacher {args.teacher_model!r} on {device}", flush=True)
    tok = _load_tokenizer(args.teacher_model, allow_download=args.allow_download)
    teacher = _load_model(args.teacher_model, allow_download=args.allow_download,
                          device=device, dtype=dtype)
    teacher.eval()

    prompts = [render_instruction_prompt(tok, ex.state.to_prompt()) for ex in examples]

    rows = []
    t0 = time.time()
    for ex, prompt in zip(examples, prompts, strict=True):
        decision, raw = generate_router_decision(
            teacher, tok, ex.state, max_new_tokens=args.max_new_tokens
        )
        ev = realized[ex.example_id]
        routed_rho = _routed_spearman(decision, ev)
        rows.append({
            "example_id": ex.example_id,
            "split_group": ex.split_group,
            "decision": {
                "expert": decision.expert, "action": decision.action,
                "confidence": decision.confidence, "valid": decision.valid,
                "reason_codes": list(decision.reason_codes),
            },
            "raw_completion": raw[:200],
            "routed_spearman": routed_rho,
            "realized": ev,
        })
        print(f"  {ex.example_id:22s} {decision.expert:8s} {decision.action:8s} "
              f"valid={decision.valid} routed_rho={routed_rho:+.3f}", flush=True)

    valid = sum(bool(r["decision"]["valid"]) for r in rows)
    valid_frac = valid / len(rows)
    routed = [r["routed_spearman"] for r in rows]
    routed_median = float(np.median(routed))

    # best frozen single expert baseline (median over edges)
    frozen = {
        "standard": float(np.median([realized[e]["standard_spearman"] for e in realized])),
        "mhar": float(np.median([realized[e]["mhar_spearman"] for e in realized])),
        "ensemble": float(np.median([realized[e]["ensemble_spearman"] for e in realized])),
    }
    best_frozen_name, best_frozen_med = max(frozen.items(), key=lambda kv: kv[1])
    gain = routed_median - best_frozen_med

    # harm: routed edge with negative rho
    harm_routed = sum(1 for r in routed if r < 0)
    harm_best_frozen = sum(
        1 for e in realized if realized[e][f"{best_frozen_name}_spearman"] < 0
    )
    harm_rate_routed = harm_routed / len(routed)
    harm_rate_frozen = harm_best_frozen / len(realized)

    # direction regression: edges where routed is negative but best-frozen is positive
    direction_reg = sum(
        1 for r in rows
        if r["routed_spearman"] < 0 and r["realized"][f"{best_frozen_name}_spearman"] > 0
    )

    impl_gate = valid_frac >= 0.95
    sci_gate = (
        gain >= 0.02
        and direction_reg <= 0.03 * len(rows)  # at most 3% direction regressions
        and harm_rate_routed <= harm_rate_frozen
    )

    report = {
        "design": "opd-router-teacher-preflight-v1",
        "teacher": args.teacher_model,
        "wall_time_s": round(time.time() - t0, 1),
        "n_edges": len(rows),
        "implementation_gate": {
            "strict_json_valid_fraction": valid_frac,
            "minimum": 0.95,
            "passed": bool(impl_gate),
        },
        "scientific_gate": {
            "routed_median_spearman": routed_median,
            "best_frozen_single_expert": {"name": best_frozen_name, "median": best_frozen_med},
            "median_gain": gain,
            "minimum_gain": 0.02,
            "direction_regressions": direction_reg,
            "max_allowed_direction_regression": 0.03 * len(rows),
            "harm_rate_routed": harm_rate_routed,
            "harm_rate_best_frozen": harm_rate_frozen,
            "harm_must_not_increase": harm_rate_routed <= harm_rate_frozen,
            "passed": bool(sci_gate),
        },
        "frozen_baselines": frozen,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(report, indent=1))

    print(f"\n{'='*70}")
    print(f"IMPLEMENTATION GATE: valid_json={valid_frac:.3f} (>=0.95) -> {'PASS' if impl_gate else 'FAIL'}")
    print(f"SCIENTIFIC GATE:")
    print(f"  routed median rho = {routed_median:.4f}")
    print(f"  best frozen single expert = {best_frozen_name} ({best_frozen_med:.4f})")
    print(f"  median gain = {gain:+.4f} (>=0.02) -> {'PASS' if gain>=0.02 else 'FAIL'}")
    print(f"  direction regressions = {direction_reg} (<= {0.03*len(rows):.1f})")
    print(f"  harm rate routed = {harm_rate_routed:.3f} vs frozen {harm_rate_frozen:.3f}")
    print(f"  -> {'PASS' if sci_gate else 'FAIL'}")
    print(f"\nWrote {args.out}")


def _routed_spearman(decision: RouterDecision, ev: dict) -> float:
    """Apply the router's expert+action to the realized outcome.

    abstain -> 0 (no claim, no harm); predict/rank -> that expert's rho.
    Invalid decisions fail closed to abstain (0).
    """
    if not decision.valid or decision.action == "abstain":
        return 0.0
    key = f"{decision.expert}_spearman"
    return float(ev.get(key, 0.0))


if __name__ == "__main__":
    main()
