"""Exploratory, frozen composition-distance hard-OOD decision analysis."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from common import ELEMENTS, composition_features, load_obelix, load_property
from run_ood_decision_borrowing import (
    aggregate_repeats,
    core_gates,
    evaluate_units,
    holm_adjust,
    inference,
    load_family_rows,
)


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "hard_ood_composition_design.json"


def fraction_features(keys: list[str]) -> np.ndarray:
    return composition_features(keys)[:, : len(ELEMENTS)]


def nearest_l1(test_keys: list[str], train_keys: list[str]) -> np.ndarray:
    if not train_keys:
        raise ValueError("A hard-OOD pool has no target-domain reference compositions")
    test_x = fraction_features(test_keys)
    train_x = fraction_features(train_keys)
    return np.abs(test_x[:, None, :] - train_x[None, :, :]).sum(axis=2).min(axis=1)


def birdshot_references() -> dict[str, list[str]]:
    raw = load_property("birdshot-high-entropy-alloy-campaign", "Yield Strength (MPa)")
    parsed = raw["conditions_json"].map(json.loads)
    raw["year"] = parsed.map(lambda item: int(float(item["campaign_year"])))
    raw = raw[raw["value"] > 0]
    frame = raw.groupby(["year", "material_key"], as_index=False)["value"].median()
    return {
        "year1_to_year2": sorted(frame.loc[frame["year"] == 1, "material_key"].unique()),
        "years1_2_to_year3": sorted(
            frame.loc[frame["year"].isin([1, 2]), "material_key"].unique()
        ),
    }


def build_membership(frame: pd.DataFrame, edge: dict, fraction: float) -> pd.DataFrame:
    pool_column = edge["pool_column"]
    identity_column = edge["identity_column"]
    primary = frame[
        (frame["source"] == edge["source"]) & (frame["learner"] == edge["learner"])
    ].copy()
    candidates = primary[[pool_column, identity_column]].drop_duplicates()
    candidates = candidates.rename(columns={identity_column: "identity"})

    if edge["edge_id"].startswith("hard_ood_birdshot"):
        references = birdshot_references()
    elif edge["edge_id"].startswith("hard_ood_matbench"):
        universe = set(candidates["identity"])
        references = {
            str(pool): sorted(universe - set(group["identity"]))
            for pool, group in candidates.groupby(pool_column)
        }
    elif edge["edge_id"].startswith("hard_ood_obelix"):
        target = load_obelix()
        references = {
            "official_pool": sorted(
                target.loc[target["split"] == "train", "material_key"].unique()
            )
        }
    else:
        raise ValueError(edge["edge_id"])

    rows: list[dict] = []
    for pool, group in candidates.groupby(pool_column, sort=True):
        pool_name = str(pool)
        test_keys = sorted(group["identity"].unique())
        reference = sorted(set(references[pool_name]) - set(test_keys))
        distances = nearest_l1(test_keys, reference)
        local = pd.DataFrame(
            {"pool": pool_name, "identity": test_keys, "nearest_target_l1": distances}
        ).sort_values(
            ["nearest_target_l1", "identity"],
            ascending=[False, True],
            kind="mergesort",
        )
        selected_n = max(1, math.ceil(fraction * len(local)))
        local["hard_ood_rank"] = np.arange(1, len(local) + 1)
        local["hard_ood_selected"] = local["hard_ood_rank"] <= selected_n
        local["candidate_pool_n"] = len(local)
        local["hard_ood_n"] = selected_n
        local["target_reference_n"] = len(reference)
        rows.extend(local.to_dict("records"))
    return pd.DataFrame(rows)


def filter_hard_ood(frame: pd.DataFrame, edge: dict, membership: pd.DataFrame) -> pd.DataFrame:
    selected = membership[membership["hard_ood_selected"]][["pool", "identity"]]
    pool_column = edge["pool_column"]
    identity_column = edge["identity_column"]
    output = frame.merge(
        selected,
        left_on=[pool_column, identity_column],
        right_on=["pool", "identity"],
        how="inner",
        validate="many_to_one",
    )
    return output.drop(columns=["pool", "identity"])


def main() -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    design = json.loads(design_bytes)
    bootstrap_replicates = int(design["inference"]["bootstrap_replicates"])
    sign_flips = int(design["inference"]["sign_flip_draws"])
    hard_fraction = float(design["distance"]["fraction"])

    memberships: list[pd.DataFrame] = []
    unit_frames: list[pd.DataFrame] = []
    boot_frames: list[pd.DataFrame] = []
    results: dict[str, dict] = {}
    controls_by_parent: dict[str, list[str]] = {}
    sensitivities: dict[str, list[dict]] = {}

    for edge in design["primary_family"]:
        frame = load_family_rows(edge, edge["controls"])
        membership = build_membership(frame, edge, hard_fraction)
        membership.insert(0, "edge_id", edge["edge_id"])
        memberships.append(membership)
        hard = filter_hard_ood(frame, edge, membership)

        units = evaluate_units(hard, edge, edge["source"], edge["learner"])
        units["edge_role"] = "named-edge"
        result, boot = inference(
            units,
            edge_id=edge["edge_id"],
            bootstrap_replicates=bootstrap_replicates,
            sign_flips=sign_flips,
        )
        result.update(
            {
                "edge_role": "named-edge",
                "source": edge["source"],
                "learner": edge["learner"],
                "parent_edge_id": edge["parent_edge_id"],
                "hard_ood_fraction": hard_fraction,
            }
        )
        results[edge["edge_id"]] = result
        unit_frames.append(units)
        boot_frames.append(boot)

        control_ids: list[str] = []
        for source in edge["controls"]:
            control_id = edge["edge_id"] + "__control__" + source.replace(" ", "_")
            control_units = evaluate_units(hard, edge, source, edge["learner"])
            control_units["edge_id"] = control_id
            control_units["edge_role"] = "control"
            control_result, control_boot = inference(
                control_units,
                edge_id=control_id,
                bootstrap_replicates=bootstrap_replicates,
                sign_flips=sign_flips,
            )
            control_result.update(
                {
                    "edge_role": "control",
                    "source": source,
                    "learner": edge["learner"],
                    "parent_edge_id": edge["edge_id"],
                    "hard_ood_fraction": hard_fraction,
                }
            )
            results[control_id] = control_result
            control_ids.append(control_id)
            unit_frames.append(control_units)
            boot_frames.append(control_boot)
        controls_by_parent[edge["edge_id"]] = control_ids

        learner_rows: list[dict] = []
        for learner in sorted(hard.loc[hard["source"] == edge["source"], "learner"].unique()):
            if learner == edge["learner"]:
                continue
            sensitivity_id = edge["edge_id"] + "__learner__" + learner.replace(" ", "_")
            sensitivity_units = evaluate_units(hard, edge, edge["source"], learner)
            sensitivity_result, _ = inference(
                sensitivity_units,
                edge_id=sensitivity_id,
                bootstrap_replicates=bootstrap_replicates,
                sign_flips=sign_flips,
            )
            sensitivity_result["learner"] = learner
            learner_rows.append(sensitivity_result)
        sensitivities[edge["edge_id"]] = learner_rows

    primary_p = {
        edge["edge_id"]: results[edge["edge_id"]]["signflip_p_one_sided"]
        for edge in design["primary_family"]
    }
    adjusted = holm_adjust(primary_p)

    for result in results.values():
        if result["edge_role"] != "control":
            continue
        result["gates"] = core_gates(result)
        result["passes_all_core_gates"] = bool(all(result["gates"].values()))
        result["decision_status"] = (
            "control-would-pass-core-gates"
            if result["passes_all_core_gates"]
            else "control-does-not-pass-core-gates"
        )

    for edge in design["primary_family"]:
        edge_id = edge["edge_id"]
        result = results[edge_id]
        result["holm_p_primary_family"] = adjusted[edge_id]
        result["gates"] = core_gates(result, adjusted[edge_id])
        result["gates"]["prespecified_controls_clean"] = not any(
            results[control_id]["passes_all_core_gates"]
            for control_id in controls_by_parent[edge_id]
        )
        improvement = bool(all(result["gates"].values()))
        crossing = bool(
            result["baseline_fraction_to_first_hit_median"] > 0.10
            and result["augmented_fraction_to_first_hit_median"] <= 0.10
        )
        result["gates"]["baseline_above_shortlist_boundary"] = bool(
            result["baseline_fraction_to_first_hit_median"] > 0.10
        )
        result["gates"]["augmented_within_shortlist_boundary"] = bool(
            result["augmented_fraction_to_first_hit_median"] <= 0.10
        )
        result["passes_improvement_gates"] = improvement
        result["passes_rescue_crossing"] = crossing
        if improvement and crossing:
            status = "exploratory-hard-OOD-rescue"
        elif improvement:
            status = "exploratory-hard-OOD-improvement"
        elif result["effect_fraction_to_first_hit_mean"] > 0:
            status = "exploratory-directional-only"
        else:
            status = "exploratory-unresolved-or-harmful"
        result["decision_status"] = status

    membership_out = pd.concat(memberships, ignore_index=True)
    units_out = pd.concat(unit_frames, ignore_index=True)
    bootstrap_out = pd.concat(boot_frames, ignore_index=True)
    edges_out = pd.DataFrame(results.values()).sort_values(["edge_role", "edge_id"])
    for column in ("effect_fraction_to_first_hit_bootstrap_95", "gates"):
        edges_out[column] = edges_out[column].map(json.dumps)

    membership_out.to_csv(RESULTS / "hard_ood_composition_membership.csv", index=False)
    units_out.to_csv(RESULTS / "hard_ood_decision_units.csv", index=False)
    bootstrap_out.to_csv(RESULTS / "hard_ood_decision_bootstrap.csv", index=False)
    edges_out.to_csv(RESULTS / "hard_ood_decision_edges.csv", index=False)

    summary = {
        "analysis_status": "frozen-exploratory-hard-OOD-after-whole-pool-result",
        "design_sha256": hashlib.sha256(design_bytes).hexdigest(),
        "design_frozen_utc": design["frozen_utc"],
        "selection_history": design["selection_history"],
        "distance": design["distance"],
        "primary_edges": [results[edge["edge_id"]] for edge in design["primary_family"]],
        "controls": [result for result in results.values() if result["edge_role"] == "control"],
        "learner_sensitivity": sensitivities,
        "claim_guard": design["claim_guard"],
    }
    (RESULTS / "hard_ood_decision_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
