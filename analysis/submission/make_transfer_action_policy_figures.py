#!/usr/bin/env python3
"""Draw the transfer-timing and synthesis-route/bridge figures.

Figure contract
---------------
Figure 5 conclusion: transfer is used now only at the highest endpoint whose
frozen recipient evidence is positive; the same contract can withhold.
Archetype: quantitative grid. Hero evidence: endpoint-specific confidence
intervals. Validation: recipient-specific action and support annotations.

Figure 6 conclusion: the current synthesis data cannot identify a route, and a
bridge experiment is justified only after route-resolved candidate metadata are
complete and the endpoint remains decision-ambiguous.
Archetype: schematic-led composite. Hero evidence: fail-closed decision flow.
Validation: current solid-synthesis readiness checklist and record counts.

Backend: Python/matplotlib exclusively. Output: editable SVG and PDF plus
450-dpi PNG and 600-dpi TIFF at 183-mm journal width.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["svg.hashsalt"] = "transfer-action-policy-v1"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["font.size"] = 6.2
plt.rcParams["axes.linewidth"] = 0.7
plt.rcParams["axes.spines.right"] = False
plt.rcParams["axes.spines.top"] = False
plt.rcParams["legend.frameon"] = False


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "analysis" / "results"
OUT = ROOT / "analysis" / "figures" / "transfer_action_policy"
SOURCE = ROOT / "analysis" / "figures" / "source_data"

MM = 1 / 25.4
WHITE = "#FFFFFF"
INK = "#272727"
MID = "#6F7480"
LIGHT = "#E7E9ED"
NAVY = "#0F4D92"
TEAL = "#2E8B83"
PALE_TEAL = "#DDF1ED"
PURPLE = "#7C6CCF"
PALE_PURPLE = "#E9E5F7"
CORAL = "#B64342"
PALE_CORAL = "#F6DAD7"
AMBER = "#C47A15"
PALE_AMBER = "#F5E7CB"
PALE_GREY = "#F3F4F6"


def _box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    *,
    face: str = WHITE,
    edge: str = INK,
    color: str = INK,
    size: float = 5.4,
    weight: str = "normal",
    radius: float = 0.025,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        facecolor=face,
        edgecolor=edge,
        linewidth=0.8,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=color,
        fontweight=weight,
        linespacing=1.05,
    )


def _arrow(ax, start, end, *, color=INK, style="-|>", connectionstyle=None) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=8,
            linewidth=0.8,
            color=color,
            connectionstyle=connectionstyle,
        )
    )


def _panel_label(ax, label: str) -> None:
    ax.text(
        -0.08,
        1.05,
        label,
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=INK,
    )


def _clean_axis(ax) -> None:
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=LIGHT, linewidth=0.55, zorder=0)


def _save(fig, stem: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = stem.with_suffix(".svg")
    fig.savefig(
        svg_path, facecolor=WHITE, metadata={"Date": None}
    )
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text().splitlines()) + "\n",
        encoding="utf-8",
    )
    fig.savefig(
        stem.with_suffix(".pdf"),
        facecolor=WHITE,
        metadata={"CreationDate": None, "ModDate": None},
    )
    fig.savefig(
        stem.with_suffix(".png"),
        dpi=450,
        facecolor=WHITE,
        metadata={"Software": "matplotlib"},
    )
    fig.savefig(
        stem.with_suffix(".tiff"),
        dpi=600,
        facecolor=WHITE,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def _load() -> tuple[dict, dict]:
    cards = json.loads(
        (RESULTS / "transferability_evidence_cards.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (RESULTS / "transfer_action_policy_summary.json").read_text(encoding="utf-8")
    )
    return cards, policy


def _write_figure5_source(cards: dict) -> list[dict]:
    by_name = {card["recipient"]: card for card in cards["cards"]}
    li = by_name["LiAsF6"]["absolute_endpoint"]
    sol = by_name["SolventSeg"]["rank_endpoint"]
    fin = by_name["FINALES"]["rank_endpoint"]
    rows = [
        {
            "recipient": "LiAsF6",
            "metric": "relative_log_rmse_gain_percent",
            "estimate": 100 * li["relative_log_rmse_gain_vs_state_only"],
            "ci_low": 100 * li["relative_log_rmse_gain_vs_state_only_ci95"]["low"],
            "ci_high": 100 * li["relative_log_rmse_gain_vs_state_only_ci95"]["high"],
            "action": "PREDICT",
        },
        {
            "recipient": "SolventSeg",
            "metric": "source_minus_recipient_spearman",
            "estimate": sol["source_minus_recipient_spearman"],
            "ci_low": sol["source_minus_recipient_spearman_ci95"]["low"],
            "ci_high": sol["source_minus_recipient_spearman_ci95"]["high"],
            "action": "RANK",
        },
        {
            "recipient": "FINALES",
            "metric": "donor_minus_recipient_concordance",
            "estimate": fin["donor_minus_recipient_concordance"],
            "ci_low": fin["donor_minus_recipient_concordance_ci95"]["low"],
            "ci_high": fin["donor_minus_recipient_concordance_ci95"]["high"],
            "action": "WITHHOLD",
        },
    ]
    SOURCE.mkdir(parents=True, exist_ok=True)
    path = SOURCE / "figure5_transfer_action_map.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=rows[0].keys(), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _figure5_support_notes(cards: dict) -> tuple[str, str, str]:
    by_name = {card["recipient"]: card for card in cards["cards"]}
    li_card = by_name["LiAsF6"]
    solvent_card = by_name["SolventSeg"]
    finales_card = by_name["FINALES"]
    li_support = li_card["data_support"]
    li_absolute = li_card["absolute_endpoint"]
    solvent_absolute = solvent_card["absolute_endpoint"]
    solvent_rank = solvent_card["rank_endpoint"]
    finales_support = finales_card["data_support"]
    finales_rank = finales_card["rank_endpoint"]
    return (
        "State coverage "
        f"{100 * min(li_support['temperature_inside_source_range_fraction'], li_support['concentration_inside_source_range_fraction']):.0f}%\n"
        f"Full-relation support {100 * li_support['full_representation_inside_donor_q95_fraction']:.1f}%\n"
        "Chemistry-shuffled control "
        + (
            "passed"
            if li_absolute[
                "relative_log_rmse_gain_vs_chemistry_permuted_ci95"
            ]["low"]
            > 0
            else "failed"
        ),
        f"Absolute RMSE gain {100 * solvent_absolute['relative_log_rmse_gain_vs_state_only']:.1f}%\n"
        f"Rank permutation Holm P = {solvent_rank['holm_adjusted_permutation_p']:.5f}\n"
        "Top-quartile precision "
        f"{solvent_rank['source_top_quartile_precision']:.3f} vs "
        f"{solvent_rank['recipient_top_quartile_precision']:.3f}",
        f"{finales_support['eligible_temperature_matched_pairs']} eligible pairs · "
        f"P = {finales_rank['permutation_p']:.3f}\n"
        "Precision "
        f"{finales_rank['donor_top_quartile_precision']:.2f} vs "
        f"{finales_rank['recipient_top_quartile_precision']:.2f}\n"
        "Regret "
        f"{finales_rank['donor_normalized_regret']:.3f} vs "
        f"{finales_rank['recipient_normalized_regret']:.3f}",
    )


def make_figure5(cards: dict) -> None:
    rows = _write_figure5_source(cards)
    fig, axes = plt.subplots(1, 3, figsize=(183 * MM, 98 * MM))
    fig.subplots_adjust(left=0.065, right=0.985, top=0.77, bottom=0.34, wspace=0.39)
    colors = (TEAL, PURPLE, CORAL)
    faces = (PALE_TEAL, PALE_PURPLE, PALE_CORAL)
    titles = (
        "Absolute-value transfer",
        "Candidate-order transfer",
        "Frozen second recipient",
    )
    support_notes = _figure5_support_notes(cards)
    xlims = ((0, 36), (-0.05, 0.65), (-0.36, 0.16))
    xticks = ((0, 10, 20, 30), (0, 0.2, 0.4, 0.6), (-0.3, -0.15, 0, 0.15))
    xlabels = (
        "Relative log-RMSE gain (%)",
        "Source − recipient Spearman",
        "Donor − recipient concordance",
    )

    for idx, (ax, row, color, face) in enumerate(zip(axes, rows, colors, faces)):
        _panel_label(ax, chr(ord("a") + idx))
        ax.set_title(titles[idx], loc="left", fontsize=7.1, fontweight="bold", pad=8)
        ax.axvline(0, color=MID, linestyle=(0, (2.5, 2.2)), linewidth=0.75, zorder=1)
        ax.plot(
            [row["ci_low"], row["ci_high"]],
            [0, 0],
            color=color,
            linewidth=2.4,
            solid_capstyle="round",
            zorder=3,
        )
        ax.scatter(
            row["estimate"],
            0,
            s=48,
            marker="D",
            color=color,
            edgecolor=WHITE,
            linewidth=0.6,
            zorder=4,
        )
        ax.set_xlim(*xlims[idx])
        ax.set_xticks(xticks[idx])
        ax.set_ylim(-0.7, 0.8)
        ax.set_yticks([])
        ax.set_xlabel(xlabels[idx], labelpad=4)
        _clean_axis(ax)
        fmt = ".1f" if idx == 0 else ".3f"
        value = (
            f"{row['estimate']:{fmt}}  "
            f"[{row['ci_low']:{fmt}}, {row['ci_high']:{fmt}}]"
        )
        ax.text(
            row["estimate"],
            0.19,
            value,
            ha="center",
            va="bottom",
            fontsize=5.7,
            color=color,
            fontweight="bold",
        )
        ax.text(
            0.5,
            0.12,
            row["action"],
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=6.1,
            color=color,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.42,rounding_size=0.18",
                "facecolor": face,
                "edgecolor": color,
                "linewidth": 0.9,
            },
            clip_on=False,
        )
        ax.text(
            0.5,
            -0.31,
            support_notes[idx],
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=4.75,
            color=MID,
            linespacing=1.16,
            clip_on=False,
        )

    fig.text(
        0.065,
        0.955,
        "Transfer is used only at the highest resolution supported in the recipient",
        ha="left",
        va="top",
        fontsize=9.0,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        0.065,
        0.885,
        "Points are estimates and horizontal lines are the reported 95% intervals; positive values favour transfer.",
        ha="left",
        va="top",
        fontsize=5.5,
        color=MID,
    )
    _save(fig, OUT / "figure5_transfer_action_map")


def _write_figure6_source(policy: dict) -> list[dict]:
    readiness = policy["synthesis_route_readiness"]
    rows = readiness["checklist"]
    SOURCE.mkdir(parents=True, exist_ok=True)
    path = SOURCE / "figure6_route_bridge_readiness.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("requirement", "status"),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def make_figure6(policy: dict) -> None:
    readiness = policy["synthesis_route_readiness"]
    checklist = _write_figure6_source(policy)
    fig = plt.figure(figsize=(183 * MM, 116 * MM))
    fig.patch.set_facecolor(WHITE)
    ax_a = fig.add_axes([0.055, 0.11, 0.57, 0.70])
    ax_b = fig.add_axes([0.68, 0.30, 0.285, 0.51])
    ax_c = fig.add_axes([0.68, 0.09, 0.285, 0.14])
    for ax in (ax_a, ax_b, ax_c):
        ax.set_axis_off()

    _panel_label(ax_a, "a")
    ax_a.text(0.0, 1.02, "Fail-closed experimental action policy", transform=ax_a.transAxes, fontsize=7.2, fontweight="bold", color=INK)
    ax_a.set_xlim(0, 1)
    ax_a.set_ylim(0, 1)

    _box(ax_a, 0.02, 0.75, 0.25, 0.13, "Candidate-available\nroute metadata", face=PALE_GREY, edge=NAVY, color=NAVY, size=5.5, weight="bold")
    _box(ax_a, 0.38, 0.75, 0.24, 0.13, "Feasibility · safety\nprocess support", face=PALE_GREY, edge=NAVY, color=NAVY, size=5.5, weight="bold")
    _box(ax_a, 0.73, 0.75, 0.24, 0.13, "Endpoint interval +\nmatched falsifiers", face=PALE_GREY, edge=NAVY, color=NAVY, size=5.5, weight="bold")
    _arrow(ax_a, (0.27, 0.815), (0.38, 0.815), color=NAVY)
    _arrow(ax_a, (0.62, 0.815), (0.73, 0.815), color=NAVY)

    _box(ax_a, 0.02, 0.48, 0.25, 0.14, "INCOMPLETE\nroute labels or target table", face=PALE_AMBER, edge=AMBER, color=AMBER, size=5.3, weight="bold")
    _box(ax_a, 0.38, 0.49, 0.24, 0.12, "DATA RECOVERY", face=PALE_AMBER, edge=AMBER, color=AMBER, size=6.0, weight="bold")
    _arrow(ax_a, (0.145, 0.75), (0.145, 0.62), color=AMBER)
    _arrow(ax_a, (0.27, 0.55), (0.38, 0.55), color=AMBER)
    ax_a.text(0.50, 0.455, "Current solid-synthesis direction", ha="center", va="top", fontsize=4.8, color=AMBER)

    _box(ax_a, 0.02, 0.20, 0.25, 0.14, "SUPPORTED\nlower bound clears gate", face=PALE_TEAL, edge=TEAL, color=TEAL, size=5.3, weight="bold")
    _box(ax_a, 0.38, 0.21, 0.24, 0.12, "TRANSFER NOW", face=PALE_TEAL, edge=TEAL, color=TEAL, size=6.0, weight="bold")
    _arrow(ax_a, (0.78, 0.75), (0.27, 0.34), color=TEAL, connectionstyle="arc3,rad=0.12")
    _arrow(ax_a, (0.27, 0.27), (0.38, 0.27), color=TEAL)

    _box(ax_a, 0.72, 0.43, 0.25, 0.14, "AMBIGUOUS\ninterval crosses gate", face=PALE_PURPLE, edge=PURPLE, color=PURPLE, size=5.3, weight="bold")
    _box(ax_a, 0.72, 0.20, 0.25, 0.14, "BRIDGE EXPERIMENT\nonly if EVSI > cost", face=PALE_PURPLE, edge=PURPLE, color=PURPLE, size=5.5, weight="bold")
    _arrow(ax_a, (0.85, 0.75), (0.85, 0.57), color=PURPLE)
    _arrow(ax_a, (0.845, 0.43), (0.845, 0.34), color=PURPLE)
    _arrow(ax_a, (0.97, 0.27), (0.96, 0.75), color=PURPLE, connectionstyle="arc3,rad=-0.28")
    ax_a.text(0.84, 0.145, "paired contrast updates the frozen gate", fontsize=4.55, color=PURPLE, ha="center")

    _box(ax_a, 0.38, 0.02, 0.24, 0.11, "WITHHOLD", face=PALE_CORAL, edge=CORAL, color=CORAL, size=6.0, weight="bold")
    ax_a.text(0.50, 0.0, "hard negative · falsifier failure · no feasible route", ha="center", va="top", fontsize=4.6, color=CORAL)

    _panel_label(ax_b, "b")
    ax_b.text(0.0, 1.02, "Current route-selection readiness", transform=ax_b.transAxes, fontsize=7.2, fontweight="bold", color=INK)
    ax_b.set_xlim(0, 1)
    ax_b.set_ylim(-0.4, len(checklist) - 0.2)
    for idx, item in enumerate(reversed(checklist)):
        y = idx
        available = item["status"] == "available"
        color = TEAL if available else CORAL
        marker = "YES" if available else "NO"
        ax_b.axhline(y - 0.43, color=LIGHT, linewidth=0.45)
        ax_b.text(0.02, y, item["requirement"], ha="left", va="center", fontsize=4.65, color=INK)
        ax_b.text(0.96, y, marker, ha="right", va="center", fontsize=4.8, color=color, fontweight="bold")
    ax_b.text(0.02, len(checklist) - 0.35, "Requirement", fontsize=4.6, color=MID, fontweight="bold")
    ax_b.text(0.96, len(checklist) - 0.35, "Ready", fontsize=4.6, color=MID, fontweight="bold", ha="right")

    _panel_label(ax_c, "c")
    donor_reactions = readiness["record_counts"]["donor_reactions"]
    recipient_attempts = readiness["record_counts"]["recipient_reported_attempts"]
    _box(ax_c, 0.0, 0.0, 1.0, 1.0, f"ROUTE CHOICE: NOT EVALUABLE\n{donor_reactions:,} donor reactions · {recipient_attempts:,} reported target attempts\ncomplete attempt table and route alternatives not verified", face=PALE_AMBER, edge=AMBER, color=AMBER, size=5.2, weight="bold", radius=0.04)

    fig.text(0.055, 0.965, "Bridge experiments are conditional actions, not a substitute for missing route data", fontsize=9.0, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.055, 0.910, "The current synthesis evidence supports data recovery before route selection; no specific synthesis route is nominated.", fontsize=5.5, color=MID, ha="left", va="top")
    _save(fig, OUT / "figure6_route_bridge_readiness")


def main() -> None:
    cards, policy = _load()
    make_figure5(cards)
    make_figure6(policy)
    contract = """# Transfer-action figure contract

## Figure 5

- Core conclusion: transfer is used only at the highest endpoint supported by frozen recipient evidence.
- Archetype: quantitative grid.
- Source data: `analysis/figures/source_data/figure5_transfer_action_map.csv`.
- Statistics: formulation-grouped 95% bootstrap interval for LiAsF6; anchor-selection interval for SolventSeg; pair/bootstrap interval for FINALES.

## Figure 6

- Core conclusion: current synthesis data do not identify a route; bridge experiments become actionable only after route-resolved metadata are complete and endpoint evidence remains ambiguous.
- Archetype: schematic-led composite.
- Source data: `analysis/figures/source_data/figure6_route_bridge_readiness.csv` and the frozen synthesis-readiness audit.
- Integrity boundary: schematic actions are policy states; no unobserved route effect is plotted.
"""
    (OUT / "FIGURE_CONTRACT.md").write_text(contract, encoding="utf-8")
    print(OUT / "figure5_transfer_action_map")
    print(OUT / "figure6_route_bridge_readiness")


if __name__ == "__main__":
    main()
