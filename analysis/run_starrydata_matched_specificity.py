"""Run the frozen matched-source specificity family on Starrydata."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import mean_squared_error, r2_score

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.run_starrydata_reverse_transport import (  # noqa: E402
    METADATA,
    PREDICTIONS,
    fit_predict,
    join_target_outcomes,
    representations,
    select_labelled,
    sha256,
    stable_seed,
    verify_preoutcome,
)

RESULTS = HERE / "results"
CONTROL_FILE = RESULTS / "starrydata_reverse_matched_source_controls.csv"
CONTROL_AUDIT = RESULTS / "starrydata_reverse_matched_source_controls.json"
AMENDMENT = HERE / "STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md"

PAIRS = [
    ("obelix_adjacent_ionic", "borg_wrong_mechanical"),
    ("obelix_adjacent_ionic", "ocx_wrong_catalysis"),
    ("caltech_adjacent_ionic", "borg_wrong_mechanical"),
    ("caltech_adjacent_ionic", "ocx_wrong_catalysis"),
]


def task(
    repeat: int,
    trees: int,
    target: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    frozen: pd.DataFrame,
    controls: pd.DataFrame,
) -> list[dict]:
    train = select_labelled(target, repeat, 30)
    evaluation = np.sort(target.index[target["split"].eq("evaluation")].to_numpy(int))
    q4 = evaluation[target.loc[evaluation, "ood_quartile"].to_numpy(int) == 4]
    seed = stable_seed(f"matched-specificity|{repeat}")
    method_predictions: dict[str, np.ndarray] = {}
    method_predictions["target_only"] = fit_predict("extra_trees", seed, trees, x, y, train, evaluation)
    ionic_x = np.column_stack(
        [x, frozen["obelix_adjacent_ionic_rank"], frozen["caltech_adjacent_ionic_rank"]]
    )
    method_predictions["ionic_consensus"] = fit_predict(
        "extra_trees", stable_seed(f"{seed}|ionic"), trees, ionic_x, y, train, evaluation
    )
    skill_x = np.column_stack([x, controls["skill_matched_wrong_rank"]])
    method_predictions["skill_matched_ocx_control"] = fit_predict(
        "extra_trees", stable_seed(f"{seed}|skill"), trees, skill_x, y, train, evaluation
    )
    random_x = np.column_stack(
        [x] + [frozen[f"random_feature_{index}"] for index in range(1, 6)]
    )
    method_predictions["equal_capacity_random_control"] = fit_predict(
        "extra_trees", stable_seed(f"{seed}|capacity"), trees, random_x, y, train, evaluation
    )
    for adjacent, wrong in PAIRS:
        adjacent_col = f"size_matched_{adjacent}_for_{wrong}_rank"
        wrong_col = f"size_matched_{wrong}_for_{adjacent}_rank"
        for role, column in [("adjacent", adjacent_col), ("wrong", wrong_col)]:
            augmented = np.column_stack([x, controls[column]])
            method = f"size_matched|{adjacent}|{wrong}|{role}"
            method_predictions[method] = fit_predict(
                "extra_trees", stable_seed(f"{seed}|{method}"), trees, augmented, y, train, evaluation
            )

    rows: list[dict] = []
    index_to_local = {index: position for position, index in enumerate(evaluation)}
    scopes: dict[str, np.ndarray] = {"hard_ood_q4": q4}
    for adjacent, wrong in PAIRS:
        pair = f"{adjacent}_vs_{wrong}"
        mask = controls[f"coverage_matched_{pair}"].astype(bool).to_numpy()
        matched = evaluation[mask[evaluation]]
        scopes[f"coverage_matched|{pair}"] = matched
        matched_q4 = np.intersect1d(matched, q4)
        if len(matched_q4) >= 20:
            scopes[f"coverage_matched_hard_ood|{pair}"] = matched_q4
    for method, prediction in method_predictions.items():
        for scope, indices in scopes.items():
            if len(indices) < 20:
                continue
            local = np.asarray([index_to_local[index] for index in indices], dtype=int)
            truth = y[indices]
            estimate = prediction[local]
            rows.append(
                {
                    "repeat": repeat,
                    "method": method,
                    "scope": scope,
                    "n": len(indices),
                    "rmse": math.sqrt(mean_squared_error(truth, estimate)),
                    "r2": r2_score(truth, estimate),
                }
            )
    return rows


def interval(values: np.ndarray, rng: np.random.Generator, reps: int) -> list[float]:
    boot = np.mean(rng.choice(values, size=(reps, len(values)), replace=True), axis=1)
    return [float(np.mean(values)), float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))]


def summarize(metrics: pd.DataFrame, smoke: bool) -> dict:
    q4 = metrics[metrics["scope"].eq("hard_ood_q4")].pivot(index="repeat", columns="method", values="rmse")
    baseline = q4["target_only"].to_numpy()
    ionic_gain = (baseline - q4["ionic_consensus"].to_numpy()) / baseline
    skill_gain = (baseline - q4["skill_matched_ocx_control"].to_numpy()) / baseline
    capacity_gain = (baseline - q4["equal_capacity_random_control"].to_numpy()) / baseline
    rng = np.random.default_rng(stable_seed("matched-specificity-bootstrap"))
    reps = 200 if smoke else 10000
    size_contrasts: dict[str, list[float]] = {}
    for adjacent, wrong in PAIRS:
        adjacent_method = f"size_matched|{adjacent}|{wrong}|adjacent"
        wrong_method = f"size_matched|{adjacent}|{wrong}|wrong"
        contrast = (q4[wrong_method].to_numpy() - q4[adjacent_method].to_numpy()) / baseline
        size_contrasts[f"{adjacent}_minus_{wrong}"] = interval(contrast, rng, reps)
    return {
        "status": "smoke-nonclaim" if smoke else "formal-complete",
        "primary_scope": "n=30, ExtraTrees, composition, frozen OOD quartile 4",
        "ionic_consensus_relative_rmse_gain": interval(ionic_gain, rng, reps),
        "ionic_minus_skill_matched_ocx": interval(ionic_gain - skill_gain, rng, reps),
        "ionic_minus_equal_capacity_random": interval(ionic_gain - capacity_gain, rng, reps),
        "size_matched_adjacent_minus_wrong": size_contrasts,
        "coverage_scopes_reported": sorted(
            scope for scope in metrics["scope"].unique() if scope.startswith("coverage_matched")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))
    args = parser.parse_args()
    freeze = verify_preoutcome()
    audit = json.loads(CONTROL_AUDIT.read_text(encoding="utf-8"))
    if sha256(CONTROL_FILE) != audit["output_sha256"]:
        raise AssertionError("Matched-control hash mismatch")
    metadata = pd.read_csv(METADATA)
    target, outcome_audit = join_target_outcomes(metadata)
    x = representations(target)["composition"]
    y = target["target_zt"].to_numpy(float)
    frozen = target[["entity_id"]].merge(pd.read_csv(PREDICTIONS), on="entity_id", validate="one_to_one")
    controls = target[["entity_id"]].merge(pd.read_csv(CONTROL_FILE), on="entity_id", validate="one_to_one")
    frozen.index = target.index
    controls.index = target.index
    repeats = 2 if args.smoke else 100
    trees = 30 if args.smoke else 300
    outputs = Parallel(n_jobs=args.jobs, verbose=10)(
        delayed(task)(repeat, trees, target, x, y, frozen, controls)
        for repeat in range(repeats)
    )
    metrics = pd.DataFrame([row for output in outputs for row in output])
    summary = summarize(metrics, args.smoke)
    summary["outcome_audit"] = outcome_audit
    summary["original_preoutcome_sha256"] = sha256(RESULTS / "starrydata_reverse_PREOUTCOME.json")
    summary["formal_amendment_sha256"] = sha256(AMENDMENT)
    prefix = "starrydata_reverse_matched_specificity_smoke" if args.smoke else "starrydata_reverse_matched_specificity"
    metrics.to_csv(RESULTS / f"{prefix}_metrics.csv", index=False)
    (RESULTS / f"{prefix}_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    complete = {
        "status": "smoke-nonclaim" if args.smoke else "complete",
        "repeats": repeats,
        "metric_rows": len(metrics),
        "preoutcome_sha256": sha256(RESULTS / "starrydata_reverse_PREOUTCOME.json"),
        "control_audit_sha256": sha256(CONTROL_AUDIT),
        "amendment_sha256": sha256(AMENDMENT),
    }
    (RESULTS / f"{prefix}_COMPLETE.json").write_text(
        json.dumps(complete, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
