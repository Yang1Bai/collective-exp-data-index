"""Kinetic profile tokens for domain-invariant catalyst representation.

Inspired by Prof. Donna Blackman's insight: kinetic profiles are a universal
language for catalytic reactions. The shape of a rate-vs-time curve encodes
mechanistic information independent of the specific chemistry.

This module implements:
1. Kinetic profile shape extraction (from time-series or endpoint data)
2. Universal catalytic cycle tokenization
3. Integration with CatalystTransferTransformer
"""
from __future__ import annotations

import numpy as np
from typing import Sequence

from .data import CatalystSample


# ---- Kinetic profile shape parameters ----

KINETIC_FEATURE_NAMES = [
    "apparent_order",           # 0, 1, or 2 (from concentration dependence)
    "rate_constant_log",        # log10 of apparent rate constant
    "activation_energy",        # E_a in eV (from Arrhenius)
    "induction_period",         # normalized induction period (0-1)
    "max_rate_position",        # where max rate occurs (0=start, 1=end)
    "deactivation_rate",        # rate of catalyst decay (0=stable)
    "conversion_at_half",       # conversion at half reaction time
    "profile_curvature",        # 2nd derivative at midpoint (sign tells mechanism)
    "resting_state_early",      # 1 if resting state is early in cycle
    "resting_state_late",       # 1 if resting state is late in cycle
    "is_saturated",             # 1 if zero-order (catalyst saturated)
    "is_first_order",           # 1 if first-order in substrate
    "is_second_order",          # 1 if second-order overall
    "has_induction",            # 1 if induction period present
    "has_deactivation",         # 1 if rate decreases over time
    "profile_symmetry",         # 0=front-loaded, 1=back-loaded
    "initial_rate_ratio",       # initial rate / average rate
    "final_rate_ratio",         # final rate / average rate
    "area_under_curve",         # total conversion (normalized)
    "time_to_50pct",            # time to 50% conversion (normalized)
]

KINETIC_FEATURE_DIM = len(KINETIC_FEATURE_NAMES)


def extract_kinetic_features(
    times: np.ndarray,
    rates: np.ndarray,
    concentrations: np.ndarray | None = None,
    temperatures: np.ndarray | None = None,
) -> np.ndarray:
    """Extract 20 kinetic profile shape features from time-series data.

    Parameters
    ----------
    times: (n_points,) reaction times (normalized to 0-1 or raw).
    rates: (n_points,) reaction rates at each time.
    concentrations: (n_points,) substrate concentrations (optional).
    temperatures: (n_points,) temperatures (optional, for E_a).

    Returns
    -------
    (20,) kinetic feature vector.
    """
    if len(times) < 3:
        return np.zeros(KINETIC_FEATURE_DIM, dtype=np.float32)

    # Normalize time to 0-1.
    t_norm = (times - times.min()) / max(times.max() - times.min(), 1e-12)
    # Normalize rate to 0-1.
    r_norm = rates / max(rates.max(), 1e-12)

    # Basic shape features.
    max_rate_idx = np.argmax(r_norm)
    max_rate_pos = float(t_norm[max_rate_idx])

    # Initial and final rates.
    initial_rate = float(r_norm[0])
    final_rate = float(r_norm[-1])
    avg_rate = float(np.mean(r_norm))

    # Conversion estimate (integral of rate).
    conversion = np.trapezoid(r_norm, t_norm)
    half_idx = np.searchsorted(np.cumsum(r_norm) / np.sum(r_norm), 0.5)
    t_half = float(t_norm[min(half_idx, len(t_norm) - 1)])

    # Curvature (2nd derivative at midpoint).
    mid = len(t_norm) // 2
    if mid > 0 and mid < len(t_norm) - 1:
        curvature = float(r_norm[mid + 1] - 2 * r_norm[mid] + r_norm[mid - 1])
    else:
        curvature = 0.0

    # Induction period: time before rate exceeds 10% of max.
    induction_idx = np.argmax(r_norm > 0.1 * r_norm.max())
    induction = float(t_norm[induction_idx]) if induction_idx > 0 else 0.0

    # Deactivation: rate decrease after maximum.
    if max_rate_idx < len(r_norm) - 1:
        deactivation = float(
            (r_norm[max_rate_idx] - r_norm[-1]) / max(r_norm[max_rate_idx], 1e-12)
        )
    else:
        deactivation = 0.0

    # Reaction order estimation (if concentration data available).
    order = 1.0  # default
    if concentrations is not None and len(concentrations) == len(rates):
        # Fit rate = k * [S]^order using log-log.
        valid = (concentrations > 0) & (rates > 0)
        if np.sum(valid) > 2:
            log_c = np.log(concentrations[valid])
            log_r = np.log(rates[valid])
            order = float(np.polyfit(log_c, log_r, 1)[0])
            order = np.clip(order, 0.0, 2.0)

    # Activation energy (if temperature data available).
    activation_energy = 0.0
    if temperatures is not None and len(temperatures) == len(rates):
        valid = (temperatures > 0) & (rates > 0)
        if np.sum(valid) > 2:
            # Simplified Arrhenius: ln(k) = -E_a/R * (1/T) + const
            inv_T = 1.0 / temperatures[valid]
            log_r = np.log(rates[valid])
            slope = np.polyfit(inv_T, log_r, 1)[0]
            R = 8.314e-3  # kJ/mol/K
            activation_energy = float(-slope * R / 96.485)  # Convert to eV

    # Mechanism indicators.
    is_saturated = float(order < 0.1)
    is_first_order = float(0.9 < order < 1.1)
    is_second_order = float(order > 1.9)
    has_induction = float(induction > 0.05)
    has_deactivation = float(deactivation > 0.1)

    # Resting state position (early vs late in cycle).
    resting_early = float(max_rate_pos < 0.3)
    resting_late = float(max_rate_pos > 0.7)

    # Profile symmetry.
    front_half = np.trapezoid(r_norm[:mid], t_norm[:mid]) if mid > 0 else 0
    back_half = np.trapezoid(r_norm[mid:], t_norm[mid:]) if mid < len(r_norm) else 0
    total = front_half + back_half
    symmetry = float(back_half / max(total, 1e-12))

    # Rate ratios.
    initial_ratio = float(initial_rate / max(avg_rate, 1e-12))
    final_ratio = float(final_rate / max(avg_rate, 1e-12))

    # Area under curve (total conversion proxy).
    auc = float(np.trapezoid(r_norm, t_norm))

    features = np.array([
        order,
        float(np.log10(max(avg_rate, 1e-12))),
        activation_energy,
        induction,
        max_rate_pos,
        deactivation,
        float(conversion),
        curvature,
        resting_early,
        resting_late,
        is_saturated,
        is_first_order,
        is_second_order,
        has_induction,
        has_deactivation,
        symmetry,
        initial_ratio,
        final_ratio,
        auc,
        t_half,
    ], dtype=np.float32)

    return features


def estimate_kinetic_from_endpoints(
    yields: np.ndarray,
    times: np.ndarray,
    temperatures: np.ndarray | None = None,
) -> np.ndarray:
    """Estimate kinetic features from endpoint measurements (no time-series).

    This is the practical case: we have yield at a few time points,
    not continuous monitoring.

    Parameters
    ----------
    yields: (n_points,) product yields or conversions.
    times: (n_points,) reaction times.
    temperatures: (n_points,) temperatures (optional).

    Returns
    -------
    (20,) estimated kinetic feature vector.
    """
    if len(yields) < 2:
        return np.zeros(KINETIC_FEATURE_DIM, dtype=np.float32)

    # Estimate rates from yield differences.
    rates = np.diff(yields) / np.maximum(np.diff(times), 1e-12)
    times_mid = (times[1:] + times[:-1]) / 2

    return extract_kinetic_features(times_mid, rates, temperatures=temperatures)


# ---- Universal catalytic cycle tokenization ----

class CatalyticCycleTokenizer:
    """Tokenize catalyst samples using universal kinetic descriptors.

    The key insight: kinetic profiles are domain-invariant. A first-order
    decay curve looks the same whether it's OER on Ir or hydrogenation on Pd.
    """

    def __init__(self) -> None:
        self.feature_names = KINETIC_FEATURE_NAMES

    def tokenize(
        self,
        sample: CatalystSample,
        times: np.ndarray | None = None,
        rates: np.ndarray | None = None,
        concentrations: np.ndarray | None = None,
        temperatures: np.ndarray | None = None,
    ) -> np.ndarray:
        """Convert a catalyst sample to kinetic feature vector.

        If time-series data is available, extract from it.
        If not, estimate from composition + conditions.
        """
        if times is not None and rates is not None:
            return extract_kinetic_features(times, rates, concentrations, temperatures)

        # Fallback: estimate from composition and target.
        # Use composition to estimate likely kinetic behavior.
        from .chemical_features import composition_chemical_features
        chem = composition_chemical_features(sample.elements, sample.fractions)

        # Map chemical properties to kinetic estimates.
        # This is a heuristic mapping based on physical intuition.
        d_elec = chem[6]  # max d-electrons
        en = chem[0]      # mean electronegativity
        cohesive = chem[24] if len(chem) > 24 else 4.0  # cohesive energy

        # Estimate kinetic features from chemistry.
        estimated_order = 1.0 + 0.1 * (d_elec - 5)  # More d-electrons → higher order
        estimated_ea = 0.5 + 0.05 * cohesive  # Higher cohesive energy → higher E_a
        estimated_rate = -1.0 - 0.2 * (en - 2.0)  # Higher EN → lower rate

        return np.array([
            estimated_order,
            estimated_rate,
            estimated_ea,
            0.0,  # no induction
            0.3,  # max rate early
            0.0,  # no deactivation
            0.5,  # 50% conversion
            0.0,  # zero curvature
            1.0 if estimated_order < 0.5 else 0.0,  # early resting state
            0.0,  # not late
            1.0 if estimated_order < 0.1 else 0.0,  # saturated
            1.0 if 0.9 < estimated_order < 1.1 else 0.0,  # first order
            1.0 if estimated_order > 1.9 else 0.0,  # second order
            0.0,  # no induction
            0.0,  # no deactivation
            0.5,  # symmetric
            1.0,  # initial = average
            1.0,  # final = average
            0.5,  # medium conversion
            0.5,  # half time at midpoint
        ], dtype=np.float32)


# ---- Integration with CatalystSample ----

def augment_with_kinetic_tokens(
    samples: Sequence[CatalystSample],
    times_list: Sequence[np.ndarray] | None = None,
    rates_list: Sequence[np.ndarray] | None = None,
) -> list[CatalystSample]:
    """Add kinetic profile tokens to catalyst samples.

    If time-series data is provided, extract real kinetic features.
    Otherwise, estimate from composition.
    """
    tokenizer = CatalyticCycleTokenizer()
    augmented = []

    for i, sample in enumerate(samples):
        times = times_list[i] if times_list else None
        rates = rates_list[i] if rates_list else None

        kinetic_features = tokenizer.tokenize(sample, times, rates)

        # Encode kinetic features as additional "condition" values.
        # This is a hack to inject them into the existing model architecture.
        new_cond = np.copy(sample.condition_values)
        new_mask = np.copy(sample.condition_mask)

        # Map key kinetic features to condition slots.
        if len(new_cond) >= 4:
            new_cond[2] = kinetic_features[0]  # apparent order
            new_mask[2] = 1.0
        if len(new_cond) >= 5:
            new_cond[3] = kinetic_features[2]  # activation energy
            new_mask[3] = 1.0
        if len(new_cond) >= 6:
            new_cond[4] = kinetic_features[4]  # max rate position
            new_mask[4] = 1.0

        new_sample = CatalystSample(
            sample_id=sample.sample_id,
            program=sample.program,
            elements=sample.elements,
            fractions=sample.fractions,
            curve_axis=sample.curve_axis,
            curve_values=sample.curve_values,
            curve_channel_mask=sample.curve_channel_mask,
            condition_values=new_cond,
            condition_mask=new_mask,
            reaction_id=sample.reaction_id,
            modality_id=sample.modality_id,
            program_id=sample.program_id,
            target=sample.target,
            target_name=sample.target_name,
            group_id=sample.group_id,
            surface_elements=sample.surface_elements,
            surface_fractions=sample.surface_fractions,
            provenance={
                **sample.provenance,
                "kinetic_features": kinetic_features.tolist(),
                "kinetic_augmented": True,
            },
        )
        augmented.append(new_sample)

    return augmented
