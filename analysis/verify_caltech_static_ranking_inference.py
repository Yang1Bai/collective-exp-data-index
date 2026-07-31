"""Independent semantic verification of the Caltech corrective reanalysis."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
UTILITY = RESULTS / "caltech_ionic_external_policy_utility.csv"
OUTPUT = RESULTS / "caltech_static_ranking_empirical_null.csv"
SUMMARY = RESULTS / "caltech_static_ranking_empirical_null_summary.json"


def empirical_p(observed: float, null: np.ndarray) -> float:
    return float((1 + np.sum(null >= observed)) / (len(null) + 1))


def main() -> None:
    utility = pd.read_csv(UTILITY)
    result = pd.read_csv(OUTPUT)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    expected_p = {
        ("external_candidate", "obelix_same_property_static"): 9 / 101,
        ("external_candidate", "estm_transport_neighbor_static"): 3 / 101,
        ("hard_ood_40pct", "obelix_same_property_static"): 4 / 101,
        ("hard_ood_40pct", "estm_transport_neighbor_static"): 1 / 101,
    }
    for key, target in expected_p.items():
        scope, policy = key
        observed_values = utility.loc[
            utility["scope"].eq(scope) & utility["policy"].eq(policy), "auc20"
        ].unique()
        if len(observed_values) != 1:
            raise AssertionError(f"Non-static observed policy: {key}")
        null = utility.loc[
            utility["scope"].eq(scope)
            & utility["policy"].eq("shuffled_obelix_static_control"),
            "auc20",
        ].to_numpy(float)
        computed = empirical_p(float(observed_values[0]), null)
        row = result[
            result["scope"].eq(scope) & result["policy"].eq(policy)
        ].iloc[0]
        if not np.isclose(computed, target, atol=1e-15):
            raise AssertionError(f"Unexpected independently computed p: {key}")
        if not np.isclose(
            float(row["empirical_p_vs_shuffled"]), computed, atol=1e-15
        ):
            raise AssertionError(f"Saved p mismatch: {key}")

    adjusted = {
        (row.scope, row.policy): float(row.holm_p_vs_shuffled_four_tests)
        for row in result.itertuples()
    }
    expected_adjusted = {
        ("external_candidate", "obelix_same_property_static"): 9 / 101,
        ("external_candidate", "estm_transport_neighbor_static"): 9 / 101,
        ("hard_ood_40pct", "obelix_same_property_static"): 9 / 101,
        ("hard_ood_40pct", "estm_transport_neighbor_static"): 4 / 101,
    }
    for key, target in expected_adjusted.items():
        if not np.isclose(adjusted[key], target, atol=1e-15):
            raise AssertionError(f"Holm mismatch: {key}: {adjusted[key]} != {target}")

    family = {
        row["scope"]: row for row in summary["family_first_vs_best_single"]
    }
    if not np.isclose(family["external_candidate"]["auc20_difference"], 11.0):
        raise AssertionError("External family-first best-single contrast changed")
    if not np.isclose(family["external_candidate"]["recall20_difference"], 0.0):
        raise AssertionError("External family-first recall is not complementary")
    if not np.isclose(family["hard_ood_40pct"]["auc20_difference"], 0.0):
        raise AssertionError("Hard-OOD family-first should tie best single")
    if summary["interpretation"]["confirmed_after_holm"] != [
        "hard_ood_40pct|estm_transport_neighbor_static"
    ]:
        raise AssertionError("Unexpected Holm survivor")
    print(
        json.dumps(
            {
                "status": "verified-complete",
                "rows": int(len(result)),
                "holm_survivors": summary["interpretation"][
                    "confirmed_after_holm"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
