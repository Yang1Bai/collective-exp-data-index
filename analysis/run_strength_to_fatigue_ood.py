"""Run the frozen static-strength -> fatigue OOD benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from joblib import Parallel, delayed
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from common import ELEMENTS, RESULTS, composition_features, ensure_output_dirs


HERE = Path(__file__).resolve().parent
DESIGN = HERE / "strength_to_fatigue_ood_design.json"
AUDIT = RESULTS / "strength_fatigue_preoutcome_audit.json"
PREOUTCOME_VERIFIED = RESULTS / "strength_fatigue_preoutcome_VERIFIED.json"
RELEASE_MANIFEST = RESULTS / "strength_fatigue_formal_release_manifest.json"
TARGET_RELEASE = RESULTS / "strength_fatigue_formal_target_release.csv"
DONOR_RELEASE = RESULTS / "strength_fatigue_formal_donor_release.csv"
IMPLEMENTATION = HERE / "strength_fatigue_implementation.json"

SOURCE_CARDS = RESULTS / "strength_fatigue_source_cards.csv"
SHUFFLED_CARDS = RESULTS / "strength_fatigue_shuffled_source_cards.csv"
SOURCE_SUMMARY = RESULTS / "strength_fatigue_source_summary.json"
SPLITS = RESULTS / "strength_fatigue_split_audit.csv"
METRICS = RESULTS / "strength_fatigue_metrics.csv"
PREDICTIONS = RESULTS / "strength_fatigue_predictions.csv"
BOOTSTRAP = RESULTS / "strength_fatigue_bootstrap.csv"
SUMMARY = RESULTS / "strength_fatigue_summary.json"
ENVIRONMENT = RESULTS / "strength_fatigue_environment.json"

PROCESS_COLUMNS = [
    "process_cast_or_melt",
    "process_wrought",
    "process_powder",
    "process_heat_treated",
    "process_additive",
]
PHASE_COLUMNS = [
    "phase_fcc",
    "phase_bcc",
    "phase_hcp",
    "phase_amorphous",
    "phase_multiphase",
]
TARGET_NUMERIC = [
    *PROCESS_COLUMNS,
    *PHASE_COLUMNS,
    "fatigue_temperature_c",
    "load_ratio",
    "frequency_hz",
    "log_stress_amplitude",
]
TARGET_CATEGORICAL = [
    "fatigue_test_type",
    "fatigue_environment",
    "load_control",
]
CARD_COLUMNS = [
    "card_prediction_log10",
    "stress_minus_card_log10",
    "maximum_stress_over_card",
    "nearest_borg_l1",
    "source_disagreement_log10",
    "source_applicable",
]
METHODS = [
    "target_only",
    "safe_borg_uts",
    "safe_shuffled_uts",
    "safe_borg_hardness_control",
    "safe_borg_elongation_control",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", type=Path, default=DESIGN)
    parser.add_argument("--implementation", type=Path, default=IMPLEMENTATION)
    parser.add_argument("--target", type=Path, default=TARGET_RELEASE)
    parser.add_argument("--donors", type=Path, default=DONOR_RELEASE)
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--trees", type=int)
    parser.add_argument("--bootstrap-replicates", type=int)
    parser.add_argument("--jobs", type=int, default=-1)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def stable_seed(*parts: Any) -> int:
    value = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(value[:4], "little")


def verify_inputs(args: argparse.Namespace) -> dict[str, Any]:
    design = json.loads(args.design.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    verified = json.loads(PREOUTCOME_VERIFIED.read_text(encoding="utf-8"))
    release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    implementation = json.loads(args.implementation.read_text(encoding="utf-8"))
    expected_design = digest(args.design)
    if audit["design_sha256"] != expected_design:
        raise AssertionError("Audit design hash mismatch")
    if verified["design_sha256"] != expected_design:
        raise AssertionError("Pre-outcome verifier design hash mismatch")
    if release["design_sha256"] != expected_design:
        raise AssertionError("Formal release design hash mismatch")
    if implementation["design_sha256"] != expected_design:
        raise AssertionError("Implementation design hash mismatch")
    if release["target_release_sha256"] != digest(args.target):
        raise AssertionError("Target formal release changed")
    if release["donor_release_sha256"] != digest(args.donors):
        raise AssertionError("Donor formal release changed")
    for relative, expected in implementation["code_sha256"].items():
        path = HERE.parent / relative
        if digest(path) != expected:
            raise AssertionError(f"Frozen implementation file changed: {relative}")
    return design


def add_composition(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    output = frame.copy()
    values = composition_features(output["material_key"].astype(str).tolist())
    columns = [f"composition_{index:03d}" for index in range(values.shape[1])]
    composition = pd.DataFrame(values, columns=columns, index=output.index)
    return pd.concat([output, composition], axis=1), columns


def deterministic_size_match(
    frame: pd.DataFrame, target_n: int, seed: int
) -> pd.DataFrame:
    if len(frame) < target_n:
        raise RuntimeError(f"Cannot size-match {len(frame)} rows to {target_n}")
    if len(frame) == target_n:
        return frame.sort_values(
            ["material_key", "raw_row_id"], kind="mergesort"
        ).reset_index(drop=True)
    output = frame.copy()
    output["_selection"] = [
        stable_seed(seed, donor, row_id, key)
        for donor, row_id, key in zip(
            output["donor"],
            output["raw_row_id"],
            output["material_key"],
            strict=True,
        )
    ]
    return (
        output.sort_values(
            ["_selection", "material_key", "raw_row_id"], kind="mergesort"
        )
        .head(target_n)
        .drop(columns="_selection")
        .reset_index(drop=True)
    )


def source_model(seed: int, trees: int, jobs: int = 1) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=trees,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=jobs,
    )


def source_matrix(
    frame: pd.DataFrame,
    composition_columns: Sequence[str],
    *,
    composition_only: bool,
) -> np.ndarray:
    columns = list(composition_columns)
    if not composition_only:
        columns += PROCESS_COLUMNS + PHASE_COLUMNS + ["temperature_c"]
    output = frame[columns].copy()
    for column in output.columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")
        if output[column].isna().all():
            output[column] = 0.0
        else:
            output[column] = output[column].fillna(output[column].median())
    return output.to_numpy(float)


def target_source_matrix(
    frame: pd.DataFrame,
    composition_columns: Sequence[str],
    *,
    composition_only: bool,
) -> np.ndarray:
    columns = list(composition_columns)
    if not composition_only:
        columns += PROCESS_COLUMNS + PHASE_COLUMNS + ["fatigue_temperature_c"]
    output = frame[columns].copy()
    for column in output.columns:
        output[column] = pd.to_numeric(output[column], errors="coerce")
        output[column] = output[column].fillna(0.0)
    return output.to_numpy(float)


def predict_source_card(
    source: pd.DataFrame,
    target_curves: pd.DataFrame,
    composition_columns: Sequence[str],
    *,
    trees: int,
    seed: int,
    composition_only: bool,
    shuffled: bool,
) -> np.ndarray:
    prediction = np.full(len(target_curves), np.nan)
    for composition_key in sorted(target_curves["composition_key"].unique()):
        held = target_curves["composition_key"].eq(composition_key).to_numpy()
        fit_source = source[~source["material_key"].eq(composition_key)].copy()
        if len(fit_source) < 50:
            raise RuntimeError(
                f"Only {len(fit_source)} source rows after excluding "
                f"{composition_key}"
            )
        y = fit_source["log_value"].to_numpy(float).copy()
        if shuffled:
            np.random.default_rng(
                stable_seed(seed, "source-shuffle", composition_key)
            ).shuffle(y)
        x_fit = source_matrix(
            fit_source, composition_columns, composition_only=composition_only
        )
        x_target = target_source_matrix(
            target_curves.loc[held],
            composition_columns,
            composition_only=composition_only,
        )
        fitted = source_model(
            stable_seed(seed, "source-fit", composition_key), trees, jobs=1
        ).fit(x_fit, y)
        prediction[held] = fitted.predict(x_target)
    if not np.isfinite(prediction).all():
        raise AssertionError("Incomplete source-card predictions")
    return prediction


def donor_only_disagreement_threshold(
    borg_uts: pd.DataFrame,
    birdshot: pd.DataFrame,
    composition_columns: Sequence[str],
    trees: int,
    seed: int,
) -> float:
    overlap = set(borg_uts["material_key"]) & set(birdshot["material_key"])
    if not overlap:
        fitted = source_model(
            stable_seed(seed, "disagreement-threshold-full"), trees, jobs=1
        ).fit(
            source_matrix(
                borg_uts, composition_columns, composition_only=True
            ),
            borg_uts["log_value"].to_numpy(float),
        )
        prediction = fitted.predict(
            source_matrix(
                birdshot, composition_columns, composition_only=True
            )
        )
        error = np.abs(prediction - birdshot["log_value"].to_numpy(float))
        return float(np.quantile(error, 0.9))

    prediction = np.full(len(birdshot), np.nan)
    for key in sorted(birdshot["material_key"].unique()):
        held = birdshot["material_key"].eq(key).to_numpy()
        fit = borg_uts[~borg_uts["material_key"].eq(key)]
        fitted = source_model(
            stable_seed(seed, "disagreement-threshold", key), trees, jobs=1
        ).fit(
            source_matrix(fit, composition_columns, composition_only=True),
            fit["log_value"].to_numpy(float),
        )
        prediction[held] = fitted.predict(
            source_matrix(
                birdshot.loc[held],
                composition_columns,
                composition_only=True,
            )
        )
    error = np.abs(prediction - birdshot["log_value"].to_numpy(float))
    if not np.isfinite(error).all():
        raise AssertionError("Non-finite donor-only disagreement calibration")
    return float(np.quantile(error, 0.9))


def prepare_source_cards(
    target: pd.DataFrame,
    donors: pd.DataFrame,
    design: dict[str, Any],
    repeats: int,
    trees: int,
    jobs: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], list[str]]:
    curve_columns = [
        "dataset_id",
        "composition_key",
        "nearest_borg_l1",
        "fatigue_temperature_c",
        *PROCESS_COLUMNS,
        *PHASE_COLUMNS,
    ]
    curves = (
        target[curve_columns]
        .drop_duplicates("dataset_id")
        .sort_values("dataset_id")
        .reset_index(drop=True)
    )
    curves["material_key"] = curves["composition_key"]
    curves_with_comp, composition_columns = add_composition(curves)
    donors_with_comp, donor_composition_columns = add_composition(donors)
    if composition_columns != donor_composition_columns:
        raise AssertionError("Composition feature schemas differ")
    common_n = int(design["models"]["primary_common_source_size"])
    primary_sources = {}
    for donor in ("borg_uts", "borg_hardness", "borg_elongation"):
        primary_sources[donor] = deterministic_size_match(
            donors_with_comp[donors_with_comp["donor"].eq(donor)].copy(),
            common_n,
            stable_seed(design["models"]["random_seed"], donor, "size-match"),
        )
    birdshot = donors_with_comp[
        donors_with_comp["donor"].eq("birdshot_uts")
    ].reset_index(drop=True)

    predictions = {}
    for donor, source in primary_sources.items():
        predictions[donor] = predict_source_card(
            source,
            curves_with_comp,
            composition_columns,
            trees=trees,
            seed=stable_seed(design["models"]["random_seed"], donor),
            composition_only=False,
            shuffled=False,
        )
    predictions["birdshot_uts"] = predict_source_card(
        birdshot,
        curves_with_comp,
        composition_columns,
        trees=trees,
        seed=stable_seed(design["models"]["random_seed"], "birdshot"),
        composition_only=True,
        shuffled=False,
    )
    threshold = donor_only_disagreement_threshold(
        primary_sources["borg_uts"],
        birdshot,
        composition_columns,
        trees,
        stable_seed(design["models"]["random_seed"], "disagreement"),
    )
    source_cards = curves_with_comp[
        ["dataset_id", "material_key", "nearest_borg_l1"]
    ].copy()
    for name, values in predictions.items():
        source_cards[f"{name}_log10"] = values
    source_cards["source_disagreement_log10"] = np.abs(
        source_cards["borg_uts_log10"] - source_cards["birdshot_uts_log10"]
    )
    source_cards["source_applicable"] = (
        source_cards["nearest_borg_l1"].le(
            design["preoutcome_gate"]["supported_neighbor_l1_threshold"]
        )
        & source_cards["source_disagreement_log10"].le(threshold)
    )

    source = primary_sources["borg_uts"]
    def one_shuffled_repeat(repeat: int) -> list[dict[str, Any]]:
        values = predict_source_card(
            source,
            curves_with_comp,
            composition_columns,
            trees=trees,
            seed=stable_seed(
                design["models"]["random_seed"], "shuffled", repeat
            ),
            composition_only=False,
            shuffled=True,
        )
        return [
            {
                "repeat": repeat,
                "dataset_id": int(dataset_id),
                "shuffled_uts_log10": float(prediction),
            }
            for dataset_id, prediction in zip(
                curves_with_comp["dataset_id"], values, strict=True
            )
        ]

    shuffled_batches = Parallel(n_jobs=jobs, verbose=5)(
        delayed(one_shuffled_repeat)(repeat) for repeat in range(repeats)
    )
    shuffled_rows = [
        row for batch in shuffled_batches for row in batch
    ]
    shuffled_cards = pd.DataFrame(shuffled_rows)
    summary = {
        "common_source_size": common_n,
        "source_rows_before_size_match": {
            donor: int(donors["donor"].eq(donor).sum())
            for donor in sorted(donors["donor"].unique())
        },
        "donor_only_disagreement_q90_log10": threshold,
        "applicable_curves": int(source_cards["source_applicable"].sum()),
        "total_curves": int(len(source_cards)),
        "applicability_fraction_curves": float(
            source_cards["source_applicable"].mean()
        ),
    }
    return source_cards, shuffled_cards, summary, composition_columns


def target_pipeline(
    learner: str,
    numeric: Sequence[str],
    categorical: Sequence[str],
    seed: int,
    trees: int,
) -> Pipeline:
    transformers: list[tuple[str, Any, Sequence[str]]] = [
        (
            "numeric",
            Pipeline(
                [
                    (
                        "impute",
                        SimpleImputer(
                            strategy="median", keep_empty_features=True
                        ),
                    ),
                    ("scale", StandardScaler()),
                ]
            ),
            list(numeric),
        )
    ]
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "impute",
                            SimpleImputer(
                                strategy="most_frequent",
                                keep_empty_features=True,
                            ),
                        ),
                        (
                            "onehot",
                            OneHotEncoder(
                                handle_unknown="ignore", sparse_output=False
                            ),
                        ),
                    ]
                ),
                list(categorical),
            )
        )
    pre = ColumnTransformer(transformers, remainder="drop")
    if learner == "extra_trees":
        estimator = ExtraTreesRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=1,
        )
    elif learner == "random_forest":
        estimator = RandomForestRegressor(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.7,
            random_state=seed,
            n_jobs=1,
        )
    else:
        raise ValueError(learner)
    return Pipeline([("preprocess", pre), ("model", estimator)])


def balanced_curve_sample(
    curve_table: pd.DataFrame, budget: int, seed: int
) -> list[int]:
    rng = np.random.default_rng(seed)
    groups = {
        str(component): list(values)
        for component, values in curve_table.groupby(
            "provenance_chemistry_component"
        )["dataset_id"]
    }
    for values in groups.values():
        rng.shuffle(values)
    order = list(groups)
    rng.shuffle(order)
    selected: list[int] = []
    while len(selected) < budget and any(groups.values()):
        progressed = False
        for component in order:
            if groups[component] and len(selected) < budget:
                selected.append(int(groups[component].pop()))
                progressed = True
        if not progressed:
            break
        rng.shuffle(order)
    if len(selected) < budget:
        raise RuntimeError(f"Only {len(selected)} curves available for budget {budget}")
    return selected


def apply_card(
    frame: pd.DataFrame, prediction_log: pd.Series
) -> pd.DataFrame:
    output = frame.copy()
    output["card_prediction_log10"] = prediction_log.to_numpy(float)
    output["stress_minus_card_log10"] = (
        output["log_stress_amplitude"]
        - output["card_prediction_log10"]
    )
    denominator = 1.0 - output["load_ratio"].to_numpy(float)
    maximum_stress = np.divide(
        2.0 * output["stress_amplitude_mpa"].to_numpy(float),
        denominator,
        out=np.full(len(output), np.nan),
        where=np.abs(denominator) > 1e-8,
    )
    card_raw = np.power(10.0, output["card_prediction_log10"].to_numpy(float))
    output["maximum_stress_over_card"] = maximum_stress / card_raw
    return output


def card_column(method: str) -> str:
    return {
        "safe_borg_uts": "borg_uts_log10",
        "safe_shuffled_uts": "shuffled_uts_log10",
        "safe_borg_hardness_control": "borg_hardness_log10",
        "safe_borg_elongation_control": "borg_elongation_log10",
    }[method]


def fit_one_run(
    component: str,
    repeat: int,
    learner: str,
    target: pd.DataFrame,
    curve_table: pd.DataFrame,
    shuffled_cards: pd.DataFrame,
    composition_columns: Sequence[str],
    budget: int,
    trees: int,
    base_seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    evaluation = target[
        target["provenance_chemistry_component"].eq(component)
    ].copy()
    development_curves = curve_table[
        ~curve_table["provenance_chemistry_component"].eq(component)
    ]
    selected = balanced_curve_sample(
        development_curves,
        budget,
        stable_seed(base_seed, component, repeat, "curve-sample"),
    )
    training = target[
        target["dataset_id"].isin(selected) & target["runout"].eq(0)
    ].copy()
    if set(training["dataset_id"]) & set(evaluation["dataset_id"]):
        raise AssertionError("Target curve leakage")
    if set(training["provenance_chemistry_component"]) & {component}:
        raise AssertionError("Target component leakage")
    y_train = training["log_life"].to_numpy(float)
    numeric = [*composition_columns, *TARGET_NUMERIC]
    fitted_base = target_pipeline(
        learner,
        numeric,
        TARGET_CATEGORICAL,
        stable_seed(base_seed, component, repeat, learner, "base"),
        trees,
    ).fit(training, y_train)
    base_prediction = fitted_base.predict(evaluation)

    predictions_by_method = {"target_only": base_prediction}
    shuffled_map = (
        shuffled_cards[shuffled_cards["repeat"].eq(repeat)]
        .set_index("dataset_id")["shuffled_uts_log10"]
    )
    for method in METHODS[1:]:
        column = card_column(method)
        if method == "safe_shuffled_uts":
            train_values = training["dataset_id"].map(shuffled_map)
            eval_values = evaluation["dataset_id"].map(shuffled_map)
        else:
            train_values = training[column]
            eval_values = evaluation[column]
        train_card = apply_card(training, train_values)
        eval_card = apply_card(evaluation, eval_values)
        applicable_train = train_card["source_applicable"].astype(bool)
        if train_card.loc[applicable_train, "dataset_id"].nunique() < 5:
            prediction = base_prediction.copy()
        else:
            fitted = target_pipeline(
                learner,
                [*numeric, *CARD_COLUMNS],
                TARGET_CATEGORICAL,
                stable_seed(base_seed, component, repeat, learner, method),
                trees,
            ).fit(
                train_card.loc[applicable_train],
                train_card.loc[applicable_train, "log_life"].to_numpy(float),
            )
            augmented_prediction = fitted.predict(eval_card)
            prediction = np.where(
                eval_card["source_applicable"].astype(bool),
                augmented_prediction,
                base_prediction,
            )
        predictions_by_method[method] = prediction

    metric_rows = []
    prediction_rows = []
    failure = evaluation["runout"].eq(0).to_numpy()
    for method, prediction in predictions_by_method.items():
        y = evaluation.loc[failure, "log_life"].to_numpy(float)
        p = np.asarray(prediction)[failure]
        rmse = float(mean_squared_error(y, p) ** 0.5)
        mae = float(mean_absolute_error(y, p))
        component_r2 = (
            float(r2_score(y, p)) if len(y) >= 2 and np.std(y) > 0 else math.nan
        )
        metric_rows.append(
            {
                "component": component,
                "repeat": repeat,
                "learner": learner,
                "method": method,
                "budget_curves": budget,
                "evaluation_rows_failure": int(failure.sum()),
                "evaluation_curves": int(evaluation["dataset_id"].nunique()),
                "rmse_log10_cycles": rmse,
                "mae_log10_cycles": mae,
                "component_r2": component_r2,
                "applicability_fraction": float(
                    evaluation["source_applicable"].mean()
                ),
            }
        )
        for row, predicted in zip(
            evaluation.itertuples(index=False), prediction, strict=True
        ):
            prediction_rows.append(
                {
                    "component": component,
                    "repeat": repeat,
                    "learner": learner,
                    "method": method,
                    "dataset_id": int(row.dataset_id),
                    "life_cycles": float(row.life_cycles),
                    "log_life": float(row.log_life),
                    "runout": int(row.runout),
                    "prediction_log10_cycles": float(predicted),
                    "source_applicable": bool(row.source_applicable),
                    "nearest_borg_l1": float(row.nearest_borg_l1),
                }
            )
    split_row = {
        "component": component,
        "repeat": repeat,
        "learner": learner,
        "budget_curves": budget,
        "training_curves": json.dumps(sorted(selected)),
        "evaluation_curves": json.dumps(
            sorted(map(int, evaluation["dataset_id"].unique()))
        ),
        "training_components": int(
            training["provenance_chemistry_component"].nunique()
        ),
    }
    return metric_rows, prediction_rows, split_row


def contrast_table(metrics: pd.DataFrame) -> pd.DataFrame:
    wide = metrics.pivot_table(
        index=["component", "repeat", "learner"],
        columns="method",
        values="rmse_log10_cycles",
        aggfunc="first",
    ).reset_index()
    definitions = {
        "real_vs_target_only": ("target_only", "safe_borg_uts"),
        "real_vs_shuffled_uts": ("safe_shuffled_uts", "safe_borg_uts"),
        "real_vs_hardness": (
            "safe_borg_hardness_control",
            "safe_borg_uts",
        ),
        "real_vs_elongation": (
            "safe_borg_elongation_control",
            "safe_borg_uts",
        ),
    }
    rows = []
    for name, (control, real) in definitions.items():
        part = wide[["component", "repeat", "learner", control, real]].copy()
        part["contrast"] = name
        part["relative_rmse_gain"] = 1.0 - part[real] / part[control]
        rows.append(
            part[
                [
                    "component",
                    "repeat",
                    "learner",
                    "contrast",
                    "relative_rmse_gain",
                ]
            ]
        )
    return pd.concat(rows, ignore_index=True)


def exact_sign_flip_p(component_effects: np.ndarray) -> float:
    values = np.asarray(component_effects, dtype=float)
    observed = float(values.mean())
    if observed <= 0:
        return 1.0
    n = len(values)
    if n <= 20:
        count = 0
        total = 1 << n
        for mask in range(total):
            signs = np.array(
                [1.0 if (mask >> index) & 1 else -1.0 for index in range(n)]
            )
            if float(np.mean(values * signs)) >= observed - 1e-15:
                count += 1
        return float((count + 1) / (total + 1))
    rng = np.random.default_rng(2026072902)
    signs = rng.choice([-1.0, 1.0], size=(100000, n))
    null = (signs * values).mean(axis=1)
    return float((np.sum(null >= observed) + 1) / (len(null) + 1))


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    m = len(ordered)
    for rank, key in enumerate(ordered):
        value = min(1.0, (m - rank) * p_values[key])
        running = max(running, value)
        adjusted[key] = running
    return adjusted


def bootstrap_contrasts(
    contrasts: pd.DataFrame, replicates: int, seed: int
) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]:
    outputs = []
    summaries: dict[str, dict[str, Any]] = {}
    rng = np.random.default_rng(seed)
    p_values = {}
    for contrast in sorted(contrasts["contrast"].unique()):
        frame = contrasts[contrasts["contrast"].eq(contrast)].copy()
        components = sorted(frame["component"].unique())
        runs = sorted(
            set(zip(frame["repeat"], frame["learner"], strict=False))
        )
        pivot = frame.pivot_table(
            index="component",
            columns=["repeat", "learner"],
            values="relative_rmse_gain",
            aggfunc="first",
        ).reindex(index=components, columns=pd.MultiIndex.from_tuples(runs))
        values = pivot.to_numpy(float)
        if not np.isfinite(values).all():
            raise AssertionError(f"Incomplete contrast grid: {contrast}")
        component_effects = values.mean(axis=1)
        observed = float(values.mean())
        p_values[contrast] = exact_sign_flip_p(component_effects)
        chunk = 2000
        samples = []
        for start in range(0, replicates, chunk):
            size = min(chunk, replicates - start)
            component_draw = rng.integers(
                0, len(components), size=(size, len(components))
            )
            run_draw = rng.integers(0, len(runs), size=(size, len(runs)))
            result = np.empty(size, dtype=float)
            for index in range(size):
                result[index] = values[
                    component_draw[index][:, None],
                    run_draw[index][None, :],
                ].mean()
            samples.append(result)
        draws = np.concatenate(samples)
        outputs.extend(
            {
                "contrast": contrast,
                "bootstrap": index,
                "relative_rmse_gain": float(value),
            }
            for index, value in enumerate(draws)
        )
        summaries[contrast] = {
            "mean_relative_rmse_gain": observed,
            "ci95": [
                float(np.quantile(draws, 0.025)),
                float(np.quantile(draws, 0.975)),
            ],
            "positive_component_fraction": float(
                np.mean(component_effects > 0)
            ),
            "positive_run_fraction": float(
                np.mean(values.mean(axis=0) > 0)
            ),
            "component_effects": {
                component: float(effect)
                for component, effect in zip(
                    components, component_effects, strict=True
                )
            },
            "one_sided_component_sign_flip_p": p_values[contrast],
        }
    adjusted = holm_adjust(p_values)
    for contrast, value in adjusted.items():
        summaries[contrast]["holm_adjusted_p"] = value
    return pd.DataFrame(outputs), summaries


def pooled_r2(predictions: pd.DataFrame) -> dict[str, dict[str, float]]:
    failures = predictions[predictions["runout"].eq(0)]
    rows: dict[str, dict[str, float]] = {}
    for method, part in failures.groupby("method"):
        run_values = []
        for (_, _), run in part.groupby(["repeat", "learner"]):
            run_values.append(
                float(r2_score(run["log_life"], run["prediction_log10_cycles"]))
            )
        rows[method] = {
            "mean_pooled_r2": float(np.mean(run_values)),
            "minimum_pooled_r2": float(np.min(run_values)),
        }
    return rows


def concordance_index(frame: pd.DataFrame) -> float:
    time = frame["log_life"].to_numpy(float)
    event = frame["runout"].eq(0).to_numpy()
    score = frame["prediction_log10_cycles"].to_numpy(float)
    concordant = 0.0
    comparable = 0
    for left in range(len(frame)):
        for right in range(left + 1, len(frame)):
            if time[left] < time[right] and event[left]:
                comparable += 1
                concordant += (
                    1.0
                    if score[left] < score[right]
                    else 0.5 if score[left] == score[right] else 0.0
                )
            elif time[right] < time[left] and event[right]:
                comparable += 1
                concordant += (
                    1.0
                    if score[right] < score[left]
                    else 0.5 if score[left] == score[right] else 0.0
                )
    return float(concordant / comparable) if comparable else math.nan


def censored_secondary(predictions: pd.DataFrame) -> dict[str, float]:
    output = {}
    for method, part in predictions.groupby("method"):
        values = [
            concordance_index(run)
            for (_, _), run in part.groupby(["repeat", "learner"])
        ]
        output[method] = float(np.nanmean(values))
    return output


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    design = verify_inputs(args)
    repeats = args.repeats or int(design["models"]["repeats"])
    trees = args.trees or int(design["models"]["tree_estimators"])
    bootstrap_replicates = (
        args.bootstrap_replicates
        or int(design["inference"]["bootstrap_replicates"])
    )
    target = pd.read_csv(args.target)
    donors = pd.read_csv(args.donors)
    release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    if len(target) != release["target_rows"]:
        raise AssertionError("Target release row count changed")
    if target["dataset_id"].nunique() != release["target_curves"]:
        raise AssertionError("Target curve count changed")
    if not target["runout"].isin([0, 1]).all():
        raise AssertionError("Invalid runout values")
    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "validated-only-no-model-fit",
                    "target_rows": int(len(target)),
                    "target_curves": int(target["dataset_id"].nunique()),
                    "components": int(
                        target["provenance_chemistry_component"].nunique()
                    ),
                    "donor_rows": int(len(donors)),
                    "design_sha256": digest(args.design),
                },
                indent=2,
            )
        )
        return

    target["material_key"] = target["composition_key"]
    target["log_life"] = np.log10(target["life_cycles"].to_numpy(float))
    target["log_stress_amplitude"] = np.log10(
        target["stress_amplitude_mpa"].to_numpy(float)
    )
    target, composition_columns = add_composition(target)
    jobs = os.cpu_count() if args.jobs == -1 else args.jobs
    source_cards, shuffled_cards, source_summary, source_comp = (
        prepare_source_cards(target, donors, design, repeats, trees, jobs)
    )
    if source_comp != composition_columns:
        raise AssertionError("Target and source composition features differ")
    source_cards.to_csv(SOURCE_CARDS, index=False)
    shuffled_cards.to_csv(SHUFFLED_CARDS, index=False)
    source_summary.update(
        {
            "design_sha256": digest(args.design),
            "source_cards_sha256": digest(SOURCE_CARDS),
            "shuffled_cards_sha256": digest(SHUFFLED_CARDS),
        }
    )
    SOURCE_SUMMARY.write_text(
        json.dumps(source_summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    target = target.merge(
        source_cards.drop(columns=["material_key"]),
        on=["dataset_id", "nearest_borg_l1"],
        how="left",
        validate="many_to_one",
    )
    if target[
        [
            "borg_uts_log10",
            "borg_hardness_log10",
            "borg_elongation_log10",
            "birdshot_uts_log10",
        ]
    ].isna().any().any():
        raise AssertionError("Source cards did not map to target rows")

    failures = target[target["runout"].eq(0)].copy()
    curve_table = (
        failures[
            ["dataset_id", "provenance_chemistry_component"]
        ]
        .drop_duplicates()
        .sort_values("dataset_id")
        .reset_index(drop=True)
    )
    components = sorted(
        failures["provenance_chemistry_component"].unique()
    )
    learners = list(design["models"]["target_learners"])
    tasks = [
        (component, repeat, learner)
        for component in components
        for repeat in range(repeats)
        for learner in learners
    ]
    outputs = Parallel(n_jobs=jobs, verbose=10)(
        delayed(fit_one_run)(
            component,
            repeat,
            learner,
            target,
            curve_table,
            shuffled_cards,
            composition_columns,
            int(design["ood_design"]["primary_budget"]),
            trees,
            int(design["models"]["random_seed"]),
        )
        for component, repeat, learner in tasks
    )
    metric_rows = [row for result in outputs for row in result[0]]
    prediction_rows = [row for result in outputs for row in result[1]]
    split_rows = [result[2] for result in outputs]
    metrics = pd.DataFrame(metric_rows)
    predictions = pd.DataFrame(prediction_rows)
    splits = pd.DataFrame(split_rows)
    metrics.to_csv(METRICS, index=False)
    predictions.to_csv(PREDICTIONS, index=False)
    splits.to_csv(SPLITS, index=False)

    contrasts = contrast_table(metrics)
    bootstrap, inference = bootstrap_contrasts(
        contrasts,
        bootstrap_replicates,
        int(design["inference"]["seed"]),
    )
    bootstrap.to_csv(BOOTSTRAP, index=False)
    absolute_r2 = pooled_r2(predictions)
    censored = censored_secondary(predictions)
    primary = inference["real_vs_target_only"]
    learner_effects = {}
    for learner in learners:
        part = contrasts[
            contrasts["contrast"].eq("real_vs_target_only")
            & contrasts["learner"].eq(learner)
        ]
        learner_effects[learner] = float(part["relative_rmse_gain"].mean())
    coverage = float(predictions["source_applicable"].mean())
    gates_spec = design["success_gate"]
    checks = {
        "relative_rmse_gain_at_least_0_05": (
            primary["mean_relative_rmse_gain"]
            >= gates_spec["primary_relative_rmse_gain_at_least"]
        ),
        "bootstrap_ci_lower_positive": (
            primary["ci95"][0]
            > gates_spec["cluster_bootstrap_ci95_lower_above"]
        ),
        "holm_p_below_0_05": (
            primary["holm_adjusted_p"]
            < gates_spec["holm_adjusted_one_sided_p_below"]
        ),
        "absolute_augmented_r2_positive": (
            absolute_r2["safe_borg_uts"]["mean_pooled_r2"]
            > gates_spec["augmented_absolute_r2_above"]
        ),
        "positive_repeat_fraction_at_least_0_8": (
            primary["positive_run_fraction"]
            >= gates_spec["positive_repeat_fraction_at_least"]
        ),
        "beats_all_controls": all(
            inference[name]["mean_relative_rmse_gain"] > 0
            and inference[name]["ci95"][0] > 0
            for name in (
                "real_vs_shuffled_uts",
                "real_vs_hardness",
                "real_vs_elongation",
            )
        ),
        "both_learners_nonnegative": all(
            value >= 0 for value in learner_effects.values()
        ),
        "applicability_coverage": (
            coverage >= gates_spec["minimum_applicability_coverage"]
        ),
    }
    summary = {
        "status": "verified-inference-ready-pending-independent-verifier",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "design_sha256": digest(args.design),
        "implementation_sha256": digest(args.implementation),
        "release_manifest_sha256": digest(RELEASE_MANIFEST),
        "source_summary_sha256": digest(SOURCE_SUMMARY),
        "metrics_sha256": digest(METRICS),
        "predictions_sha256": digest(PREDICTIONS),
        "splits_sha256": digest(SPLITS),
        "bootstrap_sha256": digest(BOOTSTRAP),
        "target_rows": int(len(target)),
        "target_curves": int(target["dataset_id"].nunique()),
        "failure_rows": int(target["runout"].eq(0).sum()),
        "runout_rows": int(target["runout"].eq(1).sum()),
        "components": int(len(components)),
        "repeats": repeats,
        "learners": learners,
        "methods": METHODS,
        "applicability_coverage_rows": coverage,
        "inference": inference,
        "learner_primary_effects": learner_effects,
        "absolute_r2": absolute_r2,
        "censored_secondary_mean_concordance": censored,
        "gate_checks": checks,
        "passes_complete_gate": bool(all(checks.values())),
        "decision": (
            "independent-positive-edge"
            if all(checks.values())
            else "null-harmful-or-incomplete-edge"
        ),
        "claim_guard": design["claim_guard"],
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    environment = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "node": os.environ.get("SLURMD_NODENAME"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "trees": trees,
        "parallel_jobs": jobs,
    }
    ENVIRONMENT.write_text(
        json.dumps(environment, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "decision": summary["decision"],
                "passes_complete_gate": summary["passes_complete_gate"],
                "primary": inference["real_vs_target_only"],
                "components": summary["components"],
                "applicability_coverage_rows": coverage,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
