"""Verify the AI-v4 Figure 1 and the unchanged canonical Figures 2-4."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

import verify_main_figures_nature_v3 as legacy


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE = FIGURES / "source_data"
ASSET = FIGURES / "assets" / "knowledge_borrowing_hero_ai_v4.png"
PROVENANCE = FIGURES / "assets" / "knowledge_borrowing_hero_ai_v4_provenance.md"
REPORT = RESULTS / "main_figures_ai_v4_verification.json"


def close(actual: float, expected: float, tolerance: float = 5e-6) -> None:
    if not np.isclose(actual, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"numeric mismatch: {actual} != {expected}")


def source_value(frame: pd.DataFrame, route: str, metric: str) -> float:
    row = frame[(frame.route == route) & (frame.metric == metric)]
    if len(row) != 1:
        raise AssertionError(f"expected one Figure 1 row for {route}:{metric}")
    return float(row.iloc[0].value)


def main() -> None:
    # Figures 2-4 and their evidence tables are unchanged from the verified v3
    # set. Re-run that verifier instead of silently inheriting its conclusion.
    legacy.main()

    expected_files: list[str] = []
    for stem in [
        "knowledge_borrowing_overview_ai_v4",
        "figure2_failure_benchmark_nmi_v2",
        "figure3_relation_transfer_nmi_v2",
        "figure4_ordinal_screening_nmi_v2",
    ]:
        for suffix in ["pdf", "svg", "png", "tiff"]:
            path = FIGURES / f"{stem}.{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                raise AssertionError(f"missing or empty figure export: {path}")
            expected_files.append(str(path.relative_to(ROOT)))

    if not ASSET.exists() or not PROVENANCE.exists():
        raise AssertionError("Figure 1 conceptual asset or provenance is missing")
    with Image.open(ASSET) as image:
        if image.size != (1774, 887) or image.mode != "RGB":
            raise AssertionError(f"unexpected conceptual asset: {image.size}, {image.mode}")

    fig1 = pd.read_csv(SOURCE / "knowledge_borrowing_overview_ai_v4.csv")
    expected = {
        ("predict", "relative_log_rmse_gain"): 28.64,
        ("predict", "raw_r2"): .629,
        ("predict", "spearman"): .871,
        ("screen", "recipient_spearman"): .537,
        ("screen", "borrowed_spearman"): .910,
        ("screen", "recipient_precision_top_quartile"): .490,
        ("screen", "borrowed_precision_top_quartile"): .933,
        ("abstain", "generic_edges_passed"): 0,
        ("abstain", "frozen_donor_score"): .694,
        ("abstain", "frozen_recipient_score"): .783,
    }
    for key, value in expected.items():
        close(source_value(fig1, *key), value, .0005)

    report = {
        "status": "verified-complete",
        "canonical_exports": expected_files,
        "figure1_asset_role": "conceptual-not-quantitative",
        "figure1_asset_pixels": [1774, 887],
        "figure1_vector_labels": True,
        "figure1_routes": ["predict", "screen", "abstain"],
        "figure1_source_rows": int(len(fig1)),
        "figures_2_to_4_reverified": True,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
