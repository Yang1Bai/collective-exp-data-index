"""Build the portable complete summary from dataset-scoped advanced results."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from catalyst_attention.data import atomic_write_text
from run_advanced_catalyst_benchmark import (
    ocx24_gate,
    reference_ocx24,
    reference_specgen,
    specgen_gate,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "catalyst_attention_advanced_design.json"
DEFAULT_RESULTS = {
    "specgen": HERE / "results/catalyst_attention_advanced_specgen.json",
    "ocx24": HERE / "results/catalyst_attention_advanced_ocx24.json",
    "seccm": HERE / "results/catalyst_attention_advanced_seccm.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError as error:
        raise ValueError(
            f"claim-bearing result must be inside the repository: {path}"
        ) from error


def validate_metrics(value: object, context: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{context} metrics must be a dictionary")
    expected = {"mae", "rmse", "r2", "spearman"}
    if set(value) != expected:
        raise ValueError(f"{context} metrics have the wrong fields")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        for item in value.values()
    ):
        raise ValueError(f"{context} metrics must be finite numbers")


def validate_neural_model(
    row: object,
    *,
    expected_seeds: list[int],
    expected_targets: set[str],
    context: str,
    expected_validation_split: str,
    expected_validation_overlap: set[str],
) -> None:
    if not isinstance(row, dict) or set(row) != {"runs", "ensemble"}:
        raise ValueError(f"{context} neural result has the wrong schema")
    runs = row["runs"]
    if (
        not isinstance(runs, list)
        or [run.get("seed") for run in runs] != expected_seeds
    ):
        raise ValueError(f"{context} seed runs do not match the design")
    for run in runs:
        if set(run["targets"]) != expected_targets:
            raise ValueError(f"{context} run targets are incomplete")
        for target, metrics in run["targets"].items():
            validate_metrics(metrics, f"{context}/{target}")
        validate_metrics(
            run["validation_metrics"], f"{context}/validation"
        )
        if (
            not isinstance(run["parameter_count"], int)
            or run["parameter_count"] <= 0
            or not isinstance(run["best_epoch"], int)
            or run["best_epoch"] < 0
            or Path(run["checkpoint"]).is_absolute()
        ):
            raise ValueError(f"{context} run metadata is invalid")
        if (
            run["validation_split"] != expected_validation_split
            or set(run["validation_group_overlap"])
            != expected_validation_overlap
        ):
            raise ValueError(
                f"{context} validation split does not match the design"
            )
    if set(row["ensemble"]) != expected_targets:
        raise ValueError(f"{context} ensemble targets are incomplete")
    for target, metrics in row["ensemble"].items():
        validate_metrics(metrics, f"{context}/ensemble/{target}")


def validate_tabpfn(
    row: object,
    *,
    design: dict,
    expected_targets: set[str],
    context: str,
) -> None:
    if not isinstance(row, dict) or set(row) != {"manifest", "targets"}:
        raise ValueError(f"{context} TabPFN result has the wrong schema")
    manifest = row["manifest"]
    contract = design["tabpfn"]
    expected_manifest = {
        "package": "tabpfn",
        "package_version": contract["package_version"],
        "model_version": contract["model_version"],
        "model_sha256": contract["regressor_sha256"],
    }
    if any(manifest.get(key) != value for key, value in expected_manifest.items()):
        raise ValueError(f"{context} TabPFN manifest does not match the design")
    curve_components = manifest.get("curve_components")
    if (
        not isinstance(curve_components, int)
        or not 0 <= curve_components <= 24
    ):
        raise ValueError(f"{context} curve component count is invalid")
    if set(row["targets"]) != expected_targets:
        raise ValueError(f"{context} TabPFN targets are incomplete")
    for target, metrics in row["targets"].items():
        validate_metrics(metrics, f"{context}/TabPFN/{target}")


def validate_dataset_manifest(
    manifest: object,
    *,
    expected_programs: set[str],
    expected_target: str,
    context: str,
) -> None:
    if not isinstance(manifest, dict):
        raise ValueError(f"{context} dataset manifest is missing")
    programmes = manifest.get("programs")
    targets = manifest.get("targets")
    if (
        not isinstance(programmes, dict)
        or set(programmes) != expected_programs
        or any(
            not isinstance(count, int) or count <= 0
            for count in programmes.values()
        )
        or not isinstance(targets, dict)
        or set(targets) != {expected_target}
    ):
        raise ValueError(f"{context} dataset scope does not match the design")


def validate_specgen(dataset: dict, design: dict) -> None:
    contract = design["execution"]["specgen"]
    variants = set(design["source_models"])
    expected_models = variants | {"tabpfn_v2"}
    systems = set(contract["target_systems"])
    validate_dataset_manifest(
        dataset.get("dataset"),
        expected_programs={
            contract["source_program"],
            *(f"specgen_{name}" for name in systems),
        },
        expected_target="oer_overpotential_mV",
        context="specgen",
    )
    if set(dataset.get("models", {})) != expected_models:
        raise ValueError("specgen model set does not match the design")
    seeds = [
        int(value)
        for value in design["seeds"][: int(contract["seed_count"])]
    ]
    validation = contract["source_validation"]
    for variant in variants:
        validate_neural_model(
            dataset["models"][variant],
            expected_seeds=seeds,
            expected_targets=systems,
            context=f"specgen/{variant}",
            expected_validation_split=validation["split"],
            expected_validation_overlap=set(validation["overlap"]),
        )
    validate_tabpfn(
        dataset["models"]["tabpfn_v2"],
        design=design,
        expected_targets=systems,
        context="specgen",
    )
    if dataset.get("reference") != reference_specgen(design):
        raise ValueError("specgen reference artifact reconstruction failed")
    recomputed = specgen_gate(dataset, design)
    if dataset.get("gate") != recomputed:
        raise ValueError("specgen stored gate does not match recomputation")


def validate_ocx24(dataset: dict, design: dict) -> None:
    contract = design["execution"]["ocx24"]
    variants = set(design["source_models"])
    expected_models = variants | {"tabpfn_v2"}
    programmes = {
        programme
        for direction in contract["directions"]
        for programme in direction
    }
    validate_dataset_manifest(
        dataset.get("dataset"),
        expected_programs=programmes,
        expected_target=contract["target_name"],
        context="ocx24",
    )
    expected_directions = {
        f"{source}_to_{target}"
        for source, target in contract["directions"]
    }
    if (
        set(dataset.get("directions", {})) != expected_directions
        or set(dataset.get("model_names", [])) != expected_models
        or len(dataset.get("model_names", [])) != len(expected_models)
    ):
        raise ValueError("ocx24 direction or model set is incomplete")
    seeds = [
        int(value)
        for value in design["seeds"][: int(contract["seed_count"])]
    ]
    validation = contract["source_validation"]
    for direction, direction_row in dataset["directions"].items():
        models = direction_row.get("models", {})
        if set(models) != expected_models:
            raise ValueError(f"ocx24/{direction} model set is incomplete")
        for variant in variants:
            validate_neural_model(
                models[variant],
                expected_seeds=seeds,
                expected_targets={"target"},
                context=f"ocx24/{direction}/{variant}",
                expected_validation_split=validation["split"],
                expected_validation_overlap=set(validation["overlap"]),
            )
        validate_tabpfn(
            models["tabpfn_v2"],
            design=design,
            expected_targets={"target"},
            context=f"ocx24/{direction}",
        )
    if dataset.get("reference") != reference_ocx24(design):
        raise ValueError("ocx24 reference artifact reconstruction failed")
    recomputed = ocx24_gate(dataset, design)
    if dataset.get("gate") != recomputed:
        raise ValueError("ocx24 stored gate does not match recomputation")


def validate_seccm(dataset: dict, design: dict) -> None:
    contract = design["execution"]["seccm"]
    variants = set(design["source_models"])
    expected_models = variants | {"tabpfn_v2"}
    libraries = set(contract["held_out_libraries"])
    validate_dataset_manifest(
        dataset.get("dataset"),
        expected_programs={f"seccm_{name}" for name in libraries},
        expected_target=contract["target_name"],
        context="seccm",
    )
    if set(dataset.get("libraries", {})) != libraries:
        raise ValueError("seccm library set is incomplete")
    seeds = [
        int(value)
        for value in design["seeds"][: int(contract["seed_count"])]
    ]
    for library, library_row in dataset["libraries"].items():
        models = library_row.get("models", {})
        if set(models) != expected_models:
            raise ValueError(f"seccm/{library} model set is incomplete")
        validation = contract["source_validation"]
        expected_overlap = (
            libraries - {library}
            if validation["overlap"] == "source_libraries"
            else set(validation["overlap"])
        )
        for variant in variants:
            validate_neural_model(
                models[variant],
                expected_seeds=seeds,
                expected_targets={"target"},
                context=f"seccm/{library}/{variant}",
                expected_validation_split=validation["split"],
                expected_validation_overlap=expected_overlap,
            )
        validate_tabpfn(
            models["tabpfn_v2"],
            design=design,
            expected_targets={"target"},
            context=f"seccm/{library}",
        )
    if dataset.get("evidence_boundary") != design[
        "development_gates"
    ]["seccm"]:
        raise ValueError("seccm evidence boundary does not match the design")


def validate_dataset_payload(
    name: str, dataset: dict, design: dict
) -> None:
    validators = {
        "specgen": validate_specgen,
        "ocx24": validate_ocx24,
        "seccm": validate_seccm,
    }
    validators[name](dataset, design)


def aggregate_results(
    design_path: Path,
    result_paths: dict[str, Path],
) -> dict:
    design = json.loads(design_path.read_text(encoding="utf-8"))
    design_hash = sha256(design_path)
    required = set(design["result_contract"]["required_datasets"])
    if set(result_paths) != required:
        raise ValueError("aggregate inputs must match all required datasets")
    gate_eligible = set(
        design["result_contract"]["gate_eligible_datasets"]
    )
    artifacts = {}
    gates = {}
    boundaries = {}
    for name in sorted(required):
        path = result_paths[name]
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("status") != "partial":
            raise ValueError(f"{name} result must be dataset-scoped partial")
        if result.get("design_sha256") != design_hash:
            raise ValueError(f"{name} result has the wrong design hash")
        if result.get("completed_datasets") != [name]:
            raise ValueError(f"{name} completed-dataset contract is invalid")
        datasets = result.get("datasets", {})
        if set(datasets) != {name}:
            raise ValueError(f"{name} result contains an invalid dataset scope")
        expected_missing = sorted(required - {name})
        if result.get("missing_datasets") != expected_missing:
            raise ValueError(f"{name} missing-dataset contract is invalid")
        dataset = datasets.get(name)
        if not isinstance(dataset, dict):
            raise ValueError(f"{name} dataset result is missing")
        validate_dataset_payload(name, dataset, design)
        artifacts[name] = {
            "path": repository_path(path),
            "sha256": sha256(path),
        }
        if name in gate_eligible:
            gate = dataset.get("gate")
            if not isinstance(gate, dict):
                raise ValueError(f"{name} promotion gate is missing")
            if not isinstance(gate.get("passed"), bool):
                raise ValueError(f"{name} gate pass value must be boolean")
            gates[name] = {
                "passed": gate["passed"],
                "selected": gate["selected"],
            }
            if gates[name]["passed"] != (
                gates[name]["selected"] is not None
            ):
                raise ValueError(
                    f"{name} gate pass and selection are inconsistent"
                )
        else:
            boundaries[name] = design["development_gates"][name]["reason"]
    return {
        "status": "complete",
        "design_path": repository_path(design_path),
        "design_sha256": design_hash,
        "completed_datasets": sorted(required),
        "missing_datasets": [],
        "dataset_artifacts": artifacts,
        "gate_evaluations": gates,
        "non_gate_boundaries": boundaries,
        "any_advanced_gate_passed": any(
            row["passed"] for row in gates.values()
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, default=DESIGN_PATH)
    parser.add_argument("--specgen", type=Path, default=DEFAULT_RESULTS["specgen"])
    parser.add_argument("--ocx24", type=Path, default=DEFAULT_RESULTS["ocx24"])
    parser.add_argument("--seccm", type=Path, default=DEFAULT_RESULTS["seccm"])
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE / "results/catalyst_attention_advanced_summary.json",
    )
    args = parser.parse_args()
    summary = aggregate_results(
        args.design,
        {
            "specgen": args.specgen,
            "ocx24": args.ocx24,
            "seccm": args.seccm,
        },
    )
    atomic_write_text(
        args.output,
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
    )
    print(json.dumps(summary["gate_evaluations"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
