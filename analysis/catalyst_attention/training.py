"""Leakage-aware training, adaptation, baselines, and evaluation."""
from __future__ import annotations

import copy
import json
import os
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from scipy import stats
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch import Tensor, nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from .data import (
    CONDITION_NAMES,
    CatalystSample,
    atomic_write_text,
    target_id,
)
from .model import CatalystAttentionConfig, CatalystTransferTransformer
from .optimizers import build_optimizer
from .schema import schema_manifest


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 20260731
    epochs: int = 180
    patience: int = 30
    batch_size: int = 32
    learning_rate: float = 8e-4
    weight_decay: float = 2e-4
    rank_weight: float = 0.22
    nll_weight: float = 0.18
    support_weight: float = 0.02
    validation_fraction: float = 0.18
    gradient_clip: float = 1.0
    adapter_epochs: int = 240
    adapter_learning_rate: float = 2e-3
    adapter_weight_decay: float = 0.05
    optimizer: str = "adamw"
    shampoo_beta1: float = 0.9
    shampoo_beta2: float = 0.999
    shampoo_epsilon: float = 1e-12
    shampoo_grafting_epsilon: float = 1e-8
    shampoo_max_preconditioner_dim: int = 64
    shampoo_precondition_frequency: int = 10
    shampoo_start_preconditioning_step: int = 10
    domain_alignment_weight: float = 0.0
    domain_adversarial_weight: float = 0.0
    grl_lambda: float = 1.0
    contrastive_weight: float = 0.0
    contrastive_temperature: float = 0.1


@dataclass
class FeatureNormalizer:
    curve_mean: np.ndarray
    curve_std: np.ndarray
    axis_min: float
    axis_max: float
    condition_mean: np.ndarray
    condition_std: np.ndarray
    target_mean: float
    target_std: float

    @classmethod
    def fit(cls, samples: Sequence[CatalystSample]) -> "FeatureNormalizer":
        if not samples:
            raise ValueError("cannot fit normalizer without samples")
        curve_chunks = [
            sample.curve_values
            for sample in samples
            if len(sample.curve_values)
        ]
        if curve_chunks:
            curve = np.concatenate(curve_chunks, axis=0).astype(np.float64)
            curve_mean = curve.mean(axis=0)
            curve_std = curve.std(axis=0)
            axes = np.concatenate(
                [sample.curve_axis for sample in samples if len(sample.curve_axis)]
            )
            axis_min = float(np.min(axes))
            axis_max = float(np.max(axes))
        else:
            curve_mean = np.zeros(2, dtype=float)
            curve_std = np.ones(2, dtype=float)
            axis_min, axis_max = 0.0, 1.0
        curve_std = np.where(curve_std > 1e-8, curve_std, 1.0)
        condition_values = np.stack([sample.condition_values for sample in samples])
        condition_masks = np.stack([sample.condition_mask for sample in samples])
        condition_mean = np.zeros(len(CONDITION_NAMES), dtype=float)
        condition_std = np.ones(len(CONDITION_NAMES), dtype=float)
        for index in range(len(CONDITION_NAMES)):
            observed = condition_values[condition_masks[:, index] > 0, index]
            if len(observed):
                condition_mean[index] = float(np.mean(observed))
                scale = float(np.std(observed))
                condition_std[index] = scale if scale > 1e-8 else 1.0
        targets = targets_array(samples)
        target_std = float(np.std(targets))
        return cls(
            curve_mean=np.asarray(curve_mean, dtype=np.float32),
            curve_std=np.asarray(curve_std, dtype=np.float32),
            axis_min=axis_min,
            axis_max=axis_max,
            condition_mean=np.asarray(condition_mean, dtype=np.float32),
            condition_std=np.asarray(condition_std, dtype=np.float32),
            target_mean=float(np.mean(targets)),
            target_std=target_std if target_std > 1e-8 else 1.0,
        )

    def transform_axis(self, axis: np.ndarray) -> np.ndarray:
        span = max(self.axis_max - self.axis_min, 1e-8)
        return (2.0 * (axis - self.axis_min) / span - 1.0).astype(np.float32)

    def transform_curve(self, values: np.ndarray, channel_mask: np.ndarray) -> np.ndarray:
        transformed = (values - self.curve_mean) / self.curve_std
        return (transformed * channel_mask[None, :]).astype(np.float32)

    def transform_conditions(
        self, values: np.ndarray, mask: np.ndarray
    ) -> np.ndarray:
        transformed = (values - self.condition_mean) / self.condition_std
        return (transformed * mask).astype(np.float32)

    def transform_target(self, target: float | np.ndarray) -> np.ndarray:
        return (np.asarray(target) - self.target_mean) / self.target_std

    def inverse_target(self, target: float | np.ndarray) -> np.ndarray:
        return np.asarray(target) * self.target_std + self.target_mean

    def to_json(self) -> dict:
        return {
            "curve_mean": self.curve_mean.tolist(),
            "curve_std": self.curve_std.tolist(),
            "axis_min": self.axis_min,
            "axis_max": self.axis_max,
            "condition_mean": self.condition_mean.tolist(),
            "condition_std": self.condition_std.tolist(),
            "target_mean": self.target_mean,
            "target_std": self.target_std,
        }

    @classmethod
    def from_json(cls, value: dict) -> "FeatureNormalizer":
        return cls(
            curve_mean=np.asarray(value["curve_mean"], dtype=np.float32),
            curve_std=np.asarray(value["curve_std"], dtype=np.float32),
            axis_min=float(value["axis_min"]),
            axis_max=float(value["axis_max"]),
            condition_mean=np.asarray(value["condition_mean"], dtype=np.float32),
            condition_std=np.asarray(value["condition_std"], dtype=np.float32),
            target_mean=float(value["target_mean"]),
            target_std=float(value["target_std"]),
        )


class _Samples(Dataset):
    def __init__(self, samples: Sequence[CatalystSample]) -> None:
        self.samples = list(samples)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> CatalystSample:
        return self.samples[index]


class BatchCollator:
    def __init__(
        self,
        normalizer: FeatureNormalizer,
        *,
        unknown_program: bool = False,
        require_target: bool = True,
    ) -> None:
        self.normalizer = normalizer
        self.unknown_program = unknown_program
        self.require_target = require_target

    def __call__(self, samples: Sequence[CatalystSample]) -> dict[str, Tensor | list[str]]:
        batch = len(samples)
        max_elements = max(len(sample.elements) for sample in samples)
        max_surface = max(1, max(len(sample.surface_elements) for sample in samples))
        max_curve = max(1, max(len(sample.curve_axis) for sample in samples))
        elements = torch.zeros((batch, max_elements), dtype=torch.long)
        fractions = torch.zeros((batch, max_elements), dtype=torch.float32)
        composition_mask = torch.ones((batch, max_elements), dtype=torch.bool)
        surface_elements = torch.zeros((batch, max_surface), dtype=torch.long)
        surface_fractions = torch.zeros((batch, max_surface), dtype=torch.float32)
        surface_mask = torch.ones((batch, max_surface), dtype=torch.bool)
        surface_present = torch.zeros(batch, dtype=torch.bool)
        axis = torch.zeros((batch, max_curve), dtype=torch.float32)
        values = torch.zeros((batch, max_curve, 2), dtype=torch.float32)
        curve_mask = torch.ones((batch, max_curve), dtype=torch.bool)
        channel_mask = torch.zeros((batch, 2), dtype=torch.float32)
        curve_present = torch.zeros(batch, dtype=torch.bool)
        conditions = torch.zeros(
            (batch, len(CONDITION_NAMES)), dtype=torch.float32
        )
        condition_mask = torch.zeros_like(conditions)
        reaction = torch.zeros(batch, dtype=torch.long)
        modality = torch.zeros(batch, dtype=torch.long)
        program = torch.zeros(batch, dtype=torch.long)
        target_type = torch.zeros(batch, dtype=torch.long)
        targets = torch.zeros(batch, dtype=torch.float32)
        for row, sample in enumerate(samples):
            count = len(sample.elements)
            elements[row, :count] = torch.from_numpy(sample.elements)
            fractions[row, :count] = torch.from_numpy(sample.fractions)
            composition_mask[row, :count] = False
            surface_count = len(sample.surface_elements)
            if surface_count:
                surface_elements[row, :surface_count] = torch.from_numpy(
                    sample.surface_elements
                )
                surface_fractions[row, :surface_count] = torch.from_numpy(
                    sample.surface_fractions
                )
                surface_mask[row, :surface_count] = False
                surface_present[row] = True
            length = len(sample.curve_axis)
            if length:
                axis[row, :length] = torch.from_numpy(
                    self.normalizer.transform_axis(sample.curve_axis)
                )
                values[row, :length] = torch.from_numpy(
                    self.normalizer.transform_curve(
                        sample.curve_values, sample.curve_channel_mask
                    )
                )
                curve_mask[row, :length] = False
                curve_present[row] = True
            channel_mask[row] = torch.from_numpy(sample.curve_channel_mask)
            conditions[row] = torch.from_numpy(
                self.normalizer.transform_conditions(
                    sample.condition_values, sample.condition_mask
                )
            )
            condition_mask[row] = torch.from_numpy(sample.condition_mask)
            reaction[row] = sample.reaction_id
            modality[row] = sample.modality_id
            program[row] = 0 if self.unknown_program else sample.program_id
            target_type[row] = target_id(sample.target_name)
            if self.require_target:
                if sample.target is None:
                    raise ValueError(
                        f"training sample {sample.sample_id} has no target"
                    )
                targets[row] = float(
                    self.normalizer.transform_target(sample.target)
                )
        result = {
            "elements": elements,
            "fractions": fractions,
            "composition_padding_mask": composition_mask,
            "surface_elements": surface_elements,
            "surface_fractions": surface_fractions,
            "surface_padding_mask": surface_mask,
            "surface_present": surface_present,
            "curve_axis": axis,
            "curve_values": values,
            "curve_padding_mask": curve_mask,
            "curve_channel_mask": channel_mask,
            "curve_present": curve_present,
            "condition_values": conditions,
            "condition_mask": condition_mask,
            "reaction_id": reaction,
            "modality_id": modality,
            "program_id": program,
            "target_id": target_type,
            "sample_ids": [sample.sample_id for sample in samples],
            "group_ids": [sample.group_id for sample in samples],
        }
        if self.require_target:
            result["target"] = targets
        return result


def targets_array(samples: Sequence[CatalystSample]) -> np.ndarray:
    missing = [sample.sample_id for sample in samples if sample.target is None]
    if missing:
        preview = ", ".join(missing[:3])
        raise ValueError(f"supervised operation requires targets; missing: {preview}")
    return np.asarray([sample.target for sample in samples], dtype=float)


def set_deterministic(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))


def _to_device(batch: dict[str, Tensor | list[str]], device: torch.device) -> dict:
    return {
        key: value.to(device) if isinstance(value, Tensor) else value
        for key, value in batch.items()
    }


def pairwise_rank_loss(prediction: Tensor, target: Tensor) -> Tensor:
    differences = target[:, None] - target[None, :]
    prediction_differences = prediction[:, None] - prediction[None, :]
    valid = differences.abs() > 1e-5
    valid &= ~torch.eye(len(target), dtype=torch.bool, device=target.device)
    if not valid.any():
        return prediction.sum() * 0.0
    direction = differences.sign()
    return F.softplus(-direction[valid] * prediction_differences[valid]).mean()


def training_loss(
    output: dict[str, Tensor | dict[str, Tensor]],
    target: Tensor,
    config: TrainingConfig,
) -> tuple[Tensor, dict[str, float]]:
    mean = output["mean"]
    log_variance = output["log_variance"]
    source_support = output["source_support"]
    assert isinstance(mean, Tensor)
    assert isinstance(log_variance, Tensor)
    assert isinstance(source_support, Tensor)
    regression = F.smooth_l1_loss(mean, target, beta=0.5)
    nll = 0.5 * (torch.exp(-log_variance) * (mean - target).square() + log_variance)
    nll = nll.mean()
    ranking = pairwise_rank_loss(mean, target)
    support = F.binary_cross_entropy(source_support, torch.ones_like(source_support))
    total = (
        (1.0 - config.rank_weight - config.nll_weight) * regression
        + config.rank_weight * ranking
        + config.nll_weight * nll
        + config.support_weight * support
    )
    return total, {
        "regression": float(regression.detach()),
        "nll": float(nll.detach()),
        "ranking": float(ranking.detach()),
        "support": float(support.detach()),
    }


def coral_alignment_loss(source: Tensor, target: Tensor) -> Tensor:
    """Match latent first and second moments using no target outcomes."""
    if source.ndim != 2 or target.ndim != 2:
        raise ValueError("CORAL alignment expects two latent matrices")
    if source.shape[1] != target.shape[1]:
        raise ValueError("CORAL latent widths must match")
    source = F.layer_norm(source, (source.shape[-1],))
    target = F.layer_norm(target, (target.shape[-1],))
    mean_loss = (source.mean(dim=0) - target.mean(dim=0)).square().mean()

    def covariance(value: Tensor) -> Tensor:
        centered = value - value.mean(dim=0, keepdim=True)
        return centered.T @ centered / max(len(value) - 1, 1)

    covariance_loss = (
        covariance(source) - covariance(target)
    ).square().mean()
    return mean_loss + covariance_loss


def metrics(y_true: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    rank = stats.spearmanr(y_true, prediction).statistic
    return {
        "rmse": float(mean_squared_error(y_true, prediction) ** 0.5),
        "mae": float(mean_absolute_error(y_true, prediction)),
        "r2": float(r2_score(y_true, prediction)),
        "spearman": float(rank) if np.isfinite(rank) else 0.0,
    }


@torch.no_grad()
def predict(
    model: CatalystTransferTransformer,
    samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    *,
    device: torch.device,
    batch_size: int = 64,
    adaptation: bool = False,
    support_calibrator: "LatentSupportCalibrator | None" = None,
    return_latent: bool = False,
    unknown_program: bool = False,
) -> dict[str, np.ndarray]:
    if not samples:
        raise ValueError("prediction requires at least one sample")
    model.eval()
    loader = DataLoader(
        _Samples(samples),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=BatchCollator(
            normalizer,
            unknown_program=unknown_program,
            require_target=False,
        ),
    )
    outputs: dict[str, list[np.ndarray]] = {
        "mean": [],
        "base_mean": [],
        "std": [],
        "support": [],
        "latent": [],
    }
    for raw_batch in loader:
        batch = _to_device(raw_batch, device)
        latent, _ = model.encode(batch)
        external = None
        if support_calibrator is not None:
            external = torch.as_tensor(
                support_calibrator.support(latent.detach().cpu().numpy()),
                dtype=latent.dtype,
                device=device,
            )
        result = model(
            batch,
            adaptation=adaptation,
            external_source_support=external,
        )
        for key in ("mean", "base_mean", "source_support", "log_variance", "latent"):
            value = result[key]
            assert isinstance(value, Tensor)
            if key == "source_support":
                outputs["support"].append(value.detach().cpu().numpy())
            elif key == "log_variance":
                outputs["std"].append(
                    np.exp(0.5 * value.detach().cpu().numpy()) * normalizer.target_std
                )
            else:
                outputs[key].append(value.detach().cpu().numpy())
    means = normalizer.inverse_target(np.concatenate(outputs["mean"]))
    base = normalizer.inverse_target(np.concatenate(outputs["base_mean"]))
    result = {
        "mean": means,
        "base_mean": base,
        "std": np.concatenate(outputs["std"]),
        "support": np.concatenate(outputs["support"]),
    }
    if return_latent:
        result["latent"] = np.concatenate(outputs["latent"])
    return result


def _validation_score(y_true: np.ndarray, prediction: np.ndarray) -> float:
    score = metrics(y_true, prediction)
    scale = max(float(np.std(y_true)), 1e-8)
    return score["rmse"] / scale - 0.25 * score["spearman"]


def train_source_model(
    samples: Sequence[CatalystSample],
    model_config: CatalystAttentionConfig,
    training_config: TrainingConfig,
    *,
    device: torch.device | None = None,
    unlabeled_target_samples: Sequence[CatalystSample] | None = None,
) -> tuple[CatalystTransferTransformer, FeatureNormalizer, dict]:
    if len(samples) < 20:
        raise ValueError("source training requires at least 20 samples")
    set_deterministic(training_config.seed)
    device = device or torch.device("cpu")
    indices = np.arange(len(samples))
    groups = np.asarray([sample.group_id for sample in samples])
    if len(set(groups.tolist())) >= 5:
        splitter = GroupShuffleSplit(
            n_splits=1,
            test_size=training_config.validation_fraction,
            random_state=training_config.seed,
        )
        train_indices, validation_indices = next(
            splitter.split(indices, groups=groups)
        )
    else:
        train_indices, validation_indices = train_test_split(
            indices,
            test_size=training_config.validation_fraction,
            random_state=training_config.seed,
        )
    train_samples = [samples[index] for index in train_indices]
    validation_samples = [samples[index] for index in validation_indices]
    normalizer = FeatureNormalizer.fit(train_samples)
    train_loader = DataLoader(
        _Samples(train_samples),
        batch_size=training_config.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(training_config.seed),
        collate_fn=BatchCollator(normalizer),
    )
    target_loader = None
    use_target_batches = (
        training_config.domain_alignment_weight > 0.0
        or training_config.domain_adversarial_weight > 0.0
    )
    if use_target_batches:
        if not unlabeled_target_samples:
            if training_config.domain_adversarial_weight > 0.0:
                import warnings
                warnings.warn(
                    "adversarial domain adaptation requires unlabeled "
                    "target samples; disabling adversarial loss for "
                    "this training run"
                )
            use_target_batches = bool(
                training_config.domain_alignment_weight > 0.0
            )
    if use_target_batches:
        target_loader = DataLoader(
            _Samples(unlabeled_target_samples),
            batch_size=training_config.batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(
                training_config.seed + 1701
            ),
            collate_fn=BatchCollator(
                normalizer,
                unknown_program=True,
                require_target=False,
            ),
        )
    model = CatalystTransferTransformer(model_config).to(device)
    domain_classifier = None
    if training_config.domain_adversarial_weight > 0.0:
        from .domain_adversarial import (  # noqa: E402
            DomainClassifier,
            adversarial_domain_loss,
            grl_lambda_schedule,
        )
        domain_classifier = DomainClassifier(
            model_config.d_model, n_domains=2
        ).to(device)
    contrastive_projection = None
    if training_config.contrastive_weight > 0.0:
        from .contrastive import ContrastiveProjection, contrastive_loss  # noqa: E402
        contrastive_projection = ContrastiveProjection(
            model_config.d_model,
        ).to(device)
    optimizer, optimizer_manifest = build_optimizer(
        model, training_config
    )
    if domain_classifier is not None:
        optimizer.add_param_group(
            {"params": domain_classifier.parameters()}
        )
    if contrastive_projection is not None:
        optimizer.add_param_group(
            {"params": contrastive_projection.parameters()}
        )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=max(5, training_config.patience // 4)
    )
    best_state = copy.deepcopy(model.state_dict())
    best_score = float("inf")
    best_epoch = 0
    history: list[dict] = []
    for epoch in range(training_config.epochs):
        model.train()
        epoch_loss = 0.0
        seen = 0
        components: dict[str, float] = {}
        target_iterator = iter(target_loader) if target_loader else None
        for raw_batch in train_loader:
            batch = _to_device(raw_batch, device)
            optimizer.zero_grad(set_to_none=True)
            output = model(batch)
            target = batch["target"]
            loss, parts = training_loss(output, target, training_config)
            if target_iterator is not None:
                try:
                    raw_target_batch = next(target_iterator)
                except StopIteration:
                    assert target_loader is not None
                    target_iterator = iter(target_loader)
                    raw_target_batch = next(target_iterator)
                target_batch = _to_device(raw_target_batch, device)
                target_output = model(target_batch)
                source_latent = output["latent"]
                target_latent = target_output["latent"]
                assert isinstance(source_latent, Tensor)
                assert isinstance(target_latent, Tensor)
                alignment = coral_alignment_loss(
                    source_latent, target_latent
                )
                loss = (
                    loss
                    + training_config.domain_alignment_weight
                    * alignment
                )
                parts["domain_alignment"] = float(
                    alignment.detach()
                )
                if domain_classifier is not None:
                    combined_latent = torch.cat(
                        [source_latent, target_latent], dim=0
                    )
                    domain_ids = torch.cat(
                        [
                            torch.zeros(
                                len(source_latent),
                                dtype=torch.long,
                                device=device,
                            ),
                            torch.ones(
                                len(target_latent),
                                dtype=torch.long,
                                device=device,
                            ),
                        ]
                    )
                    adv_loss, adv_accuracy = adversarial_domain_loss(
                        combined_latent,
                        domain_ids,
                        domain_classifier,
                        grl_lambda=training_config.grl_lambda,
                    )
                    loss = (
                        loss
                        + training_config.domain_adversarial_weight
                        * adv_loss
                    )
                    parts["domain_adversarial"] = float(
                        adv_loss.detach()
                    )
                    parts["domain_classifier_accuracy"] = adv_accuracy
            if contrastive_projection is not None:
                cont_loss, cont_diag = contrastive_loss(
                    output["latent"],
                    batch["elements"],
                    batch["fractions"],
                    contrastive_projection,
                    similarity_threshold=0.7,
                    temperature=training_config.contrastive_temperature,
                )
                loss = (
                    loss
                    + training_config.contrastive_weight
                    * cont_loss
                )
                parts["contrastive"] = float(cont_loss.detach())
                parts["contrastive_pairs"] = float(
                    cont_diag["n_positive_pairs"]
                )
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), training_config.gradient_clip)
            optimizer.step()
            count = len(target)
            epoch_loss += float(loss.detach()) * count
            seen += count
            for key, value in parts.items():
                components[key] = components.get(key, 0.0) + value * count
        prediction = predict(
            model,
            validation_samples,
            normalizer,
            device=device,
            batch_size=training_config.batch_size,
            unknown_program=False,
        )["mean"]
        y_validation = targets_array(validation_samples)
        score = _validation_score(y_validation, prediction)
        scheduler.step(score)
        row = {
            "epoch": epoch + 1,
            "train_loss": epoch_loss / max(seen, 1),
            "validation_score": score,
            "validation": metrics(y_validation, prediction),
            "learning_rate": optimizer.param_groups[0]["lr"],
            **{f"loss_{key}": value / max(seen, 1) for key, value in components.items()},
        }
        history.append(row)
        if score < best_score - 1e-5:
            best_score = score
            best_epoch = epoch + 1
            best_state = copy.deepcopy(model.state_dict())
        if epoch + 1 - best_epoch >= training_config.patience:
            break
    model.load_state_dict(best_state)
    source_prediction = predict(
        model,
        samples,
        normalizer,
        device=device,
        batch_size=training_config.batch_size,
        return_latent=True,
    )
    source_y = targets_array(samples)
    report = {
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "parameter_count": model.trainable_parameter_count(),
        "source_apparent_metrics": metrics(source_y, source_prediction["mean"]),
        "validation_metrics": history[best_epoch - 1]["validation"],
        "history": history,
        "model_config": asdict(model_config),
        "training_config": asdict(training_config),
        "optimizer": optimizer_manifest,
        "normalizer": normalizer.to_json(),
        "validation_split": (
            "group-held-out"
            if len(set(groups.tolist())) >= 5
            else "row-held-out-insufficient-source-groups"
        ),
        "validation_group_overlap": sorted(
            {
                sample.group_id for sample in train_samples
            }
            & {
                sample.group_id for sample in validation_samples
            }
        ),
    }
    return model, normalizer, report


@dataclass
class LatentSupportCalibrator:
    mean: np.ndarray
    scale: np.ndarray
    threshold: float

    @classmethod
    def fit(cls, latent: np.ndarray, quantile: float = 0.95) -> "LatentSupportCalibrator":
        latent = np.asarray(latent, dtype=float)
        mean = np.mean(latent, axis=0)
        scale = np.std(latent, axis=0)
        scale = np.where(scale > 1e-6, scale, 1.0)
        distance = np.sqrt(np.mean(((latent - mean) / scale) ** 2, axis=1))
        threshold = float(np.quantile(distance, quantile))
        return cls(mean=mean, scale=scale, threshold=max(threshold, 1e-6))

    def distance(self, latent: np.ndarray) -> np.ndarray:
        return np.sqrt(
            np.mean(((np.asarray(latent) - self.mean) / self.scale) ** 2, axis=1)
        )

    def ood_score(self, latent: np.ndarray) -> np.ndarray:
        return self.distance(latent) / self.threshold

    def support(self, latent: np.ndarray) -> np.ndarray:
        score = self.ood_score(latent)
        return np.exp(-0.5 * score**2).astype(np.float32)


def calibrate_support(
    model: CatalystTransferTransformer,
    source_samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    *,
    device: torch.device,
    batch_size: int = 64,
) -> LatentSupportCalibrator:
    latent = predict(
        model,
        source_samples,
        normalizer,
        device=device,
        batch_size=batch_size,
        return_latent=True,
    )["latent"]
    return LatentSupportCalibrator.fit(latent)


def recommend_candidates(
    model: CatalystTransferTransformer,
    candidates: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    support_calibrator: LatentSupportCalibrator,
    *,
    device: torch.device,
    objective: str,
    top_k: int = 10,
    uncertainty_weight: float = 0.5,
    max_ood_score: float = 1.0,
) -> list[dict[str, float | int | str | bool]]:
    """Risk-adjusted ranking inside a declared unlabeled candidate library."""

    if objective not in {"minimize", "maximize"}:
        raise ValueError("objective must be 'minimize' or 'maximize'")
    if top_k <= 0 or uncertainty_weight < 0 or max_ood_score <= 0:
        raise ValueError("recommendation controls must be positive")
    prediction = predict(
        model,
        candidates,
        normalizer,
        device=device,
        support_calibrator=support_calibrator,
        return_latent=True,
        unknown_program=True,
    )
    ood_score = support_calibrator.ood_score(prediction["latent"])
    if objective == "maximize":
        utility = prediction["mean"] - uncertainty_weight * prediction["std"]
    else:
        utility = -prediction["mean"] - uncertainty_weight * prediction["std"]
    eligible = ood_score <= max_ood_score
    order = np.lexsort(
        (
            np.asarray([sample.sample_id for sample in candidates]),
            -utility,
            ~eligible,
        )
    )
    recommendations = []
    for rank, index in enumerate(order[: min(top_k, len(order))], start=1):
        recommendations.append(
            {
                "rank": rank,
                "sample_id": candidates[int(index)].sample_id,
                "predicted_mean": float(prediction["mean"][index]),
                "predicted_std": float(prediction["std"][index]),
                "source_support": float(prediction["support"][index]),
                "ood_score": float(ood_score[index]),
                "eligible": bool(eligible[index]),
                "utility": float(utility[index]),
                "decision": "recommend" if eligible[index] else "abstain",
            }
        )
    return recommendations


def adapt_model(
    source_model: CatalystTransferTransformer,
    anchors: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    support_calibrator: LatentSupportCalibrator,
    config: TrainingConfig,
    *,
    device: torch.device,
) -> CatalystTransferTransformer:
    if len(anchors) < 2:
        raise ValueError("target adaptation requires at least two anchors")
    set_deterministic(config.seed + len(anchors) * 101)
    model = copy.deepcopy(source_model).to(device)
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.target_residual.parameters():
        parameter.requires_grad = True
    model.target_scale.requires_grad = True
    model.target_bias.requires_grad = True
    adapter_parameters = [
        *model.target_residual.parameters(),
        model.target_scale,
        model.target_bias,
    ]
    optimizer = torch.optim.AdamW(
        adapter_parameters,
        lr=config.adapter_learning_rate,
        weight_decay=config.adapter_weight_decay,
    )
    batch = _to_device(
        BatchCollator(normalizer, unknown_program=True)(anchors), device
    )
    model.eval()
    with torch.no_grad():
        latent, _ = model.encode(batch)
        external_support = torch.as_tensor(
            support_calibrator.support(latent.cpu().numpy()),
            dtype=latent.dtype,
            device=device,
        )
    best_state = {
        "residual": copy.deepcopy(model.target_residual.state_dict()),
        "scale": model.target_scale.detach().clone(),
        "bias": model.target_bias.detach().clone(),
    }
    best_loss = float("inf")
    stale = 0
    for _ in range(config.adapter_epochs):
        optimizer.zero_grad(set_to_none=True)
        output = model(
            batch,
            adaptation=True,
            external_source_support=external_support,
        )
        prediction = output["mean"]
        assert isinstance(prediction, Tensor)
        loss = F.smooth_l1_loss(prediction, batch["target"], beta=0.5)
        residual = output["residual"]
        assert isinstance(residual, Tensor)
        loss = (
            loss
            + 0.02 * residual.square().mean()
            + 0.08 * (model.target_scale - 1.0).square()
            + 0.005 * model.target_bias.square()
        )
        loss.backward()
        nn.utils.clip_grad_norm_(adapter_parameters, 1.0)
        optimizer.step()
        value = float(loss.detach())
        if value < best_loss - 1e-7:
            best_loss = value
            best_state = {
                "residual": copy.deepcopy(model.target_residual.state_dict()),
                "scale": model.target_scale.detach().clone(),
                "bias": model.target_bias.detach().clone(),
            }
            stale = 0
        else:
            stale += 1
        if stale >= 45:
            break
    model.target_residual.load_state_dict(best_state["residual"])
    model.target_scale.data.copy_(best_state["scale"])
    model.target_bias.data.copy_(best_state["bias"])
    return model


def _aligned_curve_matrix(
    samples: Sequence[CatalystSample],
    target_length: int | None = None,
) -> np.ndarray:
    lengths = [len(sample.curve_axis) for sample in samples]
    if not lengths or min(lengths) == 0:
        raise ValueError("baseline requires non-empty curves")
    if target_length is None:
        target_length = (
            lengths[0]
            if len(set(lengths)) == 1
            else int(np.median(lengths))
        )
    destination = np.linspace(0.0, 1.0, target_length)
    rows = []
    for sample in samples:
        primary = sample.curve_values[:, 0]
        if len(primary) == target_length:
            rows.append(primary)
        else:
            source = np.linspace(0.0, 1.0, len(primary))
            rows.append(np.interp(destination, source, primary))
    return np.stack(rows)


def target_only_knn(
    all_target_samples: Sequence[CatalystSample],
    anchor_indices: np.ndarray,
    test_indices: np.ndarray,
    neighbors: int = 3,
) -> np.ndarray:
    """Outcome-free target representation with only anchor outcomes."""

    matrix = _aligned_curve_matrix(all_target_samples)
    scaled = StandardScaler().fit_transform(matrix)
    max_components = min(len(all_target_samples) - 1, 20)
    embedding = PCA(n_components=max_components, random_state=0).fit_transform(scaled)
    anchor_x = embedding[anchor_indices]
    test_x = embedding[test_indices]
    distances = np.sqrt(
        np.maximum(
            0.0,
            np.sum((test_x[:, None, :] - anchor_x[None, :, :]) ** 2, axis=2),
        )
    )
    count = min(neighbors, len(anchor_indices))
    nearest = np.argpartition(distances, kth=count - 1, axis=1)[:, :count]
    nearest_distance = np.take_along_axis(distances, nearest, axis=1)
    weights = 1.0 / np.maximum(nearest_distance, 1e-8)
    anchor_y = targets_array(
        [all_target_samples[index] for index in anchor_indices]
    )
    return np.sum(weights * anchor_y[nearest], axis=1) / np.sum(weights, axis=1)


def fit_pls_baseline(
    source_samples: Sequence[CatalystSample], components: int = 8
) -> Pipeline:
    matrix = _aligned_curve_matrix(source_samples)
    target = targets_array(source_samples)
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pls", PLSRegression(n_components=components, scale=False, max_iter=2000)),
        ]
    )
    model.fit(matrix, target)
    return model


def predict_pls(model: Pipeline, samples: Sequence[CatalystSample]) -> np.ndarray:
    return np.asarray(
        model.predict(
            _aligned_curve_matrix(samples, target_length=int(model.n_features_in_))
        )
    ).reshape(-1)


def composition_matrix(samples: Sequence[CatalystSample]) -> np.ndarray:
    matrix = np.zeros((len(samples), 118), dtype=np.float32)
    for row, sample in enumerate(samples):
        matrix[row, sample.elements - 1] = sample.fractions
    return matrix


def composition_condition_matrix(
    samples: Sequence[CatalystSample],
) -> np.ndarray:
    composition = composition_matrix(samples)
    conditions = np.stack(
        [
            sample.condition_values * sample.condition_mask
            for sample in samples
        ]
    )
    condition_mask = np.stack([sample.condition_mask for sample in samples])
    return np.concatenate([composition, conditions, condition_mask], axis=1)


def fit_composition_baseline(
    source_samples: Sequence[CatalystSample], seed: int
) -> ExtraTreesRegressor:
    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=0.75,
        random_state=seed,
        n_jobs=1,
    )
    model.fit(
        composition_matrix(source_samples),
        targets_array(source_samples),
    )
    return model


def fit_composition_condition_baseline(
    source_samples: Sequence[CatalystSample], seed: int
) -> ExtraTreesRegressor:
    model = ExtraTreesRegressor(
        n_estimators=500,
        min_samples_leaf=2,
        max_features=0.75,
        random_state=seed,
        n_jobs=1,
    )
    model.fit(
        composition_condition_matrix(source_samples),
        targets_array(source_samples),
    )
    return model


def few_shot_experiment(
    source_model: CatalystTransferTransformer,
    source_samples: Sequence[CatalystSample],
    target_samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    training_config: TrainingConfig,
    *,
    anchors: int,
    draws: int,
    seed: int,
    device: torch.device,
) -> dict:
    if anchors >= len(target_samples):
        raise ValueError("anchor budget must leave held-out target samples")
    support_calibrator = calibrate_support(
        source_model,
        source_samples,
        normalizer,
        device=device,
        batch_size=training_config.batch_size,
    )
    rng = np.random.default_rng(seed)
    adapted_rows: list[dict[str, float]] = []
    bias_calibrated_rows: list[dict[str, float]] = []
    target_rows: list[dict[str, float]] = []
    zero_prediction = predict(
        source_model,
        target_samples,
        normalizer,
        device=device,
        support_calibrator=support_calibrator,
        unknown_program=True,
    )
    all_target = targets_array(target_samples)
    for draw in range(draws):
        anchor_indices = np.sort(
            rng.choice(len(target_samples), size=anchors, replace=False)
        )
        mask = np.ones(len(target_samples), dtype=bool)
        mask[anchor_indices] = False
        test_indices = np.flatnonzero(mask)
        adapter_config = TrainingConfig(
            **{
                **asdict(training_config),
                "seed": seed + draw * 17,
            }
        )
        adapted = adapt_model(
            source_model,
            [target_samples[index] for index in anchor_indices],
            normalizer,
            support_calibrator,
            adapter_config,
            device=device,
        )
        adapted_prediction = predict(
            adapted,
            [target_samples[index] for index in test_indices],
            normalizer,
            device=device,
            adaptation=True,
            support_calibrator=support_calibrator,
            unknown_program=True,
        )["mean"]
        target_prediction = target_only_knn(
            target_samples, anchor_indices, test_indices
        )
        # With five labels a single offset is the highest-capacity calibration
        # that is reliably identifiable.  It preserves the borrowed ordering
        # while correcting systematic inter-program voltage offsets.
        anchor_bias = float(
            np.mean(
                all_target[anchor_indices]
                - zero_prediction["mean"][anchor_indices]
            )
        )
        bias_prediction = zero_prediction["mean"][test_indices] + anchor_bias
        adapted_metric = metrics(all_target[test_indices], adapted_prediction)
        bias_metric = metrics(all_target[test_indices], bias_prediction)
        target_metric = metrics(all_target[test_indices], target_prediction)
        adapted_rows.append(adapted_metric)
        bias_calibrated_rows.append(bias_metric)
        target_rows.append(target_metric)
    def summarize(rows: list[dict[str, float]]) -> dict[str, dict[str, float | list[float]]]:
        return {
            key: {
                "median": float(np.median([row[key] for row in rows])),
                "ci90": [
                    float(np.quantile([row[key] for row in rows], 0.05)),
                    float(np.quantile([row[key] for row in rows], 0.95)),
                ],
            }
            for key in rows[0]
        }

    relative_rmse_gain = [
        (target["rmse"] - adapted["rmse"]) / target["rmse"]
        for adapted, target in zip(adapted_rows, target_rows, strict=True)
    ]
    spearman_gain = [
        adapted["spearman"] - target["spearman"]
        for adapted, target in zip(adapted_rows, target_rows, strict=True)
    ]
    bias_relative_rmse_gain = [
        (target["rmse"] - adapted["rmse"]) / target["rmse"]
        for adapted, target in zip(
            bias_calibrated_rows, target_rows, strict=True
        )
    ]
    bias_spearman_gain = [
        adapted["spearman"] - target["spearman"]
        for adapted, target in zip(
            bias_calibrated_rows, target_rows, strict=True
        )
    ]
    return {
        "anchors": anchors,
        "draws": draws,
        "zero_label": metrics(all_target, zero_prediction["mean"]),
        "zero_label_support": {
            "median": float(np.median(zero_prediction["support"])),
            "ood_fraction": float(
                np.mean(
                    support_calibrator.ood_score(
                        predict(
                            source_model,
                            target_samples,
                            normalizer,
                            device=device,
                            return_latent=True,
                            unknown_program=True,
                        )["latent"]
                    )
                    > 1.0
                )
            ),
        },
        "adapted": summarize(adapted_rows),
        "bias_calibrated_attention": summarize(bias_calibrated_rows),
        "target_only": summarize(target_rows),
        "gains": {
            "relative_rmse": {
                "median": float(np.median(relative_rmse_gain)),
                "ci90": [
                    float(np.quantile(relative_rmse_gain, 0.05)),
                    float(np.quantile(relative_rmse_gain, 0.95)),
                ],
            },
            "spearman": {
                "median": float(np.median(spearman_gain)),
                "ci90": [
                    float(np.quantile(spearman_gain, 0.05)),
                    float(np.quantile(spearman_gain, 0.95)),
                ],
            },
            "bias_calibrated_relative_rmse": {
                "median": float(np.median(bias_relative_rmse_gain)),
                "ci90": [
                    float(np.quantile(bias_relative_rmse_gain, 0.05)),
                    float(np.quantile(bias_relative_rmse_gain, 0.95)),
                ],
            },
            "bias_calibrated_spearman": {
                "median": float(np.median(bias_spearman_gain)),
                "ci90": [
                    float(np.quantile(bias_spearman_gain, 0.05)),
                    float(np.quantile(bias_spearman_gain, 0.95)),
                ],
            },
        },
        "draw_metrics": {
            "adapted": adapted_rows,
            "bias_calibrated_attention": bias_calibrated_rows,
            "target_only": target_rows,
        },
    }


def save_checkpoint(
    path: Path,
    model: CatalystTransferTransformer,
    normalizer: FeatureNormalizer,
    report: dict,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": model.state_dict(),
            "model_config": asdict(model.config),
            "normalizer": normalizer.to_json(),
            "report": report,
            "schema": schema_manifest(),
        },
        path,
    )


def load_checkpoint(
    path: Path,
    *,
    device: torch.device | None = None,
) -> tuple[CatalystTransferTransformer, FeatureNormalizer, dict]:
    device = device or torch.device("cpu")
    torch_version = re.match(r"^(\d+)\.(\d+)", torch.__version__)
    if torch_version is None or tuple(
        int(value) for value in torch_version.groups()
    ) < (2, 6):
        raise RuntimeError(
            "checkpoint loading requires PyTorch 2.6 or newer"
        )
    payload = torch.load(path, map_location=device, weights_only=True)
    if not isinstance(payload, dict):
        raise ValueError("checkpoint payload must be a dictionary")
    required = {"model_state", "model_config", "normalizer", "report", "schema"}
    missing = required - set(payload)
    if missing:
        raise ValueError(f"checkpoint is missing required fields: {sorted(missing)}")
    state = payload["model_state"]
    if not isinstance(state, dict) or any(
        not isinstance(key, str) or not isinstance(value, Tensor)
        for key, value in state.items()
    ):
        raise ValueError("checkpoint model_state must map names to tensors")
    if not isinstance(payload["model_config"], dict):
        raise ValueError("checkpoint model_config must be a dictionary")
    if not isinstance(payload["normalizer"], dict):
        raise ValueError("checkpoint normalizer must be a dictionary")
    if not isinstance(payload["report"], dict):
        raise ValueError("checkpoint report must be a dictionary")
    if payload["schema"] != schema_manifest():
        raise ValueError("checkpoint categorical schema does not match runtime schema")
    try:
        model_config = CatalystAttentionConfig(**payload["model_config"])
        normalizer = FeatureNormalizer.from_json(payload["normalizer"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"invalid checkpoint schema: {error}") from error
    model = CatalystTransferTransformer(model_config).to(device)
    if model_config.fusion_mode != "perceiver":
        # Advanced-v1 briefly serialized unused Perceiver parameters for every
        # fusion mode.  They never participated in cross-attention or mean-pool
        # predictions, so discard only this exact historical prefix while
        # retaining strict validation for every active model parameter.
        legacy_exact = {"fusion.perceiver_latents"}
        legacy_prefixes = (
            "fusion.perceiver_cross.",
            "fusion.perceiver_latent_norm.",
            "fusion.perceiver_memory_norm.",
            "fusion.perceiver_self.",
        )
        state = {
            key: value
            for key, value in state.items()
            if key not in legacy_exact
            and not key.startswith(legacy_prefixes)
        }
    model.load_state_dict(state)
    model.eval()
    return model, normalizer, payload["report"]


def write_json(path: Path, value: dict) -> None:
    atomic_write_text(
        path,
        json.dumps(value, indent=2, sort_keys=True) + "\n",
    )
