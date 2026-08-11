"""Context-conditioned transfer-policy simulation for representation baselines.

The manuscript's comparison rows so far all live in the *representation*
layer: embedding similarity, attention, and contrastive objectives decide
implicitly where transfer happens. This module adds the first
**decision-layer** row: a frozen, outcome-unseen transfer policy observes
only source-side and geometry descriptors of a donor-recipient pair and
decides ``apply / rank_only / abstain`` *before* any target outcome is
consulted. Evaluation then compares the policy's realized target
performance against always-transfer and always-abstain anchors.

Scientific contract
-------------------
* The policy state contains **no target outcome information** — only
  source fit quality, donor-recipient geometry (composition coverage,
  distance), dataset sizes, and method identity. This mirrors the
  falsification-gated borrowing contract: qualify first, then transfer.
* A policy is frozen as a small set of human-interpretable rules with
  thresholds fixed a priori from the repo's accumulated null/positive
  ledger (e.g. "weak source fit + contrastive objective ⇒ harmful").
* The benchmark is exhaustive leave-one-pair-out over all directed
  donor→recipient pairs in the task suite, so every method's decision is
  evaluated on every edge, including edges where abstention is correct.
* Everything is deterministic: fixed seeds, frozen configs, JSON
  artifacts with a manifest hash.

This is the baseline that any future *learned* or *LLM-reasoned* policy
must beat: if a reasoning policy cannot outperform frozen threshold rules,
the reasoning adds no decision value.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

import numpy as np

POLICY_DESIGN_VERSION = "policy-transfer-baseline-v1"

DECISIONS = ("apply", "rank_only", "abstain")
Decision = Literal["apply", "rank_only", "abstain"]


# ---------------------------------------------------------------------------
# Policy state — the only fields a policy (or downstream LLM prompt) may see
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransferEdgeState:
    """Outcome-free description of one directed donor→recipient edge."""

    pair_name: str
    method: str
    source_n: int
    target_n: int
    source_fit_spearman: float
    coverage: float  # fraction of target composition space near the donor
    mean_min_distance: float  # mean over targets of distance to nearest donor
    donor_family: str
    recipient_family: str
    feature_richness: float  # 0 = composition only, 1 = spectra + conditions

    def as_prompt_dict(self) -> dict[str, Any]:
        """Fields admitted to an LLM/agent prompt. No target outcomes."""
        return {
            "pair_name": self.pair_name,
            "method": self.method,
            "source_n": self.source_n,
            "target_n": self.target_n,
            "source_fit_spearman": round(self.source_fit_spearman, 4),
            "coverage": round(self.coverage, 4),
            "mean_min_distance": round(self.mean_min_distance, 4),
            "donor_family": self.donor_family,
            "recipient_family": self.recipient_family,
            "feature_richness": self.feature_richness,
        }


# ---------------------------------------------------------------------------
# Edge geometry — computed from samples, never from outcomes
# ---------------------------------------------------------------------------


def composition_vector(elements: np.ndarray, fractions: np.ndarray) -> np.ndarray:
    """118-dim fractional composition vector, L2-normalised."""
    vec = np.zeros(118, dtype=np.float64)
    for z, f in zip(elements, fractions, strict=True):
        if 1 <= int(z) <= 118:
            vec[int(z) - 1] += float(f)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def edge_geometry(
    source_samples: Sequence[Any],
    target_samples: Sequence[Any],
) -> dict[str, float]:
    """Coverage and distance of a donor-recipient pair.

    coverage: fraction of targets whose nearest donor has cosine distance
        <= 0.25 (chemically close neighbourhood).
    mean_min_distance: mean cosine distance from each target to its
        nearest donor row.
    """
    src = np.stack(
        [composition_vector(s.elements, s.fractions) for s in source_samples]
    )
    tgt = np.stack(
        [composition_vector(t.elements, t.fractions) for t in target_samples]
    )
    # cosine distance = 1 - cos sim; rows are unit norm.
    sims = tgt @ src.T
    dists = 1.0 - sims
    min_d = dists.min(axis=1)
    coverage = float(np.mean(min_d <= 0.25))
    return {"coverage": coverage, "mean_min_distance": float(min_d.mean())}


# ---------------------------------------------------------------------------
# Frozen threshold policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrozenThresholdPolicy:
    """Human-interpretable a-priori rules.

    Thresholds are fixed from the repo's attempt ledger BEFORE seeing the
    benchmark outcomes of this suite:

    * Weak donor fit (source rho < ``source_fit_floor``) means the donor
      relation itself is not established — transferring it transfers noise.
      The ledger shows contrastive objectives amplify this failure
      (steel-family rows), so they abstain earlier.
    * A geometrically uncovered recipient (coverage below
      ``coverage_floor``) cannot be interpolated to; at best a coarse
      ranking signal may cross.
    * Very small donors cannot support attention-based transfer at all
      (repo finding: Transformer needs >= ~400 rows with rich features).
    """

    source_fit_floor: float = 0.5
    source_fit_floor_contrastive: float = 0.6
    coverage_floor: float = 0.35
    rank_only_coverage_floor: float = 0.15
    min_source_n_attention: int = 400

    name: str = "frozen_threshold_v1"

    def decide(self, state: TransferEdgeState) -> Decision:
        floor = (
            self.source_fit_floor_contrastive
            if state.method == "contrastive"
            else self.source_fit_floor
        )
        if state.source_fit_spearman < floor:
            return "abstain"
        if state.source_n < self.min_source_n_attention:
            return "abstain"
        if state.coverage >= self.coverage_floor:
            return "apply"
        if state.coverage >= self.rank_only_coverage_floor:
            return "rank_only"
        return "abstain"


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@dataclass
class EdgeOutcome:
    """Realized, post-decision outcome for one edge (evaluation only)."""

    state: TransferEdgeState
    decision: Decision
    target_spearman: float
    rank_accepted: bool  # decision permits a ranking claim


@dataclass
class PolicyBenchmarkResult:
    edges: list[EdgeOutcome] = field(default_factory=list)

    def realized_scores(self) -> list[float]:
        """Spearman where applied, 0 where abstained (no claim, no harm)."""
        return [
            e.target_spearman if e.decision == "apply" else 0.0 for e in self.edges
        ]

    def harm_count(self) -> int:
        return sum(
            1 for e in self.edges if e.decision == "apply" and e.target_spearman < 0.0
        )

    def missed_positive_count(self) -> int:
        return sum(
            1 for e in self.edges if e.decision == "abstain" and e.target_spearman > 0.3
        )

    def summary(self) -> dict[str, Any]:
        scores = self.realized_scores()
        return {
            "n_edges": len(self.edges),
            "n_apply": sum(1 for e in self.edges if e.decision == "apply"),
            "n_rank_only": sum(1 for e in self.edges if e.decision == "rank_only"),
            "n_abstain": sum(1 for e in self.edges if e.decision == "abstain"),
            "mean_realized_spearman": float(np.mean(scores)) if scores else math.nan,
            "harm_edges": self.harm_count(),
            "missed_positive_edges": self.missed_positive_count(),
        }


def evaluate_policy(
    policy: FrozenThresholdPolicy,
    states: Sequence[TransferEdgeState],
    realized: dict[tuple[str, str], float],
) -> PolicyBenchmarkResult:
    """Apply the frozen policy to every edge; attach realized outcomes.

    ``realized`` maps (pair_name, method) -> measured target Spearman.
    These values are evaluation-only: the policy never sees them.
    """
    result = PolicyBenchmarkResult()
    for state in states:
        decision = policy.decide(state)
        rho = realized.get((state.pair_name, state.method))
        if rho is None:
            raise KeyError(f"missing realized outcome for {state.pair_name}/{state.method}")
        result.edges.append(
            EdgeOutcome(
                state=state,
                decision=decision,
                target_spearman=float(rho),
                rank_accepted=decision in ("apply", "rank_only"),
            )
        )
    return result


def always_transfer_baseline(
    states: Sequence[TransferEdgeState],
    realized: dict[tuple[str, str], float],
) -> PolicyBenchmarkResult:
    result = PolicyBenchmarkResult()
    for state in states:
        result.edges.append(
            EdgeOutcome(
                state=state,
                decision="apply",
                target_spearman=float(realized[(state.pair_name, state.method)]),
                rank_accepted=True,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def result_manifest(result: PolicyBenchmarkResult) -> dict[str, Any]:
    payload = {
        "design": POLICY_DESIGN_VERSION,
        "edges": [
            {
                "pair": e.state.pair_name,
                "method": e.state.method,
                "decision": e.decision,
                "state": e.state.as_prompt_dict(),
                "target_spearman": round(e.target_spearman, 6),
            }
            for e in result.edges
        ],
        "summary": result.summary(),
    }
    blob = json.dumps(payload, sort_keys=True).encode()
    payload["sha256"] = hashlib.sha256(blob).hexdigest()
    return payload
