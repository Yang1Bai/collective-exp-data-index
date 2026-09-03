"""Independently verify the completed Caltech external-policy result bundle."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .run_caltech_ionic_external_policy import (
        CONFIRMATORY_POLICIES,
        EXPLORATORY_POLICIES,
        PRIMARY_COMPARISONS,
        RESULTS,
        STATIC_SOURCE,
        contrast_table,
        fit_source_models,
        file_hash,
        gate_summary,
        load_target,
        composition_novelty,
        run_seed_scope,
        utility_table,
    )
except ImportError:
    from run_caltech_ionic_external_policy import (
        CONFIRMATORY_POLICIES,
        EXPLORATORY_POLICIES,
        PRIMARY_COMPARISONS,
        RESULTS,
        STATIC_SOURCE,
        contrast_table,
        fit_source_models,
        file_hash,
        gate_summary,
        load_target,
        composition_novelty,
        run_seed_scope,
        utility_table,
    )

HERE = Path(__file__).resolve().parent
PREFIX = "caltech_ionic_external_policy"
DESIGN_PATH = HERE / "caltech_ionic_external_policy_design.json"
SUMMARY_PATH = RESULTS / f"{PREFIX}_summary.json"
TRAJECTORY_PATH = RESULTS / f"{PREFIX}_trajectories.csv"
GATE_PATH = RESULTS / f"{PREFIX}_gates.csv"
UTILITY_PATH = RESULTS / f"{PREFIX}_utility.csv"
GATE_SUMMARY_PATH = RESULTS / f"{PREFIX}_gate_summary.csv"
SOURCE_QUALITY_PATH = RESULTS / f"{PREFIX}_source_quality.csv"
CONTRAST_PATH = RESULTS / f"{PREFIX}_contrasts.csv"
CHECKSUM_PATH = RESULTS / f"{PREFIX}_balam_checksums.sha256"
COMPLETE_PATH = RESULTS / f"{PREFIX}_COMPLETE.json"
VERIFIER_AMENDMENT_PATH = HERE / "CALTECH_IONIC_VERIFIER_AMENDMENT_4.md"
REMOTE_AMENDMENT_PATH = HERE / "CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md"
REMOTE_VERIFIED_PATH = RESULTS / f"{PREFIX}_VERIFIED.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checksums() -> None:
    for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(maxsplit=1)
        relative = relative.lstrip("* ")
        path = HERE.parent / relative
        if sha256(path) != digest:
            raise AssertionError(f"Checksum mismatch: {relative}")


def assert_frame_equal_numeric(
    observed: pd.DataFrame,
    expected: pd.DataFrame,
    keys: list[str],
    numeric: list[str],
) -> None:
    left = observed.sort_values(keys).reset_index(drop=True)
    right = expected.sort_values(keys).reset_index(drop=True)
    if len(left) != len(right):
        raise AssertionError(f"Frame row mismatch for {keys}: {len(left)} vs {len(right)}")
    for key in keys:
        if left[key].astype(str).tolist() != right[key].astype(str).tolist():
            raise AssertionError(f"Key mismatch: {key}")
    for column in numeric:
        if not np.allclose(
            pd.to_numeric(left[column], errors="coerce"),
            pd.to_numeric(right[column], errors="coerce"),
            rtol=1e-10,
            atol=1e-12,
            equal_nan=True,
        ):
            raise AssertionError(f"Numeric mismatch: {column}")


def parse_interval(value: object) -> list[float]:
    if isinstance(value, list):
        return [float(item) for item in value]
    return [float(item) for item in ast.literal_eval(str(value))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args()
    required = [
        SUMMARY_PATH,
        TRAJECTORY_PATH,
        GATE_PATH,
        UTILITY_PATH,
        GATE_SUMMARY_PATH,
        SOURCE_QUALITY_PATH,
        CONTRAST_PATH,
        CHECKSUM_PATH,
        COMPLETE_PATH,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing result files: {missing}")
    verify_checksums()
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    complete = json.loads(COMPLETE_PATH.read_text(encoding="utf-8"))
    if complete["status"] != "COMPLETE":
        raise AssertionError("Completion sentinel is not COMPLETE")
    if complete["summary_sha256"] != sha256(SUMMARY_PATH):
        raise AssertionError("Completion sentinel summary hash mismatch")
    if summary["status"] != "complete" or summary["seeds"] != 100 or summary["budget"] != 40:
        raise AssertionError("Formal campaign dimensions/status are wrong")

    trajectories = pd.read_csv(TRAJECTORY_PATH)
    gates = pd.read_csv(GATE_PATH)
    utilities = pd.read_csv(UTILITY_PATH)
    gate_summaries = pd.read_csv(GATE_SUMMARY_PATH)
    source_quality = pd.read_csv(SOURCE_QUALITY_PATH)
    contrasts = pd.read_csv(CONTRAST_PATH)
    policies = CONFIRMATORY_POLICIES + EXPLORATORY_POLICIES
    if len(trajectories) != 2 * 100 * len(policies) * 40:
        raise AssertionError("Trajectory row count is incomplete")
    if len(utilities) != 2 * 100 * len(policies):
        raise AssertionError("Utility row count is incomplete")
    if len(gates) != 2 * 100 * 40 * 23:
        raise AssertionError(f"Gate row count is incomplete: {len(gates)}")
    if len(contrasts) != 2 * len(PRIMARY_COMPARISONS):
        raise AssertionError("Contrast row count is incomplete")
    if set(source_quality["source"]) != {
        "obelix_same_property",
        "estm_transport_neighbor",
        "borg_mechanical_control",
        "ocx_catalysis_control",
    }:
        raise AssertionError("Source-quality coverage is incomplete")

    campaign_sizes = trajectories.groupby(["scope", "seed", "policy"]).size()
    if not (campaign_sizes == 40).all():
        raise AssertionError("At least one campaign does not contain 40 acquisitions")
    duplicate_choice = trajectories.groupby(["scope", "seed", "policy"])["chosen_index"].nunique()
    if not (duplicate_choice == 40).all():
        raise AssertionError("A campaign reacquires a target composition")
    if not trajectories["step"].between(1, 40).all():
        raise AssertionError("Invalid acquisition step")

    target, x, x_scaled = load_target()
    candidate = target.index[target["split"] == "candidate"].astype(int).tolist()
    development = target.index[target["split"] == "development"].astype(int).tolist()
    distances = composition_novelty(x_scaled[candidate], x_scaled[development])
    hard_n = int(math.ceil(0.40 * len(candidate)))
    hard = [candidate[index] for index in np.argsort(distances)[-hard_n:]]
    pools = {"external_candidate": candidate, "hard_ood_40pct": hard}
    for scope, pool in pools.items():
        chosen = set(
            trajectories.loc[trajectories["scope"] == scope, "chosen_index"].astype(int)
        )
        if not chosen.issubset(set(pool)):
            raise AssertionError(f"{scope}: acquired an entity outside the frozen pool")

    recomputed_utility = utility_table(trajectories, target, pools, 40)
    assert_frame_equal_numeric(
        utilities,
        recomputed_utility,
        ["scope", "seed", "policy"],
        [
            "auc20",
            "first_hit",
            "recall_at_10",
            "recall_at_20",
            "recall_at_40",
            "best_y_at_10",
            "best_y_at_20",
            "best_y_at_40",
            "regret_at_10",
            "regret_at_20",
            "regret_at_40",
        ],
    )
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    recomputed_contrasts = contrast_table(recomputed_utility, design)
    for frame in (contrasts, recomputed_contrasts):
        frame["auc20_ci_lo"] = frame["auc20_gain_ci95"].map(lambda value: parse_interval(value)[0])
        frame["auc20_ci_hi"] = frame["auc20_gain_ci95"].map(lambda value: parse_interval(value)[1])
        frame["first_ci_lo"] = frame["first_hit_saved_ci95"].map(lambda value: parse_interval(value)[0])
        frame["first_ci_hi"] = frame["first_hit_saved_ci95"].map(lambda value: parse_interval(value)[1])
    assert_frame_equal_numeric(
        contrasts,
        recomputed_contrasts,
        ["scope", "left_policy", "right_policy"],
        [
            "left_auc20_mean",
            "right_auc20_mean",
            "mean_auc20_gain",
            "relative_auc20_gain",
            "auc20_ci_lo",
            "auc20_ci_hi",
            "fraction_campaigns_improved",
            "signflip_p_one_sided",
            "holm_p",
            "left_first_hit_mean",
            "right_first_hit_mean",
            "mean_first_hit_saved",
            "first_ci_lo",
            "first_ci_hi",
            "left_recall_at_20_mean",
        ],
    )
    recomputed_gate_summary = gate_summary(gates)
    assert_frame_equal_numeric(
        gate_summaries,
        recomputed_gate_summary,
        ["scope", "policy", "source"],
        [
            "evaluated_steps",
            "admission_rate",
            "selected_rate",
            "mean_weight",
            "median_weight",
            "median_cv_gain",
        ],
    )
    if args.portable:
        if not REMOTE_VERIFIED_PATH.exists():
            raise FileNotFoundError("Missing same-environment VERIFIED sentinel")
        remote_verified = json.loads(REMOTE_VERIFIED_PATH.read_text(encoding="utf-8"))
        if remote_verified["status"] != "VERIFIED":
            raise AssertionError("Remote verification sentinel did not pass")
        expected_hashes = {
            "verifier_sha256": sha256(Path(__file__).resolve()),
            "verifier_amendment_sha256": sha256(VERIFIER_AMENDMENT_PATH),
            "remote_amendment_sha256": sha256(REMOTE_AMENDMENT_PATH),
            "checksums_sha256": sha256(CHECKSUM_PATH),
            "summary_sha256": sha256(SUMMARY_PATH),
        }
        for key, value in expected_hashes.items():
            if remote_verified[key] != value:
                raise AssertionError(f"Remote verification hash mismatch: {key}")
    else:
        recomputed_sources, recomputed_source_quality = fit_source_models(target, x)
        assert_frame_equal_numeric(
            source_quality,
            recomputed_source_quality,
            ["source"],
            ["entities", "groups", "oof_r2", "oof_rmse", "oof_spearman"],
        )
        recomputed_static_rows: list[dict] = []
        for scope, pool in pools.items():
            for seed in range(100):
                static_trajectory, _ = run_seed_scope(
                    scope=scope,
                    seed=seed,
                    policies=list(STATIC_SOURCE),
                    target=target,
                    x=x,
                    x_scaled=x_scaled,
                    base_sources=recomputed_sources,
                    candidates=pool,
                    budget=40,
                    initial_n=30,
                )
                recomputed_static_rows.extend(static_trajectory)
        observed_static = trajectories[trajectories["policy"].isin(STATIC_SOURCE)].copy()
        recomputed_static = pd.DataFrame(recomputed_static_rows)
        assert_frame_equal_numeric(
            observed_static,
            recomputed_static,
            ["scope", "seed", "policy", "step", "chosen_key"],
            [
                "chosen_index",
                "chosen_y",
                "is_true_top5_hit",
                "acquisition_score",
                "composition_novelty",
                "initial_target_n",
            ],
        )

    print(
        json.dumps(
            {
                "status": "verified-complete",
                "verification_mode": "portable-after-remote" if args.portable else "same-environment-full",
                "design_sha256": summary["design_sha256"],
                "implementation_sha256": summary["implementation_sha256"],
                "verifier_amendment_sha256": summary.get(
                    "verifier_amendment_sha256", sha256(VERIFIER_AMENDMENT_PATH)
                ),
                "trajectory_rows": len(trajectories),
                "gate_rows": len(gates),
                "utility_rows": len(utilities),
                "contrasts": len(contrasts),
                "claim_guard": summary["claim_guard"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
