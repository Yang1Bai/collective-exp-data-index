"""Post-outcome sensitivity of the frozen FINALES result to anchor policy.

The formal result used the first three chronological formulations.  This
analysis instead applies the outcome-independent maximin coverage rule used in
the SolventSeg stress test, over 100 deterministic starts.  The CALiSol donor
score, recipient model family, endpoint, temperature tolerance, and candidate
pool remain unchanged.  The result is diagnostic only and cannot replace the
frozen chronological decision.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler

from common import RESULTS
from mixture_response_transfer_common import maximin_anchors, sha256, stable_seed
from run_finales_rank_replication import (
    FEATURES,
    TARGET,
    concordance,
    make_target_models,
)


HERE = Path(__file__).resolve().parent
CANDIDATES_PATH = RESULTS / "finales_rank_replication_candidates.csv"
FROZEN_SUMMARY_PATH = RESULTS / "finales_rank_replication_summary.json"
METRICS_PATH = RESULTS / "finales_anchor_policy_sensitivity_metrics.csv"
SUMMARY_PATH = RESULTS / "finales_anchor_policy_sensitivity_summary.json"


def main() -> None:
    candidates = pd.read_csv(CANDIDATES_PATH).sort_values("candidate_index")
    if len(candidates) != 19 or candidates["formulation_key"].nunique() != 19:
        raise AssertionError("FINALES primary candidate pool changed")
    frozen = json.loads(FROZEN_SUMMARY_PATH.read_text(encoding="utf-8"))
    tolerance = float(frozen["primary"]["temperature_tolerance_C"])

    x = candidates[FEATURES].to_numpy(dtype=float)
    compact = StandardScaler().fit_transform(x)
    groups = candidates["formulation_key"].astype(str).to_numpy()
    models = make_target_models()
    rows: list[dict] = []
    for draw in range(100):
        anchors = maximin_anchors(
            compact,
            groups,
            budget=3,
            start_index=stable_seed("finales-maximin-anchor", draw),
        )
        evaluation = np.flatnonzero(~np.isin(np.arange(len(candidates)), anchors))
        donor_concordance, donor_pairs = concordance(
            candidates.iloc[evaluation][TARGET].to_numpy(),
            candidates.iloc[evaluation]["calisol_rank_score"].to_numpy(),
            candidates.iloc[evaluation]["temperature_C"].to_numpy(),
            tolerance,
        )
        rows.append(
            {
                "draw": draw,
                "model": "calisol_rank_score",
                "anchor_indices": json.dumps(sorted(anchors.tolist())),
                "evaluation_formulations": len(evaluation),
                "pairwise_concordance": donor_concordance,
                "eligible_pairs": donor_pairs,
            }
        )
        for name, prototype in models.items():
            model = clone(prototype)
            model.fit(candidates.iloc[anchors][FEATURES], candidates.iloc[anchors][TARGET])
            score = model.predict(candidates.iloc[evaluation][FEATURES])
            value, pairs = concordance(
                candidates.iloc[evaluation][TARGET].to_numpy(),
                np.asarray(score, dtype=float),
                candidates.iloc[evaluation]["temperature_C"].to_numpy(),
                tolerance,
            )
            rows.append(
                {
                    "draw": draw,
                    "model": name,
                    "anchor_indices": json.dumps(sorted(anchors.tolist())),
                    "evaluation_formulations": len(evaluation),
                    "pairwise_concordance": value,
                    "eligible_pairs": pairs,
                }
            )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(METRICS_PATH, index=False)
    donor = metrics[metrics["model"].eq("calisol_rank_score")].set_index("draw")
    recipient = metrics[~metrics["model"].eq("calisol_rank_score")]
    recipient_macro = (
        recipient.groupby("model", sort=True)["pairwise_concordance"]
        .mean()
        .dropna()
        .sort_values(ascending=False)
    )
    strongest = str(recipient_macro.index[0])
    strongest_draw = recipient[recipient["model"].eq(strongest)].set_index("draw")
    difference = donor["pairwise_concordance"] - strongest_draw["pairwise_concordance"]
    oracle = recipient.groupby("draw")["pairwise_concordance"].max()
    oracle_difference = donor["pairwise_concordance"] - oracle
    valid = difference.dropna()
    valid_oracle = oracle_difference.dropna()

    summary = {
        "status": "complete-post-outcome-anchor-policy-sensitivity",
        "claim_guard": (
            "This analysis was performed after FINALES outcomes and the frozen chronological result "
            "were known. It diagnoses anchor-policy dependence but cannot replace or confirm the frozen decision."
        ),
        "candidate_pool": 19,
        "anchor_budget": 3,
        "evaluation_formulations_per_draw": 16,
        "draws": 100,
        "unique_anchor_sets": int(metrics.drop_duplicates("draw")["anchor_indices"].nunique()),
        "anchor_policy": "outcome-independent maximin coverage with deterministic start seeds",
        "unchanged_elements": [
            "CALiSol donor score",
            "recipient model family",
            "conductivity endpoint",
            "temperature tolerance",
            "candidate pool",
        ],
        "strongest_average_recipient_model": strongest,
        "mean_concordance": {
            "donor": float(donor["pairwise_concordance"].mean()),
            "strongest_recipient": float(strongest_draw["pairwise_concordance"].mean()),
        },
        "donor_minus_strongest_recipient": {
            "mean": float(valid.mean()),
            "anchor_selection_interval95": [
                float(valid.quantile(0.025)),
                float(valid.quantile(0.975)),
            ],
            "positive_draw_fraction": float((valid > 0).mean()),
            "valid_draws": int(len(valid)),
        },
        "donor_minus_per_draw_oracle": {
            "mean": float(valid_oracle.mean()),
            "anchor_selection_interval95": [
                float(valid_oracle.quantile(0.025)),
                float(valid_oracle.quantile(0.975)),
            ],
        },
        "frozen_chronological_result": {
            "donor_concordance": float(frozen["primary"]["donor_concordance"]),
            "strongest_recipient_concordance": float(
                frozen["primary"]["strongest_baseline_concordance"]
            ),
            "donor_advantage": float(frozen["primary"]["concordance_advantage"]),
        },
        "metrics_sha256": sha256(METRICS_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
