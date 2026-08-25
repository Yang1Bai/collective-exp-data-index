import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis.submission import make_transfer_action_policy_figures as figures


ROOT = Path(__file__).resolve().parents[1]


class TransferActionFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = json.loads(
            (ROOT / "analysis" / "results" / "transferability_evidence_cards.json").read_text(
                encoding="utf-8"
            )
        )
        cls.policy = json.loads(
            (ROOT / "analysis" / "results" / "transfer_action_policy_summary.json").read_text(
                encoding="utf-8"
            )
        )

    def test_support_notes_are_derived_from_frozen_cards(self):
        notes = figures._figure5_support_notes(self.cards)
        self.assertIn("Full-relation support 60.8%", notes[0])
        self.assertIn("Rank permutation Holm P = 0.00070", notes[1])
        self.assertIn("98 eligible pairs", notes[2])

    def test_figure_source_tables_match_loaded_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            figures, "SOURCE", Path(temp_dir)
        ):
            rows5 = figures._write_figure5_source(self.cards)
            rows6 = figures._write_figure6_source(self.policy)
            self.assertEqual([row["action"] for row in rows5], ["PREDICT", "RANK", "WITHHOLD"])
            li_card = next(
                card for card in self.cards["cards"] if card["recipient"] == "LiAsF6"
            )
            self.assertEqual(
                rows5[0]["estimate"],
                100
                * li_card["absolute_endpoint"][
                    "relative_log_rmse_gain_vs_state_only"
                ],
            )
            self.assertEqual(len(rows6), 8)
            self.assertTrue((Path(temp_dir) / "figure5_transfer_action_map.csv").is_file())
            self.assertTrue((Path(temp_dir) / "figure6_route_bridge_readiness.csv").is_file())


if __name__ == "__main__":
    unittest.main()
