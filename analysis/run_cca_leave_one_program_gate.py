"""Run the frozen leave-one-target-program-out CCA gate benchmark.

This is explicitly outcome-informed method development.  The outer prediction
for each programme is trained without any edge outcome from that programme.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"
DESIGN_PATH = ANALYSIS / "cca_leave_one_program_gate_design.json"
SEED = 20260720
BOOTSTRAPS = 10_000

EDGE_OUT = RESULTS / "cca_leave_one_program_edge_panel.csv"
PRED_OUT = RESULTS / "cca_leave_one_program_predictions.csv"
POLICY_OUT = RESULTS / "cca_leave_one_program_policy_summary.csv"
CONTRAST_OUT = RESULTS / "cca_leave_one_program_contrasts.csv"
SUMMARY_OUT = RESULTS / "cca_leave_one_program_summary.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def number(value, default=np.nan) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float(default)
    return out if np.isfinite(out) else float(default)


def first_number(row: pd.Series, columns: list[str], default=np.nan) -> float:
    for column in columns:
        value = number(row.get(column), np.nan)
        if np.isfinite(value):
            return value
    return float(default)


def programme_for_target(target: str) -> str:
    mapping = {
        "te_zt": "internal_te",
        "alloy_ys": "internal_alloy",
        "catalysis_h2": "internal_catalysis",
        "electrolyte_conductivity": "internal_obelix",
        "solubility": "internal_aqueous",
        "hydration": "internal_aqueous",
        "photo_z_pipi": "internal_photoswitch",
        "polymer_tensile": "internal_openpoly",
        "polymer_tm": "internal_openpoly",
        "birdshot_ys": "external_birdshot",
        "birdshot_uts": "external_birdshot",
        "birdshot_hardness": "external_birdshot",
        "matbench_steel_ys": "external_matbench",
        "kit_conductivity_minus_30_C": "kit_temperature",
        "calisol_conductivity_minus_40_C": "calisol_temperature",
    }
    if target not in mapping:
        raise KeyError(f"No programme mapping for target {target!r}")
    return mapping[target]


def temperature_neighborhood(relation: str, distance: float) -> float:
    if "shuffled" in relation:
        return 0.0
    if relation == "adjacent-condition-primary":
        return 3.0
    if relation == "temperature-distance-control":
        if distance <= 10:
            return 3.0
        if distance <= 30:
            return 2.0
        if distance <= 60:
            return 1.0
        return 0.0
    return np.nan


def feature_flags(
    *,
    relation: str,
    neighborhood: float,
    source_quality: float,
    target_domain: str,
    source_domain: str,
    evidence_set: str,
) -> dict[str, float | bool]:
    relation_lower = relation.lower()
    shuffled = "shuffled" in relation_lower
    distant_wrong = any(token in relation_lower for token in ("distant", "wrong"))
    same_domain = bool(target_domain and source_domain and target_domain == source_domain)
    same_domain = same_domain or "same-domain" in relation_lower or "same-reaction" in relation_lower
    adjacent_condition = "condition" in relation_lower or "temperature" in relation_lower
    cross_dataset = (
        "independent" in evidence_set.lower()
        or "cross-dataset" in relation_lower
        or "cross-domain" in relation_lower
    )
    strong_neighbor = neighborhood >= 2 and not distant_wrong and not shuffled
    credible_positive = source_quality > 0
    return {
        "neighborhood_scaled": float(np.clip(neighborhood / 3.0, 0.0, 1.0)),
        "source_quality_clipped": float(np.clip(source_quality, -1.0, 1.0)),
        "credible_positive": float(credible_positive),
        "strong_neighbor": float(strong_neighbor),
        "same_domain": float(same_domain),
        "adjacent_condition": float(adjacent_condition),
        "cross_dataset": float(cross_dataset),
        "distant_wrong": float(distant_wrong),
        "shuffled": float(shuffled),
    }


def base_edge_panel() -> list[dict]:
    frame = pd.read_csv(RESULTS / "knowledge_map_synthesis_edges.csv")
    rows: list[dict] = []
    for _, source_row in frame.iterrows():
        target = str(source_row["target"])
        source = str(source_row["source"])
        relation = str(source_row.get("relation") or "")
        neighborhood = number(source_row.get("neighborhood"), np.nan)
        distance = number(source_row.get("absolute_temperature_distance_C"), np.nan)
        if not np.isfinite(neighborhood):
            neighborhood = temperature_neighborhood(relation, distance)
        if not np.isfinite(neighborhood):
            neighborhood = 0.0
        source_quality = first_number(
            source_row,
            [
                "source_group_cv_r2_mean",
                "source_pooled_oof_r2",
                "source_pooled_article_oof_r2",
            ],
            default=0.0,
        )
        effect = number(source_row.get("relative_rmse_improvement_mean"))
        if not np.isfinite(effect):
            raise AssertionError(f"Missing effect for {target} <- {source}")
        ci_lo = number(source_row.get("relative_rmse_ci_lo"), np.nan)
        ci_hi = number(source_row.get("relative_rmse_ci_hi"), np.nan)
        aug_r2 = first_number(source_row, ["pooled_aug_r2", "aug_r2_mean"], default=np.nan)
        evidence_set = str(source_row.get("evidence_set") or "historical-synthesis")
        target_domain = str(source_row.get("target_domain") or "")
        source_domain = str(source_row.get("source_domain") or "")
        flags = feature_flags(
            relation=relation,
            neighborhood=neighborhood,
            source_quality=source_quality,
            target_domain=target_domain,
            source_domain=source_domain,
            evidence_set=evidence_set,
        )
        rows.append(
            {
                "edge_id": f"{target}__{source}",
                "programme": programme_for_target(target),
                "target_task": target,
                "source": source,
                "evidence_set": evidence_set,
                "relation": relation,
                "target_domain": target_domain,
                "source_domain": source_domain,
                "neighborhood": neighborhood,
                "source_quality_r2": source_quality,
                "effect_relative_rmse": effect,
                "effect_ci_lo": ci_lo,
                "effect_ci_hi": ci_hi,
                "augmented_r2": aug_r2,
                "reported_status": str(
                    source_row.get("synthesis_status")
                    or source_row.get("edge_status_refined")
                    or source_row.get("edge_status")
                    or ""
                ),
                **flags,
            }
        )
    return rows


def paired_primary_effects(
    metrics_path: Path,
    filters: dict[str, object],
    methods: dict[str, dict],
    source_quality: dict[str, float],
    target_task: str,
    programme: str,
    plate: str | None = None,
) -> list[dict]:
    frame = pd.read_csv(metrics_path)
    for column, expected in filters.items():
        frame = frame.loc[frame[column] == expected]
    if plate is not None:
        frame = frame.loc[frame["plate"].astype(str) == str(plate)]
    required = ["target_only", *methods.keys()]
    frame = frame.loc[frame["method"].isin(required)]
    index_columns = ["repeat"]
    if plate is not None:
        index_columns.insert(0, "plate")
    rmse = frame.pivot(index=index_columns, columns="method", values="rmse")
    r2 = frame.pivot(index=index_columns, columns="method", values="r2")
    missing = set(required) - set(rmse.columns)
    if missing:
        raise AssertionError(f"Missing primary methods in {metrics_path.name}: {sorted(missing)}")
    if len(rmse) != 100:
        raise AssertionError(f"Expected 100 paired repeats, found {len(rmse)} for {target_task}")
    rows: list[dict] = []
    base = rmse["target_only"].to_numpy(dtype=float)
    for method, metadata in methods.items():
        gain = (base - rmse[method].to_numpy(dtype=float)) / base
        source = metadata["source"]
        quality_key = metadata.get("quality_key", source)
        quality = float(source_quality[quality_key])
        neighborhood = float(metadata["neighborhood"])
        relation = str(metadata["relation"])
        flags = feature_flags(
            relation=relation,
            neighborhood=neighborhood,
            source_quality=quality,
            target_domain=str(metadata.get("target_domain", "")),
            source_domain=str(metadata.get("source_domain", "")),
            evidence_set=str(metadata["evidence_set"]),
        )
        rows.append(
            {
                "edge_id": f"{target_task}__{source}",
                "programme": programme,
                "target_task": target_task,
                "source": source,
                "evidence_set": metadata["evidence_set"],
                "relation": relation,
                "target_domain": metadata.get("target_domain", ""),
                "source_domain": metadata.get("source_domain", ""),
                "neighborhood": neighborhood,
                "source_quality_r2": quality,
                "effect_relative_rmse": float(np.mean(gain)),
                "effect_ci_lo": float(np.quantile(gain, 0.025)),
                "effect_ci_hi": float(np.quantile(gain, 0.975)),
                "augmented_r2": float(r2[method].mean()),
                "reported_status": "outcome-unseen-primary-cell-source-specific",
                **flags,
            }
        )
    return rows


def outcome_unseen_edges() -> list[dict]:
    star_quality_frame = pd.read_csv(RESULTS / "starrydata_reverse_source_quality.csv")
    star_quality = dict(zip(star_quality_frame["source"], star_quality_frame["oof_r2"]))
    star_quality["wrong_max"] = float(
        star_quality_frame.loc[
            star_quality_frame["source"].str.contains("wrong"), "oof_r2"
        ].max()
    )
    star_quality["neighbor_mean"] = float(
        star_quality_frame.loc[
            star_quality_frame["source"].isin(
                ["obelix_adjacent_ionic", "caltech_adjacent_ionic"]
            ),
            "oof_r2",
        ].mean()
    )
    star_methods = {
        "same_domain_estm_frozen_stack": {
            "source": "estm_same_domain",
            "neighborhood": 3,
            "relation": "cross-dataset-same-domain",
            "evidence_set": "outcome-unseen-starrydata",
            "target_domain": "thermoelectric",
            "source_domain": "thermoelectric",
        },
        "obelix_adjacent_frozen_stack": {
            "source": "obelix_adjacent_ionic",
            "neighborhood": 2,
            "relation": "cross-domain-transport",
            "evidence_set": "outcome-unseen-starrydata",
            "target_domain": "thermoelectric",
            "source_domain": "solid electrolyte",
        },
        "caltech_adjacent_frozen_stack": {
            "source": "caltech_adjacent_ionic",
            "neighborhood": 2,
            "relation": "cross-domain-transport",
            "evidence_set": "outcome-unseen-starrydata",
            "target_domain": "thermoelectric",
            "source_domain": "solid electrolyte",
        },
        "wrong_source_frozen_stack": {
            "source": "wrong_source_control",
            "quality_key": "wrong_max",
            "neighborhood": 0,
            "relation": "wrong-domain-control",
            "evidence_set": "outcome-unseen-starrydata",
            "target_domain": "thermoelectric",
            "source_domain": "wrong",
        },
        "shuffled_source_frozen_stack": {
            "source": "shuffled_neighbor_control",
            "quality_key": "neighbor_mean",
            "neighborhood": 0,
            "relation": "shuffled-source-control",
            "evidence_set": "outcome-unseen-starrydata",
            "target_domain": "thermoelectric",
            "source_domain": "transport",
        },
    }
    rows = paired_primary_effects(
        RESULTS / "starrydata_reverse_metrics.csv",
        {
            "budget": 30,
            "learner": "extra_trees",
            "representation": "composition",
            "scope": "ood_q4",
        },
        star_methods,
        star_quality,
        target_task="starrydata_reverse_zt",
        programme="starrydata_reverse",
    )

    tri_quality_frame = pd.read_csv(RESULTS / "tri_oer_source_quality.csv")
    tri_quality = dict(zip(tri_quality_frame["source"], tri_quality_frame["oof_r2"]))
    tri_quality["wrong_max"] = float(
        tri_quality_frame.loc[
            tri_quality_frame["source"].str.contains("wrong"), "oof_r2"
        ].max()
    )
    tri_quality["neighbor_mean"] = float(
        tri_quality_frame.loc[
            tri_quality_frame["source"].isin(
                [
                    "acid_oer_same_reaction",
                    "orr_adjacent_oxygen_electrocatalysis",
                    "ocx_adjacent_electrocatalysis",
                ]
            ),
            "oof_r2",
        ].mean()
    )
    tri_methods = {
        "acid_same_reaction_frozen_stack": {
            "source": "acid_oer_same_reaction",
            "neighborhood": 3,
            "relation": "cross-dataset-same-reaction",
            "evidence_set": "outcome-unseen-tri-oer",
            "target_domain": "oxygen evolution electrocatalysis",
            "source_domain": "oxygen evolution electrocatalysis",
        },
        "orr_adjacent_frozen_stack": {
            "source": "orr_adjacent_oxygen_electrocatalysis",
            "neighborhood": 2,
            "relation": "cross-dataset-adjacent-electrocatalysis",
            "evidence_set": "outcome-unseen-tri-oer",
            "target_domain": "oxygen evolution electrocatalysis",
            "source_domain": "oxygen reduction electrocatalysis",
        },
        "ocx_adjacent_frozen_stack": {
            "source": "ocx_adjacent_electrocatalysis",
            "neighborhood": 2,
            "relation": "cross-dataset-adjacent-electrocatalysis",
            "evidence_set": "outcome-unseen-tri-oer",
            "target_domain": "oxygen evolution electrocatalysis",
            "source_domain": "carbon dioxide electrocatalysis",
        },
        "wrong_source_frozen_stack": {
            "source": "wrong_source_control",
            "quality_key": "wrong_max",
            "neighborhood": 0,
            "relation": "wrong-domain-control",
            "evidence_set": "outcome-unseen-tri-oer",
            "target_domain": "oxygen evolution electrocatalysis",
            "source_domain": "wrong",
        },
        "shuffled_source_frozen_stack": {
            "source": "shuffled_neighbor_control",
            "quality_key": "neighbor_mean",
            "neighborhood": 0,
            "relation": "shuffled-source-control",
            "evidence_set": "outcome-unseen-tri-oer",
            "target_domain": "oxygen evolution electrocatalysis",
            "source_domain": "electrocatalysis",
        },
    }
    for plate in ["3496", "3851", "3860", "4098"]:
        rows.extend(
            paired_primary_effects(
                RESULTS / "tri_oer_metrics.csv",
                {
                    "budget": 30,
                    "learner": "extra_trees",
                    "representation": "element_fraction",
                    "scope": "dynamic_ood_q4",
                },
                tri_methods,
                tri_quality,
                target_task=f"tri_oer_plate_{plate}",
                programme="tri_oer",
                plate=plate,
            )
        )
    return rows


FEATURES = [
    "neighborhood_scaled",
    "source_quality_clipped",
    "credible_positive",
    "strong_neighbor",
    "same_domain",
    "adjacent_condition",
    "cross_dataset",
    "distant_wrong",
    "shuffled",
]


def leave_one_program_predictions(edges: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for programme in sorted(edges["programme"].unique()):
        train = edges.loc[edges["programme"] != programme].copy()
        test = edges.loc[edges["programme"] == programme].copy()
        counts = train.groupby("programme")["edge_id"].transform("count")
        weights = 1.0 / counts.to_numpy(dtype=float)
        x_train = train[FEATURES].to_numpy(dtype=float)
        x_test = test[FEATURES].to_numpy(dtype=float)
        mean = np.average(x_train, axis=0, weights=weights)
        variance = np.average((x_train - mean) ** 2, axis=0, weights=weights)
        scale = np.sqrt(variance)
        scale[scale < 1e-12] = 1.0
        x_train = (x_train - mean) / scale
        x_test = (x_test - mean) / scale
        y_train = train["effect_relative_rmse"].to_numpy(dtype=float)
        y_mean = float(np.average(y_train, weights=weights))
        sqrt_weight = np.sqrt(weights)[:, None]
        weighted_x = x_train * sqrt_weight
        weighted_y = (y_train - y_mean) * sqrt_weight[:, 0]
        penalty = 10.0 * np.eye(weighted_x.shape[1])
        coefficients = np.linalg.solve(
            weighted_x.T @ weighted_x + penalty,
            weighted_x.T @ weighted_y,
        )
        test["predicted_gain_lopo"] = y_mean + x_test @ coefficients
        test["gate_eligible"] = (
            (test["credible_positive"] == 1)
            & (test["strong_neighbor"] == 1)
            & (test["distant_wrong"] == 0)
            & (test["shuffled"] == 0)
        )
        test["gate_admitted"] = test["gate_eligible"] & (
            test["predicted_gain_lopo"] > 0
        )
        test["held_out_programme"] = programme
        parts.append(test)
    predictions = pd.concat(parts, ignore_index=True)
    if not (predictions["programme"] == predictions["held_out_programme"]).all():
        raise AssertionError("Outer programme assignment mismatch")
    return predictions


def select_row(group: pd.DataFrame, policy: str) -> pd.Series | None:
    candidates = group.copy()
    if policy == "never_borrow":
        return None
    if policy == "cca_meta":
        candidates = candidates.loc[candidates["gate_admitted"]]
        if candidates.empty:
            return None
        return candidates.sort_values(
            ["predicted_gain_lopo", "source_quality_r2"], ascending=False
        ).iloc[0]
    if policy == "cca_rule":
        candidates = candidates.loc[
            (candidates["credible_positive"] == 1)
            & (candidates["strong_neighbor"] == 1)
            & (candidates["distant_wrong"] == 0)
            & (candidates["shuffled"] == 0)
        ]
        if candidates.empty:
            return None
        return candidates.sort_values(
            ["neighborhood", "source_quality_r2"], ascending=False
        ).iloc[0]
    if policy == "always_best_credibility":
        candidates = candidates.loc[candidates["shuffled"] == 0]
        return candidates.sort_values("source_quality_r2", ascending=False).iloc[0]
    if policy == "adjacency_only":
        return candidates.sort_values(
            ["neighborhood", "source_quality_r2"], ascending=False
        ).iloc[0]
    if policy == "credibility_only":
        candidates = candidates.loc[candidates["credible_positive"] == 1]
        if candidates.empty:
            return None
        return candidates.sort_values("source_quality_r2", ascending=False).iloc[0]
    if policy == "oracle_upper_bound":
        candidates = candidates.loc[candidates["effect_relative_rmse"] > 0]
        if candidates.empty:
            return None
        return candidates.sort_values("effect_relative_rmse", ascending=False).iloc[0]
    raise KeyError(policy)


POLICIES = [
    "cca_meta",
    "cca_rule",
    "always_best_credibility",
    "adjacency_only",
    "credibility_only",
    "never_borrow",
    "oracle_upper_bound",
]


def policy_decisions(predictions: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    grouped = predictions.groupby(["programme", "target_task"], sort=True)
    for (programme, target_task), group in grouped:
        task_has_clear_benefit = bool((group["effect_ci_lo"] > 0).any())
        for policy in POLICIES:
            selected = select_row(group, policy)
            admitted = selected is not None
            records.append(
                {
                    "programme": programme,
                    "target_task": target_task,
                    "policy": policy,
                    "admitted": admitted,
                    "selected_edge_id": "" if selected is None else selected["edge_id"],
                    "selected_source": "" if selected is None else selected["source"],
                    "utility": 0.0
                    if selected is None
                    else float(selected["effect_relative_rmse"]),
                    "point_harm": False
                    if selected is None
                    else bool(selected["effect_relative_rmse"] < 0),
                    "clear_harm": False
                    if selected is None
                    else bool(selected["effect_ci_hi"] < 0),
                    "clear_benefit": False
                    if selected is None
                    else bool(selected["effect_ci_lo"] > 0),
                    "augmented_r2": np.nan
                    if selected is None
                    else float(selected["augmented_r2"]),
                    "positive_absolute_r2": False
                    if selected is None or not np.isfinite(selected["augmented_r2"])
                    else bool(selected["augmented_r2"] > 0),
                    "task_has_clear_benefit": task_has_clear_benefit,
                }
            )
    return pd.DataFrame(records)


def cluster_bootstrap(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    indices = rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))
    samples = values[indices].mean(axis=1)
    return float(np.quantile(samples, 0.025)), float(np.quantile(samples, 0.975))


def exact_sign_flip_p(values: np.ndarray) -> float:
    observed = float(np.mean(values))
    if observed <= 0:
        return 1.0
    signs = np.asarray(list(itertools.product([-1.0, 1.0], repeat=len(values))))
    null = (signs * values[None, :]).mean(axis=1)
    return float(np.mean(null >= observed - 1e-15))


def holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    m = len(p_values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * p_values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def summarize_policies(decisions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    programme = (
        decisions.groupby(["programme", "policy"], as_index=False)
        .agg(
            utility=("utility", "mean"),
            task_coverage=("admitted", "mean"),
            any_admission=("admitted", "max"),
            point_harm_rate=("point_harm", "mean"),
            clear_harm_rate=("clear_harm", "mean"),
            clear_benefit_rate=("clear_benefit", "mean"),
            positive_absolute_r2_rate=("positive_absolute_r2", "mean"),
        )
    )
    rng = np.random.default_rng(SEED)
    benefit_denominator = int(
        decisions.loc[decisions["policy"] == "cca_meta", "task_has_clear_benefit"].sum()
    )
    summary_rows = []
    for policy in POLICIES:
        program_rows = programme.loc[programme["policy"] == policy].sort_values("programme")
        values = program_rows["utility"].to_numpy(dtype=float)
        lo, hi = cluster_bootstrap(values, rng)
        task_rows = decisions.loc[decisions["policy"] == policy]
        admitted = task_rows.loc[task_rows["admitted"]]
        retained = int(
            task_rows.loc[task_rows["task_has_clear_benefit"], "clear_benefit"].sum()
        )
        summary_rows.append(
            {
                "policy": policy,
                "programme_clusters": len(program_rows),
                "target_tasks": len(task_rows),
                "mean_programme_utility": float(np.mean(values)),
                "bootstrap_ci_lo": lo,
                "bootstrap_ci_hi": hi,
                "programme_coverage": float(program_rows["any_admission"].mean()),
                "task_coverage": float(task_rows["admitted"].mean()),
                "admitted_tasks": len(admitted),
                "admitted_point_harm_rate": float(admitted["point_harm"].mean())
                if len(admitted)
                else np.nan,
                "admitted_clear_harm_rate": float(admitted["clear_harm"].mean())
                if len(admitted)
                else np.nan,
                "clear_benefit_retained": retained,
                "clear_benefit_available": benefit_denominator,
                "clear_benefit_retention_rate": retained / benefit_denominator
                if benefit_denominator
                else np.nan,
                "selected_positive_absolute_r2_rate_when_available": float(
                    admitted.loc[admitted["augmented_r2"].notna(), "positive_absolute_r2"].mean()
                )
                if admitted["augmented_r2"].notna().any()
                else np.nan,
            }
        )
    policy_summary = pd.DataFrame(summary_rows)

    contrasts = []
    raw_p = []
    for comparator in ["always_best_credibility", "never_borrow"]:
        left = programme.loc[programme["policy"] == "cca_meta", ["programme", "utility"]]
        right = programme.loc[programme["policy"] == comparator, ["programme", "utility"]]
        paired = left.merge(right, on="programme", suffixes=("_cca", "_comparator"))
        diff = (paired["utility_cca"] - paired["utility_comparator"]).to_numpy(dtype=float)
        lo, hi = cluster_bootstrap(diff, rng)
        p = exact_sign_flip_p(diff)
        raw_p.append(p)
        contrasts.append(
            {
                "contrast": f"cca_meta_minus_{comparator}",
                "programme_clusters": len(diff),
                "mean_utility_difference": float(np.mean(diff)),
                "bootstrap_ci_lo": lo,
                "bootstrap_ci_hi": hi,
                "sign_flip_p_raw_one_sided": p,
            }
        )
    adjusted = holm(raw_p)
    for row, value in zip(contrasts, adjusted):
        row["holm_p"] = value
    return policy_summary, pd.DataFrame(contrasts)


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    for entry in design["inputs"]:
        path = ROOT / entry["path"]
        if sha256(path).upper() != entry["sha256"].upper():
            raise AssertionError(f"Input hash mismatch: {entry['path']}")

    rows = base_edge_panel() + outcome_unseen_edges()
    edges = pd.DataFrame(rows).sort_values(["programme", "target_task", "source"])
    if edges["edge_id"].duplicated().any():
        duplicates = edges.loc[edges["edge_id"].duplicated(), "edge_id"].tolist()
        raise AssertionError(f"Duplicate edge IDs: {duplicates[:5]}")
    if not np.isfinite(edges["effect_relative_rmse"]).all():
        raise AssertionError("Non-finite edge utility")
    expected_programmes = set(design["independent_program_clusters"])
    observed_programmes = set(edges["programme"])
    if expected_programmes != observed_programmes:
        raise AssertionError(
            f"Programme mismatch: expected {sorted(expected_programmes)}, observed {sorted(observed_programmes)}"
        )

    predictions = leave_one_program_predictions(edges)
    decisions = policy_decisions(predictions)
    policy_summary, contrasts = summarize_policies(decisions)

    RESULTS.mkdir(parents=True, exist_ok=True)
    edges.to_csv(EDGE_OUT, index=False)
    predictions.to_csv(PRED_OUT, index=False)
    policy_summary.to_csv(POLICY_OUT, index=False)
    contrasts.to_csv(CONTRAST_OUT, index=False)

    cca = policy_summary.loc[policy_summary["policy"] == "cca_meta"].iloc[0]
    coverage_pass = bool(
        cca["programme_coverage"] >= design["nontriviality_guard"]["minimum_programme_coverage"]
    )
    primary_pass = bool(
        coverage_pass
        and (contrasts["mean_utility_difference"] > 0).all()
        and (contrasts["bootstrap_ci_lo"] > 0).all()
        and (contrasts["holm_p"] < 0.05).all()
    )
    summary = {
        "status": "complete-method-development",
        "claim_guard": design["claim_guard"],
        "design_sha256": sha256(DESIGN_PATH),
        "input_sha256": {entry["path"]: sha256(ROOT / entry["path"]) for entry in design["inputs"]},
        "edge_rows": int(len(edges)),
        "target_tasks": int(edges["target_task"].nunique()),
        "programme_clusters": int(edges["programme"].nunique()),
        "features": FEATURES,
        "cca_meta": {
            key: (None if pd.isna(value) else float(value) if isinstance(value, (float, np.floating)) else int(value) if isinstance(value, (int, np.integer)) else value)
            for key, value in cca.to_dict().items()
        },
        "coverage_guard_pass": coverage_pass,
        "primary_policy_superiority_pass": primary_pass,
        "decision": (
            "leave-one-program CCA meta-gate passes the frozen nontrivial superiority family"
            if primary_pass
            else "leave-one-program CCA meta-gate does not pass the frozen nontrivial superiority family"
        ),
        "output_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [EDGE_OUT, PRED_OUT, POLICY_OUT, CONTRAST_OUT]
        },
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
