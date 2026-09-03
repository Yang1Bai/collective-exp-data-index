"""Versioned categorical schema shared by loaders, models, and checkpoints."""
from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "catalyst-attention-v1"

CONDITION_NAMES = (
    "current_density_mA_cm2",
    "temperature_K",
    "pH",
    "ligand_carboxyl_count",
    "ligand_amino_count",
    "substitution_atomic_number",
)
REACTION_NAMES = ("unknown", "OER", "HER", "CO2R", "ORR")
MEASUREMENT_MODALITY_NAMES = ("none", "UV_VIS_NIR", "LSV")
TARGET_NAMES = (
    "unknown",
    "oer_overpotential_mV",
    "voltage",
    "fe_h2",
    "fe_co",
    "fe_ch4",
    "fe_c2h4",
    "fe_gas_total",
    "fe_liquid",
    "log10_k0",
    "alpha",
    "i_lim",
)
PROGRAM_NAMES = (
    "unknown",
    "specgen_source",
    "specgen_A",
    "specgen_B",
    "specgen_C",
    "specgen_D",
    "ocx24_uoft",
    "ocx24_vsp",
    "seccm_Au-rich",
    "seccm_Ir-rich",
    "seccm_Rh-rich",
)
FUSION_BLOCK_NAMES = (
    "composition",
    "curve",
    "conditions",
    "surface",
    "task",
)


def schema_manifest() -> dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "conditions": list(CONDITION_NAMES),
        "reactions": list(REACTION_NAMES),
        "measurement_modalities": list(MEASUREMENT_MODALITY_NAMES),
        "targets": list(TARGET_NAMES),
        "programs": list(PROGRAM_NAMES),
        "fusion_blocks": list(FUSION_BLOCK_NAMES),
    }
