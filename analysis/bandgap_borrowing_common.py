"""Shared normalization for experimental band-gap borrowing experiments."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from common import ELEMENTS


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DONOR_ZIP = (
    ROOT
    / "data"
    / "external"
    / "bandgap_borrowing"
    / "BandgapDatabase1_v2.zip"
)
DONOR_MEMBER = "Bandpgap_database_v2/Bandgap.csv"
HSE_ZIP = (
    ROOT
    / "data"
    / "external"
    / "bandgap_borrowing"
    / "hybrid_bandgap_210413.zip"
)
HYBRID3_CSV = (
    ROOT
    / "data"
    / "external"
    / "bandgap_borrowing"
    / "hybrid3_bandgap"
    / "hybrid3_bandgap_records.csv"
)
HYBRID3_MANIFEST = HYBRID3_CSV.with_name("hybrid3_bandgap_manifest.json")
RECIPIENT_CSV = (
    ROOT
    / "data"
    / "external"
    / "bandgap_borrowing"
    / "nomad_perovskite_v4"
    / "perovskite_solar_cell_recipient.csv"
)
RECIPIENT_MANIFEST = RECIPIENT_CSV.with_name(
    "perovskite_solar_cell_recipient_manifest.json"
)

ELEMENT_SET = set(ELEMENTS)
NUMBER = re.compile(r"^(?:\d+(?:\.\d*)?|\.\d+)")
ELEMENT = re.compile(r"^[A-Z][a-z]?")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_doi(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text.strip().rstrip(".,;")


def normalize_formula_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    text = (
        text.replace("−", "-")
        .replace("–", "-")
        .replace("·", ".")
        .replace(" ", "")
    )
    return re.sub(r"[^A-Za-z0-9().|+\-]", "", text)


def parse_value_list(value: object) -> list[float]:
    if value is None or pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return []
    if not isinstance(parsed, (list, tuple)):
        parsed = [parsed]
    output = []
    for item in parsed:
        try:
            numeric = float(item)
        except (TypeError, ValueError):
            continue
        if math.isfinite(numeric):
            output.append(numeric)
    return output


def parse_composition_literal(value: object) -> dict[str, float]:
    if value is None or pd.isna(value):
        return {}
    try:
        parsed = ast.literal_eval(str(value))
    except (ValueError, SyntaxError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    output: dict[str, float] = {}
    for element, amount in parsed.items():
        if str(element) not in ELEMENT_SET:
            return {}
        try:
            numeric = float(amount)
        except (TypeError, ValueError):
            return {}
        if not math.isfinite(numeric) or numeric <= 0:
            return {}
        output[str(element)] = output.get(str(element), 0.0) + numeric
    return output


def normalized_composition(
    composition: dict[str, float],
) -> dict[str, float]:
    total = float(sum(composition.values()))
    if total <= 0:
        return {}
    return {
        element: amount / total
        for element, amount in sorted(composition.items())
        if amount > 0
    }


def composition_key(composition: dict[str, float]) -> str:
    normalized = normalized_composition(composition)
    return "|".join(
        f"{element}:{fraction:.8f}"
        for element, fraction in normalized.items()
    )


def element_system_key(composition: dict[str, float]) -> str:
    return "-".join(sorted(composition))


def strip_ionic_charge(formula: str) -> str:
    text = formula.strip().replace(" ", "")
    # NOMAD ion formulae use both N+ and N+2 conventions.  A one-element
    # string such as Pb2+ encodes charge, not two Pb atoms.
    if re.fullmatch(r"[A-Z][a-z]?\d+[+-]", text):
        return re.sub(r"\d+[+-]$", "", text)
    text = re.sub(r"[+-]\d+$", "", text)
    text = re.sub(r"[+-]$", "", text)
    return text


def parse_plain_formula(formula: str) -> dict[str, float]:
    """Parse a parenthesis-free molecular formula with decimal counts."""
    text = strip_ionic_charge(formula)
    if not text or re.search(r"[xX]", text):
        return {}
    position = 0
    output: dict[str, float] = defaultdict(float)
    while position < len(text):
        match = ELEMENT.match(text[position:])
        if match is None:
            return {}
        element = match.group()
        if element not in ELEMENT_SET:
            return {}
        position += len(element)
        number = NUMBER.match(text[position:])
        amount = float(number.group()) if number else 1.0
        if number:
            position += len(number.group())
        if not math.isfinite(amount) or amount <= 0:
            return {}
        output[element] += amount
    return dict(output)


def parse_grouped_formula(formula: str) -> dict[str, float]:
    """Parse a conventional formula with nested parenthesized groups."""
    text = strip_ionic_charge(str(formula).replace(" ", ""))
    if (
        not text
        or re.search(r"[xX|.+-]", text)
        or not re.fullmatch(r"[A-Za-z0-9()]+", text)
    ):
        return {}
    position = 0

    def number() -> float:
        nonlocal position
        match = NUMBER.match(text[position:])
        if match is None:
            return 1.0
        position += len(match.group())
        return float(match.group())

    def group(stop_at_parenthesis: bool) -> dict[str, float]:
        nonlocal position
        output: dict[str, float] = defaultdict(float)
        while position < len(text):
            if text[position] == ")":
                if not stop_at_parenthesis:
                    return {}
                position += 1
                return dict(output)
            if text[position] == "(":
                position += 1
                nested = group(True)
                if not nested:
                    return {}
                coefficient = number()
                for element, amount in nested.items():
                    output[element] += coefficient * amount
                continue
            match = ELEMENT.match(text[position:])
            if match is None or match.group() not in ELEMENT_SET:
                return {}
            element = match.group()
            position += len(element)
            output[element] += number()
        if stop_at_parenthesis:
            return {}
        return dict(output)

    parsed = group(False)
    if position != len(text):
        return {}
    return parsed


def ion_formula_map(target: pd.DataFrame) -> dict[str, dict[str, float]]:
    observations: dict[str, list[dict[str, float]]] = defaultdict(list)
    for raw in target["ions_json"].dropna().astype(str):
        try:
            ions = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(ions, list):
            continue
        for ion in ions:
            if not isinstance(ion, dict):
                continue
            name = str(ion.get("name") or "").strip().strip("()")
            formula = str(ion.get("molecular_formula") or "")
            parsed = parse_plain_formula(formula)
            if name and parsed:
                observations[name].append(parsed)
    output: dict[str, dict[str, float]] = {}
    for name, candidates in observations.items():
        serialized = [
            json.dumps(item, sort_keys=True, separators=(",", ":"))
            for item in candidates
        ]
        # Some records expose equally frequent alternative encodings.  A set
        # iteration tie-break depends on PYTHONHASHSEED, so choose the
        # lexicographically first representation among the modal candidates.
        winner = sorted(
            set(serialized),
            key=lambda item: (-serialized.count(item), item),
        )[0]
        output[name] = json.loads(winner)
    return output


def parse_ions_json(value: object) -> tuple[dict[str, float], str, bool]:
    if value is None or pd.isna(value):
        return {}, "", False
    try:
        ions = json.loads(str(value))
    except json.JSONDecodeError:
        return {}, "", False
    if not isinstance(ions, list) or not ions:
        return {}, "", False
    composition: dict[str, float] = defaultdict(float)
    sites: dict[str, list[tuple[str, float]]] = defaultdict(list)
    valid = True
    for ion in ions:
        if not isinstance(ion, dict):
            valid = False
            continue
        name = str(ion.get("name") or "").strip().strip("()")
        site = str(ion.get("ion_type") or "?").strip().upper()
        formula = parse_plain_formula(str(ion.get("molecular_formula") or ""))
        try:
            coefficient = float(ion.get("coefficients"))
        except (TypeError, ValueError):
            valid = False
            continue
        if (
            not name
            or not formula
            or not math.isfinite(coefficient)
            or coefficient <= 0
        ):
            valid = False
            continue
        sites[site].append((name, coefficient))
        for element, amount in formula.items():
            composition[element] += coefficient * amount
    site_key = "|".join(
        f"{site}["
        + ",".join(
            f"{name}:{coefficient:.6g}"
            for name, coefficient in sorted(items)
        )
        + "]"
        for site, items in sorted(sites.items())
    )
    return dict(composition), site_key, valid and bool(composition)


def site_family_key(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        ions = json.loads(str(value))
    except json.JSONDecodeError:
        return ""
    sites: dict[str, set[str]] = defaultdict(set)
    if not isinstance(ions, list):
        return ""
    for ion in ions:
        if not isinstance(ion, dict):
            continue
        name = str(ion.get("name") or "").strip().strip("()")
        site = str(ion.get("ion_type") or "?").strip().upper()
        if name:
            sites[site].add(name)
    return "|".join(
        f"{site}[{','.join(sorted(names))}]"
        for site, names in sorted(sites.items())
    )


def parse_formula_with_ions(
    value: object,
    ion_map: dict[str, dict[str, float]],
) -> dict[str, float]:
    """Parse compact perovskite formulae such as CsFAMAPbBrI.

    This is deliberately conservative: variables, layer delimiters, ambiguous
    punctuation, and unmatched tokens are rejected instead of guessed.
    """
    text = normalize_formula_text(value)
    if (
        not text
        or "|" in text
        or re.search(r"[xX]", text)
        or any(character in text for character in ".+-")
    ):
        return {}
    text = text.replace("(", "").replace(")", "")
    names = sorted(
        (
            name
            for name in ion_map
            if name
            and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name)
            and name not in ELEMENT_SET
        ),
        key=lambda name: (-len(name), name),
    )
    position = 0
    output: dict[str, float] = defaultdict(float)
    while position < len(text):
        ion_name = next(
            (name for name in names if text.startswith(name, position)),
            None,
        )
        token_composition: dict[str, float]
        if ion_name is not None:
            token_composition = ion_map[ion_name]
            position += len(ion_name)
        else:
            match = ELEMENT.match(text[position:])
            if match is None or match.group() not in ELEMENT_SET:
                return {}
            token_composition = {match.group(): 1.0}
            position += len(match.group())
        number = NUMBER.match(text[position:])
        coefficient = float(number.group()) if number else 1.0
        if number:
            position += len(number.group())
        if not math.isfinite(coefficient) or coefficient <= 0:
            return {}
        for element, amount in token_composition.items():
            output[element] += coefficient * amount
    return dict(output)


def load_recipient(
    columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    if not RECIPIENT_CSV.exists() or not RECIPIENT_MANIFEST.exists():
        raise FileNotFoundError(
            "Complete NOMAD recipient snapshot is missing; run "
            "analysis/download_nomad_perovskite_recipient.py first."
        )
    manifest = json.loads(RECIPIENT_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise RuntimeError("Recipient manifest is not complete")
    if sha256(RECIPIENT_CSV) != manifest.get("csv_sha256"):
        raise RuntimeError("Recipient CSV hash does not match its manifest")
    required = {"doi", "ions_json", "composition_long_form"}
    usecols = None if columns is None else sorted(set(columns) | required)
    target = pd.read_csv(
        RECIPIENT_CSV,
        usecols=usecols,
        low_memory=False,
    )
    if len(target) != int(manifest["rows"]):
        raise RuntimeError("Recipient row count changed after download")
    target["doi_norm"] = target["doi"].map(normalize_doi)
    parsed = target["ions_json"].map(parse_ions_json)
    target["composition_dict"] = parsed.map(lambda item: item[0])
    target["composition_key"] = target["composition_dict"].map(
        composition_key
    )
    target["element_system"] = target["composition_dict"].map(
        element_system_key
    )
    target["site_key"] = parsed.map(lambda item: item[1])
    target["ions_valid"] = parsed.map(lambda item: item[2])
    target["site_family"] = target["ions_json"].map(site_family_key)
    target["formula_text_key"] = target["composition_long_form"].map(
        normalize_formula_text
    )
    for column in (
        "band_gap",
        "pce",
        "voc",
        "jsc",
        "fill_factor",
        "cell_area_total",
        "cell_area_measured",
        "deposition_steps",
        "light_intensity",
        "test_temperature",
    ):
        if column in target:
            target[column] = pd.to_numeric(target[column], errors="coerce")
    return target


def load_donor_raw() -> pd.DataFrame:
    if not DONOR_ZIP.exists():
        raise FileNotFoundError(DONOR_ZIP)
    with zipfile.ZipFile(DONOR_ZIP) as archive:
        source = pd.read_csv(
            archive.open(DONOR_MEMBER),
            low_memory=False,
        )
    source["doi_norm"] = source["DOI"].map(normalize_doi)
    values = source["Value"].map(parse_value_list)
    source["band_gap"] = values.map(
        lambda item: float(np.median(item)) if item else np.nan
    )
    source["value_width"] = values.map(
        lambda item: float(max(item) - min(item)) if item else np.nan
    )
    source["composition_dict"] = source["Composition"].map(
        parse_composition_literal
    )
    source["composition_key"] = source["composition_dict"].map(
        composition_key
    )
    source["element_system"] = source["composition_dict"].map(
        element_system_key
    )
    source["formula_text_key"] = source["Name"].map(normalize_formula_text)
    return source


def recover_donor_compositions(
    source: pd.DataFrame,
    target: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """Recover compact perovskite names using target ion definitions only.

    The target contributes chemistry vocabulary (ion name -> formula), never a
    band-gap or photovoltaic outcome.  Existing valid source compositions are
    left untouched.
    """
    frame = source.copy()
    mapping = ion_formula_map(target)
    missing = frame["composition_key"].eq("")
    recovered = frame.loc[missing, "Name"].map(
        lambda value: parse_formula_with_ions(value, mapping)
    )
    recovered_n = int(recovered.map(bool).sum())
    frame.loc[missing, "composition_dict"] = pd.Series(
        recovered,
        index=frame.index[missing],
        dtype=object,
    )
    frame.loc[missing, "composition_key"] = frame.loc[
        missing, "composition_dict"
    ].map(composition_key)
    frame.loc[missing, "element_system"] = frame.loc[
        missing, "composition_dict"
    ].map(element_system_key)
    return frame, recovered_n


def robust_donor_records(
    source: pd.DataFrame,
    *,
    target: pd.DataFrame | None = None,
    exclude_target_dois: bool = True,
    exclude_target_compositions: bool = False,
) -> pd.DataFrame:
    """Fixed high-precision gate for the text-mined experimental donor."""
    frame = source[
        source["doi_norm"].ne("")
        & source["composition_key"].ne("")
        & source["Unit"].astype(str).str.contains("ElectronVolt", na=False)
        & source["band_gap"].between(0.20, 6.00, inclusive="both")
        & source["value_width"].le(0.50)
        & source["Snowball"].eq(True)
        & pd.to_numeric(source["Confidence"], errors="coerce").ge(0.80)
    ].copy()
    if target is not None and exclude_target_dois:
        target_dois = set(target["doi_norm"]) - {""}
        frame = frame[~frame["doi_norm"].isin(target_dois)].copy()
    if target is not None and exclude_target_compositions:
        target_compositions = set(target["composition_key"]) - {""}
        frame = frame[
            ~frame["composition_key"].isin(target_compositions)
        ].copy()
    return frame


def aggregate_donor(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate extraction duplicates within DOI before across-study use."""
    within_doi = (
        frame.groupby(["composition_key", "doi_norm"], as_index=False)
        .agg(
            band_gap=("band_gap", "median"),
            element_system=("element_system", "first"),
            formula_name=("Name", "first"),
            extraction_rows=("band_gap", "size"),
        )
        .sort_values(["composition_key", "doi_norm"])
    )
    cards = (
        within_doi.groupby("composition_key", as_index=False)
        .agg(
            band_gap=("band_gap", "median"),
            band_gap_q25=("band_gap", lambda x: float(np.quantile(x, 0.25))),
            band_gap_q75=("band_gap", lambda x: float(np.quantile(x, 0.75))),
            n_dois=("doi_norm", "nunique"),
            n_extractions=("extraction_rows", "sum"),
            element_system=("element_system", "first"),
            formula_name=("formula_name", "first"),
        )
        .sort_values("composition_key")
        .reset_index(drop=True)
    )
    cards["band_gap_iqr"] = (
        cards["band_gap_q75"] - cards["band_gap_q25"]
    )
    return cards


def load_hse_cards() -> pd.DataFrame:
    """Load composition-level HSE cards from the SNUMAT Figshare release."""
    if not HSE_ZIP.exists():
        raise FileNotFoundError(HSE_ZIP)
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(HSE_ZIP) as archive:
        for member in sorted(archive.namelist()):
            if not member.lower().endswith(".json"):
                continue
            formula = Path(member).stem.rsplit("_", 1)[0]
            composition = parse_plain_formula(formula)
            if not composition:
                continue
            try:
                record = json.load(archive.open(member))
                hse = float(record.get("Band_gap_HSE"))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not math.isfinite(hse) or not 0.0 < hse <= 6.0:
                continue
            try:
                gga = float(record.get("Band_gap_GGA"))
            except (TypeError, ValueError):
                gga = float("nan")
            rows.append(
                {
                    "composition_key": composition_key(composition),
                    "composition_dict": composition,
                    "element_system": element_system_key(composition),
                    "band_gap_hse": hse,
                    "band_gap_gga": gga,
                    "icsd_number": str(record.get("ICSD_number") or ""),
                    "snumat_id": str(record.get("SNUMAT_id") or ""),
                    "soc": str(record.get("SOC") or ""),
                }
            )
    raw = pd.DataFrame(rows)
    cards = (
        raw.groupby("composition_key", as_index=False)
        .agg(
            band_gap_hse=("band_gap_hse", "median"),
            band_gap_hse_q25=(
                "band_gap_hse",
                lambda x: float(np.quantile(x, 0.25)),
            ),
            band_gap_hse_q75=(
                "band_gap_hse",
                lambda x: float(np.quantile(x, 0.75)),
            ),
            band_gap_gga=("band_gap_gga", "median"),
            n_structures=("band_gap_hse", "size"),
            element_system=("element_system", "first"),
            composition_dict=("composition_dict", "first"),
        )
        .sort_values("composition_key")
        .reset_index(drop=True)
    )
    cards["band_gap_hse_iqr"] = (
        cards["band_gap_hse_q75"] - cards["band_gap_hse_q25"]
    )
    cards.attrs["raw_structures"] = len(raw)
    return cards


def hybrid3_composition(row: pd.Series) -> dict[str, float]:
    candidates: list[dict[str, float]] = []
    alternate = str(row.get("alternate_names") or "")
    tokens = re.findall(r"\([^)]*\)\d*[A-Za-z0-9]+|[A-Z][A-Za-z0-9()]+", alternate)
    for token in tokens:
        parsed = parse_grouped_formula(token.strip(" ,;"))
        if parsed:
            candidates.append(parsed)
    organic = str(row.get("organic_component") or "").split(",", 1)[0]
    inorganic = str(row.get("inorganic_component") or "").split(",", 1)[0]
    combined = parse_grouped_formula(organic + inorganic)
    if combined:
        candidates.append(combined)
    if not candidates:
        return {}
    serialized = [
        json.dumps(
            normalized_composition(item),
            sort_keys=True,
            separators=(",", ":"),
        )
        for item in candidates
    ]
    winner = sorted(
        set(serialized),
        key=lambda item: (-serialized.count(item), item),
    )[0]
    normalized = json.loads(winner)
    # Re-normalized fractions are sufficient because all downstream keys and
    # feature matrices are scale invariant.
    return {str(key): float(value) for key, value in normalized.items()}


def load_hybrid3_cards(
    *,
    target: pd.DataFrame | None = None,
    exclude_target_dois: bool = True,
) -> pd.DataFrame:
    """Load high-specificity experimental HybriD3 band-gap cards."""
    if not HYBRID3_CSV.exists() or not HYBRID3_MANIFEST.exists():
        raise FileNotFoundError(
            "Complete HybriD3 snapshot is missing; run "
            "analysis/download_hybrid3_bandgap_donor.py first."
        )
    manifest = json.loads(HYBRID3_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete":
        raise RuntimeError("HybriD3 manifest is not complete")
    if sha256(HYBRID3_CSV) != manifest.get("csv_sha256"):
        raise RuntimeError("HybriD3 CSV hash does not match its manifest")
    raw = pd.read_csv(HYBRID3_CSV, low_memory=False)
    raw["doi_norm"] = raw["doi"].map(normalize_doi)
    raw["band_gap"] = pd.to_numeric(raw["band_gap_ev"], errors="coerce")
    raw["composition_dict"] = raw.apply(hybrid3_composition, axis=1)
    raw["composition_key"] = raw["composition_dict"].map(composition_key)
    raw["element_system"] = raw["composition_dict"].map(element_system_key)
    clean = raw[
        raw["origin"].astype(str).str.lower().eq("experimental")
        & raw["verified"].astype(str).str.lower().isin({"true", "1"})
        & raw["doi_norm"].ne("")
        & raw["composition_key"].ne("")
        & raw["band_gap"].between(0.2, 6.0, inclusive="both")
    ].copy()
    if target is not None and exclude_target_dois:
        target_dois = set(target["doi_norm"]) - {""}
        clean = clean[~clean["doi_norm"].isin(target_dois)].copy()
    within_doi = (
        clean.groupby(["composition_key", "doi_norm"], as_index=False)
        .agg(
            band_gap=("band_gap", "median"),
            material_name=("material_name", "first"),
            element_system=("element_system", "first"),
            composition_dict=("composition_dict", "first"),
            records=("band_gap", "size"),
        )
    )
    cards = (
        within_doi.groupby("composition_key", as_index=False)
        .agg(
            band_gap=("band_gap", "median"),
            band_gap_q25=("band_gap", lambda x: float(np.quantile(x, 0.25))),
            band_gap_q75=("band_gap", lambda x: float(np.quantile(x, 0.75))),
            n_dois=("doi_norm", "nunique"),
            n_records=("records", "sum"),
            material_name=("material_name", "first"),
            element_system=("element_system", "first"),
            composition_dict=("composition_dict", "first"),
        )
        .sort_values("composition_key")
        .reset_index(drop=True)
    )
    cards["band_gap_iqr"] = (
        cards["band_gap_q75"] - cards["band_gap_q25"]
    )
    cards.attrs["raw_rows"] = len(raw)
    cards.attrs["clean_rows"] = len(clean)
    return cards


def composition_matrix(
    compositions: Iterable[dict[str, float]],
) -> np.ndarray:
    """Element fractions plus deterministic distribution descriptors."""
    element_index = {element: index for index, element in enumerate(ELEMENTS)}
    rows = list(compositions)
    output = np.zeros((len(rows), len(ELEMENTS) + 8), dtype=float)
    for row_index, raw in enumerate(rows):
        normalized = normalized_composition(raw)
        for element, fraction in normalized.items():
            output[row_index, element_index[element]] = fraction
        fractions = output[row_index, : len(ELEMENTS)]
        present = np.flatnonzero(fractions)
        if not len(present):
            continue
        atomic_numbers = present + 1
        weights = fractions[present]
        mean_z = float(np.sum(weights * atomic_numbers))
        output[row_index, len(ELEMENTS) :] = (
            len(present),
            mean_z,
            math.sqrt(
                float(np.sum(weights * (atomic_numbers - mean_z) ** 2))
            ),
            float(atomic_numbers.min()),
            float(atomic_numbers.max()),
            float(weights.max()),
            -float(np.sum(weights * np.log(weights))),
            float(np.sum(weights**2)),
        )
    return output
