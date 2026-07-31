"""Post-outcome exploratory hard coverage gate for Caltech -> OBELiX."""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler

from common import RESULTS, composition_features, ensure_output_dirs, sample_groups
from run_coverage_matched_reverse_ionic_screen import (
    aggregate_caltech,
    ensemble_prediction,
    load_caltech_rows,
    source_model,
)
from run_knowledge_map import load_task, partition_targets
from run_multi_target_ood_borrowing import (
    DESIGN_PATH as PARENT_OOD_DESIGN,
    assign_group_quartiles,
    make_target_learner,
    regression_metrics,
    stable_seed,
    validate_freeze,
)


HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "coverage_gated_reverse_ionic_design.json"
MAP_DESIGN_PATH = HERE / "knowledge_map_design.json"
OUTPUT = RESULTS / "coverage_gated_reverse_ionic_screen.csv"
SUMMARY = RESULTS / "coverage_gated_reverse_ionic_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    if (OUTPUT.exists() or SUMMARY.exists()) and not args.overwrite:
        raise FileExistsError("Coverage-gated outputs exist; pass --overwrite")

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    parent_ood = json.loads(PARENT_OOD_DESIGN.read_text(encoding="utf-8"))
    parent = json.loads(MAP_DESIGN_PATH.read_text(encoding="utf-8"))
    frozen_hashes = validate_freeze(parent_ood)
    target_id = "electrolyte_conductivity"
    target = load_task(target_id, parent["tasks"][target_id])
    subdesign = deepcopy(parent)
    subdesign["targets"] = {
        target_id: deepcopy(parent["targets"][target_id])
    }
    partitions, _ = partition_targets(
        subdesign, {target_id: target}
    )
    split = partitions[target_id]
    target.X = composition_features(
        target.frame["material_key"].tolist()
    ).astype(np.float32)
    x = np.asarray(target.X, dtype=float)
    y = target.frame["value"].to_numpy(float)
    development = split["development"]
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
        target_id, target, development, evaluation
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

    scaler = StandardScaler().fit(x[development])
    x_development_scaled = scaler.transform(x[development])
    development_distances = cdist(
        x_development_scaled, x_development_scaled
    )
    np.fill_diagonal(development_distances, np.inf)
    threshold = float(
        np.quantile(development_distances.min(axis=1), 0.95)
    )
    development_groups = (
        target.frame.loc[development, "group"].astype(str).to_numpy()
    )
    trees = int(parent_ood["learners"]["tree_estimators"])
    base_seed = int(parent_ood["seed"])
    rows: list[dict[str, object]] = []

    for repeat in range(int(design["local_repeats"])):
        draw_seed = stable_seed(
            base_seed, "coverage-hard-gate", str(repeat)
        )
        rng = np.random.default_rng(draw_seed)
        local = sample_groups(
            development_groups, int(split["budget"]), rng
        )
        train = development[local]
        train_keys = set(
            target.frame.loc[train, "material_key"].astype(str)
        )
        caltech = aggregate_caltech(
            raw_caltech,
            target_dois,
            evaluation_keys | train_keys,
        )
        source_x = composition_features(
            caltech["material_key"].tolist()
        ).astype(np.float32)
        model = source_model(
            stable_seed(draw_seed, "caltech-source")
        ).fit(source_x, caltech["value"].to_numpy(float))
        source_mean, source_sd = ensemble_prediction(model, x)
        nearest_distance = cdist(
            scaler.transform(x), scaler.transform(source_x)
        ).min(axis=1)
        covered = nearest_distance <= threshold
        reliability = np.exp(
            -nearest_distance / max(threshold, 1e-12)
        )
        reliability /= 1.0 + source_sd / max(
            float(np.median(source_sd[development])), 1e-12
        )
        rich_features = np.column_stack([
            source_mean,
            source_sd,
            nearest_distance,
            reliability,
            source_mean * reliability,
        ])
        shuffled = source_mean[
            np.random.default_rng(
                stable_seed(draw_seed, "shuffle")
            ).permutation(len(source_mean))
        ]
        features = {
            "caltech_scalar_hard_coverage_gate": source_mean[:, None],
            "caltech_features_hard_coverage_gate": rich_features,
            "shuffled_caltech_hard_coverage_gate": shuffled[:, None],
        }

        for learner_name in design["target_learners"]:
            model_seed = stable_seed(
                draw_seed, learner_name, "target"
            )
            baseline_model = make_target_learner(
                learner_name, model_seed, trees
            ).fit(x[train], y[train])
            baseline = baseline_model.predict(x)
            for method, donor_features in features.items():
                augmented_x = np.column_stack([x, donor_features])
                augmented_model = make_target_learner(
                    learner_name, model_seed, trees
                ).fit(augmented_x[train], y[train])
                augmented = augmented_model.predict(augmented_x)
                gated = np.where(covered, augmented, baseline)
                for scope, index in [
                    ("q1", q1),
                    ("q4", q4),
                    ("q4_covered", q4[covered[q4]]),
                ]:
                    if len(index) < 3:
                        continue
                    metrics = regression_metrics(
                        y[index], baseline[index], gated[index]
                    )
                    rows.append({
                        "target": target_id,
                        "method": method,
                        "learner": learner_name,
                        "repeat": repeat,
                        "scope": scope,
                        "entities": len(index),
                        "coverage_fraction": float(
                            np.mean(covered[index])
                        ),
                        "relative_rmse_gain": metrics[
                            "relative_rmse_gain"
                        ],
                        "augmented_r2": metrics["aug_r2"],
                    })

    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT, index=False)
    grouped = (
        frame.groupby(["method", "scope"], as_index=False)
        .agg(
            relative_rmse_gain=("relative_rmse_gain", "mean"),
            augmented_r2=("augmented_r2", "mean"),
            positive_fraction=(
                "relative_rmse_gain",
                lambda values: float(np.mean(np.asarray(values) > 0)),
            ),
            coverage_fraction=("coverage_fraction", "mean"),
            cells=("relative_rmse_gain", "size"),
        )
        .sort_values(["method", "scope"])
    )
    summary = {
        "status": "coverage-gated-reverse-ionic-exploratory-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_guard": design["claim_guard"],
        "frozen_hashes": frozen_hashes,
        "threshold": threshold,
        "rows": len(frame),
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
