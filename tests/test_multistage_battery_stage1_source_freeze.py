from analysis.verify_multistage_battery_stage1_source_freeze import verify


def test_stage1_source_freeze_keeps_stage2_outcomes_sealed() -> None:
    result = verify()
    assert result["status"] == "verified-stage2-ready-but-still-sealed", result["errors"]
    assert result["stage2_outcome_free_feature_rows"] == 138
    assert result["stage2_outer_splits"] == 23
    assert result["hypothesis_cards"] == 2
    assert result["applicability_rows"] == 3594
    assert result["outer_test_borrowing_groups"] == 15
    assert result["stage2_numeric_outcomes_opened"] is False
