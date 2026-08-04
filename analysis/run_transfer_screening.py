#!/usr/bin/env python3
"""Unified screening: test all knowledge-transfer methods and combinations.

Tests 8 configurations on SpecGen source→A/B/C/D transfer:
  1. baseline (Standard v1)
  2. adversarial domain adaptation
  3. contrastive representation learning
  4. pairwise element encoder
  5. adversarial + contrastive
  6. adversarial + pairwise
  7. contrastive + pairwise
  8. adversarial + contrastive + pairwise (full pipeline)

Uses reduced epochs for screening. Full benchmark separately.
Output: analysis/results/transfer_screening.json
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    CatalystSample,
    download_pinned,
    load_specgen_archive,
    SPECGEN_BYTES,
    SPECGEN_SHA256,
    SPECGEN_URL,
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

DATA_DIR = ROOT / "research" / "data"
RESULTS_DIR = ROOT / "analysis" / "results"


@dataclass
class MethodSpec:
    name: str
    description: str
    adversarial_weight: float = 0.0
    contrastive_weight: float = 0.0
    grl_lambda: float = 1.0
    contrastive_temperature: float = 0.1
    composition_mode: str = "set_query"
    depth_routing: str = "standard"


METHODS = [
    MethodSpec(
        "baseline",
        "Standard hierarchical cross-attention v1",
    ),
    MethodSpec(
        "adversarial",
        "Gradient reversal domain adaptation",
        adversarial_weight=0.1,
    ),
    MethodSpec(
        "contrastive",
        "Composition-structured contrastive learning",
        contrastive_weight=0.1,
    ),
    MethodSpec(
        "pairwise",
        "Pairwise element interaction encoder",
        composition_mode="pairwise",
    ),
    MethodSpec(
        "adversarial_contrastive",
        "Adversarial + contrastive combined",
        adversarial_weight=0.08,
        contrastive_weight=0.08,
    ),
    MethodSpec(
        "adversarial_pairwise",
        "Adversarial + pairwise encoder",
        adversarial_weight=0.1,
        composition_mode="pairwise",
    ),
    MethodSpec(
        "contrastive_pairwise",
        "Contrastive + pairwise encoder",
        contrastive_weight=0.1,
        composition_mode="pairwise",
    ),
    MethodSpec(
        "full_pipeline",
        "Adversarial + contrastive + pairwise (all combined)",
        adversarial_weight=0.07,
        contrastive_weight=0.07,
        composition_mode="pairwise",
    ),
]


def evaluate_transfer(
    model: torch.nn.Module,
    source_samples: Sequence[CatalystSample],
    target_samples: Sequence[CatalystSample],
    normalizer,
    device: torch.device,
    *,
    with_adaptation: bool = True,
    anchors: int = 5,
    draws: int = 10,
    seed: int = 0,
    training_config: TrainingConfig | None = None,
) -> dict:
    """Evaluate zero-shot and few-shot transfer to a target programme."""
    from catalyst_attention.training import (
        calibrate_support,
        few_shot_experiment,
    )

    result: dict = {}

    # Zero-shot.
    zero_pred = predict(
        model,
        target_samples,
        normalizer,
        device=device,
        unknown_program=True,
    )["mean"]
    zero_metrics = metrics(targets_array(target_samples), zero_pred)
    result["zero_shot"] = zero_metrics

    if with_adaptation and training_config is not None:
        support_calibrator = calibrate_support(
            model, source_samples, normalizer, device=device,
            batch_size=training_config.batch_size,
        )
        few_shot = few_shot_experiment(
            model,
            source_samples,
            target_samples,
            normalizer,
            training_config,
            anchors=anchors,
            draws=draws,
            seed=seed,
            device=device,
        )
        result["few_shot"] = {
            "adapted_spearman": few_shot["adapted"]["spearman"]["median"],
            "adapted_spearman_ci90": few_shot["adapted"]["spearman"]["ci90"],
            "bias_calibrated_spearman": few_shot["bias_calibrated_attention"]["spearman"]["median"],
            "target_only_spearman": few_shot["target_only"]["spearman"]["median"],
            "gain_vs_target_only": few_shot["gains"]["spearman"]["median"],
        }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Transfer method screening")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=40,
                        help="reduced epochs for quick screening")
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--draws", type=int, default=10)
    parser.add_argument("--anchors", type=int, default=5)
    parser.add_argument("--skip-adaptation", action="store_true",
                        help="skip few-shot adaptation to save time")
    args = parser.parse_args()

    device = torch.device(args.device)
    set_deterministic(args.seed)
    t0 = time.time()

    # --- Load data ---
    specgen_path = DATA_DIR / "specgen.zip"
    if not specgen_path.is_file():
        print("Downloading SpecGen ...")
        download_pinned(SPECGEN_URL, specgen_path, SPECGEN_SHA256, SPECGEN_BYTES)
    all_samples = load_specgen_archive(specgen_path)

    by_program: dict[str, list[CatalystSample]] = {}
    for s in all_samples:
        by_program.setdefault(s.program, []).append(s)

    source_samples = by_program["specgen_source"]
    target_programmes = ["specgen_A", "specgen_B", "specgen_C", "specgen_D"]
    print(f"Source: {len(source_samples)} samples")
    for p in target_programmes:
        print(f"  Target {p}: {len(by_program[p])} samples")

    # --- Run all methods ---
    results: dict = {
        "screening_config": {
            "epochs": args.epochs,
            "seed": args.seed,
            "draws": args.draws,
            "anchors": args.anchors,
            "adaptation_enabled": not args.skip_adaptation,
        },
        "methods": {},
        "aggregate": {},
    }

    for method in METHODS:
        tag = method.name
        print(f"\n{'='*60}")
        print(f"  {tag}: {method.description}")
        print(f"{'='*60}")
        t_method = time.time()

        try:
            base_model_config = CatalystAttentionConfig(
                composition_mode=method.composition_mode,
                depth_routing=method.depth_routing,
            )
        except (ValueError, KeyError) as e:
            print(f"  SKIP: invalid config ({e})")
            results["methods"][tag] = {"error": str(e), "status": "skipped"}
            continue

        training_config = TrainingConfig(
            seed=args.seed,
            epochs=args.epochs,
            patience=max(10, args.epochs // 6),
            batch_size=32,
            domain_adversarial_weight=method.adversarial_weight,
            contrastive_weight=method.contrastive_weight,
            grl_lambda=method.grl_lambda,
            contrastive_temperature=method.contrastive_temperature,
        )

        method_result: dict = {
            "description": method.description,
            "config": {
                "adversarial_weight": method.adversarial_weight,
                "contrastive_weight": method.contrastive_weight,
                "composition_mode": method.composition_mode,
                "depth_routing": method.depth_routing,
            },
            "directions": {},
        }

        # Train source model.
        model, normalizer, report = train_source_model(
            source_samples,
            base_model_config,
            training_config,
            device=device,
        )
        method_result["source"] = {
            "best_epoch": report["best_epoch"],
            "source_spearman": report["source_apparent_metrics"]["spearman"],
            "validation_spearman": report["validation_metrics"]["spearman"],
            "parameter_count": report["parameter_count"],
        }
        print(f"  Source Spearman: {report['source_apparent_metrics']['spearman']:.4f} "
              f"(val: {report['validation_metrics']['spearman']:.4f}, "
              f"epochs: {report['best_epoch']}/{report['epochs_run']})")

        # Evaluate transfer to each target programme.
        transfer_spearmans = []
        for target_prog in target_programmes:
            target_samples = by_program[target_prog]
            transfer = evaluate_transfer(
                model,
                source_samples,
                target_samples,
                normalizer,
                device,
                with_adaptation=not args.skip_adaptation,
                anchors=args.anchors,
                draws=args.draws,
                seed=args.seed,
                training_config=training_config,
            )
            method_result["directions"][target_prog] = transfer
            zs_sp = transfer["zero_shot"]["spearman"]
            transfer_spearmans.append(zs_sp)
            fs_str = ""
            if "few_shot" in transfer:
                fs_str = (f" few-shot: {transfer['few_shot']['adapted_spearman']:.4f} "
                          f"(gain={transfer['few_shot']['gain_vs_target_only']:+.4f})")
            print(f"  {target_prog}: zero-shot Spearman={zs_sp:.4f}{fs_str}")

        # Per-method aggregate.
        baseline_spearmans = None
        if "baseline" in results["methods"]:
            bl_dirs = results["methods"]["baseline"]["directions"]
            baseline_spearmans = [
                bl_dirs[p]["zero_shot"]["spearman"] for p in target_programmes
            ]

        method_result["aggregate"] = {
            "median_transfer_spearman": float(np.median(transfer_spearmans)),
            "mean_transfer_spearman": float(np.mean(transfer_spearmans)),
            "transfer_spearmans": transfer_spearmans,
        }
        if baseline_spearmans:
            gains = [
                t - b for t, b in zip(transfer_spearmans, baseline_spearmans)
            ]
            method_result["aggregate"]["median_gain_vs_baseline"] = float(np.median(gains))
            method_result["aggregate"]["positive_directions"] = sum(1 for g in gains if g > 0)
            method_result["aggregate"]["all_gains"] = gains

        elapsed = time.time() - t_method
        method_result["wall_time_seconds"] = round(elapsed, 1)
        results["methods"][tag] = method_result
        print(f"  Wall time: {elapsed:.0f}s")

    # --- Cross-method comparison ---
    comparison = []
    for name, m in results["methods"].items():
        if "aggregate" not in m or "median_transfer_spearman" not in m["aggregate"]:
            comparison.append({"method": name, "median_spearman": None, "error": m.get("error")})
            continue
        comp = {
            "method": name,
            "median_spearman": m["aggregate"]["median_transfer_spearman"],
            "source_spearman": m["source"]["source_spearman"],
            "median_gain_vs_baseline": m["aggregate"].get("median_gain_vs_baseline"),
            "positive_directions": m["aggregate"].get("positive_directions"),
        }
        comparison.append(comp)

    comparison.sort(
        key=lambda x: x["median_spearman"] if x["median_spearman"] is not None else -999,
        reverse=True,
    )
    results["aggregate"]["comparison"] = comparison
    results["aggregate"]["wall_time_total_seconds"] = round(time.time() - t0, 1)

    # Find best method.
    best = comparison[0] if comparison else None
    if best:
        print(f"\n{'='*60}")
        print(f"  Ranking (by median transfer Spearman):")
        for i, row in enumerate(comparison):
            gain_str = ""
            if row.get("median_gain_vs_baseline") is not None:
                gain_str = f" gain={row['median_gain_vs_baseline']:+.4f}"
                pos = row.get("positive_directions", "?")
                gain_str += f" ({pos}/4 positive)"
            print(f"  {i+1}. {row['method']:30s} "
                  f"Spearman={row['median_spearman']:.4f}{gain_str}")
        results["aggregate"]["best_method"] = best["method"]

    # Write results.
    out_path = RESULTS_DIR / "transfer_screening.json"
    write_json(out_path, results)
    print(f"\n  Results → {out_path}")
    print(f"  Total wall time: {results['aggregate']['wall_time_total_seconds']:.0f}s")


if __name__ == "__main__":
    main()
