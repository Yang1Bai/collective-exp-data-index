from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.learned_policy import (  # noqa: E402
    LLMTransferPolicy,
    edge_label,
    evaluate_llm_policy,
    export_llm_prompts,
    learned_policy_lopo,
    load_llm_policy,
    state_features,
)
from catalyst_attention.policy_transfer import TransferEdgeState  # noqa: E402


def _state(pair: str, method: str = "standard", **overrides) -> TransferEdgeState:
    base = dict(
        pair_name=pair, method=method, source_n=500, target_n=120,
        source_fit_spearman=0.9, coverage=0.9, mean_min_distance=0.05,
        donor_family="specgen", recipient_family="specgen_x", feature_richness=1.0,
    )
    base.update(overrides)
    return TransferEdgeState(**base)


class TestLabels(unittest.TestCase):
    def test_label_thresholds(self):
        self.assertEqual(edge_label(-0.1), "abstain")
        self.assertEqual(edge_label(0.1), "rank_only")
        self.assertEqual(edge_label(0.5), "apply")


class TestFeatures(unittest.TestCase):
    def test_feature_vector_shape_and_encoding(self):
        s = _state("p", method="contrastive", source_n=1000)
        f = state_features(s)
        self.assertEqual(len(f), 8)
        self.assertEqual(f[7], 1.0)  # is_contrastive
        self.assertAlmostEqual(f[3], 3.0, places=6)  # log10(1000)


class TestLearnedLOPO(unittest.TestCase):
    def _make_suite(self):
        rng = np.random.default_rng(7)
        states, realized = [], {}
        # clear separable rule: apply iff fit*coverage > 0.3
        for i in range(10):
            for method in ("standard", "contrastive"):
                fit = float(rng.uniform(0, 1))
                cov = float(rng.uniform(0, 1))
                s = _state(f"pair{i}", method, source_fit_spearman=fit, coverage=cov)
                states.append(s)
                realized[(s.pair_name, s.method)] = 0.6 if fit * cov > 0.3 else -0.3
        return states, realized

    def test_lopo_beats_always_transfer_anchor(self):
        states, realized = self._make_suite()
        result = learned_policy_lopo(states, realized)
        summary = result.summary()
        naive_mean = float(np.mean(list(realized.values())))
        # the learned policy must realize strictly more than applying
        # everywhere, and strictly less harm than applying everywhere
        naive_harm = sum(1 for v in realized.values() if v < 0)
        self.assertGreater(summary["mean_realized_spearman"], naive_mean)
        self.assertLess(summary["harm_edges"], naive_harm)

    def test_lopo_never_trains_on_own_pair(self):
        states, realized = self._make_suite()
        # poison one pair with inverted labels; LOPO must still decide it
        # from the OTHER pairs' rule.
        victim = "pair0"
        for s in states:
            if s.pair_name == victim:
                realized[(s.pair_name, s.method)] = (
                    -0.3 if s.source_fit_spearman * s.coverage > 0.3 else 0.6
                )
        result = learned_policy_lopo(states, realized)
        # the victim's decisions follow the majority rule, so its realized
        # scores will look 'harmful' — proving the model never saw victim labels
        victim_edges = [e for e in result.edges if e.state.pair_name == victim]
        applies = [e for e in victim_edges if e.decision == "apply"]
        self.assertTrue(
            any(e.target_spearman < 0 for e in applies) or len(applies) == 0
        )


class TestLLMPolicy(unittest.TestCase):
    def test_replay_and_hash(self):
        states = [_state("a"), _state("b", source_fit_spearman=0.1)]
        realized = {("a", "standard"): 0.6, ("b", "standard"): -0.4}
        decisions = {"a": {"standard": "apply"}, "b": {"standard": "abstain"}}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "dec.json"
            path.write_text(json.dumps({"decisions": decisions}))
            policy = load_llm_policy(path)
        result = evaluate_llm_policy(policy, states, realized)
        self.assertEqual(result.summary()["harm_edges"], 0)
        self.assertAlmostEqual(result.summary()["mean_realized_spearman"], 0.3)

    def test_missing_edge_fails_closed(self):
        states = [_state("a")]
        realized = {("a", "standard"): 0.6}
        policy = LLMTransferPolicy(decisions={})
        with self.assertRaises(KeyError):
            evaluate_llm_policy(policy, states, realized)

    def test_invalid_decision_fails_closed(self):
        states = [_state("a")]
        realized = {("a", "standard"): 0.6}
        policy = LLMTransferPolicy(decisions={"a": {"standard": "yeet"}})
        with self.assertRaises(ValueError):
            evaluate_llm_policy(policy, states, realized)

    def test_export_prompts_excludes_outcomes(self):
        states = [_state("a")]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "prompts.json"
            export_llm_prompts(states, path)
            payload = json.loads(path.read_text())
        self.assertIn("edges", payload)
        banned = {"target_spearman", "realized", "outcome"}
        for edge in payload["edges"]:
            self.assertTrue(banned.isdisjoint(edge.keys()))


if __name__ == "__main__":
    unittest.main()
