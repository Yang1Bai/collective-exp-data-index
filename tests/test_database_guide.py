from __future__ import annotations

import csv

from scripts import common
from scripts.build_database_guide import LEDGER_PATH, OUTPUT_PATH, build_guide


def test_database_guide_is_current_and_complete() -> None:
    expected = build_guide()
    assert OUTPUT_PATH.read_text(encoding="utf-8") == expected

    entries = common.entries_of(common.load_catalog())
    with LEDGER_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        ledger = list(csv.DictReader(handle))

    assert f"| Broad discovery catalog | {len(entries)} |" in expected
    assert f"| Analysed-resource ledger | {len(ledger)} |" in expected
    for row in ledger:
        assert row["resource_name"] in expected
