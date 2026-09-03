"""Frozen two-way cluster bootstrap for the state-matched MPEA robustness run."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN = HERE / "state_matched_mpea_balam_design.json"
PREDICTIONS = RESULTS / "state_matched_mpea_balam_predictions.csv"
SCREEN_SUMMARY = RESULTS / "state_matched_mpea_balam_summary.json"
BOOTSTRAP = RESULTS / "state_matched_mpea_balam_bootstrap.csv.gz"
SUMMARY = RESULTS / "state_matched_mpea_balam_bootstrap_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--design-path", type=Path, default=DESIGN)
    parser.add_argument("--input-prefix", default="state_matched_mpea_balam")
    parser.add_argument("--output-prefix", default="state_matched_mpea_balam")
    return parser.parse_args()


def arrays(
    frame: pd.DataFrame,
    groups: list[str],
    runs: list[str],
    scope: str,
    prediction: str,
) -> dict[str, np.ndarray]:
    work = frame[frame["scope"] == scope].copy()
    work["run"] = (
        work["repeat"].astype(str) + "|" + work["learner"].astype(str)
    )
    work["base_sse"] = (
        work["observed_log10_ys"] - work["state_only"]
    ) ** 2
    work["aug_sse"] = (
        work["observed_log10_ys"] - work[prediction]
    ) ** 2
    work["y"] = work["observed_log10_ys"]
    work["y2"] = work["observed_log10_ys"] ** 2
    grouped = (
        work.groupby(["group", "run"], as_index=False)
        .agg(
            base_sse=("base_sse", "sum"),
            aug_sse=("aug_sse", "sum"),
            y_sum=("y", "sum"),
            y2_sum=("y2", "sum"),
            n=("y", "size"),
        )
    )
    index = pd.MultiIndex.from_product([groups, runs], names=["group", "run"])
    grouped = grouped.set_index(["group", "run"]).reindex(index, fill_value=0)
    shape = (len(groups), len(runs))
    return {
        column: grouped[column].to_numpy(float).reshape(shape)
        for column in ("base_sse", "aug_sse", "y_sum", "y2_sum", "n")
    }


def weighted_sum(
    values: np.ndarray,
    group_weights: np.ndarray,
    run_weights: np.ndarray,
) -> np.ndarray:
    return np.einsum("bg,gr,br->b", group_weights, values, run_weights, optimize=True)


def bootstrap_metrics(
    values: dict[str, np.ndarray],
    group_weights: np.ndarray,
    run_weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    n = weighted_sum(values["n"], group_weights, run_weights)
    base_sse = weighted_sum(values["base_sse"], group_weights, run_weights)
    aug_sse = weighted_sum(values["aug_sse"], group_weights, run_weights)
    y_sum = weighted_sum(values["y_sum"], group_weights, run_weights)
    y2_sum = weighted_sum(values["y2_sum"], group_weights, run_weights)
    base_rmse = np.sqrt(base_sse / n)
    aug_rmse = np.sqrt(aug_sse / n)
    gain = (base_rmse - aug_rmse) / base_rmse
    tss = y2_sum - y_sum**2 / n
    r2 = 1.0 - aug_sse / tss
    return gain, r2


def observed(values: dict[str, np.ndarray]) -> dict[str, float]:
    n = values["n"].sum()
    base_sse = values["base_sse"].sum()
    aug_sse = values["aug_sse"].sum()
    y_sum = values["y_sum"].sum()
    y2_sum = values["y2_sum"].sum()
    base_rmse = math.sqrt(base_sse / n)
    aug_rmse = math.sqrt(aug_sse / n)
    return {
        "relative_rmse_gain": float((base_rmse - aug_rmse) / base_rmse),
        "aug_r2": float(1.0 - aug_sse / (y2_sum - y_sum**2 / n)),
    }


def interval(values: np.ndarray) -> list[float]:
    return [float(value) for value in np.quantile(values, [0.025, 0.975])]


def main() -> None:
    args = parse_args()
    design_path = args.design_path.resolve()
    predictions_path = RESULTS / f"{args.input_prefix}_predictions.csv"
    screen_summary_path = RESULTS / f"{args.input_prefix}_summary.json"
    bootstrap_path = RESULTS / f"{args.output_prefix}_bootstrap.csv.gz"
    summary_path = RESULTS / f"{args.output_prefix}_bootstrap_summary.json"
    design_text = design_path.read_text(encoding="utf-8")
    design = json.loads(design_text)
    screen_summary = json.loads(screen_summary_path.read_text(encoding="utf-8"))
    frame = pd.read_csv(predictions_path)
    groups = sorted(frame["group"].astype(str).unique())
    frame["run"] = frame["repeat"].astype(str) + "|" + frame["learner"].astype(str)
    runs = sorted(frame["run"].unique())
    inference = design["inference"]
    replicates = int(inference["bootstrap_replicates"])
    rng = np.random.default_rng(int(inference["bootstrap_seed"]))

    real = {
        scope: arrays(
            frame,
            groups,
            runs,
            scope,
            "state_plus_predicted_uts",
        )
        for scope in ("q1", "q4")
    }
    shuffled = {
        scope: arrays(
            frame,
            groups,
            runs,
            scope,
            (
                "state_plus_shuffled_uts"
                if design["screen"].get("shuffled_control_method")
                == "state_plus_crossfitted_shuffled_uts"
                else "shuffled_uts_residual_anchor"
            ),
        )
        for scope in ("q1", "q4")
    }
    output: dict[str, np.ndarray] = {
        "real_q1_gain": np.empty(replicates),
        "real_q4_gain": np.empty(replicates),
        "real_q4_aug_r2": np.empty(replicates),
        "shuffled_q4_gain": np.empty(replicates),
    }
    batch_size = 1000
    group_probability = np.full(len(groups), 1.0 / len(groups))
    run_probability = np.full(len(runs), 1.0 / len(runs))
    for start in range(0, replicates, batch_size):
        stop = min(replicates, start + batch_size)
        size = stop - start
        group_weights = rng.multinomial(
            len(groups), group_probability, size=size
        ).astype(float)
        run_weights = rng.multinomial(
            len(runs), run_probability, size=size
        ).astype(float)
        q1_gain, _ = bootstrap_metrics(real["q1"], group_weights, run_weights)
        q4_gain, q4_r2 = bootstrap_metrics(real["q4"], group_weights, run_weights)
        shuffled_gain, _ = bootstrap_metrics(
            shuffled["q4"], group_weights, run_weights
        )
        output["real_q1_gain"][start:stop] = q1_gain
        output["real_q4_gain"][start:stop] = q4_gain
        output["real_q4_aug_r2"][start:stop] = q4_r2
        output["shuffled_q4_gain"][start:stop] = shuffled_gain

    bootstrap = pd.DataFrame(output)
    bootstrap["q4_minus_q1_gain"] = (
        bootstrap["real_q4_gain"] - bootstrap["real_q1_gain"]
    )
    bootstrap["real_minus_shuffled_q4_gain"] = (
        bootstrap["real_q4_gain"] - bootstrap["shuffled_q4_gain"]
    )
    bootstrap.to_csv(bootstrap_path, index=False, compression="gzip")

    observed_real_q1 = observed(real["q1"])
    observed_real_q4 = observed(real["q4"])
    observed_shuffled_q4 = observed(shuffled["q4"])
    intervals = {column: interval(bootstrap[column].to_numpy()) for column in bootstrap}
    specification = design["balam_escalation_gate"]
    primary = [
        row
        for row in screen_summary["summaries"]
        if row["contract"] == design["screen"]["primary_contract"]
        and row["budget"] == design["screen"]["primary_budget"]
        and row["method"] == design["screen"]["primary_method"]
        and row["scope"] == "q4"
    ]
    if len(primary) != 1:
        raise AssertionError("Could not identify the unique primary Q4 summary")
    checks = {
        "q4_gain_threshold": bool(
            observed_real_q4["relative_rmse_gain"]
            >= specification["mean_q4_relative_rmse_gain_at_least"]
        ),
        "q4_gain_interval_positive": bool(intervals["real_q4_gain"][0] > 0),
        "positive_q4_run_count": bool(
            primary[0]["positive_runs"]
            >= specification["positive_q4_runs_at_least"]
        ),
        "q4_augmented_r2_positive": bool(observed_real_q4["aug_r2"] > 0),
        "ood_specificity_point_positive": bool(
            observed_real_q4["relative_rmse_gain"]
            > observed_real_q1["relative_rmse_gain"]
        ),
        "beats_shuffled_interval_positive": bool(
            intervals["real_minus_shuffled_q4_gain"][0] > 0
        ),
    }
    payload: dict[str, Any] = {
        "status": "complete",
        "design_sha256": hashlib.sha256(design_text.encode("utf-8")).hexdigest(),
        "replicates": replicates,
        "groups": len(groups),
        "runs": len(runs),
        "observed": {
            "real_q1": observed_real_q1,
            "real_q4": observed_real_q4,
            "shuffled_q4": observed_shuffled_q4,
            "q4_minus_q1_gain": (
                observed_real_q4["relative_rmse_gain"]
                - observed_real_q1["relative_rmse_gain"]
            ),
            "real_minus_shuffled_q4_gain": (
                observed_real_q4["relative_rmse_gain"]
                - observed_shuffled_q4["relative_rmse_gain"]
            ),
        },
        "bootstrap_ci95": intervals,
        "gate": {
            "checks": checks,
            "pass": bool(all(checks.values())),
            "decision": (
                "stable-on-this-program"
                if all(checks.values())
                else "does-not-pass-frozen-robustness-gate"
            ),
        },
        "claim_guard": design["claim_guard"],
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
