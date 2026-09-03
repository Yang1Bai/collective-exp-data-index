"""Independent semantic verification of the frozen FINALES rank-transfer test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SUMMARY_PATH = RESULTS / "finales_rank_replication_summary.json"
CANDIDATE_PATH = RESULTS / "finales_rank_replication_candidates.csv"
METRICS_PATH = RESULTS / "finales_rank_replication_metrics.csv"
BOOTSTRAP_PATH = RESULTS / "finales_rank_replication_bootstrap.csv"
NULL_PATH = RESULTS / "finales_rank_replication_shuffled_null.csv"
COMPLETE_PATH = RESULTS / "finales_rank_replication_complete.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def concordance(
    outcome: np.ndarray,
    score: np.ndarray,
    temperature: np.ndarray,
    tolerance: float,
) -> tuple[float, int]:
    agreements = 0
    eligible = 0
    for left in range(len(outcome)):
        for right in range(left + 1, len(outcome)):
            if abs(temperature[left] - temperature[right]) > tolerance:
                continue
            outcome_delta = outcome[left] - outcome[right]
            score_delta = score[left] - score[right]
            if outcome_delta == 0 or score_delta == 0:
                continue
            eligible += 1
            agreements += int(np.sign(outcome_delta) == np.sign(score_delta))
    return agreements / eligible, eligible


def require_close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(actual, expected, rtol=0, atol=1e-12):
        raise AssertionError(f"{label}: {actual} != {expected}")


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    candidates = pd.read_csv(CANDIDATE_PATH)
    metrics = pd.read_csv(METRICS_PATH)
    bootstrap = pd.read_csv(BOOTSTRAP_PATH)["bootstrap_advantage"].dropna().to_numpy()
    shuffled = pd.read_csv(NULL_PATH)["shuffled_donor_concordance"].dropna().to_numpy()

    evaluation = candidates.loc[candidates["split"] == "evaluation"].copy()
    tolerance = float(summary["primary"]["temperature_tolerance_C"])
    donor, donor_pairs = concordance(
        evaluation["conductivity"].to_numpy(),
        evaluation["calisol_rank_score"].to_numpy(),
        evaluation["temperature_C"].to_numpy(),
        tolerance,
    )
    baseline_name = str(summary["primary"]["strongest_recipient_baseline"])
    baseline, baseline_pairs = concordance(
        evaluation["conductivity"].to_numpy(),
        evaluation[baseline_name].to_numpy(),
        evaluation["temperature_C"].to_numpy(),
        tolerance,
    )

    require_close(donor, float(summary["primary"]["donor_concordance"]), "donor concordance")
    require_close(
        baseline,
        float(summary["primary"]["strongest_baseline_concordance"]),
        "baseline concordance",
    )
    require_close(
        donor - baseline,
        float(summary["primary"]["concordance_advantage"]),
        "concordance advantage",
    )
    if donor_pairs != int(summary["primary"]["eligible_pairs"]):
        raise AssertionError("Donor eligible-pair count changed")

    primary = metrics.loc[metrics["scope"] == "primary_multitask"].set_index("score")
    require_close(
        float(primary.loc["calisol_rank_score", "pairwise_concordance"]),
        donor,
        "metrics donor concordance",
    )
    require_close(
        float(primary.loc[baseline_name, "pairwise_concordance"]),
        baseline,
        "metrics baseline concordance",
    )
    if int(primary.loc[baseline_name, "eligible_pairs"]) != baseline_pairs:
        raise AssertionError("Baseline eligible-pair count changed")

    if len(bootstrap) != 20000:
        raise AssertionError(f"Expected 20,000 bootstrap rows, found {len(bootstrap)}")
    ci = np.quantile(bootstrap, [0.025, 0.975])
    require_close(float(ci[0]), float(summary["primary"]["bootstrap_ci95"][0]), "CI lower")
    require_close(float(ci[1]), float(summary["primary"]["bootstrap_ci95"][1]), "CI upper")

    if len(shuffled) != 2000:
        raise AssertionError(f"Expected 2,000 shuffled controls, found {len(shuffled)}")
    permutation_p = (1 + int(np.sum(shuffled >= donor))) / (len(shuffled) + 1)
    require_close(
        float(permutation_p),
        float(summary["primary"]["permutation_p"]),
        "permutation p",
    )

    if not (
        donor < baseline
        and ci[0] < 0 < ci[1]
        and float(summary["primary"]["donor_normalized_regret"])
        > float(summary["primary"]["baseline_normalized_regret"])
        and summary["decision"] == "not-replicated"
        and summary["success_gate_passed"] is False
    ):
        raise AssertionError("Frozen decision is not supported by the independently checked outputs")

    files = [
        SUMMARY_PATH,
        CANDIDATE_PATH,
        RESULTS / "finales_rank_replication_secondary_candidates.csv",
        METRICS_PATH,
        BOOTSTRAP_PATH,
        NULL_PATH,
    ]
    complete = {
        "status": "independently-verified-complete",
        "decision": "not-replicated",
        "evaluation_formulations": len(evaluation),
        "donor_eligible_pairs": donor_pairs,
        "baseline_eligible_pairs": baseline_pairs,
        "bootstrap_rows": len(bootstrap),
        "shuffled_control_rows": len(shuffled),
        "verified_primary": {
            "donor_concordance": donor,
            "baseline_concordance": baseline,
            "concordance_advantage": donor - baseline,
            "bootstrap_ci95": [float(ci[0]), float(ci[1])],
            "permutation_p": float(permutation_p),
        },
        "sha256": {path.name: sha256(path) for path in files},
        "claim_guard": (
            "The unchanged CALiSol ranking did not replicate against the strongest "
            "three-anchor recipient-only baseline in the frozen FINALES primary phase."
        ),
    }
    COMPLETE_PATH.write_text(
        json.dumps(complete, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(complete, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
