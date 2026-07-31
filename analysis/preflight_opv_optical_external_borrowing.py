"""Outcome-free integrity preflight for the optical-to-OPV benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
FREEZE_PATH = HERE / "opv_optical_implementation_freeze.json"
AUDIT_PATH = RESULTS / "opv_optical_external_pair_audit.json"
METADATA_PATH = RESULTS / "opv_optical_target_metadata_no_outcomes.csv"
DRAW_PATH = RESULTS / "opv_optical_label_draws.csv"
DRAW_MANIFEST_PATH = RESULTS / "opv_optical_label_draws_manifest.json"
TARGET_PATH = ROOT / "data" / "external" / "opv_borrowing" / "opvdb.zip"
SOURCE_PATH = (
    ROOT
    / "data"
    / "external"
    / "optical_photocatalysis"
    / "DB for chromophore_Sci_Data_rev02.csv"
)
SAFE_SOURCE_SUMMARY = RESULTS / "optical_supervised_source_summary.json"
SAFE_SOURCE_VERIFIED = (
    RESULTS / "optical_supervised_source_VERIFIED.json"
)
SAFE_CHECKPOINT_DIR = RESULTS / "optical_supervised_source_checkpoints"
OPV_SOURCE_FEATURES = RESULTS / "opv_optical_source_features.csv"
OPV_SOURCE_SUMMARY = RESULTS / "opv_optical_source_summary.json"

FORBIDDEN_METADATA_COLUMNS = {
    "pce",
    "pce_avg",
    "pce_best",
    "pce_recomputed",
    "pce_relative_error_percent",
    "voc",
    "jsc",
    "ff",
    "homo_d",
    "lumo_d",
    "eg_d",
    "homo_a",
    "lumo_a",
    "eg_a",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_zip_member(
    archive: zipfile.ZipFile, expected: str
) -> str:
    names = {
        name.replace("\\", "/"): name for name in archive.namelist()
    }
    normalized = expected.replace("\\", "/")
    require(normalized in names, f"Missing normalized ZIP member: {expected}")
    return names[normalized]


def verify_static_freeze(
    design: dict[str, Any], freeze: dict[str, Any]
) -> None:
    anchored = {
        "design_sha256": DESIGN_PATH,
        "audit_sha256": HERE / "audit_opv_optical_external_pair.py",
        "draw_sha256": HERE / "prepare_opv_optical_draws.py",
        "source_feature_sha256": (
            HERE / "prepare_opv_optical_source_features.py"
        ),
        "optical_base_sha256": (
            HERE / "prepare_optical_photocatalysis_donor_features.py"
        ),
        "optical_pretrain_sha256": (
            HERE / "pretrain_optical_source_chemprop.py"
        ),
        "optical_config_sha256": (
            HERE / "optical_supervised_borrowing_config.json"
        ),
        "run_sha256": HERE / "run_opv_optical_external_borrowing.py",
        "summarizer_sha256": (
            HERE / "summarize_opv_optical_external_borrowing.py"
        ),
        "verifier_sha256": (
            HERE / "verify_opv_optical_external_borrowing.py"
        ),
        "preflight_sha256": Path(__file__).resolve(),
        "balam_runner_sha256": (
            HERE
            / "balam"
            / "run_opv_optical_external_borrowing_balam.sh"
        ),
        "balam_prepare_sha256": (
            HERE
            / "balam"
            / "prepare_and_submit_opv_optical_external_borrowing.sh"
        ),
        "balam_base_requirements_sha256": (
            HERE / "balam" / "requirements.txt"
        ),
        "balam_opv_requirements_sha256": (
            HERE / "balam" / "requirements_opv_optical.txt"
        ),
        "portable_zip_amendment_sha256": (
            HERE / "OPV_OPTICAL_PORTABLE_ZIP_AMENDMENT.md"
        ),
        "implementation_alignment_amendment_sha256": (
            HERE
            / "OPV_OPTICAL_PREOUTCOME_IMPLEMENTATION_ALIGNMENT_AMENDMENT.md"
        ),
    }
    for key, path in anchored.items():
        require(path.exists(), f"Frozen file is absent: {path}")
        require(
            freeze[key] == sha256(path),
            f"Frozen implementation hash drift: {key}",
        )
    require(
        freeze["status"].startswith("preoutcome-implementation-frozen"),
        "Implementation freeze is not preoutcome",
    )
    require(
        freeze["target_archive_sha256"] == sha256(TARGET_PATH),
        "Frozen target archive hash drift",
    )
    require(
        design["target"]["required_archive_sha256"]
        == sha256(TARGET_PATH),
        "Design target archive hash drift",
    )
    require(
        freeze["donor_file_sha256"] == sha256(SOURCE_PATH),
        "Frozen optical donor file hash drift",
    )
    require(
        design["source"]["required_sha256"] == sha256(SOURCE_PATH),
        "Design optical donor file hash drift",
    )
    with zipfile.ZipFile(TARGET_PATH) as archive:
        normalized_zip_member(archive, design["target"]["member"])


def verify_metadata_and_draws(
    design: dict[str, Any], freeze: dict[str, Any]
) -> dict[str, int]:
    audit = read_json(AUDIT_PATH)
    manifest = read_json(DRAW_MANIFEST_PATH)
    metadata_hash = sha256(METADATA_PATH)
    draw_hash = sha256(DRAW_PATH)
    require(
        metadata_hash == design["outcome_free_audit"]["metadata_sha256"],
        "Metadata hash differs from design",
    )
    require(
        metadata_hash == freeze["metadata_sha256"],
        "Metadata hash differs from implementation freeze",
    )
    require(
        audit["status"] == "metadata-audited-row-outcomes-unopened",
        "Outcome-free audit status is not sealed",
    )
    require(
        audit["outcome_sentinel"]["metadata_sha256"] == metadata_hash,
        "Audit metadata hash drift",
    )
    require(
        draw_hash == freeze["label_draw_file_sha256"],
        "Frozen label draw hash drift",
    )
    require(
        manifest["design_sha256"] == sha256(DESIGN_PATH),
        "Draw manifest design drift",
    )
    require(
        manifest["metadata_sha256"] == metadata_hash,
        "Draw manifest metadata drift",
    )
    require(
        manifest["draw_sha256"] == draw_hash,
        "Draw manifest file drift",
    )

    metadata = pd.read_csv(
        METADATA_PATH, dtype={"id": "string"}, low_memory=False
    )
    columns_lower = {column.lower() for column in metadata.columns}
    require(
        not columns_lower.intersection(FORBIDDEN_METADATA_COLUMNS),
        "A target outcome or target energy column entered metadata",
    )
    require(
        len(metadata) == int(design["target"]["expected_rows"]),
        "Metadata row count drift",
    )
    require(metadata["id"].notna().all(), "Metadata ID is missing")
    require(metadata["id"].is_unique, "Metadata IDs are not unique")
    require(
        metadata["doi_normalized_audit"].notna().all(),
        "Normalized DOI is missing",
    )
    split_counts = metadata.groupby("doi_normalized_audit")[
        "external_doi_holdout"
    ].nunique()
    require(
        bool((split_counts == 1).all()),
        "A DOI group crosses the external/development boundary",
    )
    external = metadata["external_doi_holdout"].astype(bool)
    qualified = (
        external
        & (metadata["donor_solid_source_support"] >= 0.20)
        & (metadata["acceptor_solid_source_support"] >= 0.20)
    )
    require(
        int(external.sum())
        == int(design["outcome_free_audit"]["external_holdout_rows"]),
        "External row count drift",
    )
    require(
        int(
            metadata.loc[external, "doi_normalized_audit"].nunique()
        )
        == int(design["outcome_free_audit"]["external_holdout_dois"]),
        "External DOI count drift",
    )
    require(
        int(qualified.sum())
        == int(
            design["outcome_free_audit"][
                "source_qualified_external_rows"
            ]
        ),
        "Source-qualified external row count drift",
    )
    require(
        int(audit["source"]["exact_target_molecule_overlap_solid"]) == 0,
        "Solid optical source contains an exact OPV molecule",
    )
    require(
        int(audit["source"]["target_doi_overlap_solid"]) == 0,
        "Solid optical source contains an OPV DOI",
    )

    draws = pd.read_csv(DRAW_PATH, dtype={"id": "string"})
    require(
        len(draws) == int(manifest["rows"]),
        "Label draw row count drift",
    )
    external_ids = set(metadata.loc[external, "id"].astype(str))
    require(
        not external_ids.intersection(draws["id"].astype(str)),
        "An external record entered a label draw",
    )
    expected_budgets = {
        int(value) for value in design["split_and_ood"]["label_budgets"]
    }
    require(
        set(draws["budget"].astype(int)) == expected_budgets,
        "Label budget set drift",
    )
    counts = draws.groupby(["budget", "repeat"])["id"].nunique()
    require(
        all(int(count) == int(budget) for (budget, _), count in counts.items()),
        "A label draw has the wrong size or duplicate IDs",
    )
    require(
        counts.groupby(level=0).size().eq(
            int(design["split_and_ood"]["repeats"])
        ).all(),
        "A budget has the wrong repeat count",
    )
    return {
        "metadata_rows": int(len(metadata)),
        "external_rows": int(external.sum()),
        "external_dois": int(
            metadata.loc[external, "doi_normalized_audit"].nunique()
        ),
        "source_qualified_external_rows": int(qualified.sum()),
        "draw_rows": int(len(draws)),
    }


def verify_safe_source_inputs(freeze: dict[str, Any]) -> None:
    require(
        sha256(SAFE_SOURCE_SUMMARY)
        == freeze["solid_source_summary_sha256"],
        "Verified solid source summary drift",
    )
    require(
        sha256(SAFE_SOURCE_VERIFIED)
        == freeze["solid_source_verified_sha256"],
        "Verified solid source certificate drift",
    )
    summary = read_json(SAFE_SOURCE_SUMMARY)
    certificate = read_json(SAFE_SOURCE_VERIFIED)
    require(
        summary["status"] == "source-representation-ready",
        "Solid optical source is not ready",
    )
    require(
        bool(summary["primary_scope_gate_passed"]),
        "Solid optical source skill gate did not pass",
    )
    require(
        certificate["status"]
        == "verified-complete-source-representation",
        "Solid optical source certificate is incomplete",
    )
    for name, expected in freeze[
        "solid_source_checkpoint_sha256"
    ].items():
        path = SAFE_CHECKPOINT_DIR / name
        require(path.exists(), f"Frozen solid checkpoint is absent: {name}")
        require(
            sha256(path) == expected,
            f"Frozen solid checkpoint drift: {name}",
        )
        require(
            summary["checkpoint_sha256"][name] == expected,
            f"Solid source summary checkpoint drift: {name}",
        )


def verify_strict_source_ready(
    design: dict[str, Any], metadata_counts: dict[str, int]
) -> dict[str, int]:
    summary = read_json(OPV_SOURCE_SUMMARY)
    require(
        summary["status"] == "strict-source-features-ready",
        "Strict OPV source features are not ready",
    )
    require(
        summary["global_mode"]
        == "strict-target-and-doi-excluded-retrain",
        "State-blind source was not retrained after strict exclusions",
    )
    require(
        summary["design_sha256"] == sha256(DESIGN_PATH),
        "Strict source design drift",
    )
    require(
        summary["metadata_sha256"] == sha256(METADATA_PATH),
        "Strict source metadata drift",
    )
    require(
        summary["source_sha256"] == sha256(SOURCE_PATH),
        "Strict source donor file drift",
    )
    require(
        summary["feature_sha256"] == sha256(OPV_SOURCE_FEATURES),
        "Strict source feature file drift",
    )
    require(
        summary["shared_tasks"]
        == [
            "Absorption max (nm)",
            "Emission max (nm)",
            "Quantum yield",
        ],
        "Strict source admitted task set drift",
    )
    features = pd.read_csv(OPV_SOURCE_FEATURES)
    require(
        features["canonical_smiles"].notna().all(),
        "Strict source feature molecule key is missing",
    )
    require(
        features["canonical_smiles"].is_unique,
        "Strict source feature molecule keys are duplicated",
    )
    numeric = features.drop(columns=["canonical_smiles"]).to_numpy(float)
    require(np.isfinite(numeric).all(), "Strict source feature is nonfinite")
    metadata = pd.read_csv(
        METADATA_PATH,
        usecols=[
            "donor_smiles_canonical",
            "acceptor_smiles_canonical",
        ],
        low_memory=False,
    )
    expected_molecules = (
        set(metadata["donor_smiles_canonical"].dropna().astype(str))
        | set(metadata["acceptor_smiles_canonical"].dropna().astype(str))
    ) - {""}
    require(
        set(features["canonical_smiles"].astype(str)) == expected_molecules,
        "Strict source features do not cover exactly the target molecules",
    )
    require(
        len(features) == int(summary["target_unique_molecules"]),
        "Strict source feature row count drift",
    )
    for relative, expected in summary["checkpoint_sha256"].items():
        path = ROOT / relative
        require(path.exists(), f"Strict source checkpoint absent: {relative}")
        require(
            sha256(path) == expected,
            f"Strict source checkpoint drift: {relative}",
        )
    return metadata_counts | {
        "strict_source_molecules": int(len(features)),
        "strict_source_feature_columns": int(features.shape[1] - 1),
        "strict_source_checkpoints": int(
            len(summary["checkpoint_sha256"])
        ),
    }


def verify_tar_archive(archive_path: Path, freeze: dict[str, Any]) -> int:
    expected_paths = [
        DESIGN_PATH,
        FREEZE_PATH,
        HERE / "OPV_OPTICAL_EXTERNAL_BORROWING_PROTOCOL.md",
        HERE / "OPV_OPTICAL_PORTABLE_ZIP_AMENDMENT.md",
        HERE
        / "OPV_OPTICAL_PREOUTCOME_IMPLEMENTATION_ALIGNMENT_AMENDMENT.md",
        HERE / "audit_opv_optical_external_pair.py",
        HERE / "prepare_opv_optical_draws.py",
        HERE / "prepare_opv_optical_source_features.py",
        HERE / "preflight_opv_optical_external_borrowing.py",
        HERE / "run_opv_optical_external_borrowing.py",
        HERE / "summarize_opv_optical_external_borrowing.py",
        HERE / "verify_opv_optical_external_borrowing.py",
        AUDIT_PATH,
        METADATA_PATH,
        DRAW_PATH,
        DRAW_MANIFEST_PATH,
        SAFE_SOURCE_SUMMARY,
        SAFE_SOURCE_VERIFIED,
        HERE / "balam" / "requirements.txt",
        HERE / "balam" / "requirements_opv_optical.txt",
        HERE / "balam" / "run_opv_optical_external_borrowing_balam.sh",
        HERE
        / "balam"
        / "prepare_and_submit_opv_optical_external_borrowing.sh",
        TARGET_PATH,
        SOURCE_PATH,
        ROOT / "tests" / "test_opv_optical_external_borrowing.py",
    ]
    expected_paths.extend(
        SAFE_CHECKPOINT_DIR / name
        for name in freeze["solid_source_checkpoint_sha256"]
    )
    with tarfile.open(archive_path, "r:gz") as archive:
        members: dict[str, tarfile.TarInfo] = {}
        for member in archive.getmembers():
            normalized = member.name.replace("\\", "/").lstrip("./")
            require(
                normalized not in members,
                f"Duplicate normalized tar member: {normalized}",
            )
            members[normalized] = member
        for path in expected_paths:
            relative = path.relative_to(ROOT).as_posix()
            require(relative in members, f"Package member absent: {relative}")
            extracted = archive.extractfile(members[relative])
            require(extracted is not None, f"Package member unreadable: {relative}")
            require(
                sha256_bytes(extracted.read()) == sha256(path),
                f"Package member differs from workspace: {relative}",
            )
    return len(expected_paths)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["package", "audited", "source-ready"],
        required=True,
    )
    parser.add_argument("--archive", type=Path)
    arguments = parser.parse_args()
    design = read_json(DESIGN_PATH)
    freeze = read_json(FREEZE_PATH)
    verify_static_freeze(design, freeze)
    counts = verify_metadata_and_draws(design, freeze)
    verify_safe_source_inputs(freeze)
    if arguments.stage == "source-ready":
        counts = verify_strict_source_ready(design, counts)
    archive_members = None
    if arguments.archive is not None:
        require(
            arguments.stage == "package",
            "Archive verification is valid only at package stage",
        )
        archive_members = verify_tar_archive(arguments.archive, freeze)
    result = {
        "status": "verified-complete-preoutcome",
        "stage": arguments.stage,
        "verified_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "freeze_sha256": sha256(FREEZE_PATH),
        "preflight_sha256": sha256(Path(__file__)),
        "metadata_sha256": sha256(METADATA_PATH),
        "draw_sha256": sha256(DRAW_PATH),
        "target_archive_sha256": sha256(TARGET_PATH),
        "source_sha256": sha256(SOURCE_PATH),
        "archive_verified_members": archive_members,
        "counts": counts,
        "outcome_access": (
            "No OPV PCE, Voc, Jsc, FF or target energy value was read."
        ),
    }
    output = RESULTS / f"opv_optical_preoutcome_{arguments.stage}_VERIFIED.json"
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
