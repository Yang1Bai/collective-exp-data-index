"""Synthesize fixed Starrydata and TRI OER target-level borrowing effects."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
STARRY_VALIDATED = RESULTS / "starrydata_reverse_VALIDATED.json"
STARRY_SUMMARY = RESULTS / "starrydata_reverse_summary.json"
TRI_VALIDATED = RESULTS / "tri_oer_VALIDATED.json"
OUTPUT = RESULTS / "outcome_unseen_multi_target_summary.json"


def estimate_and_variance(mean_ci: list[float]) -> tuple[float, float]:
    mean, lower, upper = map(float, mean_ci)
    se = (upper - lower) / (2 * 1.96)
    return mean, max(se**2, 1e-12)


def random_effects(effects: np.ndarray, variances: np.ndarray) -> dict:
    fixed_weights = 1 / variances
    fixed_mean = float(np.sum(fixed_weights * effects) / np.sum(fixed_weights))
    q = float(np.sum(fixed_weights * (effects - fixed_mean) ** 2))
    df = len(effects) - 1
    c = float(np.sum(fixed_weights) - np.sum(fixed_weights**2) / np.sum(fixed_weights))
    tau2 = max(0.0, (q - df) / max(c, 1e-12))
    weights = 1 / (variances + tau2)
    mean = float(np.sum(weights * effects) / np.sum(weights))
    se = math.sqrt(1 / np.sum(weights))
    return {
        "mean_relative_rmse_gain": mean,
        "ci95": [mean - 1.96 * se, mean + 1.96 * se],
        "tau_squared": tau2,
        "q": q,
        "i_squared_percent": max(0.0, (q - df) / max(q, 1e-12)) * 100,
        "targets": len(effects),
    }


def main() -> None:
    starry = json.loads(STARRY_VALIDATED.read_text(encoding="utf-8"))
    starry_summary = json.loads(STARRY_SUMMARY.read_text(encoding="utf-8"))
    tri = json.loads(TRI_VALIDATED.read_text(encoding="utf-8"))
    if starry["status"] != "verified-complete" or tri["status"] != "verified-complete":
        raise AssertionError("Both independent targets must be verified before synthesis")

    starry_effect, starry_variance = estimate_and_variance(
        starry["hierarchical_primary_prediction"]["ionic_vs_target"]["mean_ci95"]
    )
    tri_random = tri["prediction_inference"]["across_plates"]["all_vs_target"]["random_effects"]
    tri_effect = float(tri_random["mean"])
    tri_variance = max(((float(tri_random["ci95"][1]) - float(tri_random["ci95"][0])) / (2 * 1.96)) ** 2, 1e-12)
    effects = np.asarray([starry_effect, tri_effect])
    variances = np.asarray([starry_variance, tri_variance])
    meta = random_effects(effects, variances)

    starry_gate = {
        "positive_interval": starry["hierarchical_primary_prediction"]["ionic_vs_target"]["mean_ci95"][1] > 0,
        "holm_p_below_0_05": starry["hierarchical_primary_prediction"]["ionic_vs_target"]["holm_p"] < 0.05,
        "absolute_r2_positive": starry_summary["ionic_consensus_absolute_r2_mean"] > 0,
    }
    tri_plate = tri["prediction_inference"]["across_plates"]["all_vs_target"]
    tri_absolute = tri["prediction_inference"]["absolute_r2_by_plate"]
    tri_gate = {
        "positive_random_effects_interval": tri_random["ci95"][0] > 0,
        "holm_p_below_0_05": tri_plate["holm_p"] < 0.05,
        "positive_plates_at_least_3_of_4": tri_plate["positive_plates"] >= 3,
        "positive_absolute_r2_plates": int(sum(float(value) > 0 for value in tri_absolute.values())),
    }
    result = {
        "status": "verified-complete-boundary",
        "claim_guard": "Two retrospective target programmes quantify cross-target heterogeneity. A positive mean cannot establish prospective discovery; a null mean does not erase target-specific positive edges.",
        "target_effects": {
            "starrydata_reverse_transport": {
                "relative_rmse_gain": starry_effect,
                "variance": starry_variance,
                "gate": starry_gate,
                "passes_full_prediction_gate": all(starry_gate.values()),
            },
            "tri_oer_second_family": {
                "relative_rmse_gain": tri_effect,
                "variance": tri_variance,
                "gate": tri_gate,
                "passes_full_prediction_gate": all(tri_gate.values()),
            },
        },
        "random_effects": meta,
        "directionally_concordant_targets": int(np.sum(effects > 0)),
        "interpretation": "The main claim remains edge-selective. Independent positive predictive replication requires at least one new target to pass its complete gate; null or abstaining targets remain evidence for the map boundary.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
