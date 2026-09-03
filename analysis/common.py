"""Shared, deterministic utilities for the confirmatory analyses."""
from __future__ import annotations

import json
import math
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable, Sequence

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB = Path(os.environ.get("COLLECTIVE_DB", ROOT / "data" / "collective.sqlite")).resolve()
RESULTS = HERE / "results"
FIGURES = HERE / "figures"

# Atomic-number order makes composition vectors deterministic and supplies one
# simple periodic descriptor without an external featurization service.
ELEMENTS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn "
    "Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce "
    "Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn "
    "Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og"
).split()
ELEMENT_INDEX = {element: index for index, element in enumerate(ELEMENTS)}


def connect() -> sqlite3.Connection:
    if not DB.exists() or DB.stat().st_size == 0:
        raise FileNotFoundError(
            f"Missing data snapshot: {DB}. Run scripts/localdb/build_localdb.py first."
        )
    return sqlite3.connect(DB)


def key_to_dict(key: str) -> dict[str, float]:
    return {token.split(":", 1)[0]: float(token.split(":", 1)[1]) for token in key.split("|")}


def composition_features(keys: Sequence[str]) -> np.ndarray:
    """Element fractions plus compact distribution descriptors."""
    output = np.zeros((len(keys), len(ELEMENTS) + 8), dtype=float)
    for row_index, key in enumerate(keys):
        composition = key_to_dict(key)
        for element, fraction in composition.items():
            if element in ELEMENT_INDEX:
                output[row_index, ELEMENT_INDEX[element]] = fraction
        fractions = output[row_index, : len(ELEMENTS)]
        present = np.flatnonzero(fractions)
        atomic_numbers = present + 1
        weights = fractions[present]
        mean_z = float(np.sum(weights * atomic_numbers))
        output[row_index, len(ELEMENTS) :] = (
            len(present),
            mean_z,
            math.sqrt(float(np.sum(weights * (atomic_numbers - mean_z) ** 2))),
            float(atomic_numbers.min()),
            float(atomic_numbers.max()),
            float(weights.max()),
            -float(np.sum(weights * np.log(weights))),
            float(np.sum(weights**2)),
        )
    return output


def load_property(
    dataset: str,
    prop: str,
    *,
    valid: Callable[[pd.Series], pd.Series] | None = None,
    log10: bool = False,
) -> pd.DataFrame:
    with connect() as connection:
        frame = pd.read_sql(
            """SELECT source_row_id,material_raw,material_key,value,conditions_json,
                      source_reference,quality_flags
               FROM measurements WHERE dataset=? AND property=?""",
            connection,
            params=(dataset, prop),
        )
    frame = frame[frame["material_key"].notna()].copy()
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"])]
    if valid is not None:
        frame = frame[valid(frame["value"])].copy()
    if log10:
        frame = frame[frame["value"] > 0].copy()
        frame["value"] = np.log10(frame["value"])
    return frame


def aggregate_compositions(frame: pd.DataFrame) -> pd.DataFrame:
    """One target per canonical entity; median is robust to repeated reports."""
    grouped = (
        frame.groupby("material_key", as_index=False)
        .agg(value=("value", "median"), n_raw=("value", "size"), material_raw=("material_raw", "first"))
        .sort_values("material_key")
        .reset_index(drop=True)
    )
    return grouped


def load_obelix() -> pd.DataFrame:
    frame = load_property(
        "obelix-solid-electrolytes",
        "ionic_conductivity",
        valid=lambda value: value > 0,
        log10=True,
    )
    parsed = frame["conditions_json"].map(json.loads)
    frame["split"] = parsed.map(lambda item: item["official_split"])
    frame["source_group"] = parsed.map(lambda item: item["source_group"])
    train_keys = set(frame.loc[frame["split"] == "train", "material_key"])
    test_keys = set(frame.loc[frame["split"] == "test", "material_key"])
    canonical_overlap = train_keys & test_keys
    excluded_test_rows = int(
        ((frame["split"] == "test") & frame["material_key"].isin(canonical_overlap)).sum()
    )
    frame = frame[
        ~((frame["split"] == "test") & frame["material_key"].isin(canonical_overlap))
    ].reset_index(drop=True)
    # Canonicalization can identify equivalent formulas that the upstream
    # exact-string grouping kept separate.  Merge those connected components
    # before evaluation, while retaining the official train/test assignment.
    parent = np.arange(len(frame))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = int(parent[index])
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for column in ("source_group", "material_key"):
        for indices in frame.groupby(column).indices.values():
            indices = list(indices)
            for index in indices[1:]:
                union(int(indices[0]), int(index))
    roots = [find(index) for index in range(len(frame))]
    labels = {root: f"evaluation-group-{position:04d}" for position, root in enumerate(sorted(set(roots)))}
    frame["group"] = [labels[root] for root in roots]
    if (frame.groupby("group")["split"].nunique() > 1).any():
        raise AssertionError("Canonical OBELiX group crosses the official split")
    grouped = (
        frame.groupby("material_key", as_index=False)
        .agg(
            value=("value", "median"),
            n_raw=("value", "size"),
            material_raw=("material_raw", "first"),
            split=("split", "first"),
            group=("group", "first"),
            source_reference=("source_reference", "first"),
        )
        .sort_values("material_key")
        .reset_index(drop=True)
    )
    # A canonical composition must not straddle the official split or merged group.
    checks = frame.groupby("material_key").agg(split_n=("split", "nunique"), group_n=("group", "nunique"))
    if (checks[["split_n", "group_n"]] > 1).any().any():
        raise AssertionError("OBELiX canonical entity straddles an evaluation split/group")
    grouped.attrs["canonical_test_overlap_keys_excluded"] = len(canonical_overlap)
    grouped.attrs["canonical_test_overlap_rows_excluded"] = excluded_test_rows
    return grouped


def formula_dataset(dataset: str, prop: str) -> pd.DataFrame:
    validity: dict[tuple[str, str], Callable[[pd.Series], pd.Series]] = {
        ("estm-thermoelectric", "ZT"): lambda value: (value > 0) & (value <= 5),
        ("mpea-dataset-borg", "PROPERTY: YS (MPa)"): lambda value: (value > 0) & (value <= 10000),
        ("ocx24-open-catalyst-experiments-2024", "fe_h2"): lambda value: (value >= 0) & (value <= 100),
    }
    return aggregate_compositions(load_property(dataset, prop, valid=validity[(dataset, prop)]))


def ridge_model(alpha: float = 10.0):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def random_forest(seed: int = 0, n_estimators: int = 200):
    return RandomForestRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=-1,
    )


def extra_trees(seed: int = 0, n_estimators: int = 200):
    return ExtraTreesRegressor(
        n_estimators=n_estimators,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=-1,
    )


def sample_groups(groups: Sequence[str], target_n: int, rng: np.random.Generator) -> np.ndarray:
    """Select intact groups with a deterministic near-target greedy rule."""
    members: dict[str, list[int]] = defaultdict(list)
    for index, group in enumerate(groups):
        members[str(group)].append(index)
    order = list(members)
    rng.shuffle(order)
    selected: list[int] = []
    deferred: list[str] = []
    for group in order:
        candidate = members[group]
        if len(selected) + len(candidate) <= target_n:
            selected.extend(candidate)
        else:
            deferred.append(group)
    if len(selected) < int(0.8 * target_n) and deferred:
        best = min(deferred, key=lambda group: abs(target_n - len(selected) - len(members[group])))
        selected.extend(members[best])
    if len(selected) < 10:
        raise RuntimeError(f"Could only sample {len(selected)} grouped observations")
    return np.asarray(sorted(selected), dtype=int)


def metrics(y: np.ndarray, baseline: np.ndarray, augmented: np.ndarray) -> dict[str, float]:
    return {
        "base_r2": r2_score(y, baseline),
        "aug_r2": r2_score(y, augmented),
        "delta_r2": r2_score(y, augmented) - r2_score(y, baseline),
        "base_rmse": math.sqrt(mean_squared_error(y, baseline)),
        "aug_rmse": math.sqrt(mean_squared_error(y, augmented)),
        "delta_rmse": math.sqrt(mean_squared_error(y, baseline)) - math.sqrt(mean_squared_error(y, augmented)),
        "delta_mae": mean_absolute_error(y, baseline) - mean_absolute_error(y, augmented),
        "mse_improvement": mean_squared_error(y, baseline) - mean_squared_error(y, augmented),
    }


def holm_adjust(pvalues: Sequence[float]) -> np.ndarray:
    pvalues = np.asarray(pvalues, dtype=float)
    order = np.argsort(pvalues)
    adjusted = np.empty_like(pvalues)
    running = 0.0
    total = len(pvalues)
    for rank, index in enumerate(order):
        value = min(1.0, (total - rank) * pvalues[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def hierarchical_interval(
    predictions: pd.DataFrame,
    statistic: str,
    *,
    n_boot: int = 2000,
    seed: int = 20260713,
) -> tuple[float, float]:
    """Two-way cluster bootstrap over training repeats and held-out groups."""
    rng = np.random.default_rng(seed)
    repeat_codes, repeats = pd.factorize(predictions["repeat"], sort=True)
    group_codes, groups = pd.factorize(predictions["test_group"], sort=True)
    y = predictions["y"].to_numpy(float)
    baseline = predictions["baseline"].to_numpy(float)
    augmented = predictions["augmented"].to_numpy(float)
    values: list[float] = []
    for _ in range(n_boot):
        repeat_weight = np.bincount(
            rng.integers(0, len(repeats), size=len(repeats)), minlength=len(repeats)
        )
        group_weight = np.bincount(
            rng.integers(0, len(groups), size=len(groups)), minlength=len(groups)
        )
        weight = repeat_weight[repeat_codes] * group_weight[group_codes]
        keep = weight > 0
        weight = weight[keep].astype(float)
        yy, bb, aa = y[keep], baseline[keep], augmented[keep]
        if statistic == "delta_rmse":
            base_rmse = math.sqrt(np.average((yy - bb) ** 2, weights=weight))
            aug_rmse = math.sqrt(np.average((yy - aa) ** 2, weights=weight))
            values.append(base_rmse - aug_rmse)
        elif statistic == "delta_r2":
            center = np.average(yy, weights=weight)
            denominator = np.sum(weight * (yy - center) ** 2)
            base_r2 = 1 - np.sum(weight * (yy - bb) ** 2) / denominator
            aug_r2 = 1 - np.sum(weight * (yy - aa) ** 2) / denominator
            values.append(aug_r2 - base_r2)
        elif statistic == "delta_mae":
            values.append(
                np.average(np.abs(yy - bb), weights=weight)
                - np.average(np.abs(yy - aa), weights=weight)
            )
        else:
            raise ValueError(f"Unsupported hierarchical statistic: {statistic}")
    return tuple(np.percentile(values, [2.5, 97.5]))


def hc3_regression(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """OLS with HC3 standard errors for the intercept and slope."""
    design = np.column_stack([np.ones(len(x)), x])
    inv = np.linalg.inv(design.T @ design)
    beta = inv @ design.T @ y
    residual = y - design @ beta
    leverage = np.sum(design * (design @ inv), axis=1)
    scaled = residual / np.clip(1.0 - leverage, 1e-12, None)
    meat = design.T @ np.diag(scaled**2) @ design
    covariance = inv @ meat @ inv
    se = np.sqrt(np.diag(covariance))
    degrees = len(x) - 2
    t_value = beta[1] / se[1]
    p_value = 2 * stats.t.sf(abs(t_value), degrees)
    critical = stats.t.ppf(0.975, degrees)
    prediction = design @ beta
    r2 = 1 - np.sum((y - prediction) ** 2) / np.sum((y - np.mean(y)) ** 2)
    return {
        "intercept": beta[0],
        "slope": beta[1],
        "slope_se_hc3": se[1],
        "slope_ci_lo": beta[1] - critical * se[1],
        "slope_ci_hi": beta[1] + critical * se[1],
        "p_hc3": p_value,
        "r2": r2,
    }


def ensure_output_dirs() -> None:
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
