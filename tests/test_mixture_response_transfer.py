from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))

from mixture_response_transfer_common import (  # noqa: E402
    fit_shrinkage_adapter,
    formula_signature,
    maximin_anchors,
    mixture_features,
    nonanchor_test_indices,
)


def record(solvent_order: tuple[int, ...] = (0, 1)) -> dict:
    solvents = [
        {"name": "EC", "smiles": "O=C1OCCO1", "molar_ratio": 2.0},
        {"name": "DMC", "smiles": "COC(=O)OC", "molar_ratio": 3.0},
    ]
    return {
        "solvents": [solvents[index] for index in solvent_order],
        "salts": [
            {
                "name": "LiPF6",
                "smiles": "F[P-](F)(F)(F)(F)F",
                "molar_ratio": 1.0,
            }
        ],
        "salt_molar_ratio": 1.0 / 6.0,
        "temperature": 25.0,
        "conductivity": 10.0,
        "conductivity_mask": True,
    }


def test_mixture_representation_is_permutation_invariant() -> None:
    original = record((0, 1))
    reversed_components = record((1, 0))
    assert formula_signature(original) == formula_signature(reversed_components)
    assert np.allclose(
        mixture_features([original]),
        mixture_features([reversed_components]),
        rtol=0.0,
        atol=1e-14,
    )


def test_anchor_formulation_is_excluded_wholesale() -> None:
    x = np.asarray([[0.0], [0.1], [1.0], [2.0]])
    groups = np.asarray(["a", "a", "b", "c"])
    anchors = maximin_anchors(x, groups, budget=1, start_index=0)
    test = nonanchor_test_indices(groups, anchors)
    assert not set(groups[anchors]).intersection(groups[test])
    assert len(set(groups[test])) == 2


def test_large_shrinkage_penalty_preserves_source_prediction() -> None:
    source = np.asarray([0.0, 1.0, 2.0])
    state = np.asarray([[0.0], [1.0], [2.0]])
    target = source + 1.0
    adapter = fit_shrinkage_adapter(
        source,
        state,
        target,
        alpha=1e12,
    )
    adapted = adapter.predict(source, state)
    assert np.max(np.abs(adapted - source)) < 1e-10

