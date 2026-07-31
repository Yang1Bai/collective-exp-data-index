"""Independently verify the frozen leave-one-program CCA gate benchmark.

The verifier reconstructs the edge panel, outer predictions, policy decisions,
cluster-level summaries, and primary contrasts from the frozen inputs.  It does
not modify the frozen result files.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import run_cca_leave_one_program_gate as run


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
VERIFIED_OUT = RESULTS / "cca_leave_one_program_VERIFIED.json"


def assert_equivalent(actual: pd.DataFrame, expected: pd.DataFrame, name: str) -> None:
    """Compare saved and reconstructed frames after stable column alignment."""
    actual = actual.copy()
    expected = expected.copy()
    if list(actual.columns) != list(expected.columns):
        raise AssertionError(f"Column mismatch in {name}")
    for column in expected.columns:
        if pd.api.types.is_object_dtype(expected[column]) or pd.api.types.is_string_dtype(
            expected[column]
        ):
            # The runner deliberately serializes some unavailable metadata as
            # the literal string "nan"; read_csv interprets it as missing.
            actual[column] = actual[column].fillna("nan").astype(str)
            expected[column] = expected[column].fillna("nan").astype(str)
    try:
        assert_frame_equal(
            actual.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-10,
            atol=1e-12,
        )
    except AssertionError as error:
        raise AssertionError(f"Reconstructed {name} does not match saved output: {error}") from error


def main() -> None:
    design = json.loads(run.DESIGN_PATH.read_text(encoding="utf-8"))
    summary = json.loads(run.SUMMARY_OUT.read_text(encoding="utf-8"))

    if run.sha256(run.DESIGN_PATH) != summary["design_sha256"]:
        raise AssertionError("Design hash differs from the completed summary")
    for entry in design["inputs"]:
        path = ROOT / entry["path"]
        observed = run.sha256(path)
        if observed.lower() != entry["sha256"].lower():
            raise AssertionError(f"Frozen input hash mismatch: {entry['path']}")
        if observed != summary["input_sha256"][entry["path"]]:
            raise AssertionError(f"Summary input hash mismatch: {entry['path']}")

    output_paths = [run.EDGE_OUT, run.PRED_OUT, run.POLICY_OUT, run.CONTRAST_OUT]
    for path in output_paths:
        key = str(path.relative_to(ROOT)).replace("\\", "/")
        if run.sha256(path) != summary["output_sha256"][key]:
            raise AssertionError(f"Completed output hash mismatch: {key}")

    edges = pd.DataFrame(run.base_edge_panel() + run.outcome_unseen_edges()).sort_values(
        ["programme", "target_task", "source"]
    )
    predictions = run.leave_one_program_predictions(edges)
    decisions = run.policy_decisions(predictions)
    policy_summary, contrasts = run.summarize_policies(decisions)

    saved_edges = pd.read_csv(run.EDGE_OUT)
    saved_predictions = pd.read_csv(run.PRED_OUT)
    saved_policy = pd.read_csv(run.POLICY_OUT)
    saved_contrasts = pd.read_csv(run.CONTRAST_OUT)
    assert_equivalent(saved_edges, edges, "edge panel")
    assert_equivalent(saved_predictions, predictions, "LOPO predictions")
    assert_equivalent(saved_policy, policy_summary, "policy summary")
    assert_equivalent(saved_contrasts, contrasts, "primary contrasts")

    if not (predictions["programme"] == predictions["held_out_programme"]).all():
        raise AssertionError("At least one edge was not predicted in its held-out programme")
    if set(edges["programme"]) != set(design["independent_program_clusters"]):
        raise AssertionError("Observed programme clusters differ from the frozen design")
    for programme, tasks in design["independent_program_clusters"].items():
        observed_tasks = set(edges.loc[edges["programme"] == programme, "target_task"])
        if observed_tasks != set(tasks):
            raise AssertionError(f"Task grouping mismatch for programme {programme}")

    cca = policy_summary.loc[policy_summary["policy"] == "cca_meta"].iloc[0]
    saved_cca = summary["cca_meta"]
    for key in [
        "mean_programme_utility",
        "bootstrap_ci_lo",
        "bootstrap_ci_hi",
        "programme_coverage",
        "task_coverage",
        "admitted_clear_harm_rate",
        "clear_benefit_retention_rate",
    ]:
        if not np.isclose(float(cca[key]), float(saved_cca[key]), rtol=1e-10, atol=1e-12):
            raise AssertionError(f"CCA summary mismatch: {key}")

    coverage_pass = bool(
        cca["programme_coverage"]
        >= design["nontriviality_guard"]["minimum_programme_coverage"]
    )
    primary_pass = bool(
        coverage_pass
        and (contrasts["mean_utility_difference"] > 0).all()
        and (contrasts["bootstrap_ci_lo"] > 0).all()
        and (contrasts["holm_p"] < 0.05).all()
    )
    if coverage_pass != summary["coverage_guard_pass"]:
        raise AssertionError("Coverage decision mismatch")
    if primary_pass != summary["primary_policy_superiority_pass"]:
        raise AssertionError("Primary superiority decision mismatch")

    cca_decisions = decisions.loc[decisions["policy"] == "cca_meta"]
    verification = {
        "status": "verified-complete",
        "verification_mode": "independent reconstruction from frozen inputs",
        "claim_guard": design["claim_guard"],
        "design_sha256": run.sha256(run.DESIGN_PATH),
        "summary_sha256": run.sha256(run.SUMMARY_OUT),
        "edge_rows": int(len(edges)),
        "target_tasks": int(edges["target_task"].nunique()),
        "programme_clusters": int(edges["programme"].nunique()),
        "lopo_assignment_verified": True,
        "programme_grouping_verified": True,
        "saved_outputs_reconstructed": True,
        "cca_admitted_tasks": int(cca_decisions["admitted"].sum()),
        "cca_clear_harms": int(cca_decisions["clear_harm"].sum()),
        "cca_clear_benefits_retained": int(cca_decisions["clear_benefit"].sum()),
        "coverage_guard_pass": coverage_pass,
        "primary_policy_superiority_pass": primary_pass,
        "decision": summary["decision"],
    }
    VERIFIED_OUT.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
