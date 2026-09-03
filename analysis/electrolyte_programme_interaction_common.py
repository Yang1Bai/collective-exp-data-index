"""Shared, auditable loaders for cross-programme electrolyte borrowing.

The public BambooMixer source records use normalized molar component weights,
whereas the local CALiSol, KIT, SolventSeg and FINALES records use component
masses.  This module converts the latter without target-outcome-dependent
choices.  Conductivity is represented in mS cm-1 throughout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from mixture_response_transfer_common import conductivity_records, load_json_records


COMPONENTS = {
    "PC": {
        "smiles": "CC1COC(=O)O1",
        "molecular_weight": 102.09,
    },
    "EC": {
        "smiles": "O=C1OCCO1",
        "molecular_weight": 88.062,
    },
    "EMC": {
        "smiles": "CCOC(=O)OC",
        "molecular_weight": 104.105,
    },
    "LiPF6": {
        "smiles": "F[P-](F)(F)(F)(F)F",
        "molecular_weight": 151.905,
    },
}
TARGET_SOLVENTS = frozenset({"EC", "EMC"})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_hash(path: Path, expected: str) -> None:
    observed = sha256(path)
    if observed != str(expected).lower():
        raise RuntimeError(f"Hash mismatch for {path}: {observed} != {expected}")


def _component(name: str, molar_ratio: float) -> dict:
    spec = COMPONENTS[name]
    return {
        "name": name,
        "smiles": spec["smiles"],
        "molar_ratio": float(molar_ratio),
    }


def mass_formulation_record(
    *,
    solvent_masses: dict[str, float],
    salt_mass: float,
    temperature_C: float,
    conductivity_mS_cm: float,
    programme: str,
    source_id: str,
) -> dict:
    """Convert reported component masses or fractions to the common record."""
    active = {
        name: float(value)
        for name, value in solvent_masses.items()
        if float(value) > 1e-12
    }
    unknown = sorted(set(active) - TARGET_SOLVENTS - {"PC"})
    if unknown:
        raise ValueError(f"Unsupported solvent components: {unknown}")
    if not active:
        raise ValueError("A liquid formulation needs at least one solvent")
    salt_mass = float(salt_mass)
    if salt_mass <= 0:
        raise ValueError("LiPF6 mass must be positive")
    solvent_moles = {
        name: mass / float(COMPONENTS[name]["molecular_weight"])
        for name, mass in active.items()
    }
    salt_moles = salt_mass / float(COMPONENTS["LiPF6"]["molecular_weight"])
    solvent_total = float(sum(solvent_moles.values()))
    total_moles = solvent_total + salt_moles
    if solvent_total <= 0 or total_moles <= 0:
        raise ValueError("Invalid component mole total")
    conductivity = float(conductivity_mS_cm)
    if conductivity <= 0 or not np.isfinite(conductivity):
        raise ValueError("Conductivity must be positive and finite")
    return {
        "solvents": [
            _component(name, solvent_moles[name] / solvent_total)
            for name in sorted(solvent_moles)
        ],
        "salts": [_component("LiPF6", 1.0)],
        "salt_molar_ratio": float(salt_moles / total_moles),
        "temperature": float(temperature_C),
        "conductivity": conductivity,
        "conductivity_mask": True,
        "programme": str(programme),
        "source_id": str(source_id),
    }


def exact_formulation_signature(record: dict) -> str:
    """Identity includes salt concentration, unlike the legacy helper."""
    payload = {
        "solvents": sorted(
            [
                (
                    str(component["name"]),
                    round(float(component["molar_ratio"]), 8),
                )
                for component in record["solvents"]
            ]
        ),
        "salts": sorted(str(component["name"]) for component in record["salts"]),
        "salt_molar_ratio": round(float(record["salt_molar_ratio"]), 8),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def source_contains_target_family(record: dict) -> bool:
    salts = {str(component["name"]) for component in record["salts"]}
    solvents = {str(component["name"]) for component in record["solvents"]}
    return salts == {"LiPF6"} and solvents.issubset(TARGET_SOLVENTS)


def load_bamboo(path: Path) -> list[dict]:
    records = conductivity_records(load_json_records(path))
    for index, record in enumerate(records):
        record["programme"] = "bamboomixer"
        record["source_id"] = f"bamboo_{index:06d}"
    return records


def load_solventseg(path: Path) -> tuple[list[dict], pd.DataFrame]:
    frame = pd.read_csv(path)
    required = {
        "formulation_id",
        "EC_wt",
        "EMC_wt",
        "LiPF6_wt",
        "temperature_C",
        "conductivity_mS_cm",
    }
    if set(frame.columns) != required:
        raise AssertionError("SolventSeg schema changed")
    records = [
        mass_formulation_record(
            solvent_masses={"EC": row.EC_wt, "EMC": row.EMC_wt},
            salt_mass=row.LiPF6_wt,
            temperature_C=row.temperature_C,
            conductivity_mS_cm=row.conductivity_mS_cm,
            programme="solventseg",
            source_id=f"solventseg_{int(row.formulation_id):03d}_{float(row.temperature_C):g}",
        )
        for row in frame.itertuples(index=False)
    ]
    frame = frame.copy()
    frame["record_index"] = np.arange(len(frame), dtype=int)
    frame["formula_group"] = [exact_formulation_signature(record) for record in records]
    return records, frame


def load_calisol_subset(path: Path) -> tuple[list[dict], pd.DataFrame]:
    frame = pd.read_csv(path)
    required = {
        "source_doi",
        "EC_wt",
        "EMC_wt",
        "LiPF6_wt",
        "temperature_C",
        "conductivity_mS_cm",
        "source_concentration_mol_kg",
    }
    if set(frame.columns) != required:
        raise AssertionError("CALiSol harmonized subset schema changed")
    records = [
        mass_formulation_record(
            solvent_masses={"EC": row.EC_wt, "EMC": row.EMC_wt},
            salt_mass=row.LiPF6_wt,
            temperature_C=row.temperature_C,
            conductivity_mS_cm=row.conductivity_mS_cm,
            programme="calisol",
            source_id=f"{row.source_doi}|{index:04d}",
        )
        for index, row in enumerate(frame.itertuples(index=False))
    ]
    return records, frame


def load_kit(path: Path) -> tuple[list[dict], pd.DataFrame]:
    frame = pd.read_csv(path, sep=";", skiprows=[1, 2])
    required = {
        "experimentID",
        "PC",
        "EC",
        "EMC",
        "LiPF_6",
        "temperature",
        "EIS_conductivity",
    }
    if not required.issubset(frame.columns):
        raise AssertionError("KIT schema changed")
    numeric = ["PC", "EC", "EMC", "LiPF_6", "temperature", "EIS_conductivity"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[numeric].isna().any().any():
        raise AssertionError("KIT contains missing required numeric values")
    rounded = frame[["PC", "EC", "EMC", "LiPF_6"]].round(6)
    frame["formula_key"] = rounded.astype(str).agg("|".join, axis=1)
    grouped = (
        frame.groupby(["formula_key", "temperature"], as_index=False)
        .agg(
            PC=("PC", "median"),
            EC=("EC", "median"),
            EMC=("EMC", "median"),
            LiPF_6=("LiPF_6", "median"),
            conductivity_S_cm=("EIS_conductivity", "median"),
            raw_experiments=("experimentID", "nunique"),
        )
        .sort_values(["formula_key", "temperature"])
        .reset_index(drop=True)
    )
    records = [
        mass_formulation_record(
            solvent_masses={"PC": row.PC, "EC": row.EC, "EMC": row.EMC},
            salt_mass=row.LiPF_6,
            temperature_C=row.temperature,
            conductivity_mS_cm=1000.0 * row.conductivity_S_cm,
            programme="kit",
            source_id=f"{row.formula_key}|{float(row.temperature):g}",
        )
        for row in grouped.itertuples(index=False)
    ]
    return records, grouped


def load_finales(paths: Sequence[Path]) -> tuple[list[dict], pd.DataFrame]:
    tables = [pd.read_csv(path) for path in paths]
    frame = pd.concat(tables, ignore_index=True)
    required = {
        "phase",
        "formulation_key",
        "EC_wt",
        "EMC_wt",
        "LiPF6_wt",
        "temperature_C",
        "conductivity",
        "split",
    }
    if not required.issubset(frame.columns):
        raise AssertionError("FINALES candidate schema changed")
    records = [
        mass_formulation_record(
            solvent_masses={"EC": row.EC_wt, "EMC": row.EMC_wt},
            salt_mass=row.LiPF6_wt,
            temperature_C=row.temperature_C,
            conductivity_mS_cm=row.conductivity,
            programme=f"finales_{row.phase}",
            source_id=f"{row.phase}|{row.formulation_key}",
        )
        for row in frame.itertuples(index=False)
    ]
    frame = frame.copy()
    frame["record_index"] = np.arange(len(frame), dtype=int)
    frame["formula_group"] = [exact_formulation_signature(record) for record in records]
    return records, frame


def target_family_coordinate(record: dict) -> np.ndarray | None:
    if not source_contains_target_family(record):
        return None
    solvent = {
        str(component["name"]): float(component["molar_ratio"])
        for component in record["solvents"]
    }
    total = sum(solvent.values())
    ec_fraction = solvent.get("EC", 0.0) / total
    return np.asarray(
        [
            ec_fraction,
            float(record["salt_molar_ratio"]),
            float(record["temperature"]),
            float(record["conductivity"]),
        ],
        dtype=float,
    )


def strict_record_overlap_count(
    source: Iterable[dict],
    target: Iterable[dict],
    *,
    composition_tolerance: float,
    temperature_tolerance: float,
    outcome_tolerance: float,
) -> int:
    source_coordinates = [
        coordinate
        for record in source
        if (coordinate := target_family_coordinate(record)) is not None
    ]
    target_coordinates = [
        coordinate
        for record in target
        if (coordinate := target_family_coordinate(record)) is not None
    ]
    if not source_coordinates or not target_coordinates:
        return 0
    source_matrix = np.vstack(source_coordinates)
    matches = 0
    for coordinate in target_coordinates:
        temperature = np.abs(source_matrix[:, 2] - coordinate[2])
        candidates = source_matrix[temperature <= float(temperature_tolerance)]
        if not len(candidates):
            continue
        composition = np.abs(candidates[:, :2] - coordinate[:2]).sum(axis=1)
        outcome = np.abs(candidates[:, 3] - coordinate[3])
        if np.any(
            (composition <= float(composition_tolerance))
            & (outcome <= float(outcome_tolerance))
        ):
            matches += 1
    return int(matches)


def general_record_overlap_count(
    source: Iterable[dict],
    target: Iterable[dict],
    *,
    composition_tolerance: float,
    temperature_tolerance: float,
    outcome_tolerance: float,
) -> int:
    """Count target records with a near-identical source record.

    Component identities must agree exactly.  The composition distance is the
    L1 distance over normalized solvent weights and salt molar ratio.
    """
    grouped_source: dict[tuple[tuple[str, ...], tuple[str, ...]], list[np.ndarray]] = {}
    for record in source:
        solvent_names = tuple(sorted(str(item["name"]) for item in record["solvents"]))
        salt_names = tuple(sorted(str(item["name"]) for item in record["salts"]))
        solvent = {
            str(item["name"]): float(item["molar_ratio"])
            for item in record["solvents"]
        }
        total = sum(solvent.values())
        coordinate = np.asarray(
            [
                *[solvent[name] / total for name in solvent_names],
                float(record["salt_molar_ratio"]),
                float(record["temperature"]),
                float(record["conductivity"]),
            ],
            dtype=float,
        )
        grouped_source.setdefault((solvent_names, salt_names), []).append(coordinate)
    matrices = {
        key: np.vstack(values)
        for key, values in grouped_source.items()
    }
    matches = 0
    for record in target:
        solvent_names = tuple(sorted(str(item["name"]) for item in record["solvents"]))
        salt_names = tuple(sorted(str(item["name"]) for item in record["salts"]))
        matrix = matrices.get((solvent_names, salt_names))
        if matrix is None:
            continue
        solvent = {
            str(item["name"]): float(item["molar_ratio"])
            for item in record["solvents"]
        }
        total = sum(solvent.values())
        composition = np.asarray(
            [
                *[solvent[name] / total for name in solvent_names],
                float(record["salt_molar_ratio"]),
            ],
            dtype=float,
        )
        temperature = float(record["temperature"])
        outcome = float(record["conductivity"])
        candidates = matrix[
            np.abs(matrix[:, -2] - temperature) <= float(temperature_tolerance)
        ]
        if not len(candidates):
            continue
        distance = np.abs(candidates[:, :-2] - composition).sum(axis=1)
        outcome_distance = np.abs(candidates[:, -1] - outcome)
        if np.any(
            (distance <= float(composition_tolerance))
            & (outcome_distance <= float(outcome_tolerance))
        ):
            matches += 1
    return int(matches)


def percentile_rank(values: Sequence[float]) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = pd.Series(values).rank(method="average", pct=True).to_numpy(float)
    return order
