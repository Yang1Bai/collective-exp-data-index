#!/usr/bin/env python3
"""Comprehensive benchmark on the complete collective data lake.

Tests 5 methods across multiple transfer directions on alloy and catalyst data:
  1. ExtraTrees composition baseline
  2. Standard Transformer (hierarchical cross-attention)
  3. Contrastive Transformer
  4. Delta-MHAR Transformer
  5. k-NN composition interpolation

Domains:
  - SpecGen (catalyst, with spectra) — source→A/B/C/D
  - Alloy family (composition-only) — steels/MPEA/BIRDSHOT
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.data import download_pinned, load_specgen_archive
from catalyst_attention.data import SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
RESULTS_DIR = ROOT / "analysis" / "results"


def composition_matrix(samples):
    m = np.zeros((len(samples), 118), dtype=np.float32)
    for i, s in enumerate(samples):
        if len(s.elements):
            m[i, s.elements - 1] = s.fractions
    return m


def trees_baseline(source, target):
    X_src = composition_matrix(source)
    y_src = targets_array(source)
    X_tgt = composition_matrix(target)
    y_tgt = targets_array(target)

    model = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=2, max_features=0.75,
                                random_state=42, n_jobs=1)
    model.fit(X_src, y_src)
    pred = model.predict(X_tgt)
    return metrics(y_tgt, pred)


def run_method(name, source, target, model_config, training_config, device, extra_config=None):
    """Train and evaluate one method. Returns dict of metrics."""
    if extra_config:
        cfg = TrainingConfig(**{**training_config.__dict__, **extra_config})
    else:
        cfg = training_config

    model, norm, report = train_source_model(source, model_config, cfg, device=device)
    src_sp = report["source_apparent_metrics"]["spearman"]
    pred_arr = predict(model, target, norm, device=device, unknown_program=True)["mean"]
    m = metrics(targets_array(target), pred_arr)
    return {"source_spearman": src_sp, **m}


def main():
    device = torch.device("cpu")
    set_deterministic(20260802)
    t0 = time.time()

    # ---- Load data ----
    sp_path = Path("research/data/specgen.zip")
    if not sp_path.is_file():
        download_pinned(SPECGEN_URL, sp_path, SPECGEN_SHA256, SPECGEN_BYTES)

    specgen = load_specgen_archive(sp_path)
    sp_by = {}
    for s in specgen:
        sp_by.setdefault(s.program, []).append(s)

    print("Loading datasets...")
    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")
    print(f"  SpecGen source={len(sp_by['specgen_source'])} "
          f"steels={len(steels)} mpea={len(mpea)} birdshot={len(birdshot)}")

    # ---- Define experiments ----
    catalyst_cfg = CatalystAttentionConfig()
    alloy_cfg = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3,
        use_curve=False, use_conditions=False, use_surface=False,
        dropout=0.1,
    )
    train_cfg = TrainingConfig(seed=20260802, epochs=80, patience=15, batch_size=32)

    experiments = [
        # --- Catalyst domain (SpecGen) ---
        ("specgen_A", "SpecGen→A", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_A"]),
        ("specgen_C", "SpecGen→C", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_C"]),
        ("specgen_D", "SpecGen→D", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_D"]),

        # --- Alloy domain ---
        ("steel_mpea", "Steels→MPEA", alloy_cfg, steels, mpea),
        ("steel_bird", "Steels→BIRDSHOT", alloy_cfg, steels, birdshot),
        ("mpea_steel", "MPEA→Steels", alloy_cfg, mpea, steels),
        ("mpea_bird", "MPEA→BIRDSHOT", alloy_cfg, mpea, birdshot),
    ]

    all_results = {}

    for exp_id, exp_name, model_cfg, source, target in experiments:
        print(f"\n{'='*50}")
        print(f"  {exp_name}: {len(source)}→{len(target)} samples")
        print(f"{'='*50}")

        result = {"name": exp_name, "source_n": len(source), "target_n": len(target)}

        # ExtraTrees baseline.
        et = trees_baseline(source, target)
        result["extra_trees"] = et
        print(f"  ExtraTrees:          sp={et['spearman']:.4f}")

        # Standard Transformer.
        std = run_method("standard", source, target, model_cfg, train_cfg, device)
        result["standard"] = std
        print(f"  Standard Transformer: sp={std['spearman']:.4f} (src={std['source_spearman']:.3f})")

        # Contrastive.
        ct = run_method("contrastive", source, target, model_cfg, train_cfg, device,
                        extra_config={"contrastive_weight": 0.15})
        result["contrastive"] = ct
        print(f"  Contrastive:          sp={ct['spearman']:.4f} (src={ct['source_spearman']:.3f})")

        all_results[exp_id] = result

    # ---- Summary table ----
    print(f"\n\n{'='*75}")
    print(f"  COMPREHENSIVE BENCHMARK — Complete Data Lake")
    print(f"{'='*75}")
    header = f"  {'Experiment':<20s} {'ExtraTrees':>10s} {'Standard':>10s} {'Contrastive':>12s} {'Best':>8s}"
    print(header)
    print("  " + "-" * 65)

    for exp_id, exp_name, _, _, _ in experiments:
        r = all_results[exp_id]
        et_sp = r["extra_trees"]["spearman"]
        std_sp = r["standard"]["spearman"]
        ct_sp = r["contrastive"]["spearman"]
        best = max(et_sp, std_sp, ct_sp)
        best_name = "ET" if best == et_sp else ("Std" if best == std_sp else "Ct")
        print(f"  {exp_name:<20s} {et_sp:10.4f} {std_sp:10.4f} {ct_sp:12.4f} {best_name}:{best:.4f}")

    # ---- Gate check ----
    ct_gains = []
    for exp_id, _, _, _, _ in experiments:
        r = all_results[exp_id]
        ct_gains.append(r["contrastive"]["spearman"] - max(
            r["extra_trees"]["spearman"], r["standard"]["spearman"]))

    print(f"\n  Contrastive vs best baseline:")
    print(f"    Median gain: {np.median(ct_gains):+.4f}")
    print(f"    Positive: {sum(1 for g in ct_gains if g > 0)}/{len(ct_gains)}")
    print(f"    Gains: {[f'{g:+.3f}' for g in ct_gains]}")

    out = RESULTS_DIR / "comprehensive_benchmark.json"
    write_json(out, {
        "experiments": all_results,
        "aggregate": {
            "contrastive_median_gain_vs_best_baseline": float(np.median(ct_gains)),
            "positive": sum(1 for g in ct_gains if g > 0),
            "total": len(ct_gains),
            "gains": ct_gains,
        },
        "wall_time_s": round(time.time() - t0, 1),
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
