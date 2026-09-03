from __future__ import annotations

import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.numeric_router import (
    FEATURE_NAMES,
    NumericRouterEdge,
    decode_numeric_prediction,
    nested_group_predictions,
    numeric_router_features,
    summarize_predictions,
)
from catalyst_attention.opd_router import RouterState


def _state(value: float) -> RouterState:
    return RouterState(
        task_kind="catalyst_ranking",
        source_sample_count=200 + int(10 * value),
        target_candidate_count=100,
        source_validation_spearman=float(np.clip(value, -1, 1)),
        curve_available=value > 0.4,
        surface_available=value > 0.7,
        condition_observed_fraction=float(np.clip(value, 0, 1)),
        standard_predictive_std=0.2 + 0.1 * abs(value),
        mhar_predictive_std=0.3 + 0.05 * abs(value),
        normalized_expert_disagreement=0.2 + abs(value),
        standard_domain_share=float(np.clip(0.5 + value / 4, 0, 1)),
        composition_support=float(np.clip(0.5 + value / 3, 0, 1)),
    )


def _edge(index: int, suite: str, value: float) -> NumericRouterEdge:
    return NumericRouterEdge(
        example_id=f"{suite}:{index}",
        suite=suite,
        donor_group=f"{suite}:donor-{index}",
        recipient_group=f"{suite}:recipient-{index}",
        state=_state(value),
        realized={
            "standard": float(np.clip(0.5 * value, -1, 1)),
            "mhar": float(np.clip(-0.4 * value + 0.1, -1, 1)),
            "ensemble": float(np.clip(0.1 + 0.2 * abs(value), -1, 1)),
        },
    )


class NumericRouterContractTests(unittest.TestCase):
    def test_features_are_fixed_finite_and_identifier_free(self) -> None:
        features = numeric_router_features(_state(0.7))
        self.assertEqual(features.shape, (len(FEATURE_NAMES),))
        self.assertTrue(np.isfinite(features).all())
        self.assertFalse(
            any("programme" in name or "suite" in name for name in FEATURE_NAMES)
        )

    def test_decoder_thresholds_and_fail_closed(self) -> None:
        abstain = decode_numeric_prediction([-0.4, -0.2, -0.3])
        self.assertEqual(abstain.action, "abstain")
        self.assertEqual(abstain.expert, "mhar")
        rank = decode_numeric_prediction([0.1, 0.2, 0.15])
        self.assertEqual((rank.expert, rank.action), ("mhar", "rank"))
        predict = decode_numeric_prediction([0.7, 0.2, 0.4])
        self.assertEqual((predict.expert, predict.action), ("standard", "predict"))
        invalid = decode_numeric_prediction([math.nan, 0.0, 0.0])
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.action, "abstain")

    def test_edge_loader_rejects_side_channels(self) -> None:
        payload = {
            "example_id": "one",
            "suite": "suite-a",
            "donor_group": "a",
            "recipient_group": "b",
            "state": _state(0.5).__dict__,
            "evaluation": {
                "standard_spearman": 0.2,
                "mhar_spearman": 0.3,
                "ensemble_spearman": 0.4,
            },
            "oracle_expert": "ensemble",
        }
        with self.assertRaisesRegex(ValueError, "schema mismatch"):
            NumericRouterEdge.from_mapping(payload)


class NumericRouterEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        values = (-0.8, -0.3, 0.3, 0.8)
        self.edges = [
            _edge(index, suite, values[(index + suite_index) % len(values)])
            for suite_index, suite in enumerate(("a", "b", "c", "d"))
            for index in range(3)
        ]

    def _predict(self, edges: list[NumericRouterEdge]):
        return nested_group_predictions(
            edges,
            outer_group=lambda edge: edge.suite,
            inner_group=lambda edge: edge.suite,
            alpha_grid=(0.1, 1.0),
        )

    def test_held_out_outcome_change_cannot_change_held_out_prediction(self) -> None:
        original = self._predict(self.edges)
        poisoned = [
            replace(
                edge,
                realized={"standard": -1.0, "mhar": 1.0, "ensemble": -1.0},
            )
            if edge.suite == "d"
            else edge
            for edge in self.edges
        ]
        changed = self._predict(poisoned)
        original_rows = {
            row["example_id"]: row for row in original["rows"] if row["suite"] == "d"
        }
        changed_rows = {
            row["example_id"]: row for row in changed["rows"] if row["suite"] == "d"
        }
        for identifier in original_rows:
            self.assertEqual(
                original_rows[identifier]["predicted_spearman"],
                changed_rows[identifier]["predicted_spearman"],
            )
            self.assertEqual(
                original_rows[identifier]["decision"],
                changed_rows[identifier]["decision"],
            )

    def test_summary_is_deterministic_and_records_gate(self) -> None:
        prediction = self._predict(self.edges)
        first = summarize_predictions(
            prediction, self.edges, bootstrap_seed=7, bootstrap_draws=100
        )
        second = summarize_predictions(
            prediction, self.edges, bootstrap_seed=7, bootstrap_draws=100
        )
        self.assertEqual(first, second)
        self.assertEqual(first["edges"], len(self.edges))
        self.assertIn("passed", first["qualification_gate"])
        self.assertEqual(
            len(first["gain_over_always_standard"]["outer_group_bootstrap_ci90"]),
            2,
        )


if __name__ == "__main__":
    unittest.main()
