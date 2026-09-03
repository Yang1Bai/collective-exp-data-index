"""Figure 4: endpoint routing under controlled catalyst perturbations."""
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure4_routing_nmi_v4"
SOURCE = SOURCE_DIR / "figure4_routing_nmi_v4.csv"

NAVY = "#173B6C"
TEAL = "#1E9189"
GREEN = "#469A6A"
ORANGE = "#E98A32"
CORAL = "#CF6258"
INK = "#24303D"
MID = "#7A8795"
GRID = "#D9E1E8"
PALE_TEAL = "#EAF5F1"
PALE_ORANGE = "#FCF0E2"
PALE_CORAL = "#FAECE9"

TARGETS = ["A", "B", "C", "D"]
TARGET_LABELS = {
    "A": "amino-ligand",
    "B": "tricarboxylate",
    "C": "Fe substitution",
    "D": "Mn substitution",
}
ROUTE = {"A": "RANK", "B": "PREDICT + RANK", "C": "REJECT", "D": "PREDICT + RANK"}
ROUTE_COLOR = {"A": ORANGE, "B": GREEN, "C": CORAL, "D": GREEN}
ROUTE_FACE = {"A": PALE_ORANGE, "B": PALE_TEAL, "C": PALE_CORAL, "D": PALE_TEAL}

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 6.2,
    "axes.titlesize": 6.8,
    "axes.labelsize": 6.2,
    "xtick.labelsize": 5.6,
    "ytick.labelsize": 5.6,
    "axes.linewidth": .6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})


def panel_label(ax: plt.Axes, label: str, x: float = 0.0, y: float = 1.03) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8, fontweight="bold",
            ha="left", va="bottom", color="black")


def panel_a(ax: plt.Axes) -> None:
    panel_label(ax, "a", -.035, 1.02)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.set_title("One assay and composition grid; one chemical factor changes",
                 loc="left", pad=7)
    donor = FancyBboxPatch((.025, .35), .17, .34,
                           boxstyle="round,pad=.018,rounding_size=.025",
                           facecolor="#EDF4F9", edgecolor=NAVY, lw=.8)
    ax.add_patch(donor)
    ax.text(.11, .60, "donor relation", ha="center", va="center",
            color=NAVY, fontsize=6.5, fontweight="bold")
    ax.text(.11, .49, "462 catalysts", ha="center", va="center", color=INK)
    ax.text(.11, .40, "six-slot mixtures", ha="center", va="center", color=MID)
    centres = [.32, .51, .70, .89]
    for xc, target in zip(centres, TARGETS):
        ax.add_patch(FancyArrowPatch((.20, .52), (xc - .085, .52), arrowstyle="-|>",
                                     mutation_scale=7, lw=.75, color=TEAL,
                                     connectionstyle="arc3,rad=0"))
        box = FancyBboxPatch((xc - .075, .40), .15, .24,
                             boxstyle="round,pad=.010,rounding_size=.018",
                             facecolor="white", edgecolor=GRID, lw=.7)
        ax.add_patch(box)
        ax.text(xc, .55, target, ha="center", va="center", fontsize=6.5,
                color=INK, fontweight="bold")
        ax.text(xc, .46, TARGET_LABELS[target], ha="center", va="center",
                fontsize=5.1, color=MID)
        route = FancyBboxPatch((xc - .075, .21), .15, .11,
                               boxstyle="round,pad=.008,rounding_size=.015",
                               facecolor=ROUTE_FACE[target], edgecolor=ROUTE_COLOR[target], lw=.65)
        ax.add_patch(route)
        ax.text(xc, .265, ROUTE[target], ha="center", va="center", fontsize=4.8,
                color=ROUTE_COLOR[target], fontweight="bold")
    ax.text(.025, .035,
            "same OER endpoint · same composition grid · complete 126-catalyst systems · five recipient anchors",
            ha="left", va="bottom", fontsize=5.0, color=MID)


def controlled_rows(frame: pd.DataFrame, measure: str) -> pd.DataFrame:
    return (frame[(frame["panel"].eq("c")) & frame["measure"].eq(measure)]
            .set_index("target").loc[TARGETS])


def forest(ax: plt.Axes, frame: pd.DataFrame, measure: str, scale: float,
           xlabel: str, *, routes: bool) -> None:
    rows = controlled_rows(frame, measure)
    y = np.arange(4)[::-1]
    ax.axvline(0, color=INK, lw=.7)
    ax.axvspan(0, 36 if scale == 100 else .50, color=PALE_TEAL, zorder=0)
    for yi, (target, row) in zip(y, rows.iterrows()):
        estimate = scale * float(row["estimate"])
        low = scale * float(row["ci95_low"])
        high = scale * float(row["ci95_high"])
        colour = ROUTE_COLOR[target]
        ax.plot([low, high], [yi, yi], color=colour, lw=2.1, solid_capstyle="round")
        ax.scatter(estimate, yi, s=31, color=colour, edgecolor="white",
                   linewidth=.5, zorder=3)
        label = f"{estimate:+.1f}%" if scale == 100 else f"{estimate:+.3f}"
        ax.text(high + (.8 if scale == 100 else .010), yi, label,
                ha="left", va="center", fontsize=5.4, color=colour,
                fontweight="bold")
        if routes:
            ax.text(1.09, yi, ROUTE[target], transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=4.9, color=colour,
                    fontweight="bold", clip_on=False)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{target}  {TARGET_LABELS[target]}" for target in TARGETS])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=.42)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(RESULTS / "specgen_derivative_oer_figure_source_data.csv")
    frame.to_csv(SOURCE, index=False)

    fig = plt.figure(figsize=(7.204724, 4.409449))  # 183 x 112 mm
    ax_a = fig.add_axes([.055, .59, .90, .33])
    ax_b = fig.add_axes([.13, .14, .35, .34])
    ax_c = fig.add_axes([.59, .14, .28, .34])
    panel_a(ax_a)
    panel_label(ax_b, "b", -.11, 1.03)
    ax_b.set_title("Numerical utility", loc="left", pad=7)
    ax_b.set_xlim(-20, 38)
    forest(ax_b, frame, "relative_rmse_gain", 100, "relative RMSE gain (%)", routes=False)
    panel_label(ax_c, "c", -.11, 1.03)
    ax_c.set_title("Ordinal utility and route", loc="left", pad=7)
    ax_c.set_xlim(-.05, .50)
    forest(ax_c, frame, "spearman_gain", 1, "Spearman gain", routes=True)
    fig.text(.055, .035,
             "Post-primary composition relation; every non-anchor catalyst retained; points are bootstrap means and bars are 95% intervals.",
             ha="left", va="bottom", fontsize=5.1, color=MID)

    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
