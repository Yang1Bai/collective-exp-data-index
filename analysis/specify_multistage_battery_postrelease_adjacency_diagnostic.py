"""Record the explicitly outcome-guided adjacency diagnostic before computing it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "analysis" / "results" / "multistage_battery_stage2_coverage_sensitivity"
ANALYSIS = DIR / "analysis"
SUMMARY = ANALYSIS / "POSTRELEASE_SENSITIVITY_SUMMARY.json"
PREDICTIONS = ANALYSIS / "stage2_outer_predictions.csv"
GROUP_ERRORS = ANALYSIS / "condition_group_errors.csv"
APPLICABILITY = DIR / "postrelease_applicability_plan.csv"
RUNNER = ROOT / "analysis" / "analyze_multistage_battery_postrelease_adjacency.py"
OUTPUT = DIR / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SPECIFICATION.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["status"] != "verified-complete-postrelease-coverage-sensitivity":
        raise AssertionError("Base sensitivity must be complete")
    specification = {
        "status": "specified-outcome-guided-postrelease-diagnostic",
        "timing": "specified after inspecting the complete 22-group sensitivity summary",
        "method_selection_was_outcome_guided": True,
        "candidate_policy": "adjacency_only: target features plus the continuous Stage 1 degradation prediction",
        "rationale": "The base sensitivity showed that the hard-gated CCA-v2 policy abstained on most groups, while the simpler adjacency feature had positive point estimates in both aging strata.",
        "comparisons": [
            "adjacency_only minus target_only",
            "adjacency_only minus wrong_property",
            "adjacency_only minus shuffled_source",
            "adjacency_only minus random_features",
        ],
        "effect": "Within each aging stratum, one minus mean adjacency condition RMSE divided by mean comparator condition RMSE; average the two strata equally.",
        "inference": "10000 condition-cluster bootstraps and 9999 paired condition-group sign flips; Holm correction over the four named diagnostic comparisons.",
        "additional_diagnostics": [
            "absolute held-out R2 by stratum",
            "condition-group win counts",
            "highest source-distance quartile",
            "group-level map joined only to outcome-free applicability quantities",
            "exact prediction comparison with the globally rescaled source feature",
        ],
        "summary_sha256": sha256(SUMMARY),
        "predictions_sha256": sha256(PREDICTIONS),
        "group_errors_sha256": sha256(GROUP_ERRORS),
        "applicability_sha256": sha256(APPLICABILITY),
        "analysis_runner_sha256": sha256(RUNNER),
        "claim_guard": "All estimates and adjusted p-values are post hoc. They may nominate a simpler borrowing policy for a new independent outcome-unseen test but cannot establish the present target as a confirmatory success.",
        "errors": [],
    }
    OUTPUT.write_text(json.dumps(specification, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(specification, indent=2))


if __name__ == "__main__":
    main()
