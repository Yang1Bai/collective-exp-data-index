#!/usr/bin/env python3
"""Kinetic token benchmark: test if kinetic profile features improve transfer.

Compares:
  1. Standard Transformer (baseline)
  2. Chemical-augmented Transformer
  3. Kinetic-augmented Transformer
  4. Chemical + Kinetic augmented

On SpecGen and alloy datasets.
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.chemical_features import augment_samples_with_chemistry
from catalyst_attention.kinetic_tokens import augment_with_kinetic_tokens
from catalyst_attention.data import download_pinned, load_specgen_archive
from catalyst_attention.data import SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
RESULTS_DIR = ROOT / "analysis" / "results"


def run_method(name, source, target, model_config, training_config, device,
               augment_fn=None):
    """Train and evaluate one method."""
    if augment_fn:
        source = augment_fn(source)
        target = augment_fn(target)

    model, norm, report = train_source_model(source, model_config, training_config, device=device)
    src_sp = report["source_apparent_metrics"]["spearman"]
    pred_arr = predict(model, target, norm, device=device, unknown_program=True)["mean"]
    m = metrics(targets_array(target), pred_arr)
    return {"source_spearman": src_sp, **m}


def main():
    device = torch.device("cpu")
    set_deterministic(20260802)
    t0 = time.time()

    # Load data.
    sp_path = Path("research/data/specgen.zip")
    if not sp_path.is_file():
        download_pinned(SPECGEN_URL, sp_path, SPECGEN_SHA256, SPECGEN_BYTES)

    specgen = load_specgen_archive(sp_path)
    sp_by = {}
    for s in specgen:
        sp_by.setdefault(s.program, []).append(s)

    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")

    print(f"Data: SpecGen={len(sp_by['specgen_source'])} steels={len(steels)} "
          f"mpea={len(mpea)} birdshot={len(birdshot)}")

    # Model configs.
    catalyst_cfg = CatalystAttentionConfig()
    alloy_cfg = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3,
        use_curve=False, use_conditions=True, use_surface=False, dropout=0.1,
    )
    train_cfg = TrainingConfig(seed=20260802, epochs=80, patience=15, batch_size=32)

    experiments = [
        ("specgen_A", "SpecGen→A", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_A"]),
        ("specgen_D", "SpecGen→D", catalyst_cfg,
         sp_by["specgen_source"], sp_by["specgen_D"]),
        ("steel_mpea", "Steels→MPEA", alloy_cfg, steels, mpea),
        ("steel_bird", "Steels→BIRDSHOT", alloy_cfg, steels, birdshot),
        ("mpea_steel", "MPEA→Steels", alloy_cfg, mpea, steels),
        ("mpea_bird", "MPEA→BIRDSHOT", alloy_cfg, mpea, birdshot),
    ]

    all_results = {}

    for exp_id, exp_name, model_cfg, source, target in experiments:
        print(f"\n{'='*55}")
        print(f"  {exp_name}")
        print(f"{'='*55}")

        result = {"name": exp_name}

        # 1. Standard.
        std = run_method("standard", source, target, model_cfg, train_cfg, device)
        result["standard"] = std
        print(f"  Standard:              sp={std['spearman']:.4f}")

        # 2. Chemical-augmented.
        chem = run_method("chemical", source, target, model_cfg, train_cfg, device,
                          augment_fn=augment_samples_with_chemistry)
        result["chemical"] = chem
        print(f"  Chemical-augmented:    sp={chem['spearman']:.4f} "
              f"(gain={chem['spearman']-std['spearman']:+.4f})")

        # 3. Kinetic-augmented.
        kin = run_method("kinetic", source, target, model_cfg, train_cfg, device,
                         augment_fn=augment_with_kinetic_tokens)
        result["kinetic"] = kin
        print(f"  Kinetic-augmented:     sp={kin['spearman']:.4f} "
              f"(gain={kin['spearman']-std['spearman']:+.4f})")

        # 4. Chemical + Kinetic.
        def both_augment(samples):
            return augment_with_kinetic_tokens(augment_samples_with_chemistry(samples))
        both = run_method("both", source, target, model_cfg, train_cfg, device,
                          augment_fn=both_augment)
        result["chemical_kinetic"] = both
        print(f"  Chemical+Kinetic:      sp={both['spearman']:.4f} "
              f"(gain={both['spearman']-std['spearman']:+.4f})")

        all_results[exp_id] = result

    # Summary.
    print(f"\n\n{'='*75}")
    print(f"  KINETIC TOKEN BENCHMARK")
    print(f"{'='*75}")
    header = f"  {'Experiment':<20s} {'Std':>8s} {'Chem':>8s} {'Kinetic':>8s} {'C+K':>8s} {'Best':>10s}"
    print(header)
    print("  " + "-" * 70)

    for exp_id, exp_name, _, _, _ in experiments:
        r = all_results[exp_id]
        vals = [r["standard"]["spearman"], r["chemical"]["spearman"],
                r["kinetic"]["spearman"], r["chemical_kinetic"]["spearman"]]
        best_val = max(vals)
        best_idx = vals.index(best_val)
        best_names = ["Std", "Chem", "Kin", "C+K"]
        print(f"  {exp_name:<20s} {vals[0]:8.4f} {vals[1]:8.4f} "
              f"{vals[2]:8.4f} {vals[3]:8.4f} {best_names[best_idx]}:{best_val:.4f}")

    # Count wins.
    win_counts = {n: 0 for n in ["Std", "Chem", "Kin", "C+K"]}
    for exp_id, _, _, _, _ in experiments:
        r = all_results[exp_id]
        vals = [r["standard"]["spearman"], r["chemical"]["spearman"],
                r["kinetic"]["spearman"], r["chemical_kinetic"]["spearman"]]
        best_idx = vals.index(max(vals))
        win_counts[["Std", "Chem", "Kin", "C+K"][best_idx]] += 1

    print(f"\n  Wins: {win_counts}")

    # Kinetic gains.
    kin_gains = []
    for exp_id, _, _, _, _ in experiments:
        r = all_results[exp_id]
        kin_gains.append(r["kinetic"]["spearman"] - r["standard"]["spearman"])
    print(f"  Kinetic gain vs Standard: median={np.median(kin_gains):+.4f}, "
          f"mean={np.mean(kin_gains):+.4f}")

    out = RESULTS_DIR / "kinetic_benchmark.json"
    write_json(out, {
        "experiments": all_results,
        "aggregate": {
            "win_counts": win_counts,
            "kinetic_gains": kin_gains,
            "median_kinetic_gain": float(np.median(kin_gains)),
        },
        "wall_time_s": round(time.time() - t0, 1),
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
