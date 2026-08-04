#!/usr/bin/env python3
"""Round 2 screening: properly test adversarial (with target samples),
Delta-MHAR variants, and winning combinations from round 1.

Tests 7 configurations (adding to round 1 comparison):
  1. Delta-MHAR baseline
  2. adversarial+target (properly with unlabeled target samples)
  3. contrastive + Delta-MHAR (best combo hypothesis)
  4. adversarial+contrastive + Delta-MHAR (full combo)
  5-7: Retry pairwise with reduced epochs just to confirm it's dead
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    CatalystSample,
    download_pinned,
    load_specgen_archive,
    SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL,
)
from catalyst_attention.model import CatalystAttentionConfig  # noqa: E402
from catalyst_attention.training import (  # noqa: E402
    TrainingConfig,
    metrics,
    predict,
    set_deterministic,
    targets_array,
    train_source_model,
    write_json,
)

RESULTS_DIR = ROOT / "analysis" / "results"


def evaluate_zero_shot(model, samples, normalizer, device):
    pred = predict(model, samples, normalizer, device=device, unknown_program=True)["mean"]
    return metrics(targets_array(samples), pred)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260802)
    args = parser.parse_args()

    device = torch.device("cpu")
    set_deterministic(args.seed)
    t0 = time.time()

    specgen_path = Path("research/data/specgen.zip")
    if not specgen_path.is_file():
        download_pinned(SPECGEN_URL, specgen_path, SPECGEN_SHA256, SPECGEN_BYTES)
    all_samples = load_specgen_archive(specgen_path)

    by_prog = {}
    for s in all_samples:
        by_prog.setdefault(s.program, []).append(s)

    source = by_prog["specgen_source"]
    targets = {p: by_prog[p] for p in ["specgen_A", "specgen_B", "specgen_C", "specgen_D"]}
    # Combine all target samples for adversarial training.
    all_target = []
    for ts in targets.values():
        all_target.extend(ts)
    print(f"Source: {len(source)}, Combined targets: {len(all_target)}")

    configs = [
        {
            "name": "delta_mhar",
            "desc": "Delta-MHAR sublayer routing (no additional loss)",
            "composition_mode": "set_query",
            "depth_routing": "delta_mhar_sublayer",
            "adversarial_weight": 0.0,
            "contrastive_weight": 0.0,
            "use_target": False,
        },
        {
            "name": "adversarial_with_target",
            "desc": "Adversarial GRP properly with target samples",
            "composition_mode": "set_query",
            "depth_routing": "standard",
            "adversarial_weight": 0.1,
            "contrastive_weight": 0.0,
            "use_target": True,
        },
        {
            "name": "contrastive_delta_mhar",
            "desc": "Contrastive + Delta-MHAR (best combo hypothesis)",
            "composition_mode": "set_query",
            "depth_routing": "delta_mhar_sublayer",
            "adversarial_weight": 0.0,
            "contrastive_weight": 0.1,
            "use_target": False,
        },
        {
            "name": "adv_contrastive_delta_mhar",
            "desc": "Adversarial + Contrastive + Delta-MHAR (full combo)",
            "composition_mode": "set_query",
            "depth_routing": "delta_mhar_sublayer",
            "adversarial_weight": 0.07,
            "contrastive_weight": 0.07,
            "use_target": True,
        },
    ]

    all_results = {}

    for cfg in configs:
        name = cfg["name"]
        print(f"\n{'='*50}")
        print(f"  {name}: {cfg['desc']}")
        print(f"{'='*50}")

        model_config = CatalystAttentionConfig(
            composition_mode=cfg["composition_mode"],
            depth_routing=cfg["depth_routing"],
        )
        training_config = TrainingConfig(
            seed=args.seed,
            epochs=args.epochs,
            patience=max(10, args.epochs // 6),
            batch_size=32,
            domain_adversarial_weight=cfg["adversarial_weight"],
            contrastive_weight=cfg["contrastive_weight"],
        )

        unlabeled = all_target if cfg["use_target"] else None
        try:
            model, normalizer, report = train_source_model(
                source, model_config, training_config,
                device=device, unlabeled_target_samples=unlabeled,
            )
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[name] = {"error": str(e)}
            continue

        src_sp = report["source_apparent_metrics"]["spearman"]
        print(f"  Source Spearman: {src_sp:.4f} (val: {report['validation_metrics']['spearman']:.4f})")

        direction_results = {}
        spearmans = []
        for prog, samples in targets.items():
            m = evaluate_zero_shot(model, samples, normalizer, device)
            direction_results[prog] = m
            spearmans.append(m["spearman"])
            print(f"  {prog}: Spearman={m['spearman']:.4f}")

        all_results[name] = {
            "description": cfg["desc"],
            "source_spearman": src_sp,
            "directions": direction_results,
            "median_transfer_spearman": float(np.median(spearmans)),
            "mean_transfer_spearman": float(np.mean(spearmans)),
            "spearmans": spearmans,
            "wall_time": round(time.time() - t0, 1),
        }

    # Print ranking.
    print(f"\n{'='*60}")
    print("  ROUND 2 RANKING")
    print(f"{'='*60}")
    # Merge with round 1 baseline.
    round1_baseline = 0.5837
    ranking = []
    for name, r in all_results.items():
        if "median_transfer_spearman" in r:
            ranking.append((name, r["median_transfer_spearman"], r))
    ranking.sort(key=lambda x: x[1], reverse=True)

    for i, (name, sp, r) in enumerate(ranking):
        gain = sp - round1_baseline
        print(f"  {i+1}. {name:30s} Spearman={sp:.4f} (gain={gain:+.4f})")

    # Save.
    out = RESULTS_DIR / "transfer_screening_round2.json"
    write_json(out, {
        "configs_tested": configs,
        "round1_baseline_median": round1_baseline,
        "results": all_results,
        "ranking": [{"name": n, "spearman": s} for n, s, _ in ranking],
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
