"""Independently verify the development-only recipient admission decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_photocatalysis_development_gate_config.json"
IMPLEMENTATION_PATH = (
    HERE / "run_optical_photocatalysis_development_gate.py"
)
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
SOURCE_SKILL_PATH = HERE / "results" / "optical_photocatalysis_source_skill.json"
DONOR_FEATURE_PATH = (
    HERE / "results" / "optical_photocatalysis_donor_features.csv"
)
DRAW_PATH = HERE / "results" / "optical_photocatalysis_development_draws.csv"
DRAW_MANIFEST_PATH = (
    HERE / "results" / "optical_photocatalysis_development_draws_manifest.json"
)
METRICS_PATH = (
    HERE / "results" / "optical_photocatalysis_development_metrics.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_photocatalysis_development_gate.json"
)
VERIFIED_PATH = (
    HERE / "results" / "optical_photocatalysis_development_gate_VERIFIED.json"
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    source_skill = json.loads(SOURCE_SKILL_PATH.read_text(encoding="utf-8"))
    if summary["status"] == "development-not-run-source-abstained":
        if source_skill["admitted_properties"]:
            raise AssertionError("Source abstention status is inconsistent")
        verified = {
            "status": "verified-source-abstention",
            "source_summary_sha256": file_hash(SOURCE_SKILL_PATH),
            "development_summary_sha256": file_hash(SUMMARY_PATH),
            "blind_release_allowed": False,
        }
        VERIFIED_PATH.write_text(
            json.dumps(verified, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(verified, indent=2))
        return

    expected_hashes = {
        "design_sha256": file_hash(DESIGN_PATH),
        "implementation_config_sha256": file_hash(CONFIG_PATH),
        "implementation_sha256": file_hash(IMPLEMENTATION_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "source_skill_sha256": file_hash(SOURCE_SKILL_PATH),
        "donor_feature_sha256": file_hash(DONOR_FEATURE_PATH),
        "development_draw_manifest_sha256": file_hash(DRAW_MANIFEST_PATH),
        "development_draw_sha256": file_hash(DRAW_PATH),
        "metrics_sha256": file_hash(METRICS_PATH),
    }
    for field, expected in expected_hashes.items():
        if summary[field] != expected:
            raise AssertionError(f"Hash mismatch: {field}")

    metrics = pd.read_csv(METRICS_PATH)
    expected_methods = set(config["methods"])
    observed_methods = set(metrics["method"])
    if observed_methods != expected_methods:
        raise AssertionError("Development methods changed")
    if set(metrics["budget"]) != {30, 60, 120}:
        raise AssertionError("Development budgets changed")
    for budget in (30, 60, 120):
        rows = metrics[metrics["budget"] == budget]
        if rows["repeat"].nunique() != 100:
            raise AssertionError(f"Repeat count changed at budget {budget}")
        if len(rows) != 100 * len(expected_methods):
            raise AssertionError(f"Metric row count changed at budget {budget}")
    if metrics[["rmse", "mae"]].isna().any().any():
        raise AssertionError("Missing primary development metric")

    primary = metrics[metrics["budget"] == 60]
    mean_rmse = primary.groupby("method")["rmse"].mean()
    selected_form = (
        "raw"
        if mean_rmse["target_structure_plus_donor_raw"]
        <= mean_rmse["target_structure_plus_donor_rank"]
        else "rank"
    )
    if selected_form != summary["selected_feature_form"]:
        raise AssertionError("Feature-form selection mismatch")
    donor_method = f"target_structure_plus_donor_{selected_form}"
    shuffled_method = (
        f"target_structure_plus_shuffled_donor_{selected_form}"
    )
    pivot = primary.pivot(index="repeat", columns="method", values="rmse")
    donor_gain = (
        pivot["target_structure_only"] - pivot[donor_method]
    ) / pivot["target_structure_only"]
    shuffled_gain = (
        pivot["target_structure_only"] - pivot[shuffled_method]
    ) / pivot["target_structure_only"]
    if not np.isclose(
        donor_gain.mean(),
        float(summary["primary_mean_relative_rmse_gain"]),
        atol=1e-12,
    ):
        raise AssertionError("Primary gain mismatch")
    if not np.isclose(
        shuffled_gain.median(),
        float(summary["matched_shuffled_median_relative_gain"]),
        atol=1e-12,
    ):
        raise AssertionError("Shuffled-control gain mismatch")
    threshold = float(
        config["development_admission"][
            "minimum_mean_paired_relative_rmse_gain"
        ]
    )
    admitted = bool(
        donor_gain.mean() >= threshold
        and donor_gain.mean() > shuffled_gain.median()
    )
    if admitted != bool(summary["admitted_to_blind"]):
        raise AssertionError("Development gate decision mismatch")
    expected_status = (
        "development-gate-passed"
        if admitted
        else "development-gate-abstained"
    )
    if summary["status"] != expected_status:
        raise AssertionError("Development status mismatch")

    verified = {
        "status": "verified-complete",
        "verification_mode": "portable",
        **expected_hashes,
        "development_summary_sha256": file_hash(SUMMARY_PATH),
        "metric_rows": int(len(metrics)),
        "selected_feature_form": selected_form,
        "primary_mean_relative_rmse_gain": float(donor_gain.mean()),
        "matched_shuffled_median_relative_gain": float(
            shuffled_gain.median()
        ),
        "blind_release_allowed": admitted,
        "claim_guard": (
            "A passed development gate permits the frozen blind evaluation; it "
            "does not itself establish OOD transfer."
        ),
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
