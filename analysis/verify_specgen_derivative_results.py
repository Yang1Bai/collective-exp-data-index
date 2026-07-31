"""Portable integrity checks for the SpecGen derivative result package."""
from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor

from run_specgen_derivative_oer_borrowing import (
    ARCHIVE,
    DESIGN_PATH,
    RANDOM_SEED,
    RESULTS,
    evaluate,
    holm_adjust,
    read_member,
    sha256,
)


def close(actual: float, expected: float, label: str, tolerance: float = 1e-10) -> None:
    if not np.isclose(actual, expected, atol=tolerance, rtol=tolerance):
        raise AssertionError(f"{label}: {actual} != {expected}")


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    summary_path = RESULTS / "specgen_composition_secondary_summary.json"
    temporal_path = RESULTS / "specgen_top20_temporal_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    temporal = json.loads(temporal_path.read_text(encoding="utf-8"))
    if summary["design_sha256"] != sha256(DESIGN_PATH):
        raise AssertionError("Design hash mismatch")
    if summary["status"] != "complete-post-primary-secondary":
        raise AssertionError("Composition summary is incomplete")
    if temporal["status"] != "complete-retrospective-temporal-check":
        raise AssertionError("Temporal check is incomplete")

    with ZipFile(ARCHIVE) as archive:
        source = read_member(archive.read("SpecGen/data/data.xlsx"))
        targets = {
            key: read_member(archive.read(f"SpecGen/data/transfer_{key}.xlsx"))
            for key in "ABCD"
        }
    source_x = source["metals"].to_numpy(dtype=float)
    source_y = (
        source["overpotential"].iloc[:, 0].to_numpy(dtype=float) - 1.23
    ) * 1000.0
    donor = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    ).fit(source_x, source_y)

    null = pd.read_csv(RESULTS / "specgen_composition_secondary_shuffle.csv")
    expected_seeds = [
        RANDOM_SEED + 30000 + offset
        for offset in range(int(design["source_shuffle_seeds"]))
    ]
    if null["seed"].astype(int).tolist() != expected_seeds:
        raise AssertionError("Composition null seeds changed")
    raw_p = {}
    for key in "ABCD":
        x = targets[key]["metals"].to_numpy(dtype=float)
        y = (
            targets[key]["overpotential"].iloc[:, 0].to_numpy(dtype=float)
            - 1.23
        ) * 1000.0
        metrics = evaluate(y, donor.predict(x), design["selection_fraction"])
        for metric, value in metrics.items():
            close(value, summary["zero_label"][key][metric], f"{key} {metric}")
        raw_p[key] = float(
            (1 + np.sum(null[key].to_numpy() >= metrics["spearman"]))
            / (len(null) + 1)
        )
    adjusted = holm_adjust(raw_p)
    for key in "ABCD":
        close(
            adjusted[key],
            summary["zero_label"][key]["shuffled_holm_p"],
            f"{key} Holm p",
        )

    anchor = pd.read_csv(
        RESULTS / "specgen_composition_secondary_anchor_metrics.csv"
    )
    if len(anchor) != 800:
        raise AssertionError("Expected 800 five-label draw rows")
    for key in "ABCD":
        subset = anchor.loc[anchor["target"] == key]
        for column, expected in summary["five_label"][key][
            "draw_medians"
        ].items():
            close(
                float(subset[column].median()),
                expected,
                f"{key} median {column}",
            )

    top20 = pd.read_csv(RESULTS / "specgen_top20_extracted_predictions.csv")
    if len(top20) != 80 or top20.groupby("target").size().to_dict() != {
        key: 20 for key in "ABCD"
    }:
        raise AssertionError("Temporal candidate table is incomplete")

    decisions = summary["decisions"]
    expected_decisions = {
        "A": "ranking-only",
        "B": "positive-predictive-and-ranking",
        "C": "abstain-or-negative",
        "D": "positive-predictive-and-ranking",
    }
    for key, expected in expected_decisions.items():
        if decisions[key]["classification"] != expected:
            raise AssertionError(f"Decision mismatch for {key}")

    verified = {
        "status": "verified-complete",
        "design_sha256": sha256(DESIGN_PATH),
        "archive_sha256": sha256(ARCHIVE),
        "composition_summary_sha256": sha256(summary_path),
        "temporal_summary_sha256": sha256(temporal_path),
        "composition_null_rows": int(len(null)),
        "five_label_draw_rows": int(len(anchor)),
        "temporal_candidate_rows": int(len(top20)),
        "decisions": expected_decisions,
        "claim_guard": (
            "Verified retrospective within-programme perturbation result; "
            "external confirmation remains required."
        ),
    }
    output = RESULTS / "specgen_derivative_verification.json"
    output.write_text(
        json.dumps(verified, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(verified, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
