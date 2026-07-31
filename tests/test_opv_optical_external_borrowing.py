from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
sys.path.insert(0, str(ANALYSIS))

import audit_opv_optical_external_pair as audit  # noqa: E402
import run_opv_optical_external_borrowing as run  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_zip_member_resolution_is_cross_platform() -> None:
    class BackslashArchive:
        @staticmethod
        def namelist() -> list[str]:
            return [
                r"data\opv_devices_strict_molecular_benchmark.csv"
            ]

    expected = "data/opv_devices_strict_molecular_benchmark.csv"
    stored = r"data\opv_devices_strict_molecular_benchmark.csv"
    assert audit.portable_zip_member(BackslashArchive(), expected) == stored
    assert run.portable_zip_member(BackslashArchive(), expected) == stored


def test_numeric_state_scaling_uses_only_labelled_rows() -> None:
    raw = np.asarray([[1.0], [3.0], [1000.0], [np.nan]])
    training, external = run.numeric_state_blocks(
        raw,
        np.asarray([0, 1]),
        np.asarray([2, 3]),
    )
    assert np.allclose(training[:, 0], [-1.0, 1.0])
    assert np.allclose(training[:, 1], [0.0, 0.0])
    assert external[0, 0] > 900.0
    assert external[1, 0] == 0.0
    assert external[1, 1] == 1.0


def test_physics_recombined_pce_is_a_declared_metric() -> None:
    truth = np.asarray(
        [[10.0, 1.0, 20.0, 50.0], [12.0, 1.1, 22.0, 55.0]]
    )
    prediction = np.asarray(
        [[9.0, 0.8, 20.0, 50.0], [11.0, 1.0, 25.0, 40.0]]
    )
    rows = run.metric_rows(
        truth,
        prediction,
        np.asarray([True, True]),
        pd.DataFrame(
            {
                "doi_normalized_audit": [
                    "10.test/example-a",
                    "10.test/example-b",
                ]
            }
        ),
        {"budget": 1, "repeat": 0, "seed": 1},
        "state_aware_target_only",
        "extra_trees",
        "qualified_hard_ood_40pct",
    )
    by_outcome = {row["outcome"]: row for row in rows}
    assert set(by_outcome) == set(run.METRIC_OUTCOMES)
    assert by_outcome["pce_physics_recombined"]["rmse"] == 2.0


def test_outcome_free_metadata_and_draws_match_frozen_design() -> None:
    design_path = ANALYSIS / "opv_optical_external_borrowing_design.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    metadata_path = RESULTS / "opv_optical_target_metadata_no_outcomes.csv"
    draw_path = RESULTS / "opv_optical_label_draws.csv"
    manifest = json.loads(
        (RESULTS / "opv_optical_label_draws_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert sha256(metadata_path) == design["outcome_free_audit"][
        "metadata_sha256"
    ]
    assert manifest["design_sha256"] == sha256(design_path)
    assert manifest["draw_sha256"] == sha256(draw_path)


def test_metadata_contains_no_target_outcome_or_energy_columns() -> None:
    columns = {
        value.lower()
        for value in pd.read_csv(
            RESULTS / "opv_optical_target_metadata_no_outcomes.csv",
            nrows=0,
        ).columns
    }
    forbidden = {
        "pce",
        "voc",
        "jsc",
        "ff",
        "donor_homo",
        "donor_lumo",
        "acceptor_homo",
        "acceptor_lumo",
    }
    assert not columns.intersection(forbidden)


def test_external_doi_groups_never_enter_label_draws() -> None:
    metadata = pd.read_csv(
        RESULTS / "opv_optical_target_metadata_no_outcomes.csv",
        usecols=["id", "external_doi_holdout"],
        dtype={"id": "string"},
    )
    draws = pd.read_csv(
        RESULTS / "opv_optical_label_draws.csv",
        usecols=["id"],
        dtype={"id": "string"},
    )
    external_ids = set(
        metadata.loc[metadata["external_doi_holdout"], "id"].astype(str)
    )
    assert not external_ids.intersection(draws["id"].astype(str))


def test_implementation_freeze_anchors_formal_code() -> None:
    freeze = json.loads(
        (ANALYSIS / "opv_optical_implementation_freeze.json").read_text(
            encoding="utf-8"
        )
    )
    anchored = {
        "design_sha256": ANALYSIS
        / "opv_optical_external_borrowing_design.json",
        "audit_sha256": ANALYSIS / "audit_opv_optical_external_pair.py",
        "draw_sha256": ANALYSIS / "prepare_opv_optical_draws.py",
        "source_feature_sha256": ANALYSIS
        / "prepare_opv_optical_source_features.py",
        "optical_base_sha256": ANALYSIS
        / "prepare_optical_photocatalysis_donor_features.py",
        "optical_pretrain_sha256": ANALYSIS
        / "pretrain_optical_source_chemprop.py",
        "optical_config_sha256": ANALYSIS
        / "optical_supervised_borrowing_config.json",
        "run_sha256": ANALYSIS
        / "run_opv_optical_external_borrowing.py",
        "summarizer_sha256": ANALYSIS
        / "summarize_opv_optical_external_borrowing.py",
        "verifier_sha256": ANALYSIS
        / "verify_opv_optical_external_borrowing.py",
        "preflight_sha256": ANALYSIS
        / "preflight_opv_optical_external_borrowing.py",
        "balam_runner_sha256": ANALYSIS
        / "balam"
        / "run_opv_optical_external_borrowing_balam.sh",
        "balam_prepare_sha256": ANALYSIS
        / "balam"
        / "prepare_and_submit_opv_optical_external_borrowing.sh",
        "balam_base_requirements_sha256": ANALYSIS
        / "balam"
        / "requirements.txt",
        "balam_opv_requirements_sha256": ANALYSIS
        / "balam"
        / "requirements_opv_optical.txt",
        "portable_zip_amendment_sha256": ANALYSIS
        / "OPV_OPTICAL_PORTABLE_ZIP_AMENDMENT.md",
        "implementation_alignment_amendment_sha256": ANALYSIS
        / "OPV_OPTICAL_PREOUTCOME_IMPLEMENTATION_ALIGNMENT_AMENDMENT.md",
    }
    for key, path in anchored.items():
        assert freeze[key] == sha256(path)
