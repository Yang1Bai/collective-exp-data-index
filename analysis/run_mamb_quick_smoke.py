"""Quick, outcome-informed screen for multi-donor mechanism bundles.

This is not the confirmatory MAMB implementation.  It reuses the frozen
multi-target partitions and asks whether concatenating the already fitted,
leakage-excluded donor predictions can carry more OOD information than the
single designated donor.  The result is used only to decide whether the full
nested, abstaining implementation is worth computing.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from common import RESULTS, ensure_output_dirs, sample_groups
from run_knowledge_map import (
    build_feature_spaces,
    fit_source_models,
    load_task,
    partition_targets,
)
from run_multi_target_ood_borrowing import (
    DESIGN_PATH as PARENT_DESIGN_PATH,
    assign_group_quartiles,
    make_target_learner,
    regression_metrics,
    stable_seed,
    validate_freeze,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
KNOWLEDGE_MAP_DESIGN = HERE / "knowledge_map_design.json"
OUTPUT = RESULTS / "mamb_quick_smoke.csv"
SUMMARY = RESULTS / "mamb_quick_smoke_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_output_dirs()
    if (OUTPUT.exists() or SUMMARY.exists()) and not args.overwrite:
        raise FileExistsError("Quick-smoke outputs already exist; pass --overwrite")

    parent_ood = json.loads(PARENT_DESIGN_PATH.read_text(encoding="utf-8"))
    frozen_hashes = validate_freeze(parent_ood)
    parent = json.loads(KNOWLEDGE_MAP_DESIGN.read_text(encoding="utf-8"))
    included = parent_ood["eligibility"]["included_targets"]

    needed = set(parent["targets"])
    for target_spec in parent["targets"].values():
        needed.update(edge["task"] for edge in target_spec["sources"])
    tasks = {
        task_id: load_task(task_id, spec)
        for task_id, spec in parent["tasks"].items()
        if task_id in needed
    }
    build_feature_spaces(tasks)
    partitions, _ = partition_targets(deepcopy(parent), tasks)
    analysis_parent = deepcopy(parent)
    analysis_parent["targets"] = {
        target: deepcopy(parent["targets"][target]) for target in included
    }
    donor_models, _ = fit_source_models(analysis_parent, tasks, partitions)

    learners = [
        parent_ood["learners"]["primary"],
        *parent_ood["learners"]["sensitivities"],
    ]
    rows: list[dict[str, object]] = []
    base_seed = int(parent_ood["seed"])

    for target in included:
        task = tasks[target]
        evaluation = np.sort(
            np.r_[
                partitions[target]["discovery"],
                partitions[target]["confirmation"],
            ]
        )
        strata = assign_group_quartiles(
            target,
            task,
            partitions[target]["development"],
            evaluation,
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
        edges = analysis_parent["targets"][target]["sources"]
        signals = {
            edge["task"]: np.asarray(
                donor_models[(target, edge["task"])].predict(np.asarray(task.X)),
                dtype=float,
            )
            for edge in edges
        }
        primary = parent_ood["targets"][target]["primary_source"]
        mechanism_bundle = [
            edge["task"]
            for edge in edges
            if int(edge.get("neighborhood", 0)) >= 1
            and edge["relation"] != "distant-control"
        ] or [primary]
        bundles = {
            "primary": [primary],
            "mechanism_bundle": mechanism_bundle,
            "all_five": list(signals),
        }

        development = partitions[target]["development"]
        budget = int(partitions[target]["budget"])
        groups = task.frame.loc[development, "group"].astype(str).to_numpy()
        y = task.frame["value"].to_numpy(float)
        x = np.asarray(task.X, dtype=float)

        for repeat in range(args.repeats):
            rng = np.random.default_rng(
                stable_seed(base_seed, target, "target-draw", str(repeat))
            )
            local = sample_groups(groups, budget, rng)
            train = development[local]
            for learner_name in learners:
                model_seed = stable_seed(
                    base_seed, target, learner_name, str(repeat)
                )
                baseline = make_target_learner(
                    learner_name,
                    model_seed,
                    int(parent_ood["learners"]["tree_estimators"]),
                ).fit(x[train], y[train])
                baseline_prediction = baseline.predict(x)
                for method, sources in bundles.items():
                    augmented_x = np.column_stack(
                        [x, *[signals[source] for source in sources]]
                    )
                    augmented = make_target_learner(
                        learner_name,
                        model_seed,
                        int(parent_ood["learners"]["tree_estimators"]),
                    ).fit(augmented_x[train], y[train])
                    augmented_prediction = augmented.predict(augmented_x)
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
                    rows.append(
                        {
                            "target": target,
                            "method": method,
                            "learner": learner_name,
                            "repeat": repeat,
                            "train_n": len(train),
                            "sources": "|".join(sources),
                            "q1_relative_rmse_gain": q1_metrics[
                                "relative_rmse_gain"
                            ],
                            "q4_relative_rmse_gain": q4_metrics[
                                "relative_rmse_gain"
                            ],
                            "gain_specific": q4_metrics["relative_rmse_gain"]
                            - q1_metrics["relative_rmse_gain"],
                            "q4_r2": q4_metrics["aug_r2"],
                        }
                    )

    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT, index=False)
    grouped = (
        frame.groupby(["target", "method", "sources"], as_index=False)
        .agg(
            q1_relative_rmse_gain=("q1_relative_rmse_gain", "mean"),
            q4_relative_rmse_gain=("q4_relative_rmse_gain", "mean"),
            gain_specific=("gain_specific", "mean"),
            q4_r2=("q4_r2", "mean"),
            cells=("q4_r2", "size"),
        )
        .sort_values(["target", "method"])
    )
    promising = grouped[
        (grouped["method"] == "mechanism_bundle")
        & (grouped["q4_relative_rmse_gain"] >= 0.05)
        & (grouped["gain_specific"] > 0)
        & (grouped["q4_r2"] > 0)
    ]
    summary = {
        "status": "quick-smoke-complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_guard": (
            "Three target-draw repeats and three learners form a screening "
            "diagnostic after prior outcomes were inspected. No interval, "
            "multiplicity correction, nested bundle selection or independent "
            "target confirmation is provided."
        ),
        "frozen_hashes": frozen_hashes,
        "targets": len(included),
        "learners": learners,
        "repeats": args.repeats,
        "rows": len(frame),
        "promising_mechanism_bundles": promising.to_dict(orient="records"),
        "grouped_results": grouped.to_dict(orient="records"),
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(grouped.to_string(index=False))
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

