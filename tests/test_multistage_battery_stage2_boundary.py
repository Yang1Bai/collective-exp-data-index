import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_frozen_stage2_primary_remains_non_evaluable() -> None:
    release = load("analysis/results/multistage_battery_stage2/STAGE2_RELEASE_AUDIT.json")
    assert release["status"] == "non-evaluable-stage2-release"
    assert release["coverage_gate_pass"] is False
    assert release["evaluable_stage2_cells"] == 135
    assert release["missing_endpoint_stage2_cells"] == 3
    assert release["stage2_condition_groups"] == 23
    assert release["minimum_cells_per_condition_group"] == 0


def test_z10_absence_is_structurally_verified_without_substitution() -> None:
    audit = load("analysis/results/multistage_battery_stage2/Z10_MEMBER_AUDIT.json")
    assert audit["status"] == "verified-structural-endpoint-absence"
    assert audit["all_have_exactly_one_et_t23"] is True
    assert audit["all_lack_at_t23"] is True
    assert audit["numeric_csv_rows_opened"] is False
    assert audit["substitution_attempted"] is False
    assert len(audit["archives"]) == 3


def test_coverage_sensitivity_cannot_upgrade_the_primary() -> None:
    summary = load(
        "analysis/results/multistage_battery_stage2_coverage_sensitivity/analysis/"
        "POSTRELEASE_SENSITIVITY_SUMMARY.json"
    )
    verification = load(
        "analysis/results/multistage_battery_stage2_coverage_sensitivity/INDEPENDENT_VERIFICATION.json"
    )
    assert summary["frozen_primary_status"] == "non-evaluable-stage2-release"
    assert summary["confirmatory_success"] is False
    assert summary["stage2_cells_analyzed"] == 135
    assert summary["stage2_condition_groups"] == 22
    assert summary["training_gate_passed_outer_groups"] == 4
    assert summary["exploratory_pattern_pass"] is False
    assert verification["status"] == "independently-verified-postrelease-coverage-sensitivity"


def test_adjacency_result_is_strong_but_explicitly_post_hoc() -> None:
    summary = load(
        "analysis/results/multistage_battery_stage2_coverage_sensitivity/"
        "postrelease_adjacency_diagnostic/POSTRELEASE_ADJACENCY_DIAGNOSTIC_SUMMARY.json"
    )
    verification = load(
        "analysis/results/multistage_battery_stage2_coverage_sensitivity/"
        "postrelease_adjacency_diagnostic/INDEPENDENT_VERIFICATION.json"
    )
    result = summary["inference"]["adjacency_only minus target_only"]
    assert summary["method_selection_was_outcome_guided"] is True
    assert summary["confirmatory_success"] is False
    assert result["effect"] > 0.06
    assert result["ci95"][0] > 0
    assert result["holm_adjusted_p"] < 0.05
    assert summary["condition_group_wins"]["k"]["groups_improved"] == 7
    assert summary["condition_group_wins"]["z"]["groups_improved"] == 10
    assert verification["status"] == "independently-verified-postrelease-adjacency-diagnostic"
