"""Check the composition donor on subsequently synthesized SpecGen candidates."""
from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from pypdf import PdfReader
from scipy.stats import rankdata
from sklearn.ensemble import ExtraTreesRegressor

from run_specgen_derivative_oer_borrowing import (
    ARCHIVE,
    RANDOM_SEED,
    RESULTS,
    evaluate,
    holm_adjust,
    read_member,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "Dataset" / "ref6" / "44160_2025_983_MOESM1_ESM.pdf"
SOURCE_DATA = (
    ROOT / "Dataset" / "ref6" / "44160_2025_983_MOESM3_ESM.zip"
)
PROTOCOL = (
    ROOT / "analysis" / "SPECGEN_TOP20_TEMPORAL_CHECK.md"
)
PAGE_MAP = {"B": 41, "D": 42, "A": 43, "C": 44}
FIGURE_FILES = {
    "B": "SourceData for Supplementary Information/Fig S14a.txt",
    "D": "SourceData for Supplementary Information/Fig S15a.txt",
    "A": "SourceData for Supplementary Information/Fig S18a.txt",
    "C": "SourceData for Supplementary Information/Fig S19a.txt",
}
ROW_PATTERN = re.compile(
    r"(?<![\d.])(\d{1,2})\s+"
    + r"\s+".join([r"(\d\.\d{4})"] * 6)
    + r"\s+(1\.\d{4})\s+(\d{3}\.\d)"
)


def extract_tables() -> dict[str, pd.DataFrame]:
    reader = PdfReader(PDF)
    tables = {}
    columns = [
        "candidate",
        "slot_1",
        "slot_2",
        "slot_3",
        "slot_4",
        "slot_5",
        "slot_6",
        "potential_V",
        "overpotential_mV",
    ]
    for key, page_index in PAGE_MAP.items():
        text = (reader.pages[page_index].extract_text() or "").replace(
            "\n", " "
        )
        rows = ROW_PATTERN.findall(text)
        if len(rows) != 20:
            raise AssertionError(f"Expected 20 rows for {key}, found {len(rows)}")
        table = pd.DataFrame(rows, columns=columns).astype(float)
        table["candidate"] = table["candidate"].astype(int)
        table.insert(0, "target", key)
        tables[key] = table
    return tables


def verify_source_data(tables: dict[str, pd.DataFrame]) -> None:
    with ZipFile(SOURCE_DATA) as archive:
        for key, member in FIGURE_FILES.items():
            lines = archive.read(member).decode("utf-8").strip().splitlines()
            values = np.array(
                [float(line.split()[1]) for line in lines], dtype=float
            )
            if len(values) != 20:
                raise AssertionError(f"Figure source row count changed for {key}")
            pdf_values = tables[key]["overpotential_mV"].to_numpy(dtype=float)
            # Figure S15a plots two Group-D entries in the reverse order used
            # by Supplementary Table 7. Verify the released value multiset;
            # retain the PDF table as the composition-to-outcome mapping.
            if not np.allclose(
                np.sort(values), np.sort(pdf_values), atol=0.051, rtol=0
            ):
                raise AssertionError(f"PDF/source-data mismatch for {key}")


def permutation_p(
    y: np.ndarray, prediction: np.ndarray, draws: int, seed: int
) -> tuple[float, float]:
    y_rank = rankdata(y).astype(float)
    prediction_rank = rankdata(prediction).astype(float)
    y_rank -= np.mean(y_rank)
    prediction_rank -= np.mean(prediction_rank)
    denominator = float(
        np.sqrt(np.sum(y_rank**2) * np.sum(prediction_rank**2))
    )
    observed = float(np.dot(y_rank, prediction_rank) / denominator)
    rng = np.random.default_rng(seed)
    exceed = 0
    batch_size = 10000
    for start in range(0, draws, batch_size):
        count = min(batch_size, draws - start)
        order = np.argsort(rng.random((count, len(y))), axis=1)
        permuted = y_rank[order]
        null = np.sum(permuted * prediction_rank[None, :], axis=1) / denominator
        exceed += int(np.sum(null >= observed))
    return observed, float((1 + exceed) / (draws + 1))


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    tables = extract_tables()
    verify_source_data(tables)

    with ZipFile(ARCHIVE) as archive:
        source = read_member(archive.read("SpecGen/data/data.xlsx"))
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

    rows = []
    p_values = {}
    for offset, key in enumerate("ABCD"):
        table = tables[key]
        x = table[[f"slot_{i}" for i in range(1, 7)]].to_numpy(dtype=float)
        y = table["overpotential_mV"].to_numpy(dtype=float)
        prediction = donor.predict(x)
        metrics = evaluate(y, prediction, fraction=0.2)
        observed, p_value = permutation_p(
            y,
            prediction,
            draws=100000,
            seed=RANDOM_SEED + 50000 + offset,
        )
        if not np.isclose(observed, metrics["spearman"], atol=1e-12):
            raise AssertionError("Independent Spearman calculation mismatch")
        p_values[key] = p_value
        rows.append(
            {
                "target": key,
                **metrics,
                "permutation_one_sided_p": p_value,
            }
        )
        table["donor_prediction_mV"] = prediction

    adjusted = holm_adjust(p_values)
    for row in rows:
        row["permutation_holm_p"] = adjusted[row["target"]]
        row["temporal_rank_corroboration"] = bool(
            row["spearman"] > 0.3 and row["permutation_holm_p"] < 0.05
        )

    extracted = pd.concat(
        [tables[key] for key in "ABCD"], ignore_index=True
    )
    extracted.to_csv(
        RESULTS / "specgen_top20_extracted_predictions.csv", index=False
    )
    metrics_table = pd.DataFrame(rows)
    metrics_table.to_csv(
        RESULTS / "specgen_top20_temporal_metrics.csv", index=False
    )
    summary = {
        "status": "complete-retrospective-temporal-check",
        "protocol_sha256": sha256(PROTOCOL),
        "pdf_sha256": sha256(PDF),
        "source_data_sha256": sha256(SOURCE_DATA),
        "metrics": {
            row["target"]: row for row in rows
        },
        "claim_guard": (
            "Subsequent-candidate ranking corroboration within the same "
            "published programme; candidates were selected by SpecGen, so this "
            "does not establish unbiased or prospective search acceleration."
        ),
    }
    output = RESULTS / "specgen_top20_temporal_summary.json"
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
