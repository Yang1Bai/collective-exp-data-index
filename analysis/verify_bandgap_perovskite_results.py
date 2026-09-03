"""Semantic verification for the band-gap-to-perovskite OOD benchmark."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import bandgap_borrowing_common as bg
import run_bandgap_external_source_skill as source_run
import run_bandgap_perovskite_pce_ood as pce_run


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
AUDIT = RESULTS / "bandgap_perovskite_pair_audit.json"
SOURCE_SUMMARY = RESULTS / "bandgap_external_source_skill_summary.json"
SOURCE_PREDICTIONS = RESULTS / "bandgap_external_source_predictions.csv"
SOURCE_SHUFFLES = RESULTS / "bandgap_external_source_shuffled_controls.csv"
SOURCE_FEATURES = RESULTS / "bandgap_external_donor_features.csv"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_close(
    actual: float,
    expected: float,
    label: str,
    *,
    atol: float = 1e-10,
) -> None:
    if not math.isclose(
        float(actual),
        float(expected),
        rel_tol=1e-9,
        abs_tol=atol,
    ):
        raise AssertionError(
            f"{label}: actual={actual!r}, expected={expected!r}"
        )


def verify_source() -> dict:
    audit = read_json(AUDIT)
    if audit.get("status") != "eligible-for-source-skill-benchmark":
        raise AssertionError("Source-pair audit is not eligible")
    if audit["recipient"]["csv_sha256"] != bg.sha256(bg.RECIPIENT_CSV):
        raise AssertionError("Recipient snapshot changed after audit")

    summary = read_json(SOURCE_SUMMARY)
    if summary.get("status") != "source-skill-gate-passed":
        raise AssertionError("Source-skill gate did not pass")
    hashes = {
        "donor_features_sha256": SOURCE_FEATURES,
        "predictions_sha256": SOURCE_PREDICTIONS,
        "shuffled_controls_sha256": SOURCE_SHUFFLES,
    }
    for field, path in hashes.items():
        if summary.get(field) != bg.sha256(path):
            raise AssertionError(f"Source output hash mismatch: {field}")

    predictions = pd.read_csv(SOURCE_PREDICTIONS)
    shuffles = pd.read_csv(SOURCE_SHUFFLES)
    features = pd.read_csv(SOURCE_FEATURES)
    expected_candidates = list(source_run.CANDIDATES)
    prediction_columns = {
        "experimental_text_mined": "experimental_bandgap_prediction",
        "calibrated_hse": "hse_bandgap_prediction_calibrated",
        "support_weighted_fusion": (
            "support_weighted_fusion_prediction"
        ),
        "retrieval_routed_fusion": (
            "retrieval_routed_fusion_prediction"
        ),
    }
    if len(predictions) != 205:
        raise AssertionError(
            f"Unexpected direct-validation rows: {len(predictions)}"
        )
    if predictions["composition_key"].nunique() != len(predictions):
        raise AssertionError("Source validation is not composition-unique")
    if len(features) != int(summary["donor_feature_rows"]):
        raise AssertionError("Donor-feature row count changed")
    if features["composition_key"].duplicated().any():
        raise AssertionError("Donor features are not composition-unique")
    if set(shuffles["candidate"]) != set(expected_candidates):
        raise AssertionError("Unexpected source shuffle candidates")
    counts = shuffles.groupby("candidate")["seed"].nunique().to_dict()
    if any(counts.get(name) != 99 for name in expected_candidates):
        raise AssertionError(f"Incomplete source shuffles: {counts}")

    truth = predictions["band_gap"].to_numpy(float)
    donor_median = float(summary["donor_median_baseline_eV"])
    if not 0.2 <= donor_median <= 6.0:
        raise AssertionError("Invalid source donor-median baseline")
    baseline = np.full(len(truth), donor_median, dtype=float)
    real = {}
    empirical = {}
    for candidate, column in prediction_columns.items():
        recalculated = source_run.metric_row(
            truth,
            predictions[column].to_numpy(float),
            baseline,
        )
        real[candidate] = recalculated
        for metric, value in recalculated.items():
            assert_close(
                value,
                summary["real"][candidate][metric],
                f"source {candidate} {metric}",
            )
        candidate_shuffles = shuffles.loc[
            shuffles["candidate"].eq(candidate), "rmse"
        ].to_numpy(float)
        empirical[candidate] = float(
            (
                1
                + np.sum(
                    candidate_shuffles
                    <= float(recalculated["rmse"])
                )
            )
            / (len(candidate_shuffles) + 1)
        )
    adjusted = source_run.holm_adjust(empirical)
    for candidate in expected_candidates:
        assert_close(
            empirical[candidate],
            summary["shuffled_controls"][candidate][
                "empirical_one_sided_p"
            ],
            f"source empirical p {candidate}",
        )
        assert_close(
            adjusted[candidate],
            summary["shuffled_controls"][candidate]["holm_adjusted_p"],
            f"source Holm p {candidate}",
        )
    passing = [
        name
        for name, passed in summary["candidate_pass"].items()
        if passed
    ]
    if passing != ["retrieval_routed_fusion"]:
        raise AssertionError(f"Unexpected source policies passed: {passing}")
    return {
        "status": "source-verified",
        "validation_compositions": len(predictions),
        "passing_source_policy": passing[0],
        "retrieval_rmse": real["retrieval_routed_fusion"]["rmse"],
        "retrieval_r2": real["retrieval_routed_fusion"]["r2"],
        "retrieval_holm_p": adjusted["retrieval_routed_fusion"],
    }


def verify_pce() -> dict:
    summary = read_json(pce_run.SUMMARY_JSON)
    if summary.get("status") != "verified-complete":
        raise AssertionError("PCE OOD summary is incomplete")
    expected_hashes = {
        "split_sha256": pce_run.SPLIT_JSON,
        "metrics_sha256": pce_run.METRICS_CSV,
        "predictions_sha256": pce_run.PREDICTIONS_CSV,
        "bootstrap_sha256": pce_run.BOOTSTRAP_CSV,
    }
    for field, path in expected_hashes.items():
        if summary.get(field) != bg.sha256(path):
            raise AssertionError(f"PCE output hash mismatch: {field}")
    if summary.get("design_sha256") != pce_run.EXPECTED_DESIGN_SHA256:
        raise AssertionError("PCE design hash mismatch")

    split = read_json(pce_run.SPLIT_JSON)
    metrics = pd.read_csv(pce_run.METRICS_CSV)
    predictions = pd.read_csv(pce_run.PREDICTIONS_CSV)
    bootstrap = pd.read_csv(pce_run.BOOTSTRAP_CSV)
    if len(metrics) != 550:
        raise AssertionError(f"Unexpected PCE metric rows: {len(metrics)}")
    expected_metric_counts = {
        ("100", name): 50
        for name in (*pce_run.POLICIES, pce_run.CONTROL)
    }
    expected_metric_counts.update(
        {
            ("300", name): 50
            for name in (*pce_run.POLICIES, pce_run.CONTROL)
        }
    )
    expected_metric_counts.update(
        {
            ("all", name): 10
            for name in (*pce_run.POLICIES, pce_run.CONTROL)
        }
    )
    actual_counts = (
        metrics.assign(budget=metrics["budget"].astype(str))
        .groupby(["budget", "policy"])
        .size()
        .to_dict()
    )
    if actual_counts != expected_metric_counts:
        raise AssertionError("PCE budget/policy draw counts changed")
    if len(bootstrap) != 40_000:
        raise AssertionError(
            f"Unexpected PCE bootstrap rows: {len(bootstrap)}"
        )
    if (
        bootstrap.groupby("policy")["replicate"].nunique().to_dict()
        != {name: 10_000 for name in pce_run.POLICIES}
    ):
        raise AssertionError("PCE bootstrap replicates are incomplete")

    target = bg.load_recipient()
    target = target[
        target["entry_id"].notna()
        & target["doi_norm"].ne("")
        & target["ions_valid"]
        & target["composition_key"].ne("")
        & target["pce"].between(0.0, 40.0, inclusive="both")
    ].copy()
    selected = set(split["selected_ood_families"])
    expected_test = target[target["site_family"].isin(selected)].copy()
    test_dois = set(expected_test["doi_norm"])
    expected_train = target[
        ~target["site_family"].isin(selected)
        & ~target["doi_norm"].isin(test_dois)
    ]
    if set(expected_train["doi_norm"]) & test_dois:
        raise AssertionError("DOI leakage in reconstructed PCE split")
    if set(expected_train["site_family"]) & selected:
        raise AssertionError("Family leakage in reconstructed PCE split")
    if set(predictions["entry_id"]) != set(expected_test["entry_id"]):
        raise AssertionError("PCE prediction rows do not equal frozen test")
    if len(predictions) != int(summary["test_rows"]):
        raise AssertionError("PCE test row count changed")

    truth = predictions["pce"].to_numpy(float)
    baseline = predictions["target_only_prediction"].to_numpy(float)
    groups = predictions["site_family"].astype(str).to_numpy()
    recalculated = {}
    raw_p = {}
    for policy in pce_run.POLICIES:
        values = predictions[f"{policy}_prediction"].to_numpy(float)
        item = pce_run.metric_row(truth, baseline, values, groups)
        recalculated[policy] = item
        for metric, value in item.items():
            assert_close(
                value,
                summary["primary_metrics"][policy][metric],
                f"PCE {policy} {metric}",
            )
        gains = bootstrap.loc[
            bootstrap["policy"].eq(policy), "relative_rmse_gain"
        ].to_numpy(float)
        ci = np.quantile(gains, [0.025, 0.975])
        pvalue = float((1 + np.sum(gains <= 0)) / (len(gains) + 1))
        raw_p[policy] = pvalue
        assert_close(
            ci[0],
            summary["primary_metrics"][policy]["bootstrap_ci95"][0],
            f"PCE {policy} CI lower",
        )
        assert_close(
            ci[1],
            summary["primary_metrics"][policy]["bootstrap_ci95"][1],
            f"PCE {policy} CI upper",
        )
        assert_close(
            pvalue,
            summary["primary_metrics"][policy][
                "bootstrap_one_sided_p"
            ],
            f"PCE {policy} bootstrap p",
        )
    adjusted = pce_run.holm_adjust(raw_p)
    for policy in pce_run.POLICIES:
        assert_close(
            adjusted[policy],
            summary["primary_metrics"][policy]["holm_adjusted_p"],
            f"PCE {policy} Holm p",
        )
    passing = [
        name
        for name, item in summary["decisions"].items()
        if item["passes"]
    ]
    if passing != summary["passing_policies"]:
        raise AssertionError("PCE passing-policy list is inconsistent")
    return {
        "status": "pce-verified",
        "train_rows": len(expected_train),
        "test_rows": len(expected_test),
        "test_families": len(selected),
        "passing_policies": passing,
        "primary_relative_rmse_gains": {
            policy: recalculated[policy]["relative_rmse_gain"]
            for policy in pce_run.POLICIES
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    output = {"source": verify_source()}
    if not args.source_only:
        output["pce"] = verify_pce()
        output["status"] = "verified-complete"
    else:
        output["status"] = "verified-source-only"
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
