"""Latent diffusion model for catalyst knowledge transfer.

Trains a conditional DDPM on the frozen encoder's latent space, conditioned
on catalyst composition (118-dim periodic table vector). At transfer time,
generates synthetic latent vectors for target-domain compositions that are
under-represented in source data, bridging the domain gap.

The diffusion model is compact (~50K params for d_model=64) and trains
on extracted latents from a single forward pass over source data.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

from .data import CatalystSample
from .model import CatalystTransferTransformer
from .training import FeatureNormalizer, predict


# ---------------------------------------------------------------------------
# Time embedding (standard sinusoidal, as in DDPM / Vision Transformer)
# ---------------------------------------------------------------------------

class SinusoidalTimeEmbedding(nn.Module):
    """Sinusoidal time-step embedding, standard in diffusion models."""

    def __init__(self, dim: int, max_period: int = 10000) -> None:
        super().__init__()
        self.dim = dim
        self.max_period = max_period

    def forward(self, t: Tensor) -> Tensor:
        """t: (batch,) integer timesteps in [0, T-1]."""
        half = self.dim // 2
        freqs = torch.exp(
            -math.log(self.max_period)
            * torch.arange(half, dtype=torch.float32, device=t.device)
            / half
        )
        args = t.float().unsqueeze(-1) * freqs.unsqueeze(0)
        return torch.cat([torch.sin(args), torch.cos(args)], dim=-1)


# ---------------------------------------------------------------------------
# Composition-conditioned denoising network (lightweight MLP with skips)
# ---------------------------------------------------------------------------

class CompositionConditionedDenoiser(nn.Module):
    """Denoises latent vectors conditioned on composition and timestep.

    Architecture: conditioned MLP with residual skip connections.
    For d_model=64 this is ~50K parameters — training is fast.

    Parameters
    ----------
    d_model:
        Latent vector dimension (e.g. 64).
    d_condition:
        Composition vector dimension (118 for full periodic table).
    hidden:
        Hidden layer width.
    n_blocks:
        Number of residual blocks.
    """

    def __init__(
        self,
        d_model: int = 64,
        d_condition: int = 118,
        hidden: int = 256,
        n_blocks: int = 4,
    ) -> None:
        super().__init__()
        self.time_embed = SinusoidalTimeEmbedding(hidden)
        self.condition_proj = nn.Linear(d_condition, hidden)

        self.input_proj = nn.Sequential(
            nn.Linear(d_model + hidden + hidden, hidden),  # z_t + cond + time
            nn.SiLU(),
        )

        self.blocks = nn.ModuleList([
            _ResidualBlock(hidden) for _ in range(n_blocks)
        ])

        self.output_proj = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.SiLU(),
            nn.Linear(hidden, d_model),
        )

    def forward(
        self, z_t: Tensor, t: Tensor, composition: Tensor
    ) -> Tensor:
        """Predict noise given noisy latent, timestep, and composition.

        Parameters
        ----------
        z_t: (batch, d_model) noisy latent at timestep t.
        t: (batch,) integer timesteps.
        composition: (batch, d_condition) composition vector.

        Returns
        -------
        (batch, d_model) predicted noise.
        """
        t_emb = self.time_embed(t)
        c_emb = self.condition_proj(composition)
        h = self.input_proj(torch.cat([z_t, c_emb, t_emb], dim=-1))
        for block in self.blocks:
            h = block(h)
        return self.output_proj(h)


class _ResidualBlock(nn.Module):
    """MLP residual block with LayerNorm + SiLU."""

    def __init__(self, dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim * 2),
            nn.SiLU(),
            nn.Linear(dim * 2, dim),
        )

    def forward(self, x: Tensor) -> Tensor:
        return x + self.net(x)


# ---------------------------------------------------------------------------
# DDPM-style latent diffusion model
# ---------------------------------------------------------------------------

class LatentDiffusionModel(nn.Module):
    """DDPM on the encoder's latent space, conditioned on composition.

    Parameters
    ----------
    d_model:
        Latent vector dimension.
    d_condition:
        Composition vector dimension (118).
    n_timesteps:
        Number of diffusion steps (1000 default).
    beta_start, beta_end:
        Linear noise schedule endpoints.
    """

    def __init__(
        self,
        d_model: int = 64,
        d_condition: int = 118,
        n_timesteps: int = 1000,
        beta_start: float = 1e-4,
        beta_end: float = 0.02,
    ) -> None:
        super().__init__()
        self.d_model = d_model
        self.n_timesteps = n_timesteps

        # Linear noise schedule.
        betas = torch.linspace(beta_start, beta_end, n_timesteps)
        alphas = 1.0 - betas
        alpha_bars = torch.cumprod(alphas, dim=0)

        self.register_buffer("betas", betas)
        self.register_buffer("alphas", alphas)
        self.register_buffer("alpha_bars", alpha_bars)

        self.denoiser = CompositionConditionedDenoiser(
            d_model=d_model,
            d_condition=d_condition,
        )

    def forward_diffusion(self, z_0: Tensor, t: Tensor) -> tuple[Tensor, Tensor]:
        """Forward process: z_t = sqrt(ᾱ_t)·z_0 + sqrt(1-ᾱ_t)·ε.

        Returns (z_t, noise).
        """
        alpha_bar = self.alpha_bars[t].view(-1, 1)
        noise = torch.randn_like(z_0)
        z_t = torch.sqrt(alpha_bar) * z_0 + torch.sqrt(1.0 - alpha_bar) * noise
        return z_t, noise

    def training_step(
        self, z_0: Tensor, composition: Tensor
    ) -> Tensor:
        """Single diffusion training step: sample t, add noise, predict ε.

        Returns MSE loss.
        """
        batch = len(z_0)
        t = torch.randint(0, self.n_timesteps, (batch,), device=z_0.device)
        z_t, noise = self.forward_diffusion(z_0, t)
        pred = self.denoiser(z_t, t, composition)
        return F.mse_loss(pred, noise)

    @torch.no_grad()
    def sample(
        self,
        composition: Tensor,
        *,
        n_samples: int = 1,
        n_steps: int | None = None,
        return_trajectory: bool = False,
    ) -> Tensor:
        """DDPM reverse sampling: z_T → z_0, conditioned on composition.

        Uses the standard DDPM sampling formula (Algorithm 2, Ho et al. 2020):
          z_{t-1} = (1/√α_t)(z_t - (β_t/√(1-ᾱ_t))ε_θ(z_t,t,c)) + σ_t·ε

        Parameters
        ----------
        composition:
            (batch, d_condition) composition vectors.
        n_samples:
            Number of latent vectors per composition (broadcasts)
        n_steps:
            Denoising steps (default: full n_timesteps).
        """
        if composition.shape[0] == 1 and n_samples > 1:
            composition = composition.expand(n_samples, -1)
        batch_size = len(composition)
        device = composition.device

        z = torch.randn(batch_size, self.d_model, device=device)
        steps = n_steps or self.n_timesteps
        stride = self.n_timesteps // steps

        timesteps = list(range(0, self.n_timesteps, stride))
        if timesteps[-1] != self.n_timesteps - 1:
            timesteps.append(self.n_timesteps - 1)

        for i in reversed(timesteps):
            t = torch.full((batch_size,), i, device=device, dtype=torch.long)
            eps_pred = self.denoiser(z, t, composition)

            alpha_t = self.alphas[i]
            alpha_bar_t = self.alpha_bars[i]
            beta_t = self.betas[i]

            # Standard DDPM: predict x_0 then compute posterior mean.
            # More stable: compute mean directly.
            sqrt_alpha_t = torch.sqrt(alpha_t)
            sqrt_one_minus_alpha_bar = torch.sqrt(1.0 - alpha_bar_t)

            # Mean of p(z_{t-1} | z_t) with predicted noise.
            mean = (z - (beta_t / sqrt_one_minus_alpha_bar) * eps_pred) / sqrt_alpha_t

            if i > 0:
                # Standard DDPM: σ_t = √β_t
                sigma_t = torch.sqrt(beta_t)
                z = mean + sigma_t * torch.randn_like(z)
            else:
                z = mean

        return z

    def sample_ensemble(
        self,
        composition: Tensor,
        *,
        n_samples: int = 8,
        n_steps: int = 100,
    ) -> tuple[Tensor, Tensor]:
        """Generate multiple latents per composition, return mean and std.

        Returns
        -------
        mean: (batch, d_model) mean across n_samples.
        std: (batch, d_model) standard deviation across n_samples.
        """
        batch_size = len(composition)
        all_samples = []
        for _ in range(n_samples):
            z = self.sample(
                composition, n_samples=1, n_steps=n_steps,
            )  # (batch, d_model)
            all_samples.append(z)
        stacked = torch.stack(all_samples, dim=0)  # (n_samples, batch, d_model)
        return stacked.mean(dim=0), stacked.std(dim=0)


# ---------------------------------------------------------------------------
# Training and inference utilities
# ---------------------------------------------------------------------------

def _composition_to_vector(
    samples: Sequence[CatalystSample],
) -> np.ndarray:
    """Convert catalyst samples to fixed-width composition vectors."""
    matrix = np.zeros((len(samples), 118), dtype=np.float32)
    for i, s in enumerate(samples):
        if len(s.elements):
            matrix[i, s.elements - 1] = s.fractions
    return matrix


def extract_latents(
    model: CatalystTransferTransformer,
    samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    *,
    device: torch.device,
    batch_size: int = 64,
) -> np.ndarray:
    """Extract latent vectors from frozen encoder."""
    result = predict(
        model, samples, normalizer,
        device=device, batch_size=batch_size,
        return_latent=True, unknown_program=True,
    )
    return result["latent"]


def train_diffusion_model(
    model: CatalystTransferTransformer,
    source_samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    *,
    device: torch.device,
    diffusion_epochs: int = 200,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    n_timesteps: int = 1000,
) -> tuple[LatentDiffusionModel, dict]:
    """Train a latent diffusion model on a frozen encoder.

    Returns
    -------
    diffusion: Trained LatentDiffusionModel.
    report: Training diagnostics.
    """
    model.eval()
    d_model = model.config.d_model

    # Extract all source latents and compositions.
    latents = extract_latents(
        model, source_samples, normalizer, device=device,
    )
    compositions = _composition_to_vector(source_samples)

    latent_tensor = torch.from_numpy(latents).float()
    comp_tensor = torch.from_numpy(compositions).float()

    dataset = TensorDataset(latent_tensor, comp_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    diffusion = LatentDiffusionModel(
        d_model=d_model, n_timesteps=n_timesteps,
    ).to(device)

    optimizer = torch.optim.AdamW(
        diffusion.parameters(), lr=learning_rate, weight_decay=1e-5,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=diffusion_epochs,
    )

    history: list[dict] = []
    best_loss = float("inf")
    best_state = None
    best_epoch = 0
    patience = max(20, diffusion_epochs // 10)
    stale = 0

    for epoch in range(diffusion_epochs):
        diffusion.train()
        epoch_loss = 0.0
        n_batches = 0
        for z_batch, c_batch in loader:
            z_batch = z_batch.to(device)
            c_batch = c_batch.to(device)
            optimizer.zero_grad()
            loss = diffusion.training_step(z_batch, c_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.detach())
            n_batches += 1
        scheduler.step()

        avg_loss = epoch_loss / max(n_batches, 1)
        history.append({"epoch": epoch + 1, "loss": avg_loss})

        if avg_loss < best_loss - 1e-7:
            best_loss = avg_loss
            best_state = {
                k: v.clone() for k, v in diffusion.state_dict().items()
            }
            best_epoch = epoch + 1
            stale = 0
        else:
            stale += 1
        if stale >= patience:
            break

    if best_state is not None:
        diffusion.load_state_dict(best_state)

    report = {
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "final_loss": history[-1]["loss"] if history else float("inf"),
        "best_loss": best_loss,
        "d_model": d_model,
        "n_timesteps": n_timesteps,
        "parameter_count": sum(
            p.numel() for p in diffusion.parameters()
        ),
    }
    return diffusion, report


def augment_with_diffusion(
    diffusion: LatentDiffusionModel,
    target_samples: Sequence[CatalystSample],
    *,
    device: torch.device,
    n_augment_per_sample: int = 4,
    n_steps: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic latent vectors for target-domain compositions.

    Returns
    -------
    synthetic_latents: (n_target * n_augment, d_model)
    synthetic_compositions: (n_target * n_augment, 118)
    """
    compositions = _composition_to_vector(target_samples)
    comp_tensor = torch.from_numpy(compositions).float().to(device)

    diffusion.eval()
    all_latents = []
    all_comps = []
    with torch.no_grad():
        for i in range(len(comp_tensor)):
            c = comp_tensor[i:i+1]
            z = diffusion.sample(
                c, n_samples=n_augment_per_sample, n_steps=n_steps,
            )  # (n_augment, d_model)
            all_latents.append(z.cpu().numpy())
            all_comps.append(
                c.expand(n_augment_per_sample, -1).cpu().numpy()
            )

    return (
        np.concatenate(all_latents, axis=0).astype(np.float32),
        np.concatenate(all_comps, axis=0).astype(np.float32),
    )


def generate_target_predictions(
    diffusion: LatentDiffusionModel,
    model: CatalystTransferTransformer,
    target_samples: Sequence[CatalystSample],
    normalizer: FeatureNormalizer,
    *,
    device: torch.device,
    n_augment: int = 8,
    n_steps: int = 100,
    batch_size: int = 64,
) -> np.ndarray:
    """Generate predictions for target samples using diffusion-augmented latents.

    For each target sample:
    1. Generate n_augment synthetic latents conditioned on its composition
    2. Pass each through the prediction head → n_augment predictions
    3. Return the mean prediction (uncertainty from std across augmentations)

    Parameters
    ----------
    diffusion:
        Trained latent diffusion model.
    model:
        Frozen CatalystTransferTransformer (encoder + prediction head).
    target_samples:
        Target-domain catalyst samples.
    normalizer:
        Feature normalizer.

    Returns
    -------
    predictions: (n_target,) in original target scale.
    """
    compositions = _composition_to_vector(target_samples)
    comp_tensor = torch.from_numpy(compositions).float().to(device)
    d_model = model.config.d_model

    diffusion.eval()
    model.eval()

    all_means = []
    all_stds = []

    with torch.no_grad():
        for i in range(0, len(comp_tensor), batch_size):
            c_batch = comp_tensor[i:i+batch_size]
            # Generate synthetic latents.
            z_syn, z_std = diffusion.sample_ensemble(
                c_batch, n_samples=n_augment, n_steps=n_steps,
            )  # (batch, d_model), (batch, d_model)

            # Pass through prediction head (only the head, not full model).
            base = model.base_head(z_syn.to(device))
            # Use raw prediction head without adaptation logic.
            means = normalizer.inverse_target(
                base.squeeze(-1).cpu().numpy()
            )
            all_means.append(means)
            # Rough uncertainty: propagate std through head (first-order).
            # z_mean + z_std → perturbed prediction.
            z_pos = z_syn + z_std
            base_pos = model.base_head(z_pos.to(device))
            pred_pos = normalizer.inverse_target(
                base_pos.squeeze(-1).cpu().numpy()
            )
            all_stds.append(np.abs(pred_pos - means))

    return (
        np.concatenate(all_means),
        np.concatenate(all_stds),
    )
