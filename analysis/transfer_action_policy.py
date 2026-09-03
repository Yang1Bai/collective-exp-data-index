"""Fail-closed action policy for validated transfer evidence.

The policy is deliberately separate from every predictor.  It consumes frozen
evidence cards and decides whether the supported object should be used now,
withheld, or held for a bridge experiment.  Literal synthesis-route selection
is allowed only when route-resolved, candidate-available metadata and comparable
recipient outcomes exist; otherwise the policy reports ``not_evaluable``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from numbers import Real
from typing import Any, Literal


Action = Literal[
    "transfer_now",
    "bridge_experiment",
    "withhold",
    "data_recovery",
]


@dataclass(frozen=True)
class BridgeDecision:
    action: Action
    reason: str
    endpoint_interval: tuple[float, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def action_from_evidence_card(card: dict[str, Any]) -> dict[str, Any]:
    """Map a frozen evidence-card endpoint to its allowed present action."""

    decision = card["decision"]
    gates = card.get("gate_evaluation")
    if not isinstance(gates, dict):
        raise ValueError("evidence card is missing gate_evaluation")
    absolute_supported = gates.get("absolute_prediction_supported")
    ranking_supported = gates.get("candidate_ranking_supported")
    if not isinstance(absolute_supported, bool) or not isinstance(
        ranking_supported, bool
    ):
        raise ValueError("evidence-card gate values must be booleans")
    expected_decision = (
        "predict"
        if absolute_supported
        else "rank"
        if ranking_supported
        else "withhold"
    )
    if decision != expected_decision:
        raise ValueError(
            "evidence-card decision is inconsistent with its quantitative gates: "
            f"expected {expected_decision!r}, got {decision!r}"
        )
    if decision == "predict":
        return {
            "recipient": card["recipient"],
            "action": "transfer_now",
            "endpoint": "absolute_prediction",
            "synthesis_route_selection": "not_evaluable",
            "bridge_status": "not_required_for_validated_endpoint",
            "reason_codes": list(card["reason_codes"]),
        }
    if decision == "rank":
        return {
            "recipient": card["recipient"],
            "action": "transfer_now",
            "endpoint": "candidate_ranking",
            "synthesis_route_selection": "not_evaluable",
            "bridge_status": "not_required_for_validated_endpoint",
            "reason_codes": list(card["reason_codes"]),
        }
    if decision == "withhold":
        return {
            "recipient": card["recipient"],
            "action": "withhold",
            "endpoint": "none",
            "synthesis_route_selection": "not_evaluable",
            "bridge_status": "not_justified_without_route_resolved_hypothesis",
            "reason_codes": list(card["reason_codes"]),
        }
    raise ValueError(f"unsupported evidence-card decision: {decision!r}")


def _finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def decide_bridge(
    *,
    route_candidates_complete: bool,
    feasible_route_count: int,
    endpoint_interval: tuple[float, float],
    endpoint_threshold: float,
    falsifier_failed: bool,
    bridge_designable: bool,
    expected_information_value: float | None = None,
    experiment_cost: float | None = None,
) -> BridgeDecision:
    """Return a bounded transfer/bridge/withhold decision.

    The bridge action is available only for an ambiguous endpoint whose route
    candidates are explicit, feasible and experimentally distinguishable.  A
    bridge is never used to rescue a falsifier failure or missing route data.
    """

    if not isinstance(route_candidates_complete, bool):
        raise TypeError("route_candidates_complete must be boolean")
    if isinstance(feasible_route_count, bool) or not isinstance(
        feasible_route_count, int
    ):
        raise TypeError("feasible_route_count must be an integer")
    if not isinstance(falsifier_failed, bool):
        raise TypeError("falsifier_failed must be boolean")
    if not isinstance(bridge_designable, bool):
        raise TypeError("bridge_designable must be boolean")

    low, high = endpoint_interval
    low = _finite_number("endpoint_interval low", low)
    high = _finite_number("endpoint_interval high", high)
    endpoint_threshold = _finite_number("endpoint_threshold", endpoint_threshold)
    if low > high:
        raise ValueError("endpoint interval must be ordered")
    if feasible_route_count < 0:
        raise ValueError("feasible_route_count must be nonnegative")
    if expected_information_value is not None:
        expected_information_value = _finite_number(
            "expected_information_value", expected_information_value
        )
        if expected_information_value < 0:
            raise ValueError("expected_information_value must be nonnegative")
    if experiment_cost is not None:
        experiment_cost = _finite_number("experiment_cost", experiment_cost)
        if experiment_cost < 0:
            raise ValueError("experiment_cost must be nonnegative")
    if not route_candidates_complete:
        return BridgeDecision(
            "data_recovery",
            "route candidates or candidate-available process metadata are incomplete",
            endpoint_interval,
        )
    if feasible_route_count == 0:
        return BridgeDecision(
            "withhold", "no route passes feasibility and safety gates", endpoint_interval
        )
    if falsifier_failed:
        return BridgeDecision(
            "withhold", "matched falsifier evidence does not support transfer", endpoint_interval
        )
    if low > endpoint_threshold:
        return BridgeDecision(
            "transfer_now", "endpoint lower bound clears the frozen threshold", endpoint_interval
        )
    if high <= endpoint_threshold:
        return BridgeDecision(
            "withhold",
            "endpoint upper bound does not exceed the frozen threshold",
            endpoint_interval,
        )
    if feasible_route_count < 2:
        return BridgeDecision(
            "withhold",
            "an ambiguous endpoint needs at least two feasible route alternatives for a paired bridge contrast",
            endpoint_interval,
        )
    if not bridge_designable:
        return BridgeDecision(
            "withhold",
            "endpoint is ambiguous but no paired route contrast can resolve it",
            endpoint_interval,
        )
    if expected_information_value is None or experiment_cost is None:
        return BridgeDecision(
            "withhold",
            "endpoint is ambiguous, but expected information value and experiment cost must be recorded before a bridge can be authorised",
            endpoint_interval,
        )
    if expected_information_value > experiment_cost:
        return BridgeDecision(
            "bridge_experiment",
            "expected information value exceeds experiment cost",
            endpoint_interval,
        )
    return BridgeDecision(
        "withhold",
        "bridge experiment cost is not justified by expected information value",
        endpoint_interval,
    )


def audit_synthesis_route_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    """Audit whether the frozen solid-synthesis direction can select a route."""

    donor = readiness["primary_candidate"]["donor"]
    recipient = readiness["primary_candidate"]["recipient"]
    donor_fields = set(donor["candidate_available_fields"])
    required_recipient = set(readiness["required_recipient_fields"])
    route_evidence = readiness["route_readiness_evidence"]
    route_alternative_count = route_evidence["comparable_route_alternative_count"]
    if isinstance(route_alternative_count, bool) or not isinstance(
        route_alternative_count, int
    ):
        raise TypeError("comparable_route_alternative_count must be an integer")
    if route_alternative_count < 0:
        raise ValueError("comparable_route_alternative_count must be nonnegative")
    for key in (
        "complete_recipient_attempt_table",
        "recipient_failed_and_partial_outcomes",
        "candidate_level_synthesis_route_identifiers",
        "target_checksum_frozen",
        "grouped_split_frozen",
    ):
        if not isinstance(route_evidence.get(key), bool):
            raise TypeError(f"route_readiness_evidence.{key} must be boolean")

    checklist = [
        {
            "requirement": "donor precursor and stoichiometry fields",
            "status": "available"
            if {"precursor_formulae", "target_stoichiometry"} <= donor_fields
            else "missing",
        },
        {
            "requirement": "donor temperature and time fields",
            "status": "available"
            if {"heating_temperature", "heating_time"} <= donor_fields
            else "missing",
        },
        {
            "requirement": "donor negative and partial outcomes",
            "status": "available"
            if {"unreacted", "partially_reacted"} <= set(donor["outcome_classes"])
            else "missing",
        },
        {
            "requirement": "complete recipient attempt table",
            "status": "available"
            if route_evidence["complete_recipient_attempt_table"]
            else "missing",
        },
        {
            "requirement": "recipient failed and partial outcomes",
            "status": (
                "available"
                if route_evidence["recipient_failed_and_partial_outcomes"]
                else "missing"
            )
            if "failed_and_partial_outcomes" in required_recipient
            else "not_required",
        },
        {
            "requirement": "candidate-level synthesis route identifiers",
            "status": "available"
            if route_evidence["candidate_level_synthesis_route_identifiers"]
            else "missing",
        },
        {
            "requirement": "two or more comparable route alternatives",
            "status": "available" if route_alternative_count >= 2 else "missing",
        },
        {
            "requirement": "frozen target checksum and grouped split",
            "status": "available"
            if route_evidence["target_checksum_frozen"]
            and route_evidence["grouped_split_frozen"]
            else "missing",
        },
    ]

    route_choice_supported = all(
        item["status"] in {"available", "not_required"}
        for item in checklist
    )
    return {
        "programme": f"{donor['name']} -> {recipient['name']}",
        "source_status": readiness["status"],
        "record_counts": {
            "donor_reactions": donor["reactions"],
            "recipient_reported_attempts": recipient["reported_attempts"],
        },
        "route_choice_supported": route_choice_supported,
        "selected_synthesis_route": None,
        "bridge_experiment_supported_now": False,
        "current_action": (
            "evaluate_route_evidence" if route_choice_supported else "data_recovery"
        ),
        "blocking_issue": recipient["blocking_issue"],
        "next_required_evidence": [
            "verify the complete recipient attempt table including failures",
            "encode candidate-level route identifiers and process parameters",
            "freeze route alternatives, target checksum and grouped evaluation",
            "then apply the ambiguity and value-of-information bridge gate",
        ],
        "checklist": checklist,
    }


def build_policy_summary(
    cards: list[dict[str, Any]], readiness: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "model_or_training_changes": False,
        "transfer_actions": [action_from_evidence_card(card) for card in cards],
        "synthesis_route_readiness": audit_synthesis_route_readiness(readiness),
        "bridge_contract": {
            "trigger": (
                "route candidates are complete and feasible, the endpoint confidence "
                "interval crosses its frozen threshold, matched falsifiers pass, a "
                "paired route contrast is designable, and expected information value "
                "exceeds experiment cost"
            ),
            "never_bridge_to_rescue": [
                "missing route metadata",
                "no feasible route",
                "matched falsifier failure",
                "endpoint interval wholly below threshold",
            ],
        },
    }
