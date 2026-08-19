"""Small leakage-safe numeric router for Standard/MHAR/ensemble selection.

The router consumes only :class:`RouterState` fields.  Realized target
Spearman values are training labels inside each outer training fold and are
never features.  All edges in an outer suite or donor group are excluded from
both model fitting and inner alpha selection before that group is predicted.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .opd_router import (
    RouterDecision,
    RouterState,
    deterministic_target_free_decision,
)

EXPERTS = ("standard", "mhar", "ensemble")
FEATURE_NAMES = (
    "log10_source_sample_count",
    "log10_target_candidate_count",
    "source_validation_spearman",
    "curve_available",
    "surface_available",
    "condition_observed_fraction",
    "log_standard_to_mhar_predictive_std_ratio",
    "normalized_expert_disagreement",
    "standard_domain_share",
    "composition_support",
)


@dataclass(frozen=True)
class NumericRouterEdge:
    example_id: str
    suite: str
    donor_group: str
    recipient_group: str
    state: RouterState
    realized: Mapping[str, float]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> NumericRouterEdge:
        allowed = {
            "example_id",
            "suite",
            "donor_group",
            "recipient_group",
            "state",
            "evaluation",
        }
        if set(payload) != allowed:
            raise ValueError("numeric-router edge schema mismatch")
        realized = {
            expert: float(payload["evaluation"][f"{expert}_spearman"])
            for expert in EXPERTS
        }
        if any(not math.isfinite(value) for value in realized.values()):
            raise ValueError("realized expert outcomes must be finite")
        return cls(
            example_id=str(payload["example_id"]),
            suite=str(payload["suite"]),
            donor_group=str(payload["donor_group"]),
            recipient_group=str(payload["recipient_group"]),
            state=RouterState.from_mapping(payload["state"]),
            realized=realized,
        )


def numeric_router_features(state: RouterState) -> np.ndarray:
    """Return the fixed scale-aware target-free feature vector."""

    uncertainty_ratio = math.log(
        max(state.standard_predictive_std, 1e-8) / max(state.mhar_predictive_std, 1e-8)
    )
    values = np.asarray(
        [
            math.log10(state.source_sample_count),
            math.log10(state.target_candidate_count),
            state.source_validation_spearman,
            float(state.curve_available),
            float(state.surface_available),
            state.condition_observed_fraction,
            float(np.clip(uncertainty_ratio, -5.0, 5.0)),
            state.normalized_expert_disagreement,
            state.standard_domain_share,
            state.composition_support,
        ],
        dtype=np.float64,
    )
    if not np.isfinite(values).all():
        raise ValueError("numeric-router features must be finite")
    return values


def decode_numeric_prediction(predicted: Sequence[float]) -> RouterDecision:
    """Decode predicted expert utilities with conservative action thresholds."""

    values = np.asarray(predicted, dtype=np.float64)
    if values.shape != (len(EXPERTS),) or not np.isfinite(values).all():
        return RouterDecision.fail_closed("invalid_output")
    values = np.clip(values, -1.0, 1.0)
    best_index = int(np.argmax(values))
    best_value = float(values[best_index])
    expert = EXPERTS[best_index]
    if best_value < 0.0:
        return RouterDecision(
            expert=expert,
            action="abstain",
            confidence=0.0,
            reason_codes=("out_of_support",),
        )
    action = "rank" if best_value < 0.25 else "predict"
    order = np.sort(values)
    margin = float(order[-1] - order[-2])
    confidence = float(np.clip(0.5 + margin / 2.0, 0.0, 1.0))
    reason = (
        "standard_closer"
        if expert == "standard"
        else "mhar_closer"
        if expert == "mhar"
        else "experts_agree"
    )
    return RouterDecision(
        expert=expert,
        action=action,
        confidence=confidence,
        reason_codes=(reason,),
    )


def _matrix(edges: Sequence[NumericRouterEdge]) -> tuple[np.ndarray, np.ndarray]:
    x = np.stack([numeric_router_features(edge.state) for edge in edges])
    y = np.asarray(
        [[edge.realized[expert] for expert in EXPERTS] for edge in edges],
        dtype=np.float64,
    )
    return x, y


def _fit_ridge(edges: Sequence[NumericRouterEdge], alpha: float):
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    x, y = _matrix(edges)
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(x, y)
    return model


def _select_alpha(
    edges: Sequence[NumericRouterEdge],
    group: Callable[[NumericRouterEdge], str],
    alpha_grid: Sequence[float],
) -> tuple[float, dict[str, float]]:
    groups = sorted({group(edge) for edge in edges})
    if len(groups) < 2:
        raise ValueError("inner numeric-router CV requires at least two groups")
    scores: dict[str, float] = {}
    for alpha in alpha_grid:
        if alpha <= 0:
            raise ValueError("ridge alpha must be positive")
        squared_errors = []
        for held_out in groups:
            train = [edge for edge in edges if group(edge) != held_out]
            validate = [edge for edge in edges if group(edge) == held_out]
            if not train or not validate:
                raise RuntimeError("invalid inner group split")
            model = _fit_ridge(train, float(alpha))
            x_validate, y_validate = _matrix(validate)
            prediction = np.clip(model.predict(x_validate), -1.0, 1.0)
            squared_errors.extend(np.square(prediction - y_validate).ravel())
        scores[str(float(alpha))] = float(np.mean(squared_errors))
    selected = min(
        (float(alpha) for alpha in alpha_grid),
        key=lambda alpha: (scores[str(alpha)], -alpha),
    )
    return selected, scores


def nested_group_predictions(
    edges: Sequence[NumericRouterEdge],
    *,
    outer_group: Callable[[NumericRouterEdge], str],
    inner_group: Callable[[NumericRouterEdge], str],
    alpha_grid: Sequence[float] = (0.1, 1.0, 10.0, 100.0),
) -> dict[str, Any]:
    """Return strict outer-group predictions and fold audit metadata."""

    if len(edges) < 3:
        raise ValueError("numeric-router evaluation requires at least three edges")
    identifiers = [edge.example_id for edge in edges]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("numeric-router example identifiers must be unique")
    outer_groups = sorted({outer_group(edge) for edge in edges})
    if len(outer_groups) < 3:
        raise ValueError("outer numeric-router CV requires at least three groups")

    rows = []
    folds = []
    for held_out in outer_groups:
        train = [edge for edge in edges if outer_group(edge) != held_out]
        test = [edge for edge in edges if outer_group(edge) == held_out]
        train_ids = {edge.example_id for edge in train}
        test_ids = {edge.example_id for edge in test}
        if train_ids & test_ids:
            raise RuntimeError("outer numeric-router split leaked an example")
        alpha, inner_scores = _select_alpha(train, inner_group, alpha_grid)
        model = _fit_ridge(train, alpha)
        x_test, _ = _matrix(test)
        predictions = np.clip(model.predict(x_test), -1.0, 1.0)
        pipeline_ridge = model.named_steps["ridge"]
        folds.append(
            {
                "held_out_group": held_out,
                "train_edges": len(train),
                "test_edges": len(test),
                "selected_alpha": alpha,
                "inner_mse_by_alpha": inner_scores,
                "standardized_coefficients": {
                    expert: {
                        name: float(value)
                        for name, value in zip(
                            FEATURE_NAMES,
                            pipeline_ridge.coef_[expert_index],
                            strict=True,
                        )
                    }
                    for expert_index, expert in enumerate(EXPERTS)
                },
            }
        )
        for edge, predicted in zip(test, predictions, strict=True):
            decision = decode_numeric_prediction(predicted)
            routed = (
                0.0
                if decision.action == "abstain"
                else float(edge.realized[decision.expert])
            )
            oracle_expert = max(EXPERTS, key=lambda expert: edge.realized[expert])
            rows.append(
                {
                    "example_id": edge.example_id,
                    "suite": edge.suite,
                    "donor_group": edge.donor_group,
                    "recipient_group": edge.recipient_group,
                    "outer_group": held_out,
                    "state": asdict(edge.state),
                    "predicted_spearman": {
                        expert: float(predicted[index])
                        for index, expert in enumerate(EXPERTS)
                    },
                    "decision": asdict(decision),
                    "realized": dict(edge.realized),
                    "routed_spearman": routed,
                    "oracle_expert": oracle_expert,
                }
            )
    rows.sort(key=lambda row: row["example_id"])
    return {"rows": rows, "folds": folds}


def _deterministic_routed(edge: NumericRouterEdge) -> float:
    decision = deterministic_target_free_decision(edge.state)
    if decision.action == "abstain":
        return 0.0
    return float(edge.realized[decision.expert])


def summarize_predictions(
    prediction: Mapping[str, Any],
    edges: Sequence[NumericRouterEdge],
    *,
    bootstrap_seed: int = 20260813,
    bootstrap_draws: int = 2000,
) -> dict[str, Any]:
    """Summarize routed outcomes and paired outer-group bootstrap uncertainty."""

    if bootstrap_draws <= 0:
        raise ValueError("bootstrap_draws must be positive")
    by_id = {edge.example_id: edge for edge in edges}
    rows = list(prediction["rows"])
    routed = np.asarray([row["routed_spearman"] for row in rows], dtype=float)
    standard = np.asarray([row["realized"]["standard"] for row in rows], dtype=float)
    mhar = np.asarray([row["realized"]["mhar"] for row in rows], dtype=float)
    ensemble = np.asarray([row["realized"]["ensemble"] for row in rows], dtype=float)
    deterministic = np.asarray(
        [_deterministic_routed(by_id[row["example_id"]]) for row in rows],
        dtype=float,
    )
    oracle = np.maximum.reduce([standard, mhar, ensemble])
    useful = oracle >= 0.25
    useful_retained = routed >= 0.25
    non_abstain = np.asarray(
        [row["decision"]["action"] != "abstain" for row in rows], dtype=bool
    )

    groups = sorted({row["outer_group"] for row in rows})
    indices_by_group = {
        group: np.asarray(
            [index for index, row in enumerate(rows) if row["outer_group"] == group]
        )
        for group in groups
    }
    rng = np.random.default_rng(bootstrap_seed)
    gains = []
    for _ in range(bootstrap_draws):
        sampled_groups = rng.choice(groups, size=len(groups), replace=True)
        sampled = np.concatenate([indices_by_group[group] for group in sampled_groups])
        gains.append(float(np.median(routed[sampled]) - np.median(standard[sampled])))
    gain_ci90 = [float(np.quantile(gains, 0.05)), float(np.quantile(gains, 0.95))]

    def baseline(values: np.ndarray) -> dict[str, float]:
        return {
            "median_spearman": float(np.median(values)),
            "mean_spearman": float(np.mean(values)),
            "harmful_transfer_rate": float(np.mean(values < 0.0)),
        }

    expert_action_counts: dict[str, int] = {}
    for row in rows:
        key = f"{row['decision']['expert']}:{row['decision']['action']}"
        expert_action_counts[key] = expert_action_counts.get(key, 0) + 1

    summary = {
        "edges": len(rows),
        "outer_groups": len(groups),
        "numeric_router": {
            **baseline(routed),
            "non_abstain_fraction": float(np.mean(non_abstain)),
            "useful_edge_retention": (
                float(np.mean(useful_retained[useful])) if useful.any() else 0.0
            ),
            "oracle_expert_agreement": float(
                np.mean(
                    [
                        row["decision"]["expert"] == row["oracle_expert"]
                        for row in rows
                        if row["decision"]["action"] != "abstain"
                    ]
                )
            )
            if non_abstain.any()
            else 0.0,
            "expert_action_counts": dict(sorted(expert_action_counts.items())),
        },
        "baselines": {
            "always_standard": baseline(standard),
            "always_mhar": baseline(mhar),
            "always_ensemble": baseline(ensemble),
            "deterministic_target_free_router": baseline(deterministic),
            "oracle_upper_bound": baseline(oracle),
        },
        "gain_over_always_standard": {
            "median": float(np.median(routed) - np.median(standard)),
            "outer_group_bootstrap_ci90": gain_ci90,
            "draws": bootstrap_draws,
            "seed": bootstrap_seed,
        },
    }
    gate = {
        "median_gain_at_least_0_02": (
            summary["gain_over_always_standard"]["median"] >= 0.02
        ),
        "bootstrap_lower_bound_above_0": gain_ci90[0] > 0.0,
        "harm_not_above_standard": (
            summary["numeric_router"]["harmful_transfer_rate"]
            <= summary["baselines"]["always_standard"]["harmful_transfer_rate"]
        ),
        "useful_edge_retention_at_least_0_5": (
            summary["numeric_router"]["useful_edge_retention"] >= 0.5
        ),
        "non_abstain_fraction_at_least_0_5": (
            summary["numeric_router"]["non_abstain_fraction"] >= 0.5
        ),
    }
    gate["passed"] = all(gate.values())
    summary["qualification_gate"] = gate
    return summary
