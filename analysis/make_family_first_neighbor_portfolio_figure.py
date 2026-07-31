"""Make the CCA family-first exploration figure with matplotlib only."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
METRICS = RESULTS / "family_first_neighbor_portfolio_metrics.csv"
SUMMARY = RESULTS / "family_first_neighbor_portfolio_summary.json"
STEM = FIGURES / "family_first_neighbor_portfolio"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.2,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

COLORS = {
    "neutral": "#A8ADB4",
    "novelty": "#D6B55F",
    "wrong": "#CE8F9B",
    "obelix": "#9CB9D5",
    "estm": "#6F9BC3",
    "entity": "#315F8A",
    "family": "#147D73",
    "family_light": "#A7D5CF",
    "ink": "#20262E",
    "muted": "#66717C",
    "panel": "#F4F6F8",
}

POLICIES = [
    "uniform_family_first",
    "composition_novelty_family_first",
    "wrong_source_family_first_consensus",
    "obelix_family_first",
    "estm_family_first",
    "neighbor_entity_consensus",
    "neighbor_family_first_consensus",
]
LABELS = {
    "uniform_family_first": "Uniform",
    "composition_novelty_family_first": "Novelty",
    "wrong_source_family_first_consensus": "Wrong\npair",
    "obelix_family_first": "OBELiX",
    "estm_family_first": "ESTM",
    "neighbor_entity_consensus": "Entity consensus",
    "neighbor_family_first_consensus": "Family-first",
}
BAR_COLORS = {
    "uniform_family_first": COLORS["neutral"],
    "composition_novelty_family_first": COLORS["novelty"],
    "wrong_source_family_first_consensus": COLORS["wrong"],
    "obelix_family_first": COLORS["obelix"],
    "estm_family_first": COLORS["estm"],
    "neighbor_entity_consensus": COLORS["entity"],
    "neighbor_family_first_consensus": COLORS["family"],
}


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08,
        1.06,
        label,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        va="top",
        ha="left",
    )


def rounded_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    subtitle: str,
    facecolor: str,
) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=0.8,
        edgecolor=COLORS["ink"],
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(x + 0.03, y + height * 0.65, title, fontsize=7.5, fontweight="bold")
    ax.text(
        x + 0.03,
        y + height * 0.27,
        subtitle,
        fontsize=6.2,
        color=COLORS["muted"],
        va="center",
    )


def draw_workflow(ax: plt.Axes) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "a")
    rounded_box(ax, (0.01, 0.28), 0.20, 0.45, "Credibility", "leakage audit\n+ wrong-source tests", "#EAF0F5")
    rounded_box(ax, (0.27, 0.28), 0.20, 0.45, "Complementarity", "keep OBELiX and ESTM\nrankings separate", "#E1EDF5")
    rounded_box(ax, (0.53, 0.28), 0.20, 0.45, "Family-first", "one representative per\nidentity/provenance group", "#DDF1ED")
    rounded_box(ax, (0.79, 0.28), 0.20, 0.45, "Abstain / fall back", "retire harmful sources;\nretain novelty + random", "#F3E9EB")
    for x0, x1 in [(0.21, 0.27), (0.47, 0.53), (0.73, 0.79)]:
        ax.add_patch(
            FancyArrowPatch(
                (x0 + 0.01, 0.505),
                (x1 - 0.01, 0.505),
                arrowstyle="-|>",
                mutation_scale=9,
                linewidth=0.9,
                color=COLORS["ink"],
            )
        )
    ax.text(
        0.5,
        0.10,
        "OOD distance constrains exploration; it does not multiply away qualified source evidence",
        ha="center",
        fontsize=6.5,
        color=COLORS["muted"],
    )


def draw_auc_panel(
    ax: plt.Axes,
    primary: pd.DataFrame,
    null_record: dict,
    scope: str,
    title: str,
    label: str,
) -> None:
    local = primary[primary["scope"].eq(scope)].set_index("policy")
    values = np.array([float(local.at[policy, "auc20"]) for policy in POLICIES])
    y = np.arange(len(POLICIES))
    ax.axvspan(
        float(null_record["shuffled_q025_auc20"]),
        float(null_record["shuffled_q975_auc20"]),
        color="#DFE3E7",
        alpha=0.55,
        zorder=0,
    )
    ax.axvline(
        float(null_record["shuffled_mean_auc20"]),
        color=COLORS["muted"],
        linewidth=0.8,
        linestyle=(0, (3, 2)),
        zorder=1,
    )
    bars = ax.barh(
        y,
        values,
        color=[BAR_COLORS[policy] for policy in POLICIES],
        height=0.68,
        edgecolor="white",
        linewidth=0.4,
        zorder=2,
    )
    for bar, value in zip(bars, values):
        ax.text(
            value + max(values) * 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{int(value)}",
            ha="left",
            va="center",
            fontsize=6.2,
            fontweight="bold" if bar is bars[-1] else "normal",
        )
    ax.set_yticks(y)
    ax.set_yticklabels([LABELS[policy].replace("\n", " ") for policy in POLICIES])
    ax.set_xlabel("Distinct-group AUC through 20")
    ax.set_title(title, loc="left", fontweight="bold", pad=5)
    ax.set_xlim(0, max(values) * 1.20)
    ax.set_ylim(-0.7, len(POLICIES) - 0.3)
    ax.invert_yaxis()
    ax.grid(axis="x", color="#E3E6E9", linewidth=0.55, zorder=0)
    ax.text(
        0.98,
        0.985,
        f"shuffled pair 95%: {null_record['shuffled_q025_auc20']:.0f}–{null_record['shuffled_q975_auc20']:.0f}\nconditional p={null_record['conditional_randomization_p']:.4f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.1,
        color=COLORS["muted"],
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=1.5),
    )
    panel_label(ax, label)


def draw_tradeoff(ax: plt.Axes, metrics: pd.DataFrame) -> None:
    panel_label(ax, "d")
    ax.set_title("Breadth–repeat tradeoff", loc="left", fontweight="bold", pad=5)
    policy_style = {
        "neighbor_entity_consensus": (COLORS["entity"], "Entity consensus"),
        "neighbor_family_first_consensus": (COLORS["family"], "Family-first consensus"),
    }
    scope_marker = {"external_candidate": "o", "hard_ood_40pct": "s"}
    scope_name = {"external_candidate": "external", "hard_ood_40pct": "hard OOD"}
    for scope, marker in scope_marker.items():
        for policy, (color, policy_name) in policy_style.items():
            entity = metrics[
                metrics["scope"].eq(scope)
                & metrics["policy"].eq(policy)
                & metrics["unit"].eq("entity")
            ].iloc[0]
            group = metrics[
                metrics["scope"].eq(scope)
                & metrics["policy"].eq(policy)
                & metrics["unit"].eq("provenance_group")
                & metrics["group_value_aggregation"].eq("max")
            ].iloc[0]
            ax.scatter(
                float(entity["recall20"]),
                float(group["recall20"]),
                s=62,
                marker=marker,
                facecolor=color,
                edgecolor="white",
                linewidth=0.7,
                zorder=3,
            )
            label_positions = {
                ("external_candidate", "neighbor_entity_consensus"): (0.66, 0.68),
                ("external_candidate", "neighbor_family_first_consensus"): (0.03, 0.89),
                ("hard_ood_40pct", "neighbor_entity_consensus"): (0.78, 0.93),
                ("hard_ood_40pct", "neighbor_family_first_consensus"): (0.37, 0.89),
            }
            lx, ly = label_positions[(scope, policy)]
            arrow = policy == "neighbor_family_first_consensus"
            ax.annotate(
                scope_name[scope],
                xy=(float(entity["recall20"]), float(group["recall20"])),
                xytext=(lx, ly),
                textcoords="data",
                fontsize=5.8,
                color=color,
                ha="left",
                va="bottom",
                arrowprops=(
                    dict(arrowstyle="-", color=color, lw=0.7) if arrow else None
                ),
            )
    ax.annotate(
        "broader distinct-region search",
        xy=(0.27, 0.98),
        xytext=(0.51, 0.79),
        arrowprops=dict(arrowstyle="->", color=COLORS["family"], lw=1.0),
        fontsize=6.2,
        color=COLORS["family"],
    )
    ax.text(
        0.02,
        0.985,
        "Family-first",
        transform=ax.transAxes,
        fontsize=6.3,
        fontweight="bold",
        color=COLORS["family"],
        va="top",
    )
    ax.text(
        0.98,
        0.985,
        "Entity consensus",
        transform=ax.transAxes,
        fontsize=6.3,
        fontweight="bold",
        color=COLORS["entity"],
        ha="right",
        va="top",
    )
    ax.set_xlim(-0.03, 1.04)
    ax.set_ylim(-0.03, 1.08)
    ax.set_xlabel("Entity top-5% recall at 20")
    ax.set_ylabel("Distinct top-group recall at 20")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(color="#E3E6E9", linewidth=0.55)
    ax.text(
        0.02,
        0.03,
        "Group = connected formula / DOI / ICSD component",
        transform=ax.transAxes,
        fontsize=5.8,
        color=COLORS["muted"],
    )
    ax.text(
        0.02,
        0.47,
        "Family-first deliberately trades\nrepeat entity hits for new regions",
        transform=ax.transAxes,
        fontsize=6.1,
        color=COLORS["muted"],
    )


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    metrics = pd.read_csv(METRICS)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    primary = metrics[
        metrics["unit"].eq("provenance_group")
        & metrics["group_value_aggregation"].eq("max")
    ]
    null_by_scope = {row["scope"]: row for row in summary["conditional_null"]}

    fig = plt.figure(figsize=(7.2, 6.15), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        3,
        height_ratios=[0.78, 1.45],
        width_ratios=[1.0, 1.0, 1.08],
        hspace=0.38,
        wspace=0.46,
    )
    ax_a = fig.add_subplot(grid[0, :])
    ax_b = fig.add_subplot(grid[1, 0])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])
    draw_workflow(ax_a)
    draw_auc_panel(
        ax_b,
        primary,
        null_by_scope["external_candidate"],
        "external_candidate",
        "Complete external candidate pool",
        "b",
    )
    draw_auc_panel(
        ax_c,
        primary,
        null_by_scope["hard_ood_40pct"],
        "hard_ood_40pct",
        "Hard-OOD 40% pool",
        "c",
    )
    draw_tradeoff(ax_d, metrics)
    fig.text(
        0.995,
        0.008,
        "Outcome-informed Caltech method development; intervals are conditional on one fixed target pool",
        ha="right",
        va="bottom",
        fontsize=5.7,
        color=COLORS["muted"],
    )
    fig.savefig(STEM.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(STEM.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(
        FIGURES / "family_first_neighbor_portfolio_600dpi.tif",
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(fig)
    print(f"Wrote {STEM.relative_to(ROOT)}.[svg|pdf|png] and 600 dpi TIFF")


if __name__ == "__main__":
    main()
