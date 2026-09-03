from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))
VALIDATION_PATH = (
    ROOT / "analysis" / "results" / "caltech_ionic_external_policy_validation.json"
)

from analysis.run_caltech_ionic_external_policy import (  # noqa: E402
    AUDIT_PATH,
    CONFIRMATORY_POLICIES,
    DESIGN_PATH,
    IMPLEMENTATION_PATH,
    PRIMARY_COMPARISONS,
    REQUIRED_CANONICAL_AUDIT_SHA256,
    TARGET_PATH,
    file_hash,
    canonical_json_hash,
    gated_predictions,
    initial_indices,
    load_target,
)


class CaltechExternalProtocolTests(unittest.TestCase):
    def test_frozen_hashes_and_eight_contrasts_are_consistent(self):
        design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
        implementation = json.loads(IMPLEMENTATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(file_hash(DESIGN_PATH, "sha256"), implementation["parent_design_sha256"])
        self.assertEqual(design["policies"], CONFIRMATORY_POLICIES)
        self.assertEqual(len(PRIMARY_COMPARISONS), 8)

    def test_target_and_source_quality_gates_pass(self):
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            canonical_json_hash(AUDIT_PATH), REQUIRED_CANONICAL_AUDIT_SHA256
        )
        self.assertEqual(audit["status"], "pass")
        self.assertTrue(audit["all_target_gates_pass"])
        self.assertTrue(audit["all_source_minimums_pass"])
        self.assertEqual(audit["target_metrics"]["unique_canonical_compositions"], 483)
        self.assertEqual(audit["target_metrics"]["candidate_entities"], 144)
        self.assertEqual(audit["target_metrics"]["hard_ood_entities"], 58)

    def test_verified_result_keeps_primary_null_and_method_selection_separate(self):
        validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            validation["status"],
            "verified-primary-policy-null-with-post-result-source-portfolio-selection",
        )
        decisions = validation["global_decisions"]
        self.assertTrue(decisions["all_negative_transfer_weight_guards_pass"])
        self.assertFalse(decisions["composition_novelty_beats_random_in_both_scopes"])
        self.assertFalse(decisions["safe_target_backbone_beats_novelty_in_both_scopes"])
        self.assertFalse(decisions["any_confirmatory_source_increment_passes_all_gates"])
        self.assertTrue(
            decisions["neighbor_gates_have_higher_mean_admission_than_wrong_controls"]
        )
        self.assertTrue(
            decisions[
                "prespecified_static_neighbors_exceed_all_static_references_descriptively"
            ]
        )
        self.assertTrue(
            decisions["post_result_portfolio_recall20_at_least_half_in_both_scopes"]
        )
        self.assertFalse(decisions["new_science_endpoint_tested"])

    @unittest.skipUnless(TARGET_PATH.exists(), "External CC0 target file is not installed")
    def test_initial_sampling_is_exact_and_source_backbone_is_state_matched(self):
        target, x, _ = load_target()
        labelled = initial_indices(target, 0, 30)
        self.assertEqual(len(labelled), 30)
        self.assertGreaterEqual(target.loc[labelled, "group"].nunique(), 5)
        pool = target.index[target["split"] == "candidate"].astype(int).tolist()
        y = target["value"].to_numpy(float)
        source = np.linspace(-1, 1, len(target), dtype=float)
        source_predictions = {"obelix_same_property": source}
        base_target, _, target_gates = gated_predictions(
            policy="safe_target_novelty",
            seed=0,
            step=1,
            target=target,
            x=x,
            y=y,
            labelled=labelled,
            pool=pool,
            source_predictions=source_predictions,
            requested_sources=[],
        )
        base_source, _, source_gates = gated_predictions(
            policy="safe_obelix_residual",
            seed=0,
            step=1,
            target=target,
            x=x,
            y=y,
            labelled=labelled,
            pool=pool,
            source_predictions=source_predictions,
            requested_sources=["obelix_same_property"],
        )
        self.assertTrue(np.array_equal(base_target, base_source))
        for key in (
            "median_relative_rmse_gain",
            "mean_relative_rmse_gain",
            "positive_folds",
            "admitted",
            "weight",
        ):
            self.assertEqual(target_gates[0][key], source_gates[0][key])


if __name__ == "__main__":
    unittest.main()
