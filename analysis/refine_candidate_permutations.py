"""Uniformly refine permutation resolution for all discovery-selected edges.

The first knowledge-map run used 99 feature-mapping permutations, so a raw
minimum p-value of 0.01 could only become 0.05 after Holm correction across the
five selected edges.  This post-discovery amendment applies 999 permutations
to every selected edge without changing selection, folds, training samples,
models, effect thresholds, or the family of hypotheses.
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from common import RESULTS, ensure_output_dirs, holm_adjust
from run_knowledge_map import (
    DESIGN_PATH,
    build_feature_spaces,
    feature_permutation_test,
    fit_source_models,
    load_task,
    partition_targets,
    stable_offset,
    training_samples,
)

REFINED_PERMUTATIONS = 999


def main() -> None:
    warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")
    ensure_output_dirs()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    discovery = pd.read_csv(RESULTS / "knowledge_map_discovery.csv")
    selected = discovery[discovery["selected_for_internal_confirmation"].astype(bool)].copy()
    candidate_keys = list(zip(selected["target"], selected["source"]))
    if len(candidate_keys) != 5:
        raise AssertionError(f"Expected the frozen five selected edges, found {len(candidate_keys)}")

    print("Reconstructing frozen tasks and partitions", flush=True)
    tasks = {task_id: load_task(task_id, spec) for task_id, spec in design["tasks"].items()}
    build_feature_spaces(tasks)
    partitions, _ = partition_targets(design, tasks)
    models, _ = fit_source_models(design, tasks, partitions)

    base_seed = int(design["seed"])
    permutation_repeats = int(design["inference"]["permutation_training_repeats"])
    rows = []
    null_frames = []
    for target_id, source_id in candidate_keys:
        print(f"999-permutation refinement: {source_id} -> {target_id}", flush=True)
        split = partitions[target_id]
        samples = training_samples(
            split["development"], split["budget"], int(design["inference"]["confirmation_repeats"]),
            base_seed + stable_offset(f"{target_id}:confirmation") % 1_000_000,
        )[:permutation_repeats]
        feature = np.asarray(models[(target_id, source_id)].predict(np.asarray(tasks[target_id].X)), dtype=float)
        pvalue, null = feature_permutation_test(
            tasks[target_id], feature, samples, split["confirmation"], 0.0,
            REFINED_PERMUTATIONS,
            base_seed + stable_offset(f"permutation:{target_id}:{source_id}") % 1_000_000,
        )
        rows.append({"target": target_id, "source": source_id, "permutation_p_raw_refined": pvalue})
        null["target"] = target_id
        null["source"] = source_id
        null_frames.append(null)

    refined = pd.DataFrame(rows)
    refined["permutation_p_holm_refined"] = holm_adjust(refined["permutation_p_raw_refined"])
    refined["permutations"] = REFINED_PERMUTATIONS
    refined["amendment"] = "uniform-post-discovery-resolution-refinement"
    refined.to_csv(RESULTS / "knowledge_map_permutation_refined.csv", index=False)
    pd.concat(null_frames, ignore_index=True).to_csv(
        RESULTS / "knowledge_map_permutation_null_refined.csv", index=False
    )

    edges = pd.read_csv(RESULTS / "knowledge_map_edges.csv").merge(
        refined, on=["target", "source"], how="left"
    )
    statuses = []
    for _, row in edges.iterrows():
        if (
            bool(row["discovery_selected"])
            and row["relative_rmse_improvement_mean"] >= design["inference"]["confirmed_min_relative_rmse"]
            and row["relative_rmse_ci_lo"] > 0
            and pd.notna(row["permutation_p_holm_refined"])
            and row["permutation_p_holm_refined"] < 0.05
            and row["target_sample_fraction_saved"] >= design["inference"]["confirmed_min_target_sample_fraction_saved"]
            and row["learners_positive_of_three"] >= 2
            and row["source_group_cv_r2_mean"] > 0
        ):
            status = "internally-confirmed-awaits-external-replication"
        else:
            status = row["edge_status"]
        statuses.append(status)
    edges["edge_status_refined"] = statuses
    edges.to_csv(RESULTS / "knowledge_map_edges_refined.csv", index=False)

    print("\nRefined permutation decisions")
    print(refined.to_string(index=False))
    print("\nRefined internally admitted edges awaiting external replication")
    print(edges.loc[
        edges["edge_status_refined"] == "internally-confirmed-awaits-external-replication",
        ["target", "source", "relative_rmse_improvement_mean", "target_sample_fraction_saved", "permutation_p_holm_refined"],
    ].to_string(index=False))


if __name__ == "__main__":
    main()
