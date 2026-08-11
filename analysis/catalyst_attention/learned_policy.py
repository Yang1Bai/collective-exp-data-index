"""Learned and LLM transfer policies, evaluated against the frozen rules.

Three decision-layer rows compared on the same closed edge set:

* ``FrozenThresholdPolicy`` — a-priori rules (baseline, see
  ``policy_transfer.py``);
* ``LearnedTransferPolicy`` — a small gradient-boosted / logistic model
  trained on *historical* edges only, under strict leave-one-pair-out so
  the edge being decided is never in its own training set;
* ``LLMTransferPolicy`` — decisions recorded from an LLM that saw only
  ``TransferEdgeState.as_prompt_dict()`` JSON, stored as a pinned JSON
  artifact with per-edge rationale. Evaluation replays those decisions;
  the artifact hash binds the decisions to the benchmark.

Labels are derived from realized outcomes **for training only**, never
for the edge being decided: an edge is ``apply``-worthy when its realized
transfer Spearman clears the utility bar and ``abstain`` when it is
harmful (negative) — mirroring the manuscript's harm/utility framing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .policy_transfer import (
    Decision,
    FrozenThresholdPolicy,
    PolicyBenchmarkResult,
    TransferEdgeState,
    evaluate_policy,
)

UTILITY_BAR = 0.25  # realized rho above this => the edge was worth applying
HARM_BAR = 0.0  # realized rho below this => harmful transfer


# ---------------------------------------------------------------------------
# Labels (training-time only)
# ---------------------------------------------------------------------------


def edge_label(realized_rho: float) -> Decision:
    if realized_rho < HARM_BAR:
        return "abstain"
    if realized_rho >= UTILITY_BAR:
        return "apply"
    return "rank_only"


# ---------------------------------------------------------------------------
# Feature vector (identical information for learned and LLM policies)
# ---------------------------------------------------------------------------

_FEATURE_NAMES = (
    "source_fit_spearman",
    "coverage",
    "mean_min_distance",
    "log_source_n",
    "log_target_n",
    "feature_richness",
    "same_family",
    "is_contrastive",
)


def state_features(state: TransferEdgeState) -> list[float]:
    return [
        state.source_fit_spearman,
        state.coverage,
        state.mean_min_distance,
        float(np.log10(max(state.source_n, 1))),
        float(np.log10(max(state.target_n, 1))),
        state.feature_richness,
        1.0 if state.donor_family.split("_")[0] == state.recipient_family.split("_")[0] else 0.0,
        1.0 if state.method == "contrastive" else 0.0,
    ]


# ---------------------------------------------------------------------------
# Learned policy with leave-one-pair-out
# ---------------------------------------------------------------------------


@dataclass
class LearnedTransferPolicy:
    """Gradient-boosted stump ensemble over the prompt-visible features.

    ``train_states``/``train_labels`` must never contain the pair being
    decided; the benchmark harness enforces leave-one-pair-out.
    """

    train_states: list[TransferEdgeState]
    train_labels: list[Decision]
    name: str = "learned_gbm_lopo_v1"
    _model: Any = None

    def __post_init__(self) -> None:
        from sklearn.ensemble import HistGradientBoostingClassifier

        X = np.array([state_features(s) for s in self.train_states])
        y = np.array(self.train_labels)
        model = HistGradientBoostingClassifier(
            max_iter=200, max_depth=3, learning_rate=0.08,
            min_samples_leaf=3, random_state=20260810,
        )
        model.fit(X, y)
        object.__setattr__(self, "_model", model)

    def decide(self, state: TransferEdgeState) -> Decision:
        proba = self._model.predict_proba([state_features(state)])[0]
        classes = list(self._model.classes_)
        # Conservative decoding: only apply when apply is the argmax AND
        # its probability clears 0.5; abstain unless at least rank-level
        # confidence exists.
        best = classes[int(np.argmax(proba))]
        if best == "apply" and proba[classes.index("apply")] >= 0.5:
            return "apply"
        if best == "abstain" and proba[classes.index("abstain")] >= 0.5:
            return "abstain"
        return "rank_only"


def learned_policy_lopo(
    states: Sequence[TransferEdgeState],
    realized: dict[tuple[str, str], float],
) -> PolicyBenchmarkResult:
    """Leave-one-pair-out evaluation of the learned policy.

    For each edge, the model is retrained on every *other* pair, so the
    deciding model has never seen any realized outcome from its own pair.
    """
    from .policy_transfer import EdgeOutcome

    result = PolicyBenchmarkResult()
    pairs = sorted({s.pair_name for s in states})
    for pair in pairs:
        train_states = [s for s in states if s.pair_name != pair]
        train_labels = [edge_label(realized[(s.pair_name, s.method)]) for s in train_states]
        policy = LearnedTransferPolicy(train_states, train_labels)
        for state in [s for s in states if s.pair_name == pair]:
            decision = policy.decide(state)
            result.edges.append(
                EdgeOutcome(
                    state=state,
                    decision=decision,
                    target_spearman=float(realized[(state.pair_name, state.method)]),
                    rank_accepted=decision in ("apply", "rank_only"),
                )
            )
    return result


# ---------------------------------------------------------------------------
# LLM policy — replay of pinned decisions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LLMTransferPolicy:
    """Replays decisions recorded by an LLM over prompt-visible states.

    The decisions JSON maps ``pair_name`` -> {``method`` -> decision}.
    Any pair/method missing from the artifact fails closed (KeyError).
    """

    decisions: dict[str, dict[str, Decision]]
    name: str = "llm_policy_v1"

    def decide(self, state: TransferEdgeState) -> Decision:  # pragma: no cover
        raise NotImplementedError("LLM policy is evaluated via evaluate_llm_policy")

    def decision_for(self, state: TransferEdgeState) -> Decision:
        decision = self.decisions[state.pair_name][state.method]
        if decision not in ("apply", "rank_only", "abstain"):
            raise ValueError(f"invalid LLM decision: {decision!r}")
        return decision  # type: ignore[return-value]


def load_llm_policy(path: Path) -> LLMTransferPolicy:
    payload = json.loads(Path(path).read_text())
    return LLMTransferPolicy(decisions=payload["decisions"])


def evaluate_llm_policy(
    policy: LLMTransferPolicy,
    states: Sequence[TransferEdgeState],
    realized: dict[tuple[str, str], float],
) -> PolicyBenchmarkResult:
    from .policy_transfer import EdgeOutcome

    result = PolicyBenchmarkResult()
    for state in states:
        decision = policy.decision_for(state)
        result.edges.append(
            EdgeOutcome(
                state=state,
                decision=decision,
                target_spearman=float(realized[(state.pair_name, state.method)]),
                rank_accepted=decision in ("apply", "rank_only"),
            )
        )
    return result


def export_llm_prompts(states: Sequence[TransferEdgeState], path: Path) -> None:
    """Write the exact prompt-visible state per edge for LLM decision.

    The file deliberately contains no realized outcomes; whoever/whatever
    fills in decisions sees only these fields.
    """
    payload = {
        "instruction": (
            "For each edge decide apply / rank_only / abstain. "
            "apply = expect a useful transferred point prediction or ranking; "
            "rank_only = only an ordinal claim is defensible; "
            "abstain = transfer is likely harmful or unsupported. "
            "Base the decision only on the fields given."
        ),
        "edges": [s.as_prompt_dict() for s in states],
    }
    Path(path).write_text(json.dumps(payload, indent=1))
