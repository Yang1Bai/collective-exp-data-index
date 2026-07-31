from analysis.verify_multistage_battery_cca_v2_preoutcome import validate_preoutcome


def test_multistage_battery_freeze_is_outcome_free_and_hash_valid() -> None:
    result = validate_preoutcome()
    assert result["status"] == "verified-preoutcome-endpoint-schema", result["errors"]
    assert result["target_cells"] == 138
    assert result["stage2_condition_groups"] == 23
    assert result["exact_stage1_stage2_condition_overlap"] == 0
    assert result["raw_target_outcomes_opened"] is False
    assert result["numeric_csv_data_rows_opened"] is False
    assert result["csv_header_lines_read"] == 32


def test_multistage_battery_retrieval_ambiguity_remains_a_hard_gate() -> None:
    result = validate_preoutcome()
    assert result["retrieval_gate"] == "verified-complete-metadata-only-map"
