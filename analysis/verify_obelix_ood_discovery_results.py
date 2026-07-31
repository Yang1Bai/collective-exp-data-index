"""Verify completeness and provenance of the frozen OBELiX campaign outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
RESULTS = ANALYSIS / "results"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_checksums(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        relative = relative.lstrip("* ")
        artifact = ROOT / Path(relative)
        observed = sha256_file(artifact)
        if observed != expected:
            raise AssertionError(
                f"Checksum mismatch for {relative}: {observed} != {expected}"
            )


def main() -> None:
    design_path = ANALYSIS / "obelix_ood_discovery_design.json"
    input_path = RESULTS / "obelix_ood_discovery_input.npz"
    input_meta_path = RESULTS / "obelix_ood_discovery_input_meta.json"
    summary_path = RESULTS / "obelix_ood_discovery_summary.json"
    required = [
        RESULTS / "obelix_ood_discovery_reach.csv",
        RESULTS / "obelix_ood_discovery_trajectories.csv",
        RESULTS / "obelix_ood_discovery_edges.csv",
        RESULTS / "obelix_ood_discovery_bootstrap.csv",
        summary_path,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing campaign artifacts: {missing}")

    input_meta = json.loads(input_meta_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    design_hash = sha256_file(design_path)
    input_hash = sha256_file(input_path)
    if summary["design_sha256"] != design_hash:
        raise AssertionError("Summary design hash does not match frozen design")
    if summary["input_sha256"] != input_hash:
        raise AssertionError("Summary input hash does not match frozen NPZ")
    if input_meta["design_sha256"] != design_hash:
        raise AssertionError("Input manifest design hash does not match frozen design")
    if input_meta["input_sha256"] != input_hash:
        raise AssertionError("Input manifest does not match frozen NPZ")
    if summary["candidate_pools"] != {"official_test": 110, "hard_ood_40pct": 44}:
        raise AssertionError("Candidate-pool counts changed")
    if any(summary["source_target_exact_overlaps"].values()):
        raise AssertionError("A source-target exact-composition overlap is nonzero")

    reaches = pd.read_csv(required[0])
    edges = pd.read_csv(required[2])
    bootstrap = pd.read_csv(required[3])
    expected_reaches = 2 * (100 * 6 + 40 * 2)
    if len(reaches) != expected_reaches:
        raise AssertionError(
            f"Expected {expected_reaches} reach rows, found {len(reaches)}"
        )
    expected_groups = {
        (scope, model, strategy): seeds
        for scope in ("official_test", "hard_ood_40pct")
        for model, seeds, strategies in (
            (
                "extra-trees-primary",
                100,
                (
                    "target_only",
                    "thermoelectric_prior",
                    "alloy_control",
                    "catalysis_control",
                    "shuffled_thermoelectric_control",
                    "random_control",
                ),
            ),
            (
                "random-forest-sensitivity",
                40,
                ("target_only", "thermoelectric_prior"),
            ),
        )
        for strategy in strategies
    }
    observed_groups = reaches.groupby(
        ["scope", "model_family", "strategy"]
    )["seed"].nunique().to_dict()
    if observed_groups != expected_groups:
        raise AssertionError("Campaign seed/strategy coverage is incomplete")
    if len(edges) != 12:
        raise AssertionError(f"Expected 12 inference rows, found {len(edges)}")
    if len(bootstrap) != 12 * 5000:
        raise AssertionError(
            f"Expected {12 * 5000} bootstrap rows, found {len(bootstrap)}"
        )

    verify_checksums(RESULTS / "obelix_ood_discovery_balam_checksums.sha256")
    sentinel_path = RESULTS / "obelix_ood_discovery_COMPLETE.json"
    if sentinel_path.exists():
        sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
        if sentinel.get("status") != "COMPLETE":
            raise AssertionError("Balam completion sentinel is not COMPLETE")
        if sentinel.get("summary_sha256") != sha256_file(summary_path):
            raise AssertionError("Balam completion sentinel summary hash changed")
    primary = summary["primary_official_test_result"]
    print(
        json.dumps(
            {
                "status": "verified-complete",
                "decision_status": primary["decision_status"],
                "mean_experiments_saved": primary["mean_experiments_saved"],
                "bootstrap_95": primary["bootstrap_95"],
                "passes_improvement_gates": primary[
                    "passes_improvement_gates"
                ],
                "passes_rescue_crossing": primary["passes_rescue_crossing"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
