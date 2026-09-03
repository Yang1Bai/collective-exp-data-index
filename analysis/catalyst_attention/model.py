"""Hierarchical attention model for catalyst relation transfer."""
from __future__ import annotations

import math
from dataclasses import dataclass
import torch
from torch import Tensor, nn
from torch.nn import functional as F

from .schema import (
    CONDITION_NAMES,
    FUSION_BLOCK_NAMES,
    MEASUREMENT_MODALITY_NAMES,
    PROGRAM_NAMES,
    REACTION_NAMES,
    TARGET_NAMES,
)


@dataclass(frozen=True)
class CatalystAttentionConfig:
    d_model: int = 64
    n_heads: int = 4
    composition_layers: int = 2
    curve_layers: int = 3
    condition_layers: int = 1
    fusion_layers: int = 1
    fusion_queries: int = 4
    perceiver_latents: int = 12
    perceiver_layers: int = 2
    patch_size: int = 8
    feedforward_multiplier: int = 3
    dropout: float = 0.12
    modality_dropout: float = 0.0
    condition_count: int = len(CONDITION_NAMES)
    reaction_count: int = len(REACTION_NAMES)
    measurement_modality_count: int = len(MEASUREMENT_MODALITY_NAMES)
    fusion_block_count: int = len(FUSION_BLOCK_NAMES)
    target_count: int = len(TARGET_NAMES)
    program_count: int = len(PROGRAM_NAMES)
    use_composition: bool = True
    use_surface: bool = False
    use_curve: bool = True
    use_conditions: bool = True
    composition_mode: str = "set_query"
    fusion_mode: str = "cross_attention"
    depth_routing: str = "standard"
    depth_routing_heads: int = 4

    def validate(self) -> None:
        if (
            self.d_model <= 0
            or self.n_heads <= 0
            or self.d_model % self.n_heads
        ):
            raise ValueError("d_model must be positive and divisible by n_heads")
        layer_counts = (
            self.composition_layers,
            self.curve_layers,
            self.condition_layers,
            self.fusion_layers,
            self.feedforward_multiplier,
        )
        if any(value <= 0 for value in layer_counts):
            raise ValueError(
                "layer counts and feedforward multiplier must be positive"
            )
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if (
            self.patch_size <= 0
            or self.fusion_queries <= 0
            or self.perceiver_latents <= 0
            or self.perceiver_layers <= 0
        ):
            raise ValueError("patch, query, and Perceiver sizes must be positive")
        if self.composition_mode not in {"set_query", "crabnet", "pairwise"}:
            raise ValueError(
                f"unsupported composition mode: {self.composition_mode}"
            )
        if self.fusion_mode not in {
            "cross_attention",
            "mean_pool",
            "perceiver",
        }:
            raise ValueError(f"unsupported fusion mode: {self.fusion_mode}")
        if self.depth_routing not in {
            "standard",
            "delta_mhar",
            "delta_mhar_sublayer",
        }:
            raise ValueError(
                f"unsupported depth routing mode: {self.depth_routing}"
            )
        if (
            self.depth_routing_heads <= 0
            or self.d_model % self.depth_routing_heads
        ):
            raise ValueError(
                "d_model must be divisible by positive depth_routing_heads"
            )
        if not 0.0 <= self.modality_dropout < 1.0:
            raise ValueError("modality_dropout must be in [0, 1)")
        expected_counts = {
            "condition_count": len(CONDITION_NAMES),
            "reaction_count": len(REACTION_NAMES),
            "measurement_modality_count": len(MEASUREMENT_MODALITY_NAMES),
            "fusion_block_count": len(FUSION_BLOCK_NAMES),
            "target_count": len(TARGET_NAMES),
            "program_count": len(PROGRAM_NAMES),
        }
        for field, expected in expected_counts.items():
            if getattr(self, field) != expected:
                raise ValueError(
                    f"{field}={getattr(self, field)} does not match schema {expected}"
                )
        if not (
            self.use_composition
            or self.use_surface
            or self.use_curve
            or self.use_conditions
        ):
            raise ValueError("at least one modality must be enabled")


def _encoder_layer(config: CatalystAttentionConfig) -> nn.TransformerEncoderLayer:
    return nn.TransformerEncoderLayer(
        d_model=config.d_model,
        nhead=config.n_heads,
        dim_feedforward=config.d_model * config.feedforward_multiplier,
        dropout=config.dropout,
        activation="gelu",
        batch_first=True,
        norm_first=True,
    )


class DeltaMultiHeadRouter(nn.Module):
    """Additive multi-head routing over prior block deltas.

    Each feature subspace independently selects from the available depth
    deltas.  A zero-initialized gate makes the initial function exactly the
    ordinary residual stack while allowing the routing path to turn on during
    training.
    """

    def __init__(self, d_model: int, heads: int) -> None:
        super().__init__()
        if d_model <= 0 or heads <= 0 or d_model % heads:
            raise ValueError(
                "d_model must be positive and divisible by routing heads"
            )
        self.heads = heads
        self.head_dim = d_model // heads
        self.query = nn.Parameter(torch.zeros(heads, self.head_dim))
        self.gate = nn.Parameter(torch.zeros(heads))
        self.last_weights: Tensor | None = None

    def forward(self, residual: Tensor, deltas: list[Tensor]) -> Tensor:
        if not deltas:
            self.last_weights = None
            return residual
        sources = torch.stack(deltas, dim=0)
        normalized = F.rms_norm(sources, (sources.shape[-1],))
        source_heads = sources.unflatten(-1, (self.heads, self.head_dim))
        normalized_heads = normalized.unflatten(
            -1, (self.heads, self.head_dim)
        )
        logits = torch.einsum(
            "he,nbthe->nbth", self.query, normalized_heads
        )
        weights = torch.softmax(logits, dim=0)
        routed = torch.einsum(
            "nbth,nbthe->bthe", weights, source_heads
        )
        routed = routed * torch.tanh(self.gate).view(1, 1, self.heads, 1)
        self.last_weights = weights.detach()
        return residual + routed.flatten(-2)


class DeltaMHARTransformerEncoder(nn.Module):
    """Legacy v1 stack with block-delta routing at layer inputs."""

    def __init__(
        self,
        config: CatalystAttentionConfig,
        *,
        num_layers: int,
    ) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            [_encoder_layer(config) for _ in range(num_layers)]
        )
        self.routers = nn.ModuleList(
            [
                DeltaMultiHeadRouter(
                    config.d_model, config.depth_routing_heads
                )
                for _ in range(max(num_layers - 1, 0))
            ]
        )
        self.norm = nn.LayerNorm(config.d_model)

    def forward(
        self,
        src: Tensor,
        mask: Tensor | None = None,
        src_key_padding_mask: Tensor | None = None,
        is_causal: bool | None = None,
    ) -> Tensor:
        hidden = src
        deltas: list[Tensor] = []
        for index, layer in enumerate(self.layers):
            if index:
                hidden = self.routers[index - 1](hidden, deltas)
            layer_input = hidden
            hidden = layer(
                hidden,
                src_mask=mask,
                src_key_padding_mask=src_key_padding_mask,
                is_causal=False if is_causal is None else is_causal,
            )
            deltas.append(hidden - layer_input)
        return self.norm(hidden)


class DeltaMHARSublayerTransformerEncoder(nn.Module):
    """Additive Delta-MHAR over individual attention and FFN outputs.

    The routed state is used only as the sublayer input.  The ordinary residual
    stream receives the raw sublayer delta, matching the additive Delta
    Attention Residual formulation.
    """

    def __init__(
        self,
        config: CatalystAttentionConfig,
        *,
        num_layers: int,
    ) -> None:
        super().__init__()
        self.layers = nn.ModuleList(
            [_encoder_layer(config) for _ in range(num_layers)]
        )
        self.routers = nn.ModuleList(
            [
                DeltaMultiHeadRouter(
                    config.d_model, config.depth_routing_heads
                )
                for _ in range(2 * num_layers)
            ]
        )
        for router in self.routers:
            nn.init.normal_(router.query, std=0.02)
        self.norm = nn.LayerNorm(config.d_model)

    @staticmethod
    def _attention_delta(
        layer: nn.TransformerEncoderLayer,
        hidden: Tensor,
        mask: Tensor | None,
        padding_mask: Tensor | None,
        is_causal: bool,
    ) -> Tensor:
        update = layer.self_attn(
            hidden,
            hidden,
            hidden,
            attn_mask=mask,
            key_padding_mask=padding_mask,
            need_weights=False,
            is_causal=is_causal,
        )[0]
        return layer.dropout1(update)

    @staticmethod
    def _feedforward_delta(
        layer: nn.TransformerEncoderLayer,
        hidden: Tensor,
    ) -> Tensor:
        update = layer.linear2(
            layer.dropout(layer.activation(layer.linear1(hidden)))
        )
        return layer.dropout2(update)

    def forward(
        self,
        src: Tensor,
        mask: Tensor | None = None,
        src_key_padding_mask: Tensor | None = None,
        is_causal: bool | None = None,
    ) -> Tensor:
        hidden = src
        deltas: list[Tensor] = []
        causal = False if is_causal is None else is_causal
        route_index = 0
        for layer in self.layers:
            attention_input = self.routers[route_index](hidden, deltas)
            route_index += 1
            attention_delta = self._attention_delta(
                layer,
                layer.norm1(attention_input),
                mask,
                src_key_padding_mask,
                causal,
            )
            hidden = hidden + attention_delta
            deltas.append(attention_delta)

            feedforward_input = self.routers[route_index](hidden, deltas)
            route_index += 1
            feedforward_delta = self._feedforward_delta(
                layer, layer.norm2(feedforward_input)
            )
            hidden = hidden + feedforward_delta
            deltas.append(feedforward_delta)
        return self.norm(hidden)


def _encoder(
    config: CatalystAttentionConfig,
    *,
    num_layers: int,
) -> nn.Module:
    if config.depth_routing == "delta_mhar" and num_layers > 1:
        return DeltaMHARTransformerEncoder(config, num_layers=num_layers)
    if (
        config.depth_routing == "delta_mhar_sublayer"
        and num_layers > 1
    ):
        return DeltaMHARSublayerTransformerEncoder(
            config, num_layers=num_layers
        )
    return nn.TransformerEncoder(
        _encoder_layer(config),
        num_layers=num_layers,
        norm=nn.LayerNorm(config.d_model),
        enable_nested_tensor=False,
    )


class FourierAxisEncoding(nn.Module):
    """Continuous coordinate encoding that works across spectral/voltage axes."""

    def __init__(self, d_model: int, frequencies: int = 8) -> None:
        super().__init__()
        self.frequencies = frequencies
        self.projection = nn.Sequential(
            nn.Linear(2 * frequencies + 1, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )

    def forward(self, axis: Tensor) -> Tensor:
        scales = 2.0 ** torch.arange(
            self.frequencies, dtype=axis.dtype, device=axis.device
        )
        angles = math.pi * axis.unsqueeze(-1) * scales
        features = torch.cat(
            [axis.unsqueeze(-1), torch.sin(angles), torch.cos(angles)], dim=-1
        )
        return self.projection(features)


class CompositionSetEncoder(nn.Module):
    """Permutation-equivariant element attention plus invariant query pooling."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.element_embedding = nn.Embedding(119, config.d_model, padding_idx=0)
        self.fraction_embedding = nn.Sequential(
            nn.Linear(3, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.encoder = _encoder(
            config,
            num_layers=config.composition_layers,
        )
        self.pool_query = nn.Parameter(torch.empty(1, 1, config.d_model))
        self.missing_token = nn.Parameter(torch.empty(1, 1, config.d_model))
        nn.init.normal_(self.pool_query, std=0.02)
        nn.init.normal_(self.missing_token, std=0.02)
        self.pool_attention = nn.MultiheadAttention(
            config.d_model,
            config.n_heads,
            dropout=config.dropout,
            batch_first=True,
        )
        self.pool_norm = nn.LayerNorm(config.d_model)

    def forward(
        self,
        elements: Tensor,
        fractions: Tensor,
        padding_mask: Tensor,
        return_attention: bool,
        present: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor | None]:
        fraction_features = torch.stack(
            [fractions, torch.sqrt(fractions.clamp_min(0.0)), torch.log1p(fractions)],
            dim=-1,
        )
        tokens = self.element_embedding(elements) + self.fraction_embedding(
            fraction_features
        )
        if present is not None:
            missing = ~present.bool()
            if missing.any():
                tokens = tokens.clone()
                padding_mask = padding_mask.clone()
                tokens[missing, 0:1] = self.missing_token
                padding_mask[missing, 0] = False
        tokens = self.encoder(tokens, src_key_padding_mask=padding_mask)
        query = self.pool_query.expand(len(tokens), -1, -1)
        pooled, weights = self.pool_attention(
            query,
            tokens,
            tokens,
            key_padding_mask=padding_mask,
            need_weights=return_attention,
            average_attn_weights=False,
        )
        pooled = self.pool_norm(pooled)
        memory = torch.cat([pooled, tokens], dim=1)
        memory_mask = torch.cat(
            [
                torch.zeros((len(tokens), 1), dtype=torch.bool, device=tokens.device),
                padding_mask,
            ],
            dim=1,
        )
        return memory, memory_mask, weights if return_attention else None


class PairwiseElementEncoder(nn.Module):
    """Pairwise element interaction encoder for composition.

    Creates embeddings for all element pairs (i, j) in the composition,
    capturing explicit bimetallic/trimetallic interaction patterns that
    may be domain-invariant. Uses a lightweight MLP on concatenated
    element embeddings and fraction products, then pools into a fixed-size
    representation. Designed to replace or augment CompositionSetEncoder.
    """

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.element_embedding = nn.Embedding(119, config.d_model, padding_idx=0)
        self.fraction_embedding = nn.Sequential(
            nn.Linear(3, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        # Pair interaction MLP: 2*d_model (two elements) + 1 (fraction product).
        self.pair_mlp = nn.Sequential(
            nn.Linear(2 * config.d_model + 1, config.d_model * 2),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.encoder = _encoder(
            config,
            num_layers=config.composition_layers,
        )
        self.pool_query = nn.Parameter(torch.empty(1, 1, config.d_model))
        self.missing_token = nn.Parameter(torch.empty(1, 1, config.d_model))
        nn.init.normal_(self.pool_query, std=0.02)
        nn.init.normal_(self.missing_token, std=0.02)
        self.pool_attention = nn.MultiheadAttention(
            config.d_model,
            config.n_heads,
            dropout=config.dropout,
            batch_first=True,
        )
        self.pool_norm = nn.LayerNorm(config.d_model)

    def _build_pairs(
        self,
        elements: Tensor,
        fractions: Tensor,
        padding_mask: Tensor,
    ) -> tuple[Tensor, Tensor]:
        """Build pairwise element interaction tokens.

        For each sample with k real elements, creates k*(k-1)/2 pair tokens.
        Each pair token combines the embeddings of both elements and their
        fraction product, passed through a small MLP.
        """
        batch_size, max_elem = elements.shape
        element_emb = self.element_embedding(elements)  # (B, N, d)
        fraction_emb = self.fraction_embedding(
            torch.stack(
                [
                    fractions,
                    torch.sqrt(fractions.clamp_min(0.0)),
                    torch.log1p(fractions),
                ],
                dim=-1,
            )
        )  # (B, N, d)

        # Build all upper-triangular pairs for each sample.
        all_pairs: list[Tensor] = []
        pair_masks: list[Tensor] = []
        for b in range(batch_size):
            # Get valid elements for this sample.
            valid = ~padding_mask[b]
            n_valid = int(valid.sum())
            if n_valid < 2:
                # Single-element sample: use element embedding as fallback.
                all_pairs.append(
                    fraction_emb[b, 0:1]
                    + element_emb[b, 0:1]
                )
                pair_masks.append(
                    torch.zeros(1, dtype=torch.bool, device=elements.device)
                )
                continue

            idx = valid.nonzero(as_tuple=True)[0]
            pairs: list[Tensor] = []
            for i_idx in range(n_valid):
                for j_idx in range(i_idx + 1, n_valid):
                    i_val = int(idx[i_idx])
                    j_val = int(idx[j_idx])
                    # Concatenate: element_i_emb + element_j_emb + f_i*f_j.
                    pair_feat = torch.cat(
                        [
                            element_emb[b, i_val],
                            element_emb[b, j_val],
                            (fractions[b, i_val] * fractions[b, j_val])
                            .unsqueeze(-1),
                        ],
                        dim=-1,
                    )
                    pairs.append(pair_feat)

            if not pairs:
                all_pairs.append(
                    fraction_emb[b, 0:1] + element_emb[b, 0:1]
                )
                pair_masks.append(
                    torch.zeros(1, dtype=torch.bool, device=elements.device)
                )
            else:
                pair_tensor = torch.stack(pairs)  # (n_pairs, 2*d_model+1)
                pair_tokens = self.pair_mlp(pair_tensor)  # (n_pairs, d_model)
                all_pairs.append(pair_tokens)
                pair_masks.append(
                    torch.zeros(
                        len(pair_tokens), dtype=torch.bool,
                        device=elements.device,
                    )
                )

        # Pad to same length.
        max_pairs = max(p.shape[0] for p in all_pairs)
        padded = torch.zeros(
            batch_size, max_pairs, self.element_embedding.embedding_dim,
            device=elements.device,
        )
        mask = torch.ones(batch_size, max_pairs, dtype=torch.bool, device=elements.device)
        for b, (p, m) in enumerate(zip(all_pairs, pair_masks)):
            padded[b, : len(p)] = p
            mask[b, : len(m)] = m
        return padded, mask

    def forward(
        self,
        elements: Tensor,
        fractions: Tensor,
        padding_mask: Tensor,
        return_attention: bool,
        present: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor | None]:
        pair_tokens, pair_mask = self._build_pairs(
            elements, fractions, padding_mask
        )
        tokens = self.encoder(pair_tokens, src_key_padding_mask=pair_mask)
        query = self.pool_query.expand(len(tokens), -1, -1)
        pooled, weights = self.pool_attention(
            query,
            tokens,
            tokens,
            key_padding_mask=pair_mask,
            need_weights=return_attention,
            average_attn_weights=False,
        )
        pooled = self.pool_norm(pooled)
        memory = torch.cat([pooled, tokens], dim=1)
        memory_mask = torch.cat(
            [
                torch.zeros(
                    (len(tokens), 1), dtype=torch.bool, device=tokens.device
                ),
                pair_mask,
            ],
            dim=1,
        )
        return memory, memory_mask, weights if return_attention else None


class FractionalFourierEncoding(nn.Module):
    """CrabNet-style linear and logarithmic stoichiometric encoding."""

    def __init__(self, d_model: int, frequencies: int = 8) -> None:
        super().__init__()
        self.frequencies = frequencies
        self.projection = nn.Sequential(
            nn.Linear(frequencies * 4, d_model),
            nn.GELU(),
            nn.LayerNorm(d_model),
        )

    def forward(self, fractions: Tensor) -> Tensor:
        fractions = fractions.clamp(0.0, 1.0)
        log_fraction = (
            torch.log10(fractions.clamp_min(1e-8)) / 8.0 + 1.0
        ).clamp(0.0, 1.0)
        scales = 2.0 ** torch.arange(
            self.frequencies,
            dtype=fractions.dtype,
            device=fractions.device,
        )
        linear_angle = math.pi * fractions.unsqueeze(-1) * scales
        log_angle = math.pi * log_fraction.unsqueeze(-1) * scales
        features = torch.cat(
            [
                torch.sin(linear_angle),
                torch.cos(linear_angle),
                torch.sin(log_angle),
                torch.cos(log_angle),
            ],
            dim=-1,
        )
        return self.projection(features)


class CrabNetCompositionEncoder(nn.Module):
    """Composition attention with explicit fractional Fourier embeddings."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.element_embedding = nn.Embedding(
            119, config.d_model, padding_idx=0
        )
        self.fraction_encoding = FractionalFourierEncoding(config.d_model)
        self.encoder = _encoder(
            config,
            num_layers=config.composition_layers,
        )
        self.pool_score = nn.Linear(config.d_model, 1)
        self.pool_norm = nn.LayerNorm(config.d_model)
        self.missing_token = nn.Parameter(
            torch.empty(1, 1, config.d_model)
        )
        nn.init.normal_(self.missing_token, std=0.02)

    def forward(
        self,
        elements: Tensor,
        fractions: Tensor,
        padding_mask: Tensor,
        return_attention: bool,
        present: Tensor | None = None,
    ) -> tuple[Tensor, Tensor, Tensor | None]:
        tokens = self.element_embedding(elements) + self.fraction_encoding(
            fractions
        )
        if present is not None:
            missing = ~present.bool()
            if missing.any():
                tokens = tokens.clone()
                padding_mask = padding_mask.clone()
                tokens[missing, 0:1] = self.missing_token
                padding_mask[missing, 0] = False
        tokens = self.encoder(tokens, src_key_padding_mask=padding_mask)
        scores = self.pool_score(tokens).squeeze(-1)
        scores = scores.masked_fill(padding_mask, torch.finfo(scores.dtype).min)
        weights = torch.softmax(scores, dim=-1)
        pooled = self.pool_norm(
            torch.sum(tokens * weights.unsqueeze(-1), dim=1, keepdim=True)
        )
        memory = torch.cat([pooled, tokens], dim=1)
        memory_mask = torch.cat(
            [
                torch.zeros(
                    (len(tokens), 1),
                    dtype=torch.bool,
                    device=tokens.device,
                ),
                padding_mask,
            ],
            dim=1,
        )
        attention = None
        if return_attention:
            attention = weights[:, None, None, :].expand(
                -1, self.n_heads, -1, -1
            )
        return memory, memory_mask, attention


class CurveTransformer(nn.Module):
    """Patch-level attention over measurement curves, not a one-token ViT."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.patch_size = config.patch_size
        self.patch_projection = nn.Sequential(
            nn.Linear(config.patch_size * 3, config.d_model),
            nn.GELU(),
            nn.LayerNorm(config.d_model),
        )
        self.axis_encoding = FourierAxisEncoding(config.d_model)
        self.channel_mask_projection = nn.Linear(2, config.d_model, bias=False)
        self.missing_curve = nn.Parameter(torch.empty(1, 1, config.d_model))
        nn.init.normal_(self.missing_curve, std=0.02)
        self.encoder = _encoder(
            config,
            num_layers=config.curve_layers,
        )

    def forward(
        self,
        axis: Tensor,
        values: Tensor,
        padding_mask: Tensor,
        channel_mask: Tensor,
        curve_present: Tensor,
    ) -> tuple[Tensor, Tensor]:
        batch, length = axis.shape
        pad = (-length) % self.patch_size
        if pad:
            axis = F.pad(axis, (0, pad))
            values = F.pad(values, (0, 0, 0, pad))
            padding_mask = F.pad(padding_mask, (0, pad), value=True)
        patch_count = axis.shape[1] // self.patch_size
        patch_axis = axis.reshape(batch, patch_count, self.patch_size)
        patch_values = values.reshape(batch, patch_count, self.patch_size, 2)
        patch_padding = padding_mask.reshape(batch, patch_count, self.patch_size)
        valid = (~patch_padding).to(axis.dtype)
        denominator = valid.sum(dim=-1).clamp_min(1.0)
        mean_axis = (patch_axis * valid).sum(dim=-1) / denominator
        inputs = torch.cat([patch_axis.unsqueeze(-1), patch_values], dim=-1)
        inputs = inputs.masked_fill(patch_padding.unsqueeze(-1), 0.0)
        tokens = self.patch_projection(inputs.reshape(batch, patch_count, -1))
        tokens = (
            tokens
            + self.axis_encoding(mean_axis)
            + self.channel_mask_projection(channel_mask).unsqueeze(1)
        )
        patch_mask = patch_padding.all(dim=-1)
        missing = ~curve_present.bool()
        if missing.any():
            tokens = tokens.clone()
            patch_mask = patch_mask.clone()
            tokens[missing, 0:1] = self.missing_curve
            patch_mask[missing, 0] = False
        tokens = self.encoder(tokens, src_key_padding_mask=patch_mask)
        return tokens, patch_mask


class ConditionTokenEncoder(nn.Module):
    """Typed numeric and categorical experimental-condition tokens."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.condition_types = nn.Embedding(config.condition_count, config.d_model)
        self.numeric = nn.Sequential(
            nn.Linear(2, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.missing = nn.Embedding(2, config.d_model)
        self.modality = nn.Embedding(
            config.measurement_modality_count, config.d_model
        )
        self.program = nn.Embedding(config.program_count, config.d_model)
        self.category_types = nn.Parameter(torch.empty(1, 2, config.d_model))
        nn.init.normal_(self.category_types, std=0.02)
        self.encoder = _encoder(
            config,
            num_layers=config.condition_layers,
        )

    def forward(
        self,
        values: Tensor,
        mask: Tensor,
        modality_id: Tensor,
        program_id: Tensor,
    ) -> tuple[Tensor, Tensor]:
        batch, count = values.shape
        types = self.condition_types(
            torch.arange(count, device=values.device)
        ).unsqueeze(0)
        numeric_input = torch.stack([values, mask], dim=-1)
        numeric = (
            self.numeric(numeric_input)
            + types
            + self.missing(mask.long().clamp(0, 1))
        )
        categories = torch.stack(
            [
                self.modality(modality_id),
                self.program(program_id),
            ],
            dim=1,
        )
        tokens = torch.cat(
            [numeric, categories + self.category_types.expand(batch, -1, -1)],
            dim=1,
        )
        tokens = self.encoder(tokens)
        return tokens, torch.zeros(
            tokens.shape[:2], dtype=torch.bool, device=tokens.device
        )


class TaskTokenEncoder(nn.Module):
    """Always-on reaction and property identity, independent of conditions."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.reaction = nn.Embedding(config.reaction_count, config.d_model)
        self.target = nn.Embedding(config.target_count, config.d_model)
        self.types = nn.Parameter(torch.empty(1, 2, config.d_model))
        nn.init.normal_(self.types, std=0.02)
        self.norm = nn.LayerNorm(config.d_model)

    def forward(
        self, reaction_id: Tensor, target_id: Tensor
    ) -> tuple[Tensor, Tensor]:
        batch = len(reaction_id)
        tokens = torch.stack(
            [self.reaction(reaction_id), self.target(target_id)], dim=1
        )
        tokens = self.norm(tokens + self.types.expand(batch, -1, -1))
        return tokens, torch.zeros(
            tokens.shape[:2], dtype=torch.bool, device=tokens.device
        )


class CrossModalFusion(nn.Module):
    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        self.mode = config.fusion_mode
        self.queries = nn.Parameter(
            torch.empty(1, config.fusion_queries, config.d_model)
        )
        nn.init.normal_(self.queries, std=0.02)
        self.cross_attention = nn.MultiheadAttention(
            config.d_model,
            config.n_heads,
            dropout=config.dropout,
            batch_first=True,
        )
        self.self_encoder = _encoder(
            config,
            num_layers=config.fusion_layers,
        )
        self.mean_pool_projection = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.GELU(),
            nn.LayerNorm(config.d_model),
        )
        self.output_norm = nn.LayerNorm(config.d_model)
        if config.fusion_mode == "perceiver":
            self.perceiver_latents = nn.Parameter(
                torch.empty(
                    1, config.perceiver_latents, config.d_model
                )
            )
            nn.init.normal_(self.perceiver_latents, std=0.02)
            self.perceiver_cross = nn.ModuleList(
                [
                    nn.MultiheadAttention(
                        config.d_model,
                        config.n_heads,
                        dropout=config.dropout,
                        batch_first=True,
                    )
                    for _ in range(config.perceiver_layers)
                ]
            )
            self.perceiver_latent_norm = nn.ModuleList(
                [
                    nn.LayerNorm(config.d_model)
                    for _ in range(config.perceiver_layers)
                ]
            )
            self.perceiver_memory_norm = nn.ModuleList(
                [
                    nn.LayerNorm(config.d_model)
                    for _ in range(config.perceiver_layers)
                ]
            )
            self.perceiver_self = nn.ModuleList(
                [
                    _encoder(config, num_layers=1)
                    for _ in range(config.perceiver_layers)
                ]
            )
        else:
            self.register_parameter("perceiver_latents", None)
            self.perceiver_cross = nn.ModuleList()
            self.perceiver_latent_norm = nn.ModuleList()
            self.perceiver_memory_norm = nn.ModuleList()
            self.perceiver_self = nn.ModuleList()
        self.perceiver_dropout = nn.Dropout(config.dropout)

    def forward(
        self,
        memory: Tensor,
        memory_mask: Tensor,
        return_attention: bool,
    ) -> tuple[Tensor, Tensor | None]:
        if self.mode == "mean_pool":
            weights = (~memory_mask).to(memory.dtype)
            pooled = (memory * weights.unsqueeze(-1)).sum(dim=1)
            pooled /= weights.sum(dim=1, keepdim=True).clamp_min(1.0)
            return self.mean_pool_projection(pooled), None
        if self.mode == "perceiver":
            assert self.perceiver_latents is not None
            latent = self.perceiver_latents.expand(len(memory), -1, -1)
            attention = None
            for cross, latent_norm, memory_norm, self_encoder in zip(
                self.perceiver_cross,
                self.perceiver_latent_norm,
                self.perceiver_memory_norm,
                self.perceiver_self,
                strict=True,
            ):
                update, layer_attention = cross(
                    latent_norm(latent),
                    memory_norm(memory),
                    memory_norm(memory),
                    key_padding_mask=memory_mask,
                    need_weights=return_attention,
                    average_attn_weights=False,
                )
                latent = latent + self.perceiver_dropout(update)
                latent = self_encoder(latent)
                if layer_attention is not None:
                    attention = layer_attention
            return self.output_norm(latent.mean(dim=1)), attention
        queries = self.queries.expand(len(memory), -1, -1)
        latent, attention = self.cross_attention(
            queries,
            memory,
            memory,
            key_padding_mask=memory_mask,
            need_weights=return_attention,
            average_attn_weights=False,
        )
        latent = self.self_encoder(latent)
        return self.output_norm(latent.mean(dim=1)), (
            attention if return_attention else None
        )


class CatalystTransferTransformer(nn.Module):
    """Full multimodal predictor with auditable attention and transfer gating."""

    def __init__(self, config: CatalystAttentionConfig) -> None:
        super().__init__()
        config.validate()
        self.config = config
        if config.composition_mode == "crabnet":
            composition_encoder = CrabNetCompositionEncoder
        elif config.composition_mode == "pairwise":
            composition_encoder = PairwiseElementEncoder
        else:
            composition_encoder = CompositionSetEncoder
        self.composition = composition_encoder(config)
        self.surface = (
            composition_encoder(config) if config.use_surface else None
        )
        self.curve = CurveTransformer(config)
        self.conditions = ConditionTokenEncoder(config)
        self.tasks = TaskTokenEncoder(config)
        self.modality_types = nn.Embedding(
            config.fusion_block_count, config.d_model
        )
        self.fusion = CrossModalFusion(config)
        hidden = config.d_model
        self.base_head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(hidden, 1),
        )
        self.log_variance_head = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, 1),
        )
        self.target_residual = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.Tanh(),
            nn.Linear(hidden // 2, 1),
        )
        self.support_head = nn.Sequential(
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, 1),
        )
        # Few-shot target calibration starts exactly at the frozen source
        # prediction.  A global affine correction is deliberately separated
        # from the support-gated local residual: systematic inter-program
        # offsets should not require an implausibly large residual in an OOD
        # region.
        self.target_scale = nn.Parameter(torch.ones(()))
        self.target_bias = nn.Parameter(torch.zeros(()))
        nn.init.zeros_(self.target_residual[-1].weight)
        nn.init.zeros_(self.target_residual[-1].bias)

    def _typed_memory(
        self, tokens: Tensor, mask: Tensor, modality: int
    ) -> tuple[Tensor, Tensor]:
        type_id = torch.full(
            tokens.shape[:2], modality, dtype=torch.long, device=tokens.device
        )
        return tokens + self.modality_types(type_id), mask

    def _apply_modality_dropout(
        self, mask: Tensor, modality: int
    ) -> tuple[Tensor, Tensor]:
        dropped = torch.zeros(
            len(mask), dtype=torch.bool, device=mask.device
        )
        if (
            self.training
            and self.config.modality_dropout > 0.0
            and modality != 4
        ):
            dropped = (
                torch.rand(len(mask), device=mask.device)
                < self.config.modality_dropout
            )
            if dropped.any():
                mask = mask.clone()
                mask[dropped] = True
        return mask, dropped

    def encode(
        self, batch: dict[str, Tensor], return_attention: bool = False
    ) -> tuple[Tensor, dict[str, Tensor]]:
        memories: list[Tensor] = []
        masks: list[Tensor] = []
        modality_labels: list[Tensor] = []
        dropped_modalities = torch.zeros(
            (
                len(batch["reaction_id"]),
                self.config.fusion_block_count,
            ),
            dtype=torch.bool,
            device=batch["reaction_id"].device,
        )
        audit: dict[str, Tensor] = {}
        if self.config.use_composition:
            tokens, mask, weights = self.composition(
                batch["elements"],
                batch["fractions"],
                batch["composition_padding_mask"],
                return_attention,
            )
            tokens, mask = self._typed_memory(tokens, mask, 0)
            mask, dropped = self._apply_modality_dropout(mask, 0)
            memories.append(tokens)
            masks.append(mask)
            dropped_modalities[:, 0] = dropped
            modality_labels.append(
                torch.zeros(tokens.shape[:2], dtype=torch.long, device=tokens.device)
            )
            if weights is not None:
                audit["composition_pool_attention"] = weights
        if self.config.use_surface:
            assert self.surface is not None
            tokens, mask, weights = self.surface(
                batch["surface_elements"],
                batch["surface_fractions"],
                batch["surface_padding_mask"],
                return_attention,
                batch["surface_present"],
            )
            tokens, mask = self._typed_memory(tokens, mask, 3)
            mask, dropped = self._apply_modality_dropout(mask, 3)
            memories.append(tokens)
            masks.append(mask)
            dropped_modalities[:, 3] = dropped
            modality_labels.append(
                torch.full(
                    tokens.shape[:2], 3, dtype=torch.long, device=tokens.device
                )
            )
            if weights is not None:
                audit["surface_pool_attention"] = weights
        if self.config.use_curve:
            tokens, mask = self.curve(
                batch["curve_axis"],
                batch["curve_values"],
                batch["curve_padding_mask"],
                batch["curve_channel_mask"],
                batch["curve_present"],
            )
            tokens, mask = self._typed_memory(tokens, mask, 1)
            mask, dropped = self._apply_modality_dropout(mask, 1)
            memories.append(tokens)
            masks.append(mask)
            dropped_modalities[:, 1] = dropped
            modality_labels.append(
                torch.ones(tokens.shape[:2], dtype=torch.long, device=tokens.device)
            )
        tokens, mask = self.tasks(
            batch["reaction_id"],
            batch["target_id"],
        )
        tokens, mask = self._typed_memory(tokens, mask, 4)
        memories.append(tokens)
        masks.append(mask)
        modality_labels.append(
            torch.full(
                tokens.shape[:2], 4, dtype=torch.long, device=tokens.device
            )
        )
        if self.config.use_conditions:
            tokens, mask = self.conditions(
                batch["condition_values"],
                batch["condition_mask"],
                batch["modality_id"],
                batch["program_id"],
            )
            tokens, mask = self._typed_memory(tokens, mask, 2)
            mask, dropped = self._apply_modality_dropout(mask, 2)
            memories.append(tokens)
            masks.append(mask)
            dropped_modalities[:, 2] = dropped
            modality_labels.append(
                torch.full(
                    tokens.shape[:2], 2, dtype=torch.long, device=tokens.device
                )
            )
        memory = torch.cat(memories, dim=1)
        memory_mask = torch.cat(masks, dim=1)
        audit["memory_modality"] = torch.cat(modality_labels, dim=1)
        audit["modality_dropped"] = dropped_modalities
        latent, fusion_attention = self.fusion(
            memory, memory_mask, return_attention
        )
        if fusion_attention is not None:
            audit["fusion_attention"] = fusion_attention
        audit["memory_padding_mask"] = memory_mask
        return latent, audit

    def forward(
        self,
        batch: dict[str, Tensor],
        *,
        adaptation: bool = False,
        external_source_support: Tensor | None = None,
        return_attention: bool = False,
    ) -> dict[str, Tensor | dict[str, Tensor]]:
        latent, attention = self.encode(batch, return_attention=return_attention)
        base = self.base_head(latent).squeeze(-1)
        residual = self.target_residual(latent).squeeze(-1)
        learned_support = torch.sigmoid(self.support_head(latent).squeeze(-1))
        if external_source_support is None:
            source_support = learned_support
        else:
            source_support = 0.5 * (
                learned_support + external_source_support.clamp(0.0, 1.0)
            )
        mean = base
        if adaptation:
            mean = (
                self.target_scale * base
                + self.target_bias
                + (1.0 - source_support) * residual
            )
        log_variance = self.log_variance_head(latent).squeeze(-1).clamp(-6.0, 4.0)
        output: dict[str, Tensor | dict[str, Tensor]] = {
            "mean": mean,
            "base_mean": base,
            "residual": residual,
            "log_variance": log_variance,
            "source_support": source_support,
            "latent": latent,
        }
        if return_attention:
            output["attention"] = attention
        return output

    def trainable_parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters() if parameter.requires_grad)


def attention_entropy(weights: Tensor, mask: Tensor | None = None) -> Tensor:
    """Normalized entropy for audit; attention weights are not causal evidence."""

    probabilities = weights.clamp_min(1e-12)
    if mask is not None:
        while mask.ndim < probabilities.ndim:
            mask = mask.unsqueeze(1)
        probabilities = probabilities.masked_fill(mask, 0.0)
        probabilities /= probabilities.sum(dim=-1, keepdim=True).clamp_min(1e-12)
    entropy = -(probabilities * probabilities.clamp_min(1e-12).log()).sum(dim=-1)
    valid = (probabilities > 0).sum(dim=-1).clamp_min(2)
    return entropy / valid.to(entropy.dtype).log()


def depth_routing_diagnostics(model: nn.Module) -> dict[str, dict]:
    """Summarize the latest Delta-MHAR routes without causal interpretation."""
    diagnostics: dict[str, dict] = {}
    for name, module in model.named_modules():
        if not isinstance(module, DeltaMultiHeadRouter):
            continue
        row: dict[str, object] = {
            "heads": module.heads,
            "gate": torch.tanh(module.gate).detach().cpu().tolist(),
        }
        weights = module.last_weights
        if weights is not None:
            mean_weights = weights.mean(dim=(1, 2))
            entropy = -(
                mean_weights.clamp_min(1e-12)
                * mean_weights.clamp_min(1e-12).log()
            ).sum(dim=0)
            if len(mean_weights) > 1:
                entropy = entropy / math.log(len(mean_weights))
            else:
                entropy = torch.zeros_like(entropy)
            row.update(
                {
                    "source_count": len(mean_weights),
                    "mean_max_weight": float(
                        mean_weights.max(dim=0).values.mean().cpu()
                    ),
                    "mean_normalized_entropy": float(
                        entropy.mean().cpu()
                    ),
                    "head_disagreement": float(
                        mean_weights.std(dim=1, unbiased=False).mean().cpu()
                    ),
                }
            )
        diagnostics[name] = row
    return diagnostics
