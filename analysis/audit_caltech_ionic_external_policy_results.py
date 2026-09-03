"""Audit the verified Caltech policy result and isolate post-result method selection."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .run_caltech_ionic_external_policy import composition_novelty, load_target
except ImportError:
    from run_caltech_ionic_external_policy import composition_novelty, load_target

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PREFIX = "caltech_ionic_external_policy"
OUTPUT = RESULTS / "caltech_ionic_external_policy_validation.json"
PORTFOLIO_OUTPUT = RESULTS / "caltech_neighbor_portfolio_diagnostic.csv"


def load_inputs() -> tuple[dict, dict, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    verified = json.loads((RESULTS / f"{PREFIX}_VERIFIED.json").read_text(encoding="utf-8"))
    summary = json.loads((RESULTS / f"{PREFIX}_summary.json").read_text(encoding="utf-8"))
    contrasts = pd.read_csv(RESULTS / f"{PREFIX}_contrasts.csv")
    utility = pd.read_csv(RESULTS / f"{PREFIX}_utility.csv")
    trajectories = pd.read_csv(RESULTS / f"{PREFIX}_trajectories.csv")
    if verified["status"] != "VERIFIED" or summary["status"] != "complete":
        raise AssertionError("The formal result is not verified and complete")
    if len(trajectories) != 120_000 or len(utility) != 3_000 or len(contrasts) != 16:
        raise AssertionError("Formal output coverage is incomplete")
    return verified, summary, contrasts, utility, trajectories


def mean_utility(utility: pd.DataFrame) -> pd.DataFrame:
    return (
        utility.groupby(["scope", "policy"], as_index=False)
        .agg(
            auc20=("auc20", "mean"),
            first_hit=("first_hit", "mean"),
            recall20=("recall_at_20", "mean"),
            recall40=("recall_at_40", "mean"),
            regret20=("regret_at_20", "mean"),
        )
    )


def build_neighbor_portfolios(trajectories: pd.DataFrame) -> pd.DataFrame:
    target, _, x_scaled = load_target()
    candidate = target.index[target["split"] == "candidate"].astype(int).tolist()
    development = target.index[target["split"] == "development"].astype(int).tolist()
    distance = composition_novelty(x_scaled[candidate], x_scaled[development])
    hard_n = int(math.ceil(0.40 * len(candidate)))
    hard = [candidate[index] for index in np.argsort(distance)[-hard_n:]]
    pools = {"external_candidate": candidate, "hard_ood_40pct": hard}
    source_policies = ["obelix_same_property_static", "estm_transport_neighbor_static"]
    rows: list[dict] = []
    for scope, pool in pools.items():
        top_n = int(math.ceil(0.05 * len(pool)))
        top = set(
            target.loc[pool]
            .sort_values(["value", "material_key"], ascending=[False, True])
            .index[:top_n]
            .astype(int)
        )
        pool_max = float(target.loc[pool, "value"].max())
        for seed in range(100):
            local = trajectories[
                (trajectories["scope"] == scope) & (trajectories["seed"] == seed)
            ]
            orders = {
                policy: local[local["policy"] == policy]
                .sort_values("step")["chosen_index"]
                .astype(int)
                .tolist()
                for policy in source_policies
            }
            round_robin: list[int] = []
            for rank in range(40):
                for policy in source_policies:
                    candidate_index = orders[policy][rank]
                    if candidate_index not in round_robin:
                        round_robin.append(candidate_index)
                    if len(round_robin) == 40:
                        break
                if len(round_robin) == 40:
                    break
            ranks = {
                policy: {index: rank + 1 for rank, index in enumerate(order)}
                for policy, order in orders.items()
            }
            union = set(orders[source_policies[0]]) | set(orders[source_policies[1]])
            consensus = sorted(
                union,
                key=lambda index: (
                    -sum(max(0, 41 - ranks[policy].get(index, 41)) for policy in source_policies),
                    target.at[index, "material_key"],
                ),
            )[:40]
            for policy, order in (
                ("neighbor_round_robin", round_robin),
                ("neighbor_consensus_top40", consensus),
            ):
                hits = np.asarray([index in top for index in order], dtype=bool)
                cumulative = np.cumsum(hits)
                hit_steps = np.flatnonzero(hits)
                rows.append(
                    {
                        "scope": scope,
                        "seed": seed,
                        "policy": policy,
                        "auc20": float(np.sum(cumulative[:20])),
                        "first_hit": int(hit_steps[0] + 1) if len(hit_steps) else 41,
                        "recall20": float(np.sum(hits[:20]) / top_n),
                        "recall40": float(np.sum(hits[:40]) / top_n),
                        "regret20": float(pool_max - target.loc[order[:20], "value"].max()),
                    }
                )
    return pd.DataFrame(rows)


def records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records"))


def main() -> None:
    verified, summary, contrasts, utility, trajectories = load_inputs()
    means = mean_utility(utility)
    gates = pd.read_csv(RESULTS / f"{PREFIX}_gate_summary.csv")
    portfolio = build_neighbor_portfolios(trajectories)
    portfolio.to_csv(PORTFOLIO_OUTPUT, index=False)
    portfolio_means = (
        portfolio.groupby(["scope", "policy"], as_index=False)
        .agg(
            auc20=("auc20", "mean"),
            first_hit=("first_hit", "mean"),
            recall20=("recall20", "mean"),
            recall40=("recall40", "mean"),
            regret20=("regret20", "mean"),
        )
    )

    source_increment = contrasts[contrasts["family"].isin(
        ["same_property_increment", "adjacent_transport_increment", "safe_multisource_increment"]
    )]
    policy_validity = contrasts[contrasts["family"] == "policy_validity"]
    safe_target_vs_novelty = policy_validity[
        policy_validity["left_policy"] == "safe_target_novelty"
    ]
    novelty_vs_random = policy_validity[
        policy_validity["left_policy"] == "composition_novelty"
    ]

    static_neighbors = ["obelix_same_property_static", "estm_transport_neighbor_static"]
    static_references = [
        "uniform_random",
        "shuffled_obelix_static_control",
        "borg_mechanical_static_control",
        "ocx_catalysis_static_control",
    ]
    static_specific = True
    for scope in means["scope"].unique():
        local = means[means["scope"] == scope].set_index("policy")
        static_specific &= bool(
            local.loc[static_neighbors, "auc20"].min()
            > local.loc[static_references, "auc20"].max()
        )

    neighbor_gate = gates[
        gates["policy"].isin(["safe_obelix_residual", "safe_estm_residual"])
        & ~gates["source"].eq("__target__")
    ]
    wrong_gate = gates[
        gates["policy"].isin(
            [
                "safe_borg_residual_control",
                "safe_ocx_residual_control",
                "safe_shuffled_obelix_control",
            ]
        )
        & ~gates["source"].eq("__target__")
    ]

    report = {
        "status": "verified-primary-policy-null-with-post-result-source-portfolio-selection",
        "formal_job_id": verified["formal_job_id"],
        "verification_job_id": verified["verification_job_id"],
        "trajectory_rows": len(trajectories),
        "gate_rows": int(summary["gate_rows"]),
        "utility_rows": len(utility),
        "primary_contrasts": len(contrasts),
        "global_decisions": {
            "all_negative_transfer_weight_guards_pass": bool(
                summary["all_negative_transfer_guards_pass"]
            ),
            "composition_novelty_beats_random_in_both_scopes": bool(
                novelty_vs_random["passes_incremental_statistical"].all()
                and novelty_vs_random["passes_incremental_practical"].all()
                and novelty_vs_random["passes_consistency"].all()
            ),
            "safe_target_backbone_beats_novelty_in_both_scopes": bool(
                safe_target_vs_novelty["passes_incremental_statistical"].all()
                and safe_target_vs_novelty["passes_incremental_practical"].all()
                and safe_target_vs_novelty["passes_consistency"].all()
            ),
            "any_confirmatory_source_increment_passes_all_gates": bool(
                (
                    source_increment[
                        [
                            "passes_incremental_statistical",
                            "passes_incremental_practical",
                            "passes_consistency",
                            "passes_first_hit_noninferiority",
                            "passes_absolute_recall",
                        ]
                    ].all(axis=1)
                ).any()
            ),
            "neighbor_gates_have_higher_mean_admission_than_wrong_controls": bool(
                neighbor_gate["admission_rate"].mean() > wrong_gate["admission_rate"].mean()
            ),
            "prespecified_static_neighbors_exceed_all_static_references_descriptively": bool(
                static_specific
            ),
            "post_result_portfolio_recall20_at_least_half_in_both_scopes": bool(
                (portfolio_means["recall20"] >= 0.50).all()
            ),
            "new_science_endpoint_tested": False,
        },
        "confirmatory_contrasts": records(contrasts),
        "policy_utility_means": records(means),
        "source_gate_means": records(gates),
        "post_result_neighbor_portfolio": records(portfolio_means),
        "interpretation": {
            "confirmed": "Wrong-source weights are suppressed under the frozen guard; no adaptive source-aware policy improves broad recovery beyond its target-only comparator.",
            "descriptive": "Both prespecified real-neighbor static rankings exceed random, shuffled, mechanical and catalysis rankings in both scopes, but no primary static-source contrast or dataset-level replication interval was frozen.",
            "method_selected": "A target-model-free portfolio that alternates or combines OBELiX and ESTM shortlists recovers complementary high-value candidates and should be frozen on a new target.",
            "rejected_mechanism": "Cross-validated residual injection and target-mean steering do not convert the source ranking signal into a reliable sequential policy on this target.",
        },
        "claim_guard": "The verified primary external result is null for adaptive source-aware acquisition. Static-source and portfolio findings select the next independent method only; they do not establish prospective discovery, new science, or a field-wide rescue claim.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], **report["global_decisions"]}, indent=2))


if __name__ == "__main__":
    main()
