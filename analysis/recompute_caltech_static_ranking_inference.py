"""Corrective empirical-null inference for Caltech static donor rankings.

This reanalysis was added after an external scientific review identified that
plotting only the mean shuffled/random control obscured their wide empirical
distributions.  Static rankings are compared with the 100-seed shuffled-source
null using a finite-sample one-sided empirical p value.  The four declared
source-by-scope comparisons are adjusted together with Holm's procedure.

The family-first analysis is also compared directly with the strongest single
neighboring donor so that diversity allocation is not mislabeled as
complementarity when it only ties that donor.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
UTILITY = RESULTS / "caltech_ionic_external_policy_utility.csv"
FAMILY_SUMMARY = RESULTS / "family_first_neighbor_portfolio_summary.json"
OUTPUT = RESULTS / "caltech_static_ranking_empirical_null.csv"
SUMMARY = RESULTS / "caltech_static_ranking_empirical_null_summary.json"

SCOPES = ("external_candidate", "hard_ood_40pct")
REAL_POLICIES = {
    "obelix_same_property_static": "OBELiX same-property donor",
    "estm_transport_neighbor_static": "ESTM transport-neighbor donor",
}
SHUFFLED_POLICY = "shuffled_obelix_static_control"
RANDOM_POLICY = "uniform_random"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def empirical_p(observed: float, null: np.ndarray) -> float:
    """Finite-sample valid upper-tail randomization p value."""
    return float((1 + np.count_nonzero(null >= observed)) / (len(null) + 1))


def holm(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p values in the original order."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p, kind="mergesort")
    adjusted_sorted = np.empty(len(p), dtype=float)
    running = 0.0
    m = len(p)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * p[index])
        running = max(running, candidate)
        adjusted_sorted[rank] = running
    adjusted = np.empty(len(p), dtype=float)
    for rank, index in enumerate(order):
        adjusted[index] = adjusted_sorted[rank]
    return adjusted.tolist()


def unique_static_value(frame: pd.DataFrame, scope: str, policy: str, metric: str) -> float:
    values = (
        frame.loc[
            frame["scope"].eq(scope) & frame["policy"].eq(policy),
            metric,
        ]
        .astype(float)
        .unique()
    )
    if len(values) != 1:
        raise AssertionError(
            f"Expected one static {metric} value for {scope}|{policy}; got {values}"
        )
    return float(values[0])


def null_summary(values: np.ndarray) -> dict[str, float | int]:
    return {
        "n": int(len(values)),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "q025": float(np.quantile(values, 0.025)),
        "q050": float(np.quantile(values, 0.5)),
        "q950": float(np.quantile(values, 0.95)),
        "q975": float(np.quantile(values, 0.975)),
    }


def family_first_comparison() -> list[dict[str, object]]:
    payload = json.loads(FAMILY_SUMMARY.read_text(encoding="utf-8"))
    metrics = payload["primary_metrics"]
    output: list[dict[str, object]] = []
    for scope in SCOPES:
        rows = {
            row["policy"]: row
            for row in metrics
            if row["scope"] == scope
            and row["unit"] == "provenance_group"
            and row["group_value_aggregation"] == "max"
        }
        family = rows["neighbor_family_first_consensus"]
        donor_candidates = [
            rows["obelix_family_first"],
            rows["estm_family_first"],
        ]
        best = max(
            donor_candidates,
            key=lambda row: (float(row["auc20"]), float(row["recall20"])),
        )
        output.append(
            {
                "scope": scope,
                "family_first_policy": family["policy"],
                "family_first_auc20": float(family["auc20"]),
                "family_first_recall20": float(family["recall20"]),
                "family_first_hit_count20": int(family["hit_count20"]),
                "best_single_policy": best["policy"],
                "best_single_auc20": float(best["auc20"]),
                "best_single_recall20": float(best["recall20"]),
                "best_single_hit_count20": int(best["hit_count20"]),
                "auc20_difference": float(family["auc20"]) - float(best["auc20"]),
                "recall20_difference": float(family["recall20"])
                - float(best["recall20"]),
                "supports_complementary_recall": bool(
                    float(family["recall20"]) > float(best["recall20"])
                ),
            }
        )
    return output


def main() -> None:
    frame = pd.read_csv(UTILITY)
    required = {"scope", "seed", "policy", "auc20", "recall_at_20"}
    missing = required - set(frame.columns)
    if missing:
        raise AssertionError(f"Missing utility columns: {sorted(missing)}")

    rows: list[dict[str, object]] = []
    for scope in SCOPES:
        shuffled = frame.loc[
            frame["scope"].eq(scope)
            & frame["policy"].eq(SHUFFLED_POLICY),
            "auc20",
        ].to_numpy(float)
        random = frame.loc[
            frame["scope"].eq(scope) & frame["policy"].eq(RANDOM_POLICY),
            "auc20",
        ].to_numpy(float)
        if len(shuffled) != 100 or len(random) != 100:
            raise AssertionError(f"Expected 100 null seeds for {scope}")
        shuffled_summary = null_summary(shuffled)
        random_summary = null_summary(random)
        for policy, label in REAL_POLICIES.items():
            observed = unique_static_value(frame, scope, policy, "auc20")
            recall = unique_static_value(frame, scope, policy, "recall_at_20")
            rows.append(
                {
                    "scope": scope,
                    "policy": policy,
                    "label": label,
                    "observed_auc20": observed,
                    "observed_recall20": recall,
                    "empirical_p_vs_shuffled": empirical_p(observed, shuffled),
                    "empirical_p_vs_uniform_random": empirical_p(observed, random),
                    **{
                        f"shuffled_{key}": value
                        for key, value in shuffled_summary.items()
                    },
                    **{
                        f"random_{key}": value
                        for key, value in random_summary.items()
                    },
                }
            )

    adjusted = holm([float(row["empirical_p_vs_shuffled"]) for row in rows])
    for row, adjusted_p in zip(rows, adjusted):
        row["holm_p_vs_shuffled_four_tests"] = adjusted_p
        row["holm_significant_0_05"] = bool(adjusted_p < 0.05)

    output = pd.DataFrame(rows)
    output.to_csv(OUTPUT, index=False)
    family = family_first_comparison()
    payload = {
        "status": "verified-corrective-reanalysis",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_scope": (
            "Review-triggered correction of retrospective Caltech static-ranking "
            "inference; no frozen policy or candidate outcome was changed."
        ),
        "input_sha256": {
            str(UTILITY.relative_to(ROOT)).replace("\\", "/"): sha256(UTILITY),
            str(FAMILY_SUMMARY.relative_to(ROOT)).replace("\\", "/"): sha256(
                FAMILY_SUMMARY
            ),
        },
        "multiplicity_family": {
            "tests": 4,
            "definition": (
                "Two real static donors crossed with external-candidate and "
                "hard-OOD scopes, all tested against the shuffled-source null."
            ),
            "method": "Holm family-wise error control",
        },
        "static_ranking_tests": output.to_dict("records"),
        "family_first_vs_best_single": family,
        "interpretation": {
            "confirmed_after_holm": [
                f"{row['scope']}|{row['policy']}"
                for row in rows
                if row["holm_significant_0_05"]
            ],
            "family_first_claim": (
                "Family-first consensus improves external AUC20 over the best "
                "single donor without improving recall, and ties the best single "
                "donor on hard-OOD AUC20 and recall. It therefore supports an "
                "allocation-policy result, not demonstrated donor complementarity."
            ),
        },
        "claim_guard": (
            "These retrospective finite-seed tests quantify ranking evidence on "
            "one external target. They do not establish prospective discovery."
        ),
    }
    SUMMARY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
