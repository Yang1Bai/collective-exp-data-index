"""Evaluate frozen decision utility on held-out experimental candidate pools.

This script deliberately consumes prediction artifacts produced by the earlier
frozen analyses. It does not refit or tune any model. The new estimand is the
fraction of a held-out candidate pool screened before the first true top-5%
candidate is found. See ``ood_decision_borrowing_design.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "ood_decision_borrowing_design.json"
SUMMARY_PATH = RESULTS / "ood_decision_summary.json"
UNITS_PATH = RESULTS / "ood_decision_units.csv"
EDGES_PATH = RESULTS / "ood_decision_edges.csv"
BOOTSTRAP_PATH = RESULTS / "ood_decision_bootstrap.csv"


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - index) * float(value))
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def load_family_rows(edge: dict, control_sources: list[str]) -> pd.DataFrame:
    path = ROOT / edge["prediction_file"]
    wanted_sources = {edge["source"], *control_sources}
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, chunksize=250_000):
        mask = chunk["source"].isin(wanted_sources)
        if "target" in edge and "target" in chunk.columns:
            mask &= chunk["target"].eq(edge["target"])
        # Keep all learner sensitivities for the primary source, but controls
        # only for the frozen primary learner.
        mask &= chunk["source"].eq(edge["source"]) | chunk["learner"].eq(
            edge["learner"]
        )
        selected = chunk.loc[mask].copy()
        if not selected.empty:
            chunks.append(selected)
    if not chunks:
        raise ValueError(f"No prediction rows found for {edge['edge_id']}")
    frame = pd.concat(chunks, ignore_index=True)
    if edge.get("pool_column") == "__single_official_pool__":
        frame["__single_official_pool__"] = "official_pool"
    return frame


def stable_top_set(frame: pd.DataFrame, fraction: float) -> set[str]:
    count = max(1, math.ceil(fraction * len(frame)))
    ordered = frame.sort_values(
        ["y", "identity"], ascending=[False, True], kind="mergesort"
    )
    return set(ordered.iloc[:count]["identity"])


def score_metrics(frame: pd.DataFrame, score_column: str) -> dict[str, float]:
    positives = stable_top_set(frame, 0.05)
    ordered = frame.sort_values(
        [score_column, "identity"], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)
    is_positive = ordered["identity"].isin(positives).to_numpy()
    first_rank = int(np.flatnonzero(is_positive)[0]) + 1
    shortlist_n = max(1, math.ceil(0.10 * len(ordered)))
    shortlist = ordered.iloc[:shortlist_n]
    hits = int(shortlist["identity"].isin(positives).sum())
    prevalence = len(positives) / len(ordered)
    precision = hits / shortlist_n
    recall = hits / len(positives)
    enrichment = precision / prevalence
    rho = float(spearmanr(ordered[score_column], ordered["y"]).statistic)
    if not np.isfinite(rho):
        rho = 0.0
    return {
        "fraction_to_first_hit": first_rank / len(ordered),
        "first_hit_rank": float(first_rank),
        "top10_recall_top5": recall,
        "top10_enrichment": enrichment,
        "top10_regret": float(ordered["y"].max() - shortlist["y"].max()),
        "spearman_rho": rho,
    }


def evaluate_units(frame: pd.DataFrame, edge: dict, source: str, learner: str) -> pd.DataFrame:
    pool_column = edge.get("pool_column", "fold")
    identity_column = edge.get("identity_column", "material_key")
    repeat_column = edge.get("repeat_column", "repeat")
    subset = frame[(frame["source"] == source) & (frame["learner"] == learner)].copy()
    if subset.empty:
        raise ValueError(f"Missing {source!r}, {learner!r} for {edge['edge_id']}")
    required = [repeat_column, pool_column, identity_column, "y", "baseline", "augmented"]
    subset = subset[required].dropna().rename(columns={identity_column: "identity"})
    # A candidate must contribute once to a pool. Median aggregation is a
    # deterministic safeguard for repeated measurement rows.
    subset = (
        subset.groupby([repeat_column, pool_column, "identity"], as_index=False)
        .agg(y=("y", "median"), baseline=("baseline", "median"), augmented=("augmented", "median"))
    )
    rows: list[dict] = []
    for (repeat, pool), group in subset.groupby([repeat_column, pool_column], sort=True):
        minimum_candidate_n = int(edge.get("minimum_candidate_n", 20))
        if len(group) < minimum_candidate_n:
            raise ValueError(
                f"Candidate pool too small ({len(group)}) for {edge['edge_id']} {pool}"
            )
        baseline = score_metrics(group, "baseline")
        augmented = score_metrics(group, "augmented")
        row = {
            "edge_id": edge["edge_id"],
            "source_evaluated": source,
            "learner_evaluated": learner,
            "repeat": int(repeat),
            "pool": str(pool),
            "candidate_n": len(group),
        }
        for key in baseline:
            row[f"baseline_{key}"] = baseline[key]
            row[f"augmented_{key}"] = augmented[key]
        row["effect_fraction_to_first_hit"] = (
            baseline["fraction_to_first_hit"] - augmented["fraction_to_first_hit"]
        )
        row["effect_top10_recall_top5"] = (
            augmented["top10_recall_top5"] - baseline["top10_recall_top5"]
        )
        row["effect_top10_enrichment"] = (
            augmented["top10_enrichment"] - baseline["top10_enrichment"]
        )
        row["effect_top10_regret_reduction"] = (
            baseline["top10_regret"] - augmented["top10_regret"]
        )
        row["effect_spearman_rho"] = (
            augmented["spearman_rho"] - baseline["spearman_rho"]
        )
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_repeats(units: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        column
        for column in units.columns
        if column.startswith("baseline_")
        or column.startswith("augmented_")
        or column.startswith("effect_")
    ]
    rows: list[dict] = []
    for repeat, group in units.groupby("repeat", sort=True):
        weights = group["candidate_n"].to_numpy(float)
        row = {"repeat": int(repeat)}
        for column in numeric:
            row[column] = float(np.average(group[column], weights=weights))
        rows.append(row)
    return pd.DataFrame(rows)


def inference(
    units: pd.DataFrame, *, edge_id: str, bootstrap_replicates: int, sign_flips: int
) -> tuple[dict, pd.DataFrame]:
    repeat = aggregate_repeats(units)
    effects = repeat["effect_fraction_to_first_hit"].to_numpy(float)
    rng = np.random.default_rng(stable_seed(edge_id + ":bootstrap"))
    indices = rng.integers(0, len(effects), size=(bootstrap_replicates, len(effects)))
    bootstrap = effects[indices].mean(axis=1)
    ci = np.quantile(bootstrap, [0.025, 0.975])

    sign_rng = np.random.default_rng(stable_seed(edge_id + ":signflip"))
    observed = float(effects.mean())
    exceed = 0
    remaining = sign_flips
    while remaining:
        batch = min(1000, remaining)
        signs = sign_rng.choice((-1.0, 1.0), size=(batch, len(effects)))
        exceed += int(np.sum((signs * effects).mean(axis=1) >= observed))
        remaining -= batch
    p_value = (exceed + 1) / (sign_flips + 1)

    base_mean = float(repeat["baseline_fraction_to_first_hit"].mean())
    aug_mean = float(repeat["augmented_fraction_to_first_hit"].mean())
    relative = observed / base_mean if base_mean > 0 else float("nan")
    result = {
        "edge_id": edge_id,
        "repeat_n": len(repeat),
        "pool_n": int(units["pool"].nunique()),
        "candidate_rows_per_repeat": float(
            units.groupby("repeat")["candidate_n"].sum().mean()
        ),
        "baseline_fraction_to_first_hit_mean": base_mean,
        "augmented_fraction_to_first_hit_mean": aug_mean,
        "baseline_fraction_to_first_hit_median": float(
            repeat["baseline_fraction_to_first_hit"].median()
        ),
        "augmented_fraction_to_first_hit_median": float(
            repeat["augmented_fraction_to_first_hit"].median()
        ),
        "effect_fraction_to_first_hit_mean": observed,
        "effect_fraction_to_first_hit_bootstrap_95": [float(ci[0]), float(ci[1])],
        "relative_reduction_fraction_to_first_hit": float(relative),
        "fraction_repeat_effects_positive": float(np.mean(effects > 0)),
        "signflip_p_one_sided": float(p_value),
        "baseline_top10_recall_top5_mean": float(
            repeat["baseline_top10_recall_top5"].mean()
        ),
        "augmented_top10_recall_top5_mean": float(
            repeat["augmented_top10_recall_top5"].mean()
        ),
        "baseline_top10_enrichment_mean": float(
            repeat["baseline_top10_enrichment"].mean()
        ),
        "augmented_top10_enrichment_mean": float(
            repeat["augmented_top10_enrichment"].mean()
        ),
        "effect_top10_regret_reduction_mean": float(
            repeat["effect_top10_regret_reduction"].mean()
        ),
        "effect_spearman_rho_mean": float(repeat["effect_spearman_rho"].mean()),
    }
    boot_frame = pd.DataFrame(
        {
            "edge_id": edge_id,
            "bootstrap": np.arange(bootstrap_replicates),
            "effect_fraction_to_first_hit": bootstrap,
        }
    )
    return result, boot_frame


def core_gates(result: dict, adjusted_p: float | None = None) -> dict[str, bool]:
    p_value = result["signflip_p_one_sided"] if adjusted_p is None else adjusted_p
    return {
        "p_le_0_05": bool(p_value <= 0.05),
        "ci_bounded_above_zero": bool(
            result["effect_fraction_to_first_hit_bootstrap_95"][0] > 0
        ),
        "positive_repeat_fraction_ge_0_80": bool(
            result["fraction_repeat_effects_positive"] >= 0.80
        ),
        "relative_reduction_ge_0_25": bool(
            result["relative_reduction_fraction_to_first_hit"] >= 0.25
        ),
    }


def main() -> None:
    design_bytes = DESIGN_PATH.read_bytes()
    design = json.loads(design_bytes)
    bootstrap_replicates = int(design["inference"]["bootstrap_replicates"])
    sign_flips = 9999

    primary = design["primary_edges"]
    secondary = design["secondary_boundaries"]
    families: list[tuple[str, dict]] = [("primary", edge) for edge in primary]
    families += [("secondary", edge) for edge in secondary]

    all_unit_frames: list[pd.DataFrame] = []
    all_boot_frames: list[pd.DataFrame] = []
    result_by_id: dict[str, dict] = {}
    control_ids_by_parent: dict[str, list[str]] = {}
    learner_sensitivity: dict[str, list[dict]] = {}

    for family_name, edge in families:
        if "pool_column" not in edge:
            edge = {
                **edge,
                "pool_column": "fold",
                "repeat_column": "repeat",
                "identity_column": "material_key",
            }
        family_key = (
            "birdshot"
            if edge["edge_id"].startswith("birdshot")
            else "calisol"
            if edge["edge_id"].startswith("calisol")
            else "obelix"
            if edge["edge_id"].startswith("obelix")
            else "kit"
            if edge["edge_id"].startswith("kit")
            else "matbench"
        )
        controls = design["prespecified_controls"][family_key]
        frame = load_family_rows(edge, controls)

        primary_units = evaluate_units(frame, edge, edge["source"], edge["learner"])
        primary_units["analysis_family"] = family_name
        primary_units["edge_role"] = "named-edge"
        primary_result, boot = inference(
            primary_units,
            edge_id=edge["edge_id"],
            bootstrap_replicates=bootstrap_replicates,
            sign_flips=sign_flips,
        )
        primary_result.update(
            {
                "analysis_family": family_name,
                "edge_role": "named-edge",
                "source": edge["source"],
                "learner": edge["learner"],
                "scope": edge.get("ood_definition", edge.get("scope", "")),
            }
        )
        result_by_id[edge["edge_id"]] = primary_result
        all_unit_frames.append(primary_units)
        all_boot_frames.append(boot)

        control_ids: list[str] = []
        for source in controls:
            control_id = edge["edge_id"] + "__control__" + source.replace(" ", "_")
            control_units = evaluate_units(frame, edge, source, edge["learner"])
            control_units["edge_id"] = control_id
            control_units["analysis_family"] = family_name
            control_units["edge_role"] = "control"
            control_result, control_boot = inference(
                control_units,
                edge_id=control_id,
                bootstrap_replicates=bootstrap_replicates,
                sign_flips=sign_flips,
            )
            control_result.update(
                {
                    "analysis_family": family_name,
                    "edge_role": "control",
                    "source": source,
                    "learner": edge["learner"],
                    "scope": "prespecified distant or shuffled control",
                }
            )
            result_by_id[control_id] = control_result
            control_ids.append(control_id)
            all_unit_frames.append(control_units)
            all_boot_frames.append(control_boot)
        control_ids_by_parent[edge["edge_id"]] = control_ids

        sensitivities: list[dict] = []
        for learner in sorted(frame.loc[frame["source"] == edge["source"], "learner"].unique()):
            if learner == edge["learner"]:
                continue
            sensitivity_id = edge["edge_id"] + "__learner__" + learner.replace(" ", "_")
            sensitivity_units = evaluate_units(frame, edge, edge["source"], learner)
            sensitivity_result, _ = inference(
                sensitivity_units,
                edge_id=sensitivity_id,
                bootstrap_replicates=bootstrap_replicates,
                sign_flips=sign_flips,
            )
            sensitivity_result["learner"] = learner
            sensitivities.append(sensitivity_result)
        learner_sensitivity[edge["edge_id"]] = sensitivities

    primary_p = {
        edge["edge_id"]: result_by_id[edge["edge_id"]]["signflip_p_one_sided"]
        for edge in primary
    }
    adjusted = holm_adjust(primary_p)

    # Controls must be classified before their parent edges are allowed to use
    # the prespecified-control gate.
    for result in result_by_id.values():
        if result["edge_role"] != "control":
            continue
        result["gates"] = core_gates(result)
        result["passes_all_core_gates"] = bool(all(result["gates"].values()))
        result["decision_status"] = (
            "control-would-pass-core-gates"
            if result["passes_all_core_gates"]
            else "control-does-not-pass-core-gates"
        )

    for edge_id, result in result_by_id.items():
        if result["edge_role"] == "control":
            continue

        is_primary = result["analysis_family"] == "primary"
        p_for_gate = adjusted[edge_id] if is_primary else result["signflip_p_one_sided"]
        result["holm_p_primary_family"] = adjusted.get(edge_id)
        result["gates"] = core_gates(result, p_for_gate)
        controls_clean = not any(
            result_by_id[control_id].get("passes_all_core_gates", False)
            for control_id in control_ids_by_parent[edge_id]
        )
        result["gates"]["prespecified_controls_clean"] = controls_clean
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
        if improvement and crossing:
            status = "OOD-exploration-rescue" if is_primary else "contextual-screening-rescue"
        elif improvement:
            status = (
                "OOD-exploration-improvement"
                if is_primary
                else "contextual-screening-improvement"
            )
        elif result["effect_fraction_to_first_hit_mean"] > 0:
            status = "directional-only"
        else:
            status = "unresolved-or-harmful"
        result["decision_status"] = status
        result["passes_improvement_gates"] = improvement
        result["passes_rescue_crossing"] = crossing

    units_out = pd.concat(all_unit_frames, ignore_index=True)
    bootstrap_out = pd.concat(all_boot_frames, ignore_index=True)
    edge_rows = pd.DataFrame(result_by_id.values()).sort_values(
        ["analysis_family", "edge_role", "edge_id"]
    )
    # Nested fields remain authoritative in JSON; compact CSV fields are
    # serialized for audit convenience.
    for column in ("effect_fraction_to_first_hit_bootstrap_95", "gates"):
        if column in edge_rows:
            edge_rows[column] = edge_rows[column].map(json.dumps)

    RESULTS.mkdir(parents=True, exist_ok=True)
    units_out.to_csv(UNITS_PATH, index=False)
    edge_rows.to_csv(EDGES_PATH, index=False)
    bootstrap_out.to_csv(BOOTSTRAP_PATH, index=False)

    primary_results = [result_by_id[edge["edge_id"]] for edge in primary]
    secondary_results = [result_by_id[edge["edge_id"]] for edge in secondary]
    controls = [
        result
        for result in result_by_id.values()
        if result["edge_role"] == "control"
    ]
    summary = {
        "analysis_status": "frozen-post-existing-prediction-OOD-decision-extension",
        "design_sha256": hashlib.sha256(design_bytes).hexdigest(),
        "design_frozen_utc": design["frozen_utc"],
        "estimand_scope": design["estimand_scope"],
        "primary_endpoint": design["primary_endpoint"],
        "primary_multiplicity": "Holm across exactly three named independent OOD edges",
        "primary_edges": primary_results,
        "secondary_boundaries": secondary_results,
        "prespecified_controls": controls,
        "learner_sensitivity": learner_sensitivity,
        "claim_boundary": (
            "Decision utility is evaluated on fixed retrospective held-out candidate pools. "
            "A ranking gain need not improve global RMSE and is not a prospective laboratory "
            "acceleration. Only an edge labeled OOD-exploration-rescue passes the frozen "
            "adjusted, stability, practical, control, and shortlist-crossing gates."
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
