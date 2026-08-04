#!/usr/bin/env python3
"""Adversarial domain adaptation benchmark for catalyst knowledge transfer.

Trains with gradient reversal on fused latent representations to force
the encoder to produce domain-invariant features.

Usage:
    python run_adversarial_domain_benchmark.py [--device cpu|cuda] [--epochs N]
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    download_pinned,
    load_ocx24_csv,
    load_specgen_archive,
    OCX24_BYTES,
    OCX24_SHA256,
    OCX24_URL,
    SPECGEN_BYTES,
    SPECGEN_SHA256,
    SPECGEN_URL,
)
from catalyst_attention.model import CatalystAttentionConfig  # noqa: E402
from catalyst_attention.training import (  # noqa: E402
    TrainingConfig,
    few_shot_experiment,
    metrics,
    predict,
    set_deterministic,
    targets_array,
    train_source_model,
    write_json,
)

DATA_DIR = ROOT / "research" / "data"
RESULTS_DIR = ROOT / "analysis" / "results"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Adversarial domain adaptation benchmark"
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument(
        "--adversarial-weight",
        type=float,
        default=0.1,
        help="weight of adversarial domain loss",
    )
    parser.add_argument(
        "--grl-lambda",
        type=float,
        default=1.0,
        help="gradient reversal strength",
    )
    args = parser.parse_args()

    device = torch.device(args.device)
    set_deterministic(args.seed)

    # Load data.
    specgen_path = DATA_DIR / "specgen.zip"
    ocx24_path = DATA_DIR / "ocx24.csv"
    if not specgen_path.is_file():
        download_pinned(SPECGEN_URL, specgen_path, SPECGEN_SHA256, SPECGEN_BYTES)
    if not ocx24_path.is_file():
        download_pinned(OCX24_URL, ocx24_path, OCX24_SHA256, OCX24_BYTES)
    specgen = load_specgen_archive(specgen_path)
    ocx24 = load_ocx24_csv(ocx24_path, target_name="fe_co")

    by_program: dict[str, list] = {}
    for s in specgen:
        by_program.setdefault(s.program, []).append(s)
    ocx24_by_prog: dict[str, list] = {}
    for s in ocx24:
        ocx24_by_prog.setdefault(s.program, []).append(s)

    model_config = CatalystAttentionConfig()
    training_config = TrainingConfig(
        seed=args.seed,
        epochs=args.epochs,
        domain_adversarial_weight=args.adversarial_weight,
        grl_lambda=args.grl_lambda,
    )
    baseline_config = TrainingConfig(
        seed=args.seed,
        epochs=args.epochs,
        domain_adversarial_weight=0.0,
    )

    results: dict = {
        "dataset": "specgen",
        "adversarial_weight": args.adversarial_weight,
        "grl_lambda": args.grl_lambda,
        "directions": {},
    }

    source = by_program["specgen_source"]

    for target_prog in ["specgen_A", "specgen_B", "specgen_C", "specgen_D"]:
        target = by_program[target_prog]
        print(f"\n=== SpecGen source → {target_prog} ===")

        # Train with adversarial adaptation.
        ad_model, normalizer, ad_report = train_source_model(
            source,
            model_config,
            training_config,
            device=device,
            unlabeled_target_samples=target,
        )
        ad_metrics = metrics(
            targets_array(target),
            predict(
                ad_model,
                target,
                normalizer,
                device=device,
                unknown_program=True,
            )["mean"],
        )
        print(f"  Adversarial zero-shot Spearman: {ad_metrics['spearman']:.4f}")

        # Few-shot evaluation.
        ad_few_shot = few_shot_experiment(
            ad_model,
            source,
            target,
            normalizer,
            training_config,
            anchors=5,
            draws=20,
            seed=args.seed,
            device=device,
        )

        # Train baseline (no adversarial loss) for comparison.
        bl_model, bl_normalizer, bl_report = train_source_model(
            source,
            model_config,
            baseline_config,
            device=device,
        )
        bl_metrics = metrics(
            targets_array(target),
            predict(
                bl_model,
                target,
                bl_normalizer,
                device=device,
                unknown_program=True,
            )["mean"],
        )
        print(f"  Baseline zero-shot Spearman:     {bl_metrics['spearman']:.4f}")
        print(
            f"  Gain: {ad_metrics['spearman'] - bl_metrics['spearman']:+.4f}"
        )

        results["directions"][target_prog] = {
            "adversarial": {
                "zero_shot": ad_metrics,
                "few_shot": ad_few_shot,
                "source_report": {
                    "best_epoch": ad_report["best_epoch"],
                    "source_spearman": ad_report[
                        "source_apparent_metrics"
                    ]["spearman"],
                },
            },
            "baseline": {
                "zero_shot": bl_metrics,
                "source_spearman": bl_report["source_apparent_metrics"][
                    "spearman"
                ],
            },
            "gain": ad_metrics["spearman"] - bl_metrics["spearman"],
        }

    # Aggregate.
    gains = [
        d["gain"] for d in results["directions"].values()
    ]
    results["aggregate"] = {
        "median_gain": float(np.median(gains)),
        "positive_directions": sum(1 for g in gains if g > 0),
        "total_directions": len(gains),
    }
    results["gate"] = {
        "passed": float(np.median(gains)) > 0
        and sum(1 for g in gains if g > 0) >= len(gains) // 2,
    }

    out = RESULTS_DIR / "adversarial_domain_benchmark.json"
    write_json(out, results)
    print(f"\n=== Results → {out} ===")
    print(f"Median gain: {results['aggregate']['median_gain']:+.4f}")
    print(f"Positive: {results['aggregate']['positive_directions']}/"
          f"{results['aggregate']['total_directions']}")


if __name__ == "__main__":
    main()
