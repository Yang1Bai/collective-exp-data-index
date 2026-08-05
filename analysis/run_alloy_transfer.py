#!/usr/bin/env python3
"""Cross-alloy-family knowledge transfer screening.

Tests Contrastive vs Baseline (Standard v1) on three alloy datasets:
  matbench-steels (312 steels, 13 elements)  →  Fe-based
  mpea-dataset-borg (395 compositions, 5+ elements)  →  multi-principal
  birdshot-HEA (151 compositions, 5+ elements)  →  high-entropy

Transfer directions:
  1. steels → MPEA (yield strength)
  2. steels → BIRDSHOT (yield strength)
  3. MPEA → steels (yield strength)
  4. MPEA → BIRDSHOT (yield strength)

Composition-only model: use_curve=False, use_conditions=False, use_surface=False.
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
RESULTS_DIR = ROOT / "analysis" / "results"


def evaluate_transfer(model, source, target, normalizer, device):
    """Zero-shot only for composition-only transfer."""
    zs_pred = predict(model, target, normalizer, device=device, unknown_program=True)["mean"]
    zs = metrics(targets_array(target), zs_pred)
    return {
        "zero_shot_spearman": zs["spearman"],
        "zero_shot_rmse": zs["rmse"],
        "zero_shot_mae": zs["mae"],
        "zero_shot_r2": zs["r2"],
    }


def main():
    device = torch.device("cpu")
    set_deterministic(20260802)
    t0 = time.time()

    # Load all alloy datasets.
    print("Loading alloy datasets...")
    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")

    for name, data in [("steels", steels), ("mpea", mpea), ("birdshot", birdshot)]:
        targets = [s.target for s in data if s.target is not None]
        print(f"  {name}: {len(data)} samples, "
              f"target mean={np.mean(targets):.1f} std={np.std(targets):.1f}")

    # Transfer pairs.
    pairs = [
        ("steels→MPEA", steels, mpea),
        ("steels→BIRDSHOT", steels, birdshot),
        ("MPEA→steels", mpea, steels),
        ("MPEA→BIRDSHOT", mpea, birdshot),
    ]

    # Composition-only model config.
    model_config = CatalystAttentionConfig(
        d_model=48, n_heads=4,
        composition_layers=3,
        curve_layers=1,
        fusion_layers=1,
        feedforward_multiplier=3,
        use_curve=False,
        use_conditions=False,
        use_surface=False,
        dropout=0.1,
    )

    training_config = TrainingConfig(
        seed=20260802, epochs=100, patience=20,
        batch_size=32, learning_rate=8e-4,
        rank_weight=0.15, nll_weight=0.10,
    )
    ct_training_config = TrainingConfig(
        seed=20260802, epochs=100, patience=20,
        batch_size=32, learning_rate=8e-4,
        rank_weight=0.15, nll_weight=0.10,
        contrastive_weight=0.2,
    )

    all_results = {"pairs": {}, "aggregate": {}}

    for pair_name, source_data, target_data in pairs:
        print(f"\n{'='*60}")
        print(f"  {pair_name}")
        print(f"{'='*60}")

        # ---- Baseline ----
        print(f"  Training baseline ({len(source_data)} samples)...")
        bl_model, bl_norm, bl_report = train_source_model(
            source_data, model_config, training_config, device=device,
        )
        bl_src = bl_report["source_apparent_metrics"]["spearman"]
        bl_result = evaluate_transfer(bl_model, source_data, target_data, bl_norm, device)
        print(f"  Baseline: src_sp={bl_src:.4f} "
              f"zs={bl_result['zero_shot_spearman']:.4f}")

        # ---- Contrastive ----
        print(f"  Training contrastive...")
        ct_model, ct_norm, ct_report = train_source_model(
            source_data, model_config, ct_training_config, device=device,
        )
        ct_src = ct_report["source_apparent_metrics"]["spearman"]
        ct_result = evaluate_transfer(ct_model, source_data, target_data, ct_norm, device)
        print(f"  Contrastive: src_sp={ct_src:.4f} "
              f"zs={ct_result['zero_shot_spearman']:.4f}")

        all_results["pairs"][pair_name] = {
            "source_samples": len(source_data),
            "target_samples": len(target_data),
            "baseline": bl_result,
            "contrastive": ct_result,
            "gain_vs_baseline": ct_result["zero_shot_spearman"] - bl_result["zero_shot_spearman"],
        }

    # ---- Aggregate ----
    gains = [p["gain_vs_baseline"] for p in all_results["pairs"].values()]
    all_results["aggregate"] = {
        "median_gain": float(np.median(gains)),
        "mean_gain": float(np.mean(gains)),
        "positive_directions": sum(1 for g in gains if g > 0),
        "total_directions": len(gains),
        "gains": gains,
        "wall_time_s": round(time.time() - t0, 1),
    }

    # Print comparison.
    print(f"\n{'='*65}")
    print(f"  ALLOY TRANSFER RESULTS (yield strength, zero-shot)")
    print(f"{'='*65}")
    print(f"  {'Direction':<20s} {'Baseline':>10s} {'Contrastive':>12s} {'Gain':>8s}")
    for name, p in all_results["pairs"].items():
        bl = p["baseline"]["zero_shot_spearman"]
        ct = p["contrastive"]["zero_shot_spearman"]
        gain = p["gain_vs_baseline"]
        print(f"  {name:<20s} {bl:10.4f} {ct:12.4f} {gain:+8.4f}")

    print(f"\n  Median gain: {all_results['aggregate']['median_gain']:+.4f}")
    print(f"  Positive: {all_results['aggregate']['positive_directions']}/"
          f"{all_results['aggregate']['total_directions']}")

    out = RESULTS_DIR / "alloy_transfer.json"
    write_json(out, all_results)
    print(f"\n  Results → {out}")
    print(f"  Wall time: {all_results['aggregate']['wall_time_s']:.0f}s")


if __name__ == "__main__":
    main()
