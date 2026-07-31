"""Verify state-matched donor features and source-only admission gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score

import prepare_optical_photocatalysis_donor_features as base

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_transfer_method_discovery_config.json"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
METADATA_PATH = HERE / "results" / "optical_photocatalysis_target_metadata.csv"
IMPLEMENTATION_PATH = HERE / "prepare_optical_state_matched_donor_features.py"
FEATURE_PATH = HERE / "results" / "optical_state_matched_donor_features.csv"
OOF_PATH = (
    HERE / "results" / "optical_state_matched_donor_oof_predictions.csv"
)
SUMMARY_PATH = HERE / "results" / "optical_state_matched_donor_summary.json"
VERIFIED_PATH = (
    HERE / "results" / "optical_state_matched_donor_VERIFIED.json"
)

SEED = 20260726
RANK_SERIALIZATION_ATOL = 5e-5


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    metadata = pd.read_csv(METADATA_PATH)
    features = pd.read_csv(FEATURE_PATH)
    oof = pd.read_csv(OOF_PATH)
    expected_hashes = {
        "design_sha256": file_hash(DESIGN_PATH),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "target_metadata_sha256": file_hash(METADATA_PATH),
        "implementation_sha256": file_hash(IMPLEMENTATION_PATH),
        "feature_sha256": file_hash(FEATURE_PATH),
        "oof_sha256": file_hash(OOF_PATH),
    }
    for field, expected in expected_hashes.items():
        if summary[field] != expected:
            raise AssertionError(f"Hash mismatch: {field}")
    if len(features) != len(metadata):
        raise AssertionError("State feature row count mismatch")
    if not features["target_key"].equals(metadata["target_key"]):
        raise AssertionError("State feature target keys do not align")

    gate = config["source_modeling"]["property_gate"]
    recomputed: dict[str, dict[str, object]] = {}
    for scope_index, (scope_name, property_items) in enumerate(
        summary["properties"].items()
    ):
        recomputed[scope_name] = {}
        support_column = f"support_{scope_name}"
        if support_column not in features:
            raise AssertionError(f"Missing support column: {scope_name}")
        support = features[support_column].to_numpy(float)
        if not np.isfinite(support).all() or np.any((support < 0) | (support > 1)):
            raise AssertionError(f"Invalid support values: {scope_name}")
        expected_admitted_columns: list[str] = []
        for property_index, (property_name, reported) in enumerate(
            property_items.items()
        ):
            if reported["status"] == "size-gate-failed":
                if reported["admitted"]:
                    raise AssertionError("Size-gate failure was admitted")
                recomputed[scope_name][property_name] = {
                    "status": "size-gate-failed",
                    "admitted": False,
                }
                continue
            rows = oof[
                (oof["scope"] == scope_name)
                & (oof["property"] == property_name)
            ]
            if len(rows) != int(reported["unique_molecules"]):
                raise AssertionError(
                    f"OOF row mismatch: {scope_name}/{property_name}"
                )
            observed = rows["observed"].to_numpy(float)
            predicted = rows["predicted"].to_numpy(float)
            r2 = float(r2_score(observed, predicted))
            spearman = float(stats.spearmanr(observed, predicted).statistic)
            ci = base.bootstrap_spearman_lower(
                observed,
                predicted,
                rows["scaffold"].astype(str).to_numpy(),
                SEED + 1000000 + 100 * scope_index + property_index,
            )
            if not np.isclose(r2, float(reported["oof_r2"]), atol=1e-12):
                raise AssertionError(f"R2 mismatch: {scope_name}/{property_name}")
            if (
                abs(spearman - float(reported["oof_spearman"]))
                > RANK_SERIALIZATION_ATOL
            ):
                raise AssertionError(
                    f"Spearman mismatch: {scope_name}/{property_name}"
                )
            if (
                np.max(
                    np.abs(
                        np.asarray(ci)
                        - np.asarray(
                            reported["scaffold_bootstrap_spearman_ci95"],
                            dtype=float,
                        )
                    )
                )
                > RANK_SERIALIZATION_ATOL
            ):
                raise AssertionError(
                    f"Bootstrap mismatch: {scope_name}/{property_name}"
                )
            admitted = bool(
                len(rows) >= int(gate["minimum_unique_molecules"])
                and r2 > float(gate["oof_r2_greater_than"])
                and spearman > float(gate["oof_spearman_greater_than"])
                and ci[0]
                > float(gate["bootstrap_95pct_lower_spearman_greater_than"])
            )
            if admitted != bool(reported["admitted"]):
                raise AssertionError(
                    f"Admission mismatch: {scope_name}/{property_name}"
                )
            slug = str(reported["slug"])
            prediction_column = f"pred_{scope_name}_{slug}"
            uncertainty_column = f"unc_{scope_name}_{slug}"
            for column in (prediction_column, uncertainty_column):
                if column not in features:
                    raise AssertionError(f"Missing feature: {column}")
                if not np.isfinite(features[column].to_numpy(float)).all():
                    raise AssertionError(f"Nonfinite feature: {column}")
            if admitted:
                expected_admitted_columns.extend(
                    [prediction_column, uncertainty_column]
                )
            recomputed[scope_name][property_name] = {
                "oof_r2": r2,
                "oof_spearman": spearman,
                "scaffold_bootstrap_spearman_ci95": list(ci),
                "admitted": admitted,
            }
        if (
            expected_admitted_columns
            != summary["admitted_feature_columns_by_scope"][scope_name]
        ):
            raise AssertionError(f"Admitted feature list mismatch: {scope_name}")

    verified = {
        "status": "verified-complete",
        **expected_hashes,
        "summary_sha256": file_hash(SUMMARY_PATH),
        "feature_rows": int(len(features)),
        "oof_rows": int(len(oof)),
        "recomputed": recomputed,
        "rank_serialization_absolute_tolerance": RANK_SERIALIZATION_ATOL,
        "outcome_guard": "No recipient HER value was used in verification.",
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
