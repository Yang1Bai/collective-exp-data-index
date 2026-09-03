from analysis.prepare_multistage_battery_stage1_allowlist import build_rows


def test_stage1_allowlist_excludes_every_stage2_archive() -> None:
    rows = build_rows()
    assert len(rows) == 141
    assert {row["stage"] for row in rows} == {"1"}
    assert len({row["file_id"] for row in rows}) == 141
