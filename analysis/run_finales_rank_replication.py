"""Run the frozen FINALES second-recipient ordinal-transfer test.

The design is frozen in ``finales_rank_replication_design.json``.  The
transferred object is the unchanged CALiSol conductivity ranking used in the
independent SolventSeg audit.  FINALES outcomes are used only after the design
and archive hashes have been fixed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import stats
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "finales_rank_replication_design.json"
FREEZE_PATH = HERE / "finales_rank_replication_freeze.json"
TARGET_DIR = HERE / "target_metadata" / "finales_rank_replication"
DONOR_PATH = (
    HERE
    / "review_packages"
    / "edison"
    / "legacy_kosmos_2026-07-30"
    / "solventseg_validation"
    / "CALiSol23_LiPF6_EC_EMC_harmonized.csv"
)
RAW_CALISOL_PATH = (
    Path.home()
    / ".collective_data_cache"
    / "calisol-23"
    / "calisol23_DOI_10.11583DTU.c.6929599.csv"
)

INCHI = {
    "LiPF6": "AXPLOJNSKRXQPA-UHFFFAOYSA-N",
    "EC": "KMTRUDSVKNLOMY-UHFFFAOYSA-N",
    "EMC": "JBTWLSYIZRCDFO-UHFFFAOYSA-N",
}
MOLAR_MASS = {"LiPF6": 151.9, "EC": 88.06, "EMC": 104.1}
FEATURES = ["EC_wt", "EMC_wt", "LiPF6_wt", "temperature_C"]
TARGET = "conductivity"
RANDOM_STATE = 2025


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def locate_member(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {suffix} member, found {matches}")
    return matches[0]


def formulation_to_weight(formulation: list[dict[str, Any]]) -> dict[str, float]:
    mole: dict[str, float] = {}
    for item in formulation:
        key = str(item["chemical"]["InChIKey"])
        for name, expected in INCHI.items():
            if key == expected:
                mole[name] = float(item["fraction"])
                break
    if set(mole) != set(INCHI):
        raise AssertionError(f"Unexpected formulation chemistry: {mole}")
    total_mole = sum(mole.values())
    if not np.isfinite(total_mole) or total_mole <= 0:
        raise AssertionError("Invalid mole-fraction total")
    mole = {key: value / total_mole for key, value in mole.items()}
    masses = {key: mole[key] * MOLAR_MASS[key] for key in mole}
    total_mass = sum(masses.values())
    return {
        "LiPF6_wt": masses["LiPF6"] / total_mass,
        "EC_wt": masses["EC"] / total_mass,
        "EMC_wt": masses["EMC"] / total_mass,
    }


def load_phase(path: Path, phase: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        member = locate_member(archive, "results_for_requests.json")
        records = json.loads(archive.read(member))

    rows: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for record in records:
        result = record.get("result", {})
        if result.get("quantity") != "conductivity":
            continue
        if "two_electrode" not in result.get("method", []):
            continue
        status = str(record.get("status"))
        status_counts[status] = status_counts.get(status, 0) + 1
        if status != "original":
            continue
        conductivity = result.get("data", {}).get("conductivity", {})
        meta = conductivity.get("meta", {})
        values = np.asarray(conductivity.get("values", []), dtype=float)
        rating = float(meta.get("rating", np.nan))
        success = bool(meta.get("success", False))
        if not success or not np.isfinite(rating) or rating < 4:
            continue
        if len(values) == 0 or not np.all(np.isfinite(values)):
            continue
        formulation = result["parameters"]["two_electrode"]["formulation"]
        weights = formulation_to_weight(formulation)
        temperature_k = float(conductivity["temperature"])
        rows.append(
            {
                "phase": phase,
                "result_uuid": str(record["uuid"]),
                "request_uuid": str(result["request_uuid"]),
                "ctime": str(record["ctime"]),
                **weights,
                "temperature_C": temperature_k - 273.15,
                TARGET: float(np.median(values)),
                "replicate_sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "instrument_replicates": int(len(values)),
                "rating": rating,
            }
        )

    frame = pd.DataFrame(rows).sort_values(["ctime", "request_uuid"]).reset_index(drop=True)
    if frame.empty:
        raise AssertionError(f"No eligible experimental rows in {phase}")
    frame["formulation_key"] = frame[["EC_wt", "EMC_wt", "LiPF6_wt"]].round(8).astype(str).agg("|".join, axis=1)

    grouped: list[dict[str, Any]] = []
    for key, group in frame.groupby("formulation_key", sort=False):
        ordered = group.sort_values(["ctime", "request_uuid"])
        grouped.append(
            {
                "phase": phase,
                "formulation_key": key,
                "first_ctime": str(ordered.iloc[0]["ctime"]),
                "first_request_uuid": str(ordered.iloc[0]["request_uuid"]),
                "EC_wt": float(group["EC_wt"].median()),
                "EMC_wt": float(group["EMC_wt"].median()),
                "LiPF6_wt": float(group["LiPF6_wt"].median()),
                "temperature_C": float(group["temperature_C"].median()),
                TARGET: float(group[TARGET].median()),
                "measurement_events": int(len(group)),
                "instrument_replicates": int(group["instrument_replicates"].sum()),
                "minimum_rating": float(group["rating"].min()),
            }
        )
    candidates = pd.DataFrame(grouped).sort_values(
        ["first_ctime", "first_request_uuid"]
    ).reset_index(drop=True)
    candidates["candidate_index"] = np.arange(len(candidates), dtype=int)
    audit = {
        "phase": phase,
        "all_result_records": len(records),
        "two_electrode_status_counts": status_counts,
        "eligible_measurement_events": len(frame),
        "eligible_unique_formulations": len(candidates),
        "temperature_C_range": [
            float(candidates["temperature_C"].min()),
            float(candidates["temperature_C"].max()),
        ],
        "ratings": sorted(float(value) for value in candidates["minimum_rating"].unique()),
        "duplicate_measurement_events_collapsed": int(len(frame) - len(candidates)),
    }
    return candidates, audit


def concordance(y: np.ndarray, score: np.ndarray, temp: np.ndarray, tolerance: float) -> tuple[float, int]:
    left, right = np.triu_indices(len(y), k=1)
    keep = np.abs(temp[left] - temp[right]) <= tolerance
    dy = y[left] - y[right]
    ds = score[left] - score[right]
    keep &= (dy != 0) & (ds != 0)
    if not np.any(keep):
        return np.nan, 0
    agreements = np.sign(dy[keep]) == np.sign(ds[keep])
    return float(np.mean(agreements)), int(np.sum(keep))


def bin_metrics(frame: pd.DataFrame, score_col: str) -> dict[str, float]:
    work = frame.copy()
    work["temperature_bin_C"] = np.floor(work["temperature_C"] / 2.0) * 2.0
    rhos: list[float] = []
    hits = 0
    predicted = 0
    regrets: list[float] = []
    for _, group in work.groupby("temperature_bin_C"):
        if len(group) < 4:
            continue
        rho = stats.spearmanr(group[TARGET], group[score_col]).statistic
        if np.isfinite(rho):
            rhos.append(float(rho))
        n_top = max(1, int(math.ceil(0.25 * len(group))))
        true_top = set(group.nlargest(n_top, TARGET).index)
        pred_top = set(group.nlargest(n_top, score_col).index)
        hits += len(true_top & pred_top)
        predicted += len(pred_top)
        chosen = group.loc[group[score_col].idxmax(), TARGET]
        true_max = float(group[TARGET].max())
        true_min = float(group[TARGET].min())
        if true_max > true_min:
            regrets.append(float((true_max - chosen) / (true_max - true_min)))
    return {
        "within_temperature_mean_rho": float(np.mean(rhos)) if rhos else np.nan,
        "temperature_bins_with_rho": int(len(rhos)),
        "top_quartile_precision": float(hits / predicted) if predicted else np.nan,
        "normalized_regret": float(np.mean(regrets)) if regrets else np.nan,
        "temperature_bins_with_regret": int(len(regrets)),
    }


def make_target_models() -> dict[str, Any]:
    return {
        "target_extra_trees": ExtraTreesRegressor(
            n_estimators=500,
            min_samples_leaf=1,
            max_features=1.0,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "target_hist_gradient_boosting": HistGradientBoostingRegressor(
            random_state=RANDOM_STATE
        ),
        "target_linear": LinearRegression(),
    }


def add_predictions(frame: pd.DataFrame, donor: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if len(frame) <= 3:
        raise AssertionError("Fewer than four eligible formulations")
    work = frame.copy()
    work["split"] = np.where(work["candidate_index"] < 3, "anchor", "evaluation")
    anchors = work.loc[work["split"] == "anchor"]

    donor_model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
    donor_model.fit(donor[FEATURES], donor["conductivity_mS_cm"])
    work["calisol_rank_score"] = donor_model.predict(work[FEATURES])

    baseline_primary: dict[str, float] = {}
    for name, model in make_target_models().items():
        model.fit(anchors[FEATURES], anchors[TARGET])
        work[name] = model.predict(work[FEATURES])
        evaluation = work.loc[work["split"] == "evaluation"]
        value, _ = concordance(
            evaluation[TARGET].to_numpy(),
            evaluation[name].to_numpy(),
            evaluation["temperature_C"].to_numpy(),
            1.0,
        )
        baseline_primary[name] = value

    eligible = {name: value for name, value in baseline_primary.items() if np.isfinite(value)}
    if not eligible:
        raise AssertionError("No eligible target-only baseline")
    strongest = max(eligible, key=eligible.get)
    work["temperature_only_score"] = work["temperature_C"]
    work["salt_fraction_only_score"] = work["LiPF6_wt"]
    return work, strongest


def scope_metrics(frame: pd.DataFrame, score_columns: list[str], tolerance: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for score_col in score_columns:
        value, pairs = concordance(
            frame[TARGET].to_numpy(),
            frame[score_col].to_numpy(),
            frame["temperature_C"].to_numpy(),
            tolerance,
        )
        pooled_rho = stats.spearmanr(frame[TARGET], frame[score_col]).statistic
        rows.append(
            {
                "score": score_col,
                "temperature_tolerance_C": tolerance,
                "pairwise_concordance": value,
                "eligible_pairs": pairs,
                "pooled_spearman_rho": float(pooled_rho),
                **bin_metrics(frame, score_col),
            }
        )
    return pd.DataFrame(rows)


def hard_ood_mask(frame: pd.DataFrame) -> np.ndarray:
    anchors = frame.loc[frame["split"] == "anchor", ["EC_wt", "EMC_wt", "LiPF6_wt"]]
    evaluation = frame.loc[frame["split"] == "evaluation", ["EC_wt", "EMC_wt", "LiPF6_wt"]]
    scaler = StandardScaler().fit(frame[["EC_wt", "EMC_wt", "LiPF6_wt"]])
    anchor_z = scaler.transform(anchors)
    eval_z = scaler.transform(evaluation)
    distances = np.sqrt(((eval_z[:, None, :] - anchor_z[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    count = max(1, int(math.ceil(0.40 * len(evaluation))))
    order = np.argsort(distances)[::-1]
    mask = np.zeros(len(evaluation), dtype=bool)
    mask[order[:count]] = True
    return mask


def bootstrap_advantage(
    evaluation: pd.DataFrame,
    donor_col: str,
    baseline_col: str,
    tolerance: float,
    replicates: int,
) -> np.ndarray:
    rng = np.random.default_rng(20260730)
    effects: list[float] = []
    n = len(evaluation)
    for _ in range(replicates):
        sample = evaluation.iloc[rng.integers(0, n, size=n)]
        donor_c, pairs = concordance(
            sample[TARGET].to_numpy(),
            sample[donor_col].to_numpy(),
            sample["temperature_C"].to_numpy(),
            tolerance,
        )
        baseline_c, _ = concordance(
            sample[TARGET].to_numpy(),
            sample[baseline_col].to_numpy(),
            sample["temperature_C"].to_numpy(),
            tolerance,
        )
        if pairs > 0 and np.isfinite(donor_c) and np.isfinite(baseline_c):
            effects.append(float(donor_c - baseline_c))
    return np.asarray(effects, dtype=float)


def permutation_null(
    donor: pd.DataFrame,
    evaluation: pd.DataFrame,
    tolerance: float,
    replicates: int,
) -> np.ndarray:
    rng = np.random.default_rng(20260731)
    donor_y = donor["conductivity_mS_cm"].to_numpy()
    seeds = rng.integers(0, np.iinfo(np.uint32).max, size=replicates, dtype=np.uint32)

    def one(seed: np.uint32) -> float:
        local_rng = np.random.default_rng(int(seed))
        model = HistGradientBoostingRegressor(random_state=RANDOM_STATE)
        model.fit(donor[FEATURES], local_rng.permutation(donor_y))
        score = model.predict(evaluation[FEATURES])
        value, _ = concordance(
            evaluation[TARGET].to_numpy(),
            score,
            evaluation["temperature_C"].to_numpy(),
            tolerance,
        )
        return float(value)

    values = Parallel(n_jobs=-1, prefer="processes", batch_size="auto")(
        delayed(one)(seed) for seed in seeds
    )
    return np.asarray(values, dtype=float)


def wrong_donor_eligibility() -> dict[str, Any]:
    if not RAW_CALISOL_PATH.exists():
        return {"eligible": False, "reason": "raw CALiSol file unavailable"}
    frame = pd.read_csv(RAW_CALISOL_PATH)
    solvent_marker = frame.columns.get_loc("solvent ratio type") + 1
    solvents = list(frame.columns[solvent_marker:])
    other = [column for column in solvents if column not in {"EC", "EMC"}]
    mask = (
        (frame["salt"] != "LiPF6")
        & (pd.to_numeric(frame["EC"], errors="coerce").fillna(0) > 0)
        & (pd.to_numeric(frame["EMC"], errors="coerce").fillna(0) > 0)
        & (frame[other].apply(pd.to_numeric, errors="coerce").fillna(0).abs().sum(axis=1) == 0)
    )
    strict = frame.loc[mask]
    return {
        "eligible": bool(len(strict) >= 205),
        "strict_EC_EMC_non_LiPF6_rows": int(len(strict)),
        "minimum_rows": 205,
        "salt_counts": strict["salt"].value_counts().to_dict(),
        "reason": None if len(strict) >= 205 else "fewer than half the real-donor rows",
    }


def run(args: argparse.Namespace) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if digest(DESIGN_PATH) != freeze["design"]["sha256"]:
        raise RuntimeError("Frozen design hash changed")
    if digest(DONOR_PATH) != freeze["donor"]["sha256"]:
        raise RuntimeError("Frozen donor hash changed")
    if digest(TARGET_DIR / "multi_task.zip", "md5") != design["recipient"]["primary_archive"]["md5"]:
        raise RuntimeError("Primary archive MD5 mismatch")
    if digest(TARGET_DIR / "single_task.zip", "md5") != design["recipient"]["secondary_archive"]["md5"]:
        raise RuntimeError("Secondary archive MD5 mismatch")

    donor = pd.read_csv(DONOR_PATH)
    if len(donor) != design["donor"]["rows"]:
        raise AssertionError("Donor row count changed")
    primary, primary_audit = load_phase(TARGET_DIR / "multi_task.zip", "multitask_2023_11")
    secondary, secondary_audit = load_phase(TARGET_DIR / "single_task.zip", "singletask_2023_09")

    primary, strongest = add_predictions(primary, donor)
    secondary, secondary_strongest = add_predictions(secondary, donor)
    score_columns = [
        "calisol_rank_score",
        *make_target_models().keys(),
        "temperature_only_score",
        "salt_fraction_only_score",
    ]

    primary_eval = primary.loc[primary["split"] == "evaluation"].copy()
    tolerance = 1.0
    _, pair_count = concordance(
        primary_eval[TARGET].to_numpy(),
        primary_eval["calisol_rank_score"].to_numpy(),
        primary_eval["temperature_C"].to_numpy(),
        tolerance,
    )
    if pair_count < 50:
        tolerance = 2.0
        _, pair_count = concordance(
            primary_eval[TARGET].to_numpy(),
            primary_eval["calisol_rank_score"].to_numpy(),
            primary_eval["temperature_C"].to_numpy(),
            tolerance,
        )
    primary_eligible = pair_count >= 50

    primary_metrics = scope_metrics(primary_eval, score_columns, tolerance)
    hard_mask = hard_ood_mask(primary)
    hard_eval = primary_eval.iloc[np.flatnonzero(hard_mask)].copy()
    hard_metrics = scope_metrics(hard_eval, score_columns, tolerance)
    secondary_eval = secondary.loc[secondary["split"] == "evaluation"].copy()
    secondary_metrics = scope_metrics(secondary_eval, score_columns, tolerance)
    primary_metrics.insert(0, "scope", "primary_multitask")
    hard_metrics.insert(0, "scope", "primary_hard_ood_40pct")
    secondary_metrics.insert(0, "scope", "secondary_singletask")
    metrics = pd.concat([primary_metrics, hard_metrics, secondary_metrics], ignore_index=True)

    metric_lookup = primary_metrics.set_index("score")["pairwise_concordance"]
    donor_c = float(metric_lookup["calisol_rank_score"])
    baseline_c = float(metric_lookup[strongest])
    observed_advantage = donor_c - baseline_c

    bootstrap = (
        bootstrap_advantage(
            primary_eval,
            "calisol_rank_score",
            strongest,
            tolerance,
            args.bootstrap,
        )
        if primary_eligible
        else np.asarray([], dtype=float)
    )
    null = (
        permutation_null(donor, primary_eval, tolerance, args.permutations)
        if primary_eligible
        else np.asarray([], dtype=float)
    )
    ci = (
        [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))]
        if len(bootstrap)
        else [None, None]
    )
    permutation_p = (
        float((1 + np.sum(null >= donor_c)) / (len(null) + 1))
        if len(null)
        else None
    )

    primary_table = primary_metrics.set_index("score")
    donor_row = primary_table.loc["calisol_rank_score"]
    baseline_row = primary_table.loc[strongest]
    wrong_control = wrong_donor_eligibility()
    gates = {
        "archive_and_donor_hashes_match": True,
        "recipient_doi_absent_from_donor": not donor["source_doi"].astype(str).str.contains(
            "10.1002/aenm.202403263", regex=False
        ).any(),
        "at_least_50_temperature_matched_pairs": primary_eligible,
        "concordance_advantage_at_least_0_10": observed_advantage >= 0.10,
        "bootstrap_interval_above_zero": ci[0] is not None and ci[0] > 0,
        "permutation_p_at_most_0_05": permutation_p is not None and permutation_p <= 0.05,
        "top_quartile_precision_improved": float(donor_row["top_quartile_precision"])
        > float(baseline_row["top_quartile_precision"]),
        "normalized_regret_improved": float(donor_row["normalized_regret"])
        < float(baseline_row["normalized_regret"]),
        "wrong_donor_gate": True if not wrong_control["eligible"] else None,
    }
    if wrong_control["eligible"]:
        raise RuntimeError("Wrong donor became eligible but is not implemented; stop before decision")
    success = all(value is True for value in gates.values())

    primary["hard_ood_40pct"] = False
    primary.loc[primary_eval.index[hard_mask], "hard_ood_40pct"] = True
    primary.to_csv(RESULTS / "finales_rank_replication_candidates.csv", index=False)
    secondary.to_csv(RESULTS / "finales_rank_replication_secondary_candidates.csv", index=False)
    metrics.to_csv(RESULTS / "finales_rank_replication_metrics.csv", index=False)
    pd.DataFrame({"bootstrap_advantage": bootstrap}).to_csv(
        RESULTS / "finales_rank_replication_bootstrap.csv", index=False
    )
    pd.DataFrame({"shuffled_donor_concordance": null}).to_csv(
        RESULTS / "finales_rank_replication_shuffled_null.csv", index=False
    )

    summary = {
        "status": "verified-complete" if primary_eligible else "primary-ineligible",
        "decision": "replicated" if success else ("not-replicated" if primary_eligible else "ineligible"),
        "design_sha256": digest(DESIGN_PATH),
        "freeze_sha256": digest(FREEZE_PATH),
        "donor_sha256": digest(DONOR_PATH),
        "recipient_audit": {
            "primary": primary_audit,
            "secondary": secondary_audit,
        },
        "primary": {
            "anchors": 3,
            "evaluation_formulations": len(primary_eval),
            "temperature_tolerance_C": tolerance,
            "eligible_pairs": pair_count,
            "donor_concordance": donor_c,
            "strongest_recipient_baseline": strongest,
            "strongest_baseline_concordance": baseline_c,
            "concordance_advantage": observed_advantage,
            "bootstrap_ci95": ci,
            "permutation_p": permutation_p,
            "donor_top_quartile_precision": float(donor_row["top_quartile_precision"]),
            "baseline_top_quartile_precision": float(baseline_row["top_quartile_precision"]),
            "donor_normalized_regret": float(donor_row["normalized_regret"]),
            "baseline_normalized_regret": float(baseline_row["normalized_regret"]),
        },
        "secondary": {
            "strongest_recipient_baseline": secondary_strongest,
        },
        "wrong_donor_control": wrong_control,
        "gates": gates,
        "success_gate_passed": success,
        "claim_guard": design["claim_guard"],
    }
    (RESULTS / "finales_rank_replication_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", type=int, default=20000)
    parser.add_argument("--permutations", type=int, default=2000)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
