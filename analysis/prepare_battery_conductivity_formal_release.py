"""Create the frozen numeric release for the battery borrowing benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from audit_battery_conductivity_preoutcome import (
    CONDITION_VALUE_PATTERNS,
    DESIGN_PATH,
    FIRST_NUMBER_PATTERN,
    GRAVIMETRIC_CAPACITY_PATTERN,
    MASS_CURRENT_PATTERN,
    RATE_C_PATTERN,
    file_hash,
    normalized_identifier,
    normalized_material,
    normalized_text,
    property_class,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
IMPLEMENTATION_PATH = HERE / "battery_conductivity_implementation.json"
VALUE_AMENDMENT_PATH = (
    HERE / "BATTERY_CONDUCTIVITY_VALUE_SEMANTICS_AMENDMENT.md"
)
AUDIT_PATH = (
    HERE / "results" / "battery_conductivity_preoutcome_audit.json"
)
ARCHIVE = (
    ROOT
    / "data"
    / "external"
    / "battery_conductivity_borrowing"
    / "battery-v2.zip"
)
RELEASE = (
    HERE / "results" / "battery_conductivity_formal_release.csv"
)
MANIFEST = (
    HERE / "results" / "battery_conductivity_formal_release_manifest.json"
)

READ_COLUMNS = [
    "Property",
    "Name",
    "Value",
    "Raw_unit",
    "Raw_value",
    "Unit",
    "Extracted_name",
    "DOI",
    "Specifier",
    "Tag",
    "Warning",
    "Type",
    "Info",
    "Date",
]
NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


def numeric_median(value: object) -> float:
    if value is None:
        return float("nan")
    numbers = [
        float(token)
        for token in NUMBER_PATTERN.findall(str(value).replace(",", ""))
    ]
    finite = [number for number in numbers if np.isfinite(number)]
    return float(np.median(finite)) if finite else float("nan")


def extracted_condition(series: pd.Series, key: str) -> pd.Series:
    return series.str.extract(
        CONDITION_VALUE_PATTERNS[key], expand=False
    ).fillna("")


def first_number(series: pd.Series) -> pd.Series:
    extracted = series.str.extract(FIRST_NUMBER_PATTERN, expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def compact_unit(series: pd.Series) -> pd.Series:
    return (
        normalized_text(series)
        .str.replace("−", "-", regex=False)
        .str.replace("–", "-", regex=False)
        .str.replace("—", "-", regex=False)
        .str.replace(r"\s+", "", regex=True)
        .str.lower()
    )


def capacity_factor(unit: pd.Series) -> pd.Series:
    compact = compact_unit(unit)
    factor = pd.Series(np.nan, index=unit.index, dtype=float)
    factor[compact.str.contains("mah") & compact.str.contains("g")] = 1.0
    factor[
        compact.str.contains("ah")
        & compact.str.contains("kg")
        & ~compact.str.contains("mah")
    ] = 1.0
    factor[
        compact.str.contains("ah")
        & compact.str.contains("g")
        & ~compact.str.contains("mah")
        & ~compact.str.contains("kg")
    ] = 1000.0
    return factor


def conductivity_factor(unit: pd.Series) -> pd.Series:
    compact = compact_unit(unit)
    factor = pd.Series(np.nan, index=unit.index, dtype=float)
    factor[compact.str.startswith("s") & compact.str.contains("cm")] = 1.0
    factor[compact.str.startswith("ms") & compact.str.contains("cm")] = 1e-3
    factor[compact.str.startswith("ms") & compact.str.contains("/m")] = 1e-5
    factor[compact.str.startswith("ms") & compact.str.contains("m-1")] = 1e-5
    return factor


def voltage_factor(unit: pd.Series) -> pd.Series:
    compact = compact_unit(unit)
    factor = pd.Series(np.nan, index=unit.index, dtype=float)
    factor[compact.str.startswith("v")] = 1.0
    factor[compact.str.startswith("mv")] = 1e-3
    return factor


def energy_factor(unit: pd.Series) -> pd.Series:
    compact = compact_unit(unit)
    factor = pd.Series(np.nan, index=unit.index, dtype=float)
    factor[compact.str.contains("wh") & compact.str.contains("kg")] = 1.0
    factor[
        compact.str.contains("wh")
        & compact.str.contains("g")
        & ~compact.str.contains("kg")
    ] = 1000.0
    return factor


def current_factor(unit: pd.Series) -> pd.Series:
    compact = compact_unit(unit)
    factor = pd.Series(np.nan, index=unit.index, dtype=float)
    factor[compact.str.startswith("ma") & compact.str.contains("g")] = 1e-3
    factor[
        compact.str.startswith("a")
        & compact.str.contains("g")
        & ~compact.str.contains("kg")
    ] = 1.0
    factor[compact.str.startswith("a") & compact.str.contains("kg")] = 1e-3
    return factor


def stable_record_id(row: pd.Series) -> str:
    payload = "\x1f".join(str(row[column]) for column in row.index)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def quantiles(series: pd.Series) -> dict[str, float]:
    finite = pd.to_numeric(series, errors="coerce").dropna()
    if finite.empty:
        return {}
    values = finite.quantile([0.01, 0.1, 0.5, 0.9, 0.99])
    return {str(index): float(value) for index, value in values.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--release", type=Path, default=RELEASE)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    implementation = json.loads(
        IMPLEMENTATION_PATH.read_text(encoding="utf-8")
    )
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit["status"] != "eligible-preoutcome":
        raise RuntimeError("Pre-outcome audit did not release this benchmark")
    if audit["design_sha256"] != file_hash(DESIGN_PATH):
        raise RuntimeError("Design changed after the pre-outcome audit")
    if args.archive.stat().st_size != design["dataset"]["expected_bytes"]:
        raise RuntimeError("Archive byte size changed")
    if file_hash(args.archive, "md5") != design["dataset"]["expected_md5"]:
        raise RuntimeError("Archive MD5 changed")

    with zipfile.ZipFile(args.archive) as archive:
        with archive.open(implementation["formal_member"]) as handle:
            frame = pd.read_csv(
                handle,
                usecols=READ_COLUMNS,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
            )

    for column in READ_COLUMNS:
        frame[column] = normalized_text(frame[column])
    frame["property_class"] = property_class(frame["Property"])
    frame = frame.loc[
        frame["property_class"].isin(implementation["release"]["properties"])
    ].copy()
    frame["material_normalized"] = normalized_material(frame)
    frame["doi_normalized"] = normalized_identifier(frame["DOI"])
    frame["condition_text"] = (
        frame["Specifier"]
        + " | "
        + frame["Tag"]
        + " | "
        + frame["Type"]
        + " | "
        + frame["Info"]
    ).str.strip(" |")
    frame["raw_numeric"] = frame["Value"].map(numeric_median)

    frame["cycle_value_text"] = extracted_condition(
        frame["condition_text"], "cycle_value"
    )
    frame["cycle_number"] = first_number(frame["cycle_value_text"])
    frame["current_value_text"] = extracted_condition(
        frame["condition_text"], "current_value"
    )
    frame["current_value_number"] = first_number(
        frame["current_value_text"]
    )
    frame["current_units_text"] = extracted_condition(
        frame["condition_text"], "current_units"
    )
    frame["current_a_per_g"] = (
        frame["current_value_number"]
        * current_factor(frame["current_units_text"])
    )
    frame["is_early_cycle"] = (
        frame["cycle_number"].notna()
        & frame["cycle_number"].ge(0)
        & frame["cycle_number"].le(10)
    )
    frame["is_gravimetric_capacity"] = (
        frame["Raw_unit"] + " | " + frame["Unit"]
    ).str.contains(GRAVIMETRIC_CAPACITY_PATTERN, na=False)
    frame["has_rate"] = frame["condition_text"].str.contains(
        RATE_C_PATTERN, na=False
    ) | frame["condition_text"].str.contains(MASS_CURRENT_PATTERN, na=False)

    frame["normalized_value"] = np.nan
    frame["normalized_unit"] = ""
    factors = {
        "capacity": capacity_factor(frame["Raw_unit"]),
        "conductivity": conductivity_factor(frame["Raw_unit"]),
        "voltage": voltage_factor(frame["Raw_unit"]),
        "energy": energy_factor(frame["Raw_unit"]),
    }
    units = {
        "capacity": "mAh_g",
        "conductivity": "S_cm",
        "voltage": "V",
        "energy": "Wh_kg",
    }
    for property_name, factor in factors.items():
        mask = frame["property_class"].eq(property_name) & factor.notna()
        frame.loc[mask, "normalized_value"] = frame.loc[
            mask, "raw_numeric"
        ]
        frame.loc[mask, "normalized_unit"] = units[property_name]

    bounds = implementation["release"]["bounds"]
    property_bounds = {
        "capacity": bounds["capacity_mAh_g"],
        "conductivity": bounds["conductivity_S_cm"],
        "voltage": bounds["voltage_V"],
        "energy": bounds["energy_Wh_kg"],
    }
    valid = (
        frame["material_normalized"].ne("")
        & frame["material_normalized"].ne("none")
        & frame["doi_normalized"].ne("")
        & frame["normalized_value"].notna()
    )
    for property_name, (lower, upper) in property_bounds.items():
        property_rows = frame["property_class"].eq(property_name)
        valid &= ~property_rows | frame["normalized_value"].between(
            lower, upper, inclusive="both"
        )
    capacity_rows = frame["property_class"].eq("capacity")
    current_lower, current_upper = bounds["current_A_g"]
    valid &= (
        ~capacity_rows
        | (
            frame["is_gravimetric_capacity"]
            & frame["has_rate"]
            & frame["current_a_per_g"].between(
                current_lower, current_upper, inclusive="both"
            )
        )
    )
    frame = frame.loc[valid].copy()

    release_columns = [
        "property_class",
        "material_normalized",
        "doi_normalized",
        "normalized_value",
        "normalized_unit",
        "current_a_per_g",
        "cycle_number",
        "is_early_cycle",
        "Type",
        "Specifier",
        "Tag",
        "Info",
        "Warning",
        "Date",
    ]
    before_deduplication = len(frame)
    frame = frame.drop_duplicates(release_columns).reset_index(drop=True)
    frame.insert(
        0,
        "record_id",
        frame[release_columns].apply(stable_record_id, axis=1),
    )

    args.release.parent.mkdir(parents=True, exist_ok=True)
    frame[["record_id", *release_columns]].to_csv(
        args.release, index=False
    )
    property_summary: dict[str, Any] = {}
    for property_name, group in frame.groupby("property_class"):
        property_summary[property_name] = {
            "records": int(len(group)),
            "materials": int(group["material_normalized"].nunique()),
            "publications": int(group["doi_normalized"].nunique()),
            "value_quantiles": quantiles(group["normalized_value"]),
        }
    manifest = {
        "status": "formal-release-created",
        "design_sha256": file_hash(DESIGN_PATH),
        "implementation_sha256": file_hash(IMPLEMENTATION_PATH),
        "value_semantics_amendment_sha256": file_hash(
            VALUE_AMENDMENT_PATH
        ),
        "preoutcome_audit_sha256": file_hash(AUDIT_PATH),
        "archive_sha256": file_hash(args.archive),
        "release_sha256": file_hash(args.release),
        "input_rows_after_property_selection": int(before_deduplication),
        "release_rows": int(len(frame)),
        "exact_duplicates_removed": int(before_deduplication - len(frame)),
        "property_summary": property_summary,
        "numeric_property_values_read": True,
        "claim_guard": implementation["claim_guard"],
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
