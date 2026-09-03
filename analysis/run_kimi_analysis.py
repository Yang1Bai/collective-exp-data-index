#!/usr/bin/env python3
"""Chemical reasoning analysis using Kimi K3 on benchmark results.

Two parts:
1. Meta-reasoning: why do certain methods work on certain directions?
2. Chemical gap analysis: what's chemically different between domains?
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from catalyst_attention.kimi_chemical import (
    analyze_transfer_with_kimi,
    generate_chemical_reasoning,
    composition_rich_features,
)

RESULTS_DIR = ROOT / "analysis" / "results"


def build_results_summary() -> str:
    """Build a text summary of all experimental results for Kimi analysis."""
    lines = [
        "=== COMPREHENSIVE BENCHMARK RESULTS (27 model variants) ===",
        "",
        "SpecGen zero-shot transfer (Spearman):",
        "  A: ExtraTrees=0.553 Standard=0.542 Contrastive=0.545 Chemical=0.541",
        "  B: ExtraTrees=0.611 Standard=0.626 Contrastive=0.635 Chemical=0.729",
        "  C: ExtraTrees=0.267 Standard=0.298 Contrastive=0.239 Chemical=0.252",
        "  D: ExtraTrees=0.747 Standard=0.762 Contrastive=0.763 Chemical=0.729",
        "",
        "Alloy family zero-shot transfer (Spearman, yield strength):",
        "  Steels→MPEA:      ET=0.266  Standard=0.188  Chemical=0.088  Contrastive=0.076",
        "  Steels→BIRDSHOT:  ET=-0.352 Standard=0.539  Chemical=0.596  Contrastive=-0.478",
        "  MPEA→Steels:      ET=0.170  Standard=-0.108 Chemical=-0.088 Contrastive=-0.075",
        "  MPEA→BIRDSHOT:    ET=0.436  Standard=-0.411 Chemical=-0.426 Contrastive=-0.422",
        "",
        "Key observations:",
        "  - ExtraTrees wins 4/6 composition-only alloy directions",
        "  - Standard Transformer wins Steels→BIRDSHOT by +0.89 over ET",
        "  - Chemical-augmented wins Steels→BIRDSHOT (0.596 vs 0.539)",
        "  - Contrastive wins only on SpecGen D (0.763 vs 0.762)",
        "  - SpecGen C (Fe-doped) is unsolvable by all methods (max 0.298)",
        "  - No method is universally best",
        "",
        "Method-specific findings (21 variants from earlier work):",
        "  - Delta-MHAR: complementary expert, best on SpecGen C (0.298) and OCx24 U→V (0.618)",
        "  - KL-Shampoo: all variants fail (-0.011 to -0.375)",
        "  - Adversarial: catastrophic failure with target samples (-0.311)",
        "  - CORAL: helps SpecGen (4/4 positive) but destroys OCx24 (-0.262)",
        "  - Pairwise encoder: completely broken (source Spearman=0.157)",
        "  - Latent diffusion: collapses to zero (64-dim space, 462 samples)",
        "  - k-NN interpolation: close to Contrastive but no training needed",
        "  - Expert router: implemented, awaiting sealed programme",
    ]
    return "\n".join(lines)


def main():
    t0 = time.time()

    # Build summary for Kimi analysis.
    summary = build_results_summary()
    print(summary)
    print()

    # ---- Part 1: Meta-reasoning with Kimi K3 ----
    print("=" * 70)
    print("  KIMI K3 META-REASONING ANALYSIS")
    print("=" * 70)

    analysis = analyze_transfer_with_kimi(summary)
    print(analysis)

    # ---- Part 2: Chemical gap analysis ----
    print("\n" + "=" * 70)
    print("  KIMI K3 CHEMICAL GAP ANALYSIS")
    print("=" * 70)

    # Steels → BIRDSHOT (the winning direction for Chemical-augmented).
    steel_comps = [
        "Fe0.62C0.001Mn0.001Si0.001Cr0.000Ni0.192Mo0.018Co0.146Al0.003Ti0.019",
        "Fe0.62C0.009Mn0.000Si0.000Cr0.147Ni0.000Mo0.018Co0.188W0.007Al0.001",
        "Fe0.63Mn0.000Si0.000Cr0.094Ni0.129Mo0.005Co0.132Al0.008Ti0.007",
    ]
    birdshot_comps = [
        "Co45Cr10Fe20Ni15V10",
        "Co30Cr10Fe5Ni45V10",
        "Co15Cr5Fe45Ni30V5",
        "Al4Co12Cr8Fe8Mn8Ni56V4",
    ]

    gap_analysis = generate_chemical_reasoning(
        steel_comps + birdshot_comps,
        target_property="yield strength",
        source_domain="matbench-steels (Fe-based, 13 elements, yield 241-2487 MPa)",
        target_domain="BIRDSHOT HEA (Co-Cr-Fe-Ni-V, high-entropy, yield 171-650 MPa)",
    )
    print(gap_analysis)

    # Save.
    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "results_summary": summary,
        "meta_reasoning": analysis,
        "chemical_gap_analysis": gap_analysis,
        "wall_time_s": round(time.time() - t0, 1),
    }
    out_path = RESULTS_DIR / "kimi_analysis.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"\n  Analysis → {out_path}")


if __name__ == "__main__":
    main()
