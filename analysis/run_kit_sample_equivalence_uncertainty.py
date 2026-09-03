"""Post-outcome uncertainty diagnostic for KIT target-label equivalence.

The frozen rescue rule used the point estimate from the target-only learning
curve.  This diagnostic does not redefine that rule.  It reconstructs
formulation-level target-only prediction errors at every curve budget and
resamples both formulations and target-training repetitions to quantify the
stability of the interpolated equivalent sample count.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.isotonic import IsotonicRegression

from common import RESULTS
from run_kit_temperature_borrowing import (
    DESIGN_PATH,
    build_samples,
    load_raw,
    outer_splits,
    prepare_formulations,
    target_forest,
)
from run_knowledge_map import stable_offset, target_equivalent_samples


def baseline_curve_predictions(
    x: np.ndarray,
    y: np.ndarray,
    keys: list[str],
    splits: dict[str, dict[str, np.ndarray]],
    budgets: list[int],
    repeats: int,
    seed: int,
    jobs: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    curve_seed = seed + stable_offset("kit-learning-curve")
    for budget in budgets:
        active_repeats = 100 if budget == 30 else repeats
        samples = build_samples(
            splits,
            budget,
            active_repeats,
            seed
            if budget == 30
            else curve_seed + stable_offset(f"curve:{budget}"),
        )
        tasks = [
            (fold_id, split, repeat, train)
            for fold_id, split in splits.items()
            for repeat, train in enumerate(samples[fold_id])
        ]

        def one_fit(fold_id, split, repeat, train):
            test = split["test"]
            if budget == 30:
                model_seed = seed + stable_offset(
                    f"target:random-forest-primary:{fold_id}:{repeat}"
                ) % 1_000_000
            else:
                model_seed = curve_seed + stable_offset(
                    f"curve:{budget}:{fold_id}:{repeat}"
                ) % 1_000_000
            prediction = target_forest(model_seed, n_jobs=1).fit(
                x[train], y[train]
            ).predict(x[test])
            return [
                {
                    "budget": budget,
                    "repeat": repeat,
                    "formulation_key": keys[index],
                    "squared_error": float((y[index] - prediction[position]) ** 2),
                }
                for position, index in enumerate(test)
            ]

        fitted = Parallel(n_jobs=jobs, prefer="processes", verbose=0)(
            delayed(one_fit)(*task) for task in tasks
        )
        rows.extend(row for block in fitted for row in block)
    return pd.DataFrame(rows)


def error_matrix(
    frame: pd.DataFrame, keys: list[str], repeats: list[int]
) -> np.ndarray:
    matrix = (
        frame.pivot(index="repeat", columns="formulation_key", values="squared_error")
        .reindex(index=repeats, columns=keys)
        .to_numpy(float)
    )
    if not np.isfinite(matrix).all():
        raise AssertionError("Incomplete formulation-by-repeat error matrix")
    return matrix


def augmented_error_matrix(keys: list[str]) -> np.ndarray:
    path = RESULTS / "kit_temperature_predictions.csv"
    predictions = pd.read_csv(path)
    primary = predictions[
        (predictions["source"] == "temperature_-20_C")
        & (predictions["learner"] == "random-forest-primary")
    ].copy()
    primary = primary.rename(columns={"material_key": "formulation_key"})
    primary["squared_error"] = (primary["y"] - primary["augmented"]) ** 2
    return error_matrix(primary, keys, sorted(primary["repeat"].unique()))


def bootstrap_equivalence(
    curve_matrices: dict[int, np.ndarray],
    augmented: np.ndarray,
    budgets: list[int],
    seed: int,
    n_boot: int,
) -> pd.DataFrame:
    n_entities = augmented.shape[1]
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for iteration in range(n_boot):
        entity_index = rng.integers(0, n_entities, size=n_entities)
        curve_rows = []
        for budget in budgets:
            matrix = curve_matrices[budget]
            repeat_index = rng.integers(0, matrix.shape[0], size=matrix.shape[0])
            rmse = float(
                np.sqrt(matrix[repeat_index][:, entity_index].mean())
            )
            curve_rows.append({"train_n": budget, "rmse_mean": rmse})
        curve = pd.DataFrame(curve_rows).sort_values("train_n")
        curve["rmse_monotone"] = IsotonicRegression(
            increasing=False
        ).fit_transform(curve["train_n"], curve["rmse_mean"])
        aug_repeat_index = rng.integers(
            0, augmented.shape[0], size=augmented.shape[0]
        )
        aug_rmse = float(
            np.sqrt(augmented[aug_repeat_index][:, entity_index].mean())
        )
        equivalent, fraction, status = target_equivalent_samples(curve, aug_rmse, 30)
        rows.append(
            {
                "bootstrap": iteration,
                "augmented_rmse": aug_rmse,
                "target_equivalent_n": equivalent,
                "target_sample_fraction_saved": fraction,
                "interpolation_status": status,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=-1)
    parser.add_argument("--bootstrap", type=int, default=5000)
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    seed = int(design["seed"])
    budgets = [int(value) for value in design["inference"]["learning_curve_budgets"]]
    raw = load_raw(design)
    formulations, x, outcomes, _ = prepare_formulations(raw, design)
    keys = formulations["formulation_key"].astype(str).tolist()
    splits = outer_splits(keys)
    y = outcomes[int(design["split"]["target_temperature_C"])]

    predictions = baseline_curve_predictions(
        x,
        y,
        keys,
        splits,
        budgets,
        int(design["inference"]["learning_curve_repeats"]),
        seed,
        args.jobs,
    )
    predictions.to_csv(
        RESULTS / "kit_temperature_learning_curve_prediction_repeats.csv", index=False
    )
    curve_matrices = {
        budget: error_matrix(
            predictions[predictions["budget"] == budget],
            keys,
            sorted(predictions.loc[predictions["budget"] == budget, "repeat"].unique()),
        )
        for budget in budgets
    }
    augmented = augmented_error_matrix(keys)
    boot = bootstrap_equivalence(
        curve_matrices,
        augmented,
        budgets,
        seed + stable_offset("sample-equivalence-bootstrap"),
        args.bootstrap,
    )

    existing = json.loads(
        (RESULTS / "kit_temperature_summary.json").read_text(encoding="utf-8")
    )
    fraction = boot["target_sample_fraction_saved"].to_numpy(float)
    equivalent = boot["target_equivalent_n"].to_numpy(float)
    summary = {
        "analysis_status": "post-outcome-sample-equivalence-uncertainty-diagnostic",
        "decision_policy": (
            "does not redefine the frozen rescue decision or its point-estimate gate"
        ),
        "resampled_units": [
            "unique_formulations",
            "target_training_repetitions_independently_within_each_curve_budget",
        ],
        "bootstrap_replicates": int(args.bootstrap),
        "target_budget": 30,
        "point_target_equivalent_n": existing["target_equivalent_n"],
        "point_target_sample_fraction_saved": existing[
            "target_sample_fraction_saved"
        ],
        "bootstrap_target_equivalent_n_95": [
            float(np.percentile(equivalent, 2.5)),
            float(np.percentile(equivalent, 97.5)),
        ],
        "bootstrap_target_sample_fraction_saved_95": [
            float(np.percentile(fraction, 2.5)),
            float(np.percentile(fraction, 97.5)),
        ],
        "bootstrap_probability_fraction_saved_at_least_30pct": float(
            np.mean(fraction >= 0.30)
        ),
        "interpolation_status_counts": {
            str(key): int(value)
            for key, value in boot["interpolation_status"].value_counts().items()
        },
        "limitation": (
            "This conditional bootstrap quantifies formulation and target-subset "
            "stability in the observed KIT campaign; it is not prospective or "
            "cross-campaign uncertainty."
        ),
    }
    boot.to_csv(RESULTS / "kit_sample_equivalence_bootstrap.csv", index=False)
    (RESULTS / "kit_sample_equivalence_uncertainty.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
