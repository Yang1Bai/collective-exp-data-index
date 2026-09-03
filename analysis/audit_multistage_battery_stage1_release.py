"""Audit the authorized Stage 1 battery endpoints and build the source table."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1"
ENDPOINTS = RESULT_DIR / "stage1_capacity_endpoints.csv"
RELEASE_AUDIT = RESULT_DIR / "STAGE1_RELEASE_AUDIT.json"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
SOURCE_TABLE = RESULT_DIR / "stage1_source_table.csv"
AUDIT = RESULT_DIR / "STAGE1_DATA_QUALITY_AUDIT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe(series: pd.Series) -> dict[str, float]:
    return {
        "min": float(series.min()),
        "q01": float(series.quantile(0.01)),
        "median": float(series.median()),
        "mean": float(series.mean()),
        "q99": float(series.quantile(0.99)),
        "max": float(series.max()),
    }


def condition_id(row: pd.Series) -> str:
    if row["type"] == "k":
        values = ["k", row["amb_temp_tp"], row["soc_max_tp"]]
    else:
        values = ["z", row["amb_temp_tp"], row["soc_max_tp"], row["dod_tp"], row["c_ch_tp"], row["c_dch_tp"]]
    return "|".join(str(value) for value in values)


def main() -> None:
    errors: list[str] = []
    release = json.loads(RELEASE_AUDIT.read_text(encoding="utf-8"))
    if release.get("status") != "verified-complete-stage1-release":
        errors.append("Stage 1 release audit is not complete")
    if release.get("stage2_archives_downloaded") != 0 or release.get("stage2_numeric_data_rows_opened") is not False:
        errors.append("Stage 2 seal failed")

    endpoints = pd.read_csv(ENDPOINTS, dtype={"file_id": str, "serial_internal": str, "serial": str, "stage": str})
    meta = pd.read_csv(META, dtype={"serial_internal": str, "serial": str, "stage": str})
    if len(endpoints) != 141 or set(endpoints["stage"]) != {"1"}:
        errors.append("endpoint ledger is not exactly 141 Stage 1 cells")
    counts = endpoints["status"].value_counts().to_dict()
    if counts != {"extracted-stage1": 138, "missing-endpoint": 3}:
        errors.append(f"unexpected endpoint status counts: {counts}")

    stage1_meta = meta.loc[meta["stage"].eq("1")].copy()
    source = endpoints.merge(
        stage1_meta,
        on=["serial_internal", "serial", "stage", "lab", "type", "tp", "cell", "sampling"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_meta"),
        indicator=True,
    )
    if not source["_merge"].eq("both").all():
        errors.append("Stage 1 endpoint-to-metadata join is incomplete")
    source.drop(columns=["_merge"], inplace=True)
    source["condition_group"] = source.apply(condition_id, axis=1)
    evaluable = source.loc[source["status"].eq("extracted-stage1")].copy()

    numeric = [
        "q_rpt_et_Ah", "q_rpt_at_Ah", "q_rel_end_percent",
        "q_charge_et_Ah", "q_discharge_et_Ah", "q_charge_at_Ah", "q_discharge_at_Ah",
    ]
    if not np.isfinite(evaluable[numeric].to_numpy(dtype=float)).all():
        errors.append("nonfinite frozen capacity value found")
    if not (evaluable[numeric] > 0).all().all():
        errors.append("nonpositive frozen capacity value found")

    group_counts = evaluable.groupby("type")["condition_group"].nunique().to_dict()
    missing = source.loc[source["status"].eq("missing-endpoint")]
    missing_groups = sorted(missing["condition_group"].unique())
    if group_counts != {"k": 11, "z": 24}:
        errors.append(f"unexpected evaluable Stage 1 condition counts: {group_counts}")

    source.to_csv(SOURCE_TABLE, index=False, lineterminator="\n")
    result = {
        "status": "verified-stage1-source-ready" if not errors else "invalid",
        "stage1_cells": len(source),
        "evaluable_stage1_cells": len(evaluable),
        "missing_endpoint_cells": len(missing),
        "missing_endpoint_condition_groups": missing_groups,
        "evaluable_condition_groups": group_counts,
        "endpoint_summary": {
            "q_rpt_et_Ah": describe(evaluable["q_rpt_et_Ah"]),
            "q_rpt_at_Ah": describe(evaluable["q_rpt_at_Ah"]),
            "q_rel_end_percent": describe(evaluable["q_rel_end_percent"]),
            "charge_discharge_disagreement_et_percent": describe(evaluable["charge_discharge_disagreement_et_percent"]),
            "charge_discharge_disagreement_at_percent": describe(evaluable["charge_discharge_disagreement_at_percent"]),
        },
        "charge_discharge_sensitivity": {
            "max_absolute_retention_difference_percentage_points": float(
                (evaluable["q_rel_charge_percent"] - evaluable["q_rel_discharge_percent"]).abs().max()
            ),
            "mean_absolute_retention_difference_percentage_points": float(
                (evaluable["q_rel_charge_percent"] - evaluable["q_rel_discharge_percent"]).abs().mean()
            ),
        },
        "stage2_archives_downloaded": 0,
        "stage2_numeric_data_rows_opened": False,
        "endpoint_table_sha256": sha256(ENDPOINTS),
        "release_audit_sha256": sha256(RELEASE_AUDIT),
        "experiments_meta_sha256": sha256(META),
        "source_table_sha256": sha256(SOURCE_TABLE),
        "claim_guard": "This audit establishes Stage 1 source-data integrity only. It contains no Stage 2 outcome evidence and cannot support an OOD-transfer claim.",
        "errors": errors,
    }
    AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
