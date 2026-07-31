"""Outcome-blind eligibility audit for conductivity-to-capacity borrowing."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN_PATH = HERE / "battery_conductivity_borrowing_design.json"
AMENDMENT_PATH = HERE / "BATTERY_CONDUCTIVITY_SCHEMA_AMENDMENT.md"
DEFAULT_ARCHIVE = (
    ROOT
    / "data"
    / "external"
    / "battery_conductivity_borrowing"
    / "battery-v2.zip"
)
DEFAULT_OUTPUT = (
    HERE / "results" / "battery_conductivity_preoutcome_audit.json"
)
DEFAULT_METADATA = (
    HERE / "results" / "battery_conductivity_metadata_no_outcomes.csv"
)
MEMBER = "battery-2022.csv"

SAFE_COLUMNS = [
    "Property",
    "Name",
    "Raw_unit",
    "Unit",
    "Extracted_name",
    "DOI",
    "Specifier",
    "Tag",
    "Warning",
    "Type",
    "Info",
    "Date",
    "Correctness",
]
FORBIDDEN_COLUMNS = {"Value", "Raw_value", "value", "Title", "Journal"}

RATE_C_PATTERN = re.compile(
    r"(?<![A-Za-z°])(?:\d+(?:\.\d+)?|\.\d+)\s*C(?:\b|[-−–—])",
    re.IGNORECASE,
)
MASS_CURRENT_PATTERN = re.compile(
    r"(?:mA|A)\s*(?:h\s*)?(?:g|kg)\s*(?:[-−–—]?\s*1|/\s*(?:g|kg))",
    re.IGNORECASE,
)
CYCLE_PATTERN = re.compile(
    r"\b(?:first|initial|\d+(?:st|nd|rd|th)?)?\s*cycles?\b",
    re.IGNORECASE,
)
TEMPERATURE_PATTERN = re.compile(
    r"(?:[-+]?\d+(?:\.\d+)?)\s*(?:°\s*C|deg(?:ree)?s?\s*C|K)\b",
    re.IGNORECASE,
)
GRAVIMETRIC_CAPACITY_PATTERN = re.compile(
    r"(?:mA\s*h|mAh)\s*(?:g\s*[-−–—]?\s*1|/\s*g)\b",
    re.IGNORECASE,
)
CONDITION_VALUE_PATTERNS = {
    "cycle_value": re.compile(
        r"['\"]cycle_value['\"]\s*:\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    ),
    "current_value": re.compile(
        r"['\"]current_value['\"]\s*:\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    ),
    "current_units": re.compile(
        r"['\"]current_units['\"]\s*:\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    ),
}
FIRST_NUMBER_PATTERN = re.compile(r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))")


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def normalized_identifier(series: pd.Series) -> pd.Series:
    return normalized_text(series).str.lower().str.replace(
        r"^https?://(?:dx\.)?doi\.org/", "", regex=True
    )


def normalized_material(frame: pd.DataFrame) -> pd.Series:
    extracted = normalized_text(frame["Extracted_name"])
    name = normalized_text(frame["Name"])
    selected = extracted.where(extracted.ne(""), name)
    return (
        selected.str.lower()
        .str.replace(r"\s+", "", regex=True)
        .str.replace("−", "-", regex=False)
        .str.replace("–", "-", regex=False)
    )


def property_class(series: pd.Series) -> pd.Series:
    text = normalized_text(series).str.lower()
    output = pd.Series("other", index=series.index, dtype="object")
    output[text.str.contains("conduct", regex=False)] = "conductivity"
    output[text.str.contains("capacity", regex=False)] = "capacity"
    output[text.str.contains("coulomb", regex=False)] = (
        "coulombic_efficiency"
    )
    output[text.str.contains("voltage", regex=False)] = "voltage"
    output[text.str.contains("energy", regex=False)] = "energy"
    return output


def extracted_condition(series: pd.Series, key: str) -> pd.Series:
    return series.str.extract(
        CONDITION_VALUE_PATTERNS[key], expand=False
    ).fillna("")


def first_number(series: pd.Series) -> pd.Series:
    extracted = series.str.extract(FIRST_NUMBER_PATTERN, expand=False)
    return pd.to_numeric(extracted, errors="coerce")


def count_summary(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "records": int(len(frame)),
        "materials": int(frame["material_normalized"].nunique()),
        "publications": int(
            frame.loc[frame["doi_normalized"].ne(""), "doi_normalized"].nunique()
        ),
        "doi_coverage_fraction": float(frame["doi_normalized"].ne("").mean()),
        "rate_coverage_fraction": float(frame["has_rate"].mean()),
        "cycle_coverage_fraction": float(frame["has_cycle"].mean()),
        "temperature_coverage_fraction": float(
            frame["has_temperature"].mean()
        ),
    }


def top_counts(series: pd.Series, limit: int = 20) -> dict[str, int]:
    counts = normalized_text(series).replace("", "<missing>").value_counts()
    return {str(key): int(value) for key, value in counts.head(limit).items()}


def condition_examples(
    frame: pd.DataFrame, mask: pd.Series, limit: int = 12
) -> list[str]:
    examples = (
        frame.loc[mask, "condition_text"]
        .drop_duplicates()
        .sort_values(key=lambda values: values.str.len())
    )
    return [str(value)[:500] for value in examples.head(limit)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    expected = design["dataset"]
    archive_path = args.archive.resolve()
    if archive_path.stat().st_size != expected["expected_bytes"]:
        raise RuntimeError("Battery archive byte size does not match freeze")
    if file_hash(archive_path, "md5") != expected["expected_md5"]:
        raise RuntimeError("Battery archive MD5 does not match freeze")

    with zipfile.ZipFile(archive_path) as archive:
        with archive.open(MEMBER) as handle:
            frame = pd.read_csv(
                handle,
                usecols=SAFE_COLUMNS,
                dtype=str,
                keep_default_na=False,
                low_memory=False,
            )

    overlap = FORBIDDEN_COLUMNS.intersection(frame.columns)
    if overlap:
        raise AssertionError(f"Forbidden outcome columns read: {overlap}")

    for column in SAFE_COLUMNS:
        frame[column] = normalized_text(frame[column])
    frame["property_class"] = property_class(frame["Property"])
    frame["material_normalized"] = normalized_material(frame)
    frame["doi_normalized"] = normalized_identifier(frame["DOI"])
    frame["unit_text"] = (
        frame["Raw_unit"] + " | " + frame["Unit"]
    ).str.strip(" |")
    frame["condition_text"] = (
        frame["Specifier"]
        + " | "
        + frame["Tag"]
        + " | "
        + frame["Type"]
        + " | "
        + frame["Info"]
    ).str.strip(" |")
    frame["has_c_rate"] = frame["condition_text"].str.contains(
        RATE_C_PATTERN, na=False
    )
    frame["has_mass_current"] = frame["condition_text"].str.contains(
        MASS_CURRENT_PATTERN, na=False
    )
    frame["has_rate"] = frame["has_c_rate"] | frame["has_mass_current"]
    frame["has_cycle"] = frame["condition_text"].str.contains(
        CYCLE_PATTERN, na=False
    )
    frame["has_temperature"] = frame["condition_text"].str.contains(
        TEMPERATURE_PATTERN, na=False
    )
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
    frame["is_early_cycle"] = (
        frame["cycle_number"].notna()
        & frame["cycle_number"].ge(0)
        & frame["cycle_number"].le(10)
    )
    frame["is_gravimetric_capacity"] = frame["unit_text"].str.contains(
        GRAVIMETRIC_CAPACITY_PATTERN, na=False
    )

    donor = frame.loc[frame["property_class"].eq("conductivity")].copy()
    capacity = frame.loc[frame["property_class"].eq("capacity")].copy()
    primary = capacity.loc[
        capacity["is_gravimetric_capacity"] & capacity["has_rate"]
    ].copy()
    strict_early_cycle = primary.loc[primary["is_early_cycle"]].copy()

    safe_duplicate_columns = [
        "Property",
        "Name",
        "Raw_unit",
        "Unit",
        "Extracted_name",
        "DOI",
        "Specifier",
        "Tag",
        "Warning",
        "Type",
        "Info",
        "Date",
        "Correctness",
    ]
    metadata_duplicate_fraction = float(
        frame.duplicated(safe_duplicate_columns, keep=False).mean()
    )

    gates = design["outcome_blind_audit"]
    gate_checks = {
        "donor_records": len(donor) >= gates["minimum_donor_records"],
        "donor_materials": (
            donor["material_normalized"].nunique()
            >= gates["minimum_donor_materials"]
        ),
        "donor_publications": (
            donor.loc[
                donor["doi_normalized"].ne(""), "doi_normalized"
            ].nunique()
            >= gates["minimum_donor_publications"]
        ),
        "primary_recipient_records": (
            len(primary) >= gates["minimum_primary_recipient_records"]
        ),
        "primary_recipient_materials": (
            primary["material_normalized"].nunique()
            >= gates["minimum_primary_recipient_materials"]
        ),
        "primary_recipient_publications": (
            primary.loc[
                primary["doi_normalized"].ne(""), "doi_normalized"
            ].nunique()
            >= gates["minimum_primary_recipient_publications"]
        ),
        "capacity_rate_coverage": (
            float(capacity["has_rate"].mean())
            >= gates["minimum_condition_coverage_fraction"]
        ),
        "capacity_cycle_coverage": (
            float(capacity["has_cycle"].mean())
            >= gates["minimum_condition_coverage_fraction"]
        ),
        "metadata_duplicate_fraction": (
            metadata_duplicate_fraction
            <= gates["maximum_exact_duplicate_fraction"]
        ),
    }

    per_property = {
        name: count_summary(group)
        for name, group in frame.groupby("property_class", sort=True)
    }
    report = {
        "status": (
            "eligible-preoutcome"
            if all(gate_checks.values())
            else "ineligible-preoutcome"
        ),
        "design_sha256": file_hash(DESIGN_PATH),
        "schema_amendment_sha256": file_hash(AMENDMENT_PATH),
        "archive_sha256": file_hash(archive_path),
        "member": MEMBER,
        "numeric_property_values_read": False,
        "read_columns": SAFE_COLUMNS,
        "forbidden_columns": sorted(FORBIDDEN_COLUMNS),
        "all_records": int(len(frame)),
        "per_property": per_property,
        "primary_recipient": count_summary(primary),
        "strict_early_cycle_sensitivity": count_summary(
            strict_early_cycle
        ),
        "capacity_unit_counts": top_counts(capacity["unit_text"]),
        "condition_examples": {
            "rate": condition_examples(capacity, capacity["has_rate"]),
            "cycle": condition_examples(capacity, capacity["has_cycle"]),
            "temperature": condition_examples(
                capacity, capacity["has_temperature"]
            ),
        },
        "metadata_duplicate_fraction": metadata_duplicate_fraction,
        "gate_checks": gate_checks,
        "errors": [
            key for key, passed in gate_checks.items() if not passed
        ],
    }

    metadata_columns = [
        "property_class",
        "material_normalized",
        "doi_normalized",
        "unit_text",
        "condition_text",
        "has_c_rate",
        "has_mass_current",
        "has_rate",
        "has_cycle",
        "has_temperature",
        "cycle_value_text",
        "cycle_number",
        "current_value_text",
        "current_value_number",
        "current_units_text",
        "is_early_cycle",
        "is_gravimetric_capacity",
        "Warning",
        "Correctness",
        "Date",
    ]
    args.metadata_output.parent.mkdir(parents=True, exist_ok=True)
    frame[metadata_columns].to_csv(args.metadata_output, index=False)
    report["metadata_output"] = str(args.metadata_output)
    report["metadata_sha256"] = file_hash(args.metadata_output)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
