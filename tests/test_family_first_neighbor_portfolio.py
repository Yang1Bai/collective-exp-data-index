from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"


class FamilyFirstNeighborPortfolioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = [
            RESULTS / "family_first_neighbor_portfolio_summary.json",
            RESULTS / "family_first_neighbor_portfolio_metrics.csv",
            RESULTS / "family_first_neighbor_portfolio_orders.csv",
            RESULTS / "family_first_neighbor_portfolio_null.csv",
            RESULTS / "family_first_neighbor_hypothesis_cards.csv",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise unittest.SkipTest("Run the family-first audit: " + ", ".join(missing))
        cls.summary = json.loads(required[0].read_text(encoding="utf-8"))
        cls.metrics = pd.read_csv(required[1])
        cls.orders = pd.read_csv(required[2])
        cls.null = pd.read_csv(required[3])
        cls.cards = pd.read_csv(required[4])

    def test_design_discloses_outcome_informed_status(self) -> None:
        design = json.loads(
            (ROOT / "analysis" / "family_first_neighbor_portfolio_design.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(design["status"].startswith("outcome-informed"))
        self.assertIn("cannot serve as independent confirmation", design["claim_guard"])
        self.assertIn("breadth-versus-repeat tradeoff", design["sensitivity_endpoints"][-1])

    def test_orders_are_candidate_outcome_invariant_and_complete(self) -> None:
        self.assertTrue(self.summary["candidate_outcome_permutation_invariance"])
        self.assertEqual(len(self.orders), 8 * (144 + 58))
        counts = self.orders.groupby(["scope", "policy"])["candidate_index"].agg(
            ["size", "nunique"]
        )
        self.assertTrue((counts["size"] == counts["nunique"]).all())
        external = counts.loc["external_candidate"]
        hard = counts.loc["hard_ood_40pct"]
        self.assertTrue((external["size"] == 144).all())
        self.assertTrue((hard["size"] == 58).all())

    def test_primary_breadth_result_and_controls(self) -> None:
        primary = self.metrics[
            self.metrics["unit"].eq("provenance_group")
            & self.metrics["group_value_aggregation"].eq("max")
        ].set_index(["scope", "policy"])
        external = primary.loc[
            "external_candidate", "neighbor_family_first_consensus"
        ]
        hard = primary.loc["hard_ood_40pct", "neighbor_family_first_consensus"]
        self.assertEqual((external["auc20"], external["hit_count20"]), (60, 4))
        self.assertEqual((hard["auc20"], hard["hit_count20"]), (39, 2))
        self.assertEqual(
            primary.loc[
                "external_candidate", "wrong_source_family_first_consensus"
            ]["auc20"],
            6,
        )
        self.assertEqual(
            primary.loc[
                "hard_ood_40pct", "wrong_source_family_first_consensus"
            ]["auc20"],
            18,
        )
        null = {row["scope"]: row for row in self.summary["conditional_null"]}
        self.assertLessEqual(null["external_candidate"]["conditional_randomization_p"], 0.002)
        self.assertLessEqual(null["hard_ood_40pct"]["conditional_randomization_p"], 0.003)
        self.assertEqual(len(self.null), 10000)

    def test_entity_repeat_tradeoff_is_not_hidden(self) -> None:
        entity = self.metrics[
            self.metrics["unit"].eq("entity")
            & self.metrics["policy"].isin(
                ["neighbor_entity_consensus", "neighbor_family_first_consensus"]
            )
        ].set_index(["scope", "policy"])
        self.assertEqual(
            entity.loc[
                "external_candidate", "neighbor_entity_consensus"
            ]["hit_count20"],
            5,
        )
        self.assertEqual(
            entity.loc[
                "external_candidate", "neighbor_family_first_consensus"
            ]["hit_count20"],
            2,
        )
        self.assertEqual(
            entity.loc[
                "hard_ood_40pct", "neighbor_family_first_consensus"
            ]["hit_count20"],
            1,
        )

    def test_hypothesis_cards_are_retrospective_and_falsifiable(self) -> None:
        self.assertEqual(len(self.cards), 4)
        self.assertTrue(self.cards["evidence_status"].str.contains("retrospective").all())
        self.assertTrue(self.cards["prospective_falsifier"].str.len().gt(80).all())
        self.assertTrue(self.cards["mechanistic_follow_up"].str.contains("activation").all())

    def test_figure_bundle_exists(self) -> None:
        for filename in [
            "family_first_neighbor_portfolio.svg",
            "family_first_neighbor_portfolio.pdf",
            "family_first_neighbor_portfolio.png",
            "family_first_neighbor_portfolio_600dpi.tif",
        ]:
            path = ROOT / "analysis" / "figures" / filename
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 1000)

    def test_next_validation_protocol_is_outcome_unseen(self) -> None:
        protocol = json.loads(
            (
                ROOT
                / "analysis"
                / "cca_family_first_outcome_unseen_protocol.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("no target selected", protocol["status"])
        self.assertIn(
            "target outcome values", protocol["target_selection"]["forbidden_before_freeze"]
        )
        self.assertIn(
            "verify candidate-outcome permutation invariance",
            protocol["audit_sentinels"],
        )


if __name__ == "__main__":
    unittest.main()
