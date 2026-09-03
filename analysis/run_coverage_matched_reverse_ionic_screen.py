"""Coverage-matched Caltech -> OBELiX reverse borrowing local screen."""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.localdb.build_localdb import canonical_formula

from audit_caltech_ionic_external_target import (
    COLUMNS,
    TARGET_PATH,
    normalize_dois,
)
from common import RESULTS, composition_features, ensure_output_dirs, sample_groups
from run_knowledge_map import load_task, partition_targets
from run_multi_target_ood_borrowing import (
    DESIGN_PATH as PARENT_DESIGN_PATH,
    assign_group_quartiles,
    make_target_learner,
    regression_metrics,
    stable_seed,
    validate_freeze,
)


DESIGN_PATH = HERE / "coverage_matched_reverse_ionic_design.json"
KNOWLEDGE_MAP_DESIGN = HERE / "knowledge_map_design.json"
OUTPUT = RESULTS / "coverage_matched_reverse_ionic_screen.csv"
SUMMARY = RESULTS / "coverage_matched_reverse_ionic_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_caltech_rows() -> pd.DataFrame:
    raw = pd.read_csv(TARGET_PATH)
    parsed = raw[COLUMNS["formula"]].map(canonical_formula)
    raw["material_key"] = parsed.map(lambda item: item[0])
    raw["value_raw"] = pd.to_numeric(
        raw[COLUMNS["outcome"]], errors="coerce"
    )
    raw["normalized_dois"] = raw[COLUMNS["doi"]].map(normalize_dois)
    return raw[
        raw["material_key"].notna()
        & np.isfinite(raw["value_raw"])
        & (raw["value_raw"] > 0)
    ].copy()


def aggregate_caltech(
    raw: pd.DataFrame,
    target_dois: set[str],
    blocked_keys: set[str],
) -> pd.DataFrame:
    keep = (
        ~raw["material_key"].isin(blocked_keys)
        & ~raw["normalized_dois"].map(
            lambda values: bool(set(values) & target_dois)
        )
    )
    safe = raw.loc[keep].copy()
    safe["value"] = np.log10(safe["value_raw"].astype(float))
    return (
        safe.groupby("material_key", as_index=False)
        .agg(
            value=("value", "median"),
            n_raw=("value", "size"),
        )
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def source_model(seed: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=240,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=-1,
    )


def ensemble_prediction(
    model: ExtraTreesRegressor,
    x: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    members = np.row_stack(
        [estimator.predict(x) for estimator in model.estimators_]
    )
    return members.mean(axis=0), members.std(axis=0, ddof=1)


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    if (OUTPUT.exists() or SUMMARY.exists()) and not args.overwrite:
        raise FileExistsError("Coverage-matched outputs exist; pass --overwrite")

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    parent_ood = json.loads(PARENT_DESIGN_PATH.read_text(encoding="utf-8"))
    parent = json.loads(KNOWLEDGE_MAP_DESIGN.read_text(encoding="utf-8"))
    frozen_hashes = validate_freeze(parent_ood)
    target_id = design["target"]
    target = load_task(target_id, parent["tasks"][target_id])
    te_source = load_task(
        "te_electrical", parent["tasks"]["te_electrical"]
    )
    tasks: dict[str, Any] = {
        target_id: target,
        "te_electrical": te_source,
    }
    subdesign = deepcopy(parent)
    subdesign["targets"] = {
        target_id: deepcopy(parent["targets"][target_id])
    }
    partitions, _ = partition_targets(subdesign, tasks)
    split = partitions[target_id]

    target.X = composition_features(
        target.frame["material_key"].tolist()
    ).astype(np.float32)
    te_source.X = composition_features(
        te_source.frame["material_key"].tolist()
    ).astype(np.float32)
    x = np.asarray(target.X, dtype=float)
    y = target.frame["value"].to_numpy(float)
    evaluation = np.sort(
        np.r_[split["discovery"], split["confirmation"]]
    )
    evaluation_keys = set(
        target.frame.loc[evaluation, "material_key"].astype(str)
    )
    target_dois = set(
        target.frame["source_reference"]
        .dropna()
        .astype(str)
        .str.lower()
    )
    raw_caltech = load_caltech_rows()

    strata = assign_group_quartiles(
        target_id, target, split["development"], evaluation
    )
    scope_by_index = dict(
        zip(strata["entity_index"].astype(int), strata["scope"].astype(str))
    )
    q1 = np.asarray(
        [index for index in evaluation if scope_by_index[int(index)] == "q1"],
        dtype=int,
    )
    q4 = np.asarray(
        [index for index in evaluation if scope_by_index[int(index)] == "q4"],
        dtype=int,
    )
    q1_local = np.flatnonzero(np.isin(evaluation, q1))
    q4_local = np.flatnonzero(np.isin(evaluation, q4))

    development = split["development"]
    development_groups = (
        target.frame.loc[development, "group"].astype(str).to_numpy()
    )
    distance_scaler = StandardScaler().fit(x[development])
    x_development_scaled = distance_scaler.transform(x[development])
    dev_distances = cdist(
        x_development_scaled, x_development_scaled
    )
    np.fill_diagonal(dev_distances, np.inf)
    nn95 = float(np.quantile(dev_distances.min(axis=1), 0.95))

    repeats = args.repeats or int(design["local_repeats"])
    trees = int(parent_ood["learners"]["tree_estimators"])
    base_seed = int(parent_ood["seed"])
    rows: list[dict[str, Any]] = []
    source_audits: list[dict[str, Any]] = []

    for repeat in range(repeats):
        draw_seed = stable_seed(
            base_seed, "coverage-reverse-ionic", str(repeat)
        )
        rng = np.random.default_rng(draw_seed)
        local = sample_groups(
            development_groups, int(split["budget"]), rng
        )
        train = development[local]
        train_keys = set(
            target.frame.loc[train, "material_key"].astype(str)
        )
        blocked_keys = evaluation_keys | train_keys

        caltech = aggregate_caltech(
            raw_caltech, target_dois, blocked_keys
        )
        if len(caltech) < 100:
            raise RuntimeError(
                f"Only {len(caltech)} leakage-safe Caltech entities"
            )
        caltech_x = composition_features(
            caltech["material_key"].tolist()
        ).astype(np.float32)
        caltech_model = source_model(
            stable_seed(draw_seed, "caltech-source")
        ).fit(caltech_x, caltech["value"].to_numpy(float))
        caltech_mean, caltech_std = ensemble_prediction(
            caltech_model, x
        )
        source_scaled = distance_scaler.transform(caltech_x)
        target_scaled = distance_scaler.transform(x)
        nearest_distance = cdist(
            target_scaled, source_scaled
        ).min(axis=1)
        reliability = np.exp(
            -nearest_distance / max(nn95, 1e-12)
        )
        uncertainty_scale = float(
            np.median(caltech_std[development])
        )
        reliability /= 1.0 + caltech_std / max(
            uncertainty_scale, 1e-12
        )
        coverage_features = np.column_stack([
            caltech_mean,
            caltech_std,
            nearest_distance,
            reliability,
            caltech_mean * reliability,
        ])

        te_keep = ~te_source.frame["material_key"].isin(
            blocked_keys
        )
        te_indices = np.flatnonzero(te_keep.to_numpy())
        te_model = source_model(
            stable_seed(draw_seed, "te-source")
        ).fit(
            np.asarray(te_source.X)[te_indices],
            te_source.frame.loc[te_keep, "value"].to_numpy(float),
        )
        te_prediction = te_model.predict(x)
        shuffled = caltech_mean[
            np.random.default_rng(
                stable_seed(draw_seed, "shuffle")
            ).permutation(len(caltech_mean))
        ]
        method_features = {
            "caltech_same_endpoint_scalar": caltech_mean[:, None],
            "caltech_coverage_aware": coverage_features,
            "te_electrical_zero_coverage_control": te_prediction[:, None],
            "shuffled_caltech_control": shuffled[:, None],
        }
        source_audits.append({
            "repeat": repeat,
            "caltech_entities": len(caltech),
            "caltech_q4_coverage_fraction": float(
                np.mean(nearest_distance[q4] <= nn95)
            ),
            "caltech_q4_median_distance": float(
                np.median(nearest_distance[q4])
            ),
            "target_development_nn95": nn95,
            "caltech_median_ensemble_sd": float(
                np.median(caltech_std)
            ),
        })

        for learner_name in design["target_learners"]:
            model_seed = stable_seed(
                draw_seed, learner_name, "target"
            )
            baseline = make_target_learner(
                learner_name, model_seed, trees
            ).fit(x[train], y[train])
            baseline_prediction = baseline.predict(x)
            for method, features in method_features.items():
                augmented_x = np.column_stack([x, features])
                augmented = make_target_learner(
                    learner_name, model_seed, trees
                ).fit(augmented_x[train], y[train])
                augmented_prediction = augmented.predict(
                    augmented_x
                )
                q1_metrics = regression_metrics(
                    y[q1],
                    baseline_prediction[q1],
                    augmented_prediction[q1],
                )
                q4_metrics = regression_metrics(
                    y[q4],
                    baseline_prediction[q4],
                    augmented_prediction[q4],
                )
                rows.append({
                    "target": target_id,
                    "method": method,
                    "learner": learner_name,
                    "repeat": repeat,
                    "train_n": len(train),
                    "source_entities": len(caltech)
                    if method.startswith("caltech")
                    else len(te_indices),
                    "q1_relative_rmse_gain": q1_metrics[
                        "relative_rmse_gain"
                    ],
                    "q4_relative_rmse_gain": q4_metrics[
                        "relative_rmse_gain"
                    ],
                    "gain_specific": q4_metrics[
                        "relative_rmse_gain"
                    ] - q1_metrics["relative_rmse_gain"],
                    "q4_r2": q4_metrics["aug_r2"],
                })

    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT, index=False)
    grouped = (
        frame.groupby(["target", "method"], as_index=False)
        .agg(
            q1_relative_rmse_gain=("q1_relative_rmse_gain", "mean"),
            q4_relative_rmse_gain=("q4_relative_rmse_gain", "mean"),
            gain_specific=("gain_specific", "mean"),
            q4_r2=("q4_r2", "mean"),
            positive_q4_fraction=(
                "q4_relative_rmse_gain",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            cells=("q4_r2", "size"),
        )
        .sort_values("method")
    )
    summary = {
        "status": "coverage-matched-reverse-ionic-local-screen-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_guard": design["claim_guard"],
        "frozen_hashes": frozen_hashes,
        "repeats": repeats,
        "rows": len(frame),
        "source_audits": source_audits,
        "grouped_results": grouped.to_dict(orient="records"),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(grouped.to_string(index=False), flush=True)
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
