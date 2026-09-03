from __future__ import annotations

import json
import math
import sqlite3
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))

from analysis.common import DB, load_obelix  # noqa: E402
from scripts.localdb.build_localdb import canonical_formula, canonical_mixture  # noqa: E402


class EntityResolutionTests(unittest.TestCase):
    def test_parenthesized_formula(self):
        key, flag = canonical_formula("BiSb(Se0.92Br0.08)3")
        self.assertIsNone(flag)
        self.assertEqual(key, "Bi:0.2|Br:0.048|Sb:0.2|Se:0.552")

    def test_hyphenated_alloy(self):
        key, flag = canonical_formula("Ag-0.125-Cu-0.125-Pd-0.75")
        self.assertIsNone(flag)
        self.assertEqual(key, "Ag:0.125|Cu:0.125|Pd:0.75")

    def test_scale_invariance(self):
        left, _ = canonical_formula("Li20.1Ge2.1P3.9S24")
        right, _ = canonical_formula("Li80.4Ge8.4P15.6S96")
        self.assertEqual(left, right)

    def test_mixture_scale_invariance(self):
        left, left_flag = canonical_mixture("PC:1.5|EC:1.5|EMC:7.2|LiPF_6:0.3")
        right, right_flag = canonical_mixture("PC:15|EC:15|EMC:72|LiPF_6:3")
        self.assertIsNone(left_flag)
        self.assertIsNone(right_flag)
        self.assertEqual(left, right)
        self.assertIn("LiPF_6", left)


class SnapshotIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DB.exists():
            raise unittest.SkipTest("Build data/collective.sqlite before running snapshot tests")
        cls.connection = sqlite3.connect(DB)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()

    def test_signed_organic_values_are_retained(self):
        rows = dict(
            self.connection.execute(
                """SELECT dataset,SUM(value<=0) FROM measurements
                   WHERE (dataset='aqsoldb' AND property='logS')
                      OR (dataset='freesolv' AND property='dG_hydration')
                   GROUP BY dataset"""
            )
        )
        self.assertEqual(rows["aqsoldb"], 8920)
        self.assertEqual(rows["freesolv"], 558)

    def test_isodb_is_analysis_only(self):
        count, status = self.connection.execute(
            "SELECT n_measurements,normalization_status FROM datasets WHERE id='nist-isodb'"
        ).fetchone()
        self.assertEqual(count, 0)
        self.assertEqual(
            status,
            "analysis-only-streamed-isosteric-fits-not-in-material-schema",
        )

    def test_schema_v3_and_kit_snapshot(self):
        schema_version = dict(
            self.connection.execute("SELECT key,value FROM build_metadata")
        )["schema_version"]
        self.assertEqual(schema_version, "3")
        dataset = "kit-electrolyte-conductivity-5035"
        measurements, entities, rows, kinds, properties = self.connection.execute(
            """SELECT COUNT(*),COUNT(DISTINCT material_key),
                      COUNT(DISTINCT source_row_id),COUNT(DISTINCT material_kind),
                      COUNT(DISTINCT property)
               FROM measurements WHERE dataset=?""",
            (dataset,),
        ).fetchone()
        self.assertEqual(measurements, 5035)
        self.assertEqual(rows, 5035)
        self.assertEqual(entities, 109)
        self.assertEqual(kinds, 1)
        self.assertEqual(properties, 1)
        kind, prop, unit = self.connection.execute(
            """SELECT MIN(material_kind),MIN(property),MIN(unit)
               FROM measurements WHERE dataset=?""",
            (dataset,),
        ).fetchone()
        self.assertEqual(kind, "mixture")
        self.assertEqual(prop, "electrolyte_conductivity")
        self.assertEqual(unit, "S/cm")

    def test_calisol_snapshot_retains_provenance_and_valid_mixture_keys(self):
        dataset = "calisol-23"
        measurements, entities, rows, missing_keys, articles = self.connection.execute(
            """SELECT COUNT(*),COUNT(DISTINCT material_key),
                      COUNT(DISTINCT source_row_id),SUM(material_key IS NULL),
                      COUNT(DISTINCT json_extract(conditions_json,'$.source_article_doi'))
               FROM measurements WHERE dataset=?""",
            (dataset,),
        ).fetchone()
        self.assertEqual(measurements, 13301)
        self.assertEqual(rows, 13301)
        self.assertEqual(entities, 6116)
        self.assertEqual(missing_keys, 0)
        self.assertEqual(articles, 27)
        kind, prop, unit = self.connection.execute(
            """SELECT MIN(material_kind),MIN(property),MIN(unit)
               FROM measurements WHERE dataset=?""",
            (dataset,),
        ).fetchone()
        self.assertEqual((kind, prop, unit), ("mixture", "electrolyte_conductivity", "mS/cm"))

    def test_birdshot_snapshot_is_complete(self):
        dataset = "birdshot-high-entropy-alloy-campaign"
        rows = self.connection.execute(
            """SELECT property,COUNT(*),COUNT(DISTINCT source_row_id)
               FROM measurements WHERE dataset=? GROUP BY property""",
            (dataset,),
        ).fetchall()
        self.assertEqual(
            {row[0] for row in rows},
            {
                "Hardness, HV",
                "Yield Strength (MPa)",
                "UTS_True (Mpa)",
                "Elong_T (%)",
                "Modulus (GPa) SRJT",
            },
        )
        self.assertTrue(all(count == 171 and sources == 171 for _, count, sources in rows))
        n_measurements, n_entities = self.connection.execute(
            """SELECT COUNT(*),COUNT(DISTINCT material_key)
               FROM measurements WHERE dataset=?""",
            (dataset,),
        ).fetchone()
        self.assertEqual(n_measurements, 855)
        self.assertEqual(n_entities, 151)

    def test_borg_birdshot_exact_composition_overlap_is_zero(self):
        query = "SELECT DISTINCT material_key FROM measurements WHERE dataset=?"
        borg = {
            row[0]
            for row in self.connection.execute(query, ("mpea-dataset-borg",))
            if row[0]
        }
        birdshot = {
            row[0]
            for row in self.connection.execute(
                query, ("birdshot-high-entropy-alloy-campaign",)
            )
            if row[0]
        }
        self.assertEqual(borg & birdshot, set())

    def test_obelix_evaluation_groups_do_not_cross_split(self):
        frame = load_obelix()
        self.assertEqual(frame.attrs["canonical_test_overlap_keys_excluded"], 2)
        self.assertEqual(frame.attrs["canonical_test_overlap_rows_excluded"], 2)
        self.assertTrue((frame.groupby("group")["split"].nunique() == 1).all())
        self.assertEqual(set(frame.loc[frame.split == "train", "material_key"]) &
                         set(frame.loc[frame.split == "test", "material_key"]), set())

    def test_primary_summary_has_multiplicity_adjustment(self):
        path = ROOT / "analysis" / "results" / "primary_transfer_summary.csv"
        if not path.exists():
            self.skipTest("Run analysis/run_confirmatory.py before result tests")
        summary = pd.read_csv(path)
        primary = summary[summary["learner"] == "Ridge (primary)"]
        self.assertEqual(len(primary), 3)
        self.assertTrue(primary["permutation_p_holm"].notna().all())
        self.assertTrue((primary["permutation_p_holm"] >= primary["permutation_p_raw"]).all())


class ClaimOutputTests(unittest.TestCase):
    @staticmethod
    def load_json(name: str) -> dict:
        path = ROOT / "analysis" / "results" / name
        if not path.exists():
            raise unittest.SkipTest(f"Missing claim output: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_internal_core_edge_passes_refined_multiplicity_gate(self):
        path = ROOT / "analysis" / "results" / "knowledge_map_edges_refined.csv"
        if not path.exists():
            self.skipTest("Run the knowledge-map workflow before result tests")
        frame = pd.read_csv(path)
        row = frame[(frame["source"] == "alloy_uts") & (frame["target"] == "alloy_ys")]
        self.assertEqual(len(row), 1)
        row = row.iloc[0]
        self.assertGreater(row["relative_rmse_ci_lo"], 0)
        self.assertLessEqual(row["permutation_p_holm_refined"], 0.05)
        self.assertEqual(row["learners_positive_of_three"], 3)
        self.assertEqual(
            row["edge_status_refined"],
            "internally-confirmed-awaits-external-replication",
        )

    def test_external_core_edge_is_directional_not_fully_confirmed(self):
        path = ROOT / "analysis" / "results" / "external_confirmation_edges.csv"
        if not path.exists():
            self.skipTest("Run external confirmation before result tests")
        frame = pd.read_csv(path)
        row = frame[(frame["source"] == "alloy_uts") & (frame["target"] == "birdshot_ys")]
        self.assertEqual(len(row), 1)
        row = row.iloc[0]
        self.assertGreater(row["relative_rmse_ci_lo"], 0)
        self.assertLess(row["relative_rmse_improvement_mean"], 0.05)
        self.assertLessEqual(row["primary_permutation_p"], 0.05)
        self.assertTrue(math.isnan(row["target_sample_fraction_saved"]))
        self.assertEqual(
            row["edge_status"],
            "directionally-replicated-below-practical-gate",
        )

    def test_direct_strength_law_fails_external_transport(self):
        summary = self.load_json("strength_law_summary.json")
        self.assertEqual(summary["canonical_composition_overlap"], 0)
        self.assertGreater(summary["fits"]["borg"]["r2"], 0.7)
        self.assertLess(summary["fits"]["birdshot"]["r2"], 0.1)
        self.assertLess(summary["borg_to_birdshot"]["external_r2"], 0)
        self.assertLess(summary["cluster_bootstrap_95"]["external_r2"][1], 0)

    def test_process_robustness_does_not_become_a_rescue_claim(self):
        summary = self.load_json("external_confirmation_utility_summary.json")
        process = summary["rolling_time_process_aware"]
        self.assertGreater(process["relative_rmse_ci"][0], 0)
        self.assertLess(process["pooled_augmented_r2"], 0)
        self.assertFalse(summary["rescue_claim_supported"])
        interpolation = summary["same_campaign_interpolation_n30"]
        self.assertGreater(interpolation["augmented_r2_mean"], 0)
        self.assertLess(interpolation["repeat_quantile_95"][0], 0)

    def test_map_is_selective_but_not_ordinally_calibrated(self):
        summary = self.load_json("knowledge_map_synthesis_summary.json")
        self.assertLess(summary["selectivity"]["internal_cochran_q_p"], 0.05)
        self.assertGreaterEqual(summary["selectivity"]["harmful_external_edges"], 1)
        self.assertGreater(summary["physical_ordering"]["ordinal_spearman_p"], 0.05)
        self.assertTrue(
            summary["core_edge"]["within_campaign_local_rescue"][
                "rescue_claim_supported"
            ]
        )
        saving_interval = summary["core_edge"]["within_campaign_local_rescue"][
            "target_sample_fraction_saved_diagnostic_95"
        ]
        self.assertLess(saving_interval[0], 0.30)
        self.assertGreater(saving_interval[1], 0.30)
        self.assertFalse(
            summary["core_edge"]["independent_matbench"][
                "rescue_claim_supported"
            ]
        )
        self.assertFalse(
            summary["core_edge"]["independent_multi_article_local_boundary"][
                "rescue_claim_supported"
            ]
        )

    def test_matbench_is_an_independent_negative_boundary(self):
        summary = self.load_json("matbench_steels_external_summary.json")
        self.assertEqual(summary["target_rows"], 312)
        self.assertEqual(summary["official_folds"], 5)
        self.assertEqual(summary["post_exclusion_overlap"], 0)
        self.assertFalse(summary["same_row_matbench_tensile_strength_used_as_input"])
        self.assertLess(summary["relative_rmse_improvement"], 0)
        self.assertGreater(summary["relative_rmse_ci"][1], 0)
        self.assertGreater(summary["primary_permutation_p"], 0.05)
        self.assertFalse(summary["rescue_claim_supported"])

    def test_kit_local_rescue_passes_every_frozen_gate(self):
        summary = self.load_json("kit_temperature_summary.json")
        self.assertFalse(summary["quick_smoke_test"])
        self.assertEqual(summary["raw_rows"], 5035)
        self.assertEqual(summary["raw_experiment_ids"], 504)
        self.assertEqual(summary["independent_formulations"], 108)
        self.assertEqual(summary["outer_folds"], 5)
        self.assertEqual(summary["target_budget_per_fold"], 30)
        self.assertEqual(summary["test_formulations_seen_by_source_model"], 0)
        self.assertFalse(summary["arrhenius_or_eis_fit_features_used"])
        self.assertGreater(summary["relative_rmse_improvement"], 0.05)
        self.assertGreater(summary["relative_rmse_ci"][0], 0)
        self.assertGreater(summary["pooled_augmented_r2"], summary["pooled_base_r2"])
        self.assertGreater(summary["target_sample_fraction_saved"], 0.30)
        self.assertEqual(summary["positive_learners_of_three"], 3)
        self.assertEqual(summary["primary_permutation_p"], 0.001)
        self.assertEqual(summary["source_feature_rank_median"], 1.0)
        self.assertEqual(summary["temperature_distance_spearman_rho"], -1.0)
        self.assertLess(summary["shuffled_source_effect"], 0)
        self.assertTrue(all(summary["gates"].values()))
        self.assertTrue(summary["rescue_claim_supported"])
        self.assertEqual(
            summary["decision"],
            "within-campaign-local-neighbor-rescue-gate-passed",
        )

    def test_kit_compact_outputs_preserve_distance_placebo_and_anchor(self):
        result_dir = ROOT / "analysis" / "results"
        edges = pd.read_csv(result_dir / "kit_temperature_edges.csv")
        real = edges[edges["relation"] != "shuffled-source-placebo"].sort_values(
            "absolute_temperature_distance_C"
        )
        self.assertTrue(
            np.all(np.diff(real["relative_rmse_improvement_mean"].to_numpy()) < 0)
        )
        self.assertEqual(edges["pooled_base_r2"].nunique(), 1)
        placebo = edges[edges["relation"] == "shuffled-source-placebo"].iloc[0]
        self.assertLess(placebo["relative_rmse_ci_hi"], 0)
        curve = pd.read_csv(result_dir / "kit_temperature_learning_curve.csv")
        anchor = curve[curve["train_n"] == 30].iloc[0]
        self.assertEqual(anchor["repeats_used"], 100)
        self.assertTrue(anchor["valid_for_target_equivalence"])
        self.assertTrue(np.all(np.diff(curve["rmse_mean"].to_numpy()) < 0))
        null = pd.read_csv(result_dir / "kit_temperature_permutation_null.csv")
        observed = null["observed_relative_mse_improvement"].iloc[0]
        p_value = (1 + int((null["relative_mse_improvement"] >= observed).sum())) / (
            len(null) + 1
        )
        self.assertEqual(len(null), 999)
        self.assertEqual(p_value, 0.001)

    def test_kit_sample_equivalence_uncertainty_is_not_hidden(self):
        summary = self.load_json("kit_sample_equivalence_uncertainty.json")
        frozen = self.load_json("kit_temperature_summary.json")
        self.assertEqual(
            summary["analysis_status"],
            "post-outcome-sample-equivalence-uncertainty-diagnostic",
        )
        self.assertEqual(summary["bootstrap_replicates"], 5000)
        self.assertAlmostEqual(
            summary["point_target_sample_fraction_saved"],
            frozen["target_sample_fraction_saved"],
        )
        interval = summary["bootstrap_target_sample_fraction_saved_95"]
        self.assertLess(interval[0], 0.30)
        self.assertGreater(interval[1], 0.30)
        probability = summary[
            "bootstrap_probability_fraction_saved_at_least_30pct"
        ]
        self.assertGreater(probability, 0.75)
        self.assertLess(probability, 0.9)
        bootstrap = pd.read_csv(
            ROOT / "analysis" / "results" / "kit_sample_equivalence_bootstrap.csv"
        )
        self.assertEqual(len(bootstrap), 5000)
        self.assertTrue(
            np.isfinite(bootstrap["target_sample_fraction_saved"]).all()
        )

    def test_kit_row_level_prediction_audit_when_available(self):
        path = ROOT / "analysis" / "results" / "kit_temperature_predictions.csv"
        if not path.exists():
            self.skipTest("Large KIT prediction artifact is reproducible but not versioned")
        predictions = pd.read_csv(path)
        primary = predictions[
            (predictions["source"] == "temperature_-20_C")
            & (predictions["learner"] == "random-forest-primary")
        ]
        self.assertEqual(len(primary), 10800)
        self.assertTrue((primary.groupby("repeat").size() == 108).all())
        baselines = predictions[
            predictions["learner"] == "random-forest-primary"
        ].pivot(
            index=["fold", "repeat", "material_key"],
            columns="source",
            values="baseline",
        )
        self.assertEqual(float((baselines.max(axis=1) - baselines.min(axis=1)).max()), 0.0)

    def test_calisol_is_a_frozen_cross_article_failure_boundary(self):
        summary = self.load_json("calisol_external_summary.json")
        self.assertFalse(summary["quick_smoke_test"])
        self.assertEqual(summary["raw_rows"], 13825)
        self.assertEqual(summary["literature_articles"], 27)
        self.assertEqual(summary["target_units"], 891)
        self.assertEqual(summary["target_articles"], 15)
        self.assertEqual(summary["outer_folds"], 5)
        self.assertEqual(summary["target_budget_per_fold"], 30)
        self.assertEqual(summary["test_articles_seen_by_source_model"], 0)
        self.assertEqual(summary["exact_test_chemistries_seen_by_source_model"], 0)
        self.assertFalse(summary["article_doi_used_as_predictor"])
        self.assertFalse(summary["temperature_or_curve_fit_features_used"])
        self.assertLess(summary["relative_rmse_improvement"], 0.05)
        self.assertLess(summary["relative_rmse_ci"][0], 0)
        self.assertLess(summary["pooled_augmented_r2"], 0)
        self.assertLess(summary["target_sample_fraction_saved"], 0.30)
        self.assertTrue(any(value < 0 for value in summary["fold_effects"]))
        self.assertEqual(summary["temperature_distance_spearman_rho"], 0.0)
        # A small fixed-subset mapping p-value cannot override the repeated-
        # effect, utility, fold, saving, and adjacency gates.
        self.assertEqual(summary["primary_permutation_p"], 0.004)
        self.assertFalse(summary["rescue_claim_supported"])
        self.assertEqual(summary["decision"], "cross-article-borrowing-unresolved")

    def test_calisol_compact_outputs_preserve_failed_distance_and_anchor(self):
        result_dir = ROOT / "analysis" / "results"
        edges = pd.read_csv(result_dir / "calisol_external_edges.csv")
        self.assertEqual(edges["pooled_base_r2"].nunique(), 1)
        primary = edges[edges["source"] == "temperature_-30_C"].iloc[0]
        zero_control = edges[edges["source"] == "temperature_0_C"].iloc[0]
        self.assertGreater(
            zero_control["relative_rmse_improvement_mean"],
            primary["relative_rmse_improvement_mean"],
        )
        curve = pd.read_csv(result_dir / "calisol_external_learning_curve.csv")
        anchor = curve[curve["train_n"] == 30].iloc[0]
        self.assertEqual(anchor["repeats_used"], 100)
        self.assertTrue(anchor["valid_for_target_equivalence"])
        null = pd.read_csv(result_dir / "calisol_external_permutation_null.csv")
        observed = null["observed_relative_mse_improvement"].iloc[0]
        p_value = (1 + int((null["relative_mse_improvement"] >= observed).sum())) / (
            len(null) + 1
        )
        self.assertEqual(len(null), 999)
        self.assertEqual(p_value, 0.004)

    def test_calisol_row_level_prediction_audit_when_available(self):
        path = ROOT / "analysis" / "results" / "calisol_external_predictions.csv"
        if not path.exists():
            self.skipTest("Large CALiSol prediction artifact is reproducible but not versioned")
        predictions = pd.read_csv(path)
        primary = predictions[
            (predictions["source"] == "temperature_-30_C")
            & (predictions["learner"] == "random-forest-primary")
        ]
        self.assertEqual(len(primary), 89100)
        self.assertTrue((primary.groupby("repeat").size() == 891).all())
        baselines = predictions[
            predictions["learner"] == "random-forest-primary"
        ].pivot(
            index=["fold", "repeat", "material_key"],
            columns="source",
            values="baseline",
        )
        self.assertEqual(float((baselines.max(axis=1) - baselines.min(axis=1)).max()), 0.0)

    def test_isodb_is_strong_conditional_not_simple_krug_artifact(self):
        compensation = self.load_json("isodb_compensation_summary.json")
        universality = self.load_json("isodb_universality_summary.json")
        self.assertEqual(compensation["primary"]["n_systems"], 1103)
        self.assertEqual(compensation["primary"]["n_dois"], 512)
        self.assertGreater(compensation["primary"]["r2"], 0.6)
        self.assertFalse(compensation["artifact_gate"]["artifact_consistent"])
        self.assertLessEqual(compensation["krug_null"]["p_null_r2_at_least_observed"], 0.001)
        self.assertLess(
            universality["pooled_vs_family_intercepts"]["p_doi_wild_cluster"],
            0.05,
        )
        self.assertGreater(
            universality["common_vs_family_specific_slopes"]["p_doi_wild_cluster"],
            0.05,
        )

    def test_fixed_ood_signal_does_not_become_an_improvement_claim(self):
        official = self.load_json("ood_decision_summary.json")
        row = next(
            edge
            for edge in official["primary_edges"]
            if edge["edge_id"]
            == "obelix_official_thermoelectric_zt_to_ionic_conductivity"
        )
        self.assertGreater(row["effect_fraction_to_first_hit_bootstrap_95"][0], 0)
        self.assertLess(row["relative_reduction_fraction_to_first_hit"], 0.25)
        self.assertLess(row["fraction_repeat_effects_positive"], 0.80)
        self.assertFalse(row["passes_improvement_gates"])
        self.assertEqual(row["decision_status"], "directional-only")

        hard = self.load_json("hard_ood_decision_summary.json")
        hard_row = next(
            edge
            for edge in hard["primary_edges"]
            if edge["edge_id"]
            == "hard_ood_obelix_thermoelectric_zt_to_ionic_conductivity"
        )
        self.assertEqual(hard_row["decision_status"], "exploratory-directional-only")
        self.assertFalse(hard_row["passes_improvement_gates"])

    def test_sequential_ood_discovery_fails_every_primary_effect_gate(self):
        summary = self.load_json("obelix_ood_discovery_summary.json")
        result = summary["primary_official_test_result"]
        self.assertEqual(result["seeds"], 100)
        self.assertEqual(result["mean_experiments_saved"], 0.25)
        self.assertLess(result["bootstrap_95"][0], 0)
        self.assertGreater(result["bootstrap_95"][1], 0)
        self.assertGreater(result["signflip_p_one_sided"], 0.05)
        self.assertTrue(all(not passed for passed in result["core_gates"].values()))
        self.assertFalse(result["passes_improvement_gates"])
        self.assertFalse(result["passes_rescue_crossing"])

    def test_random_reference_remains_a_policy_diagnostic(self):
        diagnostics = self.load_json("obelix_ood_discovery_diagnostics.json")
        self.assertTrue(diagnostics["primary_decision_unchanged"])
        random_reference = diagnostics["random_reference"]["official_test"]
        self.assertAlmostEqual(
            random_reference["empirical_random_mean"],
            random_reference["exact_censored_random_mean"],
            delta=0.5,
        )
        contrast = next(
            row
            for row in diagnostics["pairwise_diagnostics"]
            if row["scope"] == "official_test"
            and row["contrast"] == "thermoelectric_prior_minus_random_control"
        )
        self.assertGreater(contrast["bootstrap_95"][0], 0)
        self.assertIn("does not redefine frozen decision", contrast["status"])
        self.assertIn("does not establish random search", diagnostics["claim_guard"])

    def test_post_result_signal_anatomy_preserves_the_frozen_null(self):
        summary = self.load_json("neighbor_transfer_signal_summary.json")
        self.assertTrue(summary["analysis_status"].startswith("post-result"))
        self.assertIn("not a new positive OOD claim", summary["claim_guard"])
        official = {
            row["score"]: row
            for row in summary["score_summary"]
            if row["scope"] == "official_test"
        }
        random_rank = summary["uniform_random_full_ranking_reference"][
            "official_test"
        ]["exact_expected_first_hit_rank"]
        self.assertEqual(
            official["thermoelectric_prior_high"]["first_hit_rank_mean"], 3.0
        )
        self.assertLess(
            official["equal_positive_rank_fusion"]["first_hit_rank_mean"],
            random_rank,
        )
        self.assertGreater(official["target_mean"]["first_hit_rank_mean"], random_rank)
        self.assertGreater(official["ucb_beta_1"]["first_hit_rank_mean"], random_rank)
        uncertainty = next(
            row
            for row in summary["uncertainty_summary"]
            if row["scope"] == "official_test"
        )
        self.assertGreater(uncertainty["spread_absolute_error_spearman_mean"], 0)
        self.assertLess(uncertainty["spread_outcome_spearman_mean"], 0)

    def test_post_result_policy_benchmark_does_not_claim_source_attribution(self):
        audit = self.load_json("neighbor_transfer_policy_validation.json")
        self.assertEqual(
            audit["status"],
            "verified-exploratory-method-selection-not-claim-bearing",
        )
        decisions = audit["global_decisions"]
        self.assertTrue(decisions["target_mean_backbone_fails_random_in_both_scopes"])
        self.assertTrue(decisions["composition_novelty_beats_random_in_both_scopes"])
        self.assertTrue(decisions["source_static_beats_random_in_both_scopes"])
        self.assertFalse(
            decisions[
                "source_static_separates_from_catalysis_practically_in_both_scopes"
            ]
        )
        self.assertFalse(
            decisions["rank_fusion_increment_is_attributable_to_neighbor_borrowing"]
        )
        self.assertFalse(decisions["negative_transfer_safety_gate_passes"])
        self.assertTrue(decisions["independent_external_validation_required"])
        self.assertFalse(decisions["new_science_endpoint_tested"])
        fusion_vs_novelty = {
            row["scope"]: row
            for row in audit["posthoc_first_hit_vs_composition_novelty"]
            if row["left_policy"] == "target_source_novelty_rank_fusion"
        }
        self.assertLess(
            fusion_vs_novelty["official_test"][
                "mean_experiments_saved_by_left"
            ],
            0,
        )
        self.assertLess(
            fusion_vs_novelty["hard_ood_40pct"][
                "mean_experiments_saved_by_left"
            ],
            0,
        )
        self.assertTrue(
            all(
                row["unique_first_hit_counts_across_100_seeds"] == 1
                for row in audit["deterministic_static_policy_audit"]
            )
        )
        self.assertIn("cannot change", audit["claim_guard"])

    def test_primary_figure_marks_and_source_tables_are_auditable(self):
        result_dir = ROOT / "analysis" / "results"
        panel_b = pd.read_csv(result_dir / "figure_main_panel_b.csv")
        primary = panel_b[panel_b["is_primary"].astype(str).str.lower() == "true"]
        self.assertEqual(len(primary), 2)
        self.assertEqual(set(primary["evidence_layer"]), {"KIT", "CALiSol"})
        self.assertTrue((primary["lo"] <= primary["effect"]).all())
        self.assertTrue((primary["effect"] <= primary["hi"]).all())
        self.assertEqual(primary["effect"].nunique(), 2)

        expected_sources = {
            *(f"figure_main_panel_{letter}.csv" for letter in "abcd"),
            *(f"figure_ood_decision_panel_{letter}.csv" for letter in "abc"),
            *(f"figure_caltech_policy_panel_{letter}.csv" for letter in "abc"),
            *(f"figure_outcome_unseen_panel_{letter}.csv" for letter in "abcd"),
        }
        for name in expected_sources:
            self.assertTrue((result_dir / name).is_file(), name)

        bundle_list = (
            ROOT
            / "analysis"
            / "review_packages"
            / "claude"
            / "BUNDLE_FILE_LIST.txt"
        ).read_text(encoding="utf-8").splitlines()
        for name in expected_sources:
            self.assertIn(f"analysis/results/{name}", bundle_list)

    def test_manuscript_strategy_claim_is_assertive_and_bounded(self):
        manuscript = (ROOT / "analysis" / "MANUSCRIPT_DRAFT.md").read_text(
            encoding="utf-8"
        )
        normalized = " ".join(manuscript.split())
        self.assertTrue(
            manuscript.startswith(
                "# Artifact-gated mapping of selective knowledge borrowing across "
                "experimental materials domains"
            )
        )
        self.assertIn(
            "utility is sparse, directed and endpoint-specific rather than a general "
            "transfer law",
            normalized,
        )
        self.assertIn(
            "outcome-unseen evidence converts “selective” from a post-hoc qualifier "
            "into a tested result",
            normalized,
        )
        self.assertIn(
            "Prospective discovery acceleration and source-inspired new science remain "
            "a separate claim upgrade",
            normalized,
        )

        strategy_path = ROOT / "analysis" / "SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md"
        strategy = strategy_path.read_text(encoding="utf-8")
        for phrase in (
            "Declare the neighborhood",
            "Qualify source signal",
            "Match the borrowing mechanism",
            "Preserve complementary neighbors",
            "Require source-specific and safety comparisons",
            "Convert a ranked proposal into a scientific hypothesis",
        ):
            self.assertIn(phrase, strategy)

        bundle_list = (
            ROOT
            / "analysis"
            / "review_packages"
            / "claude"
            / "BUNDLE_FILE_LIST.txt"
        ).read_text(encoding="utf-8").splitlines()
        self.assertIn("analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md", bundle_list)

    def test_caltech_figure_surfaces_source_skill_and_small_count_denominators(self):
        result_dir = ROOT / "analysis" / "results"
        panel_a = pd.read_csv(result_dir / "figure_caltech_policy_panel_a.csv")
        quality = panel_a.dropna(subset=["source_oof_r2"]).set_index("source")
        self.assertAlmostEqual(
            quality.loc["obelix_same_property", "source_oof_r2"],
            0.0653768958615161,
        )
        self.assertEqual(
            quality["source_oof_r2"].idxmax(),
            "ocx_catalysis_control",
        )

        panel_c = pd.read_csv(result_dir / "figure_caltech_policy_panel_c.csv")
        neighbors = panel_c[panel_c["source_class"] == "real neighbor"]
        external = neighbors[neighbors["scope"] == "external_candidate"]
        hard_ood = neighbors[neighbors["scope"] == "hard_ood_40pct"]
        self.assertEqual(set(external["true_top_entities"]), {8})
        self.assertEqual(set(external["recall20_count"]), {2, 3})
        self.assertEqual(set(hard_ood["true_top_entities"]), {3})
        self.assertEqual(set(hard_ood["recall20_count"]), {3})

    def test_release_manifest_covers_designs_code_claims_and_current_counts(self):
        manifest = self.load_json("manifest.json")
        self.assertEqual(manifest["manifest_schema_version"], 5)
        self.assertGreaterEqual(len(manifest["frozen_designs"]), 4)
        self.assertGreaterEqual(len(manifest["analysis_scripts"]), 10)
        self.assertGreaterEqual(len(manifest["manuscript_documentation"]), 5)
        self.assertGreaterEqual(len(manifest["claim_artifacts"]), 10)
        release_paths = (
            manifest["frozen_designs"]
            + manifest["analysis_scripts"]
            + manifest["manuscript_documentation"]
            + manifest["claim_artifacts"]
        )
        for path in release_paths:
            self.assertIn(path, manifest["artifacts"])
            self.assertTrue((ROOT / path).is_file())
            self.assertGreater(manifest["artifacts"][path]["bytes"], 0)
        for required in [
            "analysis/obelix_ood_discovery_design.json",
            "analysis/run_obelix_ood_discovery.py",
            "analysis/results/obelix_ood_discovery_summary.json",
            "analysis/figures/ood_decision_borrowing.svg",
            "analysis/neighbor_transfer_policy_design.json",
            "analysis/results/neighbor_transfer_signal_summary.json",
            "analysis/audit_neighbor_transfer_policy_results.py",
            "analysis/NEIGHBOR_TRANSFER_POLICY_VALIDATION.md",
            "analysis/results/neighbor_transfer_policy_validation.json",
            "analysis/results/starrydata_reverse_VALIDATED.json",
            "analysis/results/tri_oer_VALIDATED.json",
            "analysis/results/outcome_unseen_multi_target_summary.json",
            "analysis/results/figure_outcome_unseen_panel_a.csv",
            "analysis/figures/outcome_unseen_validation.svg",
        ]:
            self.assertIn(required, release_paths)
        if DB.exists():
            with sqlite3.connect(DB) as connection:
                count = connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]
            self.assertEqual(manifest["database"]["measurements"], count)


if __name__ == "__main__":
    unittest.main()
