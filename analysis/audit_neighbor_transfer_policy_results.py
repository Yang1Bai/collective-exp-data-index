"""Audit the post-diagnostic neighborhood-transfer policy benchmark.

This is an author-side method-selection audit, not a confirmatory analysis.
It independently summarizes the frozen comparisons, adds explicitly post-hoc
paired descriptions against the validated novelty baseline, and writes a
machine-readable claim guard.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
OUTPUT = RESULTS / "neighbor_transfer_policy_validation.json"
BOOTSTRAP_REPLICATES = 5000


def stable_seed(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "little")


def as_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().lower() == "true"


def posthoc_pair(
    frame: pd.DataFrame,
    *,
    scope: str,
    left: str,
    right: str,
) -> dict:
    local = frame[frame["scope"] == scope]
    paired = local.pivot(index="seed", columns="policy", values="experiments_to_hit")
    effect = (paired[right] - paired[left]).to_numpy(float)
    rng = np.random.default_rng(stable_seed(f"posthoc:{scope}:{left}:{right}"))
    indices = rng.integers(
        0, len(effect), size=(BOOTSTRAP_REPLICATES, len(effect))
    )
    bootstrap = effect[indices].mean(axis=1)
    return {
        "scope": scope,
        "left_policy": left,
        "right_policy": right,
        "effect_definition": (
            "right-policy acquisitions minus left-policy acquisitions; "
            "positive favors left"
        ),
        "mean_experiments_saved_by_left": float(effect.mean()),
        "descriptive_bootstrap_95": [
            float(value) for value in np.quantile(bootstrap, [0.025, 0.975])
        ],
        "fraction_seeds_left_improves": float(np.mean(effect > 0)),
        "fraction_seeds_tied": float(np.mean(effect == 0)),
        "status": "post-hoc descriptive; no confirmatory p value",
    }


def utility_difference(
    utility: pd.DataFrame,
    *,
    scope: str,
    left: str,
    right: str,
    metric: str,
) -> dict:
    local = utility[utility["scope"] == scope]
    paired = local.pivot(index="seed", columns="policy", values=metric)
    effect = (paired[left] - paired[right]).to_numpy(float)
    rng = np.random.default_rng(
        stable_seed(f"posthoc-utility:{scope}:{left}:{right}:{metric}")
    )
    indices = rng.integers(
        0, len(effect), size=(BOOTSTRAP_REPLICATES, len(effect))
    )
    bootstrap = effect[indices].mean(axis=1)
    return {
        "metric": metric,
        "mean_left_minus_right": float(effect.mean()),
        "descriptive_bootstrap_95": [
            float(value) for value in np.quantile(bootstrap, [0.025, 0.975])
        ],
    }


def contrast_row(
    contrasts: pd.DataFrame,
    *,
    scope: str,
    left: str,
    right: str,
) -> dict:
    local = contrasts[
        (contrasts["scope"] == scope)
        & (contrasts["left_policy"] == left)
        & (contrasts["right_policy"] == right)
    ]
    if len(local) != 1:
        raise AssertionError(f"Expected one contrast for {scope}: {left} vs {right}")
    row = local.iloc[0]
    return {
        "scope": scope,
        "left_policy": left,
        "right_policy": right,
        "mean_experiments_saved_by_left": float(
            row["mean_experiments_saved_by_left"]
        ),
        "bootstrap_95": json.loads(row["bootstrap_95"]),
        "holm_p": float(row["holm_p"]),
        "fraction_seeds_left_improves": float(
            row["fraction_seeds_left_improves"]
        ),
        "passes_development_gates": as_bool(row["passes_development_gates"]),
    }


def main() -> None:
    summary = json.loads(
        (RESULTS / "neighbor_transfer_policy_summary.json").read_text(
            encoding="utf-8"
        )
    )
    reach = pd.read_csv(RESULTS / "neighbor_transfer_policy_reach.csv")
    trajectories = pd.read_csv(
        RESULTS / "neighbor_transfer_policy_trajectories.csv"
    )
    contrasts = pd.read_csv(RESULTS / "neighbor_transfer_policy_contrasts.csv")
    utility = pd.read_csv(
        RESULTS / "neighbor_transfer_policy_secondary_utility.csv"
    )

    scopes = ["official_test", "hard_ood_40pct"]
    prespecified: dict[str, list[dict]] = {}
    for scope in scopes:
        prespecified[scope] = [
            contrast_row(
                contrasts,
                scope=scope,
                left="target_mean_greedy",
                right="uniform_random",
            ),
            contrast_row(
                contrasts,
                scope=scope,
                left="composition_novelty",
                right="uniform_random",
            ),
            contrast_row(
                contrasts,
                scope=scope,
                left="thermoelectric_prior_static",
                right="uniform_random",
            ),
            contrast_row(
                contrasts,
                scope=scope,
                left="thermoelectric_prior_static",
                right="catalysis_prior_static_control",
            ),
            contrast_row(
                contrasts,
                scope=scope,
                left="target_source_rank_fusion",
                right="target_mean_greedy",
            ),
            contrast_row(
                contrasts,
                scope=scope,
                left="target_source_novelty_rank_fusion",
                right="target_mean_greedy",
            ),
        ]

    posthoc_first_hit: list[dict] = []
    posthoc_utility: list[dict] = []
    for scope in scopes:
        for left in (
            "thermoelectric_prior_static",
            "target_source_rank_fusion",
            "target_source_novelty_rank_fusion",
        ):
            posthoc_first_hit.append(
                posthoc_pair(
                    reach,
                    scope=scope,
                    left=left,
                    right="composition_novelty",
                )
            )
        for metric in (
            "cumulative_hit_auc_to_40",
            "top5_hits_at_20",
            "top5_recall_at_40",
            "regret_to_pool_max_at_40",
        ):
            posthoc_utility.append(
                {
                    "scope": scope,
                    "left_policy": "target_source_novelty_rank_fusion",
                    "right_policy": "composition_novelty",
                    **utility_difference(
                        utility,
                        scope=scope,
                        left="target_source_novelty_rank_fusion",
                        right="composition_novelty",
                        metric=metric,
                    ),
                    "status": "post-hoc descriptive; secondary endpoint",
                }
            )

    static_policies = [
        "thermoelectric_prior_static",
        "alloy_prior_static_control",
        "catalysis_prior_static_control",
        "shuffled_thermoelectric_static_control",
    ]
    static_variation = []
    for (scope, policy), local in reach[
        reach["policy"].isin(static_policies)
    ].groupby(["scope", "policy"], sort=True):
        static_variation.append(
            {
                "scope": scope,
                "policy": policy,
                "unique_first_hit_counts_across_100_seeds": int(
                    local["experiments_to_hit"].nunique()
                ),
            }
        )

    source_trajectory = trajectories[
        (trajectories["scope"] == "official_test")
        & (trajectories["seed"] == 0)
        & (trajectories["policy"] == "thermoelectric_prior_static")
    ].sort_values("step")
    first_hit = source_trajectory[
        source_trajectory["is_true_top5_hit"].astype(bool)
    ].iloc[0]

    target_mean_valid = all(
        not prespecified[scope][0]["passes_development_gates"] for scope in scopes
    )
    novelty_valid = all(
        prespecified[scope][1]["passes_development_gates"] for scope in scopes
    )
    source_vs_random = all(
        prespecified[scope][2]["passes_development_gates"] for scope in scopes
    )
    source_vs_catalysis = all(
        prespecified[scope][3]["passes_development_gates"] for scope in scopes
    )
    fusion_vs_mean = all(
        prespecified[scope][4]["passes_development_gates"]
        and prespecified[scope][5]["passes_development_gates"]
        for scope in scopes
    )

    result = {
        "status": "verified-exploratory-method-selection-not-claim-bearing",
        "design_sha256": summary["design_sha256"],
        "input_sha256": summary["input_sha256"],
        "analysis_status": summary["analysis_status"],
        "prespecified_contrasts": prespecified,
        "posthoc_first_hit_vs_composition_novelty": posthoc_first_hit,
        "posthoc_secondary_utility_fusion_vs_composition_novelty": posthoc_utility,
        "deterministic_static_policy_audit": static_variation,
        "first_thermoelectric_static_hit": {
            "step": int(first_hit["step"]),
            "candidate_index": int(first_hit["chosen_index"]),
            "candidate_key": str(first_hit["chosen_key"]),
            "target_value": float(first_hit["chosen_y"]),
            "guard": (
                "The first hit is one fixed Li-Y-Br candidate; it is not 100 "
                "independent discoveries."
            ),
        },
        "global_decisions": {
            "target_mean_backbone_fails_random_in_both_scopes": target_mean_valid,
            "composition_novelty_beats_random_in_both_scopes": novelty_valid,
            "source_static_beats_random_in_both_scopes": source_vs_random,
            "source_static_separates_from_catalysis_practically_in_both_scopes": (
                source_vs_catalysis
            ),
            "rank_fusions_beat_target_mean_in_both_scopes": fusion_vs_mean,
            "rank_fusion_increment_is_attributable_to_neighbor_borrowing": False,
            "reason_increment_not_attributable": (
                "The target-mean comparator fails against random; composition "
                "novelty is the valid target-only backbone, and neither source-only "
                "nor source-aware fusion improves the primary first-hit endpoint "
                "over novelty in both scopes."
            ),
            "negative_transfer_safety_gate_passes": False,
            "reason_negative_transfer_gate_fails": (
                "The thermoelectric source saves only two acquisitions relative "
                "to the catalysis control in each scope, below the frozen "
                "five-acquisition practical gate."
            ),
            "independent_external_validation_required": True,
            "new_science_endpoint_tested": False,
        },
        "method_selection": {
            "mandatory_target_only_comparator": "composition_novelty",
            "candidate_for_first_hit_screening": [
                "composition_novelty",
                "thermoelectric_prior_static",
            ],
            "candidate_for_breadth_on_an_unseen_official-like_pool": (
                "target_source_novelty_rank_fusion"
            ),
            "must_not_claim": [
                "confirmed OBELiX discovery acceleration",
                "neighbor-specific OOD benefit beyond composition novelty",
                "prospective discovery of new science",
            ],
        },
        "claim_guard": summary["claim_guard"],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["global_decisions"], indent=2))
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
