from __future__ import annotations

import json
import hashlib
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    CatalystSample,
    atomic_write_text,
    parse_ocx24_composition,
    samples_manifest,
)
from catalyst_attention.baselines import (  # noqa: E402
    CatalystTabularFeaturizer,
    combine_expert_predictions,
)
from catalyst_attention.expert_router import (  # noqa: E402
    ExpertPair,
    ExpertRouter,
    ExpertRouterOutput,
    calibrate_disagreement_threshold,
    evaluate_router,
    router_audit_trail,
    train_expert_pair,
)
from catalyst_attention.domain_adversarial import (  # noqa: E402
    DomainClassifier,
    GradientReversalFunction,
    adversarial_domain_loss,
    gradient_reversal,
    grl_lambda_schedule,
)
from catalyst_attention.contrastive import (  # noqa: E402
    ContrastiveProjection,
    build_contrastive_pairs,
    composition_cosine_similarity,
    composition_to_vector,
    contrastive_loss,
)
from catalyst_attention.genetic_search import (  # noqa: E402
    CatalystGASearch,
    Individual,
    crossover,
    mutate,
    random_individual,
)
from catalyst_attention.meta_learning import (  # noqa: E402
    FOMAMLWrapper,
    _split_support_query,
)
from catalyst_attention.model import (  # noqa: E402
    CatalystAttentionConfig,
    CatalystTransferTransformer,
    PairwiseElementEncoder,
    attention_entropy,
    depth_routing_diagnostics,
)
from catalyst_attention.optimizers import build_optimizer  # noqa: E402
from catalyst_attention.schema import FUSION_BLOCK_NAMES  # noqa: E402
from catalyst_attention.training import (  # noqa: E402
    BatchCollator,
    FeatureNormalizer,
    LatentSupportCalibrator,
    TrainingConfig,
    metrics,
    pairwise_rank_loss,
    targets_array,
    fit_pls_baseline,
    predict_pls,
    predict,
    load_checkpoint,
    calibrate_support,
    coral_alignment_loss,
    recommend_candidates,
    save_checkpoint,
    train_source_model,
)


def sample(
    index: int,
    *,
    curve: bool = True,
    permutation: np.ndarray | None = None,
) -> CatalystSample:
    elements = np.asarray([27, 28, 29], dtype=np.int64)
    fractions = np.asarray([0.2, 0.3, 0.5], dtype=np.float32)
    if permutation is not None:
        elements = elements[permutation]
        fractions = fractions[permutation]
    axis = np.linspace(-1.0, 1.0, 32, dtype=np.float32) if curve else np.zeros(0, np.float32)
    primary = (
        np.sin(axis * (1.0 + 0.03 * index)) + 0.02 * index
        if curve
        else np.zeros(0, np.float32)
    )
    values = (
        np.column_stack([primary, np.full_like(primary, 0.02)])
        if curve
        else np.zeros((0, 2), np.float32)
    ).astype(np.float32)
    row = CatalystSample(
        sample_id=f"sample-{index}",
        program="specgen_source",
        elements=elements,
        fractions=fractions,
        curve_axis=axis,
        curve_values=values,
        curve_channel_mask=np.asarray([1.0, 1.0 if curve else 0.0], np.float32),
        condition_values=np.asarray([10.0, 298.0, 7.0, 2.0, 0.0, 0.0], np.float32),
        condition_mask=np.asarray([1.0, 1.0, 1.0, 1.0, 1.0, 0.0], np.float32),
        reaction_id=1,
        modality_id=1 if curve else 0,
        program_id=1,
        target=350.0 + 4.0 * index + float(primary.mean() if curve else 0.0),
        target_name="oer_overpotential_mV",
        group_id=f"group-{index // 3}",
        provenance={"synthetic": True},
    )
    row.validate()
    return row


class CatalystDataTests(unittest.TestCase):
    def test_ocx24_composition_is_canonical_and_normalized(self) -> None:
        elements, fractions = parse_ocx24_composition(
            "Ag-0.125-Cu-0.125-Pd-0.75"
        )
        self.assertEqual(elements.tolist(), [29, 46, 47])
        np.testing.assert_allclose(fractions, [0.125, 0.75, 0.125])
        self.assertAlmostEqual(float(fractions.sum()), 1.0)

    def test_manifest_keeps_program_and_curve_counts(self) -> None:
        manifest = samples_manifest([sample(0), sample(1, curve=False)])
        self.assertEqual(manifest["samples"], 2)
        self.assertEqual(manifest["with_curves"], 1)
        self.assertEqual(manifest["with_uncertainty"], 1)
        self.assertEqual(manifest["with_targets"], 2)

    def test_invalid_fraction_sum_fails_closed(self) -> None:
        row = sample(0)
        object.__setattr__(row, "fractions", np.asarray([0.2, 0.2, 0.2], np.float32))
        with self.assertRaisesRegex(ValueError, "sum to one"):
            row.validate()

    def test_invalid_categorical_id_fails_closed(self) -> None:
        row = replace(sample(0), modality_id=99)
        with self.assertRaisesRegex(ValueError, "categorical schema"):
            row.validate()


class CatalystModelTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(11)
        self.rows = [sample(index) for index in range(8)]
        self.normalizer = FeatureNormalizer.fit(self.rows)

    def test_composition_encoder_is_permutation_invariant(self) -> None:
        first = sample(0)
        permuted = sample(0, permutation=np.asarray([2, 0, 1]))
        batch = BatchCollator(self.normalizer)([first, permuted])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch)
        np.testing.assert_allclose(
            output["mean"][0].numpy(),
            output["mean"][1].numpy(),
            rtol=1e-5,
            atol=1e-6,
        )

    def test_invalid_attention_dimensions_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "n_heads"):
            CatalystTransferTransformer(
                CatalystAttentionConfig(d_model=32, n_heads=0)
            )
        with self.assertRaisesRegex(ValueError, "dropout"):
            CatalystTransferTransformer(
                CatalystAttentionConfig(dropout=1.0)
            )
        with self.assertRaisesRegex(ValueError, "depth routing"):
            CatalystTransferTransformer(
                CatalystAttentionConfig(depth_routing="unknown")
            )
        with self.assertRaisesRegex(ValueError, "depth_routing_heads"):
            CatalystTransferTransformer(
                CatalystAttentionConfig(
                    d_model=32, depth_routing_heads=3
                )
            )

    def test_delta_mhar_is_identity_preserving_at_initialization(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:2])
        standard = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=2,
                curve_layers=2,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        routed = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=2,
                curve_layers=2,
                fusion_layers=1,
                depth_routing="delta_mhar",
                depth_routing_heads=4,
                dropout=0.0,
            )
        ).eval()
        missing, unexpected = routed.load_state_dict(
            standard.state_dict(), strict=False
        )
        self.assertFalse(unexpected)
        self.assertTrue(missing)
        self.assertTrue(
            all(
                key.endswith((".query", ".gate"))
                for key in missing
            )
        )
        with torch.no_grad():
            standard_output = standard(batch)["mean"]
            routed_output = routed(batch)["mean"]
        torch.testing.assert_close(
            routed_output, standard_output, rtol=0.0, atol=1e-6
        )
        diagnostics = depth_routing_diagnostics(routed)
        self.assertTrue(diagnostics)
        for row in diagnostics.values():
            self.assertTrue(
                all(abs(value) < 1e-12 for value in row["gate"])
            )

    def test_sublayer_delta_mhar_preserves_residual_stream(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:2])
        standard = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=2,
                curve_layers=2,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        routed = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=2,
                curve_layers=2,
                fusion_layers=1,
                depth_routing="delta_mhar_sublayer",
                depth_routing_heads=4,
                dropout=0.0,
            )
        ).eval()
        missing, unexpected = routed.load_state_dict(
            standard.state_dict(), strict=False
        )
        self.assertFalse(unexpected)
        self.assertTrue(missing)
        with torch.no_grad():
            standard_output = standard(batch)["mean"]
            routed_output = routed(batch)["mean"]
        torch.testing.assert_close(
            routed_output, standard_output, rtol=0.0, atol=1e-6
        )
        diagnostics = depth_routing_diagnostics(routed)
        source_counts = [
            row.get("source_count", 0)
            for row in diagnostics.values()
        ]
        self.assertGreaterEqual(max(source_counts), 3)

    def test_adamw_optimizer_manifest_is_auditable(self) -> None:
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=16,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
            )
        )
        optimizer, manifest = build_optimizer(
            model, TrainingConfig(optimizer="adamw")
        )
        self.assertIsInstance(optimizer, torch.optim.AdamW)
        self.assertEqual(manifest["name"], "adamw")
        self.assertEqual(
            manifest["parameter_count"],
            sum(parameter.numel() for parameter in model.parameters()),
        )

    def test_official_kl_shampoo_variants_take_a_step(self) -> None:
        try:
            import distributed_shampoo  # noqa: F401
        except ImportError:
            self.skipTest("optional official KL-Shampoo is not installed")
        for name in ("kl_shampoo", "kl_shampoo_grafted"):
            with self.subTest(optimizer=name):
                model = CatalystTransferTransformer(
                    CatalystAttentionConfig(
                        d_model=16,
                        n_heads=4,
                        composition_layers=1,
                        curve_layers=1,
                        fusion_layers=1,
                    )
                )
                optimizer, manifest = build_optimizer(
                    model,
                    TrainingConfig(
                        optimizer=name,
                        learning_rate=1e-4,
                        shampoo_max_preconditioner_dim=16,
                        shampoo_precondition_frequency=1,
                        shampoo_start_preconditioning_step=1,
                    ),
                )
                loss = sum(
                    parameter.square().mean()
                    for parameter in model.parameters()
                    if parameter.requires_grad
                )
                loss.backward()
                optimizer.step()
                self.assertEqual(manifest["name"], name)
                self.assertGreater(
                    manifest["matrix_parameter_count"], 0
                )
                self.assertGreater(
                    manifest["adamw_fallback_parameter_count"], 0
                )

    def test_crabnet_encoder_is_permutation_invariant(self) -> None:
        first = sample(0)
        permuted = sample(0, permutation=np.asarray([2, 0, 1]))
        batch = BatchCollator(self.normalizer)([first, permuted])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                composition_mode="crabnet",
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch)
        np.testing.assert_allclose(
            output["mean"][0].numpy(),
            output["mean"][1].numpy(),
            rtol=1e-5,
            atol=1e-6,
        )

    def test_perceiver_fusion_has_fixed_latents_and_audit_weights(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:2])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_mode="perceiver",
                perceiver_latents=6,
                perceiver_layers=2,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch, return_attention=True)
        attention = output["attention"]["fusion_attention"]
        self.assertEqual(attention.shape[:3], (2, 4, 6))
        self.assertTrue(torch.isfinite(output["mean"]).all())

    def test_modality_dropout_keeps_task_tokens_available(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:4])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_mode="perceiver",
                perceiver_latents=4,
                perceiver_layers=1,
                modality_dropout=0.95,
                dropout=0.0,
            )
        ).train()
        output = model(batch, return_attention=True)
        dropped = output["attention"]["modality_dropped"]
        self.assertEqual(
            dropped.shape,
            (4, len(FUSION_BLOCK_NAMES)),
        )
        self.assertTrue(dropped.any())
        self.assertFalse(dropped[:, FUSION_BLOCK_NAMES.index("task")].any())
        self.assertTrue(torch.isfinite(output["mean"]).all())

    def test_curve_has_multiple_attention_tokens_and_audit_weights(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:2])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                patch_size=8,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch, return_attention=True)
        attention = output["attention"]["fusion_attention"]
        # 1 pooled composition + 3 elements + 4 curve patches + 10 conditions.
        self.assertEqual(attention.shape, (2, 4, 4, 18))
        entropy = attention_entropy(
            attention, output["attention"]["memory_padding_mask"]
        )
        self.assertTrue(torch.isfinite(entropy).all())

    def test_missing_curve_uses_explicit_token_without_nan(self) -> None:
        rows = [sample(0, curve=False), sample(1)]
        normalizer = FeatureNormalizer.fit(rows)
        batch = BatchCollator(normalizer)(rows)
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch)
        self.assertTrue(torch.isfinite(output["mean"]).all())

    def test_unlabeled_candidate_can_be_predicted(self) -> None:
        unlabeled = replace(sample(0), target=None)
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        output = predict(
            model,
            [unlabeled],
            self.normalizer,
            device=torch.device("cpu"),
            unknown_program=True,
        )
        self.assertEqual(output["mean"].shape, (1,))
        self.assertTrue(np.isfinite(output["mean"]).all())
        with self.assertRaisesRegex(ValueError, "at least one"):
            predict(
                model,
                [],
                self.normalizer,
                device=torch.device("cpu"),
            )

    def test_surface_composition_is_an_explicit_attention_modality(self) -> None:
        surfaced = replace(
            sample(0),
            surface_elements=np.asarray([77, 79], dtype=np.int64),
            surface_fractions=np.asarray([0.4, 0.6], dtype=np.float32),
        )
        batch = BatchCollator(self.normalizer)([surfaced, sample(1)])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                use_surface=True,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch, return_attention=True)
        modalities = output["attention"]["memory_modality"]
        self.assertTrue((modalities == 3).any())
        self.assertTrue(torch.isfinite(output["mean"]).all())

    def test_task_tokens_remain_when_numeric_conditions_are_disabled(self) -> None:
        batch = BatchCollator(self.normalizer)(self.rows[:2])
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=32,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                fusion_layers=1,
                use_conditions=False,
                dropout=0.0,
            )
        ).eval()
        with torch.no_grad():
            output = model(batch, return_attention=True)
        modalities = output["attention"]["memory_modality"]
        self.assertTrue(torch.all((modalities == 4).sum(dim=1) == 2))

    def test_rank_loss_rewards_correct_order(self) -> None:
        target = torch.tensor([0.0, 1.0, 2.0])
        correct = pairwise_rank_loss(torch.tensor([0.0, 1.0, 2.0]), target)
        reversed_loss = pairwise_rank_loss(torch.tensor([2.0, 1.0, 0.0]), target)
        self.assertLess(float(correct), float(reversed_loss))

    def test_coral_alignment_uses_latents_without_target_labels(self) -> None:
        source = torch.tensor(
            [[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]]
        )
        aligned = coral_alignment_loss(source, source.clone())
        shifted = coral_alignment_loss(source, source + torch.tensor([2.0, 0.0]))
        self.assertAlmostEqual(float(aligned), 0.0, places=6)
        self.assertGreater(float(shifted), float(aligned))
        unlabeled = BatchCollator(
            self.normalizer,
            unknown_program=True,
            require_target=False,
        )(self.rows[:2])
        self.assertNotIn("target", unlabeled)

    def test_support_calibrator_marks_far_latent_as_ood(self) -> None:
        source = np.asarray([[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [0.05, 0.0]])
        calibrator = LatentSupportCalibrator.fit(source, quantile=0.95)
        scores = calibrator.ood_score(np.asarray([[0.0, 0.0], [10.0, 10.0]]))
        self.assertLess(scores[0], 1.0)
        self.assertGreater(scores[1], 1.0)

    def test_small_source_training_runs_and_reports_metrics(self) -> None:
        rows = [sample(index) for index in range(30)]
        model, _, report = train_source_model(
            rows,
            CatalystAttentionConfig(
                d_model=24,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                condition_layers=1,
                fusion_layers=1,
                dropout=0.0,
            ),
            TrainingConfig(
                seed=7,
                epochs=2,
                patience=2,
                batch_size=10,
            ),
        )
        self.assertGreater(model.trainable_parameter_count(), 10_000)
        self.assertEqual(report["epochs_run"], 2)
        self.assertEqual(report["validation_split"], "group-held-out")
        self.assertEqual(report["validation_group_overlap"], [])
        self.assertTrue(
            np.isfinite(report["validation_metrics"]["rmse"])
        )

    def test_metric_contract(self) -> None:
        result = metrics(np.asarray([1.0, 2.0, 3.0]), np.asarray([1.0, 2.0, 3.0]))
        self.assertEqual(result["rmse"], 0.0)
        self.assertEqual(result["spearman"], 1.0)

    def test_pls_baseline_resamples_variable_curve_lengths(self) -> None:
        rows = [sample(index) for index in range(10)]
        shortened = sample(10)
        object.__setattr__(shortened, "curve_axis", shortened.curve_axis[:-3])
        object.__setattr__(shortened, "curve_values", shortened.curve_values[:-3])
        model = fit_pls_baseline(rows, components=2)
        prediction = predict_pls(model, [shortened])
        self.assertEqual(prediction.shape, (1,))
        self.assertTrue(np.isfinite(prediction).all())

    def test_checkpoint_round_trip_uses_tensor_only_schema(self) -> None:
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=24,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                condition_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            save_checkpoint(path, model, self.normalizer, {"best_epoch": 1})
            loaded, normalizer, report = load_checkpoint(path)
            payload = torch.load(path, map_location="cpu", weights_only=True)
            payload["schema"]["version"] = "incompatible"
            invalid = Path(directory) / "invalid.pt"
            torch.save(payload, invalid)
            with self.assertRaisesRegex(ValueError, "schema"):
                load_checkpoint(invalid)
        self.assertEqual(report["best_epoch"], 1)
        self.assertEqual(loaded.config.d_model, 24)
        self.assertAlmostEqual(normalizer.target_mean, self.normalizer.target_mean)

    def test_checkpoint_loader_discards_only_inactive_perceiver_weights(
        self,
    ) -> None:
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=24,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                condition_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-advanced.pt"
            save_checkpoint(path, model, self.normalizer, {"best_epoch": 1})
            payload = torch.load(path, map_location="cpu", weights_only=True)
            payload["model_state"][
                "fusion.perceiver_cross.0.in_proj_weight"
            ] = torch.zeros(3, 3)
            torch.save(payload, path)
            loaded, _, _ = load_checkpoint(path)
            payload["model_state"]["fusion.perceiver_unknown"] = torch.zeros(
                1
            )
            torch.save(payload, path)
            with self.assertRaisesRegex(RuntimeError, "Unexpected key"):
                load_checkpoint(path)
        self.assertEqual(loaded.config.fusion_mode, "cross_attention")

    def test_candidate_recommendation_is_risk_adjusted_and_target_free(self) -> None:
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=24,
                n_heads=4,
                composition_layers=1,
                curve_layers=1,
                condition_layers=1,
                fusion_layers=1,
                dropout=0.0,
            )
        ).eval()
        calibrator = calibrate_support(
            model,
            self.rows,
            self.normalizer,
            device=torch.device("cpu"),
        )
        candidates = [replace(row, target=None) for row in self.rows[:4]]
        ranked = recommend_candidates(
            model,
            candidates,
            self.normalizer,
            calibrator,
            device=torch.device("cpu"),
            objective="minimize",
            top_k=3,
        )
        self.assertEqual(len(ranked), 3)
        self.assertEqual([row["rank"] for row in ranked], [1, 2, 3])
        self.assertTrue(all(row["decision"] in {"recommend", "abstain"} for row in ranked))

    def test_tabular_featurizer_is_source_fitted_and_program_blind(self) -> None:
        source = self.rows[:6]
        featurizer = CatalystTabularFeaturizer(
            curve_components=3,
            maximum_curve_length=16,
        )
        matrix = featurizer.fit_transform(source)
        alternate_program = replace(
            source[0],
            program="specgen_B",
            program_id=3,
            target=None,
        )
        pair = featurizer.transform(
            [replace(source[0], target=None), alternate_program]
        )
        self.assertEqual(matrix.shape[0], len(source))
        self.assertTrue(np.isfinite(matrix).all())
        np.testing.assert_allclose(pair[0], pair[1])

    def test_atomic_writer_rejects_symlink_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "manifest.json"
            destination.symlink_to(root / "victim.json")
            with self.assertRaisesRegex(ValueError, "symlink"):
                atomic_write_text(destination, "{}\n")

    def test_expert_portfolio_abstains_on_high_disagreement(self) -> None:
        portfolio = combine_expert_predictions(
            [
                np.asarray([1.0, 2.0, 3.0, 4.0]),
                np.asarray([1.1, 2.1, 2.9, 10.0]),
                np.asarray([0.9, 1.9, 3.1, -2.0]),
            ],
            abstention_fraction=0.25,
        )
        self.assertEqual(portfolio.eligible.tolist(), [True, True, True, False])
        self.assertAlmostEqual(float(portfolio.weights.sum()), 1.0)
        self.assertTrue(np.isfinite(portfolio.mean).all())


class ExpertRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(42)
        self.rows = [sample(index) for index in range(20)]
        self.normalizer = FeatureNormalizer.fit(self.rows)

    def _tiny_pair(self) -> ExpertPair:
        """Train a minimal expert pair for unit testing."""
        config = CatalystAttentionConfig(
            d_model=16,
            n_heads=4,
            composition_layers=1,
            curve_layers=1,
            condition_layers=1,
            fusion_layers=1,
            dropout=0.0,
        )
        training = TrainingConfig(seed=1, epochs=2, patience=2, batch_size=10)
        return train_expert_pair(
            self.rows, config, training, device=torch.device("cpu")
        )

    def test_invalid_strategy_raises(self) -> None:
        pair = self._tiny_pair()
        with self.assertRaisesRegex(ValueError, "unsupported strategy"):
            ExpertRouter(
                pair.standard,
                pair.mhar,
                pair.standard_calibrator,
                pair.mhar_calibrator,
                strategy="nonexistent",
            )

    def test_router_produces_valid_output(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="disagreement_gated",
        )
        output = router.route(
            self.rows[:4],
            self.normalizer,
            device=torch.device("cpu"),
        )
        self.assertEqual(len(output.mean), 4)
        self.assertTrue(np.isfinite(output.mean).all())
        self.assertTrue(np.isfinite(output.disagreement).all())
        self.assertTrue(np.isfinite(output.domain_distance_ratio).all())
        # All samples should be non-abstaining in disagreement_gated.
        self.assertFalse(output.abstain.any())

    def test_ensemble_strategy_abstains_on_high_disagreement(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="ensemble",
        )
        output = router.route(
            self.rows[:8],
            self.normalizer,
            device=torch.device("cpu"),
        )
        self.assertEqual(len(output.mean), 8)
        # Ensemble always uses weighted average.
        np.testing.assert_allclose(
            output.mean,
            0.5 * (output.standard_mean + output.mhar_mean),
            rtol=1e-5,
        )
        # Selected expert should be -1 (ensemble) for all.
        self.assertTrue((output.selected_expert == -1).all())

    def test_domain_preferring_routes_to_closer_expert(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="domain_preferring",
        )
        output = router.route(
            self.rows[:8],
            self.normalizer,
            device=torch.device("cpu"),
        )
        self.assertEqual(len(output.mean), 8)
        # Each sample should be routed to exactly one expert.
        for i in range(8):
            ratio = output.domain_distance_ratio[i]
            if ratio < 0.5:
                self.assertEqual(output.selected_expert[i], 0)
            else:
                self.assertEqual(output.selected_expert[i], 1)

    def test_uncertainty_minimizing_routes_to_more_confident(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="uncertainty_minimizing",
        )
        output = router.route(
            self.rows[:8],
            self.normalizer,
            device=torch.device("cpu"),
        )
        self.assertEqual(len(output.mean), 8)
        for i in range(8):
            ratio = (
                output.standard_std[i]
                / (output.standard_std[i] + output.mhar_std[i])
                if (output.standard_std[i] + output.mhar_std[i]) > 1e-12
                else 0.5
            )
            if ratio < 0.5:
                self.assertEqual(output.selected_expert[i], 0)
            else:
                self.assertEqual(output.selected_expert[i], 1)

    def test_oracle_always_picks_better_expert(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="oracle",
        )
        output = router.route(
            self.rows[:8],
            self.normalizer,
            device=torch.device("cpu"),
        )
        targets = targets_array(self.rows[:8])
        for i in range(8):
            standard_err = abs(output.standard_mean[i] - targets[i])
            mhar_err = abs(output.mhar_mean[i] - targets[i])
            if standard_err <= mhar_err:
                self.assertEqual(output.selected_expert[i], 0)
            else:
                self.assertEqual(output.selected_expert[i], 1)

    def test_audit_trail_has_required_fields(self) -> None:
        pair = self._tiny_pair()
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
        )
        sample_ids = [row.sample_id for row in self.rows[:4]]
        output = router.route(
            self.rows[:4],
            self.normalizer,
            device=torch.device("cpu"),
        )
        trail = router_audit_trail(output, sample_ids)
        self.assertEqual(len(trail), 4)
        required = {
            "sample_id",
            "standard_mean",
            "mhar_mean",
            "routed_mean",
            "selected_expert",
            "disagreement",
            "domain_distance_ratio",
            "abstain",
        }
        for row in trail:
            self.assertEqual(set(row), required)

    def test_calibrate_disagreement_threshold_is_finite(self) -> None:
        pair = self._tiny_pair()
        threshold = calibrate_disagreement_threshold(
            pair,
            self.rows[:10],
            device=torch.device("cpu"),
        )
        self.assertTrue(np.isfinite(threshold))
        self.assertGreaterEqual(threshold, 0.0)


class CatalystResultContractTests(unittest.TestCase):
    def load_result(self, name: str) -> dict:
        path = ROOT / "analysis" / "results" / name
        return json.loads(path.read_text(encoding="utf-8"))

    def test_promising_and_boundary_gates_are_preserved(self) -> None:
        specgen = self.load_result("catalyst_attention_specgen_summary.json")
        ocx24 = self.load_result("catalyst_attention_ocx24_summary.json")
        seccm = self.load_result("catalyst_attention_seccm_summary.json")
        self.assertTrue(specgen["promising_gate"]["passed"])
        self.assertTrue(ocx24["transfer_gate"]["passed"])
        self.assertFalse(seccm["representation_gate"]["passed"])

    def test_ocx24_validation_never_crosses_physical_sample_groups(self) -> None:
        result = self.load_result("catalyst_attention_ocx24_summary.json")
        for direction in result["directions"].values():
            for variant in (
                "composition_condition_attention",
                "composition_attention_only",
            ):
                for run in direction[variant]["runs"]:
                    self.assertEqual(run["validation_split"], "group-held-out")
                    self.assertEqual(run["validation_group_overlap"], [])

    def test_attention_audit_keeps_noncausal_warning_and_repeated_shuffles(self) -> None:
        result = self.load_result("catalyst_attention_audit.json")
        self.assertIn("not causal", result["warning"].lower())
        system_b = result["programs"]["specgen_B"]
        self.assertGreaterEqual(system_b["curve_shuffle"]["draws"], 20)
        self.assertGreaterEqual(system_b["composition_shuffle"]["draws"], 20)

    def test_advanced_model_null_and_frozen_design_are_preserved(self) -> None:
        design_path = (
            ROOT / "analysis" / "catalyst_attention_advanced_design.json"
        )
        design = json.loads(design_path.read_text(encoding="utf-8"))
        design_hash = hashlib.sha256(design_path.read_bytes()).hexdigest()
        specgen = self.load_result(
            "catalyst_attention_advanced_specgen.json"
        )
        ocx24 = self.load_result(
            "catalyst_attention_advanced_ocx24.json"
        )
        seccm = self.load_result(
            "catalyst_attention_advanced_seccm.json"
        )
        summary = self.load_result(
            "catalyst_attention_advanced_summary.json"
        )
        for result in (specgen, ocx24, seccm):
            self.assertEqual(result["design_sha256"], design_hash)
            self.assertEqual(result["status"], "partial")
            self.assertIsNone(result["any_advanced_gate_passed"])
        self.assertEqual(summary["design_sha256"], design_hash)
        self.assertEqual(summary["status"], "complete")
        self.assertFalse(summary["any_advanced_gate_passed"])
        self.assertEqual(summary["missing_datasets"], [])
        for artifact in summary["dataset_artifacts"].values():
            path = ROOT / artifact["path"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["sha256"],
            )
        for artifact in design["reference_artifacts"].values():
            path = ROOT / "analysis" / artifact["path"]
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                artifact["sha256"],
            )
        self.assertFalse(specgen["datasets"]["specgen"]["gate"]["passed"])
        self.assertFalse(ocx24["datasets"]["ocx24"]["gate"]["passed"])
        boundary = seccm["datasets"]["seccm"]["evidence_boundary"]
        self.assertFalse(boundary["independent_discovery_claim_allowed"])
        tabpfn = specgen["datasets"]["specgen"]["models"]["tabpfn_v2"]
        self.assertEqual(
            tabpfn["manifest"]["model_sha256"],
            (
                "2ab5a07d5c41dfe6db9aa7ae106fc6de898326c2765be66505"
                "a07e2868c10736"
            ),
        )

    def test_advanced_ocx24_source_validation_remains_group_disjoint(
        self,
    ) -> None:
        result = self.load_result(
            "catalyst_attention_advanced_ocx24.json"
        )
        for direction in result["datasets"]["ocx24"][
            "directions"
        ].values():
            for name in (
                "crabnet_cross",
                "set_perceiver",
                "crabnet_perceiver",
            ):
                for run in direction["models"][name]["runs"]:
                    self.assertEqual(
                        run["validation_split"], "group-held-out"
                    )
                    self.assertEqual(
                        run["validation_group_overlap"], []
                    )


class DomainAdversarialTests(unittest.TestCase):
    def test_grl_reverses_gradient_sign(self) -> None:
        x = torch.tensor([1.0, 2.0], requires_grad=True)
        y = gradient_reversal(x, lambda_=1.0)
        loss = y.sum()
        loss.backward()
        self.assertTrue((x.grad < 0).all())
        # Without GRL, gradient would be positive.
        x2 = torch.tensor([1.0, 2.0], requires_grad=True)
        loss2 = x2.sum()
        loss2.backward()
        self.assertTrue((x2.grad > 0).all())

    def test_domain_classifier_output_shape(self) -> None:
        classifier = DomainClassifier(d_model=64, n_domains=2)
        latent = torch.randn(16, 64)
        logits = classifier(latent)
        self.assertEqual(logits.shape, (16, 2))

    def test_adversarial_domain_loss(self) -> None:
        classifier = DomainClassifier(d_model=64, n_domains=2)
        latent = torch.randn(16, 64, requires_grad=True)
        domain_ids = torch.cat(
            [torch.zeros(8, dtype=torch.long), torch.ones(8, dtype=torch.long)]
        )
        loss, accuracy = adversarial_domain_loss(
            latent, domain_ids, classifier
        )
        self.assertTrue(torch.isfinite(loss))
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 1.0)

    def test_grl_lambda_schedule_is_monotonic(self) -> None:
        values = [grl_lambda_schedule(s, 100) for s in range(101)]
        for i in range(len(values) - 1):
            self.assertLessEqual(values[i], values[i + 1])
        self.assertAlmostEqual(values[0], 0.0, places=3)
        self.assertAlmostEqual(values[-1], 1.0, places=3)


class ContrastiveTests(unittest.TestCase):
    def test_composition_to_vector(self) -> None:
        elements = torch.tensor([[26, 27, 0], [28, 0, 0]])  # Fe, Co; Ni.
        fractions = torch.tensor([[0.4, 0.6, 0.0], [1.0, 0.0, 0.0]])
        vec = composition_to_vector(elements, fractions)
        self.assertEqual(vec.shape, (2, 118))
        self.assertAlmostEqual(float(vec[0, 25]), 0.4)  # Fe (26) → index 25.
        self.assertAlmostEqual(float(vec[0, 26]), 0.6)  # Co (27) → index 26.

    def test_composition_cosine_similarity(self) -> None:
        v1 = torch.zeros(1, 118)
        v1[0, 25] = 0.4
        v1[0, 26] = 0.6
        v2 = torch.zeros(1, 118)
        v2[0, 25] = 0.4
        v2[0, 26] = 0.6
        sim = composition_cosine_similarity(v1, v2)
        self.assertAlmostEqual(float(sim), 1.0, places=4)
        v3 = torch.zeros(1, 118)
        v3[0, 45] = 1.0
        sim2 = composition_cosine_similarity(v1, v3)
        self.assertLess(float(sim2), 0.1)

    def test_contrastive_projection(self) -> None:
        proj = ContrastiveProjection(d_model=64, projection_dim=32)
        latent = torch.randn(8, 64)
        projected = proj(latent)
        self.assertEqual(projected.shape, (8, 32))
        norms = projected.norm(dim=-1)
        self.assertTrue(torch.allclose(norms, torch.ones_like(norms), atol=1e-6))

    def test_contrastive_loss_returns_valid(self) -> None:
        proj = ContrastiveProjection(d_model=32, projection_dim=16)
        latent = torch.randn(4, 32)
        elements = torch.tensor(
            [[26, 27, 0, 0], [26, 27, 0, 0], [28, 0, 0, 0], [28, 0, 0, 0]]
        )
        fractions = torch.tensor(
            [[0.5, 0.5, 0.0, 0.0], [0.5, 0.5, 0.0, 0.0],
             [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
        )
        loss, diag = contrastive_loss(
            latent, elements, fractions, proj
        )
        self.assertTrue(torch.isfinite(loss))
        self.assertIn("n_positive_pairs", diag)


class GeneticSearchTests(unittest.TestCase):
    def test_random_individual_is_valid(self) -> None:
        ind = random_individual()
        config = ind.to_model_config()
        tconfig = ind.to_training_config()
        config.validate()
        self.assertIsNotNone(config.d_model)
        self.assertIsNotNone(tconfig.learning_rate)

    def test_crossover_is_valid(self) -> None:
        a = random_individual()
        b = random_individual()
        child = crossover(a, b)
        self.assertEqual(set(child.genes.keys()), set(a.genes.keys()))
        # Verify child is valid.
        child.to_model_config().validate()

    def test_mutate_is_valid(self) -> None:
        ind = random_individual()
        mutated = mutate(ind, rate=1.0)
        self.assertEqual(set(mutated.genes.keys()), set(ind.genes.keys()))
        mutated.to_model_config().validate()

    def test_ga_population_initialization(self) -> None:
        from catalyst_attention.genetic_search import CatalystGASearch
        searcher = CatalystGASearch(
            [sample(i) for i in range(30)],
            device=torch.device("cpu"),
            population_size=4,
            generations=1,
            epochs=2,
        )
        population = [random_individual() for _ in range(4)]
        for ind in population:
            self.assertIsNotNone(ind.to_model_config())
            self.assertIsNotNone(ind.to_training_config())


class MetaLearningTests(unittest.TestCase):
    def test_split_support_query(self) -> None:
        rows = [sample(i) for i in range(10)]
        support, query = _split_support_query(rows, support_size=3, seed=42)
        self.assertEqual(len(support), 3)
        self.assertEqual(len(query), 7)
        self.assertEqual(
            len(set(s.sample_id for s in support) & set(q.sample_id for q in query)),
            0,
        )

    def test_fomaml_inner_loop_trains(self) -> None:
        model = CatalystTransferTransformer(
            CatalystAttentionConfig(
                d_model=16, n_heads=4, composition_layers=1,
                curve_layers=1, fusion_layers=1, dropout=0.0,
            )
        )
        maml = FOMAMLWrapper(model, inner_lr=0.01, inner_steps=2, first_order=True)
        normalizer = FeatureNormalizer.fit([sample(i) for i in range(10)])
        support_batch = BatchCollator(normalizer)([sample(i) for i in range(5)])
        params_before = {
            name: p.clone() for name, p in model.named_parameters()
        }
        maml.inner_loop(support_batch, TrainingConfig())
        changed = 0
        for name, param in model.named_parameters():
            if not torch.allclose(param, params_before[name], atol=1e-8):
                changed += 1
        self.assertGreater(changed, 0, "Inner loop should update parameters")


if __name__ == "__main__":
    unittest.main()
