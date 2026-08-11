#!/usr/bin/env python3
"""Compare decision-layer policies on the frozen benchmark artifact.

Reads ``policy_transfer_benchmark.json`` (representation rows + edge
geometry), then evaluates four decision policies on the identical closed
edge set:

1. frozen threshold rules (a-priori baseline)
2. learned GBM policy, leave-one-pair-out
3. LLM policy, replayed from a pinned decisions artifact
4. always-transfer / always-abstain anchors

Outputs ``policy_comparison.json`` and a console table. Also exports the
LLM prompt file (``llm_policy_prompts.json``) when decisions are missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.learned_policy import (  # noqa: E402
    evaluate_llm_policy,
    export_llm_prompts,
    learned_policy_lopo,
    load_llm_policy,
)
from catalyst_attention.policy_transfer import (  # noqa: E402
    FrozenThresholdPolicy,
    TransferEdgeState,
    always_transfer_baseline,
    evaluate_policy,
    result_manifest,
)

RESULTS = ROOT / "analysis" / "results"


def states_from_benchmark(payload: dict) -> tuple[list[TransferEdgeState], dict]:
    states, realized = [], {}
    for edge in payload["policy"]["edges"]:
        s = edge["state"]
        states.append(TransferEdgeState(
            pair_name=s["pair_name"], method=s["method"],
            source_n=s["source_n"], target_n=s["target_n"],
            source_fit_spearman=s["source_fit_spearman"],
            coverage=s["coverage"], mean_min_distance=s["mean_min_distance"],
            donor_family=s["donor_family"], recipient_family=s["recipient_family"],
            feature_richness=s["feature_richness"],
        ))
        realized[(s["pair_name"], s["method"])] = edge["target_spearman"]
    return states, realized


def _statistics(rows, frozen, learned, llm_manifest, naive):
    """Paired bootstrap (policy minus always-transfer) + harm accounting."""
    rng = np.random.default_rng(20260810)
    stats = {}
    manifests = {"frozen_threshold": frozen, "learned_gbm_lopo": learned}
    for name, result in manifests.items():
        realized = np.array([
            e.target_spearman if e.decision == "apply" else 0.0 for e in result.edges
        ])
        naive_scores = np.array([e.target_spearman for e in result.edges])
        diffs = np.array([
            realized[idx].mean() - naive_scores[idx].mean()
            for idx in rng.integers(0, len(realized), (20000, len(realized)))
        ])
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        stats[name] = {
            "delta_mean_vs_always_transfer": float(realized.mean() - naive_scores.mean()),
            "ci95": [float(lo), float(hi)],
            "p_delta_positive": float(np.mean(diffs > 0)),
        }
    # harm rate over claimed (apply+rank_only) edges and apply precision
    for name, summary in rows.items():
        if name not in stats:
            stats[name] = {}
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default=str(RESULTS / "policy_transfer_benchmark.json"))
    parser.add_argument("--llm-decisions", default=str(RESULTS / "llm_policy_decisions.json"))
    parser.add_argument("--out", default=str(RESULTS / "policy_comparison.json"))
    args = parser.parse_args()

    payload = json.loads(Path(args.benchmark).read_text())
    states, realized = states_from_benchmark(payload)
    print(f"{len(states)} edge-decisions over {len({s.pair_name for s in states})} pairs")

    rows = {}

    frozen = evaluate_policy(FrozenThresholdPolicy(), states, realized)
    rows["frozen_threshold"] = frozen.summary()

    learned = learned_policy_lopo(states, realized)
    rows["learned_gbm_lopo"] = learned.summary()

    llm_path = Path(args.llm_decisions)
    if llm_path.exists():
        llm = evaluate_llm_policy(load_llm_policy(llm_path), states, realized)
        rows["llm_policy"] = llm.summary()
        llm_manifest = result_manifest(llm)
    else:
        export_llm_prompts(states, RESULTS / "llm_policy_prompts.json")
        print(f"LLM decisions missing; exported prompts to {RESULTS / 'llm_policy_prompts.json'}")
        llm_manifest = None

    naive = always_transfer_baseline(states, realized)
    rows["always_transfer"] = naive.summary()
    rows["always_abstain"] = {
        "mean_realized_spearman": 0.0, "harm_edges": 0,
        "missed_positive_edges": sum(1 for s in states if realized[(s.pair_name, s.method)] > 0.3),
    }

    out = {
        "design": "policy-comparison-v1",
        "n_states": len(states),
        "policies": rows,
        "statistics": _statistics(rows, frozen, learned, llm_manifest, naive),
        "frozen_manifest": result_manifest(frozen),
        "learned_manifest": result_manifest(learned),
        "llm_manifest": llm_manifest,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))

    print(f"\n{'policy':22s} {'mean_rho':>9s} {'harm':>5s} {'miss':>5s} {'apply':>6s} {'rank':>6s} {'abst':>6s}")
    for name, s in rows.items():
        if name == "always_abstain":
            print(f"{name:22s} {s['mean_realized_spearman']:9.3f} {s['harm_edges']:5d} "
                  f"{s['missed_positive_edges']:5d} {'—':>6s} {'—':>6s} {'—':>6s}")
        else:
            print(f"{name:22s} {s['mean_realized_spearman']:9.3f} {s['harm_edges']:5d} "
                  f"{s['missed_positive_edges']:5d} {s['n_apply']:6d} {s['n_rank_only']:6d} {s['n_abstain']:6d}")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
