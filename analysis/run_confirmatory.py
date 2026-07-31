"""Run the confirmatory and explicitly labelled exploratory analyses.

The primary hypothesis is fixed before execution here:

* target: OBELiX log10 ionic conductivity;
* held-out evaluation: the official DOI/composition-disjoint test split;
* target training size: approximately 30, sampled as intact DOI/composition
  connected components from the official training split;
* source candidates: ESTM ZT, MPEA yield strength, and OCx24 H2 FE;
* primary learner/endpoint: ridge regression, reduction in held-out RMSE;
* inference: source-label permutation, Holm correction over three sources;
* uncertainty: two-way cluster bootstrap over training repeats and test groups.

All other transfer-matrix cells, learners, sample sizes, feature attributions,
and retrospective search simulations are sensitivity or exploratory analyses.
"""
from __future__ import annotations

import json
import hashlib
import importlib.metadata
import math
import sqlite3
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.Scaffolds import MurckoScaffold
from scipy import stats
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupShuffleSplit, KFold, cross_val_score

from common import (
    DB,
    ELEMENTS,
    FIGURES,
    RESULTS,
    aggregate_compositions,
    composition_features,
    connect,
    ensure_output_dirs,
    extra_trees,
    formula_dataset,
    hc3_regression,
    hierarchical_interval,
    holm_adjust,
    key_to_dict,
    load_obelix,
    load_property,
    metrics,
    random_forest,
    ridge_model,
    sample_groups,
)

RDLogger.DisableLog("rdApp.*")
warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")
RANDOM_SEED = 20260713
PRIMARY_REPEATS = 60
PRIMARY_PERMUTATIONS = 99
TARGET_N = 30

SOURCE_SPECS = {
    "Thermoelectric ZT": ("estm-thermoelectric", "ZT"),
    "Alloy yield strength": ("mpea-dataset-borg", "PROPERTY: YS (MPa)"),
    "CO2R H2 Faradaic efficiency": ("ocx24-open-catalyst-experiments-2024", "fe_h2"),
}
SHORT_SOURCE = {
    "Thermoelectric ZT": "TE ZT",
    "Alloy yield strength": "MPEA YS",
    "CO2R H2 Faradaic efficiency": "OCx H2 FE",
}


def prepare_formula_sources() -> tuple[dict[str, dict[str, object]], pd.DataFrame]:
    target = load_obelix()
    target["X_index"] = np.arange(len(target))
    target_x = composition_features(target["material_key"].tolist())
    sources: dict[str, dict[str, object]] = {}
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    for label, (dataset, prop) in SOURCE_SPECS.items():
        frame = formula_dataset(dataset, prop)
        x = composition_features(frame["material_key"].tolist())
        y = frame["value"].to_numpy(float)
        model = random_forest(RANDOM_SEED, 240).fit(x, y)
        scores = cross_val_score(random_forest(RANDOM_SEED, 160), x, y, cv=cv, scoring="r2", n_jobs=1)
        overlap = set(frame["material_key"]) & set(target["material_key"])
        sources[label] = {
            "frame": frame,
            "X": x,
            "y": y,
            "model": model,
            "target_feature": model.predict(target_x),
            "source_cv_r2_mean": float(scores.mean()),
            "source_cv_r2_sd": float(scores.std(ddof=1)),
            "target_overlap": len(overlap),
        }
    target.attrs["X"] = target_x
    return sources, target


def primary_training_samples(target: pd.DataFrame) -> list[np.ndarray]:
    train = target[target["split"] == "train"].reset_index()
    samples = []
    for repeat in range(PRIMARY_REPEATS):
        rng = np.random.default_rng(RANDOM_SEED + repeat)
        local = sample_groups(train["group"].tolist(), TARGET_N, rng)
        samples.append(train.loc[local, "index"].to_numpy(int))
    return samples


def fit_target_pair(
    model,
    x: np.ndarray,
    y: np.ndarray,
    feature: np.ndarray,
    train_index: np.ndarray,
    test_index: np.ndarray,
):
    baseline = clone(model).fit(x[train_index], y[train_index])
    augmented = clone(model).fit(
        np.column_stack([x[train_index], feature[train_index]]), y[train_index]
    )
    return (
        baseline.predict(x[test_index]),
        augmented.predict(np.column_stack([x[test_index], feature[test_index]])),
    )


def run_primary_transfer(sources: dict[str, dict[str, object]], target: pd.DataFrame):
    x = target.attrs["X"]
    y = target["value"].to_numpy(float)
    test_index = target.index[target["split"] == "test"].to_numpy(int)
    samples = primary_training_samples(target)
    learners = {
        "Ridge (primary)": ridge_model(10.0),
        "Random forest (sensitivity)": random_forest(RANDOM_SEED, 180),
        "Extra trees (sensitivity)": extra_trees(RANDOM_SEED, 180),
    }
    prediction_rows = []
    repeat_rows = []
    for learner_label, learner in learners.items():
        for source_label, source in sources.items():
            feature = np.asarray(source["target_feature"])
            for repeat, train_index in enumerate(samples):
                baseline, augmented = fit_target_pair(learner, x, y, feature, train_index, test_index)
                result = metrics(y[test_index], baseline, augmented)
                repeat_rows.append(
                    {
                        "learner": learner_label,
                        "source": source_label,
                        "repeat": repeat,
                        "train_n": len(train_index),
                        **result,
                    }
                )
                for position, index in enumerate(test_index):
                    prediction_rows.append(
                        {
                            "learner": learner_label,
                            "source": source_label,
                            "repeat": repeat,
                            "test_group": target.at[index, "group"],
                            "material_key": target.at[index, "material_key"],
                            "y": y[index],
                            "baseline": baseline[position],
                            "augmented": augmented[position],
                        }
                    )
    repeats = pd.DataFrame(repeat_rows)
    predictions = pd.DataFrame(prediction_rows)

    # Source-label permutation is the primary null.  It preserves the source
    # feature map and model class while destroying property semantics.
    null_rows = []
    rng = np.random.default_rng(RANDOM_SEED)
    for source_label, source in sources.items():
        source_x = np.asarray(source["X"])
        source_y = np.asarray(source["y"])
        for permutation in range(PRIMARY_PERMUTATIONS):
            permuted_y = rng.permutation(source_y)
            placebo_model = random_forest(RANDOM_SEED + permutation + 1, 100).fit(source_x, permuted_y)
            feature = placebo_model.predict(x)
            improvements = []
            for train_index in samples:
                baseline, augmented = fit_target_pair(
                    ridge_model(10.0), x, y, feature, train_index, test_index
                )
                improvements.append(metrics(y[test_index], baseline, augmented)["mse_improvement"])
            null_rows.append(
                {
                    "source": source_label,
                    "permutation": permutation,
                    "mean_mse_improvement": float(np.mean(improvements)),
                }
            )
    nulls = pd.DataFrame(null_rows)

    summary_rows = []
    for (learner, source_label), group in repeats.groupby(["learner", "source"], sort=False):
        prediction_group = predictions[(predictions["learner"] == learner) & (predictions["source"] == source_label)]
        row = {
            "learner": learner,
            "source": source_label,
            "repeats": group["repeat"].nunique(),
            "train_n_median": float(group["train_n"].median()),
            "train_n_min": int(group["train_n"].min()),
            "train_n_max": int(group["train_n"].max()),
            "test_n": len(test_index),
            "test_groups": int(target.loc[test_index, "group"].nunique()),
            "source_n": len(sources[source_label]["y"]),
            "source_cv_r2_mean": sources[source_label]["source_cv_r2_mean"],
            "source_cv_r2_sd": sources[source_label]["source_cv_r2_sd"],
            "source_target_exact_overlap": sources[source_label]["target_overlap"],
            "obelix_canonical_test_overlap_keys_excluded": target.attrs.get("canonical_test_overlap_keys_excluded", 0),
            "obelix_canonical_test_overlap_rows_excluded": target.attrs.get("canonical_test_overlap_rows_excluded", 0),
        }
        for metric in ["base_r2", "aug_r2", "delta_r2", "delta_rmse", "delta_mae", "mse_improvement"]:
            row[f"{metric}_mean"] = float(group[metric].mean())
        row["delta_r2_ci_lo"], row["delta_r2_ci_hi"] = hierarchical_interval(
            prediction_group, "delta_r2", seed=RANDOM_SEED
        )
        row["delta_rmse_ci_lo"], row["delta_rmse_ci_hi"] = hierarchical_interval(
            prediction_group, "delta_rmse", seed=RANDOM_SEED + 1
        )
        if learner == "Ridge (primary)":
            observed = group["mse_improvement"].mean()
            null_values = nulls.loc[nulls["source"] == source_label, "mean_mse_improvement"].to_numpy()
            row["permutation_p_raw"] = (1 + np.sum(null_values >= observed)) / (len(null_values) + 1)
        else:
            row["permutation_p_raw"] = np.nan
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows)
    primary_mask = summary["learner"] == "Ridge (primary)"
    summary.loc[primary_mask, "permutation_p_holm"] = holm_adjust(
        summary.loc[primary_mask, "permutation_p_raw"].to_numpy()
    )
    summary.loc[~primary_mask, "permutation_p_holm"] = np.nan

    repeats.to_csv(RESULTS / "primary_transfer_repeats.csv", index=False)
    predictions.to_csv(RESULTS / "primary_transfer_predictions.csv", index=False)
    nulls.to_csv(RESULTS / "primary_transfer_permutation_null.csv", index=False)
    summary.to_csv(RESULTS / "primary_transfer_summary.csv", index=False)
    return summary, repeats, predictions, samples


def run_nonchalcogenide_sensitivity(sources, target, samples):
    target = target.copy()
    target["has_chalcogen"] = target["material_key"].map(
        lambda key: bool({"S", "Se", "Te"} & set(key_to_dict(key)))
    )
    subset = target[~target["has_chalcogen"]].reset_index(drop=True)
    x = composition_features(subset["material_key"].tolist())
    y = subset["value"].to_numpy(float)
    train_pool = subset[subset["split"] == "train"].reset_index()
    test_index = subset.index[subset["split"] == "test"].to_numpy(int)
    rows = []
    for source_label, source in sources.items():
        feature = source["model"].predict(x)
        for repeat in range(PRIMARY_REPEATS):
            local = sample_groups(
                train_pool["group"].tolist(), TARGET_N, np.random.default_rng(RANDOM_SEED + repeat)
            )
            train_index = train_pool.loc[local, "index"].to_numpy(int)
            baseline, augmented = fit_target_pair(
                ridge_model(10.0), x, y, feature, train_index, test_index
            )
            rows.append(
                {
                    "source": source_label,
                    "repeat": repeat,
                    "train_n": len(train_index),
                    "test_n": len(test_index),
                    **metrics(y[test_index], baseline, augmented),
                }
            )
    result = pd.DataFrame(rows)
    result.to_csv(RESULTS / "nonchalcogenide_sensitivity.csv", index=False)
    summary = (
        result.groupby("source", as_index=False)
        .agg(
            repeats=("repeat", "size"),
            train_n_median=("train_n", "median"),
            test_n=("test_n", "first"),
            delta_r2_mean=("delta_r2", "mean"),
            delta_r2_lo=("delta_r2", lambda values: np.percentile(values, 2.5)),
            delta_r2_hi=("delta_r2", lambda values: np.percentile(values, 97.5)),
            delta_rmse_mean=("delta_rmse", "mean"),
        )
    )
    summary.to_csv(RESULTS / "nonchalcogenide_sensitivity_summary.csv", index=False)
    return result


def run_exploratory_matrix(sources, target):
    datasets = {label: formula_dataset(*spec) for label, spec in SOURCE_SPECS.items()}
    datasets["Solid-electrolyte conductivity"] = target.copy()
    source_models = {label: source["model"] for label, source in sources.items()}
    source_models["Solid-electrolyte conductivity"] = random_forest(RANDOM_SEED, 240).fit(
        target.attrs["X"], target["value"].to_numpy(float)
    )
    rows = []
    for target_label, target_frame in datasets.items():
        x = composition_features(target_frame["material_key"].tolist())
        y = target_frame["value"].to_numpy(float)
        for source_label, source_model in source_models.items():
            if source_label == target_label:
                continue
            feature = source_model.predict(x)
            for repeat in range(30):
                rng = np.random.default_rng(RANDOM_SEED + repeat)
                if target_label == "Solid-electrolyte conductivity":
                    train_pool = target_frame[target_frame["split"] == "train"].reset_index()
                    local = sample_groups(train_pool["group"].tolist(), TARGET_N, rng)
                    train_index = train_pool.loc[local, "index"].to_numpy(int)
                    test_index = target_frame.index[target_frame["split"] == "test"].to_numpy(int)
                else:
                    train_index = np.sort(rng.choice(len(y), size=TARGET_N, replace=False))
                    test_index = np.setdiff1d(np.arange(len(y)), train_index)
                baseline, augmented = fit_target_pair(
                    ridge_model(10.0), x, y, feature, train_index, test_index
                )
                rows.append(
                    {
                        "target": target_label,
                        "source": source_label,
                        "repeat": repeat,
                        "train_n": len(train_index),
                        "test_n": len(test_index),
                        **metrics(y[test_index], baseline, augmented),
                    }
                )
    raw = pd.DataFrame(rows)
    raw["relative_rmse_improvement"] = raw["delta_rmse"] / raw["base_rmse"]
    summary = (
        raw.groupby(["target", "source"], as_index=False)
        .agg(
            delta_r2_mean=("delta_r2", "mean"),
            delta_r2_lo=("delta_r2", lambda values: np.percentile(values, 2.5)),
            delta_r2_hi=("delta_r2", lambda values: np.percentile(values, 97.5)),
            delta_rmse_mean=("delta_rmse", "mean"),
            relative_rmse_improvement_median=("relative_rmse_improvement", "median"),
            relative_rmse_improvement_q25=("relative_rmse_improvement", lambda values: np.percentile(values, 25)),
            relative_rmse_improvement_q75=("relative_rmse_improvement", lambda values: np.percentile(values, 75)),
            fraction_positive=("relative_rmse_improvement", lambda values: np.mean(values > 0)),
        )
    )
    raw.to_csv(RESULTS / "exploratory_transfer_matrix_repeats.csv", index=False)
    summary.to_csv(RESULTS / "exploratory_transfer_matrix.csv", index=False)
    return summary


def morgan_features(smiles: list[str]) -> np.ndarray:
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)
    output = np.zeros((len(smiles), 1024), dtype=np.float32)
    for index, value in enumerate(smiles):
        mol = Chem.MolFromSmiles(value)
        if mol is None:
            raise ValueError(f"Invalid canonical SMILES: {value}")
        fingerprint = generator.GetFingerprint(mol)
        DataStructs.ConvertToNumpyArray(fingerprint, output[index])
    return output


def scaffold(smiles: str) -> str:
    value = MurckoScaffold.MurckoScaffoldSmilesFromSmiles(smiles)
    return value or f"acyclic:{smiles}"


def run_organic_control():
    source = aggregate_compositions(load_property("freesolv", "dG_hydration"))
    target = aggregate_compositions(load_property("aqsoldb", "logS"))
    overlap = set(source["material_key"]) & set(target["material_key"])
    target = target[~target["material_key"].isin(overlap)].reset_index(drop=True)
    source_x = morgan_features(source["material_key"].tolist())
    target_x = morgan_features(target["material_key"].tolist())
    source_y = source["value"].to_numpy(float)
    target_y = target["value"].to_numpy(float)
    source_model = random_forest(RANDOM_SEED, 300).fit(source_x, source_y)
    feature = source_model.predict(target_x)
    target["scaffold"] = target["material_key"].map(scaffold)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_SEED)
    train_pool_index, test_index = next(
        splitter.split(target_x, target_y, groups=target["scaffold"].to_numpy())
    )
    train_pool = target.iloc[train_pool_index].reset_index()
    rows = []
    prediction_rows = []
    for repeat in range(40):
        local = sample_groups(
            train_pool["scaffold"].tolist(), 60, np.random.default_rng(RANDOM_SEED + repeat)
        )
        train_index = train_pool.loc[local, "index"].to_numpy(int)
        learner = extra_trees(RANDOM_SEED + repeat, 160)
        baseline, augmented = fit_target_pair(
            learner, target_x, target_y, feature, train_index, test_index
        )
        rows.append(
            {
                "repeat": repeat,
                "train_n": len(train_index),
                "test_n": len(test_index),
                **metrics(target_y[test_index], baseline, augmented),
            }
        )
        for position, index in enumerate(test_index):
            prediction_rows.append(
                {
                    "repeat": repeat,
                    "test_group": target.at[index, "scaffold"],
                    "material_key": target.at[index, "material_key"],
                    "y": target_y[index],
                    "baseline": baseline[position],
                    "augmented": augmented[position],
                }
            )
    repeats = pd.DataFrame(rows)
    predictions = pd.DataFrame(prediction_rows)
    delta_r2_ci = hierarchical_interval(predictions, "delta_r2", seed=RANDOM_SEED)
    delta_rmse_ci = hierarchical_interval(predictions, "delta_rmse", seed=RANDOM_SEED + 1)
    summary = pd.DataFrame(
        [
            {
                "source": "FreeSolv dG_hydration",
                "target": "AqSolDB logS",
                "feature": "Morgan radius-2, 1024-bit",
                "split": "fixed scaffold-disjoint test",
                "exact_molecule_overlap_removed": len(overlap),
                "source_n": len(source),
                "target_n_after_overlap_removal": len(target),
                "train_n_median": repeats["train_n"].median(),
                "test_n": len(test_index),
                "repeats": len(repeats),
                "delta_r2_mean": repeats["delta_r2"].mean(),
                "delta_r2_ci_lo": delta_r2_ci[0],
                "delta_r2_ci_hi": delta_r2_ci[1],
                "delta_rmse_mean": repeats["delta_rmse"].mean(),
                "delta_rmse_ci_lo": delta_rmse_ci[0],
                "delta_rmse_ci_hi": delta_rmse_ci[1],
                "equivalent_within_abs_delta_r2_0.05": bool(delta_r2_ci[0] > -0.05 and delta_r2_ci[1] < 0.05),
            }
        ]
    )
    repeats.to_csv(RESULTS / "organic_control_repeats.csv", index=False)
    predictions.to_csv(RESULTS / "organic_control_predictions.csv", index=False)
    summary.to_csv(RESULTS / "organic_control_summary.csv", index=False)
    return summary


def family_from_key(key: str) -> str:
    composition = key_to_dict(key)
    major = sorted(element for element, fraction in composition.items() if fraction >= 0.15)
    return "-".join(major) if major else "other"


def run_compensation():
    with connect() as connection:
        data = pd.read_sql(
            """SELECT material_raw,material_key,value,conditions_json,source_reference
               FROM measurements
               WHERE dataset='estm-thermoelectric'
                 AND property='electrical_conductivity(S/m)' AND value>0
                 AND material_key IS NOT NULL""",
            connection,
        )
    data["temperature"] = data["conditions_json"].map(lambda value: json.loads(value)["temperature"])
    data["sample_key"] = data["material_key"] + "@@" + data["source_reference"].fillna("")
    arrhenius = []
    kb = 8.617333262e-5
    for sample_key, group in data.groupby("sample_key"):
        group = group.groupby("temperature", as_index=False).agg(
            value=("value", "median"), material_key=("material_key", "first"),
            material_raw=("material_raw", "first"), source_reference=("source_reference", "first")
        )
        if len(group) < 4 or group["temperature"].max() - group["temperature"].min() < 100:
            continue
        x = 1 / group["temperature"].to_numpy(float)
        y = np.log(group["value"].to_numpy(float))
        slope, intercept = np.polyfit(x, y, 1)
        fitted = intercept + slope * x
        r2 = 1 - np.sum((y - fitted) ** 2) / np.sum((y - y.mean()) ** 2)
        arrhenius.append(
            {
                "sample_key": sample_key,
                "material_key": group["material_key"].iloc[0],
                "material_raw": group["material_raw"].iloc[0],
                "source_reference": group["source_reference"].iloc[0],
                "n_temperature": len(group),
                "temperature_min_K": group["temperature"].min(),
                "temperature_max_K": group["temperature"].max(),
                "temperature_harmonic_K": len(group) / np.sum(1 / group["temperature"]),
                "Ea_eV": -slope * kb,
                "lnA": intercept,
                "arrhenius_r2": r2,
                "family": family_from_key(group["material_key"].iloc[0]),
            }
        )
    all_fits = pd.DataFrame(arrhenius)
    all_fits.to_csv(RESULTS / "compensation_all_arrhenius_fits.csv", index=False)
    sensitivity_rows = []
    selected_by_cutoff = {}
    for cutoff in (0.80, 0.90, 0.95):
        selected = all_fits[(all_fits["Ea_eV"] > 0) & (all_fits["Ea_eV"] < 2) & (all_fits["arrhenius_r2"] >= cutoff)].copy()
        selected_by_cutoff[cutoff] = selected
        result = hc3_regression(selected["Ea_eV"].to_numpy(), selected["lnA"].to_numpy())
        spearman = stats.spearmanr(selected["Ea_eV"], selected["lnA"])
        t_iso = 1 / (kb * result["slope"]) if result["slope"] > 0 else np.nan
        sensitivity_rows.append(
            {
                "arrhenius_r2_cutoff": cutoff,
                "n": len(selected),
                **result,
                "spearman_rho": spearman.statistic,
                "spearman_p": spearman.pvalue,
                "T_iso_K": t_iso,
                "temperature_harmonic_median_K": selected["temperature_harmonic_K"].median(),
                "temperature_min_K": selected["temperature_min_K"].min(),
                "temperature_max_K": selected["temperature_max_K"].max(),
            }
        )
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(RESULTS / "compensation_pooled_sensitivity.csv", index=False)
    selected = selected_by_cutoff[0.90]
    selected.to_csv(RESULTS / "compensation_selected_arrhenius_fits.csv", index=False)
    family_rows = []
    for family, group in selected.groupby("family"):
        if len(group) < 8:
            continue
        result = hc3_regression(group["Ea_eV"].to_numpy(), group["lnA"].to_numpy())
        t_iso = 1 / (kb * result["slope"]) if result["slope"] > 0 else np.nan
        family_rows.append(
            {
                "family": family,
                "n": len(group),
                **result,
                "T_iso_K": t_iso,
                "temperature_harmonic_median_K": group["temperature_harmonic_K"].median(),
                "temperature_min_K": group["temperature_min_K"].min(),
                "temperature_max_K": group["temperature_max_K"].max(),
                "krug_inside_observed_temperature_range": bool(
                    np.isfinite(t_iso)
                    and group["temperature_min_K"].min() <= t_iso <= group["temperature_max_K"].max()
                ),
            }
        )
    families = pd.DataFrame(family_rows)
    if not families.empty:
        families["p_holm"] = holm_adjust(families["p_hc3"].to_numpy())
        families = families.sort_values("p_holm")
    families.to_csv(RESULTS / "compensation_family_exploratory.csv", index=False)
    return selected, sensitivity, families


def paired_signflip_p(improvements: np.ndarray, seed: int = RANDOM_SEED, n_perm: int = 20000) -> float:
    rng = np.random.default_rng(seed)
    observed = improvements.mean()
    null = np.empty(n_perm)
    for index in range(n_perm):
        null[index] = np.mean(improvements * rng.choice([-1, 1], size=len(improvements)))
    return float((1 + np.sum(null >= observed)) / (n_perm + 1))


def run_search_control(sources, target):
    x = target.attrs["X"]
    y = target["value"].to_numpy(float)
    prior = np.asarray(sources["Thermoelectric ZT"]["target_feature"])
    feature_sets = {"baseline": x, "thermoelectric_prior": np.column_stack([x, prior])}
    threshold = np.percentile(y, 95)
    budget, initial = 40, 5

    def campaign(features: np.ndarray, seed: int):
        rng = np.random.default_rng(seed)
        labelled = list(rng.choice(len(y), size=initial, replace=False))
        pool = [index for index in range(len(y)) if index not in labelled]
        trajectory = [float(np.max(y[labelled]))]
        for step in range(budget):
            model = ExtraTreesRegressor(
                n_estimators=80,
                min_samples_leaf=2,
                max_features=0.7,
                random_state=seed * 100 + step,
                n_jobs=-1,
            ).fit(features[labelled], y[labelled])
            tree_predictions = np.asarray([tree.predict(features[pool]) for tree in model.estimators_])
            acquisition = tree_predictions.mean(axis=0) + tree_predictions.std(axis=0)
            chosen = pool[int(np.argmax(acquisition))]
            labelled.append(chosen)
            pool.remove(chosen)
            trajectory.append(float(np.max(y[labelled])))
        return trajectory

    trajectories = []
    reaches = []
    for seed in range(50):
        for strategy, features in feature_sets.items():
            trajectory = campaign(features, seed)
            reach = next((index for index, value in enumerate(trajectory) if value >= threshold), budget + 1)
            reaches.append({"seed": seed, "strategy": strategy, "experiments_to_top5": reach})
            trajectories.extend(
                {"seed": seed, "strategy": strategy, "experiment": index, "best_log10_sigma": value}
                for index, value in enumerate(trajectory)
            )
    trajectories = pd.DataFrame(trajectories)
    reaches = pd.DataFrame(reaches)
    paired = reaches.pivot(index="seed", columns="strategy", values="experiments_to_top5")
    improvement = (paired["baseline"] - paired["thermoelectric_prior"]).to_numpy(float)
    rng = np.random.default_rng(RANDOM_SEED)
    boot = np.asarray([rng.choice(improvement, size=len(improvement), replace=True).mean() for _ in range(10000)])
    summary = pd.DataFrame(
        [
            {
                "seeds": len(paired),
                "threshold_log10_sigma": threshold,
                "baseline_mean_experiments": paired["baseline"].mean(),
                "prior_mean_experiments": paired["thermoelectric_prior"].mean(),
                "paired_mean_improvement_experiments": improvement.mean(),
                "paired_improvement_ci_lo": np.percentile(boot, 2.5),
                "paired_improvement_ci_hi": np.percentile(boot, 97.5),
                "paired_signflip_p_one_sided": paired_signflip_p(improvement),
            }
        ]
    )
    trajectories.to_csv(RESULTS / "search_control_trajectories.csv", index=False)
    reaches.to_csv(RESULTS / "search_control_reach.csv", index=False)
    summary.to_csv(RESULTS / "search_control_summary.csv", index=False)
    return trajectories, summary


def make_figures(primary, matrix, organic, compensation, trajectories, search_summary):
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })
    colors = {"TE ZT": "#1769aa", "MPEA YS": "#d28e00", "OCx H2 FE": "#7a7a7a"}

    figure, axes = plt.subplots(2, 2, figsize=(10.2, 8.0))
    ax = axes[0, 0]
    ax.scatter(compensation["Ea_eV"], compensation["lnA"], s=18, alpha=0.65, color="#1769aa", edgecolor="none")
    pooled = hc3_regression(compensation["Ea_eV"].to_numpy(), compensation["lnA"].to_numpy())
    grid = np.linspace(compensation["Ea_eV"].min(), compensation["Ea_eV"].max(), 100)
    ax.plot(grid, pooled["intercept"] + pooled["slope"] * grid, color="#333333", lw=1.5)
    ax.set(title="A  ESTM Arrhenius intercept versus activation energy", xlabel="Activation energy, Ea (eV)", ylabel="ln A")
    ax.text(0.03, 0.97, f"n={len(compensation)}; R²={pooled['r2']:.03f}", transform=ax.transAxes, va="top")

    ax = axes[0, 1]
    source_order = list(SOURCE_SPECS)
    learner_style = {
        "Ridge (primary)": ("o", "#222222", -0.20, "ridge; designated primary"),
        "Random forest (sensitivity)": ("s", "#1769aa", 0.00, "random forest"),
        "Extra trees (sensitivity)": ("^", "#d28e00", 0.20, "extra trees"),
    }
    for learner, (marker, color, offset, legend) in learner_style.items():
        subset = primary[primary["learner"] == learner].set_index("source").loc[source_order]
        positions = np.arange(len(source_order)) + offset
        ax.errorbar(
            subset["delta_r2_mean"], positions,
            xerr=np.vstack([
                subset["delta_r2_mean"] - subset["delta_r2_ci_lo"],
                subset["delta_r2_ci_hi"] - subset["delta_r2_mean"],
            ]),
            fmt=marker, color=color, capsize=2.5, ms=5, label=legend,
        )
    ax.axvline(0, color="#555555", lw=1, ls="--")
    ax.set_yticks(range(len(source_order)), [SHORT_SOURCE[value] for value in source_order])
    ax.set(title="B  OBELiX official-test transfer estimates", xlabel="Change in held-out R² (two-way bootstrap 95% CI)")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")

    ax = axes[1, 0]
    labels = list(SOURCE_SPECS) + ["Solid-electrolyte conductivity"]
    pivot = matrix.pivot(index="target", columns="source", values="relative_rmse_improvement_median").reindex(index=labels, columns=labels) * 100
    image = ax.imshow(pivot.to_numpy(), cmap="RdBu_r", vmin=-3, vmax=3)
    short_labels = [SHORT_SOURCE.get(label, "OBELiX σ") for label in labels]
    ax.set_xticks(range(len(labels)), short_labels, rotation=35, ha="right")
    ax.set_yticks(range(len(labels)), short_labels)
    ax.set_xlabel("Source property")
    ax.set_ylabel("Target property")
    ax.set_title("C  Exploratory four-domain transfer matrix")
    for i in range(len(labels)):
        for j in range(len(labels)):
            value = pivot.iloc[i, j]
            if np.isfinite(value):
                ax.text(j, i, f"{value:+.1f}%", ha="center", va="center", fontsize=8,
                        color="white" if abs(value) > 1.7 else "#222222")
    figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="median relative RMSE improvement")

    ax = axes[1, 1]
    control_values = [organic.iloc[0]["delta_r2_mean"], search_summary.iloc[0]["paired_mean_improvement_experiments"]]
    control_lows = [organic.iloc[0]["delta_r2_ci_lo"], search_summary.iloc[0]["paired_improvement_ci_lo"]]
    control_highs = [organic.iloc[0]["delta_r2_ci_hi"], search_summary.iloc[0]["paired_improvement_ci_hi"]]
    # Separate units on two small inset-style axes avoids a misleading common scale.
    ax.axis("off")
    organic_ax = ax.inset_axes([0.04, 0.10, 0.42, 0.78])
    organic_ax.errorbar(control_values[0], 0, xerr=[[control_values[0]-control_lows[0]], [control_highs[0]-control_values[0]]],
                        fmt="o", color="#1769aa", capsize=3)
    organic_ax.axvline(0, color="#555555", ls="--", lw=1)
    organic_ax.axvspan(-0.05, 0.05, color="#1769aa", alpha=0.08)
    organic_ax.axvline(-0.05, color="#1769aa", ls=":", lw=0.8)
    organic_ax.axvline(0.05, color="#1769aa", ls=":", lw=0.8)
    organic_ax.set_xlim(-0.055, 0.055)
    organic_ax.set_yticks([])
    organic_ax.set_xlabel("Organic ΔR² (±0.05 band)")
    organic_ax.set_title("FreeSolv → AqSolDB", fontsize=9)
    search_ax = ax.inset_axes([0.55, 0.10, 0.42, 0.78])
    search_ax.errorbar(control_values[1], 0, xerr=[[control_values[1]-control_lows[1]], [control_highs[1]-control_values[1]]],
                       fmt="o", color="#d28e00", capsize=3)
    search_ax.axvline(0, color="#555555", ls="--", lw=1)
    search_ax.set_yticks([])
    search_ax.set_xlabel("Experiments saved")
    search_ax.set_title("Retrospective RF-UCB", fontsize=9)
    ax.set_title("D  Small-effect and downstream controls", loc="left", pad=2)

    figure.tight_layout()
    figure.savefig(FIGURES / "main_confirmatory.png", dpi=300, bbox_inches="tight")
    figure.savefig(FIGURES / "main_confirmatory.pdf", bbox_inches="tight")
    plt.close(figure)

    figure, ax = plt.subplots(figsize=(6.4, 4.2))
    summary = trajectories.groupby(["strategy", "experiment"])["best_log10_sigma"].agg(["mean", "sem"]).reset_index()
    for strategy, color, label in [
        ("baseline", "#666666", "composition baseline"),
        ("thermoelectric_prior", "#1769aa", "+ thermoelectric source feature"),
    ]:
        group = summary[summary["strategy"] == strategy]
        ax.plot(group["experiment"], group["mean"], color=color, label=label)
        ax.fill_between(group["experiment"], group["mean"] - 1.96 * group["sem"], group["mean"] + 1.96 * group["sem"], color=color, alpha=0.15)
    ax.axhline(search_summary.iloc[0]["threshold_log10_sigma"], color="#b33a3a", ls="--", lw=1, label="top-5% threshold")
    ax.set(title="Retrospective OBELiX pool-based search", xlabel="Acquired compositions", ylabel="Best observed log10 conductivity (S/cm)")
    ax.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(FIGURES / "search_control.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def write_manifest():
    files = sorted(path.name for path in RESULTS.glob("*.csv"))
    digest = hashlib.sha256()
    with DB.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    with sqlite3.connect(DB) as connection:
        measurement_count = connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
        property_count = connection.execute("SELECT COUNT(DISTINCT property) FROM measurements").fetchone()[0]
        entity_count = connection.execute("SELECT COUNT(DISTINCT material_key) FROM measurements").fetchone()[0]
        source_lock_sha256 = connection.execute(
            "SELECT value FROM build_metadata WHERE key='source_lock_sha256'"
        ).fetchone()[0]
        source_commits = dict(connection.execute("SELECT id,source_commit FROM datasets ORDER BY id"))
    manifest = {
        "analysis_date": "2026-07-13",
        "database": "data/collective.sqlite",
        "database_schema_version": "2",
        "database_sha256": digest.hexdigest(),
        "source_lock_sha256": source_lock_sha256,
        "measurements": measurement_count,
        "distinct_properties": property_count,
        "distinct_canonical_entities": entity_count,
        "source_commits": source_commits,
        "packages": {
            package: importlib.metadata.version(package)
            for package in ["numpy", "pandas", "scipy", "scikit-learn", "matplotlib", "rdkit"]
        },
        "random_seed": RANDOM_SEED,
        "primary_repeats": PRIMARY_REPEATS,
        "primary_permutations": PRIMARY_PERMUTATIONS,
        "primary_target_n": TARGET_N,
        "result_files": files,
    }
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main():
    ensure_output_dirs()
    sources, target = prepare_formula_sources()
    primary, _, _, samples = run_primary_transfer(sources, target)
    nonchalcogenide = run_nonchalcogenide_sensitivity(sources, target, samples)
    matrix = run_exploratory_matrix(sources, target)
    organic = run_organic_control()
    compensation, compensation_sensitivity, families = run_compensation()
    trajectories, search_summary = run_search_control(sources, target)
    make_figures(primary, matrix, organic, compensation, trajectories, search_summary)
    write_manifest()

    print("\nPRIMARY TRANSFER")
    print(primary.to_string(index=False))
    print("\nORGANIC CONTROL")
    print(organic.to_string(index=False))
    print("\nCOMPENSATION SENSITIVITY")
    print(compensation_sensitivity.to_string(index=False))
    print("\nFAMILIES")
    print(families.to_string(index=False))
    print("\nSEARCH CONTROL")
    print(search_summary.to_string(index=False))


if __name__ == "__main__":
    main()
