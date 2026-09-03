#!/usr/bin/env python3
"""Full 180-epoch benchmark: contrastive vs baseline on SpecGen + OCx24.

Runs 3 configs:
  1. Standard v1 baseline (for reference)
  2. Contrastive (best from screening)
  3. Contrastive + Delta-MHAR (combo)
  4. Contrastive + Adversarial (both losses active)

Each config trains on SpecGen source → A/B/C/D, OCx24 UofT↔VSP.
Zero-shot + few-shot (5 anchors, 20 draws) evaluation.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (
    download_pinned, load_ocx24_csv, load_specgen_archive,
    OCX24_BYTES, OCX24_SHA256, OCX24_URL,
    SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, few_shot_experiment, metrics, predict,
    set_deterministic, targets_array, train_source_model, write_json,
)

DATA_DIR = ROOT / "research" / "data"
RESULTS_DIR = ROOT / "analysis" / "results"


@dataclass
class Run:
    name: str
    edition: int
    adversarial_weight: float = 0.0
    contrastive_weight: float = 0.0
    depth_routing: str = "standard"


RUNS = [
    Run("baseline", 1),
    Run("contrastive", 2, contrastive_weight=0.1),
    Run("contrastive_mhar", 3, contrastive_weight=0.1,
        depth_routing="delta_mhar_sublayer"),
    Run("adversarial_contrastive", 4,
        adversarial_weight=0.07, contrastive_weight=0.07),
]


def eval_direction(model, source, target, normalizer, tcfg, device,
                   anchors=5, draws=20, seed=0):
    """Zero-shot + few-shot eval."""
    zs = metrics(
        targets_array(target),
        predict(model, target, normalizer, device=device, unknown_program=True)["mean"],
    )
    fs = few_shot_experiment(
        model, source, target, normalizer, tcfg,
        anchors=anchors, draws=draws, seed=seed, device=device,
    )
    return {
        "zero_shot_spearman": zs["spearman"],
        "zero_shot_rmse": zs["rmse"],
        "zero_shot_r2": zs["r2"],
        "few_shot_adapted_spearman": fs["adapted"]["spearman"]["median"],
        "few_shot_adapted_rmse": fs["adapted"]["rmse"]["median"],
        "few_shot_bias_spearman": fs["bias_calibrated_attention"]["spearman"]["median"],
        "few_shot_target_only_spearman": fs["target_only"]["spearman"]["median"],
        "few_shot_spearman_gain": fs["gains"]["spearman"]["median"],
        "few_shot_rmse_gain": fs["gains"]["relative_rmse"]["median"],
    }


def main():
    device = torch.device("cpu")
    EPOCHS = 180
    SEED = 20260802
    set_deterministic(SEED)
    t_start = time.time()

    # --- Load data ---
    sp = DATA_DIR / "specgen.zip"
    oc = DATA_DIR / "ocx24.csv"
    if not sp.is_file():
        download_pinned(SPECGEN_URL, sp, SPECGEN_SHA256, SPECGEN_BYTES)
    if not oc.is_file():
        download_pinned(OCX24_URL, oc, OCX24_SHA256, OCX24_BYTES)

    specgen = load_specgen_archive(sp)
    ocx24 = load_ocx24_csv(oc, target_name="fe_co")

    sp_by = {}; [sp_by.setdefault(s.program, []).append(s) for s in specgen]
    oc_by = {}; [oc_by.setdefault(s.program, []).append(s) for s in ocx24]

    sp_source = sp_by["specgen_source"]
    sp_targets = {p: sp_by[p] for p in ["specgen_A","specgen_B","specgen_C","specgen_D"]}
    all_target = []
    for v in sp_targets.values():
        all_target.extend(v)

    oc_pairs = [
        ("ocx24_uoft", "ocx24_vsp"),
        ("ocx24_vsp", "ocx24_uoft"),
    ]

    all_results = {}

    for run_idx, run in enumerate(RUNS):
        tag = run.name
        print(f"\n{'#'*60}")
        print(f"  RUN {run.edition}/4: {tag}")
        print(f"  adv={run.adversarial_weight} cont={run.contrastive_weight} "
              f"routing={run.depth_routing}")
        print(f"  Elapsed: {time.time()-t_start:.0f}s")
        print(f"{'#'*60}")
        t_run = time.time()

        run_result = {
            "config": {
                "adversarial_weight": run.adversarial_weight,
                "contrastive_weight": run.contrastive_weight,
                "depth_routing": run.depth_routing,
                "epochs": EPOCHS,
            },
        }

        model_cfg = CatalystAttentionConfig(depth_routing=run.depth_routing)
        train_cfg = TrainingConfig(
            seed=SEED, epochs=EPOCHS, batch_size=32,
            domain_adversarial_weight=run.adversarial_weight,
            contrastive_weight=run.contrastive_weight,
        )

        # ---- SpecGen ----
        print(f"\n  [SpecGen] Training source model ({len(sp_source)} samples)...")
        use_target = all_target if run.adversarial_weight > 0 else None
        sp_model, sp_norm, sp_report = train_source_model(
            sp_source, model_cfg, train_cfg, device=device,
            unlabeled_target_samples=use_target,
        )
        sp_model.eval()
        src_sp = sp_report["source_apparent_metrics"]["spearman"]
        val_sp = sp_report["validation_metrics"]["spearman"]
        print(f"  Source Spearman: {src_sp:.4f} (val: {val_sp:.4f}, "
              f"epochs: {sp_report['best_epoch']}/{sp_report['epochs_run']})")

        run_result["specgen_source"] = {
            "spearman": src_sp, "val_spearman": val_sp,
            "best_epoch": sp_report["best_epoch"],
        }

        sp_spearmans = []
        for prog, samples in sp_targets.items():
            d = eval_direction(
                sp_model, sp_source, samples, sp_norm,
                train_cfg, device, seed=SEED,
            )
            run_result[f"specgen_{prog}"] = d
            sp_spearmans.append(d["zero_shot_spearman"])
            print(f"  {prog}: zs={d['zero_shot_spearman']:.4f} "
                  f"fs={d['few_shot_adapted_spearman']:.4f} "
                  f"gain={d['few_shot_spearman_gain']:+.4f}")

        run_result["specgen_median_zs"] = float(np.median(sp_spearmans))

        # ---- OCx24 ----
        oc_gains = []
        for src_prog, tgt_prog in oc_pairs:
            oc_src = oc_by[src_prog]
            oc_tgt = oc_by[tgt_prog]
            oc_target_all = [s for p, ss in oc_by.items() if p != src_prog for s in ss]
            use_oc_target = oc_target_all if run.adversarial_weight > 0 else None

            print(f"\n  [OCx24] Training {src_prog} ({len(oc_src)} samples)...")
            oc_model, oc_norm, oc_report = train_source_model(
                oc_src, model_cfg, train_cfg, device=device,
                unlabeled_target_samples=use_oc_target,
            )
            oc_model.eval()
            oc_src_sp = oc_report["source_apparent_metrics"]["spearman"]
            print(f"  Source Spearman: {oc_src_sp:.4f}")

            d = eval_direction(
                oc_model, oc_src, oc_tgt, oc_norm,
                train_cfg, device, seed=SEED,
            )
            run_result[f"ocx24_{src_prog}_to_{tgt_prog}"] = d
            oc_gains.append(d["few_shot_spearman_gain"])
            print(f"  {src_prog}→{tgt_prog}: zs={d['zero_shot_spearman']:.4f} "
                  f"fs={d['few_shot_adapted_spearman']:.4f} "
                  f"gain={d['few_shot_spearman_gain']:+.4f}")

            run_result[f"ocx24_{src_prog}_source_spearman"] = oc_src_sp

        run_result["ocx24_median_gain"] = float(np.median(oc_gains))
        run_result["wall_time_s"] = round(time.time() - t_run, 1)

        all_results[tag] = run_result

        # Save intermediate.
        write_json(RESULTS_DIR / f"benchmark_{tag}.json", run_result)

    # --- Final comparison table ---
    print(f"\n\n{'='*70}")
    print(f"  FINAL COMPARISON (180 epochs, zero-shot + few-shot)")
    print(f"{'='*70}")

    header = f"{'Method':<30} {'SrcSp':>6} {'A':>7} {'B':>7} {'C':>7} {'D':>7} {'medZS':>7} {'medFSGain':>9} {'OC24Gain':>9}"
    print(header)
    print("-" * len(header))

    rows = []
    for name, r in all_results.items():
        a = r.get("specgen_specgen_A", {}).get("zero_shot_spearman", 0)
        b = r.get("specgen_specgen_B", {}).get("zero_shot_spearman", 0)
        c = r.get("specgen_specgen_C", {}).get("zero_shot_spearman", 0)
        d = r.get("specgen_specgen_D", {}).get("zero_shot_spearman", 0)
        med_zs = float(np.median([a, b, c, d]))
        sp_gains = [
            r.get(f"specgen_{p}", {}).get("few_shot_spearman_gain", 0)
            for p in ["specgen_A","specgen_B","specgen_C","specgen_D"]
        ]
        med_fs_gain = float(np.median(sp_gains))
        oc_gain = r.get("ocx24_median_gain", 0)
        src = r["specgen_source"]["spearman"]
        print(f"{name:<30} {src:6.4f} {a:7.4f} {b:7.4f} {c:7.4f} {d:7.4f} {med_zs:7.4f} {med_fs_gain:+9.4f} {oc_gain:+9.4f}")
        rows.append((name, med_zs, med_fs_gain, oc_gain))

    rows.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  Ranking by median zero-shot Spearman:")
    for i, (n, sp, fs, oc) in enumerate(rows):
        print(f"  {i+1}. {n}: median zs={sp:.4f}, fs gain={fs:+.4f}, OCx24 gain={oc:+.4f}")

    # Save final.
    out = RESULTS_DIR / "benchmark_final.json"
    write_json(out, {
        "epochs": EPOCHS, "seed": SEED,
        "results": all_results,
        "comparison": [
            {"method": n, "median_zs": float(s), "median_fs_gain": float(f),
             "ocx24_median_gain": float(o)}
            for n, s, f, o in rows
        ],
        "wall_time_total_s": round(time.time() - t_start, 1),
    })
    print(f"\n  Final → {out}")
    print(f"  Total wall time: {(time.time()-t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
