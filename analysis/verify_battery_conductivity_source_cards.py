"""Verify source cards and their source-only skill decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "battery_conductivity_borrowing_design.json"
IMPLEMENTATION = HERE / "battery_conductivity_implementation.json"
RELEASE = HERE / "results" / "battery_conductivity_formal_release.csv"
CARDS = HERE / "results" / "battery_conductivity_source_cards.csv"
SUMMARY = HERE / "results" / "battery_conductivity_source_summary.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    cards = pd.read_csv(CARDS, low_memory=False)

    if summary["design_sha256"] != sha256(DESIGN):
        raise AssertionError("Design hash changed after source cards")
    if summary["implementation_sha256"] != sha256(IMPLEMENTATION):
        raise AssertionError("Implementation hash changed after source cards")
    if summary["release_sha256"] != sha256(RELEASE):
        raise AssertionError("Formal release changed after source cards")
    if summary["cards_sha256"] != sha256(CARDS):
        raise AssertionError("Source-card hash mismatch")
    if cards["target_id"].duplicated().any():
        raise AssertionError("Target-card IDs are not unique")
    if len(cards) != summary["target_records"]:
        raise AssertionError("Target-card row count mismatch")

    card_prefixes = [
        "conductivity",
        "shuffled_conductivity",
        "voltage",
        "energy",
    ]
    for prefix in card_prefixes:
        required = {
            f"{prefix}_prediction",
            f"{prefix}_dispersion",
            f"{prefix}_support",
            f"{prefix}_missing",
        }
        if not required.issubset(cards.columns):
            raise AssertionError(f"Missing card columns: {prefix}")
        numeric = cards[list(required)].apply(
            pd.to_numeric, errors="coerce"
        )
        if not np.isfinite(numeric.to_numpy()).all():
            raise AssertionError(f"Nonfinite source card: {prefix}")

    real = next(
        item
        for item in summary["source_summaries"]
        if item["property"] == "conductivity"
    )
    gate = config["source_cards"]["conductivity_skill_gate"]
    expected = (
        real["oof_r2_transformed"] > gate["minimum_source_oof_r2"]
        and real["oof_spearman_transformed"]
        > gate["minimum_source_oof_spearman"]
    )
    if expected != summary["conductivity_skill_gate"]["passed"]:
        raise AssertionError("Conductivity source-skill decision mismatch")

    output = {
        "status": "verified-source-cards",
        "source_gate": summary["status"],
        "target_records": len(cards),
        "cards_sha256": summary["cards_sha256"],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

