"""Develop and audit a local-gated abstaining neighbor portfolio on Caltech.

This analysis is explicitly outcome-informed method development.  Candidate
outcomes are used only after an order has been produced from initial target
labels, source predictions, and composition geometry.  It cannot revise the
frozen Caltech adaptive-policy decision or establish prospective discovery.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

try:
    from .audit_caltech_ionic_external_target import (
        COLUMNS,
        TARGET_PATH,
        normalize_dois,
    )
    from .common import composition_features
    from .run_caltech_ionic_external_policy import (
        REAL_SOURCE_IDS,
        composition_novelty,
        fit_source_models,
        initial_indices,
        load_target,
        percentile_rank,
        source_entities,
        stable_seed,
        true_hit_set,
    )
except ImportError:
    from audit_caltech_ionic_external_target import COLUMNS, TARGET_PATH, normalize_dois
    from common import composition_features
    from run_caltech_ionic_external_policy import (
        REAL_SOURCE_IDS,
        composition_novelty,
        fit_source_models,
        initial_indices,
        load_target,
        percentile_rank,
        source_entities,
        stable_seed,
        true_hit_set,
    )

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "local_gated_neighbor_portfolio_design.json"

REAL_NEIGHBORS = ["obelix_same_property", "estm_transport_neighbor"]
WRONG_NEIGHBORS = ["borg_mechanical_control", "ocx_catalysis_control"]
SHUFFLED_SOURCE = "shuffled_obelix"
POLICIES = [
    "uniform_random",
    "composition_novelty",
    "static_neighbor_round_robin",
    "static_neighbor_consensus",
    "single_best_local_neighbor",
    "global_gated_neighbor_portfolio",
    "local_gated_no_source_support",
    "local_gated_no_target_ood",
    "local_gated_no_diversity",
    "local_gated_neighbor_portfolio",
    "local_gated_wrong_source_portfolio",
    "local_gated_shuffled_obelix",
]

TRAJECTORY_OUTPUT = RESULTS / "local_gated_neighbor_portfolio_trajectories.csv"
UTILITY_OUTPUT = RESULTS / "local_gated_neighbor_portfolio_utility.csv"
COMPONENT_OUTPUT = RESULTS / "local_gated_neighbor_candidate_components.csv"
ATTRIBUTION_OUTPUT = RESULTS / "local_gated_neighbor_candidate_attribution.csv"
HYPOTHESIS_OUTPUT = RESULTS / "local_gated_neighbor_hypothesis_cards.csv"
SUMMARY_OUTPUT = RESULTS / "local_gated_neighbor_portfolio_summary.json"


def canonical_json_hash(path: Path) -> str:
    obj = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def positive_percentile(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    out = np.zeros(len(values), dtype=float)
    mask = np.isfinite(values) & (values > 0)
    if mask.any():
        out[mask] = percentile_rank(values[mask])
    return out


def safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if len(left) < 3 or np.unique(left).size < 2 or np.unique(right).size < 2:
        return 0.0
    rho = float(stats.spearmanr(left, right).statistic)
    return rho if np.isfinite(rho) else 0.0


def stable_best(
    scores: np.ndarray,
    novelty: np.ndarray,
    indices: list[int],
    target: pd.DataFrame,
) -> int:
    scores = np.asarray(scores, dtype=float)
    best = np.flatnonzero(scores == np.nanmax(scores))
    if len(best) > 1:
        best_novelty = float(np.max(novelty[best]))
        best = best[novelty[best] == best_novelty]
    if len(best) > 1:
        return int(
            min(
                best,
                key=lambda pos: target.at[indices[int(pos)], "material_key"],
            )
        )
    return int(best[0])


def target_universe() -> tuple[set[str], set[str]]:
    from scripts.localdb.build_localdb import canonical_formula

    raw = pd.read_csv(
        TARGET_PATH, usecols=[COLUMNS["formula"], COLUMNS["outcome"], COLUMNS["doi"]]
    )
    keys = raw[COLUMNS["formula"]].map(canonical_formula).map(lambda item: item[0])
    values = pd.to_numeric(raw[COLUMNS["outcome"]], errors="coerce")
    valid = keys.notna() & np.isfinite(values) & (values > 0)
    dois = set().union(*raw.loc[valid, COLUMNS["doi"]].map(normalize_dois).tolist())
    return set(keys[valid]), dois


def source_support_distances(target_x: np.ndarray) -> dict[str, np.ndarray]:
    target_keys, target_dois = target_universe()
    output: dict[str, np.ndarray] = {}
    for source in REAL_SOURCE_IDS:
        frame = source_entities(source, target_keys, target_dois)
        source_x = composition_features(frame["material_key"].tolist()).astype(np.float32)
        scaler = StandardScaler().fit(source_x)
        source_scaled = scaler.transform(source_x).astype(np.float32)
        target_scaled = scaler.transform(target_x).astype(np.float32)
        output[source] = pairwise_distances(
            target_scaled, source_scaled, metric="euclidean", n_jobs=1
        ).min(axis=1)
    output[SHUFFLED_SOURCE] = output["obelix_same_property"].copy()
    return output


def local_source_components(
    *,
    source: str,
    source_prediction: np.ndarray,
    support_distance: np.ndarray,
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    initial: list[int],
    candidates: list[int],
    mode: str,
) -> pd.DataFrame:
    y = target["value"].to_numpy(float)
    initial_array = np.asarray(initial, dtype=int)
    candidate_array = np.asarray(candidates, dtype=int)
    source_rank = percentile_rank(source_prediction[candidate_array])
    global_rho = safe_spearman(source_prediction[initial_array], y[initial_array])
    n_initial = len(initial)
    qualification = max(0.0, (global_rho - 0.10) / 0.90) * n_initial / (n_initial + 20)

    target_distance = composition_novelty(
        x_scaled[candidate_array], x_scaled[initial_array]
    )
    target_ood = percentile_rank(target_distance)
    source_support = 1.0 - percentile_rank(support_distance[candidate_array])

    distances = pairwise_distances(
        x_scaled[candidate_array], x_scaled[initial_array], metric="euclidean", n_jobs=1
    )
    k = min(12, len(initial_array))
    nearest = np.argsort(distances, axis=1)[:, :k]
    local_rho = np.zeros(len(candidate_array), dtype=float)
    for row, local_positions in enumerate(nearest):
        local_indices = initial_array[local_positions]
        local_rho[row] = safe_spearman(
            source_prediction[local_indices], y[local_indices]
        )
    local_concordance = np.maximum(0.0, local_rho) * k / (k + 12)

    use_local = mode not in {"global"}
    use_support = mode not in {"no_support"}
    use_ood = mode not in {"no_ood"}
    local_factor = local_concordance if use_local else np.ones(len(candidate_array))
    support_factor = source_support if use_support else np.ones(len(candidate_array))
    ood_factor = target_ood if use_ood else np.ones(len(candidate_array))

    gate = np.full(len(candidate_array), qualification > 0, dtype=bool)
    if use_local:
        gate &= local_concordance > 0
    if use_support:
        gate &= source_support >= 0.50
    if use_ood:
        gate &= target_ood >= 0.50
    score = (
        source_rank
        * qualification
        * local_factor
        * support_factor
        * ood_factor
    )
    score = np.where(gate, score, 0.0)
    return pd.DataFrame(
        {
            "candidate_index": candidate_array,
            "source": source,
            "source_rank": source_rank,
            "global_rho": global_rho,
            "qualification": qualification,
            "target_distance": target_distance,
            "target_ood": target_ood,
            "source_support": source_support,
            "local_rho": local_rho,
            "local_concordance": local_concordance,
            "gate_passed": gate,
            "source_score": score,
        }
    )


def sequential_novelty_order(
    *,
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    initial: list[int],
    candidates: list[int],
    budget: int,
) -> list[int]:
    remaining = list(candidates)
    labelled = list(initial)
    selected: list[int] = []
    while remaining and len(selected) < budget:
        novelty = composition_novelty(x_scaled[remaining], x_scaled[labelled])
        pos = stable_best(novelty, novelty, remaining, target)
        chosen = remaining.pop(pos)
        selected.append(chosen)
        labelled.append(chosen)
    return selected


def portfolio_order(
    *,
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    initial: list[int],
    candidates: list[int],
    components: dict[str, pd.DataFrame],
    sources: list[str],
    budget: int,
    diversity: bool,
) -> list[int]:
    index_to_position = {index: pos for pos, index in enumerate(candidates)}
    base = np.zeros(len(candidates), dtype=float)
    for source in sources:
        local = components[source].set_index("candidate_index").loc[candidates]
        base += positive_percentile(local["source_score"].to_numpy(float))
    base_rank = positive_percentile(base)
    remaining = list(candidates)
    selected: list[int] = []
    labelled = list(initial)
    while remaining and len(selected) < budget:
        novelty = composition_novelty(x_scaled[remaining], x_scaled[labelled])
        positions = np.asarray([index_to_position[index] for index in remaining], dtype=int)
        local_base = base_rank[positions]
        eligible = local_base > 0
        if eligible.any():
            if diversity:
                diversity_rank = percentile_rank(novelty)
                score = 0.75 * local_base + 0.25 * diversity_rank
            else:
                score = local_base.copy()
            score = np.where(eligible, score, -np.inf)
        else:
            score = percentile_rank(novelty)
        pos = stable_best(score, novelty, remaining, target)
        chosen = remaining.pop(pos)
        selected.append(chosen)
        labelled.append(chosen)
    return selected


def static_orders(
    *,
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    initial: list[int],
    candidates: list[int],
    predictions: dict[str, np.ndarray],
    budget: int,
) -> dict[str, list[int]]:
    novelty = composition_novelty(x_scaled[candidates], x_scaled[initial])
    orders: dict[str, list[int]] = {}
    for source in REAL_NEIGHBORS:
        score = predictions[source][candidates]
        frame = pd.DataFrame(
            {
                "index": candidates,
                "score": score,
                "novelty": novelty,
                "key": target.loc[candidates, "material_key"].to_numpy(),
            }
        ).sort_values(["score", "novelty", "key"], ascending=[False, False, True])
        orders[source] = frame["index"].astype(int).tolist()
    round_robin: list[int] = []
    for rank in range(len(candidates)):
        for source in REAL_NEIGHBORS:
            index = orders[source][rank]
            if index not in round_robin:
                round_robin.append(index)
            if len(round_robin) >= budget:
                break
        if len(round_robin) >= budget:
            break
    rank_maps = {
        source: {index: rank + 1 for rank, index in enumerate(order)}
        for source, order in orders.items()
    }
    consensus = sorted(
        candidates,
        key=lambda index: (
            sum(rank_maps[source][index] for source in REAL_NEIGHBORS),
            -float(novelty[candidates.index(index)]),
            target.at[index, "material_key"],
        ),
    )[:budget]
    return {
        "static_neighbor_round_robin": round_robin,
        "static_neighbor_consensus": consensus,
    }


def evaluate_order(
    *,
    scope: str,
    seed: int,
    policy: str,
    order: list[int],
    target: pd.DataFrame,
    candidates: list[int],
    budget: int,
) -> tuple[list[dict], dict]:
    hit_set = true_hit_set(target, candidates)
    pool_max = float(target.loc[candidates, "value"].max())
    rows: list[dict] = []
    for step, index in enumerate(order[:budget], start=1):
        rows.append(
            {
                "scope": scope,
                "seed": seed,
                "policy": policy,
                "step": step,
                "chosen_index": int(index),
                "chosen_key": target.at[index, "material_key"],
                "chosen_formula": target.at[index, "material_raw"],
                "chosen_y": float(target.at[index, "value"]),
                "is_true_top5_hit": bool(index in hit_set),
            }
        )
    local = pd.DataFrame(rows)
    hits = local["is_true_top5_hit"].to_numpy(bool)
    cumulative = np.cumsum(hits)
    hit_steps = np.flatnonzero(hits)
    top_n = len(hit_set)
    utility = {
        "scope": scope,
        "seed": seed,
        "policy": policy,
        "candidate_n": len(candidates),
        "top_n": top_n,
        "auc20": float(np.sum(cumulative[:20])),
        "first_hit": int(hit_steps[0] + 1) if len(hit_steps) else budget + 1,
        "recall20": float(np.sum(hits[:20]) / top_n),
        "recall40": float(np.sum(hits[:40]) / top_n),
        "regret20": float(pool_max - local.iloc[:20]["chosen_y"].max()),
    }
    return rows, utility


def run_seed_scope(
    *,
    scope: str,
    seed: int,
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    base_predictions: dict[str, np.ndarray],
    support_distances: dict[str, np.ndarray],
    candidates: list[int],
    initial_n: int,
    budget: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    initial = initial_indices(target, seed, initial_n)
    rng = np.random.default_rng(stable_seed(f"local-gate-shuffle:{seed}"))
    predictions = {key: value.copy() for key, value in base_predictions.items()}
    predictions[SHUFFLED_SOURCE] = rng.permutation(predictions["obelix_same_property"])

    mode_components: dict[str, dict[str, pd.DataFrame]] = {}
    for mode in ("full", "global", "no_support", "no_ood"):
        mode_components[mode] = {}
        for source in [*REAL_NEIGHBORS, *WRONG_NEIGHBORS, SHUFFLED_SOURCE]:
            mode_components[mode][source] = local_source_components(
                source=source,
                source_prediction=predictions[source],
                support_distance=support_distances[source],
                target=target,
                x_scaled=x_scaled,
                initial=initial,
                candidates=candidates,
                mode=mode,
            )

    orders = static_orders(
        target=target,
        x_scaled=x_scaled,
        initial=initial,
        candidates=candidates,
        predictions=predictions,
        budget=budget,
    )
    orders["uniform_random"] = list(
        np.random.default_rng(stable_seed(f"local-gate-random:{scope}:{seed}")).permutation(
            candidates
        )[:budget]
    )
    orders["composition_novelty"] = sequential_novelty_order(
        target=target,
        x_scaled=x_scaled,
        initial=initial,
        candidates=candidates,
        budget=budget,
    )

    full_components = mode_components["full"]
    best_source = max(
        REAL_NEIGHBORS,
        key=lambda source: (
            float(full_components[source]["qualification"].iloc[0]),
            source,
        ),
    )
    orders["single_best_local_neighbor"] = portfolio_order(
        target=target,
        x_scaled=x_scaled,
        initial=initial,
        candidates=candidates,
        components=full_components,
        sources=[best_source],
        budget=budget,
        diversity=True,
    )
    policy_specs = {
        "global_gated_neighbor_portfolio": ("global", REAL_NEIGHBORS, True),
        "local_gated_no_source_support": ("no_support", REAL_NEIGHBORS, True),
        "local_gated_no_target_ood": ("no_ood", REAL_NEIGHBORS, True),
        "local_gated_no_diversity": ("full", REAL_NEIGHBORS, False),
        "local_gated_neighbor_portfolio": ("full", REAL_NEIGHBORS, True),
        "local_gated_wrong_source_portfolio": ("full", WRONG_NEIGHBORS, True),
        "local_gated_shuffled_obelix": ("full", [SHUFFLED_SOURCE], True),
    }
    for policy, (mode, sources, diversity) in policy_specs.items():
        orders[policy] = portfolio_order(
            target=target,
            x_scaled=x_scaled,
            initial=initial,
            candidates=candidates,
            components=mode_components[mode],
            sources=list(sources),
            budget=budget,
            diversity=diversity,
        )

    if set(orders) != set(POLICIES):
        raise AssertionError(f"Policy mismatch: {sorted(set(POLICIES) ^ set(orders))}")
    trajectory_rows: list[dict] = []
    utility_rows: list[dict] = []
    for policy in POLICIES:
        order = [int(index) for index in orders[policy]]
        if len(order) != budget or len(order) != len(set(order)):
            raise AssertionError(f"{scope}/{seed}/{policy}: invalid order")
        rows, utility = evaluate_order(
            scope=scope,
            seed=seed,
            policy=policy,
            order=order,
            target=target,
            candidates=candidates,
            budget=budget,
        )
        trajectory_rows.extend(rows)
        utility_rows.append(utility)

    selected_step = {
        int(index): step + 1
        for step, index in enumerate(orders["local_gated_neighbor_portfolio"])
    }
    hit_set = true_hit_set(target, candidates)
    component_rows: list[dict] = []
    for source in REAL_NEIGHBORS:
        local = full_components[source].copy()
        for record in local.to_dict(orient="records"):
            index = int(record["candidate_index"])
            component_rows.append(
                {
                    "scope": scope,
                    "seed": seed,
                    "source": source,
                    "candidate_index": index,
                    "material_key": target.at[index, "material_key"],
                    "material_raw": target.at[index, "material_raw"],
                    "target_value": float(target.at[index, "value"]),
                    "is_true_top5_hit": bool(index in hit_set),
                    "selected_step": selected_step.get(index, np.nan),
                    **{key: value for key, value in record.items() if key not in {"candidate_index", "source"}},
                }
            )
    return trajectory_rows, utility_rows, component_rows


def bootstrap_difference(
    left: np.ndarray, right: np.ndarray, *, label: str, draws: int = 5000
) -> list[float]:
    effect = np.asarray(left, dtype=float) - np.asarray(right, dtype=float)
    rng = np.random.default_rng(stable_seed(f"local-gate-bootstrap:{label}"))
    indices = rng.integers(0, len(effect), size=(draws, len(effect)))
    means = effect[indices].mean(axis=1)
    return [float(value) for value in np.quantile(means, [0.025, 0.975])]


def policy_summary(utility: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    means = (
        utility.groupby(["scope", "policy"], as_index=False)
        .agg(
            auc20=("auc20", "mean"),
            first_hit=("first_hit", "mean"),
            recall20=("recall20", "mean"),
            recall40=("recall40", "mean"),
            regret20=("regret20", "mean"),
        )
    )
    comparators = [
        "uniform_random",
        "composition_novelty",
        "static_neighbor_round_robin",
        "static_neighbor_consensus",
        "single_best_local_neighbor",
        "global_gated_neighbor_portfolio",
        "local_gated_no_source_support",
        "local_gated_no_target_ood",
        "local_gated_no_diversity",
        "local_gated_wrong_source_portfolio",
        "local_gated_shuffled_obelix",
    ]
    contrast_rows: list[dict] = []
    for scope, local in utility.groupby("scope"):
        pivot = local.pivot(index="seed", columns="policy", values="auc20")
        for comparator in comparators:
            effect = (
                pivot["local_gated_neighbor_portfolio"] - pivot[comparator]
            ).to_numpy(float)
            contrast_rows.append(
                {
                    "scope": scope,
                    "full_policy": "local_gated_neighbor_portfolio",
                    "comparator": comparator,
                    "auc20_gain": float(effect.mean()),
                    "auc20_gain_ci_low": bootstrap_difference(
                        pivot["local_gated_neighbor_portfolio"].to_numpy(float),
                        pivot[comparator].to_numpy(float),
                        label=f"{scope}:{comparator}",
                    )[0],
                    "auc20_gain_ci_high": bootstrap_difference(
                        pivot["local_gated_neighbor_portfolio"].to_numpy(float),
                        pivot[comparator].to_numpy(float),
                        label=f"{scope}:{comparator}",
                    )[1],
                    "fraction_seed_full_better": float(np.mean(effect > 0)),
                    "fraction_seed_tied": float(np.mean(effect == 0)),
                }
            )
    return means, pd.DataFrame(contrast_rows)


def aggregate_attribution(components: pd.DataFrame) -> pd.DataFrame:
    components = components.copy()
    components["selected_top20"] = components["selected_step"].le(20)
    grouped = (
        components.groupby(
            [
                "scope",
                "source",
                "candidate_index",
                "material_key",
                "material_raw",
                "is_true_top5_hit",
            ],
            as_index=False,
        )
        .agg(
            target_value=("target_value", "first"),
            selection_frequency_top20=("selected_top20", "mean"),
            median_selected_step=("selected_step", "median"),
            gate_frequency=("gate_passed", "mean"),
            mean_source_rank=("source_rank", "mean"),
            mean_qualification=("qualification", "mean"),
            mean_target_ood=("target_ood", "mean"),
            mean_source_support=("source_support", "mean"),
            mean_local_concordance=("local_concordance", "mean"),
            mean_source_score=("source_score", "mean"),
        )
    )
    return grouped


def hypothesis_cards(
    attribution: pd.DataFrame, target: pd.DataFrame, x_scaled: np.ndarray
) -> pd.DataFrame:
    local = attribution[attribution["scope"] == "external_candidate"].copy()
    index_cols = [
        "candidate_index",
        "material_key",
        "material_raw",
        "target_value",
        "is_true_top5_hit",
    ]
    base = local.groupby(index_cols, as_index=False).agg(
        selection_frequency_top20=("selection_frequency_top20", "first"),
        median_selected_step=("median_selected_step", "first"),
        mean_target_ood=("mean_target_ood", "first"),
    )
    scores = local.pivot_table(
        index="candidate_index", columns="source", values="mean_source_score"
    ).fillna(0.0)
    base = base.set_index("candidate_index").join(scores).reset_index()
    for source in REAL_NEIGHBORS:
        if source not in base:
            base[source] = 0.0
    obelix = base["obelix_same_property"]
    estm = base["estm_transport_neighbor"]
    base["combined_score"] = obelix + estm
    base["source_role"] = np.select(
        [
            (obelix > 1.25 * estm) & (obelix > 0),
            (estm > 1.25 * obelix) & (estm > 0),
            (obelix > 0) & (estm > 0),
        ],
        ["OBELiX-dominant", "ESTM-dominant", "neighbor-consensus"],
        default="fallback-dominated",
    )
    candidates = base.sort_values(
        ["selection_frequency_top20", "combined_score"], ascending=False
    )
    selected: list[pd.Series] = []
    for role in ["OBELiX-dominant", "ESTM-dominant", "neighbor-consensus"]:
        eligible = candidates[
            (candidates["source_role"] == role)
            & candidates["is_true_top5_hit"].astype(bool)
            & ~candidates["candidate_index"].isin(
                [int(row["candidate_index"]) for row in selected]
            )
        ]
        if not eligible.empty:
            selected.append(eligible.iloc[0])
    false_positive = candidates[
        ~candidates["is_true_top5_hit"].astype(bool)
        & ~candidates["candidate_index"].isin(
            [int(row["candidate_index"]) for row in selected]
        )
    ]
    if not false_positive.empty:
        row = false_positive.iloc[0].copy()
        row["source_role"] = "high-ranked falsifier"
        selected.append(row)

    controls = candidates[candidates["selection_frequency_top20"] <= 0.10].copy()
    cards: list[dict] = []
    used_controls: set[int] = set()
    for row in selected:
        index = int(row["candidate_index"])
        same_band = controls[
            np.abs(controls["mean_target_ood"] - float(row["mean_target_ood"])) <= 0.15
        ]
        same_band = same_band[same_band["candidate_index"] != index]
        if same_band.empty:
            same_band = controls[controls["candidate_index"] != index]
        same_band = same_band[~same_band["candidate_index"].isin(used_controls)]
        control_index: int | None = None
        if not same_band.empty:
            options = same_band["candidate_index"].astype(int).to_numpy()
            distance = np.linalg.norm(x_scaled[options] - x_scaled[index], axis=1)
            control_index = int(options[int(np.argmin(distance))])
            used_controls.add(control_index)
        role = str(row["source_role"])
        if role == "OBELiX-dominant":
            rationale = (
                "Same-property cross-database proposal: the composition lies in a region "
                "ranked favorably by leakage-filtered OBELiX ionic-conductivity patterns."
            )
        elif role == "ESTM-dominant":
            rationale = (
                "Transport-adjacent proposal: the composition is prioritized by ESTM "
                "thermoelectric transport chemistry, motivating a shared carrier/phonon "
                "transport hypothesis rather than coefficient transfer."
            )
        elif role == "neighbor-consensus":
            rationale = (
                "Consensus proposal: independent same-property and transport-adjacent "
                "rankings both prioritize the composition."
            )
        else:
            rationale = (
                "Falsifier: the strategy prioritizes this composition despite its target "
                "outcome falling outside the true top region."
            )
        cards.append(
            {
                "card_role": role,
                "candidate_index": index,
                "candidate_formula": row["material_raw"],
                "candidate_log10_conductivity": float(row["target_value"]),
                "true_top5_hit": bool(row["is_true_top5_hit"]),
                "selection_frequency_top20": float(row["selection_frequency_top20"]),
                "mean_target_ood": float(row["mean_target_ood"]),
                "obelix_mean_score": float(row["obelix_same_property"]),
                "estm_mean_score": float(row["estm_transport_neighbor"]),
                "source_derived_hypothesis": rationale,
                "prospective_falsifier": (
                    "The source-specific claim fails if the candidate is not enriched over "
                    "an outcome-free composition/OOD-matched control or if the source loses "
                    "marginal top-region coverage on an unseen target."
                ),
                "matched_control_index": control_index,
                "matched_control_formula": (
                    target.at[control_index, "material_raw"] if control_index is not None else None
                ),
                "matched_control_log10_conductivity": (
                    float(target.at[control_index, "value"])
                    if control_index is not None
                    else None
                ),
                "evidence_status": "retrospective method-development card; not predeclared new science",
            }
        )
    return pd.DataFrame(cards)


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if design["status"].split()[0] != "outcome-informed":
        raise AssertionError("Method-development status was changed")
    target, x, x_scaled = load_target()
    base_predictions, source_quality = fit_source_models(target, x)
    support_distances = source_support_distances(x)
    candidate = target.index[target["split"] == "candidate"].astype(int).tolist()
    development = target.index[target["split"] == "development"].astype(int).tolist()
    distance = composition_novelty(x_scaled[candidate], x_scaled[development])
    hard_n = int(math.ceil(0.40 * len(candidate)))
    hard = [candidate[index] for index in np.argsort(distance)[-hard_n:]]
    pools = {"external_candidate": candidate, "hard_ood_40pct": hard}

    trajectory_rows: list[dict] = []
    utility_rows: list[dict] = []
    component_rows: list[dict] = []
    for scope, candidates in pools.items():
        for seed in range(int(design["campaign"]["paired_initial_seeds"])):
            trajectories, utilities, components = run_seed_scope(
                scope=scope,
                seed=seed,
                target=target,
                x_scaled=x_scaled,
                base_predictions=base_predictions,
                support_distances=support_distances,
                candidates=candidates,
                initial_n=int(design["campaign"]["initial_target_labels"]),
                budget=int(design["campaign"]["budget"]),
            )
            trajectory_rows.extend(trajectories)
            utility_rows.extend(utilities)
            component_rows.extend(components)

    trajectories = pd.DataFrame(trajectory_rows)
    utility = pd.DataFrame(utility_rows)
    components = pd.DataFrame(component_rows)
    seed_n = int(design["campaign"]["paired_initial_seeds"])
    budget = int(design["campaign"]["budget"])
    expected_trajectory = len(pools) * seed_n * len(POLICIES) * budget
    expected_utility = len(pools) * seed_n * len(POLICIES)
    expected_components = sum(len(pool) for pool in pools.values()) * seed_n * 2
    if len(trajectories) != expected_trajectory:
        raise AssertionError((len(trajectories), expected_trajectory))
    if len(utility) != expected_utility:
        raise AssertionError((len(utility), expected_utility))
    if len(components) != expected_components:
        raise AssertionError((len(components), expected_components))

    means, contrasts = policy_summary(utility)
    attribution = aggregate_attribution(components)
    cards = hypothesis_cards(attribution, target, x_scaled)
    trajectories.to_csv(TRAJECTORY_OUTPUT, index=False)
    utility.to_csv(UTILITY_OUTPUT, index=False)
    components.to_csv(COMPONENT_OUTPUT, index=False)
    attribution.to_csv(ATTRIBUTION_OUTPUT, index=False)
    cards.to_csv(HYPOTHESIS_OUTPUT, index=False)
    contrasts.to_csv(
        RESULTS / "local_gated_neighbor_portfolio_contrasts.csv", index=False
    )
    summary = {
        "status": "method-development-complete",
        "design_sha256": canonical_json_hash(DESIGN_PATH),
        "claim_guard": design["claim_guard"],
        "candidate_pools": {key: len(value) for key, value in pools.items()},
        "policies": POLICIES,
        "source_quality": records(source_quality),
        "policy_means": records(means),
        "full_policy_contrasts": records(contrasts),
        "trajectory_rows": len(trajectories),
        "utility_rows": len(utility),
        "candidate_component_rows": len(components),
        "attribution_rows": len(attribution),
        "hypothesis_cards": records(cards),
        "interpretation": (
            "This result audits whether local target OOD, source support, local "
            "concordance, diversity, and abstention preserve neighbor proposals on the "
            "already observed Caltech target. It selects an algorithm for a new target; "
            "it cannot establish independent acceleration."
        ),
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
