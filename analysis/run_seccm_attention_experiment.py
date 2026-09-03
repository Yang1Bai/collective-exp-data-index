"""Library-held-out attention benchmark on the new Au-Ir-Rh SECCM dataset."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.data import load_seccm_archives, samples_manifest
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig,
    composition_matrix,
    fit_composition_baseline,
    fit_pls_baseline,
    metrics,
    predict,
    predict_pls,
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seccm-archive", type=Path, required=True)
    parser.add_argument("--edx-archive", type=Path, required=True)
    parser.add_argument("--xps-archive", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/results/catalyst_attention_seccm_summary.json"),
    )
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument(
        "--variants", default="full,curve_only,composition_only,mean_pool"
    )
    args = parser.parse_args()
    variants = [item.strip() for item in args.variants.split(",") if item.strip()]
    unknown = sorted(set(variants) - set(VARIANTS))
    if unknown:
        raise ValueError(f"unknown variants: {unknown}")
    samples = load_seccm_archives(
        args.seccm_archive,
        args.edx_archive,
        args.xps_archive,
        target_name="log10_k0",
    )
    libraries = ("Au-rich", "Ir-rich", "Rh-rich")
    device = torch.device("cpu")
    result = {
        "status": "complete",
        "evidence_boundary": (
            "Representation benchmark only: log10(k0) was fitted from the input "
            "LSV, so this does not independently validate catalyst discovery."
        ),
        "dataset": samples_manifest(samples),
        "held_out_unit": "complete composition library",
        "seed": args.seed,
        "variants": {},
        "baselines": {},
    }
    for held_out in libraries:
        source = [
            sample
            for sample in samples
            if sample.program != f"seccm_{held_out}"
        ]
        target = [
            sample
            for sample in samples
            if sample.program == f"seccm_{held_out}"
        ]
        y = targets_array(target)
        result["variants"][held_out] = {}
        for variant in variants:
            print(f"held_out={held_out} variant={variant}", flush=True)
            use_surface = bool(args.xps_archive) and variant == "full"
            model, normalizer, training_report = train_source_model(
                source,
                CatalystAttentionConfig(
                    d_model=48,
                    n_heads=4,
                    composition_layers=2,
                    curve_layers=2,
                    condition_layers=1,
                    fusion_layers=1,
                    patch_size=8,
                    use_surface=use_surface,
                    **VARIANTS[variant],
                ),
                TrainingConfig(
                    seed=args.seed,
                    epochs=args.epochs,
                    patience=args.patience,
                    batch_size=48,
                    learning_rate=8e-4,
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
            result["variants"][held_out][variant] = {
                "metrics": metrics(y, prediction["mean"]),
                "validation_metrics": training_report["validation_metrics"],
                "best_epoch": training_report["best_epoch"],
                "parameter_count": training_report["parameter_count"],
            }
        pls = fit_pls_baseline(source)
        composition = fit_composition_baseline(source, args.seed)
        result["baselines"][held_out] = {
            "pls_curve": metrics(y, predict_pls(pls, target)),
            "extra_trees_composition": metrics(
                y, composition.predict(composition_matrix(target))
            ),
        }
    full_spearman = np.median(
        [
            result["variants"][library]["full"]["metrics"]["spearman"]
            for library in libraries
        ]
    )
    composition_spearman = np.median(
        [
            result["variants"][library]["composition_only"]["metrics"]["spearman"]
            for library in libraries
        ]
    )
    result["representation_gate"] = {
        "median_full_spearman_ge_0_70": bool(full_spearman >= 0.70),
        "full_minus_composition_spearman_ge_0_10": bool(
            full_spearman - composition_spearman >= 0.10
        ),
        "values": {
            "full_spearman_median": float(full_spearman),
            "composition_spearman_median": float(composition_spearman),
            "difference": float(full_spearman - composition_spearman),
        },
    }
    result["representation_gate"]["passed"] = all(
        value
        for key, value in result["representation_gate"].items()
        if key != "values"
    )
    write_json(args.output, result)
    print(json.dumps(result["representation_gate"], indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
