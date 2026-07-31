"""Independently verify the multi-target OOD borrowing result package."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"
DESIGN_PATH = HERE / "multi_target_ood_borrowing_design.json"
PARENT_DESIGN_PATH = HERE / "knowledge_map_design.json"
PARENT_RUNNER_PATH = HERE / "run_knowledge_map.py"
DB_PATH = ROOT / "data" / "collective.sqlite"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def paths_for(smoke: bool) -> dict[str, Path]:
    stem = "multi_target_ood_smoke" if smoke else "multi_target_ood"
    return {
        "strata": RESULTS / f"{stem}_strata.csv",
        "source_quality": RESULTS / f"{stem}_source_quality.csv",
        "metrics": RESULTS / f"{stem}_metrics.csv",
        "contrasts": RESULTS / f"{stem}_contrasts.csv",
        "group_errors": RESULTS / f"{stem}_group_errors.csv",
        "edge_summary": RESULTS / f"{stem}_edge_summary.csv",
        "target_summary": RESULTS / f"{stem}_target_summary.csv",
        "summary": RESULTS / f"{stem}_summary.json",
        "complete": RESULTS / f"{stem}_COMPLETE.json",
        "verified": RESULTS / f"{stem}_VERIFIED.json",
    }


def require_unique(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    if frame.duplicated(columns).any():
        duplicate = frame.loc[frame.duplicated(columns, keep=False), columns].head()
        raise AssertionError(f"Duplicate {label} keys:\n{duplicate}")


def assert_close(
    actual: np.ndarray | pd.Series,
    expected: np.ndarray | pd.Series,
    label: str,
    *,
    rtol: float = 1e-9,
    atol: float = 1e-10,
) -> None:
    actual_array = np.asarray(actual, dtype=float)
    expected_array = np.asarray(expected, dtype=float)
    if not np.allclose(actual_array, expected_array, rtol=rtol, atol=atol, equal_nan=True):
        maximum = float(np.nanmax(np.abs(actual_array - expected_array)))
        raise AssertionError(f"Numeric mismatch for {label}; maximum absolute error {maximum}")


def holm_adjust(pvalues: np.ndarray) -> np.ndarray:
    values = np.asarray(pvalues, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    total = len(values)
    for rank, index in enumerate(order):
        candidate = min(1.0, (total - rank) * values[index])
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def recompute_classification(row: pd.Series, gate: dict[str, Any]) -> str:
    if bool(row["is_designated_primary"]):
        criteria = [
            row["gain_ood_mean"] >= gate["mean_ood_relative_rmse_gain_minimum"],
            row["gain_ood_ci_lo"] > gate["hierarchical_ood_gain_ci_lower_above"],
            row["aug_ood_r2_mean"] > gate["mean_augmented_ood_r2_above"],
            row["positive_ood_repeat_fraction"]
            >= gate["positive_ood_gain_repeat_fraction_minimum"],
            row["gain_specific_ci_lo"]
            > gate["hierarchical_gain_specific_ci_lower_above"],
            row["primary_minus_wrong_ci_lo"]
            > gate["primary_minus_wrong_ood_gain_ci_lower_above"],
            row["primary_minus_shuffled_ci_lo"]
            > gate["primary_minus_shuffled_ood_gain_ci_lower_above"],
            row["positive_ood_learners"]
            >= gate["learners_with_positive_mean_ood_gain_minimum"],
            row["holm_p"] < gate["holm_adjusted_one_sided_p_below"],
            row["post_exclusion_overlap"]
            == gate["post_exclusion_identity_overlap_equals"],
        ]
        if all(bool(value) for value in criteria):
            return "ood-repair-gate-passed"
    if row["gain_ood_ci_lo"] > 0 and row["gain_ood_mean"] > 0:
        return "ood-improvement-not-specific"
    if row["gain_ood_mean"] > 0:
        return "directional-ood-improvement"
    if row["gain_ood_mean"] < 0 and row["gain_ood_ci_hi"] < 0:
        return "harmful"
    return "unresolved"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    paths = paths_for(args.smoke)
    for key, path in paths.items():
        if key == "verified":
            continue
        if not path.exists():
            raise FileNotFoundError(path)

    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    complete = json.loads(paths["complete"].read_text(encoding="utf-8"))
    expected_mode = "smoke" if args.smoke else "formal"
    if summary["mode"] != expected_mode:
        raise AssertionError(f"Expected {expected_mode}, found {summary['mode']}")
    if complete["status"] != summary["status"]:
        raise AssertionError("COMPLETE and summary status disagree")
    if summary["design_sha256"] != sha256_file(DESIGN_PATH):
        raise AssertionError("Design hash mismatch")
    provenance_files = {
        "parent_design_sha256": PARENT_DESIGN_PATH,
        "data_snapshot_sha256": DB_PATH,
        "parent_runner_sha256_at_freeze": PARENT_RUNNER_PATH,
    }
    for key, path in provenance_files.items():
        actual = sha256_file(path)
        if actual != design["provenance"][key] or actual != summary[key]:
            raise AssertionError(f"Frozen provenance mismatch for {key}")

    for filename, expected_hash in complete["output_hashes"].items():
        path = RESULTS / filename
        if not path.exists() or sha256_file(path) != expected_hash:
            raise AssertionError(f"Output hash mismatch for {filename}")

    strata = pd.read_csv(paths["strata"])
    source_quality = pd.read_csv(paths["source_quality"])
    metrics = pd.read_csv(paths["metrics"])
    contrasts = pd.read_csv(paths["contrasts"])
    group_errors = pd.read_csv(paths["group_errors"])
    edges = pd.read_csv(paths["edge_summary"])
    targets = pd.read_csv(paths["target_summary"])

    for key, frame in (
        ("strata", strata),
        ("source_quality", source_quality),
        ("metrics", metrics),
        ("contrasts", contrasts),
        ("group_errors", group_errors),
        ("edge_summary", edges),
        ("target_summary", targets),
    ):
        if len(frame) != int(summary["rows"][key]):
            raise AssertionError(f"Row count mismatch for {key}")

    included = design["eligibility"]["included_targets"]
    if set(strata["target"]) != set(included):
        raise AssertionError("Strata target set differs from frozen eligibility")
    if "value" in strata.columns or "outcome" in strata.columns:
        raise AssertionError("OOD strata improperly contain outcomes")
    require_unique(strata, ["target", "entity_index"], "stratum entity")
    if strata.groupby(["target", "group"])["scope"].nunique().max() != 1:
        raise AssertionError("An intact evaluation group crosses OOD scopes")
    for target, frame in strata.groupby("target"):
        counts = frame.groupby("scope")["group"].nunique()
        if set(counts.index) != {"q1", "q2", "q3", "q4"}:
            raise AssertionError(f"Missing quartile for {target}")
        if counts.max() - counts.min() > 1:
            raise AssertionError(f"Quartiles are not group balanced for {target}")
        medians = frame.groupby("scope")["group_distance"].median().reindex(
            ["q1", "q2", "q3", "q4"]
        )
        if not np.all(np.diff(medians.to_numpy(float)) >= -1e-12):
            raise AssertionError(f"Distance quartiles are not ordered for {target}")

    require_unique(source_quality, ["target", "source"], "source quality")
    if len(source_quality) != 48:
        raise AssertionError(f"Expected 48 source features, found {len(source_quality)}")
    if int(source_quality["is_shuffled_control"].sum()) != 8:
        raise AssertionError("Expected eight shuffled controls")
    if (source_quality["post_exclusion_overlap"] != 0).any():
        raise AssertionError("Post-exclusion identity leakage detected")
    for target, frame in source_quality.groupby("target"):
        if len(frame) != 6:
            raise AssertionError(f"Expected six evaluated features for {target}")
        if int(frame["is_shuffled_control"].sum()) != 1:
            raise AssertionError(f"Expected one shuffled control for {target}")

    repeats = int(summary["repeats"])
    learners = design["learners"]
    learner_names = [learners["primary"], *learners["sensitivities"]]
    expected_metrics = len(included) * 6 * len(learner_names) * repeats * 3
    expected_contrasts = len(included) * 6 * len(learner_names) * repeats
    if len(metrics) != expected_metrics or len(contrasts) != expected_contrasts:
        raise AssertionError("Formal metric/contrast row count is inconsistent")
    require_unique(
        metrics, ["target", "source", "learner", "repeat", "scope"], "metric"
    )
    require_unique(
        contrasts, ["target", "source", "learner", "repeat"], "contrast"
    )
    if set(metrics["scope"]) != {"all", "q1", "q4"}:
        raise AssertionError("Unexpected metric scopes")
    if set(metrics["learner"]) != set(learner_names):
        raise AssertionError("Unexpected learner set")
    finite_columns = [
        "base_r2",
        "aug_r2",
        "delta_r2",
        "base_rmse",
        "aug_rmse",
        "relative_rmse_gain",
        "delta_mae",
    ]
    if not np.isfinite(metrics[finite_columns].to_numpy(float)).all():
        raise AssertionError("Non-finite primary metric value")
    if (metrics[["base_rmse", "aug_rmse"]] <= 0).any().any():
        raise AssertionError("Non-positive RMSE")

    pivot = metrics.pivot(
        index=["target", "source", "learner", "repeat"],
        columns="scope",
        values="relative_rmse_gain",
    ).reset_index()
    merged = contrasts.merge(
        pivot, on=["target", "source", "learner", "repeat"], validate="one_to_one"
    )
    assert_close(merged["gain_all"], merged["all"], "all-scope gain")
    assert_close(merged["gain_id"], merged["q1"], "ID gain")
    assert_close(merged["gain_ood"], merged["q4"], "OOD gain")
    assert_close(
        merged["gain_specific"],
        merged["q4"] - merged["q1"],
        "OOD-minus-ID gain",
    )

    require_unique(
        group_errors,
        ["target", "source", "learner", "repeat", "scope", "group"],
        "group error",
    )
    if set(group_errors["learner"]) != {learners["primary"]}:
        raise AssertionError("Group errors must represent the primary learner only")
    if set(group_errors["scope"]) != {"q1", "q4"}:
        raise AssertionError("Group errors must represent Q1 and Q4 only")
    expected_primary_pairs = {
        (target, spec["primary_source"]) for target, spec in design["targets"].items()
    }
    if set(zip(group_errors["target"], group_errors["source"])) != expected_primary_pairs:
        raise AssertionError("Group errors are not limited to designated primary edges")
    aggregated = (
        group_errors.groupby(
            ["target", "source", "learner", "repeat", "scope"], as_index=False
        )
        .agg(base_sse=("base_sse", "sum"), aug_sse=("aug_sse", "sum"), n=("n", "sum"))
    )
    aggregated["base_rmse_rebuilt"] = np.sqrt(
        aggregated["base_sse"] / aggregated["n"]
    )
    aggregated["aug_rmse_rebuilt"] = np.sqrt(
        aggregated["aug_sse"] / aggregated["n"]
    )
    metric_primary = metrics.merge(
        source_quality[["target", "source"]],
        on=["target", "source"],
        how="inner",
    )
    metric_primary = metric_primary[
        metric_primary.apply(
            lambda row: row["source"]
            == design["targets"][row["target"]]["primary_source"],
            axis=1,
        )
        & (metric_primary["learner"] == learners["primary"])
        & metric_primary["scope"].isin(["q1", "q4"])
    ]
    rebuilt = metric_primary.merge(
        aggregated,
        on=["target", "source", "learner", "repeat", "scope"],
        validate="one_to_one",
    )
    assert_close(rebuilt["base_rmse"], rebuilt["base_rmse_rebuilt"], "grouped base RMSE")
    assert_close(rebuilt["aug_rmse"], rebuilt["aug_rmse_rebuilt"], "grouped augmented RMSE")

    require_unique(edges, ["target", "source"], "edge summary")
    if len(edges) != 48 or int(edges["is_designated_primary"].sum()) != 8:
        raise AssertionError("Edge summary does not contain 48 edges and eight primaries")
    means = (
        contrasts[contrasts["learner"] == learners["primary"]]
        .groupby(["target", "source"], as_index=False)
        .agg(
            gain_all_rebuilt=("gain_all", "mean"),
            gain_id_rebuilt=("gain_id", "mean"),
            gain_ood_rebuilt=("gain_ood", "mean"),
            gain_specific_rebuilt=("gain_specific", "mean"),
            base_ood_r2_rebuilt=("base_ood_r2", "mean"),
            aug_ood_r2_rebuilt=("aug_ood_r2", "mean"),
            positive_fraction_rebuilt=("gain_ood", lambda value: float((value > 0).mean())),
        )
    )
    checked = edges.merge(means, on=["target", "source"], validate="one_to_one")
    for reported, rebuilt_name in (
        ("gain_all_mean", "gain_all_rebuilt"),
        ("gain_id_mean", "gain_id_rebuilt"),
        ("gain_ood_mean", "gain_ood_rebuilt"),
        ("gain_specific_mean", "gain_specific_rebuilt"),
        ("base_ood_r2_mean", "base_ood_r2_rebuilt"),
        ("aug_ood_r2_mean", "aug_ood_r2_rebuilt"),
        ("positive_ood_repeat_fraction", "positive_fraction_rebuilt"),
    ):
        assert_close(checked[reported], checked[rebuilt_name], reported)

    primary_edges = edges[edges["is_designated_primary"]].copy()
    assert_close(
        primary_edges["holm_p"],
        holm_adjust(primary_edges["one_sided_sign_flip_p"].to_numpy(float)),
        "Holm adjusted P values",
    )
    expected_classification = edges.apply(
        recompute_classification, axis=1, gate=design["edge_gate"]
    )
    if not np.array_equal(expected_classification.to_numpy(), edges["classification"].to_numpy()):
        raise AssertionError("A frozen edge classification was calculated incorrectly")
    expected_target_columns = set(targets["target"])
    if expected_target_columns != set(included) or len(targets) != 8:
        raise AssertionError("Target summary does not contain all eight recipients")

    passed_clusters = int(
        primary_edges.loc[
            primary_edges["classification"] == "ood-repair-gate-passed",
            "programme_cluster",
        ].nunique()
    )
    if (
        passed_clusters
        != summary["programme_inference"]["programme_clusters_with_full_pass"]
    ):
        raise AssertionError("Programme pass count mismatch")
    cross_database = primary_edges[
        primary_edges["primary_edge_class"] == "cross-database-neighbor"
    ]
    cross_passes = int(
        (cross_database["classification"] == "ood-repair-gate-passed").sum()
    )
    if (
        len(cross_database)
        != summary["cross_database_inference"]["designated_edges"]
        or cross_passes != summary["cross_database_inference"]["full_passes"]
    ):
        raise AssertionError("Cross-database summary mismatch")
    selective_expected = bool(
        passed_clusters
        >= design["cohort_gate"][
            "minimum_independent_programme_clusters_with_full_primary_edge_pass"
        ]
        and summary["programme_inference"]["ci95"][0]
        > design["cohort_gate"][
            "programme_bootstrap_mean_primary_ood_gain_ci_lower_above"
        ]
    )
    if (
        selective_expected
        != summary["programme_inference"][
            "selective_ood_repair_cohort_gate_passed"
        ]
    ):
        raise AssertionError("Selective cohort gate mismatch")
    cross_expected = bool(
        selective_expected
        and cross_passes
        >= design["cohort_gate"]["cross_database_upgrade_minimum_full_passes"]
    )
    if (
        cross_expected
        != summary["cross_database_inference"]["cross_database_upgrade_gate_passed"]
    ):
        raise AssertionError("Cross-database upgrade gate mismatch")

    verified = {
        "status": "verified-complete",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "mode": expected_mode,
        "design_sha256": sha256_file(DESIGN_PATH),
        "summary_sha256": sha256_file(paths["summary"]),
        "complete_sha256": sha256_file(paths["complete"]),
        "targets": len(included),
        "real_edges": 40,
        "shuffled_controls": 8,
        "metric_rows": len(metrics),
        "contrast_rows": len(contrasts),
        "group_error_rows": len(group_errors),
        "claim_guard": design["claim_guard"],
    }
    paths["verified"].write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
