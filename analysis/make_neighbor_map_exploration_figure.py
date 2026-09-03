"""Build the combined neighboring-knowledge map and exploration figure.

The figure separates predictive model augmentation from proposal-ranking utility.
Corrective inference displays the full finite-seed null for static rankings and
compares family-first allocation directly with the strongest single donor.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
STEM = FIGURES / "neighbor_map_exploration"

CALTECH_A = RESULTS / "figure_caltech_policy_panel_a.csv"
CALTECH_B = RESULTS / "figure_caltech_policy_panel_b.csv"
CALTECH_C = RESULTS / "figure_caltech_policy_panel_c.csv"
FAMILY_METRICS = RESULTS / "family_first_neighbor_portfolio_metrics.csv"
FAMILY_SUMMARY = RESULTS / "family_first_neighbor_portfolio_summary.json"
CALTECH_CORRECTIVE = RESULTS / "caltech_static_ranking_empirical_null_summary.json"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.0,
        "axes.labelsize": 7.1,
        "axes.titlesize": 8.0,
        "axes.titleweight": "bold",
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 6.3,
        "ytick.labelsize": 6.3,
        "legend.fontsize": 6.0,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

INK = "#20262E"
MUTED = "#65717C"
GRID = "#E2E6E9"
PANEL = "#F4F6F8"
TEAL = "#147D73"
TEAL_DARK = "#0E5E57"
TEAL_LIGHT = "#A7D5CF"
BLUE = "#4C78A8"
PURPLE = "#7562A8"
ORANGE = "#D9822B"
RED = "#B64342"
GRAY = "#818991"
LIGHT_GRAY = "#D7DDE1"


def panel_label(ax: plt.Axes, label: str, x: float = -0.12) -> None:
    ax.text(
        x,
        1.06,
        label,
        transform=ax.transAxes,
        fontsize=9.4,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    width: float,
    title: str,
    subtitle: str,
    facecolor: str,
) -> None:
    patch = FancyBboxPatch(
        (x, 0.24),
        width,
        0.53,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=0.75,
        edgecolor=INK,
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(x + 0.025, 0.61, title, fontsize=7.6, fontweight="bold", va="center")
    ax.text(x + 0.025, 0.38, subtitle, fontsize=6.15, color=MUTED, va="center")


def panel_a(ax: plt.Axes) -> pd.DataFrame:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "a", -0.02)
    workflow = [
        ("Qualify", "leakage, source skill\nand wrong-source controls", "#EAF0F5"),
        ("Keep diversity", "retain credible source\nrankings separately", "#E1EDF5"),
        ("Borrow continuously", "predictive feature or\nproposal-ranking prior", "#DDF1ED"),
        ("Allocate family-first", "one early proposal per\ndistinct composition region", "#D7ECE8"),
        ("Abstain", "fall back when the\nqualification gate fails", "#F3E9EB"),
    ]
    x_positions = [0.01, 0.21, 0.41, 0.61, 0.81]
    width = 0.18
    for (title, subtitle, color), x in zip(workflow, x_positions):
        rounded_box(ax, x, width, title, subtitle, color)
    for left, right in zip(x_positions[:-1], x_positions[1:]):
        ax.add_patch(
            FancyArrowPatch(
                (left + width + 0.005, 0.505),
                (right - 0.005, 0.505),
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.85,
                color=INK,
            )
        )
    ax.text(
        0.5,
        0.08,
        "The map separates model-fit transfer from OOD exploration utility",
        ha="center",
        fontsize=6.45,
        color=MUTED,
    )
    frame = pd.DataFrame(
        [
            {"step": i + 1, "title": title, "subtitle": subtitle.replace("\n", " ")}
            for i, (title, subtitle, _) in enumerate(workflow)
        ]
    )
    frame.to_csv(RESULTS / "figure_neighbor_map_panel_a.csv", index=False)
    return frame


def panel_b(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_neighbor_map_panel_b.csv", index=False)
    order = [
        "obelix_same_property",
        "estm_transport_neighbor",
        "borg_mechanical_control",
        "ocx_catalysis_control",
        "shuffled_obelix",
    ]
    local = frame.set_index("source").loc[order].reset_index()
    y = np.arange(len(local))[::-1]
    for yi, row in zip(y, local.to_dict("records")):
        color = TEAL if row["source_class"] == "real neighbor" else GRAY
        ax.plot(
            [row["mean_weight_mean"], row["admission_rate_mean"]],
            [yi, yi],
            color=LIGHT_GRAY,
            lw=1.7,
            zorder=1,
        )
        ax.scatter(
            row["admission_rate_mean"],
            yi,
            s=34,
            color=color,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.scatter(
            row["mean_weight_mean"],
            yi,
            s=27,
            marker="s",
            facecolor="white",
            edgecolor=color,
            linewidth=1.0,
            zorder=3,
        )
    ax.axvline(0.20, color=RED, lw=0.8, ls=(0, (3, 2)))
    labels = []
    for row in local.to_dict("records"):
        name = row["label"].replace("\n", " ")
        skill = row["source_oof_r2"]
        labels.append(f"{name}\nOOF $R^2$={skill:.2f}" if np.isfinite(skill) else f"{name}\nOOF $R^2$=n/a")
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 0.45)
    ax.set_ylim(-0.6, len(local) - 0.4)
    ax.set_xlabel("Mean gate rate or weight")
    ax.set_title("Source skill alone does not qualify transfer", loc="left")
    ax.scatter([], [], s=34, color=INK, label="admission")
    ax.scatter([], [], s=27, marker="s", facecolor="white", edgecolor=INK, label="weight")
    ax.legend(loc="lower right", handletextpad=0.25)
    panel_label(ax, "b")


def panel_c(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_neighbor_map_panel_c.csv", index=False)
    order = ["OBELiX residual", "ESTM residual", "multisource residual"]
    colors = {"OBELiX residual": TEAL, "ESTM residual": BLUE, "multisource residual": PURPLE}
    y_base = {name: 2 - i for i, name in enumerate(order)}
    scope_style = {
        "external_candidate": (0.13, "o", "external"),
        "hard_ood_40pct": (-0.13, "s", "hard OOD"),
    }
    for row in frame.to_dict("records"):
        offset, marker, _ = scope_style[row["scope"]]
        y = y_base[row["policy_label"]] + offset
        color = colors[row["policy_label"]]
        ax.plot([row["ci_lo"], row["ci_hi"]], [y, y], color=color, lw=1.3)
        ax.scatter(row["mean_auc20_gain"], y, marker=marker, s=29, color=color, edgecolor="white", linewidth=0.45, zorder=3)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks([2, 1, 0], order)
    ax.set_xlim(-1.5, 3.5)
    ax.set_ylim(-0.55, 2.55)
    ax.set_xlabel("AUC20 gain over target-only")
    ax.set_title("Adaptive model augmentation is null", loc="left")
    ax.scatter([], [], marker="o", s=28, color=GRAY, label="external")
    ax.scatter([], [], marker="s", s=28, color=GRAY, label="hard OOD")
    ax.legend(loc="upper right", handletextpad=0.25)
    ax.text(
        0.98,
        0.05,
        "0/6 pass all frozen gates",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.1,
        color=RED,
        fontweight="bold",
    )
    panel_label(ax, "c")


def panel_d(
    ax: plt.Axes, frame: pd.DataFrame, corrective: dict[str, object]
) -> None:
    frame.to_csv(RESULTS / "figure_neighbor_map_panel_d.csv", index=False)
    order = ["OBELiX", "ESTM", "Borg", "OCx"]
    local = frame.set_index(["scope", "label"])
    inference = {
        (row["scope"], row["policy"]): row
        for row in corrective["static_ranking_tests"]
    }
    policy_by_label = {
        "OBELiX": "obelix_same_property_static",
        "ESTM": "estm_transport_neighbor_static",
    }
    y = np.arange(len(order))[::-1]
    for scope, offset, marker, label in (
        ("external_candidate", 0.12, "o", "external"),
        ("hard_ood_40pct", -0.12, "s", "hard OOD"),
    ):
        values = [float(local.loc[(scope, name), "auc20"]) for name in order]
        for yi, name, value in zip(y, order, values):
            source_class = str(local.loc[(scope, name), "source_class"])
            color = TEAL if source_class == "real neighbor" else GRAY
            if name in policy_by_label:
                test = inference[(scope, policy_by_label[name])]
                ax.plot(
                    [test["shuffled_q025"], test["shuffled_q975"]],
                    [yi + offset, yi + offset],
                    color=LIGHT_GRAY,
                    lw=3.0,
                    solid_capstyle="round",
                    zorder=1,
                )
                adjusted = float(test["holm_p_vs_shuffled_four_tests"])
                ax.text(
                    value + 1.5,
                    yi + offset,
                    f"$p_H$={adjusted:.3f}",
                    fontsize=5.35,
                    color=TEAL_DARK if adjusted < 0.05 else MUTED,
                    va="center",
                )
            ax.scatter(value, yi + offset, s=31, marker=marker, color=color, edgecolor="white", linewidth=0.45, zorder=3)
    ax.set_yticks(y, order)
    ax.set_xlim(-1, 69)
    ax.set_xlabel("Static ranking AUC20")
    ax.set_title("Static rankings tested against finite-seed nulls", loc="left")
    ax.grid(axis="x", color=GRID, lw=0.55)
    ax.scatter([], [], marker="o", s=28, color=GRAY, label="external")
    ax.scatter([], [], marker="s", s=28, color=GRAY, label="hard OOD")
    ax.plot([], [], color=LIGHT_GRAY, lw=3.0, label="shuffled 95% interval")
    ax.legend(loc="lower right", handletextpad=0.25)
    panel_label(ax, "d")


def family_frame() -> pd.DataFrame:
    metrics = pd.read_csv(FAMILY_METRICS)
    primary = metrics[
        metrics["unit"].eq("provenance_group")
        & metrics["group_value_aggregation"].eq("max")
        & metrics["policy"].isin(
            [
                "wrong_source_family_first_consensus",
                "estm_family_first",
                "neighbor_entity_consensus",
                "neighbor_family_first_consensus",
            ]
        )
    ].copy()
    summary = json.loads(FAMILY_SUMMARY.read_text(encoding="utf-8"))
    nulls = {row["scope"]: row for row in summary["conditional_null"]}
    primary["conditional_randomization_p"] = primary["scope"].map(
        {scope: values["conditional_randomization_p"] for scope, values in nulls.items()}
    )
    primary["shuffled_q025_auc20"] = primary["scope"].map(
        {scope: values["shuffled_q025_auc20"] for scope, values in nulls.items()}
    )
    primary["shuffled_q975_auc20"] = primary["scope"].map(
        {scope: values["shuffled_q975_auc20"] for scope, values in nulls.items()}
    )
    return primary


def panel_e(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_neighbor_map_panel_e.csv", index=False)
    policies = [
        "wrong_source_family_first_consensus",
        "estm_family_first",
        "neighbor_family_first_consensus",
    ]
    labels = ["Wrong-source\nconsensus", "Best single\nneighbor", "Family-first\nconsensus"]
    y = np.array([2, 1, 0], dtype=float)
    scope_style = {
        "external_candidate": (0.13, "o", "external"),
        "hard_ood_40pct": (-0.13, "s", "hard OOD"),
    }
    index = frame.set_index(["scope", "policy"])
    for scope, (offset, marker, legend_label) in scope_style.items():
        values = [float(index.loc[(scope, p), "auc20"]) for p in policies]
        for yi, policy, value in zip(y, policies, values):
            color = TEAL if policy == "neighbor_family_first_consensus" else (BLUE if policy == "estm_family_first" else GRAY)
            ax.scatter(value, yi + offset, marker=marker, s=42, color=color, edgecolor="white", linewidth=0.5, zorder=3)
        family_value = values[-1]
        best_single = values[-2]
        ax.text(
            family_value + 1.4,
            y[-1] + offset,
            f"$\\Delta$AUC={family_value - best_single:+.0f}",
            fontsize=5.65,
            color=TEAL_DARK,
            va="center",
        )
    for yi in y:
        ax.axhline(yi, color=GRID, lw=0.55, zorder=0)
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 69)
    ax.set_ylim(-0.55, 2.55)
    ax.set_xlabel("Distinct-group AUC through 20")
    ax.set_title("Family-first changes allocation, not top-hit recall", loc="left")
    ax.scatter([], [], marker="o", s=30, color=GRAY, label="external")
    ax.scatter([], [], marker="s", s=30, color=GRAY, label="hard OOD")
    ax.legend(loc="upper right", handletextpad=0.25)
    ax.text(
        0.98,
        0.05,
        "recall gain vs best single: 0 in both scopes",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.45,
        color=MUTED,
    )
    panel_label(ax, "e")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    caltech_a = pd.read_csv(CALTECH_A)
    caltech_b = pd.read_csv(CALTECH_B)
    caltech_c = pd.read_csv(CALTECH_C)
    family = family_frame()
    corrective = json.loads(CALTECH_CORRECTIVE.read_text(encoding="utf-8"))

    figure = plt.figure(figsize=(7.2, 6.15), constrained_layout=False)
    grid = figure.add_gridspec(
        3,
        2,
        height_ratios=[0.72, 1.28, 1.38],
        width_ratios=[1.0, 1.0],
        hspace=0.56,
        wspace=0.48,
        left=0.085,
        right=0.985,
        top=0.975,
        bottom=0.075,
    )
    ax_a = figure.add_subplot(grid[0, :])
    ax_b = figure.add_subplot(grid[1, 0])
    ax_c = figure.add_subplot(grid[1, 1])
    ax_d = figure.add_subplot(grid[2, 0])
    ax_e = figure.add_subplot(grid[2, 1])

    panel_a(ax_a)
    panel_b(ax_b, caltech_a)
    panel_c(ax_c, caltech_b)
    panel_d(ax_d, caltech_c, corrective)
    panel_e(ax_e, family)

    figure.text(
        0.985,
        0.012,
        "Caltech retrospective benchmark; empirical-null correction and family-first analysis are outcome-informed",
        ha="right",
        va="bottom",
        fontsize=5.6,
        color=MUTED,
    )
    figure.savefig(STEM.with_suffix(".svg"), bbox_inches="tight")
    figure.savefig(STEM.with_suffix(".pdf"), bbox_inches="tight")
    figure.savefig(STEM.with_suffix(".png"), dpi=300, bbox_inches="tight")
    figure.savefig(
        STEM.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)
    print(f"Wrote {STEM.relative_to(ROOT)}.[svg|pdf|png|tiff]")


if __name__ == "__main__":
    main()
