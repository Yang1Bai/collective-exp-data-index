"""Run the frozen external ionic-conductor policy benchmark.

The confirmatory policy family and exact algorithms were frozen before any
source model or policy outcome was calculated.  One novelty-band policy is
reported as method-development only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

try:
    from .audit_caltech_ionic_external_target import (
        AMENDMENT_PATH,
        COLUMNS,
        DESIGN_PATH,
        SOURCE_SPECS,
        TARGET_PATH,
        aggregate_target,
        connected_groups,
        file_hash,
        normalize_dois,
        normalize_icsd,
        outcome_blind_split,
    )
    from .common import composition_features, load_property
except ImportError:
    from audit_caltech_ionic_external_target import (
        AMENDMENT_PATH,
        COLUMNS,
        DESIGN_PATH,
        SOURCE_SPECS,
        TARGET_PATH,
        aggregate_target,
        connected_groups,
        file_hash,
        normalize_dois,
        normalize_icsd,
        outcome_blind_split,
    )
    from common import composition_features, load_property

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
IMPLEMENTATION_PATH = HERE / "caltech_ionic_external_policy_implementation.json"
INFERENCE_AMENDMENT_PATH = HERE / "CALTECH_IONIC_INFERENCE_AMENDMENT.md"
STATE_MATCH_AMENDMENT_PATH = HERE / "CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md"
INFRASTRUCTURE_AMENDMENT_PATH = HERE / "CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md"
VERIFIER_AMENDMENT_PATH = HERE / "CALTECH_IONIC_VERIFIER_AMENDMENT_4.md"
AUDIT_PATH = RESULTS / "caltech_ionic_external_audit.json"
REQUIRED_CANONICAL_AUDIT_SHA256 = "d702792256e7ff3922f969bedd175e444434d7d5706347c29ae5357189181338"

CONFIRMATORY_POLICIES = [
    "uniform_random",
    "composition_novelty",
    "safe_target_novelty",
    "obelix_same_property_static",
    "estm_transport_neighbor_static",
    "borg_mechanical_static_control",
    "ocx_catalysis_static_control",
    "shuffled_obelix_static_control",
    "safe_obelix_residual",
    "safe_estm_residual",
    "safe_borg_residual_control",
    "safe_ocx_residual_control",
    "safe_shuffled_obelix_control",
    "safe_multisource_residual",
]
EXPLORATORY_POLICIES = ["safe_multisource_novelty_band"]
POLICIES = CONFIRMATORY_POLICIES + EXPLORATORY_POLICIES

REAL_SOURCE_IDS = [
    "obelix_same_property",
    "estm_transport_neighbor",
    "borg_mechanical_control",
    "ocx_catalysis_control",
]
SHUFFLED_SOURCE_ID = "shuffled_obelix"
ALL_GATE_SOURCE_IDS = REAL_SOURCE_IDS + [SHUFFLED_SOURCE_ID]

STATIC_SOURCE = {
    "obelix_same_property_static": "obelix_same_property",
    "estm_transport_neighbor_static": "estm_transport_neighbor",
    "borg_mechanical_static_control": "borg_mechanical_control",
    "ocx_catalysis_static_control": "ocx_catalysis_control",
    "shuffled_obelix_static_control": SHUFFLED_SOURCE_ID,
}
SAFE_SOURCE = {
    "safe_obelix_residual": ["obelix_same_property"],
    "safe_estm_residual": ["estm_transport_neighbor"],
    "safe_borg_residual_control": ["borg_mechanical_control"],
    "safe_ocx_residual_control": ["ocx_catalysis_control"],
    "safe_shuffled_obelix_control": [SHUFFLED_SOURCE_ID],
    "safe_multisource_residual": ALL_GATE_SOURCE_IDS,
    "safe_multisource_novelty_band": ALL_GATE_SOURCE_IDS,
}

PRIMARY_COMPARISONS = [
    ("policy_validity", "composition_novelty", "uniform_random"),
    ("policy_validity", "safe_target_novelty", "composition_novelty"),
    ("same_property_increment", "safe_obelix_residual", "safe_target_novelty"),
    ("adjacent_transport_increment", "safe_estm_residual", "safe_target_novelty"),
    ("safe_multisource_increment", "safe_multisource_residual", "safe_target_novelty"),
    ("negative_transfer", "safe_borg_residual_control", "safe_target_novelty"),
    ("negative_transfer", "safe_ocx_residual_control", "safe_target_novelty"),
    ("negative_transfer", "safe_shuffled_obelix_control", "safe_target_novelty"),
]


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "little")


def canonical_json_hash(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def percentile_rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(np.asarray(values, dtype=float)).rank(method="average", pct=True).to_numpy(float)


def make_model(seed: int, trees: int) -> ExtraTreesRegressor:
    return ExtraTreesRegressor(
        n_estimators=trees,
        min_samples_leaf=2,
        max_features=0.7,
        random_state=seed,
        n_jobs=1,
    )


def load_target() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    from scripts.localdb.build_localdb import canonical_formula

    raw = pd.read_csv(TARGET_PATH)
    parsed = raw[COLUMNS["formula"]].map(canonical_formula)
    raw["material_key"] = parsed.map(lambda item: item[0])
    raw["value_raw"] = pd.to_numeric(raw[COLUMNS["outcome"]], errors="coerce")
    raw["normalized_dois"] = raw[COLUMNS["doi"]].map(normalize_dois)
    raw["normalized_icsd"] = raw[COLUMNS["icsd"]].map(normalize_icsd)
    eligible = raw[
        raw["material_key"].notna()
        & np.isfinite(raw["value_raw"])
        & (raw["value_raw"] > 0)
    ].copy()
    eligible["value"] = np.log10(eligible["value_raw"].astype(float))
    eligible["group"] = connected_groups(eligible)
    entities = aggregate_target(eligible)
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    entities = outcome_blind_split(entities, int(design["target_split"]["seed"]))
    entities = entities.reset_index(drop=True)
    x = composition_features(entities["material_key"].tolist()).astype(np.float32)
    development = entities["split"].eq("development").to_numpy()
    scaler = StandardScaler().fit(x[development])
    x_scaled = scaler.transform(x).astype(np.float32)
    return entities, x, x_scaled


def source_entities(
    source_id: str,
    target_keys: set[str],
    target_dois: set[str],
) -> pd.DataFrame:
    spec = SOURCE_SPECS[source_id]
    frame = load_property(
        spec["dataset"],
        spec["property"],
        valid=spec["valid"],
        log10=bool(spec["log10"]),
    )
    frame["normalized_dois"] = frame["source_reference"].map(normalize_dois)
    frame["normalized_icsd"] = [()] * len(frame)
    overlap = frame["material_key"].isin(target_keys) | frame["normalized_dois"].map(
        lambda values: bool(set(values) & target_dois)
    )
    frame = frame[~overlap].copy().reset_index(drop=True)
    frame["group"] = connected_groups(frame)
    check = frame.groupby("material_key")["group"].nunique()
    if (check != 1).any():
        raise AssertionError(f"{source_id}: composition crosses source groups")
    return (
        frame.groupby("material_key", as_index=False)
        .agg(
            value=("value", "median"),
            group=("group", "first"),
            n_raw=("value", "size"),
            material_raw=("material_raw", "first"),
        )
        .sort_values("material_key")
        .reset_index(drop=True)
    )


def fit_source_models(
    target: pd.DataFrame,
    target_x: np.ndarray,
) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    raw = pd.read_csv(TARGET_PATH, usecols=[COLUMNS["formula"], COLUMNS["outcome"], COLUMNS["doi"]])
    from scripts.localdb.build_localdb import canonical_formula

    keys = raw[COLUMNS["formula"]].map(canonical_formula).map(lambda item: item[0])
    values = pd.to_numeric(raw[COLUMNS["outcome"]], errors="coerce")
    valid = keys.notna() & np.isfinite(values) & (values > 0)
    target_keys = set(keys[valid])
    target_dois = set().union(*raw.loc[valid, COLUMNS["doi"]].map(normalize_dois).tolist())

    predictions: dict[str, np.ndarray] = {}
    quality_rows: list[dict] = []
    for source_id in REAL_SOURCE_IDS:
        frame = source_entities(source_id, target_keys, target_dois)
        x = composition_features(frame["material_key"].tolist()).astype(np.float32)
        y = frame["value"].to_numpy(float)
        groups = frame["group"].astype(str).to_numpy()
        splitter = GroupKFold(n_splits=3, shuffle=True, random_state=20260716)
        oof = np.full(len(frame), np.nan)
        for fold, (train, test) in enumerate(splitter.split(x, y, groups)):
            model = make_model(stable_seed(f"source:{source_id}:fold:{fold}"), 240)
            model.fit(x[train], y[train])
            oof[test] = model.predict(x[test])
        if not np.isfinite(oof).all():
            raise AssertionError(f"{source_id}: incomplete source OOF predictions")
        quality_rows.append(
            {
                "source": source_id,
                "entities": int(len(frame)),
                "groups": int(frame["group"].nunique()),
                "oof_r2": float(r2_score(y, oof)),
                "oof_rmse": float(math.sqrt(mean_squared_error(y, oof))),
                "oof_spearman": float(stats.spearmanr(y, oof).statistic),
            }
        )
        model = make_model(stable_seed(f"source:{source_id}:full"), 240)
        model.fit(x, y)
        predictions[source_id] = model.predict(target_x).astype(np.float32)
    return predictions, pd.DataFrame(quality_rows)


def initial_indices(target: pd.DataFrame, seed: int, target_n: int) -> list[int]:
    development = target[target["split"] == "development"]
    group_members = {
        str(group): local.index.astype(int).tolist()
        for group, local in development.groupby("group", sort=False)
    }
    ordered = sorted(
        group_members,
        key=lambda group: hashlib.sha256(f"{seed}|{group}".encode()).hexdigest(),
    )
    selected: list[int] = []
    skipped: list[str] = []
    for group in ordered:
        members = group_members[group]
        if len(selected) + len(members) <= target_n:
            selected.extend(members)
        else:
            skipped.append(group)
    if len(selected) < int(0.8 * target_n) and skipped:
        best = min(
            skipped,
            key=lambda group: (
                abs(len(selected) + len(group_members[group]) - target_n),
                group,
            ),
        )
        selected.extend(group_members[best])
    if len(selected) < 10:
        raise RuntimeError(f"Campaign {seed}: only {len(selected)} initial target entities")
    return sorted(selected)


def composition_novelty(candidate_x: np.ndarray, labelled_x: np.ndarray) -> np.ndarray:
    squared = np.sum((candidate_x[:, None, :] - labelled_x[None, :, :]) ** 2, axis=2)
    return np.sqrt(np.min(squared, axis=1))


def gate_from_gains(gains: np.ndarray) -> dict[str, float | int | bool]:
    median = float(np.median(gains))
    mean = float(np.mean(gains))
    positive = int(np.sum(gains > 0))
    admitted = bool(median >= 0.02 and positive >= 3 and mean > 0)
    weight = float(np.clip(median / 0.10, 0, 1)) if admitted else 0.0
    return {
        "median_relative_rmse_gain": median,
        "mean_relative_rmse_gain": mean,
        "positive_folds": positive,
        "admitted": admitted,
        "weight": weight,
    }


def gated_predictions(
    *,
    policy: str,
    seed: int,
    step: int,
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    labelled: list[int],
    pool: list[int],
    source_predictions: dict[str, np.ndarray],
    requested_sources: list[str],
) -> tuple[np.ndarray, dict[str, np.ndarray], list[dict]]:
    labelled_groups = target.loc[labelled, "group"].astype(str).to_numpy()
    state_token = hashlib.sha256(
        f"{seed}|{step}|".encode()
        + ",".join(str(index) for index in sorted(labelled)).encode()
    ).hexdigest()
    gate_rows: list[dict] = []
    if len(np.unique(labelled_groups)) < 5:
        zero = {
            "median_relative_rmse_gain": 0.0,
            "mean_relative_rmse_gain": 0.0,
            "positive_folds": 0,
            "admitted": False,
            "weight": 0.0,
        }
        gate_rows.append({"source": "__target__", **zero})
        gate_rows.extend({"source": source, **zero} for source in requested_sources)
        return np.zeros(len(pool)), {}, gate_rows

    labelled_x = x[labelled]
    labelled_y = y[labelled]
    splitter = GroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=stable_seed(f"folds:{state_token}"),
    )
    folds = list(splitter.split(labelled_x, labelled_y, labelled_groups))
    base_rmse: list[float] = []
    mean_rmse: list[float] = []
    augmented_rmse = {source: [] for source in requested_sources}
    for fold, (train, test) in enumerate(folds):
        model_seed = stable_seed(f"target:{state_token}:fold:{fold}")
        base = make_model(model_seed, 80).fit(labelled_x[train], labelled_y[train])
        base_prediction = base.predict(labelled_x[test])
        base_error = math.sqrt(mean_squared_error(labelled_y[test], base_prediction))
        base_rmse.append(base_error)
        mean_prediction = np.full(len(test), float(np.mean(labelled_y[train])))
        mean_rmse.append(math.sqrt(mean_squared_error(labelled_y[test], mean_prediction)))
        for source in requested_sources:
            source_labelled = source_predictions[source][labelled]
            augmented_x = np.column_stack([labelled_x, source_labelled])
            augmented = make_model(model_seed, 80).fit(augmented_x[train], labelled_y[train])
            prediction = augmented.predict(augmented_x[test])
            augmented_rmse[source].append(
                math.sqrt(mean_squared_error(labelled_y[test], prediction))
            )

    base_rmse_array = np.asarray(base_rmse)
    mean_rmse_array = np.asarray(mean_rmse)
    target_gains = np.divide(
        mean_rmse_array - base_rmse_array,
        mean_rmse_array,
        out=np.zeros_like(base_rmse_array),
        where=mean_rmse_array > 0,
    )
    target_gate = gate_from_gains(target_gains)
    gate_rows.append({"source": "__target__", **target_gate})
    source_gates: dict[str, dict] = {}
    for source in requested_sources:
        aug = np.asarray(augmented_rmse[source])
        gains = np.divide(
            base_rmse_array - aug,
            base_rmse_array,
            out=np.zeros_like(base_rmse_array),
            where=base_rmse_array > 0,
        )
        source_gates[source] = gate_from_gains(gains)
        gate_rows.append({"source": source, **source_gates[source]})

    full_seed = stable_seed(f"target:{state_token}:full")
    base_full = make_model(full_seed, 80)
    base_full.fit(labelled_x, labelled_y)
    base_pool = base_full.predict(x[pool])
    corrections: dict[str, np.ndarray] = {}
    admitted = [
        source for source in requested_sources if bool(source_gates[source]["admitted"])
    ]
    admitted = sorted(
        admitted,
        key=lambda source: (
            -float(source_gates[source]["median_relative_rmse_gain"]),
            source,
        ),
    )[:2]
    for source in admitted:
        source_labelled = source_predictions[source][labelled]
        source_pool = source_predictions[source][pool]
        augmented = make_model(full_seed, 80)
        augmented.fit(np.column_stack([labelled_x, source_labelled]), labelled_y)
        augmented_pool = augmented.predict(np.column_stack([x[pool], source_pool]))
        corrections[source] = percentile_rank(augmented_pool) - percentile_rank(base_pool)
    for row in gate_rows:
        if row["source"] not in {"__target__", *admitted}:
            row["weight"] = 0.0
            row["selected_top2"] = False
        else:
            row["selected_top2"] = row["source"] != "__target__"
    return base_pool, corrections, gate_rows


def stable_argmax(
    score: np.ndarray,
    novelty: np.ndarray,
    pool: list[int],
    target: pd.DataFrame,
) -> int:
    best_score = np.flatnonzero(score == np.nanmax(score))
    if len(best_score) > 1:
        best_novelty = np.max(novelty[best_score])
        best_score = best_score[novelty[best_score] == best_novelty]
    if len(best_score) > 1:
        return int(
            min(best_score, key=lambda position: target.at[pool[int(position)], "material_key"])
        )
    return int(best_score[0])


def run_policy(
    *,
    scope: str,
    policy: str,
    seed: int,
    target: pd.DataFrame,
    x: np.ndarray,
    x_scaled: np.ndarray,
    source_predictions: dict[str, np.ndarray],
    candidates: list[int],
    hit_set: set[int],
    initial: list[int],
    budget: int,
) -> tuple[list[dict], list[dict]]:
    y = target["value"].to_numpy(float)
    pool = list(candidates)
    labelled = list(initial)
    trajectories: list[dict] = []
    gates: list[dict] = []
    random_order: list[int] | None = None
    if policy == "uniform_random":
        rng = np.random.default_rng(stable_seed(f"random:{scope}:{seed}"))
        random_order = list(rng.permutation(pool))

    for step in range(1, budget + 1):
        novelty = composition_novelty(x_scaled[pool], x_scaled[labelled])
        novelty_rank = percentile_rank(novelty)
        acquisition_mean = np.full(len(pool), np.nan)
        if policy == "uniform_random":
            chosen = int(random_order[step - 1])
            position = pool.index(chosen)
            score = np.full(len(pool), np.nan)
        elif policy == "composition_novelty":
            score = novelty_rank
            position = stable_argmax(score, novelty, pool, target)
            chosen = pool[position]
        elif policy in STATIC_SOURCE:
            source = STATIC_SOURCE[policy]
            score = source_predictions[source][pool]
            position = stable_argmax(score, novelty, pool, target)
            chosen = pool[position]
        else:
            requested = SAFE_SOURCE.get(policy, [])
            base_pool, corrections, step_gates = gated_predictions(
                policy=policy,
                seed=seed,
                step=step,
                target=target,
                x=x,
                y=y,
                labelled=labelled,
                pool=pool,
                source_predictions=source_predictions,
                requested_sources=requested,
            )
            acquisition_mean = base_pool
            target_gate = next(row for row in step_gates if row["source"] == "__target__")
            target_component = float(target_gate["weight"]) * percentile_rank(base_pool)
            source_component = np.zeros(len(pool))
            for row in step_gates:
                source = str(row["source"])
                if source in corrections:
                    source_component += float(row["weight"]) * corrections[source]
            if policy == "safe_multisource_novelty_band" and (
                float(target_gate["weight"]) > 0
                or any(float(row["weight"]) > 0 for row in step_gates if row["source"] != "__target__")
            ):
                score = target_component + source_component
                score = np.where(novelty_rank >= 0.65, score, -np.inf)
            else:
                score = novelty_rank + target_component + source_component
            position = stable_argmax(score, novelty, pool, target)
            chosen = pool[position]
            gates.extend(
                {
                    "scope": scope,
                    "seed": seed,
                    "policy": policy,
                    "step": step,
                    **row,
                }
                for row in step_gates
            )

        trajectories.append(
            {
                "scope": scope,
                "seed": seed,
                "policy": policy,
                "step": step,
                "chosen_index": int(chosen),
                "chosen_key": target.at[chosen, "material_key"],
                "chosen_y": float(y[chosen]),
                "is_true_top5_hit": bool(chosen in hit_set),
                "acquisition_score": float(score[position]) if np.isfinite(score[position]) else np.nan,
                "target_prediction": float(acquisition_mean[position]) if np.isfinite(acquisition_mean[position]) else np.nan,
                "composition_novelty": float(novelty[position]),
                "initial_target_n": int(len(initial)),
            }
        )
        pool.pop(position)
        labelled.append(chosen)
    return trajectories, gates


def true_hit_set(target: pd.DataFrame, candidates: list[int]) -> set[int]:
    top_n = max(1, int(math.ceil(0.05 * len(candidates))))
    ordered = target.loc[candidates].sort_values(
        ["value", "material_key"], ascending=[False, True]
    )
    return set(ordered.index[:top_n].astype(int))


def run_seed_scope(
    *,
    scope: str,
    seed: int,
    policies: list[str],
    target: pd.DataFrame,
    x: np.ndarray,
    x_scaled: np.ndarray,
    base_sources: dict[str, np.ndarray],
    candidates: list[int],
    budget: int,
    initial_n: int,
) -> tuple[list[dict], list[dict]]:
    sources = {key: value.copy() for key, value in base_sources.items()}
    rng = np.random.default_rng(stable_seed(f"shuffle-obelix:{seed}"))
    sources[SHUFFLED_SOURCE_ID] = rng.permutation(sources["obelix_same_property"])
    initial = initial_indices(target, seed, initial_n)
    hit_set = true_hit_set(target, candidates)
    trajectories: list[dict] = []
    gates: list[dict] = []
    for policy in policies:
        policy_trajectory, policy_gates = run_policy(
            scope=scope,
            policy=policy,
            seed=seed,
            target=target,
            x=x,
            x_scaled=x_scaled,
            source_predictions=sources,
            candidates=candidates,
            hit_set=hit_set,
            initial=initial,
            budget=budget,
        )
        trajectories.extend(policy_trajectory)
        gates.extend(policy_gates)
    return trajectories, gates


def utility_table(
    trajectories: pd.DataFrame,
    target: pd.DataFrame,
    pools: dict[str, list[int]],
    budget: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for (scope, seed, policy), local in trajectories.groupby(
        ["scope", "seed", "policy"], sort=False
    ):
        local = local.sort_values("step")
        hits = local["is_true_top5_hit"].astype(bool).to_numpy()
        cumulative = np.cumsum(hits)
        hit_steps = np.flatnonzero(hits)
        pool = pools[str(scope)]
        pool_max = float(target.loc[pool, "value"].max())
        top_n = max(1, int(math.ceil(0.05 * len(pool))))
        row = {
            "scope": scope,
            "seed": int(seed),
            "policy": policy,
            "budget": budget,
            "candidate_n": len(pool),
            "true_top_n": top_n,
            "auc20": float(np.sum(cumulative[: min(20, budget)])),
            "first_hit": int(hit_steps[0] + 1) if len(hit_steps) else budget + 1,
        }
        for horizon in (10, 20, 40):
            if budget < horizon:
                row[f"recall_at_{horizon}"] = np.nan
                row[f"best_y_at_{horizon}"] = np.nan
                row[f"regret_at_{horizon}"] = np.nan
            else:
                horizon_local = local.iloc[:horizon]
                count = int(horizon_local["is_true_top5_hit"].astype(bool).sum())
                best = float(horizon_local["chosen_y"].max())
                row[f"recall_at_{horizon}"] = float(count / top_n)
                row[f"best_y_at_{horizon}"] = best
                row[f"regret_at_{horizon}"] = float(pool_max - best)
        rows.append(row)
    return pd.DataFrame(rows)


def bootstrap_interval(effect: np.ndarray, draws: int, label: str) -> list[float]:
    rng = np.random.default_rng(stable_seed(f"bootstrap:{label}"))
    indices = rng.integers(0, len(effect), size=(draws, len(effect)))
    values = np.mean(effect[indices], axis=1)
    return [float(value) for value in np.quantile(values, [0.025, 0.975])]


def signflip_p(effect: np.ndarray, draws: int, label: str) -> float:
    observed = float(np.mean(effect))
    rng = np.random.default_rng(stable_seed(f"signflip:{label}"))
    exceed = 0
    remaining = draws
    while remaining:
        batch = min(1000, remaining)
        signs = rng.choice((-1.0, 1.0), size=(batch, len(effect)))
        exceed += int(np.sum(np.mean(signs * effect, axis=1) >= observed))
        remaining -= batch
    return float((exceed + 1) / (draws + 1))


def holm(values: pd.Series) -> pd.Series:
    output = pd.Series(index=values.index, dtype=float)
    order = values.sort_values().index.tolist()
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (len(order) - rank) * float(values[index]))
        running = max(running, candidate)
        output[index] = running
    return output


def contrast_table(utilities: pd.DataFrame, design: dict) -> pd.DataFrame:
    rows: list[dict] = []
    bootstrap_n = int(design["inference"]["paired_bootstrap_replicates"])
    signflip_n = int(design["inference"]["paired_sign_flip_draws"])
    for scope, local in utilities.groupby("scope"):
        for family, left, right in PRIMARY_COMPARISONS:
            pivot_auc = local.pivot(index="seed", columns="policy", values="auc20")
            pivot_first = local.pivot(index="seed", columns="policy", values="first_hit")
            pivot_recall = local.pivot(index="seed", columns="policy", values="recall_at_20")
            auc_effect = (pivot_auc[left] - pivot_auc[right]).to_numpy(float)
            first_saved = (pivot_first[right] - pivot_first[left]).to_numpy(float)
            label = f"{scope}:{left}:{right}"
            right_mean = float(pivot_auc[right].mean())
            rows.append(
                {
                    "scope": scope,
                    "family": family,
                    "left_policy": left,
                    "right_policy": right,
                    "seeds": int(len(auc_effect)),
                    "left_auc20_mean": float(pivot_auc[left].mean()),
                    "right_auc20_mean": right_mean,
                    "mean_auc20_gain": float(np.mean(auc_effect)),
                    "relative_auc20_gain": float(np.mean(auc_effect) / right_mean) if right_mean > 0 else np.nan,
                    "auc20_gain_ci95": bootstrap_interval(auc_effect, bootstrap_n, label + ":auc"),
                    "fraction_campaigns_improved": float(np.mean(auc_effect > 0)),
                    "signflip_p_one_sided": signflip_p(auc_effect, signflip_n, label),
                    "left_first_hit_mean": float(pivot_first[left].mean()),
                    "right_first_hit_mean": float(pivot_first[right].mean()),
                    "mean_first_hit_saved": float(np.mean(first_saved)),
                    "first_hit_saved_ci95": bootstrap_interval(first_saved, bootstrap_n, label + ":first"),
                    "left_recall_at_20_mean": float(pivot_recall[left].mean()),
                }
            )
    frame = pd.DataFrame(rows)
    frame["holm_p"] = np.nan
    for _, local in frame.groupby("scope"):
        frame.loc[local.index, "holm_p"] = holm(local["signflip_p_one_sided"])
    frame["passes_incremental_statistical"] = frame.apply(
        lambda row: bool(row["holm_p"] <= 0.05 and row["auc20_gain_ci95"][0] > 0), axis=1
    )
    frame["passes_incremental_practical"] = frame["relative_auc20_gain"] >= 0.20
    frame["passes_consistency"] = frame["fraction_campaigns_improved"] >= 0.60
    frame["passes_first_hit_noninferiority"] = frame.apply(
        lambda row: bool(
            row["left_first_hit_mean"] <= row["right_first_hit_mean"] + 2
            and row["first_hit_saved_ci95"][0] > -2
        ),
        axis=1,
    )
    frame["passes_absolute_recall"] = frame["left_recall_at_20_mean"] >= 0.50
    return frame


def gate_summary(gates: pd.DataFrame) -> pd.DataFrame:
    if gates.empty:
        return pd.DataFrame()
    return (
        gates.groupby(["scope", "policy", "source"], as_index=False)
        .agg(
            evaluated_steps=("step", "size"),
            admission_rate=("admitted", "mean"),
            selected_rate=("selected_top2", "mean"),
            mean_weight=("weight", "mean"),
            median_weight=("weight", "median"),
            median_cv_gain=("median_relative_rmse_gain", "median"),
        )
    )


def validate_freezes(design: dict, implementation: dict, audit: dict) -> None:
    if file_hash(DESIGN_PATH, "sha256") != implementation["parent_design_sha256"]:
        raise AssertionError("Parent design hash changed after implementation freeze")
    if file_hash(AMENDMENT_PATH, "sha256") != implementation["schema_amendment_sha256"]:
        raise AssertionError("Schema amendment hash changed")
    if canonical_json_hash(AUDIT_PATH) != REQUIRED_CANONICAL_AUDIT_SHA256:
        raise AssertionError("Canonical target audit content changed after freeze")
    if file_hash(TARGET_PATH, "md5") != implementation["target_md5"]:
        raise AssertionError("Target file hash changed")
    if design["policies"] != CONFIRMATORY_POLICIES:
        raise AssertionError("Confirmatory policy order differs from frozen design")
    if audit["status"] != "pass":
        raise AssertionError("Target/source audit did not pass")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    implementation = json.loads(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    validate_freezes(design, implementation, audit)
    target, x, x_scaled = load_target()
    candidate = target.index[target["split"] == "candidate"].astype(int).tolist()
    development = target.index[target["split"] == "development"].astype(int).tolist()
    distances = composition_novelty(x_scaled[candidate], x_scaled[development])
    hard_n = max(1, int(math.ceil(0.40 * len(candidate))))
    hard = [candidate[index] for index in np.argsort(distances)[-hard_n:]]
    pools = {"external_candidate": candidate, "hard_ood_40pct": hard}
    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "validated",
                    "design_sha256": file_hash(DESIGN_PATH, "sha256"),
                    "implementation_sha256": file_hash(IMPLEMENTATION_PATH, "sha256"),
                    "inference_amendment_sha256": file_hash(INFERENCE_AMENDMENT_PATH, "sha256"),
                    "state_match_amendment_sha256": file_hash(STATE_MATCH_AMENDMENT_PATH, "sha256"),
                    "infrastructure_amendment_sha256": file_hash(INFRASTRUCTURE_AMENDMENT_PATH, "sha256"),
                    "verifier_amendment_sha256": file_hash(VERIFIER_AMENDMENT_PATH, "sha256"),
                    "target_md5": file_hash(TARGET_PATH, "md5"),
                    "target_entities": len(target),
                    "candidate_pools": {key: len(value) for key, value in pools.items()},
                    "confirmatory_policies": len(CONFIRMATORY_POLICIES),
                    "primary_contrasts_per_scope": len(PRIMARY_COMPARISONS),
                },
                indent=2,
            )
        )
        return

    source_predictions, source_quality = fit_source_models(target, x)
    smoke = bool(args.smoke)
    seeds = 2 if smoke else int(design["campaign"]["paired_seeds"])
    budget = 3 if smoke else int(design["campaign"]["budget"])
    initial_n = int(design["campaign"]["initial_target_labels"])
    policies = POLICIES if not smoke else [
        "uniform_random",
        "composition_novelty",
        "safe_target_novelty",
        "safe_obelix_residual",
        "safe_estm_residual",
        "safe_borg_residual_control",
        "safe_multisource_residual",
        "safe_multisource_novelty_band",
    ]
    workers = args.workers or int(os.environ.get("CALTECH_WORKERS", min(4, os.cpu_count() or 1)))
    batch_size = int(os.environ.get("CALTECH_BATCH_SIZE", max(1, workers)))
    prefix = "caltech_ionic_external_smoke" if smoke else "caltech_ionic_external_policy"
    checkpoint_key = (
        file_hash(IMPLEMENTATION_PATH, "sha256")[:8]
        + "-"
        + file_hash(STATE_MATCH_AMENDMENT_PATH, "sha256")[:8]
        + "-"
        + file_hash(INFRASTRUCTURE_AMENDMENT_PATH, "sha256")[:8]
    )
    checkpoint = RESULTS / f"{prefix}_checkpoints" / checkpoint_key
    checkpoint.mkdir(parents=True, exist_ok=True)
    trajectory_parts: list[pd.DataFrame] = []
    gate_parts: list[pd.DataFrame] = []
    for scope, candidates in pools.items():
        for start in range(0, seeds, batch_size):
            stop = min(seeds, start + batch_size)
            trajectory_path = checkpoint / f"{scope}__{start:04d}-{stop:04d}__trajectory.csv"
            gate_path = checkpoint / f"{scope}__{start:04d}-{stop:04d}__gates.csv"
            if not trajectory_path.exists() or not gate_path.exists():
                completed = Parallel(n_jobs=workers, verbose=0)(
                    delayed(run_seed_scope)(
                        scope=scope,
                        seed=seed,
                        policies=policies,
                        target=target,
                        x=x,
                        x_scaled=x_scaled,
                        base_sources=source_predictions,
                        candidates=candidates,
                        budget=budget,
                        initial_n=initial_n,
                    )
                    for seed in range(start, stop)
                )
                pd.DataFrame(
                    [row for batch in completed for row in batch[0]]
                ).to_csv(trajectory_path, index=False)
                pd.DataFrame(
                    [row for batch in completed for row in batch[1]]
                ).to_csv(gate_path, index=False)
            trajectory_parts.append(pd.read_csv(trajectory_path))
            gate_parts.append(pd.read_csv(gate_path))

    trajectories = pd.concat(trajectory_parts, ignore_index=True)
    gates = pd.concat(gate_parts, ignore_index=True)
    expected = len(pools) * seeds * len(policies) * budget
    if len(trajectories) != expected:
        raise AssertionError(f"Expected {expected} trajectory rows, found {len(trajectories)}")
    utilities = utility_table(trajectories, target, pools, budget)
    gate_summary_frame = gate_summary(gates)

    RESULTS.mkdir(exist_ok=True)
    trajectories.to_csv(RESULTS / f"{prefix}_trajectories.csv", index=False)
    gates.to_csv(RESULTS / f"{prefix}_gates.csv", index=False)
    utilities.to_csv(RESULTS / f"{prefix}_utility.csv", index=False)
    gate_summary_frame.to_csv(RESULTS / f"{prefix}_gate_summary.csv", index=False)
    source_quality.to_csv(RESULTS / f"{prefix}_source_quality.csv", index=False)

    summary: dict[str, object] = {
        "status": "smoke-complete" if smoke else "complete",
        "design_sha256": file_hash(DESIGN_PATH, "sha256"),
        "implementation_sha256": file_hash(IMPLEMENTATION_PATH, "sha256"),
        "inference_amendment_sha256": file_hash(INFERENCE_AMENDMENT_PATH, "sha256"),
        "state_match_amendment_sha256": file_hash(STATE_MATCH_AMENDMENT_PATH, "sha256"),
        "infrastructure_amendment_sha256": file_hash(INFRASTRUCTURE_AMENDMENT_PATH, "sha256"),
        "verifier_amendment_sha256": file_hash(VERIFIER_AMENDMENT_PATH, "sha256"),
        "target_md5": file_hash(TARGET_PATH, "md5"),
        "seeds": seeds,
        "budget": budget,
        "workers": workers,
        "policies": policies,
        "candidate_pools": {key: len(value) for key, value in pools.items()},
        "trajectory_rows": len(trajectories),
        "gate_rows": len(gates),
        "source_quality": source_quality.to_dict("records"),
    }
    if not smoke:
        contrasts = contrast_table(utilities, design)
        contrasts.to_csv(RESULTS / f"{prefix}_contrasts.csv", index=False)
        wrong_policy_source = {
            "safe_borg_residual_control": "borg_mechanical_control",
            "safe_ocx_residual_control": "ocx_catalysis_control",
            "safe_shuffled_obelix_control": SHUFFLED_SOURCE_ID,
        }
        negative_guard: list[dict] = []
        for (scope, policy), local in gate_summary_frame.groupby(["scope", "policy"]):
            if policy in wrong_policy_source:
                source = wrong_policy_source[policy]
                row = local[local["source"] == source].iloc[0]
                negative_guard.append(
                    {
                        "scope": scope,
                        "policy": policy,
                        "source": source,
                        "admission_rate": float(row["admission_rate"]),
                        "mean_weight": float(row["mean_weight"]),
                        "passes": bool(row["admission_rate"] < 0.20 and row["mean_weight"] < 0.10),
                    }
                )
        summary["primary_contrasts"] = contrasts.to_dict("records")
        summary["negative_transfer_guard"] = negative_guard
        summary["all_negative_transfer_guards_pass"] = bool(
            negative_guard and all(row["passes"] for row in negative_guard)
        )
        summary["claim_guard"] = (
            "This retrospective external benchmark can validate at most one source-to-policy edge. "
            "It does not establish prospective discovery or new science."
        )
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
