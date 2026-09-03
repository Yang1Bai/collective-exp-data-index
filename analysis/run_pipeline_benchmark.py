#!/usr/bin/env python3
"""Full pipeline benchmark combining best knowledge-transfer methods.

The pipeline integrates:
  - Pairwise element interaction encoder (composition_mode="pairwise")
  - Adversarial domain adaptation (gradient reversal on latent)
  - Contrastive representation learning (NT-Xent on composition similarity)
  - Optional: Delta-MHAR depth routing

All components are trained jointly in a single run. The pipeline is
evaluated on SpecGen and OCx24 transfer directions using the same
frozen-gate protocol as all previous experiments.

Usage:
    python run_pipeline_benchmark.py [--device cpu|cuda] [--epochs 180]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.data import (  # noqa: E402
    CatalystSample,
    download_pinned,
    load_ocx24_csv,
    load_specgen_archive,
    OCX24_BYTES,
    OCX24_SHA256,
    OCX24_URL,
    SPECGEN_BYTES,
    SPECGEN_SHA256,
    SPECGEN_URL,
)
from catalyst_attention.model import CatalystAttentionConfig  # noqa: E402
from catalyst_attention.training import (  # noqa: E402
    TrainingConfig,
    few_shot_experiment,
    metrics,
    predict,
    set_deterministic,
    targets_array,
    train_source_model,
    write_json,
)

DATA_DIR = ROOT / "research" / "data"
RESULTS_DIR = ROOT / "analysis" / "results"


@dataclass
class PipelineConfig:
    """All pipeline hyperparameters in one place."""
    # Model architecture.
    composition_mode: str = "pairwise"
    depth_routing: str = "standard"
    fusion_mode: str = "cross_attention"
    d_model: int = 64
    n_heads: int = 4

    # Domain adversarial.
    adversarial_weight: float = 0.07
    grl_lambda: float = 1.0

    # Contrastive.
    contrastive_weight: float = 0.07
    contrastive_temperature: float = 0.1

    # Training.
    epochs: int = 180
    learning_rate: float = 8e-4
    weight_decay: float = 2e-4
    rank_weight: float = 0.22
    nll_weight: float = 0.18

    def to_model_config(self) -> CatalystAttentionConfig:
        return CatalystAttentionConfig(
            d_model=self.d_model,
            n_heads=self.n_heads,
            composition_mode=self.composition_mode,
            depth_routing=self.depth_routing,
            fusion_mode=self.fusion_mode,
        )

    def to_training_config(self, seed: int) -> TrainingConfig:
        return TrainingConfig(
            seed=seed,
            epochs=self.epochs,
            batch_size=32,
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            rank_weight=self.rank_weight,
            nll_weight=self.nll_weight,
            domain_adversarial_weight=self.adversarial_weight,
            contrastive_weight=self.contrastive_weight,
            grl_lambda=self.grl_lambda,
            contrastive_temperature=self.contrastive_temperature,
        )


def evaluate_direction(
    model: torch.nn.Module,
    source_samples: Sequence[CatalystSample],
    target_samples: Sequence[CatalystSample],
    normalizer,
    training_config: TrainingConfig,
    device: torch.device,
    *,
    direction_name: str,
    anchors: int = 5,
    draws: int = 20,
    seed: int = 0,
) -> dict:
    """Full evaluation: zero-shot + few-shot for one transfer direction."""
    from catalyst_attention.training import calibrate_support

    # Zero-shot.
    zero_pred = predict(
        model, target_samples, normalizer,
        device=device, unknown_program=True,
    )["mean"]
    zero_metrics = metrics(targets_array(target_samples), zero_pred)

    # Few-shot with adaptation.
    few_shot = few_shot_experiment(
        model, source_samples, target_samples, normalizer,
        training_config, anchors=anchors, draws=draws, seed=seed, device=device,
    )

    return {
        "direction": direction_name,
        "target_samples": len(target_samples),
        "zero_shot": zero_metrics,
        "few_shot": {
            "adapted_spearman": few_shot["adapted"]["spearman"],
            "adapted_rmse": few_shot["adapted"]["rmse"],
            "bias_calibrated_spearman": few_shot["bias_calibrated_attention"]["spearman"],
            "target_only_spearman": few_shot["target_only"]["spearman"],
            "spearman_gain_vs_target_only": few_shot["gains"]["spearman"],
            "rmse_gain_vs_target_only": few_shot["gains"]["relative_rmse"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline benchmark")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=180)
    parser.add_argument("--seed", type=int, default=20260802)
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--anchors", type=int, default=5)
    parser.add_argument("--adversarial-weight", type=float, default=0.07)
    parser.add_argument("--contrastive-weight", type=float, default=0.07)
    parser.add_argument("--grl-lambda", type=float, default=1.0)
    parser.add_argument("--depth-routing", default="standard",
                        choices=["standard", "delta_mhar_sublayer"])
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    device = torch.device(args.device)
    set_deterministic(args.seed)
    t0 = time.time()

    pipeline = PipelineConfig(
        epochs=args.epochs,
        adversarial_weight=args.adversarial_weight,
        contrastive_weight=args.contrastive_weight,
        grl_lambda=args.grl_lambda,
        depth_routing=args.depth_routing,
    )

    # --- Load data ---
    specgen_path = DATA_DIR / "specgen.zip"
    ocx24_path = DATA_DIR / "ocx24.csv"
    if not specgen_path.is_file():
        download_pinned(SPECGEN_URL, specgen_path, SPECGEN_SHA256, SPECGEN_BYTES)
    if not ocx24_path.is_file():
        download_pinned(OCX24_URL, ocx24_path, OCX24_SHA256, OCX24_BYTES)

    specgen = load_specgen_archive(specgen_path)
    ocx24 = load_ocx24_csv(ocx24_path, target_name="fe_co")

    sp_by_prog: dict[str, list] = {}
    for s in specgen:
        sp_by_prog.setdefault(s.program, []).append(s)
    oc_by_prog: dict[str, list] = {}
    for s in ocx24:
        oc_by_prog.setdefault(s.program, []).append(s)

    results: dict = {
        "pipeline": asdict(pipeline),
        "seed": args.seed,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    # ==== SpecGen ====
    print("=" * 60)
    print("  PIPELINE: SpecGen source training")
    print("=" * 60)
    print(f"  adversarial_weight={pipeline.adversarial_weight}, "
          f"contrastive_weight={pipeline.contrastive_weight}, "
          f"composition_mode={pipeline.composition_mode}, "
          f"depth_routing={pipeline.depth_routing}")

    sp_source = sp_by_prog["specgen_source"]
    sp_targets = {p: sp_by_prog[p] for p in ["specgen_A", "specgen_B", "specgen_C", "specgen_D"]}

    sp_model, sp_normalizer, sp_report = train_source_model(
        sp_source,
        pipeline.to_model_config(),
        pipeline.to_training_config(args.seed),
        device=device,
    )
    results["specgen_source"] = {
        "source_spearman": sp_report["source_apparent_metrics"]["spearman"],
        "validation_spearman": sp_report["validation_metrics"]["spearman"],
        "best_epoch": sp_report["best_epoch"],
        "parameter_count": sp_report["parameter_count"],
        "directions": {},
    }
    print(f"  Source Spearman: {sp_report['source_apparent_metrics']['spearman']:.4f}")

    sp_transfer_spearmans = []
    for prog, samples in sp_targets.items():
        print(f"\n  --- SpecGen source → {prog} ---")
        d = evaluate_direction(
            sp_model, sp_source, samples, sp_normalizer,
            pipeline.to_training_config(args.seed),
            device, direction_name=f"specgen_source→{prog}",
            anchors=args.anchors, draws=args.draws, seed=args.seed,
        )
        results["specgen_source"]["directions"][prog] = d
        zs = d["zero_shot"]["spearman"]
        fs = d["few_shot"]["adapted_spearman"]["median"]
        sp_transfer_spearmans.append(zs)
        print(f"    zero-shot Spearman={zs:.4f}, few-shot Spearman={fs:.4f}")

    results["specgen_source"]["aggregate"] = {
        "median_transfer_spearman": float(np.median(sp_transfer_spearmans)),
        "mean_transfer_spearman": float(np.mean(sp_transfer_spearmans)),
    }

    # ==== OCx24 ====
    print("\n" + "=" * 60)
    print("  PIPELINE: OCx24 training")
    print("=" * 60)

    ocx24_results: dict = {}
    ocx24_all_gains: list[float] = []

    for source_prog in ["ocx24_uoft", "ocx24_vsp"]:
        oc_source = oc_by_prog[source_prog]
        target_prog = "ocx24_vsp" if source_prog == "ocx24_uoft" else "ocx24_uoft"
        oc_target = oc_by_prog[target_prog]

        print(f"\n  --- OCx24 {source_prog} training ({len(oc_source)} samples) ---")
        oc_model, oc_normalizer, oc_report = train_source_model(
            oc_source,
            pipeline.to_model_config(),
            pipeline.to_training_config(args.seed),
            device=device,
        )
        print(f"  Source Spearman: {oc_report['source_apparent_metrics']['spearman']:.4f}")

        oc_dir = {}
        oc_dir["source_spearman"] = oc_report["source_apparent_metrics"]["spearman"]
        oc_dir["validation_spearman"] = oc_report["validation_metrics"]["spearman"]

        d = evaluate_direction(
            oc_model, oc_source, oc_target, oc_normalizer,
            pipeline.to_training_config(args.seed),
            device, direction_name=f"{source_prog}→{target_prog}",
            anchors=args.anchors, draws=args.draws, seed=args.seed,
        )
        oc_dir["transfer"] = d
        ocx24_results[source_prog] = oc_dir

        gain = d["few_shot"]["spearman_gain_vs_target_only"]["median"]
        ocx24_all_gains.append(gain)
        print(f"    {source_prog}→{target_prog}: "
              f"zero-shot={d['zero_shot']['spearman']:.4f}, "
              f"few-shot gain={gain:+.4f}")

    results["ocx24"] = ocx24_results

    # ==== Aggregate ====
    all_gains = []
    for prog in sp_targets:
        d = results["specgen_source"]["directions"][prog]
        all_gains.append(d["few_shot"]["spearman_gain_vs_target_only"]["median"])

    all_gains.extend(ocx24_all_gains)

    results["aggregate"] = {
        "total_directions": len(all_gains),
        "median_spearman_gain_vs_target_only": float(np.median(all_gains)),
        "positive_directions": sum(1 for g in all_gains if g > 0),
        "all_gains": all_gains,
        "wall_time_seconds": round(time.time() - t0, 1),
    }

    gate_passed = (
        float(np.median(all_gains)) > 0
        and sum(1 for g in all_gains if g > 0) >= len(all_gains) // 2
    )
    results["gate"] = {
        "passed": gate_passed,
        "criterion": "median gain > 0 AND >= half of directions positive",
    }

    out_path = RESULTS_DIR / (args.output or "pipeline_benchmark.json")
    write_json(out_path, results)

    print(f"\n{'='*60}")
    print(f"  PIPELINE RESULTS")
    print(f"{'='*60}")
    print(f"  Median gain vs target-only: {results['aggregate']['median_spearman_gain_vs_target_only']:+.4f}")
    print(f"  Positive directions: {results['aggregate']['positive_directions']}/{results['aggregate']['total_directions']}")
    print(f"  Gate passed: {gate_passed}")
    print(f"  Total wall time: {results['aggregate']['wall_time_seconds']:.0f}s")
    print(f"  Results → {out_path}")


if __name__ == "__main__":
    main()
