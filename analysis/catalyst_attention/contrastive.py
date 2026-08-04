"""Contrastive representation learning for cross-domain catalyst transfer.

Organizes the latent space by chemistry rather than by programme identity.
Positive pairs are catalysts with similar composition from any source;
negative pairs are compositionally dissimilar catalysts. The contrastive
loss (NT-Xent) pulls similar compositions together and pushes dissimilar
ones apart, creating a representation where "same chemistry → similar
representation" regardless of which lab or programme produced the data.
"""
from __future__ import annotations

from typing import Sequence

import torch
from torch import Tensor, nn
from torch.nn import functional as F


def composition_to_vector(
    elements: Tensor, fractions: Tensor, n_elements: int = 118
) -> Tensor:
    """Project composition tuples into a fixed-width periodic-table vector.

    Parameters
    ----------
    elements:
        (batch, max_atoms) atomic numbers (1-indexed, 0 for padding).
    fractions:
        (batch, max_atoms) stoichiometric fractions.
    n_elements:
        Total periodic table width (default 118).

    Returns
    -------
    (batch, n_elements) tensor where column i holds the fraction of element i.
    """
    batch_size = len(elements)
    vector = torch.zeros(batch_size, n_elements, device=elements.device, dtype=fractions.dtype)
    mask = elements > 0
    vector.scatter_add_(1, (elements - 1).clamp_min(0), fractions * mask.float())
    return vector


def composition_cosine_similarity(
    vec_a: Tensor, vec_b: Tensor
) -> Tensor:
    """Pairwise cosine similarity between two batches of composition vectors.

    Parameters
    ----------
    vec_a:
        (batch_a, n_elements) composition vectors.
    vec_b:
        (batch_b, n_elements) composition vectors.

    Returns
    -------
    (batch_a, batch_b) similarity matrix in [0, 1].
    """
    norm_a = F.normalize(vec_a, p=2, dim=-1)
    norm_b = F.normalize(vec_b, p=2, dim=-1)
    return (norm_a @ norm_b.T).clamp(0.0, 1.0)


def build_contrastive_pairs(
    latent: Tensor,
    elements: Tensor,
    fractions: Tensor,
    *,
    similarity_threshold: float = 0.7,
    temperature: float = 0.1,
) -> tuple[Tensor, Tensor]:
    """Build positive and negative pairs within a batch using composition similarity.

    Parameters
    ----------
    latent:
        (batch, d_model) latent representations.
    elements:
        (batch, max_atoms) atomic numbers.
    fractions:
        (batch, max_atoms) stoichiometric fractions.
    similarity_threshold:
        Composition cosine similarity above which two samples are considered
        a positive pair.
    temperature:
        NT-Xent temperature (lower = sharper contrast).

    Returns
    -------
    loss:
        Scalar NT-Xent contrastive loss.
    n_positive_pairs:
        Number of positive pairs found (diagnostic).
    """
    batch_size = len(latent)
    if batch_size < 2:
        return latent.new_zeros(()), 0

    vec = composition_to_vector(elements, fractions)
    sim = composition_cosine_similarity(vec, vec)

    # Self-similarity and below-threshold pairs are excluded.
    positive_mask = sim >= similarity_threshold
    positive_mask.fill_diagonal_(False)

    n_positives = int(positive_mask.sum())
    if n_positives == 0:
        return latent.new_zeros(()), 0

    # Normalize latent vectors.
    z = F.normalize(latent, p=2, dim=-1)

    # NT-Xent: for each positive pair (i, j), compute
    #   -log(exp(sim(z_i, z_j)/τ) / Σ_k≠i exp(sim(z_i, z_k)/τ))
    logits = (z @ z.T) / temperature

    total_loss = latent.new_zeros(())
    count = 0
    for i in range(batch_size):
        pos_indices = positive_mask[i].nonzero(as_tuple=True)[0]
        if len(pos_indices) == 0:
            continue
        # Denominator: all samples except i.
        neg_mask = torch.ones(batch_size, dtype=torch.bool, device=latent.device)
        neg_mask[i] = False
        denom = torch.logsumexp(logits[i][neg_mask], dim=0)
        for j in pos_indices:
            total_loss = total_loss - logits[i, j] + denom
            count += 1

    if count == 0:
        return latent.new_zeros(()), 0

    return total_loss / count, count


class ContrastiveProjection(nn.Module):
    """Small projection head for contrastive learning (SimCLR pattern).

    Projects the d_model latent into a lower-dimensional space where the
    contrastive loss is computed. The projection head is discarded after
    training; only the encoder's latent space matters for transfer.
    """

    def __init__(
        self, d_model: int, projection_dim: int = 32, hidden_multiplier: int = 2
    ) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(d_model, d_model * hidden_multiplier),
            nn.BatchNorm1d(d_model * hidden_multiplier),
            nn.ReLU(),
            nn.Linear(d_model * hidden_multiplier, projection_dim),
        )

    def forward(self, latent: Tensor) -> Tensor:
        return F.normalize(self.projection(latent), p=2, dim=-1)


def contrastive_loss(
    latent: Tensor,
    elements: Tensor,
    fractions: Tensor,
    projection: ContrastiveProjection | None = None,
    *,
    similarity_threshold: float = 0.7,
    temperature: float = 0.1,
) -> tuple[Tensor, dict[str, float]]:
    """Full contrastive pipeline: project → normalize → NT-Xent.

    Parameters
    ----------
    latent:
        Raw latent representations from the fusion encoder.
    elements:
        Composition atomic numbers.
    fractions:
        Composition fractions.
    projection:
        Optional projection head. If None, contrastive loss is computed
        directly on the latent vectors.
    similarity_threshold:
        Composition similarity threshold for positive pairs.
    temperature:
        NT-Xent temperature.

    Returns
    -------
    loss:
        Scalar contrastive loss (0 if no positive pairs found).
    diagnostics:
        Dict with 'n_positive_pairs' and 'mean_similarity' for monitoring.
    """
    if projection is not None:
        latent = projection(latent)

    vec = composition_to_vector(elements, fractions)
    sim_matrix = composition_cosine_similarity(vec, vec)
    # Mean off-diagonal similarity for diagnostics.
    mask = ~torch.eye(len(vec), dtype=torch.bool, device=vec.device)
    mean_similarity = float(sim_matrix[mask].mean())

    batch_loss, n_pairs = build_contrastive_pairs(
        latent, elements, fractions,
        similarity_threshold=similarity_threshold,
        temperature=temperature,
    )

    return batch_loss, {
        "n_positive_pairs": n_pairs,
        "mean_composition_similarity": mean_similarity,
    }
