#!/usr/bin/env python3
"""Latent interpolation: bridge source→target domain gap with k-NN.

For each target sample, finds k-nearest source compositions (by cosine
similarity in 118-dim periodic table space), then interpolates their
latents to get a synthetic representation on the source manifold.

This is a much simpler alternative to diffusion that can actually work
with 462 training samples.
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (
    download_pinned, load_specgen_archive,
    SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL,
)
from catalyst_attention.latent_diffusion import (
    extract_latents, _composition_to_vector,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.training import (
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model, write_json,
)

RESULTS_DIR = ROOT / "analysis" / "results"


def knn_interpolate_latents(
    source_latents: np.ndarray,
    source_compositions: np.ndarray,
    target_compositions: np.ndarray,
    *,
    k: int = 5,
    temperature: float = 0.1,
) -> np.ndarray:
    """For each target composition, find k-nearest source compositions
    and return a weighted average of their latents.

    Parameters
    ----------
    source_latents: (n_source, d_model)
    source_compositions: (n_source, 118)
    target_compositions: (n_target, 118)
    k: number of neighbors
    temperature: softmax temperature for weighting (lower = sharper)

    Returns
    -------
    (n_target, d_model) interpolated latents.
    """
    # Normalize composition vectors for cosine similarity.
    src_norm = source_compositions / (
        np.linalg.norm(source_compositions, axis=1, keepdims=True) + 1e-12
    )
    tgt_norm = target_compositions / (
        np.linalg.norm(target_compositions, axis=1, keepdims=True) + 1e-12
    )
    sim = tgt_norm @ src_norm.T  # (n_target, n_source) cosine similarities.

    interpolated = np.zeros((len(target_compositions), source_latents.shape[1]),
                            dtype=np.float32)
    for i in range(len(target_compositions)):
        top_k = np.argpartition(-sim[i], k)[:k]
        weights = np.exp(sim[i, top_k] / temperature)
        weights /= weights.sum()
        interpolated[i] = (weights[:, None] * source_latents[top_k]).sum(axis=0)

    return interpolated


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--seed", type=int, default=20260802)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--temperature", type=float, default=0.1)
    args = p.parse_args()

    device = torch.device("cpu")
    set_deterministic(args.seed)
    t0 = time.time()

    # Load data.
    sp = Path("research/data/specgen.zip")
    if not sp.is_file():
        download_pinned(SPECGEN_URL, sp, SPECGEN_SHA256, SPECGEN_BYTES)
    specgen = load_specgen_archive(sp)
    by_prog = {}
    for s in specgen:
        by_prog.setdefault(s.program, []).append(s)

    source = by_prog["specgen_source"]
    targets = {p: by_prog[p] for p in ["specgen_A","specgen_B","specgen_C","specgen_D"]}

    # Phase 1: Train encoder.
    print("=" * 60)
    print(f"  PHASE 1: Training encoder ({args.epochs} epochs)")
    print("=" * 60)
    model, normalizer, report = train_source_model(
        source, CatalystAttentionConfig(),
        TrainingConfig(seed=args.seed, epochs=args.epochs,
                       patience=max(10, args.epochs // 6)),
        device=device,
    )
    src_sp = report["source_apparent_metrics"]["spearman"]
    print(f"  Source Spearman: {src_sp:.4f}")

    # Baseline.
    print("\n  Baseline zero-shot:")
    baseline = {}
    bl_sp = []
    for prog, samples in targets.items():
        pred = predict(model, samples, normalizer, device=device, unknown_program=True)["mean"]
        m = metrics(targets_array(samples), pred)
        baseline[prog] = m
        bl_sp.append(m["spearman"])
        print(f"    {prog}: {m['spearman']:.4f}")

    # Phase 2: Extract source latents + compositions.
    source_lats = extract_latents(model, source, normalizer, device=device)
    source_comps = _composition_to_vector(source)

    # Phase 3: For each target, interpolate latents from nearest source compositions.
    print(f"\n{'='*60}")
    print(f"  PHASE 2: k-NN latent interpolation (k={args.k}, T={args.temperature})")
    print(f"{'='*60}")

    interp_results = {}
    interp_sp = []
    interp_weights_all = []

    model.eval()
    for prog, samples in targets.items():
        target_comps = _composition_to_vector(samples)

        # Interpolate latents.
        syn_lats = knn_interpolate_latents(
            source_lats, source_comps, target_comps,
            k=args.k, temperature=args.temperature,
        )

        # Pass through prediction head.
        with torch.no_grad():
            syn_tensor = torch.from_numpy(syn_lats).float()
            base_pred = model.base_head(syn_tensor).squeeze(-1)
            means = normalizer.inverse_target(base_pred.numpy())

        m = metrics(targets_array(samples), means)
        interp_results[prog] = m
        interp_sp.append(m["spearman"])
        print(f"    {prog}: Spearman={m['spearman']:.4f} "
              f"(baseline={baseline[prog]['spearman']:.4f})")

    # Also: combine real encoder + interpolated (ensemble)
    combined_results = {}
    combined_sp = []
    for prog, samples in targets.items():
        real_pred = predict(model, samples, normalizer, device=device, unknown_program=True)["mean"]
        interp_pred = interp_results[prog]  # just stored metrics, need to recompute

        target_comps = _composition_to_vector(samples)
        syn_lats = knn_interpolate_latents(
            source_lats, source_comps, target_comps,
            k=args.k, temperature=args.temperature,
        )
        with torch.no_grad():
            syn_tensor = torch.from_numpy(syn_lats).float()
            interp_means = normalizer.inverse_target(
                model.base_head(syn_tensor).squeeze(-1).numpy()
            )

        ensemble_mean = 0.5 * (real_pred + interp_means)
        m = metrics(targets_array(samples), ensemble_mean)
        combined_results[prog] = m
        combined_sp.append(m["spearman"])

    # ---- Compare ----
    print(f"\n{'='*60}")
    print(f"  COMPARISON")
    print(f"{'='*60}")
    print(f"  {'Program':<12} {'Baseline':>10} {'k-NN Interp':>12} {'Ensemble':>10}")
    gains_interp = []
    gains_ens = []
    for prog in targets:
        bl = baseline[prog]["spearman"]
        ip = interp_results[prog]["spearman"]
        en = combined_results[prog]["spearman"]
        gains_interp.append(ip - bl)
        gains_ens.append(en - bl)
        print(f"  {prog:<12} {bl:10.4f} {ip:12.4f} {en:10.4f}")

    print(f"\n  Median baseline:  {np.median(bl_sp):.4f}")
    print(f"  Median k-NN:      {np.median(interp_sp):.4f} "
          f"(gain={np.median(gains_interp):+.4f})")
    print(f"  Median Ensemble:  {np.median(combined_sp):.4f} "
          f"(gain={np.median(gains_ens):+.4f})")

    # Save.
    out = RESULTS_DIR / "latent_interpolation.json"
    write_json(out, {
        "k": args.k, "temperature": args.temperature,
        "baseline": {p: baseline[p] for p in targets},
        "knn_interpolation": {p: interp_results[p] for p in targets},
        "ensemble": {p: combined_results[p] for p in targets},
        "aggregate": {
            "median_baseline": float(np.median(bl_sp)),
            "median_knn": float(np.median(interp_sp)),
            "median_ensemble": float(np.median(combined_sp)),
            "median_knn_gain": float(np.median(gains_interp)),
            "median_ensemble_gain": float(np.median(gains_ens)),
        },
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
