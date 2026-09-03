#!/usr/bin/env python3
"""Transfer-aware genetic algorithm benchmark.

Uses GA to search for architectures that maximize TRANSFER performance,
not source-domain performance. Each individual is evaluated on its
zero-shot transfer to the target domain.

Key difference from standard GA: fitness = transfer_spearman, not source_spearman.
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import load_birdshot, load_mpea, load_steels
from catalyst_attention.data import download_pinned, load_specgen_archive
from catalyst_attention.data import SPECGEN_BYTES, SPECGEN_SHA256, SPECGEN_URL
from catalyst_attention.transfer_ga import run_transfer_ga
from catalyst_attention.training import set_deterministic, write_json

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
RESULTS_DIR = ROOT / "analysis" / "results"


def main():
    device = torch.device("cpu")
    set_deterministic(20260802)
    t0 = time.time()

    # Load data.
    sp_path = Path("research/data/specgen.zip")
    if not sp_path.is_file():
        download_pinned(SPECGEN_URL, sp_path, SPECGEN_SHA256, SPECGEN_BYTES)

    specgen = load_specgen_archive(sp_path)
    sp_by = {}
    for s in specgen:
        sp_by.setdefault(s.program, []).append(s)

    steels = load_steels(DB_PATH, "yield strength")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")

    # Run GA on key transfer directions.
    experiments = [
        ("specgen_A", sp_by["specgen_source"], sp_by["specgen_A"]),
        ("specgen_D", sp_by["specgen_source"], sp_by["specgen_D"]),
        ("steel_bird", steels, birdshot),
    ]

    all_results = {}

    for exp_name, source, target in experiments:
        print(f"\n{'='*60}")
        print(f"  TRANSFER GA: {exp_name}")
        print(f"  Source: {len(source)}, Target: {len(target)}")
        print(f"{'='*60}")

        result = run_transfer_ga(
            source, target,
            device=device,
            population_size=8,  # Small for speed
            generations=4,
            epochs=30,  # Reduced for screening
            seed=20260802,
        )

        all_results[exp_name] = result

        print(f"\n  Best config:")
        print(f"    Transfer Spearman: {result['best_transfer_fitness']:.4f}")
        print(f"    Source Spearman:   {result['best_source_fitness']:.4f}")
        print(f"    Combined:          {result['best_combined_fitness']:.4f}")
        print(f"    Genes: {result['best_genes']}")

    # Save.
    out = RESULTS_DIR / "transfer_ga_results.json"
    write_json(out, {
        "experiments": all_results,
        "wall_time_s": round(time.time() - t0, 1),
    })
    print(f"\n  Results → {out}")


if __name__ == "__main__":
    main()
