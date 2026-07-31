"""Inferential synthesis for the frozen optical-to-OPV benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "opv_optical_external_borrowing_design.json"
REAL = "state_aware_plus_real_solid_optical_card"
TARGET = "state_aware_target_only"
CONTROLS = {
    "target_only": TARGET,
    "shuffled_source": "state_aware_plus_shuffled_source_card",
    "state_blind": "state_aware_plus_state_blind_optical_card",
    "permuted_real": "state_aware_plus_permuted_real_card",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_gain(control_rmse: float, real_rmse: float) -> float:
    return (float(control_rmse) - float(real_rmse)) / float(control_rmse)


def holm_adjust(values: list[float]) -> list[float]:
    count = len(values)
    order = np.argsort(values)
    adjusted_sorted = np.empty(count, dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * float(values[index]))
        running = max(running, candidate)
        adjusted_sorted[rank] = running
    adjusted = np.empty(count, dtype=float)
    for rank, index in enumerate(order):
        adjusted[index] = adjusted_sorted[rank]
    return adjusted.tolist()


def paired_repeat_gain(
    metrics: pd.DataFrame,
    outcome: str,
    scope: str,
    control: str,
) -> pd.Series:
    selected = metrics[
        (metrics["budget"] == 120)
        & (metrics["learner"] == "extra_trees")
        & (metrics["scope"] == scope)
        & (metrics["outcome"] == outcome)
        & (metrics["method"].isin([REAL, control]))
    ]
    pivot = selected.pivot(
        index="repeat", columns="method", values="rmse"
    )
    if set(pivot.columns) != {REAL, control}:
        raise RuntimeError("Primary methods are incomplete")
    return (pivot[control] - pivot[REAL]) / pivot[control]


def doi_cluster_inference(
    predictions: pd.DataFrame,
    control: str,
    bootstrap_replicates: int,
    seed: int,
) -> dict[str, float | list[float]]:
    selected = predictions[
        predictions["method"].isin([REAL, control])
    ].copy()
    pivot = selected.pivot(
        index=["repeat", "id", "doi_normalized_audit"],
        columns="method",
        values=["truth_pce", "predicted_pce"],
    )
    if REAL not in pivot["predicted_pce"] or control not in pivot[
        "predicted_pce"
    ]:
        raise RuntimeError("Primary prediction methods incomplete")
    truth_real = pivot["truth_pce"][REAL].to_numpy(float)
    truth_control = pivot["truth_pce"][control].to_numpy(float)
    if not np.allclose(truth_real, truth_control, rtol=0, atol=0):
        raise AssertionError("Paired target truths differ")
    cluster = pd.DataFrame(
        {
            "doi": pivot.index.get_level_values(
                "doi_normalized_audit"
            ).astype(str),
            "sse_real": (
                truth_real - pivot["predicted_pce"][REAL].to_numpy(float)
            )
            ** 2,
            "sse_control": (
                truth_control
                - pivot["predicted_pce"][control].to_numpy(float)
            )
            ** 2,
            "n": 1,
        }
    ).groupby("doi", as_index=False).sum()
    control_rmse = float(
        np.sqrt(cluster["sse_control"].sum() / cluster["n"].sum())
    )
    real_rmse = float(
        np.sqrt(cluster["sse_real"].sum() / cluster["n"].sum())
    )
    observed_gain = relative_gain(control_rmse, real_rmse)

    rng = np.random.default_rng(seed)
    n_clusters = len(cluster)
    bootstrap = np.empty(bootstrap_replicates, dtype=float)
    sse_real = cluster["sse_real"].to_numpy(float)
    sse_control = cluster["sse_control"].to_numpy(float)
    counts = cluster["n"].to_numpy(float)
    for start in range(0, bootstrap_replicates, 250):
        width = min(250, bootstrap_replicates - start)
        draws = rng.integers(0, n_clusters, size=(width, n_clusters))
        real = np.sqrt(
            sse_real[draws].sum(axis=1) / counts[draws].sum(axis=1)
        )
        control_values = np.sqrt(
            sse_control[draws].sum(axis=1)
            / counts[draws].sum(axis=1)
        )
        bootstrap[start : start + width] = (
            control_values - real
        ) / control_values
    ci = np.quantile(bootstrap, [0.025, 0.5, 0.975]).tolist()

    differences = sse_control / counts - sse_real / counts
    permutations = min(100_000, max(10_000, bootstrap_replicates * 10))
    observed = float(differences.mean())
    exceedances = 0
    for start in range(0, permutations, 500):
        width = min(500, permutations - start)
        random_signs = rng.choice(
            np.asarray([-1.0, 1.0]),
            size=(width, n_clusters),
            replace=True,
        )
        null = (random_signs * differences).mean(axis=1)
        exceedances += int(np.sum(null >= observed))
    p_value = float((1 + exceedances) / (permutations + 1))
    return {
        "control": control,
        "clusters": int(n_clusters),
        "paired_rows": int(cluster["n"].sum()),
        "control_rmse": control_rmse,
        "real_rmse": real_rmse,
        "relative_rmse_gain": observed_gain,
        "bootstrap_ci95": [float(value) for value in ci],
        "one_sided_cluster_sign_p": p_value,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["formal", "synthetic_smoke"], required=True
    )
    arguments = parser.parse_args()
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    metrics_path = (
        RESULTS / f"opv_optical_external_{arguments.mode}_metrics.csv"
    )
    predictions_path = (
        RESULTS
        / f"opv_optical_external_{arguments.mode}_primary_predictions.csv"
    )
    run_path = RESULTS / f"opv_optical_external_{arguments.mode}_run.json"
    metrics = pd.read_csv(metrics_path)
    predictions = pd.read_csv(predictions_path)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    if run["metrics_sha256"] != sha256(metrics_path):
        raise RuntimeError("Metrics changed after model run")
    if run["primary_predictions_sha256"] != sha256(predictions_path):
        raise RuntimeError("Primary predictions changed after model run")

    replicates = int(design["inference"]["bootstrap_replicates"])
    inferences = []
    for index, (name, control) in enumerate(CONTROLS.items()):
        result = doi_cluster_inference(
            predictions,
            control,
            replicates,
            seed=2026072800 + index,
        )
        result["contrast"] = f"real_vs_{name}"
        inferences.append(result)
    raw_p = [float(item["one_sided_cluster_sign_p"]) for item in inferences]
    adjusted = holm_adjust(raw_p)
    for item, adjusted_p in zip(inferences, adjusted, strict=True):
        item["holm_p"] = float(adjusted_p)

    primary_repeat = paired_repeat_gain(
        metrics, "pce", "qualified_hard_ood_40pct", TARGET
    )
    shuffled_repeat = paired_repeat_gain(
        metrics,
        "pce",
        "qualified_hard_ood_40pct",
        CONTROLS["shuffled_source"],
    )
    permuted_repeat = paired_repeat_gain(
        metrics,
        "pce",
        "qualified_hard_ood_40pct",
        CONTROLS["permuted_real"],
    )
    jsc_repeat = paired_repeat_gain(
        metrics, "jsc", "qualified_hard_ood_40pct", TARGET
    )
    physics_pce_repeat = paired_repeat_gain(
        metrics,
        "pce_physics_recombined",
        "qualified_hard_ood_40pct",
        TARGET,
    )
    full_repeat = paired_repeat_gain(
        metrics, "pce", "full_external", TARGET
    )
    real_primary_metrics = metrics[
        (metrics["budget"] == 120)
        & (metrics["learner"] == "extra_trees")
        & (metrics["scope"] == "qualified_hard_ood_40pct")
        & (metrics["outcome"] == "pce")
        & (metrics["method"] == REAL)
    ]
    primary_inference = next(
        item for item in inferences if item["contrast"] == "real_vs_target_only"
    )
    gate_settings = design["inference"]["success_gate"]
    gates = {
        "minimum_mean_relative_pce_rmse_gain": bool(
            primary_repeat.mean()
            >= float(gate_settings["minimum_mean_relative_pce_rmse_gain"])
        ),
        "positive_cluster_bootstrap_lower": bool(
            float(primary_inference["bootstrap_ci95"][0]) > 0
        ),
        "holm_p_below_0_05": bool(
            float(primary_inference["holm_p"])
            < float(gate_settings["holm_p_below"])
        ),
        "absolute_pce_r2_positive": bool(
            real_primary_metrics["r2"].mean()
            > float(gate_settings["absolute_pce_r2_greater_than"])
        ),
        "gain_over_shuffled_at_least_0_02": bool(
            shuffled_repeat.mean()
            >= float(gate_settings["minimum_gain_over_shuffled_source"])
        ),
        "gain_over_permuted_positive": bool(
            permuted_repeat.mean()
            > float(gate_settings["minimum_gain_over_permuted_real"])
        ),
        "jsc_gain_nonnegative": bool(
            jsc_repeat.mean() >= 0
            if gate_settings["nonnegative_mean_jsc_gain"]
            else True
        ),
        "full_external_harm_within_0_01": bool(
            full_repeat.mean()
            >= -float(gate_settings["maximum_full_external_pce_rmse_harm"])
        ),
        "positive_repeat_fraction_at_least_0_65": bool(
            (primary_repeat > 0).mean()
            >= float(
                gate_settings["positive_repeat_fraction_at_least"]
            )
        ),
    }
    summary = {
        "status": "verified-inference-ready",
        "mode": arguments.mode,
        "created_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "design_sha256": sha256(DESIGN_PATH),
        "run_sha256": sha256(run_path),
        "metrics_sha256": sha256(metrics_path),
        "predictions_sha256": sha256(predictions_path),
        "implementation_sha256": sha256(Path(__file__)),
        "primary": {
            "mean_relative_pce_rmse_gain": float(primary_repeat.mean()),
            "median_relative_pce_rmse_gain": float(primary_repeat.median()),
            "positive_repeat_fraction": float((primary_repeat > 0).mean()),
            "mean_real_pce_r2": float(real_primary_metrics["r2"].mean()),
            "mean_jsc_rmse_gain": float(jsc_repeat.mean()),
            "mean_physics_recombined_pce_rmse_gain": float(
                physics_pce_repeat.mean()
            ),
            "mean_full_external_pce_rmse_gain": float(full_repeat.mean()),
            "mean_gain_real_vs_shuffled": float(shuffled_repeat.mean()),
            "mean_gain_real_vs_permuted": float(permuted_repeat.mean()),
        },
        "cluster_inference": inferences,
        "gates": gates,
        "passes_complete_gate": bool(all(gates.values())),
        "decision": (
            "qualified-positive-edge"
            if all(gates.values())
            else "null-harmful-or-incomplete-edge"
        ),
        "claim_guard": design["claim_guard"],
    }
    summary_path = (
        RESULTS / f"opv_optical_external_{arguments.mode}_summary.json"
    )
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
