"""Reusable, leakage-aware utilities for mixture-response knowledge borrowing.

The representation is inspired by the BambooMixer formulation model but is
deliberately smaller and auditable:

1. describe each molecule with physicochemical descriptors and a Morgan bit
   vector;
2. aggregate components with normalized molar weights, preserving permutation
   invariance;
3. keep temperature and concentration in an explicit state block; and
4. adapt a frozen source prediction through a strongly regularized residual
   correction rather than refitting the source relation on a few target labels.

The utilities never inspect target outcomes when constructing representations,
formulation groups, or coverage anchors.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, Crippen, Descriptors, Lipinski, rdMolDescriptors
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler


FP_SIZE = 256
ELEMENTS = ("C", "N", "O", "F", "P", "S", "Cl", "B", "As", "Si", "Li")
SCALAR_NAMES = (
    "mol_weight_over_200",
    "logp_over_5",
    "tpsa_over_150",
    "h_donors_over_5",
    "h_acceptors_over_10",
    "rotatable_bonds_over_10",
    "rings_over_5",
    "fraction_csp3",
    "heavy_atoms_over_30",
    "formal_charge_over_3",
)
MOLECULE_FEATURE_NAMES = (
    *SCALAR_NAMES,
    *(f"element_fraction_{element}" for element in ELEMENTS),
    *(f"morgan_{index:03d}" for index in range(FP_SIZE)),
)
STATE_FEATURE_NAMES = (
    "solvent_component_count_over_5",
    "solvent_ratio_entropy_over_2",
    "salt_molar_ratio",
    "salt_molar_ratio_squared",
    "log_salt_molar_ratio",
    "inverse_temperature_1000_per_K",
    "inverse_temperature_times_log_concentration",
    "inverse_temperature_times_concentration",
    "inverse_temperature_squared_scaled",
)
MOLECULE_FEATURE_DIM = len(MOLECULE_FEATURE_NAMES)
CHEMISTRY_FEATURE_DIM = 3 * MOLECULE_FEATURE_DIM


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_seed(*tokens: object) -> int:
    raw = "|".join(str(token) for token in tokens).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:8], 16)


def load_json_records(path: Path) -> list[dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError(f"Expected a non-empty JSON list: {path}")
    return records


def conductivity_records(records: Iterable[dict]) -> list[dict]:
    output = []
    for record in records:
        value = record.get("conductivity")
        if not bool(record.get("conductivity_mask", True)):
            continue
        if value is None or not np.isfinite(float(value)) or float(value) <= 0:
            continue
        output.append(record)
    if not output:
        raise ValueError("No positive labelled conductivity records")
    return output


def _safe_float(value: float) -> float:
    value = float(value)
    return value if np.isfinite(value) else 0.0


@lru_cache(maxsize=None)
def molecule_features(smiles: str) -> np.ndarray:
    molecule = Chem.MolFromSmiles(str(smiles))
    if molecule is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    scalars = np.asarray(
        [
            Descriptors.MolWt(molecule) / 200.0,
            Crippen.MolLogP(molecule) / 5.0,
            rdMolDescriptors.CalcTPSA(molecule) / 150.0,
            Lipinski.NumHDonors(molecule) / 5.0,
            Lipinski.NumHAcceptors(molecule) / 10.0,
            Lipinski.NumRotatableBonds(molecule) / 10.0,
            rdMolDescriptors.CalcNumRings(molecule) / 5.0,
            rdMolDescriptors.CalcFractionCSP3(molecule),
            molecule.GetNumHeavyAtoms() / 30.0,
            sum(atom.GetFormalCharge() for atom in molecule.GetAtoms()) / 3.0,
        ],
        dtype=float,
    )
    counts = {element: 0 for element in ELEMENTS}
    for atom in molecule.GetAtoms():
        if atom.GetSymbol() in counts:
            counts[atom.GetSymbol()] += 1
    atom_count = max(1, molecule.GetNumAtoms())
    element_fractions = np.asarray(
        [counts[element] / atom_count for element in ELEMENTS],
        dtype=float,
    )
    fingerprint = np.zeros(FP_SIZE, dtype=float)
    generator = AllChem.GetMorganGenerator(radius=2, fpSize=FP_SIZE)
    DataStructs.ConvertToNumpyArray(
        generator.GetFingerprint(molecule),
        fingerprint,
    )
    features = np.concatenate([scalars, element_fractions, fingerprint])
    if len(features) != MOLECULE_FEATURE_DIM:
        raise AssertionError("Molecule feature dimension changed")
    return np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)


def normalized_component_weights(components: Sequence[dict]) -> np.ndarray:
    if not components:
        raise ValueError("Mixture component list is empty")
    weights = np.asarray(
        [_safe_float(component.get("molar_ratio", 1.0)) for component in components],
        dtype=float,
    )
    if np.any(weights < 0) or not np.isfinite(weights.sum()) or weights.sum() <= 0:
        raise ValueError("Invalid mixture molar ratios")
    return weights / weights.sum()


def aggregate_components(
    components: Sequence[dict],
    *,
    include_variance: bool,
) -> np.ndarray:
    """Molar-weighted, permutation-invariant component aggregation."""
    features = np.vstack(
        [molecule_features(str(component["smiles"])) for component in components]
    )
    weights = normalized_component_weights(components)
    mean = np.sum(weights[:, None] * features, axis=0)
    if not include_variance:
        return mean
    variance = np.sum(weights[:, None] * (features - mean) ** 2, axis=0)
    return np.concatenate([mean, variance])


def state_features(record: dict) -> np.ndarray:
    concentration = _safe_float(record["salt_molar_ratio"])
    if concentration <= 0:
        raise ValueError("Salt molar ratio must be positive")
    temperature_kelvin = _safe_float(record["temperature"]) + 273.15
    if temperature_kelvin <= 0:
        raise ValueError("Temperature must exceed absolute zero")
    solvent_weights = normalized_component_weights(record["solvents"])
    entropy = -float(
        np.sum(solvent_weights * np.log(np.maximum(solvent_weights, 1e-12)))
    )
    inverse_temperature = 1000.0 / temperature_kelvin
    log_concentration = math.log(concentration)
    return np.asarray(
        [
            len(record["solvents"]) / 5.0,
            entropy / 2.0,
            concentration,
            concentration**2,
            log_concentration,
            inverse_temperature,
            inverse_temperature * log_concentration,
            inverse_temperature * concentration,
            1e5 / temperature_kelvin**2,
        ],
        dtype=float,
    )


def mixture_features(records: Sequence[dict]) -> np.ndarray:
    rows = []
    for record in records:
        solvent = aggregate_components(
            record["solvents"],
            include_variance=True,
        )
        salt = aggregate_components(
            record["salts"],
            include_variance=False,
        )
        rows.append(np.concatenate([solvent, salt, state_features(record)]))
    matrix = np.asarray(rows, dtype=float)
    expected = CHEMISTRY_FEATURE_DIM + len(STATE_FEATURE_NAMES)
    if matrix.shape != (len(records), expected):
        raise AssertionError(f"Mixture feature shape changed: {matrix.shape}")
    return np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)


def mixture_feature_names() -> tuple[str, ...]:
    names = (
        *(f"solvent_mean_{name}" for name in MOLECULE_FEATURE_NAMES),
        *(f"solvent_variance_{name}" for name in MOLECULE_FEATURE_NAMES),
        *(f"salt_mean_{name}" for name in MOLECULE_FEATURE_NAMES),
        *STATE_FEATURE_NAMES,
    )
    if len(names) != CHEMISTRY_FEATURE_DIM + len(STATE_FEATURE_NAMES):
        raise AssertionError("Feature-name dimension changed")
    return tuple(names)


def formula_signature(record: dict) -> str:
    payload = []
    for kind in ("solvents", "salts"):
        components = sorted(
            record[kind],
            key=lambda item: (
                str(item["smiles"]),
                round(float(item.get("molar_ratio", 0.0)), 8),
            ),
        )
        payload.extend(
            {
                "kind": kind,
                "smiles": str(component["smiles"]),
                "molar_ratio": round(float(component.get("molar_ratio", 0.0)), 8),
            }
            for component in components
        )
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def salt_identity(record: dict) -> str:
    return "+".join(sorted(str(component["name"]) for component in record["salts"]))


def response_target(records: Sequence[dict]) -> np.ndarray:
    values = np.asarray([float(record["conductivity"]) for record in records])
    if np.any(values <= 0) or not np.isfinite(values).all():
        raise ValueError("Conductivity target must be positive and finite")
    return np.log10(values)


def fit_source_forest(
    x: np.ndarray,
    y: np.ndarray,
    *,
    seed: int,
    n_estimators: int,
    state_only: bool = False,
    chemistry_permutation: np.ndarray | None = None,
) -> RandomForestRegressor:
    matrix = np.asarray(x, dtype=float).copy()
    if chemistry_permutation is not None:
        permutation = np.asarray(chemistry_permutation, dtype=int)
        if sorted(permutation.tolist()) != list(range(len(matrix))):
            raise ValueError("Chemistry permutation is invalid")
        matrix[:, :CHEMISTRY_FEATURE_DIM] = matrix[
            permutation, :CHEMISTRY_FEATURE_DIM
        ]
    if state_only:
        matrix = matrix[:, CHEMISTRY_FEATURE_DIM:]
    model = RandomForestRegressor(
        n_estimators=int(n_estimators),
        min_samples_leaf=2,
        max_features=0.7,
        random_state=int(seed),
        n_jobs=-1,
    )
    model.fit(matrix, np.asarray(y, dtype=float))
    return model


def source_predict(
    model: RandomForestRegressor,
    x: np.ndarray,
    *,
    state_only: bool,
) -> np.ndarray:
    matrix = (
        np.asarray(x, dtype=float)[:, CHEMISTRY_FEATURE_DIM:]
        if state_only
        else np.asarray(x, dtype=float)
    )
    return np.asarray(model.predict(matrix), dtype=float)


def regression_metrics(y_log: np.ndarray, prediction_log: np.ndarray) -> dict[str, float]:
    y_log = np.asarray(y_log, dtype=float)
    prediction_log = np.asarray(prediction_log, dtype=float)
    y_raw = 10.0**y_log
    prediction_raw = 10.0**prediction_log
    rho = (
        float("nan")
        if np.std(y_log) <= 1e-15 or np.std(prediction_log) <= 1e-15
        else stats.spearmanr(y_log, prediction_log).statistic
    )
    return {
        "n": int(len(y_log)),
        "log_rmse": float(np.sqrt(mean_squared_error(y_log, prediction_log))),
        "log_mae": float(mean_absolute_error(y_log, prediction_log)),
        "log_r2": float(r2_score(y_log, prediction_log)),
        "raw_rmse": float(np.sqrt(mean_squared_error(y_raw, prediction_raw))),
        "raw_mae": float(mean_absolute_error(y_raw, prediction_raw)),
        "raw_r2": float(r2_score(y_raw, prediction_raw)),
        "spearman": float(rho),
    }


def select_one_row_per_formula(
    x: np.ndarray,
    formula_groups: Sequence[str],
) -> np.ndarray:
    """Select a representative row without using target outcomes."""
    z = StandardScaler().fit_transform(np.asarray(x, dtype=float))
    centre = np.median(z, axis=0)
    selected: dict[str, int] = {}
    for index, group in enumerate(map(str, formula_groups)):
        if group not in selected:
            selected[group] = index
            continue
        old = selected[group]
        if np.linalg.norm(z[index] - centre) < np.linalg.norm(z[old] - centre):
            selected[group] = index
    return np.asarray(
        [selected[group] for group in sorted(selected)],
        dtype=int,
    )


def maximin_anchors(
    x: np.ndarray,
    formula_groups: Sequence[str],
    *,
    budget: int,
    start_index: int,
) -> np.ndarray:
    """Coverage anchors with at most one row from each exact formulation."""
    x = np.asarray(x, dtype=float)
    candidates = select_one_row_per_formula(x, formula_groups)
    if budget < 1 or budget > len(candidates):
        raise ValueError("Anchor budget outside eligible formulation count")
    z = StandardScaler().fit_transform(x)
    selected = [int(candidates[int(start_index) % len(candidates)])]
    while len(selected) < budget:
        distance = np.min(
            ((z[candidates, None, :] - z[np.asarray(selected)][None, :, :]) ** 2).sum(
                axis=2
            ),
            axis=1,
        )
        distance[np.isin(candidates, selected)] = -np.inf
        best = np.flatnonzero(np.isclose(distance, np.nanmax(distance)))
        chosen = min(
            (int(candidates[index]) for index in best),
            key=lambda index: str(formula_groups[index]),
        )
        selected.append(chosen)
    return np.asarray(selected, dtype=int)


def nonanchor_test_indices(
    formula_groups: Sequence[str],
    anchors: Sequence[int],
) -> np.ndarray:
    groups = np.asarray(list(map(str, formula_groups)))
    anchor_groups = set(groups[np.asarray(anchors, dtype=int)])
    test = np.flatnonzero(~np.isin(groups, sorted(anchor_groups)))
    if not len(test):
        raise ValueError("No non-anchor formulations remain for scoring")
    if anchor_groups.intersection(groups[test]):
        raise AssertionError("Anchor formulation entered the test set")
    return test


@dataclass(frozen=True)
class ShrinkageAdapter:
    scaler: StandardScaler
    theta: np.ndarray
    alpha: float

    def predict(self, source_prediction: np.ndarray, state: np.ndarray) -> np.ndarray:
        raw = np.column_stack([source_prediction, state])
        design = np.column_stack(
            [np.ones(len(raw)), self.scaler.transform(raw)]
        )
        return np.asarray(source_prediction, dtype=float) + design @ self.theta


def fit_shrinkage_adapter(
    source_prediction: np.ndarray,
    state: np.ndarray,
    y_log: np.ndarray,
    *,
    alpha: float,
) -> ShrinkageAdapter:
    """Fit a residual correction with an explicit zero-correction prior."""
    source_prediction = np.asarray(source_prediction, dtype=float)
    state = np.asarray(state, dtype=float)
    y_log = np.asarray(y_log, dtype=float)
    raw = np.column_stack([source_prediction, state])
    scaler = StandardScaler().fit(raw)
    design = np.column_stack([np.ones(len(raw)), scaler.transform(raw)])
    residual = y_log - source_prediction
    penalty = float(alpha) * np.eye(design.shape[1])
    theta = np.linalg.solve(design.T @ design + penalty, design.T @ residual)
    return ShrinkageAdapter(scaler=scaler, theta=theta, alpha=float(alpha))
