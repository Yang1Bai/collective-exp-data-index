from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from run_knowledge_map import TaskData  # noqa: E402
from run_multi_target_ood_borrowing import (  # noqa: E402
    assign_group_quartiles,
    classify_edge,
    hierarchical_gain_bootstrap,
    sign_flip_pvalue,
)


class MultiTargetOODDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = json.loads(
            (
                ROOT / "analysis" / "multi_target_ood_borrowing_design.json"
            ).read_text(encoding="utf-8")
        )
        cls.parent = json.loads(
            (ROOT / "analysis" / "knowledge_map_design.json").read_text(
                encoding="utf-8"
            )
        )

    def test_portfolio_and_controls_are_frozen(self) -> None:
        included = self.design["eligibility"]["included_targets"]
        self.assertEqual(len(included), 8)
        self.assertEqual(set(included), set(self.design["targets"]))
        self.assertEqual(
            sum(len(self.parent["targets"][target]["sources"]) for target in included),
            40,
        )
        for target in included:
            inherited = {
                edge["task"] for edge in self.parent["targets"][target]["sources"]
            }
            self.assertIn(self.design["targets"][target]["primary_source"], inherited)
            self.assertIn(self.design["targets"][target]["wrong_source"], inherited)

    def test_claim_guard_discloses_post_outcome_boundary(self) -> None:
        self.assertTrue(self.design["status"].startswith("frozen-post-outcome"))
        guard = self.design["claim_guard"]
        self.assertIn("cannot retroactively create prospective validation", guard)
        self.assertIn("null and harmful edges", guard)

    def test_group_quartiles_are_outcome_invariant(self) -> None:
        frame = pd.DataFrame(
            {
                "material_key": [f"material-{index}" for index in range(20)],
                "group": [f"group-{index}" for index in range(20)],
                "value": np.arange(20, dtype=float),
            }
        )
        x = np.column_stack(
            [np.arange(20, dtype=float), np.arange(20, dtype=float) ** 2]
        )
        task = TaskData(
            "synthetic",
            {"kind": "formula", "label": "Synthetic", "domain": "test"},
            frame.copy(),
            x,
        )
        first = assign_group_quartiles(
            "synthetic", task, np.arange(4), np.arange(4, 20)
        )
        task.frame["value"] = task.frame["value"].sample(
            frac=1.0, random_state=3
        ).to_numpy()
        second = assign_group_quartiles(
            "synthetic", task, np.arange(4), np.arange(4, 20)
        )
        self.assertEqual(first["scope"].to_list(), second["scope"].to_list())
        self.assertEqual(first.groupby("scope")["group"].nunique().to_dict(), {
            "q1": 4,
            "q2": 4,
            "q3": 4,
            "q4": 4,
        })
        self.assertTrue((first.groupby("group")["scope"].nunique() == 1).all())

    def test_hierarchical_bootstrap_detects_ood_specific_gain(self) -> None:
        rows = []
        for repeat in range(10):
            for scope, augmented_error in (("q1", 0.98), ("q4", 0.75)):
                for group in range(5):
                    rows.append(
                        {
                            "repeat": repeat,
                            "scope": scope,
                            "group": f"{scope}-{group}",
                            "base_sse": 1.0,
                            "aug_sse": augmented_error**2,
                            "n": 1,
                        }
                    )
        intervals = hierarchical_gain_bootstrap(
            pd.DataFrame(rows), n_boot=200, seed=7
        )
        self.assertGreater(intervals["q4"][0], 0.20)
        self.assertGreater(intervals["specific"][0], 0.20)
        self.assertLess(intervals["q1"][1], 0.03)

    def test_sign_flip_and_full_gate(self) -> None:
        p_value = sign_flip_pvalue(np.full(12, 0.1), permutations=9999, seed=11)
        self.assertLess(p_value, 0.01)
        gate = self.design["edge_gate"]
        row = pd.Series(
            {
                "is_designated_primary": True,
                "gain_ood_mean": 0.10,
                "gain_ood_ci_lo": 0.04,
                "gain_ood_ci_hi": 0.16,
                "aug_ood_r2_mean": 0.20,
                "positive_ood_repeat_fraction": 0.90,
                "gain_specific_ci_lo": 0.01,
                "primary_minus_wrong_ci_lo": 0.02,
                "primary_minus_shuffled_ci_lo": 0.02,
                "positive_ood_learners": 2,
                "holm_p": 0.01,
                "post_exclusion_overlap": 0,
            }
        )
        self.assertEqual(
            classify_edge(row, gate),
            "ood-repair-gate-passed",
        )


class MultiTargetOODResultTests(unittest.TestCase):
    def test_formal_result_is_independently_verified_when_present(self) -> None:
        path = ROOT / "analysis" / "results" / "multi_target_ood_VERIFIED.json"
        if not path.exists():
            self.skipTest("Run and verify the formal multi-target OOD benchmark")
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "verified-complete")
        self.assertEqual(result["mode"], "formal")
        self.assertEqual(result["targets"], 8)
        self.assertEqual(result["real_edges"], 40)
        self.assertEqual(result["shuffled_controls"], 8)


if __name__ == "__main__":
    unittest.main()
