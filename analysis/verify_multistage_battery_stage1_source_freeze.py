"""Verify that source models, target features, splits, and hypothesis cards are outcome-free."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage1_source_freeze"
SUMMARY = DIR / "STAGE1_SOURCE_FREEZE.json"
FEATURES = DIR / "stage2_outcome_free_source_features.csv"
SPLITS = DIR / "stage2_outer_split_plan.json"
CARDS = ROOT / "analysis" / "multistage_battery_source_inspiration_cards.json"
APPLICABILITY = DIR / "stage2_applicability_plan.csv"
APPLICABILITY_AUDIT = DIR / "STAGE2_APPLICABILITY_FREEZE.json"


def verify() -> dict:
    errors: list[str] = []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    features = pd.read_csv(FEATURES, dtype={"file_id": str})
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    cards = json.loads(CARDS.read_text(encoding="utf-8"))
    applicability = pd.read_csv(APPLICABILITY, dtype={"file_id": str})
    applicability_audit = json.loads(APPLICABILITY_AUDIT.read_text(encoding="utf-8"))
    if summary.get("status") != "verified-stage1-source-and-stage2-outcome-free-features-frozen":
        errors.append("source freeze status failed")
    if summary.get("stage2_numeric_outcomes_opened") is not False:
        errors.append("source freeze claims Stage 2 outcome access")
    if len(features) != 138 or features["condition_group"].nunique() != 23:
        errors.append("outcome-free target feature dimensions changed")
    forbidden = {"q_rel_end_percent", "q_rpt_at_Ah", "q_rpt_et_Ah", "capacity", "retention", "target_y"}
    if set(features.columns) & forbidden:
        errors.append("Stage 2 source feature table contains a target outcome column")
    if len(splits) != 23:
        errors.append("outer split plan does not contain 23 held-out groups")
    for heldout, record in splits.items():
        selected = record["target_training_groups"]
        selected_by_type = record.get("target_training_groups_by_type", {})
        valid_budget = len(selected_by_type.get("k", [])) == 4 and len(selected_by_type.get("z", [])) == 6
        if record["heldout_group"] != heldout or heldout in selected or len(selected) != 10 or not valid_budget:
            errors.append(f"invalid outcome-free split: {heldout}")
    if cards.get("status") != "frozen-before-stage2-numeric-outcome-access" or len(cards.get("cards", [])) != 2:
        errors.append("source-inspired hypothesis cards are not frozen")
    required_card_fields = {
        "condition_region", "stage1_evidence", "expected_retention_direction",
        "physical_rationale", "matched_controls", "falsifier",
        "planned_diagnostic_measurement", "timestamp",
    }
    for card in cards.get("cards", []):
        if not required_card_fields.issubset(card):
            errors.append(f"hypothesis card is incomplete: {card.get('card_id')}")
    if applicability_audit.get("status") != "verified-outcome-free-applicability-frozen":
        errors.append("outcome-free applicability audit failed")
    if len(applicability) != 3594 or set(applicability["scope"]) != {"outer_test", "outer_train_fit", "nested_validation"}:
        errors.append("applicability plan dimensions changed")
    outer = applicability.loc[applicability["scope"].eq("outer_test")]
    if len(outer) != 138 or outer["outer_heldout_group"].nunique() != 23:
        errors.append("outer-test applicability rows changed")
    borrowing_by_type = {
        aging_type: part.loc[part["borrow_allowed"], "outer_heldout_group"].nunique()
        for aging_type, part in outer.groupby("type")
    }
    if borrowing_by_type != {"k": 6, "z": 9}:
        errors.append(f"frozen applicability coverage changed: {borrowing_by_type}")
    return {
        "status": "verified-stage2-ready-but-still-sealed" if not errors else "invalid",
        "stage1_source_models_frozen": 4,
        "stage2_outcome_free_feature_rows": len(features),
        "stage2_outer_splits": len(splits),
        "hypothesis_cards": len(cards.get("cards", [])),
        "applicability_rows": len(applicability),
        "outer_test_borrowing_groups": int(outer.loc[outer["borrow_allowed"], "outer_heldout_group"].nunique()),
        "stage2_numeric_outcomes_opened": False,
        "errors": errors,
    }


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"].startswith("verified-") else 1)


if __name__ == "__main__":
    main()
