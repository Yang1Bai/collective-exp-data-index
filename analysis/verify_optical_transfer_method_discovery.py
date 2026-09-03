"""Verify the large development-only transfer-method discovery result."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_optical_transfer_method_discovery as discovery

HERE = Path(__file__).resolve().parent
DESIGN_PATH = HERE / "optical_photocatalysis_borrowing_design.json"
CONFIG_PATH = HERE / "optical_transfer_method_discovery_config.json"
IMPLEMENTATION_PATH = HERE / "run_optical_transfer_method_discovery.py"
AUDIT_PATH = HERE / "results" / "optical_photocatalysis_pair_audit.json"
GLOBAL_SUMMARY_PATH = (
    HERE / "results" / "optical_photocatalysis_source_skill.json"
)
STATE_SUMMARY_PATH = (
    HERE / "results" / "optical_state_matched_donor_summary.json"
)
STATE_VERIFIED_PATH = (
    HERE / "results" / "optical_state_matched_donor_VERIFIED.json"
)
DRAW_PATH = HERE / "results" / "optical_transfer_method_discovery_draws.csv"
DRAW_MANIFEST_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_draws_manifest.json"
)
REGISTRY_PATH = HERE / "results" / "optical_transfer_method_registry.json"
METRICS_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_metrics.csv"
)
CANDIDATE_SUMMARY_PATH = (
    HERE / "results" / "optical_transfer_method_candidate_summary.csv"
)
SUMMARY_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_summary.json"
)
VERIFIED_PATH = (
    HERE / "results" / "optical_transfer_method_discovery_VERIFIED.json"
)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    registry_payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    metrics = pd.read_csv(METRICS_PATH)
    candidate_summary = pd.read_csv(CANDIDATE_SUMMARY_PATH)
    expected_hashes = {
        "design_sha256": file_hash(DESIGN_PATH),
        "method_config_sha256": file_hash(CONFIG_PATH),
        "implementation_sha256": file_hash(IMPLEMENTATION_PATH),
        "pair_audit_sha256": file_hash(AUDIT_PATH),
        "global_source_summary_sha256": file_hash(GLOBAL_SUMMARY_PATH),
        "state_source_summary_sha256": file_hash(STATE_SUMMARY_PATH),
        "state_source_verified_sha256": file_hash(STATE_VERIFIED_PATH),
        "draw_manifest_sha256": file_hash(DRAW_MANIFEST_PATH),
        "draw_sha256": file_hash(DRAW_PATH),
        "registry_sha256": file_hash(REGISTRY_PATH),
        "metrics_sha256": file_hash(METRICS_PATH),
        "candidate_summary_sha256": file_hash(CANDIDATE_SUMMARY_PATH),
    }
    for field, expected in expected_hashes.items():
        if summary[field] != expected:
            raise AssertionError(f"Hash mismatch: {field}")
    methods = [str(item["method"]) for item in registry_payload["methods"]]
    if len(methods) != len(set(methods)):
        raise AssertionError("Duplicate registered method")
    if set(metrics["method"]) != set(methods):
        raise AssertionError("Metrics do not cover the complete registry")
    budgets = {
        int(value) for value in config["development_design"]["label_budgets"]
    }
    repeats = int(config["development_design"]["scaffold_draws_per_budget"])
    if set(metrics["budget"].astype(int)) != budgets:
        raise AssertionError("Budget set changed")
    for budget in budgets:
        rows = metrics[metrics["budget"] == budget]
        if rows["repeat"].nunique() != repeats:
            raise AssertionError(f"Repeat count changed at {budget}")
        if len(rows) != repeats * len(methods):
            raise AssertionError(f"Metric row count changed at {budget}")
    if metrics[["rmse", "mae", "r2"]].isna().any().any():
        raise AssertionError("Missing core metric")

    recomputed_candidates, recomputed_selected = discovery.summarize_candidates(
        metrics, registry_payload["methods"], config
    )
    left = candidate_summary.sort_values("method").reset_index(drop=True)
    right = recomputed_candidates.sort_values("method").reset_index(drop=True)
    if list(left.columns) != list(right.columns):
        raise AssertionError("Candidate summary columns changed")
    for column in left.columns:
        if pd.api.types.is_numeric_dtype(right[column]):
            if not np.allclose(
                pd.to_numeric(left[column]),
                pd.to_numeric(right[column]),
                atol=1e-12,
                equal_nan=True,
            ):
                raise AssertionError(f"Candidate numeric mismatch: {column}")
        elif not left[column].astype(str).equals(right[column].astype(str)):
            raise AssertionError(f"Candidate text mismatch: {column}")

    reported_selected = summary["selected_strategy"]
    if (reported_selected is None) != (recomputed_selected is None):
        raise AssertionError("Selected-strategy null status mismatch")
    if recomputed_selected is not None:
        if str(reported_selected["method"]) != str(recomputed_selected["method"]):
            raise AssertionError("Selected strategy changed")
    expected_status = (
        "development-discovery-candidate-selected"
        if recomputed_selected is not None
        else "development-discovery-abstained"
    )
    if summary["status"] != expected_status:
        raise AssertionError("Discovery status mismatch")

    verified = {
        "status": "verified-complete",
        **expected_hashes,
        "summary_sha256": file_hash(SUMMARY_PATH),
        "method_count": len(methods),
        "metric_rows": int(len(metrics)),
        "eligible_candidate_count": int(
            recomputed_candidates["eligible_for_blind_freeze"].sum()
        ),
        "selected_strategy": recomputed_selected,
        "blind_release_permitted": recomputed_selected is not None,
        "inference_guard": (
            "Repeated draws and forest seeds are computational sensitivity "
            "analyses, not independent experimental samples. No discovery-stage "
            "p value establishes transfer."
        ),
    }
    VERIFIED_PATH.write_text(
        json.dumps(verified, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verified, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
