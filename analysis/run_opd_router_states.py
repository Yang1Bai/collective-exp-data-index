#!/usr/bin/env python3
"""Real RouterState prompt suite for the OPD expert router.

The smoke prompts shipped with the OPD pilot are synthetic; the design
contract (catalyst_opd_router_design.json) requires a held-out teacher
advantage and real, programme-held-out routing states before any
scientific claim. This runner trains the frozen Standard / Delta-MHAR
expert pair on real donor programmes and derives one target-label-free
:class:`RouterState` per directed transfer edge, split by donor
programme for leave-one-programme-out evaluation.

Each emitted row contains:

* ``state`` — exactly the 12 allowed prompt fields, computed WITHOUT any
  target outcome (source validation Spearman, predictive stds, expert
  disagreement, domain share, composition support);
* ``evaluation`` — evaluation-only payload: realized zero-shot Spearman
  of each expert and their ensemble on the recipient, plus the oracle
  expert identity. Never rendered into any prompt.

Outputs ``analysis/results/opd_router_real_states.json`` plus a JSONL
rendering for the pilot runner.
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

from catalyst_attention.alloy_loader import (
    load_birdshot,
    load_mpea,
    load_steels,
)
from catalyst_attention.data import (
    load_ocx24_csv,
    load_seccm_archives,
    load_specgen_archive,
)
from catalyst_attention.expert_router import (
    ExpertRouter,
    train_expert_pair,
)
from catalyst_attention.model import CatalystAttentionConfig
from catalyst_attention.policy_transfer import edge_geometry
from catalyst_attention.training import (
    TrainingConfig,
    metrics,
    set_deterministic,
    targets_array,
)

DB_PATH = Path("collaborator_workspace/data/data/collective.sqlite")
SPECGEN_PATH = Path("research/data/specgen.zip")
OCX24_PATH = Path("research/data/ocx24.csv")
SECCM_CACHE = Path.home() / ".collective_data_cache" / "catalyst_attention"
RESULTS_DIR = ROOT / "analysis" / "results"

SEED = 20260810


def _condition_fraction(samples) -> float:
    observed = [float(s.condition_mask.mean()) for s in samples]
    return float(np.mean(observed)) if observed else 0.0


def build_edges(args):
    """Return list of dicts: name, split_group (donor family), source, target, model_config."""
    composition_config = CatalystAttentionConfig(
        d_model=48,
        n_heads=4,
        composition_layers=3,
        curve_layers=1,
        fusion_layers=1,
        feedforward_multiplier=3,
        use_curve=False,
        use_conditions=False,
        use_surface=False,
        dropout=0.1,
    )
    ocx24_config = CatalystAttentionConfig(
        d_model=48,
        n_heads=4,
        composition_layers=3,
        curve_layers=1,
        fusion_layers=1,
        feedforward_multiplier=3,
        use_curve=False,
        use_conditions=True,
        use_surface=False,
        dropout=0.1,
    )
    rich_config = CatalystAttentionConfig(
        d_model=64,
        n_heads=4,
        composition_layers=2,
        curve_layers=3,
        fusion_layers=2,
        feedforward_multiplier=3,
        dropout=0.1,
    )
    seccm_config = CatalystAttentionConfig(
        d_model=64,
        n_heads=4,
        composition_layers=2,
        curve_layers=3,
        fusion_layers=2,
        feedforward_multiplier=3,
        use_curve=True,
        use_conditions=False,
        use_surface=True,
        dropout=0.1,
    )
    edges = []

    print("Loading alloy datasets ...", flush=True)
    steels = load_steels(DB_PATH, "yield strength")
    mpea = load_mpea(DB_PATH, "YS (MPa)")
    birdshot = load_birdshot(DB_PATH, "Yield Strength (MPa)")
    for name, src, tgt in [
        ("steels→mpea", steels, mpea),
        ("steels→birdshot", steels, birdshot),
        ("mpea→steels", mpea, steels),
        ("mpea→birdshot", mpea, birdshot),
        ("birdshot→steels", birdshot, steels),
        ("birdshot→mpea", birdshot, mpea),
    ]:
        edges.append(
            {
                "name": name,
                "split": name.split("→")[0],
                "source": src,
                "target": tgt,
                "config": composition_config,
                "richness": 0.0,
            }
        )

    if not args.skip_ocx24 and OCX24_PATH.exists():
        print("Loading OCx24 ...", flush=True)
        ocx24 = load_ocx24_csv(OCX24_PATH, "fe_co")
        uoft = [s for s in ocx24 if s.program == "ocx24_uoft"]
        vsp = [s for s in ocx24 if s.program == "ocx24_vsp"]
        edges.append(
            {
                "name": "ocx24_uoft→vsp",
                "split": "ocx24_uoft",
                "source": uoft,
                "target": vsp,
                "config": ocx24_config,
                "richness": 0.3,
            }
        )
        edges.append(
            {
                "name": "ocx24_vsp→uoft",
                "split": "ocx24_vsp",
                "source": vsp,
                "target": uoft,
                "config": ocx24_config,
                "richness": 0.3,
            }
        )

    if not args.skip_seccm:
        seccm_zip = SECCM_CACHE / "SECCM_dataset.zip"
        edx_zip = SECCM_CACHE / "EDX_dataset.zip"
        xps_zip = SECCM_CACHE / "XPS_dataset.zip"
        if seccm_zip.exists() and edx_zip.exists():
            print("Loading SECCM ...", flush=True)
            seccm = load_seccm_archives(
                seccm_zip, edx_zip, xps_zip if xps_zip.exists() else None
            )
            libs = {}
            for s in seccm:
                libs.setdefault(s.program, []).append(s)
            au, ir, rh = (
                libs["seccm_Au-rich"],
                libs["seccm_Ir-rich"],
                libs["seccm_Rh-rich"],
            )
            for name, src, tgt in [
                ("seccm_Ir→Au", ir, au),
                ("seccm_Au→Ir", au, ir),
                ("seccm_Rh→Au", rh, au),
            ]:
                edges.append(
                    {
                        "name": name,
                        "split": name.split("→")[0].split("_")[1],
                        "source": src,
                        "target": tgt,
                        "config": seccm_config,
                        "richness": 0.7,
                    }
                )

    if not args.skip_specgen and SPECGEN_PATH.exists():
        print("Loading SpecGen ...", flush=True)
        samples = load_specgen_archive(SPECGEN_PATH)
        source = [s for s in samples if s.program == "specgen_source"]
        targets = {}
        for s in samples:
            if s.program != "specgen_source":
                targets.setdefault(s.program, []).append(s)
        for tname, tdata in targets.items():
            edges.append(
                {
                    "name": f"specgen→{tname}",
                    "split": "specgen",
                    "source": source,
                    "target": tdata,
                    "config": rich_config,
                    "richness": 1.0,
                }
            )
    return edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-specgen", action="store_true")
    parser.add_argument("--skip-ocx24", action="store_true")
    parser.add_argument("--skip-seccm", action="store_true")
    parser.add_argument("--alloy-epochs", type=int, default=100)
    parser.add_argument("--rich-epochs", type=int, default=40)
    parser.add_argument(
        "--out", default=str(RESULTS_DIR / "opd_router_real_states.json")
    )
    args = parser.parse_args()

    device = torch.device("cpu")
    set_deterministic(SEED)
    t0 = time.time()

    edges = build_edges(args)
    print(f"\n{len(edges)} directed edges for router-state extraction\n", flush=True)

    rows = []
    for edge in edges:
        name, source, target = edge["name"], edge["source"], edge["target"]
        epochs = args.rich_epochs if edge["richness"] > 0 else args.alloy_epochs
        cfg = TrainingConfig(
            seed=SEED,
            epochs=epochs,
            patience=20,
            batch_size=32,
            learning_rate=8e-4,
            rank_weight=0.15,
            nll_weight=0.10,
        )
        print(
            f"=== {name} (src_n={len(source)}, tgt_n={len(target)}, epochs={epochs}) ===",
            flush=True,
        )

        pair = train_expert_pair(source, edge["config"], cfg, device=device)
        src_fit = float(pair.standard_report["validation_metrics"]["spearman"])

        # Zero-shot routing states; no target labels are touched here.
        router = ExpertRouter(
            pair.standard,
            pair.mhar,
            pair.standard_calibrator,
            pair.mhar_calibrator,
            strategy="domain_preferring",
        )
        diagnostics = router.route(
            target,
            pair.normalizer,
            device=device,
        )
        geo = edge_geometry(source, target)

        # Predictive uncertainty is on the target's raw property scale.  Only
        # within-edge Standard/MHAR comparisons are meaningful.  Disagreement
        # is normalized by their pooled predictive uncertainty.
        std_std = float(np.mean(diagnostics.standard_std))
        mhar_std = float(np.mean(diagnostics.mhar_std))
        disagreement = float(np.mean(diagnostics.disagreement))
        standard_domain_share = float(np.mean(1.0 - diagnostics.domain_distance_ratio))
        support = geo["coverage"]

        state = {
            "task_kind": "catalyst_ranking",
            "source_sample_count": len(source),
            "target_candidate_count": len(target),
            "source_validation_spearman": round(src_fit, 4),
            "curve_available": bool(edge["config"].use_curve),
            "surface_available": bool(edge["config"].use_surface),
            "condition_observed_fraction": round(_condition_fraction(target), 4),
            "standard_predictive_std": round(std_std, 4),
            "mhar_predictive_std": round(mhar_std, 4),
            "normalized_expert_disagreement": round(disagreement, 4),
            "standard_domain_share": round(standard_domain_share, 4),
            "composition_support": round(support, 4),
        }

        # Evaluation-only payload (never prompted).
        y_true = targets_array(target)
        m_std = metrics(y_true, diagnostics.standard_mean)
        m_mhar = metrics(y_true, diagnostics.mhar_mean)
        ens = (diagnostics.standard_mean + diagnostics.mhar_mean) / 2.0
        m_ens = metrics(y_true, ens)
        oracle = max(
            (
                ("standard", m_std["spearman"]),
                ("mhar", m_mhar["spearman"]),
                ("ensemble", m_ens["spearman"]),
            ),
            key=lambda kv: kv[1],
        )[0]

        rows.append(
            {
                "example_id": name,
                "split_group": edge["split"],
                "state": state,
                "evaluation": {
                    "standard_spearman": round(m_std["spearman"], 4),
                    "mhar_spearman": round(m_mhar["spearman"], 4),
                    "ensemble_spearman": round(m_ens["spearman"], 4),
                    "oracle_expert": oracle,
                },
            }
        )
        print(
            f"  src_fit={src_fit:.3f} disagree={disagreement:.3f} support={support:.3f} | "
            f"std={m_std['spearman']:+.3f} mhar={m_mhar['spearman']:+.3f} "
            f"ens={m_ens['spearman']:+.3f} oracle={oracle}",
            flush=True,
        )

    payload = {
        "design": "opd-router-real-states-v1",
        "seed": SEED,
        "wall_time_s": round(time.time() - t0, 1),
        "rows": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1))

    jsonl = out.with_suffix(".jsonl")
    with jsonl.open("w") as fh:
        for row in rows:
            fh.write(
                json.dumps(
                    {
                        "example_id": row["example_id"],
                        "split_group": row["split_group"],
                        "state": row["state"],
                    }
                )
                + "\n"
            )
    print(f"\nWrote {out} and {jsonl}")


if __name__ == "__main__":
    main()
