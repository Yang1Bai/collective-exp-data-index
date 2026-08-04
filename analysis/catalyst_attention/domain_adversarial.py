"""Adversarial domain adaptation via gradient reversal on latent representations.

Forces the encoder to produce domain-invariant features by training a domain
classifier with reversed gradients. The encoder and domain classifier play a
minimax game: the classifier tries to identify which programme each sample
comes from, while the encoder tries to make all programmes look the same.
"""
from __future__ import annotations

import torch
from torch import Tensor, nn
from torch.nn import functional as F


class GradientReversalFunction(torch.autograd.Function):
    """Reverses gradient sign during backward pass.

    Forward:    y = x  (identity)
    Backward:   dL/dx = -λ · dL/dy  (negated and scaled)

    The scaling factor λ controls the strength of adversarial pressure.
    Typical schedule: λ starts near 0 and increases to 1 over training.
    """

    @staticmethod
    def forward(ctx: torch.autograd.function.FunctionCtx, x: Tensor, lambda_: float) -> Tensor:  # type: ignore[override]
        ctx.lambda_ = lambda_
        return x.clone()

    @staticmethod
    def backward(ctx: torch.autograd.function.FunctionCtx, grad_output: Tensor) -> tuple[Tensor, None]:  # type: ignore[override]
        return -ctx.lambda_ * grad_output, None


def gradient_reversal(x: Tensor, lambda_: float = 1.0) -> Tensor:
    """Apply gradient reversal with strength lambda_."""
    return GradientReversalFunction.apply(x, lambda_)


class DomainClassifier(nn.Module):
    """Two-layer MLP that predicts domain (programme) from latent vector.

    Parameters
    ----------
    d_model:
        Latent representation width.
    n_domains:
        Number of distinct domains to classify. For unsupervised DA
        between source and one target, use n_domains=2.
    hidden_multiplier:
        Hidden layer width relative to d_model.
    dropout:
        Dropout applied after the hidden layer.
    """

    def __init__(
        self,
        d_model: int,
        n_domains: int,
        hidden_multiplier: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        hidden = d_model * hidden_multiplier
        self.classifier = nn.Sequential(
            nn.Linear(d_model, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, n_domains),
        )

    def forward(self, latent: Tensor) -> Tensor:
        """Return unnormalized logits over domain classes.

        Parameters
        ----------
        latent:
            (batch_size, d_model) tensor of fused latent representations.
        """
        return self.classifier(latent)


def adversarial_domain_loss(
    latent: Tensor,
    domain_ids: Tensor,
    domain_classifier: DomainClassifier,
    grl_lambda: float = 1.0,
) -> tuple[Tensor, float]:
    """Compute domain classification loss with gradient reversal.

    Parameters
    ----------
    latent:
        (batch_size, d_model) latent representations. Gradient is reversed
        through this tensor before it reaches the encoder.
    domain_ids:
        (batch_size,) integer domain labels in [0, n_domains).
    domain_classifier:
        Trained domain classifier module.
    grl_lambda:
        Strength of gradient reversal. Higher values put more pressure on
        the encoder to hide domain information.

    Returns
    -------
    loss:
        Cross-entropy loss for the domain classifier.
    accuracy:
        Domain classification accuracy (0-1) for diagnostics. High accuracy
        means the classifier can still distinguish domains; low accuracy
        means the encoder is successfully hiding domain identity.
    """
    if latent.dim() != 2:
        raise ValueError("adversarial loss expects batched latent (N, d_model)")
    if domain_ids.dim() != 1 or len(domain_ids) != len(latent):
        raise ValueError("domain_ids must be a 1D tensor matching batch size")
    reversed_latent = gradient_reversal(latent, grl_lambda)
    logits = domain_classifier(reversed_latent)
    loss = F.cross_entropy(logits, domain_ids)
    with torch.no_grad():
        predictions = logits.argmax(dim=-1)
        accuracy = float((predictions == domain_ids).float().mean())
    return loss, accuracy


def grl_lambda_schedule(
    current_step: int,
    total_steps: int,
    max_lambda: float = 1.0,
) -> float:
    """Sigmoidal schedule for GRL λ: starts near 0, ramps to max_lambda.

    This prevents the domain classifier from dominating early training when
    the encoder hasn't yet learned useful features. The schedule follows
    Ganin et al. (2016): λ_p = 2/(1+exp(−10p)) − 1, scaled by max_lambda.
    """
    progress = current_step / max(total_steps, 1)
    return max_lambda * (2.0 / (1.0 + torch.exp(torch.tensor(-10.0 * progress)).item()) - 1.0)
