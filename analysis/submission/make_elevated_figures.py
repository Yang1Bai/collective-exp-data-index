#!/usr/bin/env python3
"""Draft figures for the elevated manuscript narrative.

Generates 5 publication-style draft figures (PNG @200 dpi, SVG) into
analysis/figures/elevated/ from the frozen figure source data and verified
summary JSONs. Drafts only: annotations/panels will be refined later.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "analysis" / "results"
FIG = ROOT / "analysis" / "figures" / "elevated"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 200,
})

NAVY = "#1B3A5C"
TEAL = "#2A9D8F"
ORANGE = "#E76F51"
GRAY = "#8A8A8A"
GOLD = "#E9C46A"


def save(fig, name: str):
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def style_ax(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---------------------------------------------------------------- Figure 1
def fig1():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.9), gridspec_kw={"width_ratios": [1.5, 1, 1]})
    ax = axes[0]
    ax.set_axis_off()
    # three donor programmes -> relation gate -> recipient
    donors = [("Source A\n(conductivity)", 0.20, 0.62, TEAL),
              ("Source B\n(conductivity)", 0.20, 0.32, TEAL),
              ("Source C\n(catalysis)", 0.20, 0.12, GRAY)]
    for label, x, y, c in donors:
        ax.add_patch(plt.Rectangle((x, y), 0.16, 0.16, facecolor=c, edgecolor="none", alpha=0.85))
        ax.text(x + 0.08, y + 0.08, label, ha="center", va="center", color="white", fontsize=8, linespacing=1.2)
    # relation arrows (narrow object crossing)
    for _, x, y, c in donors:
        ax.annotate("", xy=(0.52, 0.40), xytext=(x + 0.17, y + 0.08),
                    arrowprops=dict(arrowstyle="-", color=GRAY, lw=1.0))
    ax.add_patch(FancyBboxPatch((0.52, 0.30), 0.17, 0.22, boxstyle="round,pad=0.02",
                                    facecolor="white", edgecolor=NAVY, lw=1.6))
    ax.text(0.605, 0.415, "qualify\nrelation\nfalsify", ha="center", va="center", fontsize=8, color=NAVY, linespacing=1.3)
    ax.annotate("", xy=(0.74, 0.40), xytext=(0.70, 0.40),
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=1.6))
    ax.add_patch(plt.Rectangle((0.74, 0.26), 0.18, 0.28, facecolor="none", edgecolor=NAVY, lw=1.4))
    ax.text(0.83, 0.40, "recipient\n(anchors + OOD)", ha="center", va="center", fontsize=8, color=NAVY, linespacing=1.3)
    ax.annotate("", xy=(0.955, 0.62), xytext=(0.955, 0.40),
                arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.2))
    ax.text(0.985, 0.62, "abstain", ha="center", va="center", rotation=90, fontsize=7.5, color=GRAY)
    ax.text(0.05, 0.96, "a  The wrong object (database / model / feature) does not cross", fontsize=9.5, color=NAVY)

    # panel b: three decision-level results
    ax = axes[1]
    cats = ["Predict\nLiAsF6", "Rank\nSolventSeg", "Generic\n0/40"]
    vals = [27.4, 0.910, 0.0]
    cols = [TEAL, TEAL, GRAY]
    ax.bar(cats, vals, color=cols, alpha=0.9, edgecolor="none")
    for x, v in zip(range(3), vals):
        ax.text(x, v + (0.5 if v < 5 else 0.01), f"{v}", ha="center", fontsize=9, color=NAVY)
    ax.set_ylabel("portable signal")
    ax.set_ylim(0, 32)
    ax.set_title("b  What survives the boundary", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[2]
    cats2 = ["predict", "rank", "abstain"]
    n = [1, 1, 1]
    cols2 = [TEAL, GOLD, GRAY]
    ax.bar(cats2, n, color=cols2, edgecolor="white")
    ax.set_ylabel("admitted routes")
    ax.set_ylim(0, 1.6)
    ax.set_title("c  The borrowing map action set", fontsize=9.5, color=NAVY)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "figure1_elevated_draft")


# ---------------------------------------------------------------- Figure 2
def fig2():
    df = pd.read_csv(RESULTS / "figure_main_panel_a.csv")
    borg = df[df.dataset_label == "borg"]
    bird = df[df.dataset_label == "birdshot"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), gridspec_kw={"width_ratios": [1.3, 1, 1]})

    ax = axes[0]
    ax.scatter(borg.YS_MPa, borg.UTS_MPa, s=8, alpha=0.7, color=TEAL, label="Borg (in-domain, R²=0.790)")
    ax.scatter(bird.YS_MPa, bird.UTS_MPa, s=8, alpha=0.7, color=ORANGE, label="BIRDSHOT (independent)")
    b = np.polyfit(borg.YS_MPa, borg.UTS_MPa, 1)
    xs = np.linspace(borg.YS_MPa.min(), borg.YS_MPa.max(), 100)
    ax.plot(xs, np.polyval(b, xs), color=NAVY, lw=1.4)
    ax.text(0.05, 0.94, "Borg coefficient on BIRDSHOT: R² = −3.006", transform=ax.transAxes, fontsize=9, color=ORANGE)
    ax.set_xlabel("yield strength (MPa)"); ax.set_ylabel("ultimate strength (MPa)")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.set_title("a  Provenance breaks an unchanged coefficient", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[1]
    edges = pd.read_csv(RESULTS / "figure_multi_target_ood_panel_b.csv")
    edges = edges.sort_values("gain_ood_mean")
    cols = [ORANGE if e < 0 else GRAY for e in edges.gain_ood_mean]
    ax.barh(range(len(edges)), edges.gain_ood_mean * 100, color=cols, alpha=0.85)
    for i, r in edges.iterrows():
        ax.plot([r.gain_ood_ci_lo * 100, r.gain_ood_ci_hi * 100], [i, i], color=NAVY, lw=0.7)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("mean far-OOD RMSE change (%)")
    ax.set_yticks([])
    ax.set_title("b  40 donor-feature edges: none passes the full gate", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[2]
    cat = pd.DataFrame({
        "edge class": ["within-database", "cross-database", "complete pass"],
        "count": [37, 3, 0],
    })
    ax.bar(cat["edge class"], cat["count"], color=[GRAY, GRAY, ORANGE], edgecolor="white")
    ax.set_ylabel("edges")
    for i, v in enumerate(cat["count"]):
        ax.text(i, v + 0.3, str(v), ha="center", fontsize=9)
    ax.set_ylim(0, 42)
    ax.set_title("c  The complete-gate audit", fontsize=9.5, color=NAVY)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "figure2_elevated_draft")


# ---------------------------------------------------------------- Figure 3
def fig3():
    pred = pd.read_csv(RESULTS / "bamboomixer_LiAsF6_only_external_predictions.csv")
    boot = pd.read_csv(RESULTS / "bamboomixer_LiAsF6_only_group_bootstrap.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

    ax = axes[0]
    ax.scatter(pred.y_conductivity, pred.prediction_conductivity, s=4, alpha=0.35, color=TEAL)
    lim = [0, pred[["y_conductivity", "prediction_conductivity"]].values.max() * 1.05]
    ax.plot(lim, lim, color=NAVY, lw=1.2, ls="--")
    ax.set_xlabel("measured σ (mS/cm)"); ax.set_ylabel("borrowed prediction σ (mS/cm)")
    ax.text(0.05, 0.92, "raw R² = 0.607, ρ = 0.864\nlog-RMSE −27.4% vs state-only", transform=ax.transAxes, fontsize=9, color=NAVY)
    ax.set_title("a  LiAsF6 external prediction (1,660 rows, 156 formulations)", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[1]
    order = ["state_only", "chemistry_permuted", "without_LiPF6", "LiPF6_only"]
    labels = ["vs state-only", "vs chemistry-permuted", "drop LiPF6", "LiPF6 only"]
    means, los, his = [], [], []
    for k in order:
        sub = boot[boot.comparator == k]
        means.append(sub.relative_log_rmse_gain.mean() * 100)
        los.append(sub.relative_log_rmse_gain.quantile(0.025) * 100)
        his.append(sub.relative_log_rmse_gain.quantile(0.975) * 100)
    x = np.arange(len(order))
    ax.bar(x, means, color=[TEAL, TEAL, GOLD, GRAY], alpha=0.9, yerr=[np.array(means) - np.array(los), np.array(his) - np.array(means)],
           capsize=4, error_kw=dict(lw=1.0))
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("relative log-RMSE gain (%)")
    ax.set_title("b  Falsifier contrasts (grouped bootstrap)", fontsize=9.5, color=NAVY)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "figure3_elevated_draft")


# ---------------------------------------------------------------- Figure 4
def fig4():
    src = pd.read_csv(RESULTS / "specgen_derivative_oer_figure_source_data.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))

    ax = axes[0]
    panel_b = src[src.panel == "b"]
    order = ["A", "B", "C", "D"]
    zero = {"A": 0.552, "B": 0.610, "C": 0.259, "D": 0.748}
    one = {d["target"]: d["estimate"] for _, d in panel_b[panel_b.measure == "composition_only_donor"].iterrows()}
    r2 = {d["target"]: d["estimate"] for _, d in panel_b[panel_b.measure == "static_spectral_donor"].iterrows()}
    x = np.arange(len(order)); w = 0.36
    ax.bar(x - w / 2, [r2[o] for o in order], w, color=GRAY, alpha=0.85, label="static spectral donor")
    ax.bar(x + w / 2, [one[o] for o in order], w, color=TEAL, alpha=0.9, label="composition donor (zero-label)")
    ax.axhline(0.30, color=NAVY, lw=1.0, ls="--")
    ax.text(3.35, 0.32, "practical gate 0.30", fontsize=8, color=NAVY, ha="right")
    ax.set_xticks(x); ax.set_xticklabels([f"System {o}" for o in order])
    ax.set_ylabel("zero-label Spearman ρ")
    ax.set_ylim(-0.3, 0.95)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("a  Zero-label ranking across four derivative systems", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[1]
    panel_c = src[src.panel == "c"]
    r2_ = {d["target"]: d["estimate"] for _, d in panel_c[panel_c.measure == "relative_rmse_gain"].iterrows()}
    sp = {d["target"]: d["estimate"] for _, d in panel_c[panel_c.measure == "spearman_gain"].iterrows()}
    x = np.arange(len(order)); w = 0.36
    ax.bar(x - w / 2, [r2_[o] * 100 for o in order], w, color=GOLD, alpha=0.9, label="relative RMSE gain (%)")
    ax.bar(x + w / 2, [sp[o] for o in order], w, color=NAVY, alpha=0.75, label="Spearman gain")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels([f"System {o}" for o in order])
    ax.set_ylabel("gain vs target-only (5 anchors)")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.set_title("b  Five-anchor gains: predict / rank-only / harm", fontsize=9.5, color=NAVY)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "figure4_elevated_draft")


# ---------------------------------------------------------------- Figure 5
def fig5():
    macro = json.loads((RESULTS / "bamboomixer_cross_database_interaction_summary.json").read_text())["solventseg"]["five_anchor_macro"]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0))

    ax = axes[0]
    donors = {k: v["spearman"] for k, v in macro.items() if v.get("spearman") == v.get("spearman")}
    order = ["target_only_ridge", "calisol_frozen", "kit_frozen", "bamboo_all_frozen",
             "programme_balanced_rank_consensus_frozen", "programme_balanced_portfolio_frozen"]
    labels = ["recipient-only\nridge", "CALiSol", "KIT", "BambooMixer", "rank\nconsensus", "programme-\nbalanced"]
    vals = [donors.get(o, 0) for o in order]
    cols = [GRAY, GRAY, GRAY, GRAY, GOLD, TEAL]
    ax.bar(range(len(order)), vals, color=cols, edgecolor="white")
    ax.axhline(0.537, color=ORANGE, lw=1.2, ls="--")
    ax.text(5.2, 0.55, "strongest recipient-only\nρ = 0.537 (5 labels)", fontsize=8, color=ORANGE, ha="right")
    ax.set_xticks(range(len(order))); ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("zero-label Spearman ρ (5 anchors)")
    ax.set_ylim(0, 1.0)
    ax.set_title("a  Zero-label ranking vs 13 recipient-only models", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[1]
    df = pd.read_csv(RESULTS / "bamboomixer_cross_database_interaction_solventseg_anchor_contrasts.csv")
    df = df[(df.model == "programme_balanced_portfolio_frozen") & (df.comparator == "target_only_ridge")]
    piv = df.groupby("anchor_budget")["spearman_gain"].agg(["mean", lambda x: x.quantile(0.025), lambda x: x.quantile(0.975)]).reset_index()
    piv.columns = ["anchor_budget", "m", "lo", "hi"]
    ax.errorbar(piv.anchor_budget, piv.m, yerr=[piv.m - piv.lo, piv.hi - piv.m], fmt="o-", color=TEAL, capsize=4)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xlabel("recipient anchors (maximin, outcome-free)")
    ax.set_ylabel("Δρ vs target-only ridge")
    ax.set_title("b  Anchor budget sweep (programme-balanced)", fontsize=9.5, color=NAVY)
    style_ax(ax)

    ax = axes[2]
    fin = json.loads((RESULTS / "finales_rank_replication_summary.json").read_text())
    p = fin["primary"]
    vals = [p["donor_concordance"], p["strongest_baseline_concordance"]]
    labels = ["frozen donor", "recipient-only"]
    bars = ax.bar(labels, vals, color=[TEAL, GRAY], edgecolor="white")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=9)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("pairwise concordance")
    ax.set_title("c  Frozen FINALES: abstain\n(Δ = −0.089, p = 0.131)", fontsize=9.5, color=NAVY)
    style_ax(ax)
    fig.tight_layout()
    save(fig, "figure5_elevated_draft")


if __name__ == "__main__":
    fig1(); fig2(); fig3(); fig4(); fig5()
    print("done")
