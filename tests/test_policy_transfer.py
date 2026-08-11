from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.policy_transfer import (  # noqa: E402
    FrozenThresholdPolicy,
    TransferEdgeState,
    always_transfer_baseline,
    composition_vector,
    edge_geometry,
    evaluate_policy,
    result_manifest,
)


def _state(**overrides) -> TransferEdgeState:
    base = dict(
        pair_name="donor→recipient",
        method="standard",
        source_n=462,
        target_n=126,
        source_fit_spearman=0.9,
        coverage=0.8,
        mean_min_distance=0.1,
        donor_family="specgen",
        recipient_family="specgen_A",
        feature_richness=1.0,
    )
    base.update(overrides)
    return TransferEdgeState(**base)


class _FakeSample:
    def __init__(self, elements, fractions):
        self.elements = np.asarray(elements, dtype=np.int64)
        self.fractions = np.asarray(fractions, dtype=np.float32)


class TestPolicyState(unittest.TestCase):
    def test_prompt_dict_excludes_outcome_fields(self):
        state = _state()
        prompt = state.as_prompt_dict()
        banned = {"target_spearman", "target", "outcome", "realized", "rho"}
        self.assertTrue(banned.isdisjoint(prompt.keys()))
        self.assertIn("coverage", prompt)
        self.assertIn("source_fit_spearman", prompt)


class TestGeometry(unittest.TestCase):
    def test_identical_composition_has_zero_distance(self):
        a = [_FakeSample([26, 27], [0.5, 0.5])]
        b = [_FakeSample([26, 27], [0.5, 0.5])]
        geo = edge_geometry(a, b)
        self.assertAlmostEqual(geo["mean_min_distance"], 0.0, places=6)
        self.assertAlmostEqual(geo["coverage"], 1.0, places=6)

    def test_disjoint_elements_are_uncovered(self):
        a = [_FakeSample([26], [1.0])]  # Fe only
        b = [_FakeSample([79], [1.0])]  # Au only
        geo = edge_geometry(a, b)
        self.assertAlmostEqual(geo["coverage"], 0.0, places=6)
        self.assertGreater(geo["mean_min_distance"], 0.9)

    def test_composition_vector_is_unit_norm(self):
        v = composition_vector(np.array([26, 27]), np.array([0.3, 0.7]))
        self.assertAlmostEqual(float(np.linalg.norm(v)), 1.0, places=6)
        self.assertEqual(len(v), 118)


class TestFrozenPolicy(unittest.TestCase):
    def test_weak_source_fit_abstains(self):
        policy = FrozenThresholdPolicy()
        self.assertEqual(
            policy.decide(_state(source_fit_spearman=0.1)), "abstain"
        )

    def test_contrastive_abstains_earlier_than_standard(self):
        policy = FrozenThresholdPolicy()
        # Between the two floors: standard applies, contrastive abstains.
        std = policy.decide(_state(method="standard", source_fit_spearman=0.55))
        con = policy.decide(_state(method="contrastive", source_fit_spearman=0.55))
        self.assertEqual(std, "apply")
        self.assertEqual(con, "abstain")

    def test_uncovered_recipient_rank_only_or_abstain(self):
        policy = FrozenThresholdPolicy()
        self.assertEqual(
            policy.decide(_state(coverage=0.2)), "rank_only"
        )
        self.assertEqual(
            policy.decide(_state(coverage=0.05)), "abstain"
        )

    def test_small_donor_abstains_for_attention(self):
        policy = FrozenThresholdPolicy()
        self.assertEqual(
            policy.decide(_state(source_n=150, coverage=0.9)), "abstain"
        )


class TestEvaluation(unittest.TestCase):
    def test_abstention_scores_zero_not_negative(self):
        states = [
            _state(pair_name="bad", source_fit_spearman=0.1),
            _state(pair_name="good", source_fit_spearman=0.9),
        ]
        realized = {("bad", "standard"): -0.45, ("good", "standard"): 0.76}
        policy = FrozenThresholdPolicy()
        result = evaluate_policy(policy, states, realized)
        scores = result.realized_scores()
        self.assertEqual(scores[0], 0.0)  # abstained harm avoided
        self.assertAlmostEqual(scores[1], 0.76)
        self.assertEqual(result.harm_count(), 0)
        self.assertEqual(result.summary()["n_abstain"], 1)

    def test_always_transfer_eats_the_harm(self):
        states = [_state(pair_name="bad", source_fit_spearman=0.1)]
        realized = {("bad", "standard"): -0.45}
        naive = always_transfer_baseline(states, realized)
        self.assertEqual(naive.harm_count(), 1)
        self.assertAlmostEqual(naive.realized_scores()[0], -0.45)

    def test_missing_realized_outcome_fails_closed(self):
        states = [_state()]
        with self.assertRaises(KeyError):
            evaluate_policy(FrozenThresholdPolicy(), states, {})

    def test_manifest_is_hash_stable(self):
        states = [_state()]
        realized = {("donor→recipient", "standard"): 0.5}
        result = evaluate_policy(FrozenThresholdPolicy(), states, realized)
        m1 = result_manifest(result)
        m2 = result_manifest(result)
        self.assertEqual(m1["sha256"], m2["sha256"])
        self.assertIn("summary", m1)


if __name__ == "__main__":
    unittest.main()
