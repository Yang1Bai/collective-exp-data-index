#!/usr/bin/env python3
"""Policy-level transfer benchmark: representation rows vs decision row.

Runs the repo's first decision-layer experiment. For every directed
donor→recipient pair in the suite we:

1. train the representation baselines exactly as before
   (standard attention / contrastive / ExtraTrees) — the
   *representation-level* transfer rows;
2. compute an outcome-free edge state (source fit, coverage, distance,
   sizes, feature richness);
3. apply the frozen threshold policy, which decides
   apply / rank_only / abstain per (edge, neural method) WITHOUT seeing
   target outcomes;
4. report realized outcomes: policy row vs always-transfer row.

Success criteria (pre-registered here, printed at the end):
* the policy row's mean realized Spearman beats always-transfer for the
  same method;
* the policy has zero harm edges (no applied edge with negative rho);
* abstentions on historically harmful edges are correct.

Runtime: composition-only pairs reuse the fast composition-only config;
SpecGen pairs use the same settings as the published contrastive screen
(40 epochs). Full run ~ tens of minutes on CPU.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.alloy_loader import (  # noqa: E402
    load_birdshot, load_mpea, load_steels,
)
from catalyst_attention.data import (  # noqa: E402
    load_ocx24_csv, load_seccm_archives, load_specgen_archive,
)
from catalyst_attention.model import CatalystAttentionConfig  # noqa: E402
from catalyst_attention.policy_transfer import (  # noqa: E402
    FrozenThresholdPolicy,
    TransferEdgeState,
    always_transfer_baseline,
    edge_geometry,
    evaluate_policy,
    result_manifest,
)
from catalyst_attention.training import (  # noqa: E402
    TrainingConfig, metrics, predict, set_deterministic,
    targets_array, train_source_model,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
SPECGEN_PATH = Path("research/data/specgen.zip")
OCX24_PATH = Path("research/data/ocx24.csv")
SECCM_CACHE = Path.home() / ".collective_data_cache" / "catalyst_attention"
RESULTS_DIR = ROOT / "analysis" / "results"

SEED = 20260810


def spearman_of(model, target, normalizer, device) -> float:
    pred = predict(model, target, normalizer, device=device, unknown_program=True)["mean"]
    return float(metrics(targets_array(target), pred)["spearman"])


def run_neural(source, target, model_config, training_config, device, epochs_override=None):
    cfg = TrainingConfig(**{**training_config.__dict__, **({"epochs": epochs_override} if epochs_override else {})})
    model, norm, report = train_source_model(source, model_config, cfg, device=device)
    src_fit = float(report["source_apparent_metrics"]["spearman"])
    rho = spearman_of(model, target, norm, device)
    return src_fit, rho


def run_extra_trees(source, target):
    """Same 118-dim composition ExtraTrees as run_full_data_benchmark.py."""
    from sklearn.ensemble import ExtraTreesRegressor

    def comp_matrix(samples):
        m = np.zeros((len(samples), 118), dtype=np.float32)
        for i, s in enumerate(samples):
            if len(s.elements):
                m[i, s.elements - 1] = s.fractions
        return m

    et = ExtraTreesRegressor(
        n_estimators=500, min_samples_leaf=2, max_features=0.75,
        random_state=SEED, n_jobs=1,
    )
    et.fit(comp_matrix(source), targets_array(source))
    return float(metrics(targets_array(target), et.predict(comp_matrix(target)))["spearman"])


def build_pairs(args):
    """Return list of (pair_name, donor, recipient, donor_family, recipient_family, richness, model_config)."""
    composition_config = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3, curve_layers=1,
        fusion_layers=1, feedforward_multiplier=3,
        use_curve=False, use_conditions=False, use_surface=False, dropout=0.1,
    )
    ocx24_config = CatalystAttentionConfig(
        d_model=48, n_heads=4, composition_layers=3, curve_layers=1,
        fusion_layers=1, feedforward_multiplier=3,
        use_curve=False, use_conditions=True, use_surface=False, dropout=0.1,
    )
    seccm_config = CatalystAttentionConfig(
        d_model=64, n_heads=4, composition_layers=2, curve_layers=3,
        fusion_layers=2, feedforward_multiplier=3,
        use_curve=True, use_conditions=False, use_surface=True, dropout=0.1,
    )
    pairs = []

    print("Loading alloy datasets ...", flush=True)
    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")

    alloy = [
        ("steels→mpea", steels, mpea, "steels", "mpea"),
        ("steels→birdshot", steels, birdshot, "steels", "birdshot"),
        ("mpea→steels", mpea, steels, "mpea", "steels"),
        ("mpea→birdshot", mpea, birdshot, "mpea", "birdshot"),
        ("birdshot→steels", birdshot, steels, "birdshot", "steels"),
        ("birdshot→mpea", birdshot, mpea, "birdshot", "mpea"),
    ]
    for name, src, tgt, sfam, tfam in alloy:
        pairs.append((name, src, tgt, sfam, tfam, 0.0, composition_config))

    if not args.skip_ocx24 and OCX24_PATH.exists():
        print("Loading OCx24 (fe_co) ...", flush=True)
        ocx24 = load_ocx24_csv(OCX24_PATH, "fe_co")
        uoft = [s for s in ocx24 if s.program == "ocx24_uoft"]
        vsp = [s for s in ocx24 if s.program == "ocx24_vsp"]
        print(f"  uoft={len(uoft)} vsp={len(vsp)}", flush=True)
        pairs.append(("ocx24_uoft→vsp", uoft, vsp, "ocx24_uoft", "ocx24_vsp", 0.3, ocx24_config))
        pairs.append(("ocx24_vsp→uoft", vsp, uoft, "ocx24_vsp", "ocx24_uoft", 0.3, ocx24_config))

    if not args.skip_seccm:
        seccm_zip = SECCM_CACHE / "SECCM_dataset.zip"
        edx_zip = SECCM_CACHE / "EDX_dataset.zip"
        xps_zip = SECCM_CACHE / "XPS_dataset.zip"
        if seccm_zip.exists() and edx_zip.exists():
            print("Loading SECCM Au-Ir-Rh (log10_k0) ...", flush=True)
            seccm = load_seccm_archives(seccm_zip, edx_zip, xps_zip if xps_zip.exists() else None)
            libs = {}
            for s in seccm:
                libs.setdefault(s.program, []).append(s)
            for k, v in libs.items():
                print(f"  {k}={len(v)}", flush=True)
            # The repo's documented negative-transfer boundary: cross-library
            # HER transfer inside one ternary system.
            au, ir, rh = libs["seccm_Au-rich"], libs["seccm_Ir-rich"], libs["seccm_Rh-rich"]
            pairs.append(("seccm_Ir→Au", ir, au, "seccm_Ir-rich", "seccm_Au-rich", 0.7, seccm_config))
            pairs.append(("seccm_Au→Ir", au, ir, "seccm_Au-rich", "seccm_Ir-rich", 0.7, seccm_config))
            pairs.append(("seccm_Rh→Au", rh, au, "seccm_Rh-rich", "seccm_Au-rich", 0.7, seccm_config))

    if not args.skip_specgen and SPECGEN_PATH.exists():
        print("Loading SpecGen archive ...", flush=True)
        specgen_source, specgen_targets = _load_specgen()
        specgen_config = CatalystAttentionConfig(
            d_model=64, n_heads=4, composition_layers=2, curve_layers=3,
            fusion_layers=2, feedforward_multiplier=3, dropout=0.1,
        )
        for tname, tdata in specgen_targets.items():
            pairs.append(
                (f"specgen→{tname}", specgen_source, tdata, "specgen", f"specgen_{tname}", 1.0, specgen_config)
            )
    return pairs


def _load_specgen():
    samples = load_specgen_archive(SPECGEN_PATH)
    source = [s for s in samples if s.program == "specgen_source"]
    targets: dict[str, list] = {}
    for s in samples:
        if s.program != "specgen_source":
            targets.setdefault(s.program, []).append(s)
    return source, targets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-specgen", action="store_true", help="skip SpecGen pairs")
    parser.add_argument("--skip-ocx24", action="store_true", help="skip OCx24 pairs")
    parser.add_argument("--skip-seccm", action="store_true", help="skip SECCM pairs")
    parser.add_argument("--specgen-epochs", type=int, default=40)
    parser.add_argument("--alloy-epochs", type=int, default=100)
    parser.add_argument("--out", default=str(RESULTS_DIR / "policy_transfer_benchmark.json"))
    args = parser.parse_args()

    device = torch.device("cpu")
    set_deterministic(SEED)
    t0 = time.time()

    pairs = build_pairs(args)
    print(f"\n{len(pairs)} directed pairs queued\n", flush=True)

    base_training = TrainingConfig(
        seed=SEED, epochs=args.alloy_epochs, patience=20, batch_size=32,
        learning_rate=8e-4, rank_weight=0.15, nll_weight=0.10,
    )
    contrastive_training = TrainingConfig(
        seed=SEED, epochs=args.alloy_epochs, patience=20, batch_size=32,
        learning_rate=8e-4, rank_weight=0.15, nll_weight=0.10,
        contrastive_weight=0.2,
    )

    states: list[TransferEdgeState] = []
    realized: dict[tuple[str, str], float] = {}
    edge_rows = []

    for pair_name, source, target, sfam, tfam, richness, model_config in pairs:
        print(f"=== {pair_name} (src_n={len(source)}, tgt_n={len(target)}) ===", flush=True)
        geo = edge_geometry(source, target)
        print(f"  coverage={geo['coverage']:.3f} mean_min_dist={geo['mean_min_distance']:.3f}", flush=True)

        epochs = args.specgen_epochs if richness > 0 else None
        for method, cfg in (("standard", base_training), ("contrastive", contrastive_training)):
            src_fit, rho = run_neural(source, target, model_config, cfg, device, epochs)
            realized[(pair_name, method)] = rho
            states.append(TransferEdgeState(
                pair_name=pair_name, method=method,
                source_n=len(source), target_n=len(target),
                source_fit_spearman=src_fit,
                coverage=geo["coverage"], mean_min_distance=geo["mean_min_distance"],
                donor_family=sfam, recipient_family=tfam, feature_richness=richness,
            ))
            print(f"  {method:12s} src_fit={src_fit:.3f} transfer_rho={rho:+.3f}", flush=True)

        et_rho = run_extra_trees(source, target)
        realized[(pair_name, "extra_trees")] = et_rho
        print(f"  extra_trees  transfer_rho={et_rho:+.3f}", flush=True)

        edge_rows.append({
            "pair": pair_name, "donor_family": sfam, "recipient_family": tfam,
            "source_n": len(source), "target_n": len(target), **geo,
            "standard_rho": realized[(pair_name, "standard")],
            "contrastive_rho": realized[(pair_name, "contrastive")],
            "extra_trees_rho": et_rho,
        })

    # ---- decision layer ----
    policy = FrozenThresholdPolicy()
    policy_result = evaluate_policy(policy, states, realized)
    naive_result = always_transfer_baseline(states, realized)

    # always-transfer aggregated per method for a fair comparison
    methods = ("standard", "contrastive")
    naive_by_method = {
        m: float(np.mean([
            realized[(s.pair_name, m)] for s in states if s.method == m
        ]))
        for m in methods
    }
    harm_by_method = {
        m: sum(1 for s in states if s.method == m and realized[(s.pair_name, m)] < 0.0)
        for m in methods
    }

    out = {
        "design": "policy-transfer-benchmark-v1",
        "seed": SEED,
        "wall_time_s": round(time.time() - t0, 1),
        "edges": edge_rows,
        "policy": result_manifest(policy_result),
        "always_transfer": {
            "mean_realized_spearman_by_method": naive_by_method,
            "harm_edges_by_method": harm_by_method,
        },
        "extra_trees_row": {
            e["pair"]: e["extra_trees_rho"] for e in edge_rows
        },
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1))

    # ---- report ----
    decisions: dict[tuple[str, str], str] = {
        (e.state.pair_name, e.state.method): e.decision for e in policy_result.edges
    }
    print("\n" + "=" * 72)
    print("POLICY-LEVEL BENCHMARK (decision layer vs representation layer)")
    print("=" * 72)
    print(f"{'pair':22s} {'cov':>5s} {'std':>7s} {'contr':>7s} {'ET':>7s}  decisions(std/contr)")
    for row in edge_rows:
        std_dec = decisions[(row['pair'], 'standard')]
        con_dec = decisions[(row['pair'], 'contrastive')]
        print(f"{row['pair']:22s} {row['coverage']:5.2f} "
              f"{row['standard_rho']:+7.3f} {row['contrastive_rho']:+7.3f} {row['extra_trees_rho']:+7.3f}  "
              f"{std_dec}/{con_dec}")
    print("\nFrozen policy :", json.dumps(policy_result.summary(), indent=1))
    print("Always transfer mean rho by method:", {k: round(v, 4) for k, v in naive_by_method.items()})
    print("Always transfer harm edges by method:", harm_by_method)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
