"""Optimizer construction for catalyst-attention experiments."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
from torch import nn

if TYPE_CHECKING:
    from .training import TrainingConfig


KL_SHAMPOO_IMPLEMENTATION = (
    "facebookresearch/optimizers@f18f735c972d304542af15e62b5acaa503169f2b"
)


def _matrix_parameter_groups(
    model: nn.Module,
) -> tuple[list[nn.Parameter], list[nn.Parameter]]:
    embedding_parameters = {
        id(parameter)
        for module in model.modules()
        if isinstance(module, nn.Embedding)
        for parameter in module.parameters(recurse=False)
    }
    terminal_prefixes = (
        "mean_head.",
        "log_variance_head.",
        "support_head.",
        "target_residual.",
    )
    matrix_parameters: list[nn.Parameter] = []
    fallback_parameters: list[nn.Parameter] = []
    for name, parameter in model.named_parameters():
        eligible = (
            parameter.requires_grad
            and parameter.ndim == 2
            and id(parameter) not in embedding_parameters
            and not name.startswith(terminal_prefixes)
        )
        (matrix_parameters if eligible else fallback_parameters).append(
            parameter
        )
    if not matrix_parameters or not fallback_parameters:
        raise ValueError(
            "KL-Shampoo requires both matrix and fallback parameter groups"
        )
    return matrix_parameters, fallback_parameters


def build_optimizer(
    model: nn.Module,
    config: "TrainingConfig",
) -> tuple[torch.optim.Optimizer, dict]:
    """Construct the selected optimizer and an auditable manifest."""
    if config.optimizer == "adamw":
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        return optimizer, {
            "name": "adamw",
            "implementation": "torch.optim.AdamW",
            "parameter_count": sum(
                parameter.numel()
                for parameter in model.parameters()
                if parameter.requires_grad
            ),
        }
    if config.optimizer not in {
        "kl_shampoo",
        "kl_shampoo_grafted",
    }:
        raise ValueError(f"unsupported optimizer: {config.optimizer}")
    try:
        from distributed_shampoo import (
            AdamPreconditionerConfig,
            DistributedShampoo,
            RootInvKLShampooPreconditionerConfig,
            WeightDecayType,
        )
    except ImportError as error:
        raise RuntimeError(
            "KL-Shampoo requires torch-shampoo from "
            f"{KL_SHAMPOO_IMPLEMENTATION}; install "
            "analysis/catalyst_attention/requirements-optimizers.txt"
        ) from error

    matrix_parameters, fallback_parameters = _matrix_parameter_groups(model)
    kl_config = RootInvKLShampooPreconditionerConfig(
        factor_matrix_dtype=torch.float64,
    )
    adam_config = AdamPreconditionerConfig(
        beta2=config.shampoo_beta2,
        epsilon=config.shampoo_grafting_epsilon,
    )
    optimizer = DistributedShampoo(
        [
            {
                "params": matrix_parameters,
                "preconditioner_config": kl_config,
                "max_preconditioner_dim": (
                    config.shampoo_max_preconditioner_dim
                ),
                "precondition_frequency": (
                    config.shampoo_precondition_frequency
                ),
                "start_preconditioning_step": (
                    config.shampoo_start_preconditioning_step
                ),
                "grafting_config": (
                    adam_config
                    if config.optimizer == "kl_shampoo_grafted"
                    else None
                ),
            },
            {
                "params": fallback_parameters,
                "preconditioner_config": kl_config,
                "start_preconditioning_step": math.inf,
                "grafting_config": adam_config,
            },
        ],
        lr=config.learning_rate,
        betas=(config.shampoo_beta1, config.shampoo_beta2),
        epsilon=config.shampoo_epsilon,
        weight_decay=config.weight_decay,
        weight_decay_type=WeightDecayType.DECOUPLED,
        max_preconditioner_dim=config.shampoo_max_preconditioner_dim,
        precondition_frequency=config.shampoo_precondition_frequency,
        start_preconditioning_step=(
            config.shampoo_start_preconditioning_step
        ),
        use_bias_correction=True,
        grafting_config=None,
        preconditioner_config=kl_config,
    )
    return optimizer, {
        "name": config.optimizer,
        "implementation": KL_SHAMPOO_IMPLEMENTATION,
        "matrix_parameter_count": sum(
            parameter.numel() for parameter in matrix_parameters
        ),
        "adamw_fallback_parameter_count": sum(
            parameter.numel() for parameter in fallback_parameters
        ),
        "matrix_tensor_count": len(matrix_parameters),
        "fallback_tensor_count": len(fallback_parameters),
        "beta1": config.shampoo_beta1,
        "beta2": config.shampoo_beta2,
        "epsilon": config.shampoo_epsilon,
        "grafting_epsilon": config.shampoo_grafting_epsilon,
        "max_preconditioner_dim": (
            config.shampoo_max_preconditioner_dim
        ),
        "precondition_frequency": (
            config.shampoo_precondition_frequency
        ),
        "start_preconditioning_step": (
            config.shampoo_start_preconditioning_step
        ),
        "factor_matrix_dtype": "float64",
        "weight_decay": config.weight_decay,
        "weight_decay_type": "decoupled",
        "matrix_adam_step_norm_grafting": (
            config.optimizer == "kl_shampoo_grafted"
        ),
    }
