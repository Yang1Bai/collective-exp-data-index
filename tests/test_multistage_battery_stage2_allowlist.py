from analysis.prepare_multistage_battery_stage2_allowlist import build_rows


def test_stage2_allowlist_is_exact_and_unique() -> None:
    rows = build_rows()
    assert len(rows) == 138
    assert {row["stage"] for row in rows} == {"2"}
    assert len({row["file_id"] for row in rows}) == 138
