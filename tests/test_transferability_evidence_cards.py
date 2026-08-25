import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis import build_transferability_evidence_cards as evidence


class TransferabilityEvidenceCardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = evidence.build_cards()
        cls.by_recipient = {card["recipient"]: card for card in cls.cards}

    def test_endpoint_routes_are_evidence_specific(self):
        self.assertEqual(self.by_recipient["LiAsF6"]["decision"], "predict")
        self.assertEqual(self.by_recipient["SolventSeg"]["decision"], "rank")
        self.assertEqual(self.by_recipient["FINALES"]["decision"], "withhold")

    def test_decision_selector_uses_highest_supported_endpoint(self):
        self.assertEqual(
            evidence.choose_evidence_decision(
                absolute_prediction_supported=True,
                candidate_ranking_supported=True,
            ),
            "predict",
        )
        self.assertEqual(
            evidence.choose_evidence_decision(
                absolute_prediction_supported=False,
                candidate_ranking_supported=True,
            ),
            "rank",
        )
        self.assertEqual(
            evidence.choose_evidence_decision(
                absolute_prediction_supported=False,
                candidate_ranking_supported=False,
            ),
            "withhold",
        )

    def test_liasf6_predict_route_has_support_and_specificity(self):
        card = self.by_recipient["LiAsF6"]
        support = card["data_support"]
        endpoint = card["absolute_endpoint"]
        self.assertEqual(support["exact_salt_identity_overlap_fraction"], 0.0)
        self.assertEqual(support["temperature_inside_source_range_fraction"], 1.0)
        self.assertEqual(support["concentration_inside_source_range_fraction"], 1.0)
        self.assertGreater(
            endpoint["relative_log_rmse_gain_vs_state_only_ci95"]["low"], 0
        )
        self.assertGreater(
            endpoint["relative_log_rmse_gain_vs_chemistry_permuted_ci95"]["low"],
            0,
        )

    def test_solventseg_routes_to_rank_when_scale_fails(self):
        card = self.by_recipient["SolventSeg"]
        self.assertLess(
            card["absolute_endpoint"]["relative_log_rmse_gain_vs_state_only"], 0
        )
        self.assertGreater(
            card["rank_endpoint"]["source_minus_recipient_spearman_ci95"]["low"],
            0,
        )
        self.assertLessEqual(
            card["rank_endpoint"]["holm_adjusted_permutation_p"], 0.05
        )

    def test_finales_withholds_when_rank_evidence_fails(self):
        endpoint = self.by_recipient["FINALES"]["rank_endpoint"]
        self.assertLess(endpoint["donor_minus_recipient_concordance"], 0)
        self.assertLess(
            endpoint["donor_minus_recipient_concordance_ci95"]["low"], 0
        )
        self.assertGreater(
            endpoint["donor_minus_recipient_concordance_ci95"]["high"], 0
        )
        self.assertGreater(endpoint["permutation_p"], 0.05)
        self.assertGreater(
            endpoint["donor_normalized_regret"],
            endpoint["recipient_normalized_regret"],
        )

    def test_output_bundle_is_machine_readable(self):
        original_root = evidence.ROOT
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results = root / "analysis" / "results"
            results.mkdir(parents=True)
            with patch.object(evidence, "ROOT", root), patch.object(
                evidence, "RESULTS", results
            ):
                json_path, csv_path, report_path = evidence.write_outputs(self.cards)
            payload = json.loads(json_path.read_text())
            with csv_path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(payload["schema_version"], 1)
            self.assertFalse(payload["model_or_training_changes"])
            self.assertEqual(len(rows), 3)
            self.assertIn("LiAsF6", report_path.read_text())
        self.assertEqual(evidence.ROOT, original_root)


if __name__ == "__main__":
    unittest.main()
