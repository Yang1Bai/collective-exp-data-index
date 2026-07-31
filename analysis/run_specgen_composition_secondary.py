"""Post-primary composition-relation analysis for the SpecGen derivatives."""
from __future__ import annotations

import json
import math
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict

from run_specgen_derivative_oer_borrowing import (
    ARCHIVE,
    DESIGN_PATH,
    MEMBERS,
    RANDOM_SEED,
    RESULTS,
    candidate_bootstrap,
    evaluate,
    holm_adjust,
    pooled_candidate_comparison,
    quantile_summary,
    read_member,
    sha256,
    spearman,
    weighted_neighbor_prediction,
)


AMENDMENT = (
    Path(__file__).resolve().parent
    / "SPECGEN_COMPOSITION_SECONDARY_AMENDMENT.md"
)


def make_model(seed: int, n_jobs: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=seed,
        n_jobs=n_jobs,
    )


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    with ZipFile(ARCHIVE) as archive:
        payloads = {key: archive.read(member) for key, member in MEMBERS.items()}
    data = {key: read_member(payload) for key, payload in payloads.items()}

    source_x = data["source"]["metals"].to_numpy(dtype=float)
    source_y = (
        data["source"]["overpotential"].iloc[:, 0].to_numpy(dtype=float) - 1.23
    ) * 1000.0
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    oof = cross_val_predict(
        make_model(RANDOM_SEED, -1), source_x, source_y, cv=cv, n_jobs=1
    )
    source_skill = {
        "oof_rmse_mV": float(mean_squared_error(source_y, oof) ** 0.5),
        "oof_r2": float(r2_score(source_y, oof)),
        "oof_spearman": spearman(source_y, oof),
    }
    if source_skill["oof_r2"] <= 0:
        raise AssertionError("Composition donor failed the source-skill gate")

    donor = make_model(RANDOM_SEED, -1).fit(source_x, source_y)
    target_x = {
        key: data[key]["metals"].to_numpy(dtype=float) for key in "ABCD"
    }
    target_y = {
        key: (
            data[key]["overpotential"].iloc[:, 0].to_numpy(dtype=float) - 1.23
        )
        * 1000.0
        for key in "ABCD"
    }
    static = {key: donor.predict(target_x[key]) for key in "ABCD"}
    zero = {
        key: evaluate(
            target_y[key], static[key], design["selection_fraction"]
        )
        for key in "ABCD"
    }

    def one_shuffle(offset: int) -> dict[str, float]:
        rng = np.random.default_rng(RANDOM_SEED + 30000 + offset)
        shuffled_y = rng.permutation(source_y)
        model = make_model(RANDOM_SEED + 30000 + offset, 1).fit(
            source_x, shuffled_y
        )
        return {
            key: spearman(target_y[key], model.predict(target_x[key]))
            for key in "ABCD"
        }

    null_path = RESULTS / "specgen_composition_secondary_shuffle.csv"
    expected_seeds = [
        RANDOM_SEED + 30000 + offset
        for offset in range(int(design["source_shuffle_seeds"]))
    ]
    if null_path.exists():
        null_table = pd.read_csv(null_path)
        if (
            null_table["seed"].astype(int).tolist() != expected_seeds
            or any(key not in null_table for key in "ABCD")
        ):
            raise AssertionError("Cached composition shuffled-source table changed")
    else:
        null_records = joblib.Parallel(n_jobs=-1, verbose=0)(
            joblib.delayed(one_shuffle)(offset)
            for offset in range(int(design["source_shuffle_seeds"]))
        )
        null_table = pd.DataFrame(null_records)
        null_table.insert(0, "seed", expected_seeds)
        null_table.to_csv(null_path, index=False)
    p_values = {
        key: float(
            (1 + np.sum(null_table[key].to_numpy() >= zero[key]["spearman"]))
            / (len(null_table) + 1)
        )
        for key in "ABCD"
    }
    adjusted = holm_adjust(p_values)

    rng = np.random.default_rng(RANDOM_SEED + 40000)
    anchor_rows = []
    prediction_matrices = {}
    budget = int(design["primary_anchor_budget"])
    for key in "ABCD":
        n = len(target_y[key])
        embedding = target_x[key].copy()
        scale = np.std(embedding, axis=0, ddof=1)
        embedding = (embedding - np.mean(embedding, axis=0)) / np.where(
            scale > 0, scale, 1.0
        )
        target_matrix = np.full(
            (n, int(design["anchor_draws"])), np.nan, dtype=float
        )
        borrowed_matrix = np.full_like(target_matrix, np.nan)
        for draw in range(int(design["anchor_draws"])):
            anchors = np.sort(rng.choice(n, size=budget, replace=False))
            test_mask = np.ones(n, dtype=bool)
            test_mask[anchors] = False
            test = np.flatnonzero(test_mask)
            target_only = weighted_neighbor_prediction(
                embedding,
                anchors,
                test,
                target_y[key][anchors],
            )
            residual = target_y[key][anchors] - static[key][anchors]
            correction = weighted_neighbor_prediction(
                embedding, anchors, test, residual
            )
            borrowed = static[key][test] + correction
            target_matrix[test, draw] = target_only
            borrowed_matrix[test, draw] = borrowed
            target_metrics = evaluate(
                target_y[key][test],
                target_only,
                design["selection_fraction"],
            )
            borrowed_metrics = evaluate(
                target_y[key][test],
                borrowed,
                design["selection_fraction"],
            )
            anchor_rows.append(
                {
                    "target": key,
                    "draw": draw,
                    "relative_rmse_gain": (
                        target_metrics["rmse"] - borrowed_metrics["rmse"]
                    )
                    / target_metrics["rmse"],
                    "spearman_gain": (
                        borrowed_metrics["spearman"]
                        - target_metrics["spearman"]
                    ),
                    "precision_gain": (
                        borrowed_metrics["precision_best_fraction"]
                        - target_metrics["precision_best_fraction"]
                    ),
                    "regret_reduction": (
                        target_metrics["normalized_simple_regret"]
                        - borrowed_metrics["normalized_simple_regret"]
                    ),
                    "target_only_rmse": target_metrics["rmse"],
                    "borrowed_rmse": borrowed_metrics["rmse"],
                    "target_only_spearman": target_metrics["spearman"],
                    "borrowed_spearman": borrowed_metrics["spearman"],
                    "target_only_precision": target_metrics[
                        "precision_best_fraction"
                    ],
                    "borrowed_precision": borrowed_metrics[
                        "precision_best_fraction"
                    ],
                    "target_only_regret": target_metrics[
                        "normalized_simple_regret"
                    ],
                    "borrowed_regret": borrowed_metrics[
                        "normalized_simple_regret"
                    ],
                }
            )
        prediction_matrices[key] = (target_matrix, borrowed_matrix)

    anchor_table = pd.DataFrame(anchor_rows)
    anchor_table.to_csv(
        RESULTS / "specgen_composition_secondary_anchor_metrics.csv",
        index=False,
    )

    five_label = {}
    decisions = {}
    gate = design["positive_gate"]
    for key in "ABCD":
        subset = anchor_table.loc[anchor_table["target"] == key]
        target_matrix, borrowed_matrix = prediction_matrices[key]
        bootstrap = candidate_bootstrap(
            target_y[key],
            target_matrix,
            borrowed_matrix,
            design["selection_fraction"],
            draws=500,
        )
        pooled_point = pooled_candidate_comparison(
            target_y[key],
            target_matrix,
            borrowed_matrix,
            design["selection_fraction"],
        )
        medians = {
            column: float(subset[column].median())
            for column in [
                "relative_rmse_gain",
                "spearman_gain",
                "precision_gain",
                "regret_reduction",
                "target_only_rmse",
                "borrowed_rmse",
                "target_only_spearman",
                "borrowed_spearman",
                "target_only_precision",
                "borrowed_precision",
                "target_only_regret",
                "borrowed_regret",
            ]
        }
        intervals = {
            metric: {
                "point": pooled_point[metric],
                **quantile_summary(values),
            }
            for metric, values in bootstrap.items()
        }
        five_label[key] = {
            "draw_medians": medians,
            "candidate_bootstrap": intervals,
        }
        zero_pass = (
            zero[key]["spearman"] > gate["zero_label_spearman_gt"]
            and adjusted[key] < gate["holm_shuffled_p_lt"]
        )
        five_pass = (
            medians["relative_rmse_gain"]
            >= gate["five_label_relative_rmse_gain_ge"]
            and medians["spearman_gain"]
            >= gate["five_label_spearman_gain_ge"]
            and medians["borrowed_spearman"]
            > gate["five_label_borrowed_spearman_gt"]
            and intervals["relative_rmse_gain"]["ci95"][0] > 0
            and intervals["spearman_gain"]["ci95"][0] > 0
        )
        decisions[key] = {
            "zero_label_gate": bool(zero_pass),
            "five_label_gate": bool(five_pass),
            "classification": (
                "positive-predictive-and-ranking"
                if zero_pass and five_pass
                else "ranking-only"
                if zero_pass
                else "abstain-or-negative"
            ),
        }

    summary = {
        "status": "complete-post-primary-secondary",
        "design_sha256": sha256(DESIGN_PATH),
        "amendment_sha256": sha256(AMENDMENT),
        "source_skill": source_skill,
        "zero_label": {
            key: {
                **zero[key],
                "shuffled_one_sided_p": p_values[key],
                "shuffled_holm_p": adjusted[key],
            }
            for key in "ABCD"
        },
        "five_label": five_label,
        "decisions": decisions,
        "claim_guard": (
            "Post-primary retrospective secondary result within one published "
            "experimental programme; requires external confirmation."
        ),
    }
    output = RESULTS / "specgen_composition_secondary_summary.json"
    output.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
