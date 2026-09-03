"""Independent semantic verifier for the strength -> fatigue benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN = HERE / "strength_to_fatigue_ood_design.json"
IMPLEMENTATION = HERE / "strength_fatigue_implementation.json"
RELEASE = RESULTS / "strength_fatigue_formal_release_manifest.json"
SOURCE_CARDS = RESULTS / "strength_fatigue_source_cards.csv"
SHUFFLED_CARDS = RESULTS / "strength_fatigue_shuffled_source_cards.csv"
SOURCE_SUMMARY = RESULTS / "strength_fatigue_source_summary.json"
SPLITS = RESULTS / "strength_fatigue_split_audit.csv"
METRICS = RESULTS / "strength_fatigue_metrics.csv"
PREDICTIONS = RESULTS / "strength_fatigue_predictions.csv"
BOOTSTRAP = RESULTS / "strength_fatigue_bootstrap.csv"
SUMMARY = RESULTS / "strength_fatigue_summary.json"
OUTPUT = RESULTS / "strength_fatigue_VERIFIED.json"

METHODS = {
    "target_only",
    "safe_borg_uts",
    "safe_shuffled_uts",
    "safe_borg_hardness_control",
    "safe_borg_elongation_control",
}
CONTRASTS = {
    "real_vs_target_only": ("target_only", "safe_borg_uts"),
    "real_vs_shuffled_uts": ("safe_shuffled_uts", "safe_borg_uts"),
    "real_vs_hardness": (
        "safe_borg_hardness_control",
        "safe_borg_uts",
    ),
    "real_vs_elongation": (
        "safe_borg_elongation_control",
        "safe_borg_uts",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    return parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def close(left: float, right: float, tolerance: float = 1e-10) -> None:
    if not math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"Numeric mismatch: {left} != {right}")


def exact_sign_flip_p(values: np.ndarray) -> float:
    effects = np.asarray(values, dtype=float)
    observed = float(effects.mean())
    if observed <= 0:
        return 1.0
    total = 1 << len(effects)
    exceed = 0
    for mask in range(total):
        signed_sum = 0.0
        for index, value in enumerate(effects):
            signed_sum += value if (mask >> index) & 1 else -value
        if signed_sum / len(effects) >= observed - 1e-15:
            exceed += 1
    return float((exceed + 1) / (total + 1))


def holm(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=values.get)
    output = {}
    running = 0.0
    for rank, key in enumerate(ordered):
        adjusted = min(1.0, (len(ordered) - rank) * values[key])
        running = max(running, adjusted)
        output[key] = running
    return output


def recompute_contrasts(metrics: pd.DataFrame) -> pd.DataFrame:
    wide = metrics.pivot_table(
        index=["component", "repeat", "learner"],
        columns="method",
        values="rmse_log10_cycles",
        aggfunc="first",
    ).reset_index()
    rows = []
    for name, (control, real) in CONTRASTS.items():
        part = wide[["component", "repeat", "learner", control, real]].copy()
        part["contrast"] = name
        part["relative_rmse_gain"] = 1.0 - part[real] / part[control]
        rows.append(
            part[
                [
                    "component",
                    "repeat",
                    "learner",
                    "contrast",
                    "relative_rmse_gain",
                ]
            ]
        )
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    args = parse_args()
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    implementation = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    source_summary = json.loads(SOURCE_SUMMARY.read_text(encoding="utf-8"))
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    source_cards = pd.read_csv(SOURCE_CARDS)
    shuffled_cards = pd.read_csv(SHUFFLED_CARDS)
    splits = pd.read_csv(SPLITS)
    metrics = pd.read_csv(METRICS)
    predictions = pd.read_csv(PREDICTIONS)
    bootstrap = pd.read_csv(BOOTSTRAP)

    if summary["design_sha256"] != digest(DESIGN):
        raise AssertionError("Design hash mismatch")
    if summary["implementation_sha256"] != digest(IMPLEMENTATION):
        raise AssertionError("Implementation hash mismatch")
    if summary["release_manifest_sha256"] != digest(RELEASE):
        raise AssertionError("Release manifest hash mismatch")
    for path, key in (
        (SOURCE_SUMMARY, "source_summary_sha256"),
        (METRICS, "metrics_sha256"),
        (PREDICTIONS, "predictions_sha256"),
        (SPLITS, "splits_sha256"),
        (BOOTSTRAP, "bootstrap_sha256"),
    ):
        if summary[key] != digest(path):
            raise AssertionError(f"Output hash mismatch: {path.name}")
    if implementation["design_sha256"] != digest(DESIGN):
        raise AssertionError("Implementation points to another design")

    components = int(summary["components"])
    repeats = int(summary["repeats"])
    learners = list(summary["learners"])
    if set(summary["methods"]) != METHODS:
        raise AssertionError("Method set changed")
    expected_metrics = components * repeats * len(learners) * len(METHODS)
    if len(metrics) != expected_metrics:
        raise AssertionError(
            f"Metric row count {len(metrics)} != {expected_metrics}"
        )
    expected_predictions = (
        int(release["target_rows"]) * repeats * len(learners) * len(METHODS)
    )
    if len(predictions) != expected_predictions:
        raise AssertionError(
            f"Prediction row count {len(predictions)} != {expected_predictions}"
        )
    expected_splits = components * repeats * len(learners)
    if len(splits) != expected_splits:
        raise AssertionError("Split row count mismatch")
    if len(source_cards) != int(release["target_curves"]):
        raise AssertionError("Source-card curve count mismatch")
    if len(shuffled_cards) != int(release["target_curves"]) * repeats:
        raise AssertionError("Shuffled-card row count mismatch")

    for row in splits.itertuples(index=False):
        training = set(json.loads(row.training_curves))
        evaluation = set(json.loads(row.evaluation_curves))
        if training & evaluation:
            raise AssertionError("Training/evaluation curve leakage")
        if len(training) != int(design["ood_design"]["primary_budget"]):
            raise AssertionError("Target-label budget changed")
    if not source_cards["nearest_borg_l1"].le(
        design["preoutcome_gate"]["supported_neighbor_l1_threshold"]
    ).all():
        raise AssertionError("Composition support exceeds frozen threshold")

    contrasts = recompute_contrasts(metrics)
    p_values = {}
    for contrast in CONTRASTS:
        part = contrasts[contrasts["contrast"].eq(contrast)]
        component_effect = part.groupby("component")[
            "relative_rmse_gain"
        ].mean()
        p_values[contrast] = exact_sign_flip_p(component_effect.to_numpy())
        reported = summary["inference"][contrast]
        close(
            float(part["relative_rmse_gain"].mean()),
            reported["mean_relative_rmse_gain"],
        )
        close(
            float(np.mean(part.groupby(["repeat", "learner"])[
                "relative_rmse_gain"
            ].mean() > 0)),
            reported["positive_run_fraction"],
        )
        draws = bootstrap[
            bootstrap["contrast"].eq(contrast)
        ]["relative_rmse_gain"]
        if len(draws) != int(design["inference"]["bootstrap_replicates"]):
            raise AssertionError("Bootstrap replicate count mismatch")
        interval = np.quantile(draws, [0.025, 0.975])
        close(float(interval[0]), reported["ci95"][0])
        close(float(interval[1]), reported["ci95"][1])
        close(
            p_values[contrast],
            reported["one_sided_component_sign_flip_p"],
        )
    adjusted = holm(p_values)
    for contrast, value in adjusted.items():
        close(value, summary["inference"][contrast]["holm_adjusted_p"])

    failures = predictions[predictions["runout"].eq(0)]
    for method in METHODS:
        values = []
        for (_, _), run in failures[
            failures["method"].eq(method)
        ].groupby(["repeat", "learner"]):
            values.append(
                r2_score(run["log_life"], run["prediction_log10_cycles"])
            )
        close(
            float(np.mean(values)),
            summary["absolute_r2"][method]["mean_pooled_r2"],
        )
        close(
            float(np.min(values)),
            summary["absolute_r2"][method]["minimum_pooled_r2"],
        )

    primary = summary["inference"]["real_vs_target_only"]
    gate = design["success_gate"]
    learner_effects = {
        learner: float(
            contrasts[
                contrasts["contrast"].eq("real_vs_target_only")
                & contrasts["learner"].eq(learner)
            ]["relative_rmse_gain"].mean()
        )
        for learner in learners
    }
    checks = {
        "relative_rmse_gain_at_least_0_05": (
            primary["mean_relative_rmse_gain"]
            >= gate["primary_relative_rmse_gain_at_least"]
        ),
        "bootstrap_ci_lower_positive": (
            primary["ci95"][0] > gate["cluster_bootstrap_ci95_lower_above"]
        ),
        "holm_p_below_0_05": (
            primary["holm_adjusted_p"]
            < gate["holm_adjusted_one_sided_p_below"]
        ),
        "absolute_augmented_r2_positive": (
            summary["absolute_r2"]["safe_borg_uts"]["mean_pooled_r2"]
            > gate["augmented_absolute_r2_above"]
        ),
        "positive_repeat_fraction_at_least_0_8": (
            primary["positive_run_fraction"]
            >= gate["positive_repeat_fraction_at_least"]
        ),
        "beats_all_controls": all(
            summary["inference"][name]["mean_relative_rmse_gain"] > 0
            and summary["inference"][name]["ci95"][0] > 0
            for name in (
                "real_vs_shuffled_uts",
                "real_vs_hardness",
                "real_vs_elongation",
            )
        ),
        "both_learners_nonnegative": all(
            value >= 0 for value in learner_effects.values()
        ),
        "applicability_coverage": (
            summary["applicability_coverage_rows"]
            >= gate["minimum_applicability_coverage"]
        ),
    }
    if checks != summary["gate_checks"]:
        raise AssertionError("Reported gate decisions do not recompute")
    passes = all(checks.values())
    if passes != summary["passes_complete_gate"]:
        raise AssertionError("Complete-gate decision mismatch")
    expected_decision = (
        "independent-positive-edge"
        if passes
        else "null-harmful-or-incomplete-edge"
    )
    if summary["decision"] != expected_decision:
        raise AssertionError("Decision label mismatch")

    output = {
        "status": "verified-complete",
        "design_sha256": digest(DESIGN),
        "implementation_sha256": digest(IMPLEMENTATION),
        "summary_sha256": digest(args.summary),
        "metrics_rows": int(len(metrics)),
        "prediction_rows": int(len(predictions)),
        "bootstrap_rows": int(len(bootstrap)),
        "components": components,
        "repeats": repeats,
        "decision": summary["decision"],
        "passes_complete_gate": passes,
        "claim_guard": design["claim_guard"],
    }
    args.output.write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
