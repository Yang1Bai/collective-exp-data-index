"""Target-label-free expert router for Standard/MHAR model selection.

Routes each sample to the most appropriate frozen expert using only
epistemic disagreement, input-domain distance, and predictive uncertainty.
Never accesses target labels for routing decisions.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np
import torch
from torch import Tensor

from .data import CatalystSample
from .model import CatalystAttentionConfig, CatalystTransferTransformer
from .training import (
    BatchCollator,
    FeatureNormalizer,
    LatentSupportCalibrator,
    TrainingConfig,
    adapt_model,
    calibrate_support,
    few_shot_experiment,
    metrics,
    predict,
    targets_array,
    train_source_model,
)


@dataclass(frozen=True)
class ExpertPair:
    """Two independently trained models from the same source data."""

    standard: CatalystTransferTransformer
    mhar: CatalystTransferTransformer
    standard_calibrator: LatentSupportCalibrator
    mhar_calibrator: LatentSupportCalibrator
    normalizer: FeatureNormalizer
    standard_report: dict
    mhar_report: dict


@dataclass
class ExpertRouterOutput:
    """Per-sample routing decisions and combined predictions."""

    mean: np.ndarray
    standard_mean: np.ndarray
    mhar_mean: np.ndarray
    standard_std: np.ndarray
    mhar_std: np.ndarray
    selected_expert: np.ndarray
    strategy: str
    disagreement: np.ndarray
    domain_distance_ratio: np.ndarray
    abstain: np.ndarray
    standard_latent: np.ndarray | None = None
    mhar_latent: np.ndarray | None = None


_VALID_STRATEGIES = frozenset(
    {
        "disagreement_gated",
        "domain_preferring",
        "uncertainty_minimizing",
        "ensemble",
        "oracle",
    }
)

_EXPERT_LABELS = {0: "standard", 1: "mhar"}


class ExpertRouter:
    """Routes each sample to Standard or MHAR expert without target labels.

    Parameters
    ----------
    standard_model:
        Frozen or adapted Standard Transformer model.
    mhar_model:
        Frozen or adapted Delta-MHAR sublayer Transformer model.
    standard_calibrator:
        LatentSupportCalibrator fitted on source latents from the Standard model.
    mhar_calibrator:
        LatentSupportCalibrator fitted on source latents from the MHAR model.
    strategy:
        Routing strategy (see module docstring).  ``oracle`` requires target
        labels and is for upper-bound reference only.
    disagreement_threshold:
        Normalized-disagreement threshold for ``disagreement_gated`` and
        ``ensemble`` strategies.  Calibrated on source validation data when
        not provided.
    """

    def __init__(
        self,
        standard_model: CatalystTransferTransformer,
        mhar_model: CatalystTransferTransformer,
        standard_calibrator: LatentSupportCalibrator,
        mhar_calibrator: LatentSupportCalibrator,
        *,
        strategy: str = "disagreement_gated",
        disagreement_threshold: float | None = None,
    ) -> None:
        if strategy not in _VALID_STRATEGIES:
            raise ValueError(
                f"unsupported strategy {strategy!r}; "
                f"choose from {sorted(_VALID_STRATEGIES)}"
            )
        self.standard_model = standard_model
        self.mhar_model = mhar_model
        self.standard_calibrator = standard_calibrator
        self.mhar_calibrator = mhar_calibrator
        self.strategy = strategy
        self.disagreement_threshold = disagreement_threshold

    def route(
        self,
        samples: Sequence[CatalystSample],
        normalizer: FeatureNormalizer,
        *,
        device: torch.device,
        batch_size: int = 64,
        adaptation: bool = False,
        support_calibrator: LatentSupportCalibrator | None = None,
    ) -> ExpertRouterOutput:
        """Run both experts and route each sample to one without target labels.

        Parameters
        ----------
        samples:
            Target-domain samples to route (targets may be present for
            oracle evaluation but are **never** read by non-oracle strategies).
        normalizer:
            Feature normalizer fitted on source data.
        device:
            Torch device.
        batch_size:
            Inference batch size.
        adaptation:
            Whether the models have been adapted (affects ``adaptation`` flag
            passed to ``predict``).
        support_calibrator:
            Optional external support calibrator forwarded to ``predict``.
        """
        if not samples:
            raise ValueError("routing requires at least one sample")

        standard_result = predict(
            self.standard_model,
            samples,
            normalizer,
            device=device,
            batch_size=batch_size,
            adaptation=adaptation,
            support_calibrator=support_calibrator,
            return_latent=True,
            unknown_program=True,
        )
        mhar_result = predict(
            self.mhar_model,
            samples,
            normalizer,
            device=device,
            batch_size=batch_size,
            adaptation=adaptation,
            support_calibrator=support_calibrator,
            return_latent=True,
            unknown_program=True,
        )

        standard_mean = standard_result["mean"]
        mhar_mean = mhar_result["mean"]
        standard_std = standard_result["std"]
        mhar_std = mhar_result["std"]
        standard_latent = standard_result.get("latent")
        mhar_latent = mhar_result.get("latent")

        # Disagreement: normalized absolute difference in predictions.
        pooled_std = np.sqrt(
            np.maximum(standard_std**2 + mhar_std**2, 1e-12)
        )
        disagreement = np.abs(standard_mean - mhar_mean) / pooled_std

        # Domain distance ratio: < 1 means Standard is closer to source.
        standard_ood = self.standard_calibrator.ood_score(standard_latent)
        mhar_ood = self.mhar_calibrator.ood_score(mhar_latent)
        domain_ratio = np.full_like(standard_ood, 1.0)
        valid = (standard_ood + mhar_ood) > 1e-12
        domain_ratio[valid] = standard_ood[valid] / (
            standard_ood[valid] + mhar_ood[valid]
        )

        # Uncertainty ratio: < 1 means Standard is more confident.
        uncertainty_ratio = np.full_like(standard_std, 1.0)
        valid_unc = (standard_std + mhar_std) > 1e-12
        uncertainty_ratio[valid_unc] = standard_std[valid_unc] / (
            standard_std[valid_unc] + mhar_std[valid_unc]
        )

        # Strategy-specific routing.
        selected, mean, abstain = _apply_strategy(
            strategy=self.strategy,
            standard_mean=standard_mean,
            mhar_mean=mhar_mean,
            disagreement=disagreement,
            domain_ratio=domain_ratio,
            uncertainty_ratio=uncertainty_ratio,
            threshold=self.disagreement_threshold,
            samples=samples,
        )

        return ExpertRouterOutput(
            mean=mean,
            standard_mean=standard_mean,
            mhar_mean=mhar_mean,
            standard_std=standard_std,
            mhar_std=mhar_std,
            selected_expert=selected,
            strategy=self.strategy,
            disagreement=disagreement,
            domain_distance_ratio=domain_ratio,
            abstain=abstain,
            standard_latent=standard_latent,
            mhar_latent=mhar_latent,
        )


def _apply_strategy(
    *,
    strategy: str,
    standard_mean: np.ndarray,
    mhar_mean: np.ndarray,
    disagreement: np.ndarray,
    domain_ratio: np.ndarray,
    uncertainty_ratio: np.ndarray,
    threshold: float | None,
    samples: Sequence[CatalystSample],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Internal routing dispatch.  Returns (selected_expert, mean, abstain)."""
    n = len(standard_mean)

    if strategy == "oracle":
        targets = targets_array(samples)
        standard_error = np.abs(standard_mean - targets)
        mhar_error = np.abs(mhar_mean - targets)
        selected = np.where(standard_error <= mhar_error, 0, 1)
        mean = np.where(selected == 0, standard_mean, mhar_mean)
        return selected, mean, np.zeros(n, dtype=bool)

    if strategy == "ensemble":
        mean = 0.5 * (standard_mean + mhar_mean)
        selected = np.full(n, -1, dtype=int)
        eff_threshold = threshold
        if eff_threshold is None:
            eff_threshold = float(np.quantile(disagreement, 0.90))
        abstain = disagreement > eff_threshold
        return selected, mean, abstain

    if strategy == "domain_preferring":
        # domain_ratio < 0.5 means Standard is closer.
        selected = np.where(domain_ratio < 0.5, 0, 1)
        mean = np.where(selected == 0, standard_mean, mhar_mean)
        return selected, mean, np.zeros(n, dtype=bool)

    if strategy == "uncertainty_minimizing":
        # uncertainty_ratio < 0.5 means Standard is more confident.
        selected = np.where(uncertainty_ratio < 0.5, 0, 1)
        mean = np.where(selected == 0, standard_mean, mhar_mean)
        return selected, mean, np.zeros(n, dtype=bool)

    # disagreement_gated (default).
    eff_threshold = threshold
    if eff_threshold is None:
        eff_threshold = float(np.quantile(disagreement, 0.90))
    high_disagreement = disagreement > eff_threshold
    selected = np.full(n, -1, dtype=int)
    selected[high_disagreement] = np.where(
        domain_ratio[high_disagreement] < 0.5, 0, 1
    )
    mean = 0.5 * (standard_mean + mhar_mean)
    mean[high_disagreement] = np.where(
        selected[high_disagreement] == 0,
        standard_mean[high_disagreement],
        mhar_mean[high_disagreement],
    )
    return selected, mean, np.zeros(n, dtype=bool)


def train_expert_pair(
    source_samples: Sequence[CatalystSample],
    model_config: CatalystAttentionConfig,
    training_config: TrainingConfig,
    *,
    device: torch.device,
) -> ExpertPair:
    """Train Standard and Delta-MHAR-sublayer models from the same source.

    Both models share the same seed, data split, and normalizer so the only
    systematic difference is the depth-routing architecture.
    """
    if len(source_samples) < 20:
        raise ValueError("expert pair training requires at least 20 samples")

    standard_config = replace(model_config, depth_routing="standard")
    standard_model, normalizer, standard_report = train_source_model(
        source_samples,
        standard_config,
        training_config,
        device=device,
    )

    mhar_config = replace(model_config, depth_routing="delta_mhar_sublayer")
    # Re-seed to the same value so data splits are identical.
    mhar_model, _, mhar_report = train_source_model(
        source_samples,
        mhar_config,
        training_config,
        device=device,
    )

    standard_calibrator = calibrate_support(
        standard_model,
        source_samples,
        normalizer,
        device=device,
        batch_size=training_config.batch_size,
    )
    mhar_calibrator = calibrate_support(
        mhar_model,
        source_samples,
        normalizer,
        device=device,
        batch_size=training_config.batch_size,
    )

    return ExpertPair(
        standard=standard_model,
        mhar=mhar_model,
        standard_calibrator=standard_calibrator,
        mhar_calibrator=mhar_calibrator,
        normalizer=normalizer,
        standard_report=standard_report,
        mhar_report=mhar_report,
    )


def calibrate_disagreement_threshold(
    pair: ExpertPair,
    source_samples: Sequence[CatalystSample],
    *,
    device: torch.device,
    quantile: float = 0.90,
) -> float:
    """Calibrate the disagreement threshold on source validation data only.

    Uses a temporary router with the ``disagreement_gated`` strategy to
    compute normalized disagreement on source samples.  The threshold is
    the given quantile of that distribution.
    """
    router = ExpertRouter(
        pair.standard,
        pair.mhar,
        pair.standard_calibrator,
        pair.mhar_calibrator,
        strategy="disagreement_gated",
    )
    output = router.route(
        source_samples,
        pair.normalizer,
        device=device,
        adaptation=False,
    )
    return float(np.quantile(output.disagreement, quantile))


def evaluate_router(
    pair: ExpertPair,
    source_samples: Sequence[CatalystSample],
    target_samples: Sequence[CatalystSample],
    training_config: TrainingConfig,
    *,
    anchors: int = 5,
    draws: int = 20,
    strategies: Sequence[str] | None = None,
    seed: int,
    device: torch.device,
) -> dict:
    """Evaluate the expert router on a transfer pair with few-shot adaptation.

    For each draw:
    1. Randomly select anchor indices from the target samples.
    2. Adapt both Standard and MHAR models on the same anchors.
    3. Route test samples through all requested strategies.
    4. Compare routed predictions against single-expert baselines.

    The router never sees target labels on test samples (the ``oracle``
    strategy is excluded from evaluation by default).
    """
    if strategies is None:
        strategies = [
            "disagreement_gated",
            "domain_preferring",
            "uncertainty_minimizing",
            "ensemble",
        ]
    invalid = set(strategies) - _VALID_STRATEGIES
    if invalid:
        raise ValueError(f"unsupported strategies: {sorted(invalid)}")

    if anchors >= len(target_samples):
        raise ValueError("anchor budget must leave held-out target samples")

    rng = np.random.default_rng(seed)
    all_targets = targets_array(target_samples)

    # Pre-compute zero-shot predictions for bias calibration.
    zero_standard = predict(
        pair.standard,
        target_samples,
        pair.normalizer,
        device=device,
        support_calibrator=pair.standard_calibrator,
        unknown_program=True,
    )
    zero_mhar = predict(
        pair.mhar,
        target_samples,
        pair.normalizer,
        device=device,
        support_calibrator=pair.mhar_calibrator,
        unknown_program=True,
    )
    disagreement_threshold = calibrate_disagreement_threshold(
        pair, source_samples, device=device
    )

    # Accumulate per-strategy metrics across draws.
    strategy_rows: dict[str, list[dict[str, float]]] = {
        s: [] for s in strategies
    }
    standard_rows: list[dict[str, float]] = []
    mhar_rows: list[dict[str, float]] = []
    oracle_rows: list[dict[str, float]] = []
    routing_agreement: dict[str, list[float]] = {s: [] for s in strategies}

    for draw in range(draws):
        anchor_indices = np.sort(
            rng.choice(len(target_samples), size=anchors, replace=False)
        )
        mask = np.ones(len(target_samples), dtype=bool)
        mask[anchor_indices] = False
        test_indices = np.flatnonzero(mask)

        adapter_config = TrainingConfig(
            **{
                **vars(training_config),
                "seed": seed + draw * 17,
            }
        )
        anchor_list = [target_samples[i] for i in anchor_indices]
        test_list = [target_samples[i] for i in test_indices]

        # Adapt both models on the same anchors.
        adapted_standard = adapt_model(
            pair.standard,
            anchor_list,
            pair.normalizer,
            pair.standard_calibrator,
            adapter_config,
            device=device,
        )
        adapted_mhar = adapt_model(
            pair.mhar,
            anchor_list,
            pair.normalizer,
            pair.mhar_calibrator,
            adapter_config,
            device=device,
        )

        # Single-expert baselines.
        standard_pred = predict(
            adapted_standard,
            test_list,
            pair.normalizer,
            device=device,
            adaptation=True,
            support_calibrator=pair.standard_calibrator,
            unknown_program=True,
        )["mean"]
        mhar_pred = predict(
            adapted_mhar,
            test_list,
            pair.normalizer,
            device=device,
            adaptation=True,
            support_calibrator=pair.mhar_calibrator,
            unknown_program=True,
        )["mean"]

        test_targets = all_targets[test_indices]
        standard_rows.append(metrics(test_targets, standard_pred))
        mhar_rows.append(metrics(test_targets, mhar_pred))

        # Oracle upper bound.
        combined = np.column_stack([standard_pred, mhar_pred])
        standard_err = np.abs(standard_pred - test_targets)
        mhar_err = np.abs(mhar_pred - test_targets)
        oracle_pred = np.where(standard_err <= mhar_err, standard_pred, mhar_pred)
        oracle_rows.append(metrics(test_targets, oracle_pred))

        for strategy in strategies:
            is_oracle = strategy == "oracle"
            router = ExpertRouter(
                adapted_standard,
                adapted_mhar,
                pair.standard_calibrator,
                pair.mhar_calibrator,
                strategy=strategy,
                disagreement_threshold=disagreement_threshold,
            )
            output = router.route(
                test_list,
                pair.normalizer,
                device=device,
                adaptation=True,
                support_calibrator=None,
            )
            strategy_rows[strategy].append(
                metrics(test_targets, output.mean)
            )
            if not is_oracle and output.selected_expert is not None:
                oracle_selected = np.where(
                    standard_err <= mhar_err, 0, 1
                )
                routed = output.selected_expert
                agreement = np.mean(
                    (routed == oracle_selected) | (routed == -1)
                )
                routing_agreement[strategy].append(float(agreement))

    def _summarize(
        rows: list[dict[str, float]],
    ) -> dict[str, dict[str, float | list[float]]]:
        if not rows:
            return {}
        return {
            key: {
                "median": float(np.median([r[key] for r in rows])),
                "ci90": [
                    float(np.quantile([r[key] for r in rows], 0.05)),
                    float(np.quantile([r[key] for r in rows], 0.95)),
                ],
            }
            for key in rows[0]
        }

    result: dict = {
        "anchors": anchors,
        "draws": draws,
        "disagreement_threshold": disagreement_threshold,
        "standard": _summarize(standard_rows),
        "mhar": _summarize(mhar_rows),
        "oracle_upper_bound": _summarize(oracle_rows),
        "strategies": {},
        "source_model_metrics": {
            "standard": pair.standard_report.get(
                "source_apparent_metrics", {}
            ),
            "mhar": pair.mhar_report.get("source_apparent_metrics", {}),
        },
    }

    for strategy in strategies:
        rows = strategy_rows[strategy]
        summary = _summarize(rows)
        gains_vs_standard = []
        gains_vs_mhar = []
        for s_row, m_row, r_row in zip(
            standard_rows, mhar_rows, rows, strict=True
        ):
            gains_vs_standard.append(
                r_row["spearman"] - s_row["spearman"]
            )
            gains_vs_mhar.append(r_row["spearman"] - m_row["spearman"])

        strategy_result: dict = {
            "metrics": summary,
            "spearman_gain_vs_standard": {
                "median": float(np.median(gains_vs_standard)),
                "ci90": [
                    float(np.quantile(gains_vs_standard, 0.05)),
                    float(np.quantile(gains_vs_standard, 0.95)),
                ],
            },
            "spearman_gain_vs_mhar": {
                "median": float(np.median(gains_vs_mhar)),
                "ci90": [
                    float(np.quantile(gains_vs_mhar, 0.05)),
                    float(np.quantile(gains_vs_mhar, 0.95)),
                ],
            },
            "draw_metrics": rows,
        }
        if strategy in routing_agreement:
            agreement = routing_agreement[strategy]
            strategy_result["oracle_agreement"] = {
                "median": float(np.median(agreement)),
                "ci90": [
                    float(np.quantile(agreement, 0.05)),
                    float(np.quantile(agreement, 0.95)),
                ],
            }
        result["strategies"][strategy] = strategy_result

    # Decision: does any strategy beat both single experts?
    best_strategy = None
    best_median_gain = -float("inf")
    for strategy in strategies:
        gains = strategy_rows[strategy]
        if not gains:
            continue
        median_spearman = float(np.median([r["spearman"] for r in gains]))
        standard_median = float(
            np.median([r["spearman"] for r in standard_rows])
        )
        mhar_median = float(
            np.median([r["spearman"] for r in mhar_rows])
        )
        gain = median_spearman - max(standard_median, mhar_median)
        if gain > best_median_gain:
            best_median_gain = gain
            best_strategy = strategy

    result["decision"] = {
        "best_strategy": best_strategy,
        "best_median_gain_over_single_expert": best_median_gain,
        "beats_both_single_experts": best_median_gain > 0.0,
    }

    return result


def router_audit_trail(
    output: ExpertRouterOutput,
    sample_ids: list[str],
) -> list[dict]:
    """Convert a router output to a human-readable per-sample audit trail."""
    rows = []
    for i in range(len(output.mean)):
        expert_label = (
            _EXPERT_LABELS.get(int(output.selected_expert[i]), "ensemble")
            if output.selected_expert is not None
            else "ensemble"
        )
        rows.append(
            {
                "sample_id": sample_ids[i],
                "standard_mean": float(output.standard_mean[i]),
                "mhar_mean": float(output.mhar_mean[i]),
                "routed_mean": float(output.mean[i]),
                "selected_expert": expert_label,
                "disagreement": float(output.disagreement[i]),
                "domain_distance_ratio": float(
                    output.domain_distance_ratio[i]
                ),
                "abstain": bool(output.abstain[i]),
            }
        )
    return rows
