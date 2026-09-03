"""Post-result diagnostics for the frozen OBELiX sequential campaign.

These summaries explain the completed primary analysis; they do not redefine
its endpoints, gates, or decision status.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"


def stable_seed(label: str) -> int:
    return int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def random_censored_expectation(candidate_n: int, hit_n: int, budget: int) -> float:
    """E[min(first random hit, budget + 1)] without replacement."""
    expectation = 0.0
    for acquired in range(0, budget + 1):
        if acquired > candidate_n - hit_n:
            survival = 0.0
        else:
            survival = math.comb(candidate_n - hit_n, acquired) / math.comb(
                candidate_n, acquired
            )
        expectation += survival
    return expectation


def paired_diagnostic(
    pivot: pd.DataFrame,
    *,
    left: str,
    right: str,
    scope: str,
    bootstrap_n: int = 5000,
    signflip_n: int = 9999,
) -> dict:
    effect = (pivot[left] - pivot[right]).to_numpy(float)
    rng = np.random.default_rng(stable_seed(f"diagnostic:{scope}:{left}:{right}"))
    indices = rng.integers(0, len(effect), size=(bootstrap_n, len(effect)))
    bootstrap = effect[indices].mean(axis=1)
    observed = float(effect.mean())
    sign_rng = np.random.default_rng(
        stable_seed(f"diagnostic-sign:{scope}:{left}:{right}")
    )
    exceed = 0
    remaining = signflip_n
    while remaining:
        batch = min(1000, remaining)
        signs = sign_rng.choice((-1.0, 1.0), size=(batch, len(effect)))
        exceed += int(np.sum((signs * effect).mean(axis=1) >= observed))
        remaining -= batch
    return {
        "scope": scope,
        "contrast": f"{left}_minus_{right}",
        "interpretation": f"positive means {right} requires fewer acquisitions",
        "seeds": len(effect),
        "left_mean": float(pivot[left].mean()),
        "right_mean": float(pivot[right].mean()),
        "mean_difference": observed,
        "bootstrap_95": [float(x) for x in np.quantile(bootstrap, [0.025, 0.975])],
        "fraction_positive": float(np.mean(effect > 0)),
        "fraction_tied": float(np.mean(effect == 0)),
        "signflip_p_one_sided": float((exceed + 1) / (signflip_n + 1)),
        "status": "post-result diagnostic; does not redefine frozen decision",
    }


def main() -> None:
    reaches = pd.read_csv(RESULTS / "obelix_ood_discovery_reach.csv")
    primary = reaches[reaches["model_family"] == "extra-trees-primary"].copy()
    scopes = ["official_test", "hard_ood_40pct"]
    strategies = [
        "target_only",
        "thermoelectric_prior",
        "shuffled_thermoelectric_control",
        "random_control",
    ]

    survival_rows: list[dict] = []
    random_reference: dict[str, dict] = {}
    pairwise: list[dict] = []
    for scope in scopes:
        local = primary[primary["scope"] == scope]
        budget = int(local["budget"].iloc[0])
        candidate_n = int(local["candidate_n"].iloc[0])
        hit_n = int(local["true_hit_n"].iloc[0])
        for strategy in strategies:
            values = local.loc[
                local["strategy"] == strategy, "experiments_to_hit"
            ].to_numpy(int)
            for step in range(0, budget + 1):
                survival_rows.append(
                    {
                        "scope": scope,
                        "strategy": strategy,
                        "step": step,
                        "probability_hit": float(np.mean(values <= step)),
                        "seeds": len(values),
                        "candidate_n": candidate_n,
                        "true_hit_n": hit_n,
                    }
                )
        random_values = local.loc[
            local["strategy"] == "random_control", "experiments_to_hit"
        ].to_numpy(float)
        random_reference[scope] = {
            "candidate_n": candidate_n,
            "true_hit_n": hit_n,
            "budget": budget,
            "exact_censored_random_mean": random_censored_expectation(
                candidate_n, hit_n, budget
            ),
            "empirical_random_mean": float(random_values.mean()),
            "empirical_random_median": float(np.median(random_values)),
            "empirical_random_censor_fraction": float(
                np.mean(random_values > budget)
            ),
        }
        pivot = local.pivot(
            index="seed", columns="strategy", values="experiments_to_hit"
        )
        pairwise.extend(
            [
                paired_diagnostic(
                    pivot,
                    left="target_only",
                    right="random_control",
                    scope=scope,
                ),
                paired_diagnostic(
                    pivot,
                    left="thermoelectric_prior",
                    right="random_control",
                    scope=scope,
                ),
            ]
        )

    survival = pd.DataFrame(survival_rows)
    survival.to_csv(
        RESULTS / "obelix_ood_discovery_survival.csv", index=False
    )
    pairwise_frame = pd.DataFrame(pairwise)
    pairwise_frame["bootstrap_95"] = pairwise_frame["bootstrap_95"].map(json.dumps)
    pairwise_frame.to_csv(
        RESULTS / "obelix_ood_discovery_pairwise_diagnostics.csv", index=False
    )
    output = {
        "analysis_status": "post-result-explanatory-diagnostic",
        "primary_decision_unchanged": "directional-only; no OOD-discovery improvement or rescue",
        "random_reference": random_reference,
        "pairwise_diagnostics": pairwise,
        "claim_guard": (
            "Random acquisition outperforming the tested UCB policies establishes "
            "policy-level failure under this retrospective pool. It does not identify "
            "whether mean ranking, uncertainty calibration, or iterative refitting is "
            "the cause, and it does not establish random search as generally optimal."
        ),
    }
    (RESULTS / "obelix_ood_discovery_diagnostics.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
