"""Frozen A+B comparison for advanced catalyst knowledge-transfer models."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from catalyst_attention.baselines import (
    TABPFN_MODEL_VERSION,
    TABPFN_PACKAGE_VERSION,
    TABPFN_V2_REGRESSOR_BYTES,
    TABPFN_V2_REGRESSOR_SHA256,
    fit_tabpfn_baseline,
)
from catalyst_attention.data import (
    OCX24_BYTES,
    OCX24_SHA256,
    SECCM_BYTES,
    SECCM_EDX_BYTES,
    SECCM_EDX_SHA256,
    SECCM_SHA256,
    SECCM_XPS_BYTES,
    SECCM_XPS_SHA256,
    SPECGEN_BYTES,
    SPECGEN_SHA256,
    CatalystSample,
    load_ocx24_csv,
    load_seccm_archives,
    load_specgen_archive,
    samples_manifest,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig,
    metrics,
    predict,
    save_checkpoint,
    targets_array,
    train_source_model,
    write_json,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "catalyst_attention_advanced_design.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_names(value: str, allowed: set[str]) -> list[str]:
    names = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(names) - allowed)
    if unknown:
        raise ValueError(f"unknown selections: {unknown}")
    if not names:
        raise ValueError("at least one selection is required")
    if len(names) != len(set(names)):
        raise ValueError("selections must not contain duplicates")
    return names


def median_predictions(predictions: list[np.ndarray]) -> np.ndarray:
    return np.median(np.stack(predictions), axis=0)


def model_overrides(design: dict, name: str) -> dict:
    return dict(design["source_models"][name])


def validate_tabpfn_contract(design: dict) -> None:
    contract = design["tabpfn"]
    expected = {
        "package_version": TABPFN_PACKAGE_VERSION,
        "model_version": TABPFN_MODEL_VERSION,
        "regressor_sha256": TABPFN_V2_REGRESSOR_SHA256,
        "regressor_bytes": TABPFN_V2_REGRESSOR_BYTES,
    }
    observed = {name: contract.get(name) for name in expected}
    if observed != expected:
        raise ValueError(
            "TabPFN runtime constants do not match the frozen design"
        )


def execution_contract(
    design: dict, dataset: str
) -> tuple[dict, dict, int, dict]:
    row = design["execution"][dataset]
    return (
        dict(row["model"]),
        dict(row["training"]),
        int(row["seed_count"]),
        row,
    )


def validate_input_contract(design: dict) -> None:
    expected = {
        "specgen": {
            "sha256": SPECGEN_SHA256,
            "bytes": SPECGEN_BYTES,
        },
        "ocx24": {
            "sha256": OCX24_SHA256,
            "bytes": OCX24_BYTES,
        },
        "seccm": {
            "sha256": SECCM_SHA256,
            "bytes": SECCM_BYTES,
        },
        "seccm_edx": {
            "sha256": SECCM_EDX_SHA256,
            "bytes": SECCM_EDX_BYTES,
        },
        "seccm_xps": {
            "sha256": SECCM_XPS_SHA256,
            "bytes": SECCM_XPS_BYTES,
        },
    }
    if design["input_artifacts"] != expected:
        raise ValueError(
            "runtime input pins do not match the frozen design"
        )


def load_reference_artifact(design: dict, name: str) -> dict:
    specification = design["reference_artifacts"][name]
    path = (HERE / specification["path"]).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"reference artifact not found: {path}")
    observed = sha256(path)
    if observed != specification["sha256"]:
        raise ValueError(
            f"reference artifact hash mismatch for {name}: "
            f"{observed} != {specification['sha256']}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def train_variant(
    source: list[CatalystSample],
    targets: dict[str, list[CatalystSample]],
    *,
    variant: str,
    design: dict,
    seeds: list[int],
    model_kwargs: dict,
    training_kwargs: dict,
    checkpoint_dir: Path,
    device: torch.device,
) -> dict:
    runs = []
    target_predictions: dict[str, list[np.ndarray]] = {
        name: [] for name in targets
    }
    for seed in seeds:
        print(f"training {variant} seed={seed}", flush=True)
        model, normalizer, report = train_source_model(
            source,
            CatalystAttentionConfig(
                **model_kwargs,
                **model_overrides(design, variant),
            ),
            TrainingConfig(seed=seed, **training_kwargs),
            device=device,
        )
        checkpoint = checkpoint_dir / f"{variant}_seed{seed}.pt"
        save_checkpoint(checkpoint, model, normalizer, report)
        target_rows = {}
        for name, samples in targets.items():
            prediction = predict(
                model,
                samples,
                normalizer,
                device=device,
                unknown_program=True,
            )
            target_predictions[name].append(prediction["mean"])
            target_rows[name] = metrics(
                targets_array(samples), prediction["mean"]
            )
        runs.append(
            {
                "seed": seed,
                "checkpoint": (
                    f"{checkpoint_dir.name}/{checkpoint.name}"
                ),
                "parameter_count": report["parameter_count"],
                "best_epoch": report["best_epoch"],
                "validation_metrics": report["validation_metrics"],
                "validation_split": report["validation_split"],
                "validation_group_overlap": report[
                    "validation_group_overlap"
                ],
                "targets": target_rows,
            }
        )
    ensemble = {
        name: metrics(
            targets_array(targets[name]),
            median_predictions(predictions),
        )
        for name, predictions in target_predictions.items()
    }
    return {"runs": runs, "ensemble": ensemble}


def tabpfn_variant(
    source: list[CatalystSample],
    targets: dict[str, list[CatalystSample]],
    *,
    seed: int,
    model_path: Path,
    include_curve: bool,
    include_surface: bool,
    include_conditions: bool,
) -> dict:
    print(
        f"fitting TabPFN source={source[0].program} rows={len(source)}",
        flush=True,
    )
    model = fit_tabpfn_baseline(
        source,
        seed=seed,
        include_curve=include_curve,
        include_surface=include_surface,
        include_conditions=include_conditions,
        model_path=model_path,
    )
    return {
        "manifest": model.manifest(),
        "targets": {
            name: metrics(targets_array(rows), model.predict(rows))
            for name, rows in targets.items()
        },
    }


def reference_specgen(design: dict) -> dict:
    existing = load_reference_artifact(design, "hierarchical_specgen")
    author = load_reference_artifact(design, "author_specgen")
    attention = {}
    systems = design["execution"]["specgen"]["target_systems"]
    for name in systems:
        attention[name] = float(
            np.median(
                [
                    run["targets"][name]["zero_label"]["spearman"]
                    for run in existing["variants"]["full"]["runs"]
                ]
            )
        )
    return {
        "hierarchical_cross_attention_v1": attention,
        "author_random_forest": {
            name: float(author["zero_label"][name]["spearman"])
            for name in systems
        },
    }


def reference_ocx24(design: dict) -> dict:
    existing = load_reference_artifact(design, "hierarchical_ocx24")
    return {
        direction: {
            "hierarchical_cross_attention_v1": row[
                "composition_condition_attention"
            ]["ensemble_metrics"],
            "fair_extra_trees": row[
                "extra_trees_composition_condition"
            ]["metrics"],
        }
        for direction, row in existing["directions"].items()
    }


def specgen_gate(result: dict, design: dict) -> dict:
    systems = tuple(design["execution"]["specgen"]["target_systems"])
    reference = result["reference"]
    best_reference = {
        name: max(
            reference["hierarchical_cross_attention_v1"][name],
            reference["author_random_forest"][name],
        )
        for name in systems
    }
    threshold = design["development_gates"]["specgen"]
    candidates = {}
    for variant, row in result["models"].items():
        metrics_by_system = (
            row["ensemble"]
            if "ensemble" in row
            else row["targets"]
        )
        gains = {
            name: (
                float(metrics_by_system[name]["spearman"])
                - best_reference[name]
            )
            for name in systems
        }
        median_gain = float(np.median(list(gains.values())))
        nonnegative = sum(value >= 0.0 for value in gains.values())
        candidates[variant] = {
            "gains": gains,
            "median_gain": median_gain,
            "nonnegative_systems": nonnegative,
            "passed": bool(
                median_gain
                >= threshold[
                    "median_A_to_D_spearman_gain_over_best_reference"
                ]
                and min(gains.values())
                >= -threshold["maximum_allowed_system_regression"]
                and nonnegative
                >= threshold["minimum_systems_with_nonnegative_gain"]
            ),
        }
    passing = sorted(
        (
            (name, row["median_gain"])
            for name, row in candidates.items()
            if row["passed"]
        ),
        key=lambda item: (-item[1], item[0]),
    )
    return {
        "candidates": candidates,
        "passed": bool(passing),
        "selected": passing[0][0] if passing else None,
    }


def ocx24_gate(result: dict, design: dict) -> dict:
    threshold = design["development_gates"]["ocx24"]
    candidates = {}
    for variant in result["model_names"]:
        gains_current = []
        gains_tree = []
        directions = {}
        for name, row in result["directions"].items():
            candidate = float(
                row["models"][variant]["ensemble"]["target"]["spearman"]
                if "ensemble" in row["models"][variant]
                else row["models"][variant]["targets"]["target"]["spearman"]
            )
            current = float(
                result["reference"][name][
                    "hierarchical_cross_attention_v1"
                ]["spearman"]
            )
            tree = float(
                result["reference"][name]["fair_extra_trees"]["spearman"]
            )
            directions[name] = {
                "spearman": candidate,
                "gain_over_current": candidate - current,
                "gain_over_tree": candidate - tree,
            }
            gains_current.append(candidate - current)
            gains_tree.append(candidate - tree)
        median_gain = float(np.median(gains_current))
        candidates[variant] = {
            "directions": directions,
            "median_gain_over_current": median_gain,
            "passed": bool(
                median_gain
                >= threshold[
                    "median_spearman_gain_over_existing_attention"
                ]
                and (
                    min(gains_tree) > 0.0
                    if threshold[
                        "must_beat_fair_extra_trees_in_both_directions"
                    ]
                    else True
                )
            ),
        }
    passing = sorted(
        (
            (name, row["median_gain_over_current"])
            for name, row in candidates.items()
            if row["passed"]
        ),
        key=lambda item: (-item[1], item[0]),
    )
    return {
        "candidates": candidates,
        "passed": bool(passing),
        "selected": passing[0][0] if passing else None,
    }


def run_specgen(
    archive: Path,
    *,
    variants: list[str],
    seeds: list[int],
    design: dict,
    tabpfn_model: Path,
    checkpoint_root: Path,
    device: torch.device,
) -> dict:
    samples = load_specgen_archive(archive)
    model_kwargs, training_kwargs, seed_count, contract = execution_contract(
        design, "specgen"
    )
    if seed_count != len(seeds):
        raise ValueError("SpecGen seed count does not match the frozen design")
    source = [
        sample
        for sample in samples
        if sample.program == contract["source_program"]
    ]
    targets = {
        name: [
            sample
            for sample in samples
            if sample.program == f"specgen_{name}"
        ]
        for name in contract["target_systems"]
    }
    result = {
        "dataset": samples_manifest(samples),
        "reference": reference_specgen(design),
        "models": {},
    }
    for variant in variants:
        result["models"][variant] = train_variant(
            source,
            targets,
            variant=variant,
            design=design,
            seeds=seeds,
            model_kwargs=model_kwargs,
            training_kwargs=training_kwargs,
            checkpoint_dir=checkpoint_root / "specgen",
            device=device,
        )
    tabpfn = contract["tabpfn"]
    result["models"]["tabpfn_v2"] = tabpfn_variant(
        source,
        targets,
        seed=seeds[int(tabpfn["seed_index"])],
        model_path=tabpfn_model,
        include_curve=bool(tabpfn["include_curve"]),
        include_surface=bool(tabpfn["include_surface"]),
        include_conditions=bool(tabpfn["include_conditions"]),
    )
    result["gate"] = specgen_gate(result, design)
    return result


def run_ocx24(
    csv_path: Path,
    *,
    variants: list[str],
    seeds: list[int],
    design: dict,
    tabpfn_model: Path,
    checkpoint_root: Path,
    device: torch.device,
) -> dict:
    model_kwargs, training_kwargs, seed_count, contract = execution_contract(
        design, "ocx24"
    )
    samples = load_ocx24_csv(
        csv_path, target_name=contract["target_name"]
    )
    if seed_count != len(seeds):
        raise ValueError("OCx24 seed count does not match the frozen design")
    directions = tuple(
        tuple(direction) for direction in contract["directions"]
    )
    result = {
        "dataset": samples_manifest(samples),
        "reference": reference_ocx24(design),
        "model_names": [*variants],
        "directions": {},
    }
    result["model_names"].append("tabpfn_v2")
    for source_name, target_name in directions:
        source = [
            sample for sample in samples if sample.program == source_name
        ]
        target = [
            sample for sample in samples if sample.program == target_name
        ]
        name = f"{source_name}_to_{target_name}"
        row = {"models": {}}
        for variant in variants:
            row["models"][variant] = train_variant(
                source,
                {"target": target},
                variant=variant,
                design=design,
                seeds=seeds,
                model_kwargs=model_kwargs,
                training_kwargs=training_kwargs,
                checkpoint_dir=checkpoint_root / name,
                device=device,
            )
        tabpfn = contract["tabpfn"]
        row["models"]["tabpfn_v2"] = tabpfn_variant(
            source,
            {"target": target},
            seed=seeds[int(tabpfn["seed_index"])],
            model_path=tabpfn_model,
            include_curve=bool(tabpfn["include_curve"]),
            include_surface=bool(tabpfn["include_surface"]),
            include_conditions=bool(tabpfn["include_conditions"]),
        )
        result["directions"][name] = row
    result["gate"] = ocx24_gate(result, design)
    return result


def run_seccm(
    seccm: Path,
    edx: Path,
    xps: Path,
    *,
    variants: list[str],
    seeds: list[int],
    design: dict,
    tabpfn_model: Path,
    checkpoint_root: Path,
    device: torch.device,
) -> dict:
    model_kwargs, training_kwargs, seed_count, contract = execution_contract(
        design, "seccm"
    )
    samples = load_seccm_archives(
        seccm, edx, xps, target_name=contract["target_name"]
    )
    if seed_count <= 0 or seed_count > len(seeds):
        raise ValueError("SECCM seed count does not match the frozen design")
    run_seeds = seeds[:seed_count]
    libraries = tuple(contract["held_out_libraries"])
    result = {
        "dataset": samples_manifest(samples),
        "evidence_boundary": design["development_gates"]["seccm"],
        "libraries": {},
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
        row = {"models": {}}
        for variant in variants:
            row["models"][variant] = train_variant(
                source,
                {"target": target},
                variant=variant,
                design=design,
                seeds=run_seeds,
                model_kwargs=model_kwargs,
                training_kwargs=training_kwargs,
                checkpoint_dir=checkpoint_root / f"seccm_{held_out}",
                device=device,
            )
        tabpfn = contract["tabpfn"]
        row["models"]["tabpfn_v2"] = tabpfn_variant(
            source,
            {"target": target},
            seed=seeds[int(tabpfn["seed_index"])],
            model_path=tabpfn_model,
            include_curve=bool(tabpfn["include_curve"]),
            include_surface=bool(tabpfn["include_surface"]),
            include_conditions=bool(tabpfn["include_conditions"]),
        )
        result["libraries"][held_out] = row
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specgen-archive", type=Path, required=True)
    parser.add_argument("--ocx24-csv", type=Path, required=True)
    parser.add_argument("--seccm-archive", type=Path, required=True)
    parser.add_argument("--edx-archive", type=Path, required=True)
    parser.add_argument("--xps-archive", type=Path, required=True)
    parser.add_argument("--tabpfn-model", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE
        / "results/catalyst_attention_advanced_monolithic.json",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=HERE
        / "results/catalyst_attention_advanced_checkpoints",
    )
    parser.add_argument(
        "--datasets", default="specgen,ocx24,seccm"
    )
    parser.add_argument(
        "--variants",
        default="crabnet_cross,set_perceiver,crabnet_perceiver",
    )
    parser.add_argument(
        "--seeds", default="20260731,20260732,20260733"
    )
    args = parser.parse_args()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    validate_tabpfn_contract(design)
    validate_input_contract(design)
    datasets = parse_names(
        args.datasets, {"specgen", "ocx24", "seccm"}
    )
    variants = parse_names(
        args.variants, set(design["source_models"])
    )
    if variants != list(design["source_models"]):
        raise ValueError(
            "variants must exactly match the frozen A+B design"
        )
    seeds = [
        int(value) for value in args.seeds.split(",") if value.strip()
    ]
    if seeds != [int(value) for value in design["seeds"]]:
        raise ValueError("seeds must exactly match the frozen design")
    device = torch.device("cpu")
    result = {
        "status": "running",
        "design_path": str(DESIGN_PATH.relative_to(HERE.parent)),
        "design_sha256": sha256(DESIGN_PATH),
        "evidence_boundary": design["evidence_boundary"],
        "requested_datasets": datasets,
        "datasets": {},
    }
    if "specgen" in datasets:
        result["datasets"]["specgen"] = run_specgen(
            args.specgen_archive,
            variants=variants,
            seeds=seeds,
            design=design,
            tabpfn_model=args.tabpfn_model,
            checkpoint_root=args.checkpoint_dir,
            device=device,
        )
    if "ocx24" in datasets:
        result["datasets"]["ocx24"] = run_ocx24(
            args.ocx24_csv,
            variants=variants,
            seeds=seeds,
            design=design,
            tabpfn_model=args.tabpfn_model,
            checkpoint_root=args.checkpoint_dir,
            device=device,
        )
    if "seccm" in datasets:
        result["datasets"]["seccm"] = run_seccm(
            args.seccm_archive,
            args.edx_archive,
            args.xps_archive,
            variants=variants,
            seeds=seeds,
            design=design,
            tabpfn_model=args.tabpfn_model,
            checkpoint_root=args.checkpoint_dir,
            device=device,
        )
    selected = {
        name: dataset["gate"].get("selected")
        for name, dataset in result["datasets"].items()
        if "gate" in dataset
    }
    required = set(design["result_contract"]["required_datasets"])
    completed = set(result["datasets"])
    missing = sorted(required - completed)
    gate_required = set(
        design["result_contract"]["gate_eligible_datasets"]
    )
    aggregate_gate_complete = gate_required <= completed
    result["completed_datasets"] = sorted(completed)
    result["missing_datasets"] = missing
    result["status"] = "complete" if not missing else "partial"
    result["selection"] = selected
    result["any_advanced_gate_passed"] = (
        any(value is not None for value in selected.values())
        if aggregate_gate_complete
        else None
    )
    write_json(args.output, result)
    print(
        json.dumps(
            {
                "selection": selected,
                "any_advanced_gate_passed": result[
                    "any_advanced_gate_passed"
                ],
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
