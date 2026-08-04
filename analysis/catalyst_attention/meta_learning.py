"""First-order MAML (FOMAML) for catalyst few-shot knowledge transfer.

Treats each catalyst programme as a meta-learning task. Inner loop adapts
model parameters on a small support set; outer loop meta-updates parameters
so that future adaptation generalizes well. Uses first-order approximation
(no second derivatives) for speed while retaining most of MAML's benefits.

Reference: Finn et al., "Model-Agnostic Meta-Learning" (ICML 2017).
"""
from __future__ import annotations

import copy
from collections import defaultdict
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
    _to_device,
    adapt_model,
    calibrate_support,
    few_shot_experiment,
    metrics,
    predict,
    set_deterministic,
    targets_array,
    training_loss,
    train_source_model,
)


def _split_support_query(
    samples: Sequence[CatalystSample],
    support_size: int,
    seed: int,
) -> tuple[list[CatalystSample], list[CatalystSample]]:
    """Randomly split programme samples into support and query sets."""
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(samples))
    support_indices = indices[:support_size]
    query_indices = indices[support_size:]
    return (
        [samples[int(i)] for i in support_indices],
        [samples[int(i)] for i in query_indices],
    )


class FOMAMLWrapper:
    """First-order MAML for fast adaptation.

    Parameters
    ----------
    model:
        CatalystTransferTransformer (not yet trained).
    inner_lr:
        Learning rate for the inner loop (fast adaptation on support set).
    inner_steps:
        Number of gradient steps in the inner loop.
    first_order:
        If True, use first-order approximation (no second derivatives).
        Strongly recommended for speed.
    """

    def __init__(
        self,
        model: CatalystTransferTransformer,
        inner_lr: float = 0.01,
        inner_steps: int = 3,
        first_order: bool = True,
    ) -> None:
        self.model = model
        self.inner_lr = inner_lr
        self.inner_steps = inner_steps
        self.first_order = first_order

    def inner_loop(
        self,
        support_batch: dict[str, Tensor | list[str]],
        training_config: TrainingConfig,
    ) -> None:
        """Adapt model parameters on the support set (in-place)."""
        for _ in range(self.inner_steps):
            output = self.model(support_batch)
            loss, _ = training_loss(
                output, support_batch["target"], training_config
            )
            grads = torch.autograd.grad(
                loss,
                self.model.parameters(),
                create_graph=not self.first_order,
                allow_unused=True,
            )
            with torch.no_grad():
                for param, grad in zip(self.model.parameters(), grads):
                    if grad is not None:
                        param.sub_(self.inner_lr * grad)

    def meta_step(
        self,
        task_samples: list[list[CatalystSample]],
        normalizer: FeatureNormalizer,
        training_config: TrainingConfig,
        outer_optimizer: torch.optim.Optimizer,
        support_size: int = 5,
        seed: int = 0,
    ) -> dict[str, float]:
        """One meta-training step across multiple tasks.

        For each task: split into support/query, adapt on support,
        compute loss on query. Average query losses across tasks,
        backprop through the adaptation process (or use first-order
        approximation).

        Returns diagnostic metrics for monitoring.
        """
        self.model.train()
        outer_optimizer.zero_grad(set_to_none=True)

        meta_loss = torch.tensor(0.0, device=next(self.model.parameters()).device)
        task_count = 0
        task_losses: list[float] = []

        for task_idx, samples in enumerate(task_samples):
            if len(samples) < support_size + 2:
                continue  # Not enough samples for support + query.
            support, query = _split_support_query(
                samples, support_size, seed + task_idx
            )
            support_batch = _to_device(
                BatchCollator(normalizer)(support),
                next(self.model.parameters()).device,
            )
            query_batch = _to_device(
                BatchCollator(normalizer)(query),
                next(self.model.parameters()).device,
            )

            # Save original parameters.
            original_params = {
                name: param.clone()
                for name, param in self.model.named_parameters()
            }

            # Inner loop: adapt on support set.
            self.inner_loop(support_batch, training_config)

            # Compute query loss with adapted parameters.
            query_output = self.model(query_batch)
            task_loss, _ = training_loss(
                query_output, query_batch["target"], training_config
            )
            meta_loss = meta_loss + task_loss
            task_losses.append(float(task_loss.detach()))
            task_count += 1

            # Restore original parameters.
            with torch.no_grad():
                for name, param in self.model.named_parameters():
                    param.copy_(original_params[name])

        if task_count == 0:
            return {"meta_loss": 0.0, "n_tasks": 0}

        meta_loss = meta_loss / task_count
        meta_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(), training_config.gradient_clip
        )
        outer_optimizer.step()

        return {
            "meta_loss": float(meta_loss.detach()),
            "n_tasks": task_count,
            "mean_task_loss": float(np.mean(task_losses)) if task_losses else 0.0,
            "std_task_loss": float(np.std(task_losses)) if task_losses else 0.0,
        }


def meta_train(
    programme_samples: dict[str, list[CatalystSample]],
    model_config: CatalystAttentionConfig,
    training_config: TrainingConfig,
    *,
    device: torch.device,
    meta_epochs: int = 120,
    inner_lr: float = 0.01,
    inner_steps: int = 3,
    support_size: int = 5,
    first_order: bool = True,
    meta_validation_programme: str | None = None,
) -> tuple[CatalystTransferTransformer, FeatureNormalizer, dict]:
    """Meta-train a model across multiple catalyst programmes.

    Parameters
    ----------
    programme_samples:
        Dict mapping programme name → list of samples for that programme.
        Must have at least 3 programmes for meaningful meta-training.
    model_config:
        Catalyst model configuration.
    training_config:
        Base training configuration (learning_rate used for outer loop).
    device:
        Torch device.
    meta_epochs:
        Number of meta-training epochs.
    inner_lr:
        Learning rate for inner-loop adaptation.
    inner_steps:
        Number of gradient steps per inner loop.
    support_size:
        Number of support samples per task (matches evaluation protocol).
    first_order:
        Use first-order MAML approximation.
    meta_validation_programme:
        Programme held out for meta-validation. If provided, its samples
        are excluded from meta-training.

    Returns
    -------
    model:
        Meta-trained model (before any task-specific adaptation).
    normalizer:
        Feature normalizer fitted on all meta-training samples.
    report:
        Training history and diagnostics.
    """
    programme_names = sorted(programme_samples.keys())
    if len(programme_names) < 3:
        raise ValueError(
            "MAML requires at least 3 programmes for meta-training"
        )
    if meta_validation_programme is not None:
        train_programmes = [
            p for p in programme_names if p != meta_validation_programme
        ]
    else:
        train_programmes = programme_names

    # Fit normalizer on all meta-training samples.
    all_train = []
    for prog in train_programmes:
        all_train.extend(programme_samples[prog])
    normalizer = FeatureNormalizer.fit(all_train)

    set_deterministic(training_config.seed)
    model = CatalystTransferTransformer(model_config).to(device)
    maml = FOMAMLWrapper(
        model,
        inner_lr=inner_lr,
        inner_steps=inner_steps,
        first_order=first_order,
    )

    outer_optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        outer_optimizer,
        mode="min",
        factor=0.5,
        patience=max(5, meta_epochs // 12),
    )

    tasks = [programme_samples[p] for p in train_programmes]
    history: list[dict] = []
    best_loss = float("inf")
    best_state = copy.deepcopy(model.state_dict())
    best_epoch = 0
    stale = 0
    patience = max(10, meta_epochs // 6)

    for epoch in range(meta_epochs):
        diag = maml.meta_step(
            tasks,
            normalizer,
            training_config,
            outer_optimizer,
            support_size=support_size,
            seed=training_config.seed + epoch * 100,
        )
        scheduler.step(diag["meta_loss"])
        row = {
            "epoch": epoch + 1,
            **diag,
            "learning_rate": outer_optimizer.param_groups[0]["lr"],
        }
        history.append(row)

        if diag["meta_loss"] < best_loss - 1e-6:
            best_loss = diag["meta_loss"]
            best_epoch = epoch + 1
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1

        if stale >= patience:
            break

    model.load_state_dict(best_state)

    report = {
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "parameter_count": model.trainable_parameter_count(),
        "meta_train_programmes": train_programmes,
        "meta_validation_programme": meta_validation_programme,
        "maml_config": {
            "inner_lr": inner_lr,
            "inner_steps": inner_steps,
            "support_size": support_size,
            "first_order": first_order,
        },
        "history": history,
        "model_config": model_config.__dict__,
    }
    return model, normalizer, report
