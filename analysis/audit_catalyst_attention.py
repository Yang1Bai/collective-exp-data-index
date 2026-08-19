"""Audit attention allocation and modality-shuffle sensitivity."""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.data import load_specgen_archive
from catalyst_attention.model import attention_entropy
from catalyst_attention.training import (
    BatchCollator,
    load_checkpoint,
    metrics,
    predict,
    targets_array,
    write_json,
)


def shuffled_samples(rows, permutation: np.ndarray, modality: str):
    output = []
    for index, row in enumerate(rows):
        donor = rows[int(permutation[index])]
        if modality == "curve":
            output.append(
                replace(
                    row,
                    curve_axis=donor.curve_axis.copy(),
                    curve_values=donor.curve_values.copy(),
                    curve_channel_mask=donor.curve_channel_mask.copy(),
                )
            )
        elif modality == "composition":
            output.append(
                replace(
                    row,
                    elements=donor.elements.copy(),
                    fractions=donor.fractions.copy(),
                )
            )
        else:
            raise ValueError(modality)
    return output


def distribution_summary(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(array)),
        "q10": float(np.quantile(array, 0.10)),
        "q90": float(np.quantile(array, 0.90)),
    }


def shuffle_sensitivity(
    model,
    rows,
    normalizer,
    original: np.ndarray,
    target: np.ndarray,
    *,
    modality: str,
    draws: int,
    rng: np.random.Generator,
    device: torch.device,
    unknown_program: bool,
) -> dict:
    pooled = []
    for _ in range(draws):
        pooled.extend(shuffled_samples(rows, rng.permutation(len(rows)), modality))
    shuffled = predict(
        model,
        pooled,
        normalizer,
        device=device,
        unknown_program=unknown_program,
    )["mean"].reshape(draws, len(rows))
    shuffle_metrics = [metrics(target, prediction) for prediction in shuffled]
    prediction_mae = [
        float(np.mean(np.abs(original - prediction))) for prediction in shuffled
    ]
    original_spearman = metrics(target, original)["spearman"]
    spearman_drop = [
        float(original_spearman - row["spearman"]) for row in shuffle_metrics
    ]
    return {
        "draws": draws,
        "metrics": {
            name: distribution_summary([row[name] for row in shuffle_metrics])
            for name in ("rmse", "mae", "r2", "spearman")
        },
        "prediction_mae": distribution_summary(prediction_mae),
        "spearman_drop": distribution_summary(spearman_drop),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--specgen-archive", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/results/catalyst_attention_audit.json"),
    )
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--shuffle-draws", type=int, default=20)
    args = parser.parse_args()
    if args.shuffle_draws < 2:
        raise ValueError("--shuffle-draws must be at least two")
    device = torch.device("cpu")
    model, normalizer, training_report = load_checkpoint(
        args.checkpoint, device=device
    )
    all_samples = load_specgen_archive(args.specgen_archive)
    programs = ("specgen_source", "specgen_A", "specgen_B", "specgen_C", "specgen_D")
    rng = np.random.default_rng(args.seed)
    report = {
        "status": "complete",
        "checkpoint": str(args.checkpoint),
        "training_best_epoch": training_report["best_epoch"],
        "warning": (
            "Attention allocation and shuffle sensitivity are model audits, "
            "not causal mechanism attribution."
        ),
        "programs": {},
    }
    for program in programs:
        rows = [sample for sample in all_samples if sample.program == program]
        unknown_program = program != "specgen_source"
        batch = BatchCollator(
            normalizer, unknown_program=unknown_program
        )(rows)
        with torch.no_grad():
            output = model(batch, return_attention=True)
        audit = output["attention"]
        weights = audit["fusion_attention"]
        padding = audit["memory_padding_mask"]
        modality = audit["memory_modality"]
        mass = {}
        for identifier, name in (
            (0, "composition"),
            (1, "curve"),
            (2, "conditions"),
            (3, "surface"),
            (4, "task"),
        ):
            token_mask = (modality == identifier) & (~padding)
            token_mass = (
                weights
                * token_mask[:, None, None, :].to(weights.dtype)
            ).sum(dim=-1)
            mass[name] = float(token_mass.mean())
        composition_attention = audit["composition_pool_attention"].mean(
            dim=(1, 2)
        )
        element_weights: dict[int, list[float]] = {}
        for row_index, row in enumerate(rows):
            for token_index, element in enumerate(row.elements):
                element_weights.setdefault(int(element), []).append(
                    float(composition_attention[row_index, token_index])
                )
        top_elements = sorted(
            (
                {
                    "atomic_number": element,
                    "mean_attention": float(np.mean(values)),
                    "observations": len(values),
                }
                for element, values in element_weights.items()
            ),
            key=lambda item: item["mean_attention"],
            reverse=True,
        )
        original = predict(
            model,
            rows,
            normalizer,
            device=device,
            unknown_program=unknown_program,
        )["mean"]
        target = targets_array(rows)
        curve_shuffle = shuffle_sensitivity(
            model,
            rows,
            normalizer,
            original,
            target,
            modality="curve",
            draws=args.shuffle_draws,
            rng=rng,
            device=device,
            unknown_program=unknown_program,
        )
        composition_shuffle = shuffle_sensitivity(
            model,
            rows,
            normalizer,
            original,
            target,
            modality="composition",
            draws=args.shuffle_draws,
            rng=rng,
            device=device,
            unknown_program=unknown_program,
        )
        original_metrics = metrics(target, original)
        report["programs"][program] = {
            "samples": len(rows),
            "fusion_attention_mass": mass,
            "fusion_attention_entropy": float(
                attention_entropy(weights, padding).mean()
            ),
            "composition_pool_top_elements": top_elements,
            "original_metrics": original_metrics,
            "curve_shuffle": curve_shuffle,
            "composition_shuffle": composition_shuffle,
        }
    write_json(args.output, report)
    print(json.dumps(report["programs"]["specgen_B"], indent=2), flush=True)
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
