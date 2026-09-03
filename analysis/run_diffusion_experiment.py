#!/usr/bin/env python3
"""Latent diffusion augmentation experiment for catalyst knowledge transfer.

Trains a conditional diffusion model on the frozen encoder's latent space,
then generates synthetic latents for under-represented target compositions.

Usage:
    python run_diffusion_experiment.py [--epochs 40] [--diffusion-epochs 200]
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (
    download_pinned, load_specgen_archive,
    SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL,
)
from catalyst_attention.latent_diffusion import (
    LatentDiffusionModel,
    CompositionConditionedDenoiser,
    augment_with_diffusion,
    extract_latents,
    generate_target_predictions,
    train_diffusion_model,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

RESULTS_DIR = ROOT / "analysis" / "results"


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--diffusion-epochs", type=int, default=200)
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--n-augment", type=int, default=8)
    args = p.parse_args()

    device = torch.device("cpu")
    set_deterministic(args.seed)
    t0 = time.time()

    # ---- Load data ----
    sp = Path("research/data/specgen.zip")
    if not sp.is_file():
        download_pinned(SPECGEN_URL, sp, SPECGEN_SHA256, SPECGEN_BYTES)
    specgen = load_specgen_archive(sp)
    by_prog = {}
    for s in specgen:
        by_prog.setdefault(s.program, []).append(s)

    source = by_prog["specgen_source"]
    targets = {p: by_prog[p] for p in ["specgen_A","specgen_B","specgen_C","specgen_D"]}

    # ---- Phase 1: Train encoder (baseline) ----
    print("=" * 60)
    print("  PHASE 1: Training encoder on source data")
    print("=" * 60)
    model_cfg = CatalystAttentionConfig()
    train_cfg = TrainingConfig(seed=args.seed, epochs=args.epochs,
                               patience=max(10, args.epochs // 6))
    model, normalizer, report = train_source_model(
        source, model_cfg, train_cfg, device=device,
    )
    src_sp = report["source_apparent_metrics"]["spearman"]
    print(f"  Source Spearman: {src_sp:.4f}")

    # ---- Baseline zero-shot predictions ----
    print("\n  Baseline zero-shot transfer:")
    baseline_results = {}
    baseline_spearmans = []
    for prog, samples in targets.items():
        pred = predict(model, samples, normalizer, device=device, unknown_program=True)["mean"]
        m = metrics(targets_array(samples), pred)
        baseline_results[prog] = m
        baseline_spearmans.append(m["spearman"])
        print(f"    {prog}: Spearman={m['spearman']:.4f}")

    # ---- Phase 2: Train diffusion on frozen latents ----
    print(f"\n{'='*60}")
    print(f"  PHASE 2: Training diffusion model ({args.diffusion_epochs} epochs)")
    print(f"{'='*60}")
    diffusion, diff_report = train_diffusion_model(
        model, source, normalizer,
        device=device, diffusion_epochs=args.diffusion_epochs,
    )
    print(f"  Diffusion loss: {diff_report['best_loss']:.6f} "
          f"(best epoch {diff_report['best_epoch']}/{diff_report['epochs_run']})")
    print(f"  Parameters: {diff_report['parameter_count']}")

    # ---- Phase 3: Evaluate diffusion-augmented transfer ----
    print(f"\n{'='*60}")
    print(f"  PHASE 3: Diffusion-augmented predictions ({args.n_augment} samples)")
    print(f"{'='*60}")

    diff_results = {}
    diff_spearmans = []

    for prog, samples in targets.items():
        mean_pred, std_pred = generate_target_predictions(
            diffusion, model, samples, normalizer,
            device=device, n_augment=args.n_augment,
        )
        m = metrics(targets_array(samples), mean_pred)
        diff_results[prog] = m
        diff_spearmans.append(m["spearman"])
        std_med = float(np.median(std_pred))
        print(f"    {prog}: Spearman={m['spearman']:.4f} "
              f"(±{std_med:.1f}, baseline={baseline_results[prog]['spearman']:.4f})")

    # ---- Compare ----
    print(f"\n{'='*60}")
    print(f"  COMPARISON: Baseline vs Diffusion-Augmented")
    print(f"{'='*60}")
    print(f"  {'Program':<12} {'Baseline':>10} {'Diffusion':>10} {'Gain':>8}")
    gains = []
    for prog in targets:
        bl = baseline_results[prog]["spearman"]
        df = diff_results[prog]["spearman"]
        gain = df - bl
        gains.append(gain)
        print(f"  {prog:<12} {bl:10.4f} {df:10.4f} {gain:+8.4f}")

    median_gain = float(np.median(gains))
    print(f"\n  Median gain: {median_gain:+.4f}")
    print(f"  Baseline median: {float(np.median(baseline_spearmans)):.4f}")
    print(f"  Diffusion median: {float(np.median(diff_spearmans)):.4f}")

    # ---- Save results ----
    out = {
        "experiment": "latent_diffusion_augmentation",
        "seed": args.seed,
        "encoder_epochs": args.epochs,
        "diffusion_epochs": args.diffusion_epochs,
        "n_augment": args.n_augment,
        "source_spearman": src_sp,
        "diffusion_report": diff_report,
        "baseline": {
            prog: baseline_results[prog] for prog in targets
        },
        "diffusion_augmented": {
            prog: diff_results[prog] for prog in targets
        },
        "comparison": {
            prog: {
                "baseline": baseline_results[prog]["spearman"],
                "diffusion": diff_results[prog]["spearman"],
                "gain": diff_results[prog]["spearman"] - baseline_results[prog]["spearman"],
            }
            for prog in targets
        },
        "aggregate": {
            "median_baseline_spearman": float(np.median(baseline_spearmans)),
            "median_diffusion_spearman": float(np.median(diff_spearmans)),
            "median_gain": median_gain,
            "positive_directions": sum(1 for g in gains if g > 0),
            "total_directions": len(gains),
        },
        "wall_time_s": round(time.time() - t0, 1),
    }

    out_path = RESULTS_DIR / "diffusion_augmentation.json"
    write_json(out_path, out)
    print(f"\n  Results → {out_path}")
    print(f"  Wall time: {out['wall_time_s']:.0f}s")


if __name__ == "__main__":
    main()
