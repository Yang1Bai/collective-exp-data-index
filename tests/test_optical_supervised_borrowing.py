from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))

import prepare_optical_supervised_borrowing_scopes as scopes  # noqa: E402
import pretrain_optical_source_chemprop as source  # noqa: E402
import run_optical_supervised_borrowing_development as run  # noqa: E402


def test_shuffled_labels_preserve_mask_and_marginals() -> None:
    values = np.asarray(
        [[1.0, np.nan], [2.0, 7.0], [3.0, 8.0], [4.0, 9.0]]
    )
    shuffled = source.shuffled_labels(values, 4)
    assert np.array_equal(np.isfinite(values), np.isfinite(shuffled))
    for column in range(values.shape[1]):
        assert np.allclose(
            np.sort(values[np.isfinite(values[:, column]), column]),
            np.sort(shuffled[np.isfinite(shuffled[:, column]), column]),
        )


def test_support_gate_is_bounded_and_can_abstain() -> None:
    values = np.asarray([0.1, 0.2, 0.425, 0.65, 0.9])
    scaled = source.scale_support(values, 0.2, 0.65)
    assert np.allclose(scaled, [0.0, 0.0, 0.5, 1.0, 1.0])


def test_source_encoder_training_roundtrip() -> None:
    smiles = [
        "C" * (index % 8 + 1)
        for index in range(36)
    ]
    targets = np.column_stack(
        [
            [len(value) for value in smiles],
            [np.sqrt(len(value)) for value in smiles],
        ]
    ).astype(np.float32)
    targets[::5, 1] = np.nan
    model, epoch, loss = source.train_model(
        smiles[:28],
        targets[:28],
        smiles[28:],
        targets[28:],
        {
            "hidden_dimension": 16,
            "message_passing_depth": 2,
            "batch_normalization": False,
            "dropout": 0.0,
            "learning_rate": 0.01,
            "batch_size": 8,
            "maximum_epochs": 2,
            "minimum_epochs": 1,
            "early_stopping_patience": 1,
        },
        seed=3,
        accelerator="cpu",
    )
    prediction, latent = source.predict_and_encode(
        model,
        smiles[28:],
        tasks=2,
        accelerator="cpu",
        batch_size=8,
    )
    assert epoch >= 1
    assert np.isfinite(loss)
    assert prediction.shape == (8, 2)
    assert latent.shape == (8, 16)
    assert np.isfinite(prediction).all()
    assert np.isfinite(latent).all()


def test_dynamic_scope_selects_lowest_similarity() -> None:
    frame = pd.DataFrame(
        {
            "budget": [2, 2],
            "repeat": [0, 0],
            "target_key": ["a", "b"],
            "scaffold": ["a", "b"],
            "role": ["training", "training"],
            "boundary_scaffold": ["", ""],
        }
    )
    from rdkit import Chem
    from rdkit.Chem import rdFingerprintGenerator

    smiles = ["C", "CC", "CCC", "c1ccccc1", "N#N"]
    generator = rdFingerprintGenerator.GetMorganGenerator(
        radius=2, fpSize=128
    )
    fingerprints = [
        generator.GetFingerprint(Chem.MolFromSmiles(value))
        for value in smiles
    ]
    result = scopes.make_scope(
        2,
        0,
        np.asarray(["a", "b", "c", "d", "e"]),
        fingerprints,
        frame,
        hard_fraction=0.4,
    )
    assert len(result) == 3
    assert int(result["dynamic_hard_ood_40pct"].sum()) == 2
    hard = result[result["dynamic_hard_ood_40pct"]]
    easy = result[~result["dynamic_hard_ood_40pct"]]
    assert hard["max_similarity_to_labeled_target"].max() <= easy[
        "max_similarity_to_labeled_target"
    ].min()


def test_adapter_can_select_zero_correction() -> None:
    rng = np.random.default_rng(7)
    rows = 24
    base = np.linspace(0.0, 1.0, rows)
    observed = base.copy()
    groups = np.asarray([f"g-{index}" for index in range(rows)])
    block = rng.normal(size=(rows, 4))
    selection_folds = [
        (
            np.asarray([index for index in range(rows) if index % 3 != fold]),
            np.asarray([index for index in range(rows) if index % 3 == fold]),
            np.zeros(sum(index % 3 != fold for index in range(rows))),
        )
        for fold in range(3)
    ]
    prediction, alpha, weight, correction = run.adapter_prediction(
        [block],
        [block[:5]],
        observed,
        base,
        base[:5],
        base,
        selection_folds,
        np.ones(rows),
        np.ones(5),
        {
            "alphas": [0.1, 1.0],
            "correction_weights": [0.0, 0.5, 1.0],
        },
    )
    assert alpha in {0.1, 1.0}
    assert weight == 0.0
    assert correction == 0.0
    assert np.allclose(prediction, base[:5])


def test_hurdle_prediction_is_finite() -> None:
    rng = np.random.default_rng(3)
    train_x = rng.integers(0, 2, size=(30, 20))
    train_y = np.r_[np.zeros(15), rng.uniform(0.1, 2.0, 15)]
    prediction, fallback = run.hurdle_prediction(
        train_x,
        train_y,
        train_x[:6],
        {
            "n_estimators": 5,
            "min_samples_leaf": 1,
            "max_features": 0.5,
        },
        seed_base=9,
        seeds=1,
    )
    assert not fallback
    assert prediction.shape == (6,)
    assert np.isfinite(prediction).all()
    assert (prediction >= 0).all()


def test_small_focused_draw_covers_all_declared_methods() -> None:
    rng = np.random.default_rng(19)
    rows = 30
    development = pd.DataFrame(
        {
            "target_key": [f"development:{index}" for index in range(rows)],
            "scaffold": [f"scaffold:{index}" for index in range(rows)],
            "log1p_her": np.where(
                np.arange(rows) % 2 == 0,
                0.0,
                rng.uniform(0.1, 1.5, rows),
            ),
        }
    )
    structure = rng.integers(0, 2, size=(rows, 24), dtype=np.uint8)
    draws = pd.DataFrame(
        {
            "budget": 12,
            "repeat": 0,
            "target_key": development["target_key"].iloc[:12],
            "scaffold": development["scaffold"].iloc[:12],
            "role": "training",
            "boundary_scaffold": "",
        }
    )
    evaluation_keys = development["target_key"].iloc[12:].astype(str)
    scope_frame = pd.DataFrame(
        {
            "budget": 12,
            "repeat": 0,
            "target_key": evaluation_keys,
            "max_similarity_to_labeled_target": np.linspace(
                0.1, 0.9, len(evaluation_keys)
            ),
            "dynamic_hard_ood_40pct": [
                index < 8 for index in range(len(evaluation_keys))
            ],
        }
    )
    method_names = [
        "state_aligned_pretrained_residual",
        "state_blind_pretrained_residual",
        "shuffled_source_pretrained_residual",
        "scalar_optical_residual",
    ]
    blocks = {
        name: [rng.normal(size=(rows, 6))]
        for name in method_names
    }
    reliability = {name: np.ones(rows) for name in method_names}
    config = {
        "target_hurdle_model": {
            "n_estimators": 5,
            "min_samples_leaf": 1,
            "max_features": 0.5,
            "final_seeds_per_draw": 1,
            "inner_oof_seeds": 1,
            "inner_group_folds": 3,
        },
        "target_adapter": {
            "alphas": [0.1, 1.0],
            "correction_weights": [0.0, 0.5, 1.0],
            "selection_outer_group_folds": 3,
            "selection_inner_group_folds": 2,
        },
    }
    result = run.run_draw(
        12,
        0,
        development,
        structure,
        draws,
        scope_frame,
        blocks,
        reliability,
        config,
    )
    assert len(result) == 12
    assert {row["method"] for row in result} == {
        "target_only_direct_regression",
        "target_only_hurdle",
        *method_names,
    }
    assert all(np.isfinite(row["rmse"]) for row in result)


def test_insufficient_scaffold_draw_forces_every_donor_to_abstain() -> None:
    rng = np.random.default_rng(23)
    rows = 24
    development = pd.DataFrame(
        {
            "target_key": [f"development:{index}" for index in range(rows)],
            "scaffold": (
                ["one-scaffold"] * 8
                + [f"evaluation:{index}" for index in range(rows - 8)]
            ),
            "log1p_her": np.where(
                np.arange(rows) % 2 == 0,
                0.0,
                rng.uniform(0.1, 1.5, rows),
            ),
        }
    )
    structure = rng.integers(0, 2, size=(rows, 20), dtype=np.uint8)
    draws = pd.DataFrame(
        {
            "budget": 8,
            "repeat": 0,
            "target_key": development["target_key"].iloc[:8],
            "scaffold": ["one-scaffold"] * 8,
            "role": "training",
            "boundary_scaffold": "",
        }
    )
    evaluation_keys = development["target_key"].iloc[8:].astype(str)
    scope_frame = pd.DataFrame(
        {
            "budget": 8,
            "repeat": 0,
            "target_key": evaluation_keys,
            "max_similarity_to_labeled_target": np.linspace(
                0.1, 0.9, len(evaluation_keys)
            ),
            "dynamic_hard_ood_40pct": [
                index < 7 for index in range(len(evaluation_keys))
            ],
        }
    )
    method_names = [
        "state_aligned_pretrained_residual",
        "state_blind_pretrained_residual",
        "shuffled_source_pretrained_residual",
        "scalar_optical_residual",
    ]
    blocks = {
        name: [rng.normal(size=(rows, 5))]
        for name in method_names
    }
    reliability = {name: np.ones(rows) for name in method_names}
    config = {
        "target_hurdle_model": {
            "n_estimators": 5,
            "min_samples_leaf": 1,
            "max_features": 0.5,
            "final_seeds_per_draw": 1,
            "inner_oof_seeds": 1,
            "inner_group_folds": 3,
        },
        "target_adapter": {
            "alphas": [0.1, 1.0],
            "correction_weights": [0.0, 0.5, 1.0],
            "selection_outer_group_folds": 3,
            "selection_inner_group_folds": 2,
        },
    }
    result = pd.DataFrame(
        run.run_draw(
            8,
            0,
            development,
            structure,
            draws,
            scope_frame,
            blocks,
            reliability,
            config,
        )
    )
    assert result["insufficient_scaffold_abstention"].all()
    assert set(result["training_scaffolds"]) == {1}
    donor = result[result["method"].isin(method_names)]
    baseline = result[
        result["method"] == "target_only_hurdle"
    ].set_index("scope")
    assert (donor["selected_correction_weight"] == 0.0).all()
    assert (donor["mean_absolute_correction"] == 0.0).all()
    for _, row in donor.iterrows():
        expected = baseline.loc[row["scope"]]
        assert row["rmse"] == expected["rmse"]
        assert row["mae"] == expected["mae"]
        assert row["r2"] == expected["r2"]
        assert (
            row["spearman"] == expected["spearman"]
            or (
                np.isnan(row["spearman"])
                and np.isnan(expected["spearman"])
            )
        )


def test_focused_development_code_has_no_blind_path() -> None:
    text = (
        ANALYSIS / "run_optical_supervised_borrowing_development.py"
    ).read_text(encoding="utf-8")
    assert "SC-012-D1SC02150H-s006.csv" not in text
