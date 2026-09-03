"""Train and evaluate the catalyst transfer Transformer on SpecGen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.data import load_specgen_archive, samples_manifest
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig,
    composition_matrix,
    few_shot_experiment,
    fit_composition_baseline,
    fit_pls_baseline,
    metrics,
    predict,
    predict_pls,
    save_checkpoint,
    targets_array,
    train_source_model,
    write_json,
)


VARIANTS = {
    "full": {},
    "curve_only": {"use_composition": False, "use_conditions": False},
    "composition_only": {"use_curve": False},
    "mean_pool": {"fusion_mode": "mean_pool"},
}


def median_metric(rows: list[dict], path: tuple[str, ...]) -> float:
    values = []
    for row in rows:
        value = row
        for key in path:
            value = value[key]
        values.append(float(value))
    return float(np.median(values))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specgen-archive", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/results/catalyst_attention_specgen_summary.json"),
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("analysis/results/catalyst_attention_checkpoints"),
    )
    parser.add_argument("--seeds", default="20260731,20260732,20260733")
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--anchors", type=int, default=5)
    parser.add_argument(
        "--variants",
        default="full,curve_only,composition_only,mean_pool",
        help=f"comma-separated subset of {','.join(VARIANTS)}",
    )
    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--curve-layers", type=int, default=3)
    parser.add_argument("--patch-size", type=int, default=8)
    args = parser.parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    variants = [value.strip() for value in args.variants.split(",") if value.strip()]
    unknown = sorted(set(variants) - set(VARIANTS))
    if unknown:
        raise ValueError(f"unknown variants: {unknown}")
    samples = load_specgen_archive(args.specgen_archive)
    source = [sample for sample in samples if sample.program == "specgen_source"]
    targets = {
        name: [sample for sample in samples if sample.program == f"specgen_{name}"]
        for name in ("A", "B", "C", "D")
    }
    device = torch.device("cpu")
    result: dict = {
        "status": "complete",
        "evidence_boundary": (
            "Retrospective system-held-out SpecGen reanalysis. Attention weights "
            "are audit signals, not causal explanations; no prospective discovery claim."
        ),
        "dataset": samples_manifest(samples),
        "source_samples": len(source),
        "target_samples": {name: len(rows) for name, rows in targets.items()},
        "seeds": seeds,
        "variants": {},
    }
    for variant in variants:
        runs = []
        for seed in seeds:
            model_config = CatalystAttentionConfig(
                d_model=args.d_model,
                curve_layers=args.curve_layers,
                patch_size=args.patch_size,
                **VARIANTS[variant],
            )
            training_config = TrainingConfig(
                seed=seed,
                epochs=args.epochs,
                patience=args.patience,
            )
            print(f"training variant={variant} seed={seed}", flush=True)
            model, normalizer, training_report = train_source_model(
                source, model_config, training_config, device=device
            )
            target_results = {}
            for name, target in targets.items():
                prediction = predict(
                    model,
                    target,
                    normalizer,
                    device=device,
                    unknown_program=True,
                )
                target_results[name] = {
                    "zero_label": metrics(
                        targets_array(target),
                        prediction["mean"],
                    ),
                    "support_median": float(np.median(prediction["support"])),
                }
            if variant == "full":
                target_results["B"]["few_shot"] = few_shot_experiment(
                    model,
                    source,
                    targets["B"],
                    normalizer,
                    training_config,
                    anchors=args.anchors,
                    draws=args.draws,
                    seed=seed + 5000,
                    device=device,
                )
            checkpoint = args.checkpoint_dir / f"{variant}_seed{seed}.pt"
            save_checkpoint(checkpoint, model, normalizer, training_report)
            runs.append(
                {
                    "seed": seed,
                    "training": training_report,
                    "targets": target_results,
                    "checkpoint": str(checkpoint),
                }
            )
        result["variants"][variant] = {"runs": runs}
    pls = fit_pls_baseline(source)
    composition = fit_composition_baseline(source, seeds[0])
    result["baselines"] = {}
    for name, target in targets.items():
        y = targets_array(target)
        result["baselines"][name] = {
            "pls_spectrum": metrics(y, predict_pls(pls, target)),
            "extra_trees_composition": metrics(
                y, composition.predict(composition_matrix(target))
            ),
        }
    full_runs = result["variants"].get("full", {}).get("runs", [])
    if full_runs:
        b_spearman = median_metric(full_runs, ("targets", "B", "zero_label", "spearman"))
        source_validation = median_metric(full_runs, ("training", "validation_metrics", "spearman"))
        few_shot_gain = median_metric(
            full_runs,
            (
                "targets",
                "B",
                "few_shot",
                "gains",
                "bias_calibrated_spearman",
                "median",
            ),
        )
        few_shot_rmse_gain = median_metric(
            full_runs,
            (
                "targets",
                "B",
                "few_shot",
                "gains",
                "bias_calibrated_relative_rmse",
                "median",
            ),
        )
        result["promising_gate"] = {
            "source_validation_spearman_ge_0_60": source_validation >= 0.60,
            "system_B_zero_label_spearman_ge_0_30": b_spearman >= 0.30,
            "system_B_five_label_spearman_gain_ge_0_10": few_shot_gain >= 0.10,
            "system_B_five_label_relative_rmse_gain_ge_0_05": few_shot_rmse_gain
            >= 0.05,
            "values": {
                "source_validation_spearman_median": source_validation,
                "system_B_zero_label_spearman_median": b_spearman,
                "system_B_five_label_spearman_gain_median": few_shot_gain,
                "system_B_five_label_relative_rmse_gain_median": few_shot_rmse_gain,
            },
        }
        result["promising_gate"]["passed"] = all(
            value
            for key, value in result["promising_gate"].items()
            if key != "values"
        )
    write_json(args.output, result)
    print(json.dumps(result.get("promising_gate", {}), indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
