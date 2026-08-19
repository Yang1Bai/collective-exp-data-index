"""Cross-source OCx24 catalyst-composition attention benchmark."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.data import load_ocx24_csv, samples_manifest
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig,
    composition_condition_matrix,
    composition_matrix,
    fit_composition_baseline,
    fit_composition_condition_baseline,
    metrics,
    predict,
    targets_array,
    train_source_model,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocx24-csv", type=Path, required=True)
    parser.add_argument("--target", default="fe_co", choices=["fe_co", "fe_h2"])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/results/catalyst_attention_ocx24_summary.json"),
    )
    parser.add_argument("--seeds", default="20260731,20260732,20260733")
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--d-model", type=int, default=48)
    parser.add_argument("--composition-layers", type=int, default=2)
    parser.add_argument("--rank-weight", type=float, default=0.22)
    parser.add_argument("--nll-weight", type=float, default=0.18)
    parser.add_argument("--dropout", type=float, default=0.12)
    args = parser.parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    if not seeds:
        raise ValueError("at least one seed is required")
    samples = load_ocx24_csv(args.ocx24_csv, target_name=args.target)
    device = torch.device("cpu")
    directions = (
        ("ocx24_uoft", "ocx24_vsp"),
        ("ocx24_vsp", "ocx24_uoft"),
    )
    result = {
        "status": "complete",
        "evidence_boundary": (
            "Post-outcome method-development benchmark: capacity and ranking loss "
            "were selected after inspecting the two cross-source directions. Source "
            "labels are grouped by physical sample and the complete other source is "
            "held out, but a fresh programme is required for confirmation."
        ),
        "dataset": samples_manifest(samples),
        "target": args.target,
        "seeds": seeds,
        "directions": {},
    }
    for source_name, target_name in directions:
        source = [sample for sample in samples if sample.program == source_name]
        target = [sample for sample in samples if sample.program == target_name]
        y = targets_array(target)
        direction = f"{source_name}_to_{target_name}"
        result["directions"][direction] = {}
        ensemble_predictions = {}
        for variant, use_conditions in (
            ("composition_condition_attention", True),
            ("composition_attention_only", False),
        ):
            runs = []
            predictions = []
            for seed in seeds:
                print(f"{direction} {variant} seed={seed}", flush=True)
                model, normalizer, training_report = train_source_model(
                    source,
                    CatalystAttentionConfig(
                        d_model=args.d_model,
                        n_heads=4,
                        composition_layers=args.composition_layers,
                        curve_layers=1,
                        condition_layers=1,
                        fusion_layers=1,
                        use_curve=False,
                        use_conditions=use_conditions,
                        patch_size=8,
                        dropout=args.dropout,
                    ),
                    TrainingConfig(
                        seed=seed,
                        epochs=args.epochs,
                        patience=args.patience,
                        batch_size=64,
                        learning_rate=8e-4,
                        rank_weight=args.rank_weight,
                        nll_weight=args.nll_weight,
                    ),
                    device=device,
                )
                prediction = predict(
                    model,
                    target,
                    normalizer,
                    device=device,
                    unknown_program=True,
                )
                predictions.append(prediction["mean"])
                runs.append(
                    {
                        "seed": seed,
                        "metrics": metrics(y, prediction["mean"]),
                        "validation_metrics": training_report[
                            "validation_metrics"
                        ],
                        "validation_split": training_report["validation_split"],
                        "validation_group_overlap": training_report[
                            "validation_group_overlap"
                        ],
                        "best_epoch": training_report["best_epoch"],
                        "parameter_count": training_report["parameter_count"],
                    }
                )
            ensemble_prediction = np.mean(np.stack(predictions), axis=0)
            ensemble_predictions[variant] = ensemble_prediction
            result["directions"][direction][variant] = {
                "runs": runs,
                "ensemble_metrics": metrics(y, ensemble_prediction),
            }
        composition_baseline = fit_composition_baseline(source, seeds[0])
        fair_baseline = fit_composition_condition_baseline(source, seeds[0])
        result["directions"][direction]["extra_trees_composition"] = {
            "metrics": metrics(
                y,
                composition_baseline.predict(composition_matrix(target)),
            )
        }
        fair_prediction = fair_baseline.predict(
            composition_condition_matrix(target)
        )
        result["directions"][direction]["extra_trees_composition_condition"] = {
            "metrics": metrics(y, fair_prediction)
        }
        hybrid_prediction = 0.5 * (
            ensemble_predictions["composition_condition_attention"]
            + fair_prediction
        )
        result["directions"][direction]["attention_extra_trees_hybrid"] = {
            "attention_weight": 0.5,
            "metrics": metrics(y, hybrid_prediction),
        }
    gains = []
    ranks = []
    for row in result["directions"].values():
        attention_rank = row["composition_condition_attention"]["ensemble_metrics"][
            "spearman"
        ]
        hybrid_rank = row["attention_extra_trees_hybrid"]["metrics"]["spearman"]
        baseline_rank = row["extra_trees_composition_condition"]["metrics"][
            "spearman"
        ]
        ranks.append(attention_rank)
        gains.append(hybrid_rank - baseline_rank)
    result["transfer_gate"] = {
        "attention_ensemble_spearman_median_ge_0_50": bool(
            np.median(ranks) >= 0.50
        ),
        "hybrid_gain_over_fair_extra_trees_median_ge_0_02": bool(
            np.median(gains) >= 0.02
        ),
        "all_direction_hybrid_gains_nonnegative": bool(np.min(gains) >= 0.0),
        "values": {
            "attention_ensemble_spearman_median": float(np.median(ranks)),
            "hybrid_gain_over_fair_extra_trees_median": float(np.median(gains)),
        },
    }
    result["transfer_gate"]["passed"] = all(
        value
        for key, value in result["transfer_gate"].items()
        if key != "values"
    )
    write_json(args.output, result)
    print(json.dumps(result["transfer_gate"], indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
