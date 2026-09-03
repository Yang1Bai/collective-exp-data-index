from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))

from electrolyte_programme_interaction_common import (  # noqa: E402
    exact_formulation_signature,
    general_record_overlap_count,
    mass_formulation_record,
    percentile_rank,
)
from mixture_response_transfer_common import mixture_features  # noqa: E402


def formulation(
    *,
    solvent_masses: dict[str, float] | None = None,
    salt_mass: float = 15.0,
    temperature_C: float = 25.0,
    conductivity_mS_cm: float = 8.0,
) -> dict:
    return mass_formulation_record(
        solvent_masses=solvent_masses or {"EC": 45.0, "EMC": 40.0},
        salt_mass=salt_mass,
        temperature_C=temperature_C,
        conductivity_mS_cm=conductivity_mS_cm,
        programme="test",
        source_id="test-record",
    )


def test_mass_conversion_is_order_and_scale_invariant() -> None:
    first = formulation(solvent_masses={"EC": 45.0, "EMC": 40.0})
    reordered_scaled = formulation(
        solvent_masses={"EMC": 80.0, "EC": 90.0},
        salt_mass=30.0,
    )
    assert exact_formulation_signature(first) == exact_formulation_signature(
        reordered_scaled
    )
    assert np.allclose(
        mixture_features([first]),
        mixture_features([reordered_scaled]),
        rtol=0.0,
        atol=1e-14,
    )


def test_signature_includes_salt_concentration() -> None:
    dilute = formulation(salt_mass=10.0)
    concentrated = formulation(salt_mass=20.0)
    assert exact_formulation_signature(dilute) != exact_formulation_signature(
        concentrated
    )


def test_overlap_requires_composition_temperature_and_outcome_match() -> None:
    source = [formulation()]
    exact = [formulation()]
    temperature_shift = [formulation(temperature_C=25.2)]
    outcome_shift = [formulation(conductivity_mS_cm=8.2)]
    kwargs = {
        "composition_tolerance": 1e-4,
        "temperature_tolerance": 0.05,
        "outcome_tolerance": 0.01,
    }
    assert general_record_overlap_count(source, exact, **kwargs) == 1
    assert (
        general_record_overlap_count(source, temperature_shift, **kwargs) == 0
    )
    assert general_record_overlap_count(source, outcome_shift, **kwargs) == 0


def test_percentile_rank_preserves_declared_ties() -> None:
    observed = percentile_rank([2.0, 1.0, 2.0, 4.0])
    assert np.allclose(observed, [0.625, 0.25, 0.625, 1.0])
