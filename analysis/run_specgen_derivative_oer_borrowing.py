"""Run the frozen SpecGen derivative-system OER borrowing benchmark."""
from __future__ import annotations

import hashlib
import json
import math
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
ARCHIVE = ROOT / "Dataset" / "ref6" / "44160_2025_983_MOESM4_ESM.zip"
DESIGN_PATH = ANALYSIS / "specgen_derivative_oer_borrowing_design.json"
MEMBERS = {
    "source": "SpecGen/data/data.xlsx",
    "A": "SpecGen/data/transfer_A.xlsx",
    "B": "SpecGen/data/transfer_B.xlsx",
    "C": "SpecGen/data/transfer_C.xlsx",
    "D": "SpecGen/data/transfer_D.xlsx",
}
RANDOM_SEED = 20260730


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_member(payload: bytes) -> dict[str, pd.DataFrame]:
    frames = {}
    for sheet in ("UV", "metals", "overpotential"):
        frame = pd.read_excel(BytesIO(payload), sheet_name=sheet, header=0)
        frames[sheet] = frame.apply(pd.to_numeric, errors="raise")
    return frames


def make_model(kind: str, parameter: float | int) -> Pipeline:
    if kind == "pls":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    PLSRegression(
                        n_components=int(parameter),
                        scale=False,
                        max_iter=2000,
                    ),
                ),
            ]
        )
    if kind == "pca_ridge":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                ("pca", PCA(n_components=0.995, svd_solver="full")),
                ("model", Ridge(alpha=float(parameter))),
            ]
        )
    raise ValueError(kind)


def flat_prediction(model: Pipeline, x: np.ndarray) -> np.ndarray:
    return np.asarray(model.predict(x), dtype=float).reshape(-1)


def spearman(y: np.ndarray, prediction: np.ndarray) -> float:
    value = stats.spearmanr(y, prediction).statistic
    return float(value) if np.isfinite(value) else 0.0


def evaluate(y: np.ndarray, prediction: np.ndarray, fraction: float) -> dict[str, float]:
    y = np.asarray(y, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    if len(y) != len(prediction) or len(y) < 3:
        raise AssertionError("Metric arrays are invalid")
    k = max(1, int(math.ceil(fraction * len(y))))
    selected = np.argsort(prediction)[:k]
    truth = set(np.argsort(y)[:k].tolist())
    iqr = float(np.quantile(y, 0.75) - np.quantile(y, 0.25))
    scale = iqr if iqr > 0 else float(np.std(y))
    scale = scale if scale > 0 else 1.0
    return {
        "rmse": float(mean_squared_error(y, prediction) ** 0.5),
        "mae": float(mean_absolute_error(y, prediction)),
        "spearman": spearman(y, prediction),
        "precision_best_fraction": float(
            len(truth & set(selected.tolist())) / k
        ),
        "normalized_simple_regret": float(
            (float(np.min(y[selected])) - float(np.min(y))) / scale
        ),
    }


def weighted_neighbor_prediction(
    embedding: np.ndarray,
    anchor_indices: np.ndarray,
    test_indices: np.ndarray,
    anchor_values: np.ndarray,
    neighbors: int = 3,
) -> np.ndarray:
    anchor_x = embedding[anchor_indices]
    test_x = embedding[test_indices]
    distances = np.sqrt(
        np.maximum(
            0.0,
            np.sum((test_x[:, None, :] - anchor_x[None, :, :]) ** 2, axis=2),
        )
    )
    count = min(neighbors, len(anchor_indices))
    nearest = np.argpartition(distances, kth=count - 1, axis=1)[:, :count]
    nearest_distances = np.take_along_axis(distances, nearest, axis=1)
    weights = 1.0 / np.maximum(nearest_distances, 1e-8)
    values = anchor_values[nearest]
    return np.sum(weights * values, axis=1) / np.sum(weights, axis=1)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    adjusted = {}
    running = 0.0
    total = len(ordered)
    for rank, key in enumerate(ordered):
        value = min(1.0, (total - rank) * p_values[key])
        running = max(running, value)
        adjusted[key] = running
    return adjusted


def source_model_selection(
    x: np.ndarray, y: np.ndarray, design: dict
) -> tuple[dict, Pipeline, pd.DataFrame, np.ndarray]:
    candidates = [
        ("pls", component)
        for component in design["source_model_candidates"]["pls_components"]
    ] + [
        ("pca_ridge", alpha)
        for alpha in design["source_model_candidates"]["pca_ridge_alpha"]
    ]
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    rows = []
    predictions = {}
    for kind, parameter in candidates:
        model = make_model(kind, parameter)
        prediction = np.asarray(
            cross_val_predict(model, x, y, cv=cv, n_jobs=1)
        ).reshape(-1)
        key = f"{kind}|{parameter}"
        predictions[key] = prediction
        rows.append(
            {
                "kind": kind,
                "parameter": parameter,
                "oof_mae_mV": float(mean_absolute_error(y, prediction)),
                "oof_rmse_mV": float(mean_squared_error(y, prediction) ** 0.5),
                "oof_r2": float(r2_score(y, prediction)),
                "oof_spearman": spearman(y, prediction),
            }
        )
    table = pd.DataFrame(rows).sort_values(
        ["oof_mae_mV", "kind", "parameter"], ignore_index=True
    )
    winner = table.iloc[0].to_dict()
    selected = make_model(str(winner["kind"]), winner["parameter"])
    selected.fit(x, y)
    selected_parameter = (
        int(winner["parameter"])
        if winner["kind"] == "pls"
        else float(winner["parameter"])
    )
    key = f"{winner['kind']}|{selected_parameter}"
    return winner, selected, table, predictions[key]


def candidate_bootstrap(
    y: np.ndarray,
    target_predictions: np.ndarray,
    borrowed_predictions: np.ndarray,
    fraction: float,
    draws: int = 500,
) -> dict[str, list[float]]:
    """Bootstrap candidate identities while retaining all splits per candidate."""
    rng = np.random.default_rng(RANDOM_SEED + 9901)
    candidate_count, split_count = target_predictions.shape
    result = {
        "relative_rmse_gain": [],
        "spearman_gain": [],
    }
    for _ in range(draws):
        sampled = rng.integers(0, candidate_count, size=candidate_count)
        y_parts = []
        target_parts = []
        borrowed_parts = []
        for candidate in sampled:
            valid = np.isfinite(target_predictions[candidate])
            if not np.any(valid):
                continue
            y_parts.append(np.repeat(y[candidate], int(valid.sum())))
            target_parts.append(target_predictions[candidate, valid])
            borrowed_parts.append(borrowed_predictions[candidate, valid])
        boot_y = np.concatenate(y_parts)
        boot_target = np.concatenate(target_parts)
        boot_borrowed = np.concatenate(borrowed_parts)
        target_metrics = evaluate(boot_y, boot_target, fraction)
        borrowed_metrics = evaluate(boot_y, boot_borrowed, fraction)
        result["relative_rmse_gain"].append(
            (target_metrics["rmse"] - borrowed_metrics["rmse"])
            / target_metrics["rmse"]
        )
        result["spearman_gain"].append(
            borrowed_metrics["spearman"] - target_metrics["spearman"]
        )
    return result


def pooled_candidate_comparison(
    y: np.ndarray,
    target_predictions: np.ndarray,
    borrowed_predictions: np.ndarray,
    fraction: float,
) -> dict[str, float]:
    repeated_y = np.repeat(y[:, None], target_predictions.shape[1], axis=1)
    valid = np.isfinite(target_predictions) & np.isfinite(borrowed_predictions)
    target_metrics = evaluate(
        repeated_y[valid], target_predictions[valid], fraction
    )
    borrowed_metrics = evaluate(
        repeated_y[valid], borrowed_predictions[valid], fraction
    )
    return {
        "relative_rmse_gain": (
            target_metrics["rmse"] - borrowed_metrics["rmse"]
        )
        / target_metrics["rmse"],
        "spearman_gain": (
            borrowed_metrics["spearman"] - target_metrics["spearman"]
        ),
    }


def quantile_summary(values: list[float] | np.ndarray) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "median": float(np.median(array)),
        "ci95": [
            float(np.quantile(array, 0.025)),
            float(np.quantile(array, 0.975)),
        ],
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    with ZipFile(ARCHIVE) as archive:
        payloads = {key: archive.read(member) for key, member in MEMBERS.items()}
    data = {key: read_member(payload) for key, payload in payloads.items()}

    source_x = data["source"]["UV"].to_numpy(dtype=float)
    source_composition = data["source"]["metals"].to_numpy(dtype=float)
    source_y = (
        data["source"]["overpotential"].iloc[:, 0].to_numpy(dtype=float) - 1.23
    ) * 1000.0
    winner, selected_model, source_table, source_oof = source_model_selection(
        source_x, source_y, design
    )
    source_table.to_csv(
        RESULTS / "specgen_derivative_source_model_selection.csv", index=False
    )

    source_skill = {
        "selected_kind": str(winner["kind"]),
        "selected_parameter": float(winner["parameter"]),
        "oof_mae_mV": float(mean_absolute_error(source_y, source_oof)),
        "oof_rmse_mV": float(mean_squared_error(source_y, source_oof) ** 0.5),
        "oof_r2": float(r2_score(source_y, source_oof)),
        "oof_spearman": spearman(source_y, source_oof),
    }
    if source_skill["oof_r2"] <= design["positive_gate"]["source_oof_r2_gt"]:
        raise AssertionError("Frozen donor source-skill gate failed")

    composition_model = ExtraTreesRegressor(
        n_estimators=1000,
        min_samples_leaf=2,
        max_features=1.0,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    ).fit(source_composition, source_y)

    target_x = {
        key: data[key]["UV"].to_numpy(dtype=float) for key in "ABCD"
    }
    target_y = {
        key: (
            data[key]["overpotential"].iloc[:, 0].to_numpy(dtype=float) - 1.23
        )
        * 1000.0
        for key in "ABCD"
    }
    static_prediction = {
        key: flat_prediction(selected_model, target_x[key]) for key in "ABCD"
    }
    composition_prediction = {
        key: composition_model.predict(
            data[key]["metals"].to_numpy(dtype=float)
        )
        for key in "ABCD"
    }

    # The source PCA creates a fixed outcome-free spectral state representation.
    source_scaler = StandardScaler().fit(source_x)
    source_scaled = source_scaler.transform(source_x)
    state_pca = PCA(n_components=0.995, svd_solver="full").fit(source_scaled)
    embeddings = {}
    for key in "ABCD":
        scores = state_pca.transform(source_scaler.transform(target_x[key]))
        # Target-only scaling is outcome-free and prevents a shifted component
        # from dominating all within-recipient neighbor distances.
        scale = np.std(scores, axis=0, ddof=1)
        embeddings[key] = (scores - np.mean(scores, axis=0)) / np.where(
            scale > 0, scale, 1.0
        )

    zero_rows = []
    for key in "ABCD":
        static_metrics = evaluate(
            target_y[key],
            static_prediction[key],
            design["selection_fraction"],
        )
        composition_metrics = evaluate(
            target_y[key],
            composition_prediction[key],
            design["selection_fraction"],
        )
        zero_rows.append(
            {
                "target": key,
                "method": "static_spectral_donor",
                **static_metrics,
            }
        )
        zero_rows.append(
            {
                "target": key,
                "method": "composition_only_donor",
                **composition_metrics,
            }
        )

    # Refit the selected source architecture under a matched shuffled-label null.
    def one_shuffle(seed_offset: int) -> dict[str, float]:
        rng = np.random.default_rng(RANDOM_SEED + 10000 + seed_offset)
        shuffled = rng.permutation(source_y)
        model = make_model(str(winner["kind"]), winner["parameter"])
        model.fit(source_x, shuffled)
        return {
            key: spearman(target_y[key], flat_prediction(model, target_x[key]))
            for key in "ABCD"
        }

    shuffled_path = (
        RESULTS / "specgen_derivative_shuffled_source_spearman.csv"
    )
    expected_seeds = [
        RANDOM_SEED + 10000 + offset
        for offset in range(int(design["source_shuffle_seeds"]))
    ]
    if shuffled_path.exists():
        shuffled_table = pd.read_csv(shuffled_path)
        if (
            shuffled_table["seed"].astype(int).tolist() != expected_seeds
            or any(key not in shuffled_table for key in "ABCD")
        ):
            raise AssertionError("Cached spectral shuffled-source table changed")
    else:
        shuffled_records = joblib.Parallel(n_jobs=-1, verbose=0)(
            joblib.delayed(one_shuffle)(offset)
            for offset in range(int(design["source_shuffle_seeds"]))
        )
        shuffled_table = pd.DataFrame(shuffled_records)
        shuffled_table.insert(0, "seed", expected_seeds)
        shuffled_table.to_csv(shuffled_path, index=False)

    observed_zero = {
        row["target"]: row["spearman"]
        for row in zero_rows
        if row["method"] == "static_spectral_donor"
    }
    zero_p = {
        key: float(
            (
                1
                + np.sum(
                    shuffled_table[key].to_numpy(dtype=float)
                    >= observed_zero[key]
                )
            )
            / (len(shuffled_table) + 1)
        )
        for key in "ABCD"
    }
    zero_holm = holm_adjust(zero_p)
    for row in zero_rows:
        if row["method"] == "static_spectral_donor":
            row["shuffled_one_sided_p"] = zero_p[row["target"]]
            row["shuffled_holm_p"] = zero_holm[row["target"]]
    pd.DataFrame(zero_rows).to_csv(
        RESULTS / "specgen_derivative_zero_label_metrics.csv", index=False
    )

    rng = np.random.default_rng(RANDOM_SEED)
    anchor_rows = []
    primary_prediction_matrices = {}
    for key in "ABCD":
        n = len(target_y[key])
        for budget in design["anchor_budgets"]:
            target_matrix = np.full(
                (n, int(design["anchor_draws"])), np.nan, dtype=float
            )
            borrowed_matrix = np.full_like(target_matrix, np.nan)
            for draw in range(int(design["anchor_draws"])):
                anchors = np.sort(rng.choice(n, size=int(budget), replace=False))
                mask = np.ones(n, dtype=bool)
                mask[anchors] = False
                test = np.flatnonzero(mask)
                target_only = weighted_neighbor_prediction(
                    embeddings[key],
                    anchors,
                    test,
                    target_y[key][anchors],
                )
                residuals = target_y[key][anchors] - static_prediction[key][anchors]
                residual_correction = weighted_neighbor_prediction(
                    embeddings[key],
                    anchors,
                    test,
                    residuals,
                )
                borrowed = static_prediction[key][test] + residual_correction
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
                        "budget": int(budget),
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
            if int(budget) == int(design["primary_anchor_budget"]):
                primary_prediction_matrices[key] = (
                    target_matrix,
                    borrowed_matrix,
                )

    anchor_table = pd.DataFrame(anchor_rows)
    anchor_table.to_csv(
        RESULTS / "specgen_derivative_anchor_draw_metrics.csv", index=False
    )

    primary_summaries = {}
    for key in "ABCD":
        subset = anchor_table.loc[
            (anchor_table["target"] == key)
            & (
                anchor_table["budget"]
                == int(design["primary_anchor_budget"])
            )
        ]
        target_matrix, borrowed_matrix = primary_prediction_matrices[key]
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
        primary_summaries[key] = {
            "draw_medians": {
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
            },
            "candidate_bootstrap": {
                metric: {
                    "point": pooled_point[metric],
                    **quantile_summary(values),
                }
                for metric, values in bootstrap.items()
            },
        }

    gate = design["positive_gate"]
    decisions = {}
    for key in "ABCD":
        zero = next(
            row
            for row in zero_rows
            if row["target"] == key
            and row["method"] == "static_spectral_donor"
        )
        summary = primary_summaries[key]
        medians = summary["draw_medians"]
        bootstrap = summary["candidate_bootstrap"]
        zero_pass = (
            zero["spearman"] > gate["zero_label_spearman_gt"]
            and zero["shuffled_holm_p"] < gate["holm_shuffled_p_lt"]
        )
        five_pass = (
            medians["relative_rmse_gain"]
            >= gate["five_label_relative_rmse_gain_ge"]
            and medians["spearman_gain"]
            >= gate["five_label_spearman_gain_ge"]
            and medians["borrowed_spearman"]
            > gate["five_label_borrowed_spearman_gt"]
            and bootstrap["relative_rmse_gain"]["ci95"][0] > 0
            and bootstrap["spearman_gain"]["ci95"][0] > 0
        )
        if zero_pass and five_pass:
            classification = "positive-predictive-and-ranking"
        elif zero_pass:
            classification = "ranking-only"
        else:
            classification = "abstain-or-negative"
        decisions[key] = {
            "zero_label_gate": bool(zero_pass),
            "five_label_gate": bool(five_pass),
            "classification": classification,
        }

    summary = {
        "status": "complete",
        "design_sha256": sha256(DESIGN_PATH),
        "archive_sha256": sha256(ARCHIVE),
        "source_skill": source_skill,
        "zero_label": {
            row["target"]: row
            for row in zero_rows
            if row["method"] == "static_spectral_donor"
        },
        "five_label": primary_summaries,
        "decisions": decisions,
        "claim_guard": design["claim_guard"],
    }
    summary_path = RESULTS / "specgen_derivative_oer_borrowing_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    complete = {
        "status": "verified-complete-internal",
        "summary_sha256": sha256(summary_path),
        "source_model_rows": int(len(source_table)),
        "zero_label_rows": int(len(zero_rows)),
        "anchor_metric_rows": int(len(anchor_table)),
        "shuffle_rows": int(len(shuffled_table)),
        "decisions": decisions,
        "claim_guard": design["claim_guard"],
    }
    (RESULTS / "specgen_derivative_oer_borrowing_complete.json").write_text(
        json.dumps(complete, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
