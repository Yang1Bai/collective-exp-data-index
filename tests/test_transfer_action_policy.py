import copy
import json
import unittest
from pathlib import Path

from analysis.build_transferability_evidence_cards import build_cards
from analysis.transfer_action_policy import (
    action_from_evidence_card,
    audit_synthesis_route_readiness,
    build_policy_summary,
    decide_bridge,
)


ROOT = Path(__file__).resolve().parents[1]


class TransferActionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = build_cards()

    def test_current_cards_route_only_to_supported_endpoint(self):
        actions = {
            row["recipient"]: action_from_evidence_card(row) for row in self.cards
        }
        self.assertEqual(actions["LiAsF6"]["action"], "transfer_now")
        self.assertEqual(actions["LiAsF6"]["endpoint"], "absolute_prediction")
        self.assertEqual(actions["SolventSeg"]["action"], "transfer_now")
        self.assertEqual(actions["SolventSeg"]["endpoint"], "candidate_ranking")
        self.assertEqual(actions["FINALES"]["action"], "withhold")
        self.assertTrue(
            all(
                row["synthesis_route_selection"] == "not_evaluable"
                for row in actions.values()
            )
        )

    def test_unknown_evidence_decision_is_rejected(self):
        card = {
            "recipient": "unknown",
            "decision": "guess",
            "reason_codes": [],
            "gate_evaluation": {
                "absolute_prediction_supported": False,
                "candidate_ranking_supported": False,
            },
        }
        with self.assertRaisesRegex(ValueError, "inconsistent with its quantitative"):
            action_from_evidence_card(card)

    def test_contradictory_evidence_card_cannot_authorise_transfer(self):
        card = {
            "recipient": "contradictory",
            "decision": "predict",
            "reason_codes": [],
            "gate_evaluation": {
                "absolute_prediction_supported": False,
                "candidate_ranking_supported": False,
            },
        }
        with self.assertRaisesRegex(ValueError, "inconsistent with its quantitative"):
            action_from_evidence_card(card)

    def test_missing_or_non_boolean_card_gates_are_rejected(self):
        card = {"recipient": "invalid", "decision": "withhold", "reason_codes": []}
        with self.assertRaisesRegex(ValueError, "missing gate_evaluation"):
            action_from_evidence_card(card)

        card["gate_evaluation"] = {
            "absolute_prediction_supported": "false",
            "candidate_ranking_supported": 0,
        }
        with self.assertRaisesRegex(ValueError, "gate values must be booleans"):
            action_from_evidence_card(card)

    def test_ambiguous_route_complete_case_can_trigger_bridge(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
            expected_information_value=12.0,
            experiment_cost=4.0,
        )
        self.assertEqual(decision.action, "bridge_experiment")

    def test_missing_routes_require_data_recovery_not_bridge(self):
        decision = decide_bridge(
            route_candidates_complete=False,
            feasible_route_count=0,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=False,
        )
        self.assertEqual(decision.action, "data_recovery")

    def test_no_feasible_route_withholds(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=0,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
        )
        self.assertEqual(decision.action, "withhold")

    def test_falsifier_failure_cannot_be_rescued_by_bridge(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=True,
            bridge_designable=True,
            expected_information_value=12.0,
            experiment_cost=4.0,
        )
        self.assertEqual(decision.action, "withhold")

    def test_supported_interval_transfers_now(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(0.06, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
        )
        self.assertEqual(decision.action, "transfer_now")

    def test_harmful_interval_withholds(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.11, 0.04),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
        )
        self.assertEqual(decision.action, "withhold")

    def test_threshold_equality_is_fail_closed(self):
        common = {
            "route_candidates_complete": True,
            "feasible_route_count": 2,
            "endpoint_threshold": 0.05,
            "falsifier_failed": False,
            "bridge_designable": True,
            "expected_information_value": 12.0,
            "experiment_cost": 4.0,
        }
        lower_equal = decide_bridge(
            **common, endpoint_interval=(0.05, 0.11)
        )
        upper_equal = decide_bridge(
            **common, endpoint_interval=(-0.02, 0.05)
        )
        point_equal = decide_bridge(
            **common, endpoint_interval=(0.05, 0.05)
        )
        self.assertEqual(lower_equal.action, "bridge_experiment")
        self.assertEqual(upper_equal.action, "withhold")
        self.assertEqual(point_equal.action, "withhold")

    def test_ambiguous_but_unresolvable_interval_withholds(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=False,
        )
        self.assertEqual(decision.action, "withhold")

    def test_bridge_is_not_authorised_without_value_of_information(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
        )
        self.assertEqual(decision.action, "withhold")

    def test_bridge_is_not_authorised_when_cost_is_too_high(self):
        decision = decide_bridge(
            route_candidates_complete=True,
            feasible_route_count=2,
            endpoint_interval=(-0.02, 0.11),
            endpoint_threshold=0.05,
            falsifier_failed=False,
            bridge_designable=True,
            expected_information_value=4.0,
            experiment_cost=4.0,
        )
        self.assertEqual(decision.action, "withhold")

    def test_invalid_interval_and_route_count_are_rejected(self):
        common = {
            "route_candidates_complete": True,
            "endpoint_threshold": 0.05,
            "falsifier_failed": False,
            "bridge_designable": True,
        }
        with self.assertRaisesRegex(ValueError, "interval must be ordered"):
            decide_bridge(
                **common,
                feasible_route_count=1,
                endpoint_interval=(0.2, 0.1),
            )
        with self.assertRaisesRegex(ValueError, "must be nonnegative"):
            decide_bridge(
                **common,
                feasible_route_count=-1,
                endpoint_interval=(0.0, 0.1),
            )

    def test_invalid_numeric_and_boolean_inputs_fail_closed(self):
        common = {
            "route_candidates_complete": True,
            "feasible_route_count": 2,
            "endpoint_interval": (-0.02, 0.11),
            "endpoint_threshold": 0.05,
            "falsifier_failed": False,
            "bridge_designable": True,
            "expected_information_value": 12.0,
            "experiment_cost": 4.0,
        }
        for field, value in (
            ("endpoint_interval", (float("nan"), 0.11)),
            ("endpoint_interval", (-0.02, float("inf"))),
            ("endpoint_threshold", float("nan")),
            ("expected_information_value", float("inf")),
            ("expected_information_value", -1.0),
            ("experiment_cost", float("nan")),
            ("experiment_cost", -1.0),
        ):
            case = {**common, field: value}
            with self.subTest(field=field, value=value):
                with self.assertRaises((TypeError, ValueError)):
                    decide_bridge(**case)

        for field, value in (
            ("route_candidates_complete", None),
            ("falsifier_failed", None),
            ("bridge_designable", 1),
            ("feasible_route_count", True),
        ):
            case = {**common, field: value}
            with self.subTest(field=field, value=value):
                with self.assertRaises(TypeError):
                    decide_bridge(**case)

    def test_current_synthesis_direction_cannot_select_a_route(self):
        readiness = json.loads(
            (ROOT / "analysis" / "xrd_to_synthesis_readiness.json").read_text()
        )
        audit = audit_synthesis_route_readiness(readiness)
        self.assertFalse(audit["route_choice_supported"])
        self.assertIsNone(audit["selected_synthesis_route"])
        self.assertEqual(audit["current_action"], "data_recovery")
        self.assertFalse(audit["bridge_experiment_supported_now"])
        statuses = {row["requirement"]: row["status"] for row in audit["checklist"]}
        self.assertEqual(statuses["donor temperature and time fields"], "available")
        self.assertEqual(statuses["complete recipient attempt table"], "missing")

    def test_route_readiness_is_derived_from_explicit_evidence(self):
        readiness = json.loads(
            (ROOT / "analysis" / "xrd_to_synthesis_readiness.json").read_text()
        )
        complete = copy.deepcopy(readiness)
        route_evidence = complete["route_readiness_evidence"]
        for key in (
            "complete_recipient_attempt_table",
            "recipient_failed_and_partial_outcomes",
            "candidate_level_synthesis_route_identifiers",
            "target_checksum_frozen",
            "grouped_split_frozen",
        ):
            route_evidence[key] = True
        route_evidence["comparable_route_alternative_count"] = 2

        audit = audit_synthesis_route_readiness(complete)
        self.assertTrue(audit["route_choice_supported"])
        self.assertEqual(audit["current_action"], "evaluate_route_evidence")

    def test_invalid_route_readiness_evidence_is_rejected(self):
        readiness = json.loads(
            (ROOT / "analysis" / "xrd_to_synthesis_readiness.json").read_text()
        )
        readiness["route_readiness_evidence"][
            "complete_recipient_attempt_table"
        ] = None
        with self.assertRaisesRegex(TypeError, "must be boolean"):
            audit_synthesis_route_readiness(readiness)

    def test_policy_summary_preserves_model_boundary(self):
        readiness = json.loads(
            (ROOT / "analysis" / "xrd_to_synthesis_readiness.json").read_text()
        )
        summary = build_policy_summary(self.cards, readiness)
        self.assertFalse(summary["model_or_training_changes"])
        self.assertEqual(len(summary["transfer_actions"]), 3)
        self.assertIn(
            "missing route metadata",
            summary["bridge_contract"]["never_bridge_to_rescue"],
        )


if __name__ == "__main__":
    unittest.main()
