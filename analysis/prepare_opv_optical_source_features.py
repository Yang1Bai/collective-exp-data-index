"""Create strict, outcome-free optical property cards for OPV molecules."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import chemprop
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

import prepare_optical_photocatalysis_donor_features as base
import pretrain_optical_source_chemprop as optical_nn


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
AUDIT_PATH = HERE / "results" / "opv_optical_external_pair_audit.json"
METADATA_PATH = (
    HERE / "results" / "opv_optical_target_metadata_no_outcomes.csv"
)
SOURCE_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "DB for chromophore_Sci_Data_rev02.csv"
)
CONFIG_PATH = HERE / "optical_supervised_borrowing_config.json"
EXISTING_CHECKPOINT_DIR = (
    HERE / "results" / "optical_supervised_source_checkpoints"
)
CHECKPOINT_DIR = (
    HERE / "results" / "opv_optical_source_checkpoints"
)
FEATURE_PATH = HERE / "results" / "opv_optical_source_features.csv"
OOF_PATH = HERE / "results" / "opv_optical_global_source_oof.csv"
SUMMARY_PATH = HERE / "results" / "opv_optical_source_summary.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_doi(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().rstrip(".,;")


def load_checkpoint_model(
    path: Path, settings: dict[str, Any]
) -> tuple[torch.nn.Module, list[str]]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    tasks = [str(value) for value in payload["tasks"]]
    scaler = StandardScaler().fit(
        np.zeros((2, len(tasks)), dtype=np.float32)
    )
    model = optical_nn.build_model(len(tasks), scaler, settings)
    model.load_state_dict(payload["state_dict"])
    return model, tasks


def checkpoint_predictions(
    paths: list[Path],
    smiles: list[str],
    settings: dict[str, Any],
    accelerator: str,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    predictions = []
    expected_tasks: list[str] | None = None
    for path in paths:
        model, tasks = load_checkpoint_model(path, settings)
        if expected_tasks is None:
            expected_tasks = tasks
        elif tasks != expected_tasks:
            raise AssertionError(f"Task drift across checkpoints: {path}")
        values, _ = optical_nn.predict_and_encode(
            model,
            smiles,
            len(tasks),
            accelerator,
            int(settings["batch_size"]),
        )
        predictions.append(values.astype(np.float32))
    if expected_tasks is None:
        raise RuntimeError("No checkpoints supplied")
    stacked = np.stack(predictions, axis=0)
    return (
        expected_tasks,
        np.mean(stacked, axis=0),
        np.std(stacked, axis=0, ddof=1),
    )


def add_predictions(
    output: pd.DataFrame,
    prefix: str,
    tasks: list[str],
    mean: np.ndarray,
    std: np.ndarray,
) -> None:
    for column, task in enumerate(tasks):
        slug = base.PROPERTY_SLUGS[task]
        output[f"{prefix}__{slug}__mean"] = mean[:, column]
        output[f"{prefix}__{slug}__std"] = std[:, column]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device", choices=["auto", "cpu", "cuda"], default="auto"
    )
    parser.add_argument(
        "--reuse-existing-global",
        action="store_true",
        help="Workflow smoke only: use global checkpoints that retain four OPV molecules.",
    )
    arguments = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if sha256(SOURCE_PATH) != design["source"]["required_sha256"]:
        raise RuntimeError("Deep4Chem source hash changed")
    if sha256(METADATA_PATH) != design["outcome_free_audit"][
        "metadata_sha256"
    ]:
        raise RuntimeError("Outcome-free OPV metadata changed")
    if audit["status"] != "metadata-audited-row-outcomes-unopened":
        raise RuntimeError("OPV metadata audit is not sealed")
    if chemprop.__version__ != "2.1.2":
        raise RuntimeError(f"Chemprop version drift: {chemprop.__version__}")
    if arguments.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    accelerator = (
        "gpu"
        if arguments.device == "cuda"
        or (arguments.device == "auto" and torch.cuda.is_available())
        else "cpu"
    )

    metadata = pd.read_csv(METADATA_PATH, low_memory=False)
    target_smiles = sorted(
        set(metadata["donor_smiles_canonical"].astype(str))
        | set(metadata["acceptor_smiles_canonical"].astype(str))
    )
    target_smiles = [value for value in target_smiles if value]
    target_smiles_set = set(target_smiles)
    target_dois = set(
        metadata["doi_normalized_audit"].dropna().astype(str)
    ) - {""}

    settings = config["source_encoder"]
    solid_real_paths = sorted(
        EXISTING_CHECKPOINT_DIR.glob("self_host_solid_seed*.pt")
    )
    solid_real_paths = [
        path for path in solid_real_paths if "_shuffled_" not in path.name
    ]
    solid_shuffled_paths = sorted(
        EXISTING_CHECKPOINT_DIR.glob(
            "self_host_solid_shuffled_seed*.pt"
        )
    )
    if len(solid_real_paths) != 5 or len(solid_shuffled_paths) != 3:
        raise RuntimeError("Verified solid-state checkpoint ensemble missing")
    if int(audit["source"]["exact_target_molecule_overlap_solid"]) != 0:
        raise RuntimeError("Existing solid checkpoints are not target-clean")
    if int(audit["source"]["target_doi_overlap_solid"]) != 0:
        raise RuntimeError("Solid source DOI overlaps target")

    if arguments.reuse_existing_global:
        global_paths = sorted(
            EXISTING_CHECKPOINT_DIR.glob("global_state_blind_seed*.pt")
        )
        global_mode = "workflow-smoke-existing-global-with-four-overlaps"
        global_summary: dict[str, Any] = {}
        oof_hash = None
    else:
        raw = pd.read_csv(
            SOURCE_PATH,
            usecols=[
                "Chromophore",
                "Solvent",
                "Reference",
                *list(config["source_tasks"]),
            ],
            low_memory=False,
        )
        parsed = raw["Chromophore"].map(base.canonicalize)
        raw["canonical_smiles"] = parsed.map(lambda item: item[0])
        raw["reference_doi"] = raw["Reference"].map(normalize_doi)
        raw = raw[
            raw["canonical_smiles"].notna()
            & ~raw["canonical_smiles"].isin(target_smiles_set)
            & ~raw["reference_doi"].isin(target_dois)
        ].copy()
        for task in config["source_tasks"]:
            raw[task] = base.transform_property(task, raw[task])
        global_frame, global_tasks = optical_nn.source_frame(
            raw,
            pd.Series(True, index=raw.index),
            list(config["source_tasks"]),
            int(config["source_task_minimum_unique_molecules"]),
        )
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        optical_nn.CHECKPOINT_DIR = CHECKPOINT_DIR
        _, global_summary, global_oof = optical_nn.fit_scope(
            "opv_global_state_blind",
            global_frame,
            global_tasks,
            target_smiles,
            settings,
            accelerator,
            [int(value) for value in settings["final_seeds"]],
        )
        global_oof.to_csv(OOF_PATH, index=False, lineterminator="\n")
        global_paths = sorted(
            CHECKPOINT_DIR.glob("opv_global_state_blind_seed*.pt")
        )
        global_mode = "strict-target-and-doi-excluded-retrain"
        oof_hash = sha256(OOF_PATH)

    solid_tasks, solid_mean, solid_std = checkpoint_predictions(
        solid_real_paths, target_smiles, settings, accelerator
    )
    shuffled_tasks, shuffled_mean, shuffled_std = checkpoint_predictions(
        solid_shuffled_paths, target_smiles, settings, accelerator
    )
    global_tasks, global_mean, global_std = checkpoint_predictions(
        global_paths, target_smiles, settings, accelerator
    )
    if solid_tasks != shuffled_tasks:
        raise RuntimeError("Real and shuffled solid task sets differ")
    if not set(solid_tasks).issubset(global_tasks):
        raise RuntimeError("Global state ablation lacks a solid-state task")

    global_indices = [global_tasks.index(task) for task in solid_tasks]
    global_mean = global_mean[:, global_indices]
    global_std = global_std[:, global_indices]
    shared_tasks = solid_tasks
    output = pd.DataFrame({"canonical_smiles": target_smiles})
    add_predictions(
        output, "solid_real", shared_tasks, solid_mean, solid_std
    )
    add_predictions(
        output,
        "solid_shuffled",
        shared_tasks,
        shuffled_mean,
        shuffled_std,
    )
    add_predictions(
        output,
        "global_state_blind",
        shared_tasks,
        global_mean,
        global_std,
    )
    FEATURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(FEATURE_PATH, index=False, lineterminator="\n")

    checkpoint_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in solid_real_paths + solid_shuffled_paths + global_paths
    }
    summary = {
        "status": (
            "strict-source-features-ready"
            if not arguments.reuse_existing_global
            else "workflow-smoke-only"
        ),
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "audit_sha256": sha256(AUDIT_PATH),
        "metadata_sha256": sha256(METADATA_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "implementation_sha256": sha256(Path(__file__)),
        "feature_sha256": sha256(FEATURE_PATH),
        "global_oof_sha256": oof_hash,
        "global_mode": global_mode,
        "target_unique_molecules": int(len(target_smiles)),
        "shared_tasks": shared_tasks,
        "feature_columns": [
            column for column in output.columns if column != "canonical_smiles"
        ],
        "solid_checkpoint_provenance": (
            "Previously verified solid-state real and shuffled ensembles; "
            "the OPV metadata audit proves zero exact target-molecule and "
            "zero target-DOI overlap in that source scope."
        ),
        "global_source_summary": global_summary,
        "checkpoint_sha256": checkpoint_hashes,
        "outcome_access": (
            "No OPV PCE, Voc, Jsc, FF or target energy annotation was read."
        ),
        "environment": {
            "python": sys.version,
            "chemprop": chemprop.__version__,
            "torch": torch.__version__,
            "pandas": pd.__version__,
        },
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
