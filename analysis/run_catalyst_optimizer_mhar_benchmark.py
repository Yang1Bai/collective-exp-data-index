"""Compare Delta-MHAR and KL-Shampoo under frozen catalyst transfer splits."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.data import (
    load_ocx24_csv,
    load_specgen_archive,
    samples_manifest,
)
from catalyst_attention.model import (
    CatalystAttentionConfig,
    depth_routing_diagnostics,
)
from catalyst_attention.training import (
    TrainingConfig,
    metrics,
    predict,
    save_checkpoint,
    targets_array,
    train_source_model,
    write_json,
)
from run_advanced_catalyst_benchmark import (
    ocx24_gate,
    reference_ocx24,
    reference_specgen,
    specgen_gate,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "catalyst_optimizer_mhar_design.json"
ADVANCED_DESIGN_PATH = HERE / "catalyst_attention_advanced_design.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_subset(value: str, allowed: set[str], label: str) -> list[str]:
    selected = [item.strip() for item in value.split(",") if item.strip()]
    if not selected:
        raise ValueError(f"at least one {label} is required")
    unknown = sorted(set(selected) - allowed)
    if unknown:
        raise ValueError(f"unknown {label}: {unknown}")
    if len(selected) != len(set(selected)):
        raise ValueError(f"duplicate {label}")
    return selected


def median_predictions(predictions: list[np.ndarray]) -> np.ndarray:
    return np.median(np.stack(predictions, axis=0), axis=0)


def train_candidate(
    source: list,
    targets: dict[str, list],
    *,
    candidate_name: str,
    candidate: dict,
    seeds: list[int],
    model_kwargs: dict,
    training_kwargs: dict,
    checkpoint_dir: Path,
    device: torch.device,
) -> dict:
    runs = []
    target_predictions = {name: [] for name in targets}
    for seed in seeds:
        print(
            f"training candidate={candidate_name} seed={seed}",
            flush=True,
        )
        started = time.perf_counter()
        model = CatalystAttentionConfig(
            **model_kwargs,
            depth_routing=candidate["depth_routing"],
            depth_routing_heads=4,
        )
        training = TrainingConfig(
            seed=seed,
            optimizer=candidate["optimizer"],
            domain_alignment_weight=float(
                candidate.get("domain_alignment_weight", 0.0)
            ),
            **training_kwargs,
        )
        fitted, normalizer, report = train_source_model(
            source,
            model,
            training,
            device=device,
            unlabeled_target_samples=(
                [
                    row
                    for target_rows in targets.values()
                    for row in target_rows
                ]
                if training.domain_alignment_weight > 0.0
                else None
            ),
        )
        target_rows = {}
        routing_rows = {}
        for name, rows in targets.items():
            prediction = predict(
                fitted,
                rows,
                normalizer,
                device=device,
                unknown_program=True,
            )
            target_predictions[name].append(prediction["mean"])
            target_rows[name] = metrics(
                targets_array(rows), prediction["mean"]
            )
            routing_rows[name] = depth_routing_diagnostics(fitted)
        checkpoint = (
            checkpoint_dir / f"{candidate_name}_seed{seed}.pt"
        )
        save_checkpoint(checkpoint, fitted, normalizer, report)
        runs.append(
            {
                "seed": seed,
                "checkpoint": str(
                    checkpoint.resolve().relative_to(
                        HERE.parent.resolve()
                    )
                ),
                "elapsed_seconds": time.perf_counter() - started,
                "parameter_count": report["parameter_count"],
                "best_epoch": report["best_epoch"],
                "validation_metrics": report["validation_metrics"],
                "validation_split": report["validation_split"],
                "validation_group_overlap": report[
                    "validation_group_overlap"
                ],
                "optimizer": report["optimizer"],
                "targets": target_rows,
                "routing_diagnostics": routing_rows,
            }
        )
    return {
        "runs": runs,
        "ensemble": {
            name: metrics(
                targets_array(targets[name]),
                median_predictions(predictions),
            )
            for name, predictions in target_predictions.items()
        },
    }


def run_specgen(
    archive: Path,
    *,
    candidates: list[str],
    design: dict,
    advanced_design: dict,
    seeds: list[int],
    checkpoint_root: Path,
    device: torch.device,
) -> dict:
    contract = design["execution"]["specgen"]
    samples = load_specgen_archive(archive)
    source = [
        row
        for row in samples
        if row.program == contract["source_program"]
    ]
    targets = {
        name: [
            row
            for row in samples
            if row.program == f"specgen_{name}"
        ]
        for name in contract["target_systems"]
    }
    result = {
        "dataset": samples_manifest(samples),
        "reference": reference_specgen(advanced_design),
        "models": {},
    }
    for name in candidates:
        result["models"][name] = train_candidate(
            source,
            targets,
            candidate_name=name,
            candidate=design["candidates"][name],
            seeds=seeds,
            model_kwargs=contract["model"],
            training_kwargs=contract["training"],
            checkpoint_dir=checkpoint_root / "specgen",
            device=device,
        )
    result["gate"] = specgen_gate(result, advanced_design)
    return result


def run_ocx24(
    csv_path: Path,
    *,
    candidates: list[str],
    design: dict,
    advanced_design: dict,
    seeds: list[int],
    checkpoint_root: Path,
    device: torch.device,
) -> dict:
    contract = design["execution"]["ocx24"]
    samples = load_ocx24_csv(
        csv_path, target_name=contract["target_name"]
    )
    result = {
        "dataset": samples_manifest(samples),
        "reference": reference_ocx24(advanced_design),
        "model_names": list(candidates),
        "directions": {},
    }
    for source_name, target_name in contract["directions"]:
        source = [
            row for row in samples if row.program == source_name
        ]
        target = [
            row for row in samples if row.program == target_name
        ]
        direction = f"{source_name}_to_{target_name}"
        result["directions"][direction] = {"models": {}}
        for name in candidates:
            result["directions"][direction]["models"][name] = (
                train_candidate(
                    source,
                    {"target": target},
                    candidate_name=name,
                    candidate=design["candidates"][name],
                    seeds=seeds,
                    model_kwargs=contract["model"],
                    training_kwargs=contract["training"],
                    checkpoint_dir=checkpoint_root / direction,
                    device=device,
                )
            )
    result["gate"] = ocx24_gate(result, advanced_design)
    return result


def screening_selection(result: dict) -> dict:
    candidates = result["candidates"]
    rows = {}
    for candidate in candidates:
        gains = {}
        validations = []
        specgen = result.get("datasets", {}).get("specgen")
        if specgen is not None:
            reference = specgen["reference"]
            for system, metric in specgen["models"][candidate][
                "ensemble"
            ].items():
                baseline = max(
                    reference["hierarchical_cross_attention_v1"][
                        system
                    ],
                    reference["author_random_forest"][system],
                )
                gains[f"specgen_{system}"] = (
                    float(metric["spearman"]) - baseline
                )
            validations.extend(
                float(run["validation_metrics"]["spearman"])
                for run in specgen["models"][candidate]["runs"]
            )
        ocx24 = result.get("datasets", {}).get("ocx24")
        if ocx24 is not None:
            for direction, direction_row in ocx24["directions"].items():
                metric = direction_row["models"][candidate][
                    "ensemble"
                ]["target"]
                baseline = ocx24["reference"][direction][
                    "hierarchical_cross_attention_v1"
                ]["spearman"]
                gains[f"ocx24_{direction}"] = (
                    float(metric["spearman"]) - float(baseline)
                )
                validations.extend(
                    float(run["validation_metrics"]["spearman"])
                    for run in direction_row["models"][candidate][
                        "runs"
                    ]
                )
        values = list(gains.values())
        rows[candidate] = {
            "transfer_unit_gains": gains,
            "median_transfer_gain": float(np.median(values)),
            "worst_transfer_gain": float(np.min(values)),
            "median_source_validation_spearman": float(
                np.median(validations)
            ),
            "eligible": bool(np.min(values) >= -0.1),
        }
    ranked = sorted(
        (
            (name, row["median_transfer_gain"])
            for name, row in rows.items()
            if row["eligible"]
        ),
        key=lambda item: (-item[1], item[0]),
    )
    return {
        "candidates": rows,
        "selected_for_confirmation": ranked[0][0] if ranked else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specgen-archive", type=Path, required=True)
    parser.add_argument("--ocx24-csv", type=Path, required=True)
    parser.add_argument(
        "--design",
        type=Path,
        default=DESIGN_PATH,
    )
    parser.add_argument(
        "--stage",
        choices=["screening", "confirmation"],
        default="screening",
    )
    parser.add_argument(
        "--datasets", default="specgen,ocx24"
    )
    parser.add_argument(
        "--candidates",
        default=(
            "standard_adamw,standard_kl_shampoo,"
            "delta_mhar_adamw,delta_mhar_kl_shampoo"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE
        / "results/catalyst_optimizer_mhar_screening.json",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=HERE
        / "results/catalyst_optimizer_mhar_checkpoints",
    )
    args = parser.parse_args()

    design = json.loads(args.design.read_text(encoding="utf-8"))
    advanced_design = json.loads(
        ADVANCED_DESIGN_PATH.read_text(encoding="utf-8")
    )
    candidates = parse_subset(
        args.candidates, set(design["candidates"]), "candidates"
    )
    datasets = parse_subset(
        args.datasets, {"specgen", "ocx24"}, "datasets"
    )
    seed_count = int(design[args.stage]["seed_count"])
    seeds = [
        int(seed) for seed in design["seeds"][:seed_count]
    ]
    result = {
        "status": "running",
        "stage": args.stage,
        "evidence_boundary": design["evidence_boundary"],
        "design_path": str(
            args.design.resolve().relative_to(HERE.parent.resolve())
        ),
        "design_sha256": sha256(args.design),
        "candidates": candidates,
        "seeds": seeds,
        "input_artifacts": {
            "specgen": {
                "sha256": sha256(args.specgen_archive),
                "bytes": args.specgen_archive.stat().st_size,
            },
            "ocx24": {
                "sha256": sha256(args.ocx24_csv),
                "bytes": args.ocx24_csv.stat().st_size,
            },
        },
        "datasets": {},
    }
    device = torch.device("cpu")
    if "specgen" in datasets:
        result["datasets"]["specgen"] = run_specgen(
            args.specgen_archive,
            candidates=candidates,
            design=design,
            advanced_design=advanced_design,
            seeds=seeds,
            checkpoint_root=args.checkpoint_dir,
            device=device,
        )
    if "ocx24" in datasets:
        result["datasets"]["ocx24"] = run_ocx24(
            args.ocx24_csv,
            candidates=candidates,
            design=design,
            advanced_design=advanced_design,
            seeds=seeds,
            checkpoint_root=args.checkpoint_dir,
            device=device,
        )
    result["screening_selection"] = screening_selection(result)
    result["status"] = "complete"
    write_json(args.output, result)
    print(
        json.dumps(result["screening_selection"], indent=2),
        flush=True,
    )
    print(f"wrote {args.output}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
