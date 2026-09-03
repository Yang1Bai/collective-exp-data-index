"""Freeze every outcome-free CCA-v2 applicability value before Stage 2 release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
FEATURES = DIR / "stage2_outcome_free_source_features.csv"
SPLITS = DIR / "stage2_outer_split_plan.json"
SOURCE_FREEZE = DIR / "STAGE1_SOURCE_FREEZE.json"
META = ROOT / "analysis" / "results" / "multistage_battery_file_map" / "experiments_meta.csv"
OUTPUT = DIR / "stage2_applicability_plan.csv"
AUDIT = DIR / "STAGE2_APPLICABILITY_FREEZE.json"
CONDITIONS = {"k": ["amb_temp_tp", "soc_max_tp"], "z": ["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]}
THRESHOLD = 0.20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scaled(frame: pd.DataFrame, scaler: dict) -> np.ndarray:
    columns = scaler["columns"]
    minima = np.array([scaler["minima"][column] for column in columns])
    ranges = np.array([scaler["ranges"][column] for column in columns])
    return (frame[columns].to_numpy(dtype=float) - minima) / ranges


def distance_to_groups(candidate: pd.DataFrame, reference: pd.DataFrame, scaler: dict) -> np.ndarray:
    query = scaled(candidate, scaler)
    support = scaled(reference, scaler)
    return np.sqrt(((query[:, None, :] - support[None, :, :]) ** 2).sum(axis=2)).min(axis=1)


def append_scope(
    records: list[dict],
    candidates: pd.DataFrame,
    target_distance: np.ndarray,
    scope: str,
    outer_heldout: str,
    nested_heldout: str = "",
) -> None:
    for (_, row), d_target in zip(candidates.iterrows(), target_distance):
        applicability = (
            np.exp(-(float(row["source_distance"]) ** 2))
            * np.exp(-(float(d_target) ** 2))
            * np.exp(-0.5 * (float(row["source_uncertainty_normalized"]) ** 2))
            * float(row["provenance_compatibility"])
        )
        borrow = applicability >= THRESHOLD
        records.append({
            "scope": scope,
            "outer_heldout_group": outer_heldout,
            "nested_heldout_group": nested_heldout,
            "candidate_group": row["condition_group"],
            "file_id": row["file_id"],
            "serial_internal": row["serial_internal"],
            "serial": row["serial"],
            "type": row["type"],
            "source_distance": row["source_distance"],
            "target_distance": float(d_target),
            "source_uncertainty_normalized": row["source_uncertainty_normalized"],
            "provenance_compatibility": row["provenance_compatibility"],
            "applicability": float(applicability),
            "borrow_allowed": bool(borrow),
            "centered_source_feature": float(applicability * row["source_prediction_centered"]) if borrow else 0.0,
        })


def main() -> None:
    source = json.loads(SOURCE_FREEZE.read_text(encoding="utf-8"))
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    features = pd.read_csv(FEATURES, dtype={"file_id": str, "serial_internal": str, "serial": str})
    meta = pd.read_csv(META, dtype={"stage": str, "serial_internal": str, "serial": str})
    stage2_meta = meta.loc[meta["stage"].eq("2")]
    features = features.merge(
        stage2_meta[["serial_internal", "serial", *sorted(set(sum(CONDITIONS.values(), [])))]],
        on=["serial_internal", "serial"], how="left", validate="one_to_one",
    )
    groups = features[["type", "condition_group", *sorted(set(sum(CONDITIONS.values(), [])))]].drop_duplicates("condition_group")
    records: list[dict] = []
    for outer_heldout, split in sorted(splits.items()):
        aging_type = split["aging_type"]
        scaler = source["model_summaries"][aging_type]["condition_scaler"]
        selected = split["target_training_groups"]
        selected_by_type = split["target_training_groups_by_type"]
        outer_candidates = features.loc[features["condition_group"].eq(outer_heldout)]
        outer_reference = groups.loc[groups["condition_group"].isin(selected_by_type[aging_type])]
        append_scope(
            records, outer_candidates,
            distance_to_groups(outer_candidates, outer_reference, scaler),
            "outer_test", outer_heldout,
        )

        training_candidates = features.loc[features["condition_group"].isin(selected)]
        append_scope(
            records, training_candidates, np.zeros(len(training_candidates)),
            "outer_train_fit", outer_heldout,
        )
        for nested_heldout in selected:
            nested_type = nested_heldout.split("|", 1)[0]
            nested_scaler = source["model_summaries"][nested_type]["condition_scaler"]
            nested_candidates = features.loc[features["condition_group"].eq(nested_heldout)]
            nested_reference = groups.loc[groups["condition_group"].isin([
                group for group in selected_by_type[nested_type] if group != nested_heldout
            ])]
            append_scope(
                records, nested_candidates,
                distance_to_groups(nested_candidates, nested_reference, nested_scaler),
                "nested_validation", outer_heldout, nested_heldout,
            )

    table = pd.DataFrame(records).sort_values(
        ["type", "outer_heldout_group", "scope", "nested_heldout_group", "candidate_group", "file_id"]
    )
    table.to_csv(OUTPUT, index=False, lineterminator="\n")
    scope_counts = table["scope"].value_counts().to_dict()
    outer = table.loc[table["scope"].eq("outer_test")]
    audit = {
        "status": "verified-outcome-free-applicability-frozen",
        "rows": len(table),
        "scope_counts": scope_counts,
        "outer_test_rows": len(outer),
        "outer_test_groups": int(outer["outer_heldout_group"].nunique()),
        "outer_test_borrowing_groups": int(outer.loc[outer["borrow_allowed"], "outer_heldout_group"].nunique()),
        "outer_test_borrowing_groups_by_type": {
            aging_type: int(part.loc[part["borrow_allowed"], "outer_heldout_group"].nunique())
            for aging_type, part in outer.groupby("type")
        },
        "applicability_threshold": THRESHOLD,
        "stage2_numeric_outcomes_opened": False,
        "stage2_source_features_sha256": sha256(FEATURES),
        "outer_split_plan_sha256": sha256(SPLITS),
        "applicability_plan_sha256": sha256(OUTPUT),
        "claim_guard": "Borrowing locations are fixed without Stage 2 outcomes. Coverage is a design fact, not evidence of predictive benefit.",
        "errors": [],
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
