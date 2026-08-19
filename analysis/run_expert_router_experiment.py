#!/usr/bin/env python3
"""Expert router experiment: train Standard/MHAR pairs and evaluate routing.

Usage:
    python run_expert_router_experiment.py [--device cpu|cuda] [--epochs N] [--draws N]

Output:
    analysis/results/expert_router_screening.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    CatalystSample,
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
from catalyst_attention.expert_router import (  # noqa: E402
    ExpertPair,
    evaluate_router,
    train_expert_pair,
)
from catalyst_attention.model import CatalystAttentionConfig  # noqa: E402
from catalyst_attention.training import (  # noqa: E402
    TrainingConfig,
    set_deterministic,
    write_json,
)

DATA_DIR = ROOT / "research" / "data"
RESULTS_DIR = ROOT / "analysis" / "results"


def _prepare_data() -> tuple[
    dict[str, list[CatalystSample]],
    dict[str, list[CatalystSample]],
]:
    """Download (if needed) and load SpecGen and OCx24 datasets."""
    specgen_path = DATA_DIR / "specgen.zip"
    ocx24_path = DATA_DIR / "ocx24.csv"

    if not specgen_path.is_file():
        print(f"Downloading SpecGen archive to {specgen_path} ...")
        specgen_path.parent.mkdir(parents=True, exist_ok=True)
        download_pinned(
            SPECGEN_URL,
            specgen_path,
            SPECGEN_SHA256,
            SPECGEN_BYTES,
        )
    specgen_samples = load_specgen_archive(specgen_path)

    if not ocx24_path.is_file():
        print(f"Downloading OCx24 CSV to {ocx24_path} ...")
        ocx24_path.parent.mkdir(parents=True, exist_ok=True)
        download_pinned(
            OCX24_URL,
            ocx24_path,
            OCX24_SHA256,
            OCX24_BYTES,
        )
    ocx24_fe_co = load_ocx24_csv(ocx24_path, target_name="fe_co")

    # Partition by programme.
    specgen_by_program: dict[str, list[CatalystSample]] = {}
    for sample in specgen_samples:
        specgen_by_program.setdefault(sample.program, []).append(sample)

    ocx24_by_program: dict[str, list[CatalystSample]] = {}
    for sample in ocx24_fe_co:
        ocx24_by_program.setdefault(sample.program, []).append(sample)

    return specgen_by_program, ocx24_by_program


def _transfer_directions(
    by_program: dict[str, list[CatalystSample]],
    source_program: str,
) -> list[tuple[str, list[CatalystSample]]]:
    """List target programmes for a given source."""
    return [
        (prog, samples)
        for prog, samples in sorted(by_program.items())
        if prog != source_program
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expert router screening experiment"
    )
    parser.add_argument(
        "--device", default="cpu", help="torch device (cpu or cuda)"
    )
    parser.add_argument(
        "--epochs", type=int, default=180, help="source training epochs"
    )
    parser.add_argument(
        "--draws", type=int, default=20, help="few-shot draws per direction"
    )
    parser.add_argument(
        "--anchors", type=int, default=5, help="few-shot anchor budget"
    )
    parser.add_argument(
        "--seed", type=int, default=20260801, help="base random seed"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="skip training and use existing checkpoints",
    )
    parser.add_argument(
        "--checkpoint-dir",
        default=str(ROOT / "analysis" / "checkpoints"),
        help="directory for expert pair checkpoints",
    )
    args = parser.parse_args()

    device = torch.device(args.device)
    set_deterministic(args.seed)

    print("=== Loading datasets ===")
    specgen_by_program, ocx24_by_program = _prepare_data()

    model_config = CatalystAttentionConfig(
        d_model=64,
        n_heads=4,
        composition_layers=2,
        curve_layers=3,
        condition_layers=1,
        fusion_layers=1,
        fusion_queries=4,
        dropout=0.12,
    )
    training_config = TrainingConfig(
        seed=args.seed,
        epochs=args.epochs,
        batch_size=32,
    )

    # --- SpecGen transfer ---
    specgen_source = specgen_by_program["specgen_source"]
    specgen_targets = _transfer_directions(
        specgen_by_program, "specgen_source"
    )

    print(f"\n=== Training expert pair on SpecGen source ===")
    print(f"  Source samples: {len(specgen_source)}")
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    specgen_pair = train_expert_pair(
        specgen_source,
        model_config,
        training_config,
        device=device,
    )
    print(
        f"  Standard source Spearman: "
        f"{specgen_pair.standard_report['source_apparent_metrics']['spearman']:.4f}"
    )
    print(
        f"  MHAR source Spearman:     "
        f"{specgen_pair.mhar_report['source_apparent_metrics']['spearman']:.4f}"
    )

    specgen_results: dict[str, dict] = {}
    for target_prog, target_samples in specgen_targets:
        print(f"\n  --- SpecGen source → {target_prog} ---")
        print(f"  Target samples: {len(target_samples)}")
        result = evaluate_router(
            specgen_pair,
            specgen_source,
            target_samples,
            training_config,
            anchors=args.anchors,
            draws=args.draws,
            seed=args.seed,
            device=device,
        )
        specgen_results[target_prog] = result
        decision = result["decision"]
        print(
            f"  Best strategy: {decision['best_strategy']} "
            f"(gain={decision['best_median_gain_over_single_expert']:+.4f}, "
            f"beats_both={decision['beats_both_single_experts']})"
        )

    # --- OCx24 transfer ---
    ocx24_sources = ["ocx24_uoft", "ocx24_vsp"]
    ocx24_pairs: dict[str, ExpertPair] = {}
    ocx24_results: dict[str, dict[str, dict]] = {}

    for source_prog in ocx24_sources:
        source_samples = ocx24_by_program[source_prog]
        targets = _transfer_directions(ocx24_by_program, source_prog)

        print(f"\n=== Training expert pair on OCx24 {source_prog} ===")
        print(f"  Source samples: {len(source_samples)}")

        pair = train_expert_pair(
            source_samples,
            model_config,
            training_config,
            device=device,
        )
        ocx24_pairs[source_prog] = pair
        print(
            f"  Standard source Spearman: "
            f"{pair.standard_report['source_apparent_metrics']['spearman']:.4f}"
        )
        print(
            f"  MHAR source Spearman:     "
            f"{pair.mhar_report['source_apparent_metrics']['spearman']:.4f}"
        )

        ocx24_results[source_prog] = {}
        for target_prog, target_samples in targets:
            print(f"\n  --- OCx24 {source_prog} → {target_prog} ---")
            print(f"  Target samples: {len(target_samples)}")
            result = evaluate_router(
                pair,
                source_samples,
                target_samples,
                training_config,
                anchors=args.anchors,
                draws=args.draws,
                seed=args.seed,
                device=device,
            )
            ocx24_results[source_prog][target_prog] = result
            decision = result["decision"]
            print(
                f"  Best strategy: {decision['best_strategy']} "
                f"(gain={decision['best_median_gain_over_single_expert']:+.4f}, "
                f"beats_both={decision['beats_both_single_experts']})"
            )

    # --- Aggregate results ---
    all_gains: list[float] = []
    all_decisions: list[dict] = []
    directions_passed = 0
    total_directions = 0

    for target_prog, result in specgen_results.items():
        total_directions += 1
        gain = result["decision"]["best_median_gain_over_single_expert"]
        all_gains.append(gain)
        all_decisions.append(
            {
                "dataset": "specgen",
                "direction": f"specgen_source→{target_prog}",
                "best_strategy": result["decision"]["best_strategy"],
                "gain": gain,
            }
        )
        if result["decision"]["beats_both_single_experts"]:
            directions_passed += 1

    for source_prog, directions in ocx24_results.items():
        for target_prog, result in directions.items():
            total_directions += 1
            gain = result["decision"]["best_median_gain_over_single_expert"]
            all_gains.append(gain)
            all_decisions.append(
                {
                    "dataset": "ocx24",
                    "direction": f"{source_prog}→{target_prog}",
                    "best_strategy": result["decision"]["best_strategy"],
                    "gain": gain,
                }
            )
            if result["decision"]["beats_both_single_experts"]:
                directions_passed += 1

    median_gain = float(np.median(all_gains)) if all_gains else 0.0

    summary = {
        "status": "complete",
        "experiment": "expert_router_screening",
        "seed": args.seed,
        "epochs": args.epochs,
        "draws": args.draws,
        "anchors": args.anchors,
        "model_config": asdict(model_config),
        "training_config": asdict(training_config),
        "aggregate": {
            "total_directions": total_directions,
            "directions_where_router_beats_both": directions_passed,
            "median_gain_over_best_single_expert": median_gain,
            "per_direction": all_decisions,
        },
        "gate": {
            "median_gain_nonnegative": median_gain >= 0.0,
            "any_direction_beats_both": directions_passed > 0,
        },
        "specgen": specgen_results,
        "ocx24": ocx24_results,
    }

    output_path = RESULTS_DIR / "expert_router_screening.json"
    write_json(output_path, summary)
    print(f"\n=== Results written to {output_path} ===")
    print(
        f"Median gain over best single expert: {median_gain:+.4f}"
    )
    print(
        f"Directions where router beats both: "
        f"{directions_passed}/{total_directions}"
    )

    import numpy as np  # noqa: E402


if __name__ == "__main__":
    main()
