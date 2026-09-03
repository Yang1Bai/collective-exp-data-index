"""Verify completeness and arithmetic of the formal OOD-deficit diagnostic."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from run_ood_knowledge_deficit_audit import DESIGN_PATH, INPUT_META_PATH, sha256_file


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"


def main() -> None:
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    input_meta = json.loads(INPUT_META_PATH.read_text(encoding="utf-8"))
    metrics = pd.read_csv(RESULTS / "ood_knowledge_deficit_metrics.csv")
    contrasts = pd.read_csv(RESULTS / "ood_knowledge_deficit_contrasts.csv")
    diagnostics = pd.read_csv(RESULTS / "ood_knowledge_deficit_diagnostics.csv")
    summary = json.loads(
        (RESULTS / "ood_knowledge_deficit_summary.json").read_text(encoding="utf-8")
    )

    repeats = int(design["repeats"])
    budgets = set(design["label_budgets"])
    learners = set(design["learners"])
    sources = set(design["sources"])
    scopes = {"all", "hard_ood_fixed", "ood_q1", "ood_q2", "ood_q3", "ood_q4"}

    if summary["status"] != "post-outcome-diagnostic-complete":
        raise AssertionError("Formal completion status is absent")
    if summary["design_sha256"] != sha256_file(DESIGN_PATH):
        raise AssertionError("Design hash mismatch")
    if summary["input_sha256"] != input_meta["input_sha256"]:
        raise AssertionError("Input hash mismatch")
    if set(metrics["repeat"]) != set(range(repeats)):
        raise AssertionError("Metric repeat coverage is incomplete")
    if set(metrics["requested_budget"]) != budgets:
        raise AssertionError("Budget coverage changed")
    if set(metrics["learner"]) != learners:
        raise AssertionError("Learner coverage changed")
    if set(metrics["source"]) != sources:
        raise AssertionError("Source coverage changed")
    if set(metrics["scope"]) != scopes:
        raise AssertionError("Scope coverage changed")

    expected_tasks = repeats * len(budgets) * len(learners)
    if len(diagnostics) != expected_tasks:
        raise AssertionError("Diagnostic task count is incomplete")
    if len(metrics) != expected_tasks * len(sources) * len(scopes):
        raise AssertionError("Metric row count is incomplete")
    if len(contrasts) != expected_tasks * (len(sources) - 1) * len(scopes):
        raise AssertionError("Contrast row count is incomplete")

    metric_keys = [
        "repeat",
        "requested_budget",
        "budget",
        "learner",
        "source",
        "scope",
    ]
    if metrics.duplicated(metric_keys).any():
        raise AssertionError("Duplicate metric keys")
    contrast_keys = metric_keys
    if contrasts.duplicated(contrast_keys).any():
        raise AssertionError("Duplicate contrast keys")

    all_rows = metrics[metrics["scope"] == "all"]
    if not (all_rows["n"] == 110).all():
        raise AssertionError("Official test scope is not 110 entities")
    hard_rows = metrics[metrics["scope"] == "hard_ood_fixed"]
    if not (hard_rows["n"] == 44).all():
        raise AssertionError("Fixed hard-OOD scope is not 44 entities")
    quartile_counts = (
        metrics[metrics["scope"].str.startswith("ood_q")]
        .groupby(metric_keys[:-1], as_index=False)["n"]
        .sum()
    )
    if not (quartile_counts["n"] == 110).all():
        raise AssertionError("OOD quartiles do not partition the official test set")

    recomputed = (contrasts["baseline_rmse"] - contrasts["rmse"]) / contrasts[
        "baseline_rmse"
    ]
    if not np.allclose(
        recomputed,
        contrasts["relative_rmse_reduction"],
        rtol=1e-12,
        atol=1e-12,
    ):
        raise AssertionError("Relative RMSE contrast arithmetic changed")

    primary = summary["primary"]
    for endpoint in design["primary_problem_endpoints"] + design[
        "primary_borrowing_endpoints"
    ]:
        if not endpoint:
            raise AssertionError("Blank primary endpoint in design")
    if primary["target_only_high_minus_low_ood_rmse"]["n"] != repeats:
        raise AssertionError("Primary OOD-gap repeat count changed")
    if primary["thermoelectric_high_ood_relative_rmse_reduction"]["n"] != repeats:
        raise AssertionError("Primary neighbor repeat count changed")

    verification = {
        "status": "verified-complete",
        "design_sha256": summary["design_sha256"],
        "input_sha256": summary["input_sha256"],
        "metric_rows": len(metrics),
        "contrast_rows": len(contrasts),
        "diagnostic_rows": len(diagnostics),
        "claim_guard": design["claim_guard"],
    }
    (RESULTS / "ood_knowledge_deficit_VERIFIED.json").write_text(
        json.dumps(verification, indent=2), encoding="utf-8"
    )
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()

