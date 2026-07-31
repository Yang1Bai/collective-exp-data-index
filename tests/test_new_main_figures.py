from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"


class NewMainFigureTests(unittest.TestCase):
    def test_export_bundles_exist(self) -> None:
        for stem in (
            "data_foundation_scope",
            "specgen_derivative_oer_transfer",
            "neighbor_map_exploration",
            "battery_continuous_borrowing",
        ):
            for suffix in (".svg", ".pdf", ".png", ".tiff"):
                path = FIGURES / f"{stem}{suffix}"
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 1000, path)

    def test_data_foundation_denominators_and_portfolio(self) -> None:
        inventory = pd.read_csv(RESULTS / "figure_data_foundation_inventory.csv")
        self.assertEqual(len(inventory), 21)
        self.assertEqual(inventory["resource"].nunique(), 21)
        self.assertEqual(
            inventory["analysis_layer"].value_counts().to_dict(),
            {"normalized": 13, "external": 7, "analysis-only": 1},
        )
        self.assertEqual(int(inventory["donor"].sum()), 16)
        self.assertEqual(int(inventory["recipient"].sum()), 17)
        self.assertEqual(
            int((inventory["donor"] & inventory["recipient"]).sum()), 13
        )
        self.assertEqual(
            int((inventory["donor"] | inventory["recipient"]).sum()), 20
        )
        self.assertEqual(int(inventory["artifact_gate"].sum()), 1)

        lake = pd.read_csv(RESULTS / "figure_data_foundation_lake.csv")
        self.assertEqual(len(lake), 13)
        self.assertEqual(int(lake["measurements"].sum()), 96184)
        self.assertEqual(
            set(lake["dataset"]),
            set(
                inventory.loc[
                    inventory["analysis_layer"] == "normalized", "resource"
                ]
            ),
        )

        scope = pd.read_csv(RESULTS / "figure_data_foundation_scope.csv")
        cohort = scope.set_index("layer").loc["analysed cohort"]
        self.assertEqual(int(cohort["primary_count"]), 21)
        active = scope.set_index("layer").loc["transfer-active cohort"]
        self.assertEqual(int(active["primary_count"]), 20)
        directed = scope.set_index("layer").loc["directed benchmark"]
        self.assertEqual(int(directed["primary_count"]), 97)
        self.assertIn("20 tasks", directed["secondary_label"])
        programmes = scope.set_index("layer").loc["programme synthesis"]
        self.assertEqual(int(programmes["primary_count"]), 13)

        portfolio = pd.read_csv(
            RESULTS / "figure_data_foundation_portfolio.csv", keep_default_na=False
        )
        self.assertEqual(portfolio.loc[portfolio["role_defining"], "program"].nunique(), 5)
        self.assertIn("passed", set(portfolio["status"]))
        self.assertIn("null", set(portfolio["status"]))

    def test_neighbor_map_preserves_fit_exploration_boundary(self) -> None:
        adaptive = pd.read_csv(RESULTS / "figure_neighbor_map_panel_c.csv")
        self.assertEqual(len(adaptive), 6)
        self.assertFalse(adaptive["passes_all_frozen_gates"].astype(bool).any())

        family = pd.read_csv(RESULTS / "figure_neighbor_map_panel_e.csv")
        index = family.set_index(["scope", "policy"])
        self.assertEqual(
            index.loc[
                ("external_candidate", "neighbor_family_first_consensus"),
                "auc20",
            ],
            60,
        )
        self.assertEqual(
            index.loc[
                ("hard_ood_40pct", "neighbor_family_first_consensus"),
                "auc20",
            ],
            39,
        )
        self.assertLess(
            index.loc[
                ("external_candidate", "neighbor_family_first_consensus"),
                "conditional_randomization_p",
            ],
            0.01,
        )

    def test_battery_figure_values_and_boundary(self) -> None:
        forest = pd.read_csv(RESULTS / "figure_battery_panel_b.csv")
        self.assertEqual(len(forest), 4)
        self.assertTrue((forest["ci_lo_percent"] > 0).all())
        self.assertTrue((forest["holm_adjusted_p"] < 0.05).all())

        condition = pd.read_csv(RESULTS / "figure_battery_panel_c.csv")
        self.assertEqual(len(condition), 22)
        self.assertEqual(condition["adjacency_wins_target"].astype(bool).sum(), 17)

        gate = pd.read_csv(RESULTS / "figure_battery_panel_d.csv").set_index("stratum")
        self.assertEqual(int(gate.loc["all groups", "groups_admitted"]), 4)
        self.assertEqual(int(gate.loc["all groups", "groups_total"]), 22)
        self.assertEqual(int(gate.loc["cycle", "groups_admitted"]), 0)

        contract = (ROOT / "analysis" / "BATTERY_FIGURE_CONTRACT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("non-evaluable", contract)
        self.assertIn("not a confirmatory result", contract)


if __name__ == "__main__":
    unittest.main()
