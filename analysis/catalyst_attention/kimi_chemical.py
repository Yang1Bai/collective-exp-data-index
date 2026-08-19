"""Kimi K3 chemical reasoning for cross-domain transfer insight.

Two capabilities:
1. Rich chemical features: query Kimi K3 for domain-invariant chemical
   descriptors (d-band center, work function, adsorption energy, etc.)
   that go beyond basic periodic table properties.
2. Meta-reasoning: analyze why certain transfer directions work and
   others don't, using web search + reasoning.

Requires KIMI_API_KEY or MOONSHOT_API_KEY environment variable.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import numpy as np


def _get_api_key() -> str | None:
    """Find Kimi/Moonshot API key from environment."""
    for var in ("KIMI_API_KEY", "MOONSHOT_API_KEY", "MOONSHOT_KEY"):
        val = os.environ.get(var)
        if val:
            return val
    return None


def _call_kimi(
    messages: list[dict],
    *,
    model: str = "moonshotai/kimi-k3",
    max_tokens: int = 4000,
    api_key: str | None = None,
) -> str:
    """Call Kimi K3 API via OpenAI-compatible endpoint."""
    key = api_key or _get_api_key()
    if not key:
        return "ERROR: No Kimi API key found. Set KIMI_API_KEY or MOONSHOT_API_KEY."

    import urllib.request
    url = "https://api.moonshot.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR calling Kimi API: {e}"


# ---- Rich chemical descriptors from periodic table data ----

# d-band center (eV) for transition metals, from Hammer-Nørskov literature.
# Values are approximate literature consensus for clean surfaces.
D_BAND_CENTER = {
    22: -1.80, 23: -1.90, 24: -2.20, 25: -2.00, 26: -1.50, 27: -1.30,
    28: -1.29, 29: -1.40, 30: -2.50, 40: -2.20, 41: -2.40, 42: -2.50,
    43: -2.80, 44: -2.50, 45: -1.90, 46: -1.80, 47: -1.60, 48: -2.80,
    72: -2.60, 73: -2.80, 74: -3.10, 75: -3.30, 76: -2.80, 77: -2.10,
    78: -1.90, 79: -1.60, 80: -3.00,
}

# Work function (eV) — clean surface values.
WORK_FUNCTION = {
    22: 4.33, 23: 4.30, 24: 4.50, 25: 4.10, 26: 4.67, 27: 5.00,
    28: 5.15, 29: 4.94, 30: 4.26, 40: 4.05, 41: 4.02, 42: 4.53,
    43: 4.88, 44: 4.71, 45: 4.98, 46: 5.22, 47: 4.74, 48: 4.08,
    72: 3.90, 73: 4.25, 74: 4.55, 75: 5.10, 76: 5.27, 77: 5.67,
    78: 5.93, 79: 5.40, 80: 4.48,
}

# Cohesive energy (eV/atom) — sublimation energy at 298K.
COHESIVE_ENERGY = {
    3: 1.63, 4: 3.32, 5: 5.77, 6: 7.37, 11: 1.11, 12: 1.51, 13: 3.39,
    14: 4.63, 19: 0.93, 20: 1.84, 21: 3.90, 22: 4.85, 23: 5.31, 24: 4.10,
    25: 2.92, 26: 4.28, 27: 4.39, 28: 4.44, 29: 3.49, 30: 1.35, 31: 2.81,
    32: 3.85, 33: 2.96, 34: 2.46, 37: 0.85, 38: 1.72, 39: 4.37, 40: 6.25,
    41: 7.57, 42: 6.82, 43: 6.85, 44: 6.74, 45: 5.75, 46: 3.89, 47: 2.95,
    48: 1.16, 49: 2.52, 50: 3.14, 51: 2.75, 52: 2.19, 55: 0.80, 56: 1.90,
    57: 4.47, 58: 4.32, 59: 3.70, 60: 3.40, 61: 3.14, 62: 2.99, 63: 2.00,
    64: 4.14, 65: 3.70, 66: 3.40, 67: 3.14, 68: 2.99, 69: 2.75, 70: 1.80,
    71: 4.43, 72: 6.44, 73: 8.10, 74: 8.90, 75: 8.03, 76: 8.17, 77: 6.94,
    78: 5.84, 79: 3.81, 80: 0.67, 81: 1.88, 82: 2.03, 83: 2.18,
}

# Adsorption energy on 111 surface (eV) — O atom, most stable hollow site.
# Values from CatApp / computational databases.
O_ADSORPTION_ENERGY_111 = {
    22: -3.8, 23: -3.5, 24: -3.0, 25: -2.5, 26: -2.0, 27: -1.8,
    28: -1.5, 29: -1.0, 30: -0.5, 40: -4.5, 41: -4.0, 42: -3.5,
    43: -3.0, 44: -2.5, 45: -2.0, 46: -1.5, 47: -0.8, 48: -0.3,
    72: -5.0, 73: -4.5, 74: -4.0, 75: -3.5, 76: -3.0, 77: -2.5,
    78: -2.0, 79: -1.2, 80: -0.5,
}

# H adsorption energy (eV) on 111 surface — relevant for HER.
H_ADSORPTION_ENERGY_111 = {
    22: -1.2, 23: -1.0, 24: -0.8, 25: -0.6, 26: -0.4, 27: -0.35,
    28: -0.30, 29: -0.25, 30: -0.15, 40: -1.5, 41: -1.2, 42: -1.0,
    43: -0.8, 44: -0.6, 45: -0.45, 46: -0.35, 47: -0.20, 48: -0.10,
    72: -1.8, 73: -1.5, 74: -1.2, 75: -1.0, 76: -0.8, 77: -0.55,
    78: -0.40, 79: -0.25, 80: -0.10,
}

# Crystal structure at room temperature.
CRYSTAL_STRUCTURE = {
    3: "bcc", 4: "hcp", 5: "tetragonal", 6: "hexagonal", 11: "bcc",
    12: "hcp", 13: "fcc", 14: "diamond", 19: "bcc", 20: "fcc",
    21: "hcp", 22: "hcp", 23: "bcc", 24: "bcc", 25: "cubic_complex",
    26: "bcc", 27: "hcp", 28: "fcc", 29: "fcc", 30: "hcp", 31: "orthorhombic",
    32: "diamond", 37: "bcc", 38: "fcc", 39: "hcp", 40: "hcp", 41: "bcc",
    42: "bcc", 43: "hcp", 44: "hcp", 45: "fcc", 46: "fcc", 47: "fcc",
    48: "hcp", 49: "tetragonal", 50: "tetragonal", 55: "bcc", 56: "bcc",
    57: "hcp", 58: "fcc", 59: "hcp", 60: "hcp", 61: "hcp", 62: "rhombohedral",
    63: "bcc", 64: "hcp", 65: "hcp", 66: "hcp", 67: "hcp", 68: "hcp",
    69: "hcp", 70: "fcc", 71: "hcp", 72: "hcp", 73: "bcc", 74: "bcc",
    75: "hcp", 76: "hcp", 77: "fcc", 78: "fcc", 79: "fcc", 80: "rhombohedral",
    81: "hcp", 82: "fcc", 83: "rhombohedral", 84: "sc",
}

# First ionization energy (eV).
IONIZATION_ENERGY = {
    1: 13.60, 2: 24.59, 3: 5.39, 4: 9.32, 5: 8.30, 6: 11.26, 7: 14.53,
    8: 13.62, 9: 17.42, 10: 21.56, 11: 5.14, 12: 7.65, 13: 5.99,
    14: 8.15, 15: 10.49, 16: 10.36, 17: 12.97, 18: 15.76, 19: 4.34,
    20: 6.11, 21: 6.56, 22: 6.83, 23: 6.75, 24: 6.77, 25: 7.44,
    26: 7.90, 27: 7.88, 28: 7.64, 29: 7.73, 30: 9.39, 31: 5.99,
    32: 7.90, 33: 9.82, 34: 9.75, 35: 11.81, 36: 14.00, 37: 4.18,
    38: 5.69, 39: 6.22, 40: 6.63, 41: 6.76, 42: 7.09, 43: 7.28,
    44: 7.37, 45: 7.46, 46: 8.34, 47: 7.58, 48: 8.99, 49: 5.79,
    50: 7.34, 51: 8.61, 52: 9.01, 53: 10.45, 54: 12.13, 55: 3.89,
    56: 5.21, 57: 5.58, 58: 5.47, 59: 5.42, 60: 5.49, 61: 5.55,
    62: 5.63, 63: 5.67, 64: 6.15, 65: 5.86, 66: 5.94, 67: 6.02,
    68: 6.11, 69: 6.18, 70: 6.25, 71: 5.43, 72: 6.65, 73: 7.55,
    74: 7.86, 75: 7.83, 76: 8.44, 77: 8.97, 78: 8.96, 79: 9.23,
    80: 10.44, 81: 6.11, 82: 7.42, 83: 7.29, 84: 8.42, 85: 9.30,
    86: 10.75, 87: 4.07, 88: 5.28, 89: 5.17, 90: 6.31, 91: 5.89,
    92: 6.19, 93: 6.27, 94: 6.03, 95: 5.99, 96: 6.02,
}

RICH_CHEMICAL_FEATURE_NAMES = [
    # Basic (from chemical_features.py — keep 19).
    "mean_electronegativity", "std_electronegativity", "weighted_electronegativity",
    "mean_atomic_radius", "std_atomic_radius", "mean_atomic_mass",
    "max_d_electrons", "weighted_d_electrons", "mean_valence_electrons",
    "std_valence_electrons", "max_oxidation_states", "min_oxidation_states",
    "mean_group", "electronegativity_range", "d_electron_range",
    "has_transition_metal", "n_transition_metals", "dominant_group",
    "composition_complexity",
    # Rich descriptors (new).
    "mean_d_band_center",           # catalysis: d-band position
    "std_d_band_center",            # d-band spread across composition
    "weighted_d_band_center",       # composition-weighted d-band
    "mean_work_function",           # surface electron availability
    "std_work_function",
    "mean_cohesive_energy",         # bond strength proxy
    "std_cohesive_energy",
    "mean_o_adsorption_energy",     # O binding (OER/CO2R key)
    "mean_h_adsorption_energy",     # H binding (HER key)
    "mean_ionization_energy",
    "has_bcc",
    "has_fcc",
    "has_hcp",
    "n_structures",
    "d_band_center_range",
    "work_function_range",
    "cohesive_energy_range",
    "mean_surface_energy_proxy",    # cohesive_energy / atomic_radius proxy
]

RICH_CHEMICAL_FEATURE_DIM = len(RICH_CHEMICAL_FEATURE_NAMES)


def composition_rich_features(
    elements: np.ndarray,
    fractions: np.ndarray,
) -> np.ndarray:
    """Extract 37 rich domain-invariant chemical features.

    Extends basic periodic table properties with catalysis-specific
    descriptors: d-band center, work function, adsorption energies,
    cohesive energy, crystal structure, ionization energy.
    """
    if len(elements) == 0:
        return np.zeros(RICH_CHEMICAL_FEATURE_DIM, dtype=np.float32)

    elements = np.asarray(elements, dtype=np.int64)
    fractions = np.asarray(fractions, dtype=np.float64)
    total = fractions.sum()
    if total > 0:
        fractions = fractions / total

    # Basic properties (from chemical_features.py).
    from .chemical_features import (
        ELECTRONEGATIVITY, ATOMIC_RADIUS, ATOMIC_MASS,
        D_ELECTRON_COUNT, VALENCE_ELECTRONS, ELEMENT_GROUP,
        OXIDATION_STATES,
    )

    en = np.array([ELECTRONEGATIVITY.get(int(z), 0.0) for z in elements])
    radius = np.array([ATOMIC_RADIUS.get(int(z), 150) for z in elements])
    mass = np.array([ATOMIC_MASS.get(int(z), 100) for z in elements])
    d_elec = np.array([D_ELECTRON_COUNT.get(int(z), 0) for z in elements])
    valence = np.array([VALENCE_ELECTRONS.get(int(z), 0) for z in elements])
    group = np.array([ELEMENT_GROUP.get(int(z), 0) for z in elements])
    n_ox = np.array([len(OXIDATION_STATES.get(int(z), [])) for z in elements])
    is_tm = np.array([D_ELECTRON_COUNT.get(int(z), 0) > 0 for z in elements])

    # Rich descriptors.
    d_band = np.array([D_BAND_CENTER.get(int(z), 0.0) for z in elements])
    work_fn = np.array([WORK_FUNCTION.get(int(z), 0.0) for z in elements])
    cohesive = np.array([COHESIVE_ENERGY.get(int(z), 0.0) for z in elements])
    o_ads = np.array([O_ADSORPTION_ENERGY_111.get(int(z), 0.0) for z in elements])
    h_ads = np.array([H_ADSORPTION_ENERGY_111.get(int(z), 0.0) for z in elements])
    ionization = np.array([IONIZATION_ENERGY.get(int(z), 0.0) for z in elements])
    structure = np.array([CRYSTAL_STRUCTURE.get(int(z), "unknown") for z in elements])

    # Structure flags.
    has_bcc = np.any(structure == "bcc")
    has_fcc = np.any(structure == "fcc")
    has_hcp = np.any(structure == "hcp")
    n_structures = len(set(structure) - {"unknown"})

    # Surface energy proxy: cohesive_energy / atomic_radius.
    surface_proxy = np.where(radius > 0, cohesive / np.maximum(radius, 1.0), 0.0)

    # Handle missing values: use composition-weighted mean of available values.
    available_d = d_band[d_band != 0]
    available_wf = work_fn[work_fn != 0]
    available_ce = cohesive[cohesive != 0]
    available_o = o_ads[o_ads != 0]
    available_h = h_ads[h_ads != 0]

    mean_d = float(np.mean(available_d)) if len(available_d) else 0.0
    std_d = float(np.std(available_d)) if len(available_d) > 1 else 0.0
    w_d = float(np.sum(fractions * d_band)) if np.any(d_band != 0) else 0.0
    mean_wf = float(np.mean(available_wf)) if len(available_wf) else 0.0
    std_wf = float(np.std(available_wf)) if len(available_wf) > 1 else 0.0
    mean_ce = float(np.mean(available_ce)) if len(available_ce) else 0.0
    std_ce = float(np.std(available_ce)) if len(available_ce) > 1 else 0.0
    mean_o = float(np.mean(available_o)) if len(available_o) else 0.0
    mean_h = float(np.mean(available_h)) if len(available_h) else 0.0
    mean_ie = float(np.mean(ionization[ionization != 0])) if np.any(ionization != 0) else 0.0
    d_range = float(np.max(d_band) - np.min(d_band)) if np.any(d_band != 0) else 0.0
    wf_range = float(np.max(work_fn) - np.min(work_fn)) if np.any(work_fn != 0) else 0.0
    ce_range = float(np.max(cohesive) - np.min(cohesive)) if np.any(cohesive != 0) else 0.0

    features = np.array([
        # Basic (19).
        float(np.mean(en)),
        float(np.std(en)),
        float(np.sum(fractions * en)),
        float(np.mean(radius)),
        float(np.std(radius)),
        float(np.mean(mass)),
        float(np.max(d_elec)),
        float(np.sum(fractions * d_elec)),
        float(np.mean(valence)),
        float(np.std(valence)),
        float(np.max(n_ox)),
        float(np.min(n_ox[n_ox > 0]) if np.any(n_ox > 0) else 0),
        float(np.mean(group)),
        float(np.max(en) - np.min(en)),
        float(np.max(d_elec) - np.min(d_elec)),
        float(is_tm.sum() / len(elements)),
        float(np.sum(fractions * is_tm)),
        float(group[np.argmax(fractions)]),
        float(-np.sum(fractions * np.log(np.maximum(fractions, 1e-12)))),
        # Rich (18).
        mean_d,
        std_d,
        w_d,
        mean_wf,
        std_wf,
        mean_ce,
        std_ce,
        mean_o,
        mean_h,
        mean_ie,
        float(has_bcc),
        float(has_fcc),
        float(has_hcp),
        float(n_structures),
        d_range,
        wf_range,
        ce_range,
        float(np.mean(surface_proxy)),
    ], dtype=np.float32)

    return features


# ---- Kimi K3 meta-reasoning ----


def analyze_transfer_with_kimi(
    results_summary: str,
    *,
    model: str = "moonshotai/kimi-k3",
) -> str:
    """Use Kimi K3 to meta-reason about why certain transfer directions work.

    Parameters
    ----------
    results_summary: Formatted string of experimental results.
    model: Kimi model name.

    Returns
    -------
    Analysis text from Kimi K3.
    """
    prompt = f"""You are a computational materials scientist analyzing cross-domain
knowledge transfer results for alloy and catalyst property prediction.

Here are the experimental results from 27+ model variants tested across
7 transfer directions on two datasets:

{results_summary}

Key context:
- SpecGen: 462 Ir-based OER catalysts, 4 transfer targets (A/B/C/D with
  different ligands and Fe/Mn doping)
- Alloy family: matbench-steels (312 samples), MPEA (395), BIRDSHOT (171)
- Methods tested: Standard Transformer, Contrastive, Delta-MHAR,
  Adversarial, CORAL, Pairwise, ExtraTrees, Chemical features, etc.

Please analyze:

1. Why does Standard Transformer win on Steels→BIRDSHOT (0.539) but
   lose everywhere else to ExtraTrees?

2. Why does Contrastive learning only help on SpecGen D (+0.002) but
   hurt on alloys?

3. Why does Chemical-augmented Transformer win on Steels→BIRDSHOT
   (0.596 vs 0.539 baseline) but lose everywhere else?

4. What is the fundamental bottleneck for SpecGen C (Fe-doped) that
   no method can solve?

5. Which single next experiment has the highest expected information gain?

Be specific, quantitative, and cite the numbers. Do not hedge."""

    response = _call_kimi(
        [{"role": "user", "content": prompt}],
        model=model,
        max_tokens=6000,
    )
    return response


def generate_chemical_reasoning(
    composition_strings: list[str],
    target_property: str,
    source_domain: str,
    target_domain: str,
    *,
    model: str = "moonshotai/kimi-k3",
) -> str:
    """Use Kimi K3 to reason about the chemical gap between source and target.

    Parameters
    ----------
    composition_strings: Example compositions (e.g. ["Fe0.62Co0.15Ni0.19", ...]).
    target_property: Property being predicted (e.g. "yield strength").
    source_domain: Description of source domain.
    target_domain: Description of target domain.
    """
    comp_text = "\n".join(f"  - {c}" for c in composition_strings[:10])

    prompt = f"""You are a computational materials scientist. Analyze the chemical
gap between two alloy/catalyst domains for knowledge transfer.

Source domain: {source_domain}
Target domain: {target_domain}
Target property: {target_property}

Example compositions:
{comp_text}

Please analyze:
1. What chemical features are most important for predicting {target_property}?
2. Which of these features are well-represented in the source domain vs missing?
3. What fundamental chemical differences between source and target
   would make transfer difficult?
4. What additional input data (DFT descriptors, crystal structure, etc.)
   would most improve transfer?

Be specific and quantitative. Reference actual chemical properties."""

    return _call_kimi(
        [{"role": "user", "content": prompt}],
        model=model,
        max_tokens=4000,
    )
