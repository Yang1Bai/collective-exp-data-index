from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))

import run_optical_transfer_method_discovery as discovery  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_discovery_draws_are_current_and_outcome_independent() -> None:
    config_path = ANALYSIS / "optical_transfer_method_discovery_config.json"
    manifest_path = (
        ANALYSIS
        / "results"
        / "optical_transfer_method_discovery_draws_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["method_config_sha256"] == sha256(config_path)
    assert manifest["outcome_access"].startswith("No recipient HER")
    assert manifest["repeats_per_budget"] == 300
    assert manifest["budgets"] == [30, 60, 120]


def test_rank_transform_uses_training_reference_only() -> None:
    training = np.asarray([[1.0], [2.0], [3.0]])
    evaluation = np.asarray([[0.0], [2.5], [10.0]])
    train_rank, eval_rank = discovery.rank_from_training(training, evaluation)
    assert np.allclose(train_rank.ravel(), [0.25, 0.5, 0.75])
    assert np.allclose(eval_rank.ravel(), [0.0, 0.5, 0.75])


def test_registry_has_unique_candidates_and_matched_controls() -> None:
    frame = pd.DataFrame(
        {
            "pred_absorption_nm": [1.0, 2.0],
            "unc_absorption_nm": [0.1, 0.2],
            "max_similarity_to_retained_donor": [0.5, 0.6],
        }
    )
    blocks = {
        "global_all_environment": {
            "frame": frame,
            "columns": ["pred_absorption_nm", "unc_absorption_nm"],
            "support_columns": ["max_similarity_to_retained_donor"],
        }
    }
    subsets = {
        "full": ["absorption_nm"],
        "light_harvesting": ["absorption_nm"],
        "excited_state": ["quantum_yield"],
    }
    registry = discovery.build_registry(blocks, subsets)
    methods = {str(item["method"]) for item in registry}
    assert len(methods) == len(registry)
    for item in registry:
        if item.get("is_transfer_candidate"):
            assert item["matched_control"] in methods


def test_support_gating_abstains_at_zero_reliability() -> None:
    frame = pd.DataFrame(
        {
            "pred_absorption_nm": [1.0, 2.0, 3.0, 4.0],
            "unc_absorption_nm": [4.0, 3.0, 2.0, 1.0],
            "support_demo": [0.0, 0.0, 0.0, 0.0],
        }
    )
    block = {
        "frame": frame,
        "columns": ["pred_absorption_nm", "unc_absorption_nm"],
        "support_columns": ["support_demo"],
    }
    item = {
        "family": "support_gated_rank_predictions",
        "prediction_columns": ["pred_absorption_nm"],
        "uncertainty_columns": ["unc_absorption_nm"],
    }
    training_mask = np.asarray([True, True, False, False])
    evaluation_mask = ~training_mask
    train_x, eval_x = discovery.transformed_block(
        item, block, training_mask, evaluation_mask, 1
    )
    assert train_x.shape == (2, 2)
    assert eval_x.shape == (2, 2)
    assert np.isfinite(train_x).all()
    assert np.isfinite(eval_x).all()
    assert np.allclose(train_x, 0.0)
    assert np.allclose(eval_x, 0.0)


def test_small_end_to_end_draw_covers_registry() -> None:
    rng = np.random.default_rng(7)
    rows = 18
    metadata = pd.DataFrame(
        {
            "target_key": [f"development:{index}" for index in range(rows)],
            "scaffold": [f"scaffold-{index}" for index in range(rows)],
            "log1p_her": np.linspace(0.0, 1.0, rows),
        }
    )
    structure_x = rng.integers(0, 2, size=(rows, 32), dtype=np.uint8)
    calculated_x = rng.normal(size=(rows, 3))
    frame = pd.DataFrame(
        {
            "pred_absorption_nm": np.linspace(300, 600, rows),
            "unc_absorption_nm": np.linspace(30, 5, rows),
            "max_similarity_to_retained_donor": np.linspace(0.2, 0.9, rows),
        }
    )
    blocks = {
        "global_all_environment": {
            "frame": frame,
            "columns": ["pred_absorption_nm", "unc_absorption_nm"],
            "support_columns": ["max_similarity_to_retained_donor"],
        }
    }
    subsets = {
        "full": ["absorption_nm"],
        "light_harvesting": ["absorption_nm"],
        "excited_state": ["quantum_yield"],
    }
    registry = discovery.build_registry(blocks, subsets)
    draws = pd.DataFrame(
        {
            "budget": 6,
            "repeat": 0,
            "target_key": metadata["target_key"].iloc[:6],
            "scaffold": metadata["scaffold"].iloc[:6],
            "role": "training",
            "boundary_scaffold": "",
        }
    )
    config = {
        "recipient_random_forest": {
            "n_estimators_per_seed": 5,
            "min_samples_leaf": 1,
            "max_features": 0.5,
            "seeds_per_candidate": 1,
            "inner_oof_seeds_for_residual_and_fusion": 1,
        },
        "ridge": {
            "alphas": [0.1, 1.0],
            "blend_weights_for_donor": [0.0, 0.5, 1.0],
        },
    }
    result = discovery.run_draw(
        6,
        0,
        metadata,
        structure_x,
        calculated_x,
        blocks,
        registry,
        draws,
        config,
    )
    assert {row["method"] for row in result} == {
        str(item["method"]) for item in registry
    }
    assert all(np.isfinite(row["rmse"]) for row in result)


def test_discovery_script_has_no_blind_target_path() -> None:
    text = (
        ANALYSIS / "run_optical_transfer_method_discovery.py"
    ).read_text(encoding="utf-8")
    assert "SC-012-D1SC02150H-s006.csv" not in text
