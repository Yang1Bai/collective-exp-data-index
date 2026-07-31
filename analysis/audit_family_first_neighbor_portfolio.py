"""Audit an outcome-informed family-first neighbor portfolio on Caltech.

The ordering code never reads candidate outcomes. Outcomes enter only in the
evaluation functions below. The analysis is explicitly method development on
an already observed external target and cannot establish prospective discovery.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .run_caltech_ionic_external_policy import (
        composition_novelty,
        fit_source_models,
        load_target,
    )
except ImportError:
    from run_caltech_ionic_external_policy import (
        composition_novelty,
        fit_source_models,
        load_target,
    )


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
DESIGN_PATH = ROOT / "analysis" / "family_first_neighbor_portfolio_design.json"
SUMMARY_PATH = RESULTS / "family_first_neighbor_portfolio_summary.json"
METRICS_PATH = RESULTS / "family_first_neighbor_portfolio_metrics.csv"
ORDERS_PATH = RESULTS / "family_first_neighbor_portfolio_orders.csv"
NULL_PATH = RESULTS / "family_first_neighbor_portfolio_null.csv"
SOURCE_DATA_PATH = RESULTS / "family_first_neighbor_portfolio_figure_source.csv"
HYPOTHESIS_PATH = RESULTS / "family_first_neighbor_hypothesis_cards.csv"

REAL_SOURCES = ["obelix_same_property", "estm_transport_neighbor"]
WRONG_SOURCES = ["borg_mechanical_control", "ocx_catalysis_control"]


def canonical_json_hash(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def stable_seed(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def source_order(
    candidates: list[int], prediction: np.ndarray, target: pd.DataFrame
) -> list[int]:
    return sorted(
        candidates,
        key=lambda index: (
            -float(prediction[index]),
            str(target.at[index, "material_key"]),
        ),
    )


def consensus_order(
    candidates: list[int],
    source_orders: dict[str, list[int]],
    target: pd.DataFrame,
) -> list[int]:
    rank = {
        source: {index: position + 1 for position, index in enumerate(order)}
        for source, order in source_orders.items()
    }
    return sorted(
        candidates,
        key=lambda index: (
            sum(rank[source][index] for source in source_orders),
            str(target.at[index, "material_key"]),
        ),
    )


def round_robin_order(source_orders: dict[str, list[int]]) -> list[int]:
    output: list[int] = []
    seen: set[int] = set()
    n = max(len(order) for order in source_orders.values())
    for rank in range(n):
        for source in source_orders:
            if rank >= len(source_orders[source]):
                continue
            index = source_orders[source][rank]
            if index not in seen:
                output.append(index)
                seen.add(index)
    return output


def family_first(order: list[int], target: pd.DataFrame) -> list[int]:
    """Give every outcome-free provenance/formulation group one first pass."""
    first: list[int] = []
    repeats: list[int] = []
    seen_groups: set[str] = set()
    for index in order:
        group = str(target.at[index, "group"])
        if group in seen_groups:
            repeats.append(index)
        else:
            first.append(index)
            seen_groups.add(group)
    output = first + repeats
    if len(output) != len(order) or len(set(output)) != len(order):
        raise AssertionError("Family-first order is not a permutation")
    return output


def candidate_pools(target: pd.DataFrame, x_scaled: np.ndarray) -> dict[str, list[int]]:
    candidate = target.index[target["split"] == "candidate"].astype(int).tolist()
    development = target.index[target["split"] == "development"].astype(int).tolist()
    novelty = composition_novelty(x_scaled[candidate], x_scaled[development])
    hard_n = max(1, int(math.ceil(0.40 * len(candidate))))
    hard = [candidate[position] for position in np.argsort(novelty)[-hard_n:]]
    return {"external_candidate": candidate, "hard_ood_40pct": hard}


def fixed_orders(
    *,
    candidates: list[int],
    development: list[int],
    target: pd.DataFrame,
    x_scaled: np.ndarray,
    predictions: dict[str, np.ndarray],
) -> dict[str, list[int]]:
    real = {
        source: source_order(candidates, predictions[source], target)
        for source in REAL_SOURCES
    }
    wrong = {
        source: source_order(candidates, predictions[source], target)
        for source in WRONG_SOURCES
    }
    entity_consensus = consensus_order(candidates, real, target)
    real_round_robin = round_robin_order(real)
    wrong_consensus = consensus_order(candidates, wrong, target)
    novelty = composition_novelty(x_scaled[candidates], x_scaled[development])
    novelty_order = [candidates[position] for position in np.argsort(-novelty)]
    random_rng = np.random.default_rng(stable_seed(f"uniform-family:{len(candidates)}"))
    uniform_order = random_rng.permutation(candidates).astype(int).tolist()
    return {
        "uniform_family_first": family_first(uniform_order, target),
        "composition_novelty_family_first": family_first(novelty_order, target),
        "obelix_family_first": family_first(real[REAL_SOURCES[0]], target),
        "estm_family_first": family_first(real[REAL_SOURCES[1]], target),
        "neighbor_entity_consensus": entity_consensus,
        "neighbor_family_first_round_robin": family_first(real_round_robin, target),
        "neighbor_family_first_consensus": family_first(entity_consensus, target),
        "wrong_source_family_first_consensus": family_first(wrong_consensus, target),
    }


def top_entities(target: pd.DataFrame, candidates: list[int]) -> set[int]:
    n = max(1, int(math.ceil(0.05 * len(candidates))))
    return set(target.loc[candidates].nlargest(n, "value").index.astype(int))


def top_groups(
    target: pd.DataFrame, candidates: list[int], aggregation: str
) -> set[str]:
    score = target.loc[candidates].groupby("group")["value"].agg(aggregation)
    n = max(1, int(math.ceil(0.05 * len(score))))
    return set(score.nlargest(n).index.astype(str))


def evaluate_order(
    *,
    scope: str,
    policy: str,
    order: list[int],
    candidates: list[int],
    target: pd.DataFrame,
    budget: int = 20,
) -> list[dict]:
    rows: list[dict] = []
    entity_hits = top_entities(target, candidates)
    for unit, aggregation in [
        ("entity", "entity"),
        ("provenance_group", "max"),
        ("provenance_group", "median"),
        ("provenance_group", "mean"),
    ]:
        if unit == "entity":
            hit_set: set[int] | set[str] = entity_hits
            total = len(entity_hits)
        else:
            hit_set = top_groups(target, candidates, aggregation)
            total = len(hit_set)
        seen_groups: set[str] = set()
        cumulative = 0
        auc = 0
        positions: list[int] = []
        for step, index in enumerate(order[:budget], start=1):
            group = str(target.at[index, "group"])
            if unit == "entity":
                hit = index in hit_set
            else:
                hit = group in hit_set and group not in seen_groups
            if hit:
                cumulative += 1
                positions.append(step)
            seen_groups.add(group)
            auc += cumulative
        rows.append(
            {
                "scope": scope,
                "policy": policy,
                "unit": unit,
                "group_value_aggregation": aggregation,
                "auc20": auc,
                "hit_count20": cumulative,
                "total_top_units": total,
                "recall20": cumulative / total,
                "first_hit": min(positions) if positions else budget + 1,
                "hit_positions": ";".join(map(str, positions)),
            }
        )
    return rows


def shuffled_null(
    *,
    scope: str,
    candidates: list[int],
    target: pd.DataFrame,
    predictions: dict[str, np.ndarray],
    replicates: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(stable_seed(f"family-first-null:{scope}"))
    rows: list[dict] = []
    base = {source: predictions[source][candidates].copy() for source in REAL_SOURCES}
    for replicate in range(replicates):
        shuffled_orders: dict[str, list[int]] = {}
        for source in REAL_SOURCES:
            permuted = rng.permutation(base[source])
            lookup = np.full(len(target), np.nan)
            lookup[candidates] = permuted
            shuffled_orders[source] = source_order(candidates, lookup, target)
        order = family_first(
            consensus_order(candidates, shuffled_orders, target), target
        )
        for metric in evaluate_order(
            scope=scope,
            policy="shuffled_neighbor_family_first_consensus",
            order=order,
            candidates=candidates,
            target=target,
        ):
            if metric["unit"] == "provenance_group" and metric[
                "group_value_aggregation"
            ] == "max":
                rows.append({"scope": scope, "replicate": replicate, **metric})
    return pd.DataFrame(rows)


def order_rows(
    scope: str, orders: dict[str, list[int]], target: pd.DataFrame
) -> list[dict]:
    rows: list[dict] = []
    for policy, order in orders.items():
        seen: set[str] = set()
        for rank, index in enumerate(order, start=1):
            group = str(target.at[index, "group"])
            rows.append(
                {
                    "scope": scope,
                    "policy": policy,
                    "rank": rank,
                    "candidate_index": index,
                    "material_key": target.at[index, "material_key"],
                    "material_raw": target.at[index, "material_raw"],
                    "group": group,
                    "first_group_representative": group not in seen,
                }
            )
            seen.add(group)
    return rows


def element_set(material_key: str) -> str:
    return "-".join(token.split(":", 1)[0] for token in material_key.split("|"))


def retrospective_hypothesis_cards(
    *,
    target: pd.DataFrame,
    candidates: list[int],
    order: list[int],
    predictions: dict[str, np.ndarray],
) -> pd.DataFrame:
    """Write reporting-format cards; target outcomes make them retrospective."""
    source_orders = {
        source: source_order(candidates, predictions[source], target)
        for source in REAL_SOURCES
    }
    ranks = {
        source: {index: rank + 1 for rank, index in enumerate(indices)}
        for source, indices in source_orders.items()
    }
    group_score = target.loc[candidates].groupby("group")["value"].max()
    n_top = max(1, int(math.ceil(0.05 * len(group_score))))
    top_groups = set(group_score.nlargest(n_top).index.astype(str))
    seen: set[str] = set()
    rows: list[dict] = []
    for selected_rank, index in enumerate(order, start=1):
        group = str(target.at[index, "group"])
        if group in seen:
            continue
        seen.add(group)
        if group not in top_groups:
            continue
        members = target.loc[
            target.index.isin(candidates) & target["group"].eq(group)
        ]
        best_index = int(members["value"].idxmax())
        obelix_rank = ranks[REAL_SOURCES[0]][index]
        estm_rank = ranks[REAL_SOURCES[1]][index]
        if obelix_rank <= 0.67 * estm_rank:
            attribution = "OBELiX-dominant"
        elif estm_rank <= 0.67 * obelix_rank:
            attribution = "ESTM-dominant"
        else:
            attribution = "rank-consensus"
        motif = element_set(str(target.at[index, "material_key"]))
        rows.append(
            {
                "card_id": f"caltech-group-{len(rows) + 1}",
                "scope": "external_candidate",
                "selected_rank": selected_rank,
                "group": group,
                "selected_formula": target.at[index, "material_raw"],
                "element_set": motif,
                "obelix_entity_rank": obelix_rank,
                "estm_entity_rank": estm_rank,
                "source_attribution": attribution,
                "outcome_free_basis": (
                    f"Family-first rank {selected_rank}; OBELiX rank {obelix_rank}; "
                    f"ESTM rank {estm_rank}; no candidate outcome enters the order."
                ),
                "source_derived_hypothesis": (
                    f"The {motif} formulation region is enriched for high target ionic "
                    "conductivity relative to an outcome-free composition-distance- and "
                    "group-size-matched region."
                ),
                "prospective_falsifier": (
                    "Freeze the group and matched control before target measurement; reject "
                    "the proposal if its first measured representative is not superior or if "
                    "the source contributes no marginal distinct-group recovery."
                ),
                "mechanistic_follow_up": (
                    "Measure phase identity, density/grain-boundary sensitivity, impedance "
                    "spectrum, temperature-dependent conductivity, and activation energy "
                    "before assigning a transport mechanism."
                ),
                "selected_log10_conductivity": float(target.at[index, "value"]),
                "best_group_formula": target.at[best_index, "material_raw"],
                "best_group_log10_conductivity": float(target.at[best_index, "value"]),
                "evidence_status": (
                    "retrospective method-development card; reporting template, not "
                    "predeclared new science"
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("selected_rank").reset_index(drop=True)


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    if not design["status"].startswith("outcome-informed"):
        raise AssertionError("Method-development disclosure changed")
    target, x, x_scaled = load_target()
    predictions, source_quality = fit_source_models(target, x)
    pools = candidate_pools(target, x_scaled)
    development = target.index[target["split"] == "development"].astype(int).tolist()
    outcome_permuted = target.copy()
    candidate_indices = sorted({index for pool in pools.values() for index in pool})
    permutation_rng = np.random.default_rng(stable_seed("candidate-outcome-invariance"))
    outcome_permuted.loc[candidate_indices, "value"] = permutation_rng.permutation(
        outcome_permuted.loc[candidate_indices, "value"].to_numpy()
    )
    metric_rows: list[dict] = []
    all_order_rows: list[dict] = []
    null_frames: list[pd.DataFrame] = []
    external_family_order: list[int] | None = None
    for scope, candidates in pools.items():
        orders = fixed_orders(
            candidates=candidates,
            development=development,
            target=target,
            x_scaled=x_scaled,
            predictions=predictions,
        )
        permuted_outcome_orders = fixed_orders(
            candidates=candidates,
            development=development,
            target=outcome_permuted,
            x_scaled=x_scaled,
            predictions=predictions,
        )
        if orders != permuted_outcome_orders:
            raise AssertionError("Candidate outcomes changed an acquisition order")
        for policy, order in orders.items():
            metric_rows.extend(
                evaluate_order(
                    scope=scope,
                    policy=policy,
                    order=order,
                    candidates=candidates,
                    target=target,
                )
            )
        all_order_rows.extend(order_rows(scope, orders, target))
        if scope == "external_candidate":
            external_family_order = orders["neighbor_family_first_consensus"]
        null_frames.append(
            shuffled_null(
                scope=scope,
                candidates=candidates,
                target=target,
                predictions=predictions,
                replicates=int(design["conditional_null"]["replicates"]),
            )
        )
    metrics = pd.DataFrame(metric_rows)
    orders_frame = pd.DataFrame(all_order_rows)
    null = pd.concat(null_frames, ignore_index=True)
    primary = metrics[
        metrics["unit"].eq("provenance_group")
        & metrics["group_value_aggregation"].eq("max")
    ].copy()
    primary_rows: list[dict] = []
    for scope, local in primary.groupby("scope"):
        observed = float(
            local.loc[
                local["policy"].eq("neighbor_family_first_consensus"), "auc20"
            ].iloc[0]
        )
        null_values = null.loc[null["scope"].eq(scope), "auc20"].to_numpy()
        primary_rows.append(
            {
                "scope": scope,
                "observed_auc20": observed,
                "shuffled_mean_auc20": float(np.mean(null_values)),
                "shuffled_q025_auc20": float(np.quantile(null_values, 0.025)),
                "shuffled_q975_auc20": float(np.quantile(null_values, 0.975)),
                "conditional_randomization_p": float(
                    (1 + np.sum(null_values >= observed)) / (1 + len(null_values))
                ),
            }
        )
    primary_null = pd.DataFrame(primary_rows)
    if external_family_order is None:
        raise AssertionError("External family-first order was not generated")
    cards = retrospective_hypothesis_cards(
        target=target,
        candidates=pools["external_candidate"],
        order=external_family_order,
        predictions=predictions,
    )
    if len(cards) != 4:
        raise AssertionError(f"Expected four external top-group cards, found {len(cards)}")
    metrics.to_csv(METRICS_PATH, index=False)
    orders_frame.to_csv(ORDERS_PATH, index=False)
    null.to_csv(NULL_PATH, index=False)
    primary.to_csv(SOURCE_DATA_PATH, index=False)
    cards.to_csv(HYPOTHESIS_PATH, index=False)
    summary = {
        "status": "outcome-informed-method-development-complete",
        "design_sha256": canonical_json_hash(DESIGN_PATH),
        "claim_guard": design["claim_guard"],
        "candidate_pools": {scope: len(pool) for scope, pool in pools.items()},
        "provenance_groups": {
            scope: int(target.loc[pool, "group"].nunique())
            for scope, pool in pools.items()
        },
        "source_quality": records(source_quality),
        "primary_metrics": records(primary),
        "conditional_null": records(primary_null),
        "candidate_outcome_permutation_invariance": True,
        "hypothesis_cards": records(cards),
        "tradeoff": "Family-first allocation optimizes breadth across distinct groups and can reduce repeated entity-level top-hit recovery within one group.",
        "future_test": design["future_freeze"],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
