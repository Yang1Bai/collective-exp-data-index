"""Load alloy datasets from the collective SQLite data lake.

Converts alloy measurements to CatalystSample format for use with the
CatalystTransferTransformer model. Handles composition-only inputs
(no spectra or experimental conditions required).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Sequence

import numpy as np

from .data import ATOMIC_NUMBER, CatalystSample, CONDITION_NAMES
from .schema import MEASUREMENT_MODALITY_NAMES, PROGRAM_NAMES, REACTION_NAMES, TARGET_NAMES


# ---- Composition parsers for different alloy formula formats ----


def _parse_formula_fraction(formula: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse 'Fe0.620C0.000953...' format (matbench-steels).

    Returns (elements, fractions) sorted by atomic number.
    """
    pattern = re.compile(r'([A-Z][a-z]?)(-?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)')
    pairs = pattern.findall(str(formula))
    if not pairs:
        raise ValueError(f"cannot parse formula: {formula!r}")

    elements = []
    fractions = []
    for symbol, value_str in pairs:
        z = ATOMIC_NUMBER.get(symbol)
        if z is None:
            continue
        f = float(value_str)
        if f <= 0:
            continue
        elements.append(z)
        fractions.append(f)

    if not elements:
        raise ValueError(f"no valid elements in formula: {formula!r}")

    elements_arr = np.asarray(elements, dtype=np.int64)
    fractions_arr = np.asarray(fractions, dtype=np.float32)
    fractions_arr /= fractions_arr.sum()
    return elements_arr, fractions_arr


def _parse_mpea_composition(material: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse 'Al0.25 Co1 Fe1 Ni1' format (MPEA).

    Space-separated pairs: ElementAmount. Amount may need normalization.
    """
    parts = str(material).strip().split()
    elements = []
    amounts = []
    for part in parts:
        match = re.match(r'^([A-Z][a-z]?)(-?[0-9]*\.?[0-9]+)$', part)
        if not match:
            continue
        symbol, val_str = match.groups()
        z = ATOMIC_NUMBER.get(symbol)
        if z is None:
            continue
        val = float(val_str)
        if val <= 0:
            continue
        elements.append(z)
        amounts.append(val)

    if not elements:
        raise ValueError(f"no elements in MPEA material: {material!r}")

    elements_arr = np.asarray(elements, dtype=np.int64)
    amounts_arr = np.asarray(amounts, dtype=np.float32)
    fractions_arr = amounts_arr / amounts_arr.sum()
    return elements_arr, fractions_arr


def _parse_birdshot_composition(material: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse 'Co45Cr10Fe20Ni15V10' format (BIRDSHOT HEA).

    Element + percentage. Percentages sum to ~100.
    """
    pattern = re.compile(r'([A-Z][a-z]?)([0-9]+\.?[0-9]*)')
    pairs = pattern.findall(str(material))
    if not pairs:
        raise ValueError(f"cannot parse BIRDSHOT material: {material!r}")

    elements = []
    amounts = []
    for symbol, val_str in pairs:
        z = ATOMIC_NUMBER.get(symbol)
        if z is None:
            continue
        val = float(val_str)
        if val <= 0:
            continue
        elements.append(z)
        amounts.append(val)

    if not elements:
        raise ValueError(f"no elements in BIRDSHOT material: {material!r}")

    elements_arr = np.asarray(elements, dtype=np.int64)
    amounts_arr = np.asarray(amounts, dtype=np.float32)
    fractions_arr = amounts_arr / amounts_arr.sum()
    return elements_arr, fractions_arr


# ---- Dataset loaders ----


def load_steels(db_path: str | Path, target_property: str = "yield strength") -> list[CatalystSample]:
    """Load matbench-steels with composition-only features.

    Parameters
    ----------
    db_path: Path to collective.sqlite.
    target_property: 'yield strength', 'tensile strength', or 'elongation'.
    """
    db = sqlite3.connect(str(db_path))
    query = """
        SELECT formula, [yield strength], [tensile strength], elongation
        FROM raw_matbench_steels
    """
    rows = db.execute(query).fetchall()
    db.close()

    target_idx = {"yield strength": 1, "tensile strength": 2, "elongation": 3}[target_property]

    samples = []
    for idx, row in enumerate(rows):
        target_val = row[target_idx]
        if target_val is None:
            continue
        try:
            elements, fractions = _parse_formula_fraction(str(row[0]))
        except ValueError:
            continue

        condition_values = np.zeros(len(CONDITION_NAMES), dtype=np.float32)
        condition_mask = np.zeros(len(CONDITION_NAMES), dtype=np.float32)

        target_name_map = {
            "yield strength": "yield_strength_mpa",
            "tensile strength": "tensile_strength_mpa",
            "elongation": "elongation_pct",
        }
        tname = target_name_map.get(target_property, target_property)

        sample = CatalystSample(
            sample_id=f"steel-{idx:04d}",
            program="matbench_steels",
            elements=elements,
            fractions=fractions,
            curve_axis=np.zeros(0, dtype=np.float32),
            curve_values=np.zeros((0, 2), dtype=np.float32),
            curve_channel_mask=np.zeros(2, dtype=np.float32),
            condition_values=condition_values,
            condition_mask=condition_mask,
            reaction_id=0,
            modality_id=0,
            program_id=PROGRAM_NAMES.index("unknown") if "matbench_steels" not in PROGRAM_NAMES else 0,
            target=float(target_val),
            target_name=tname,
            group_id=f"steel-{idx // 5}",
            provenance={"dataset": "matbench-steels", "formula": str(row[0])},
        )
        samples.append(sample)

    return samples


def load_mpea(db_path: str | Path, target_property: str = "YS (MPa)") -> list[CatalystSample]:
    """Load MPEA dataset, deduplicating by material_key to one row per composition."""
    db = sqlite3.connect(str(db_path))
    query = """
        SELECT material_raw, material_key, value, property
        FROM measurements
        WHERE dataset = 'mpea-dataset-borg' AND property = ?
    """
    rows = db.execute(query, [f"PROPERTY: {target_property}"]).fetchall()
    db.close()

    # Deduplicate: one sample per unique material_key, average target if multiple.
    from collections import defaultdict
    groups = defaultdict(list)
    for material, mat_key, value, prop in rows:
        if value is None or mat_key is None:
            continue
        groups[mat_key].append((material, float(value), prop))

    samples = []
    for idx, (mat_key, entries) in enumerate(sorted(groups.items())):
        material = entries[0][0]
        value = np.mean([e[1] for e in entries])
        prop = entries[0][2]
        try:
            elements, fractions = _parse_mpea_composition(str(material))
        except ValueError:
            continue

        condition_values = np.zeros(len(CONDITION_NAMES), dtype=np.float32)
        condition_mask = np.zeros(len(CONDITION_NAMES), dtype=np.float32)

        sample = CatalystSample(
            sample_id=f"mpea-{idx:04d}",
            program="mpea_borg",
            elements=elements,
            fractions=fractions,
            curve_axis=np.zeros(0, dtype=np.float32),
            curve_values=np.zeros((0, 2), dtype=np.float32),
            curve_channel_mask=np.zeros(2, dtype=np.float32),
            condition_values=condition_values,
            condition_mask=condition_mask,
            reaction_id=0,
            modality_id=0,
            program_id=0,
            target=float(value),
            target_name="yield_strength_mpa",
            group_id=f"mpea-{idx // 5}",
            provenance={"dataset": "mpea-dataset-borg", "material": str(material), "mat_key": str(mat_key)},
        )
        samples.append(sample)

    return samples


def load_birdshot(db_path: str | Path, target_property: str = "Yield Strength (MPa)") -> list[CatalystSample]:
    """Load BIRDSHOT HEA dataset."""
    db = sqlite3.connect(str(db_path))
    query = """
        SELECT material_raw, value, property
        FROM measurements
        WHERE dataset = 'birdshot-high-entropy-alloy-campaign' AND property = ?
    """
    rows = db.execute(query, [target_property]).fetchall()
    db.close()

    samples = []
    for idx, (material, value, prop) in enumerate(rows):
        if value is None:
            continue
        try:
            elements, fractions = _parse_birdshot_composition(str(material))
        except ValueError:
            continue

        condition_values = np.zeros(len(CONDITION_NAMES), dtype=np.float32)
        condition_mask = np.zeros(len(CONDITION_NAMES), dtype=np.float32)

        sample = CatalystSample(
            sample_id=f"birdshot-{idx:04d}",
            program="birdshot_hea",
            elements=elements,
            fractions=fractions,
            curve_axis=np.zeros(0, dtype=np.float32),
            curve_values=np.zeros((0, 2), dtype=np.float32),
            curve_channel_mask=np.zeros(2, dtype=np.float32),
            condition_values=condition_values,
            condition_mask=condition_mask,
            reaction_id=0,
            modality_id=0,
            program_id=0,
            target=float(value),
            target_name=prop.replace(" ", "_").replace("(", "").replace(")", "").lower(),
            group_id=f"birdshot-{idx // 5}",
            provenance={"dataset": "birdshot-high-entropy-alloy-campaign", "material": str(material)},
        )
        samples.append(sample)

    return samples
