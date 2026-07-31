"""Build a Nature-style Figure 1 for falsification-gated knowledge borrowing.

The figure deliberately has one visual hero: a relation/order signal that is
allowed to cross from neighbouring experimental programmes into a sparse OOD
recipient only after four explicit checks. Numerical annotations are loaded
from the committed source-data table.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "analysis" / "figures"
DATA = FIG_DIR / "source_data" / "knowledge_borrowing_overview_nature_v3.csv"
OUT = FIG_DIR / "knowledge_borrowing_overview_nature_v3"

INK = "#222B38"
NAVY = "#173B6C"
BLUE = "#3478BD"
TEAL = "#128A83"
GREEN = "#3B8F5E"
ORANGE = "#E8872E"
CORAL = "#C95A50"
MID = "#7E8998"
GRID = "#D6DDE5"
PALE = "#F6F8FA"
PALE_BLUE = "#EDF4F9"
PALE_TEAL = "#EAF5F2"
PALE_ORANGE = "#FDF3E7"
PALE_CORAL = "#F9ECEA"


mpl.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 6.0,
        "axes.titlesize": 7.0,
        "axes.labelsize": 6.0,
        "xtick.labelsize": 5.3,
        "ytick.labelsize": 5.3,
        "axes.linewidth": 0.55,
        "lines.linewidth": 0.9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def panel_label(ax: plt.Axes, letter: str, x: float = 0.0, y: float = 1.01) -> None:
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.0,
        fontweight="bold",
        color="black",
    )


def rounded_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    facecolor: str = "white",
    edgecolor: str = GRID,
    linewidth: float = 0.6,
    radius: float = 0.012,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )
    ax.add_patch(patch)
    return patch


def draw_programme(
    ax: plt.Axes,
    x: float,
    y: float,
    title: str,
    kind: str,
    accent: str,
) -> None:
    """Draw a compact experimental programme as measurement curves plus state."""
    w, h = 0.235, 0.185
    rounded_box(ax, (x, y), w, h, facecolor="white", edgecolor="#C9D2DC")
    ax.text(x + 0.012, y + h - 0.030, title, ha="left", va="center", color=INK,
            fontsize=6.0, fontweight="bold")

    x0, x1 = x + 0.015, x + 0.130
    y0, y1 = y + 0.052, y + 0.133
    ax.plot([x0, x0, x1], [y1, y0, y0], color="#AAB4BF", lw=0.45)
    xx = np.linspace(0, 1, 40)
    for i, alpha in enumerate([0.30, 0.50, 0.85]):
        if kind == "transport":
            yy = 0.13 + 0.18 * i + 0.42 * xx + 0.08 * xx**2
        elif kind == "catalysis":
            yy = 0.12 + 0.15 * i + 0.55 * np.exp(-((xx - 0.52 - 0.05 * i) / 0.30) ** 2)
        else:
            yy = 0.13 + 0.15 * i + 0.46 * np.sin(np.pi * (0.82 * xx + 0.05 * i)) ** 2
        ax.plot(x0 + (x1 - x0) * xx, y0 + (y1 - y0) * yy, color=accent,
                lw=0.70, alpha=alpha)
    ax.text(x + 0.145, y + 0.111, "composition", ha="left", va="center",
            color=INK, fontsize=5.1)
    ax.text(x + 0.145, y + 0.080, "state / assay", ha="left", va="center",
            color=INK, fontsize=5.1)
    ax.text(x + 0.145, y + 0.049, "source record", ha="left", va="center",
            color=INK, fontsize=5.1)
    for yy in [0.111, 0.080, 0.049]:
        ax.add_patch(Circle((x + 0.135, y + yy), 0.0045, facecolor=accent,
                            edgecolor="none", alpha=0.85))


def draw_failed_path(ax: plt.Axes, y: float, x_end: float) -> None:
    ax.plot([0.285, x_end - 0.012], [y, y], color="#BCC5CF", lw=0.65, zorder=1)
    ax.text(x_end, y, "x", ha="center", va="center", color=CORAL,
            fontsize=6.3, fontweight="bold", zorder=3)


def draw_contract(ax: plt.Axes) -> None:
    x0, y0, w, h = 0.335, 0.225, 0.300, 0.560
    rounded_box(ax, (x0, y0), w, h, facecolor=PALE, edgecolor="#BCC7D2",
                linewidth=0.75, radius=0.015)
    ax.text(x0 + w / 2, y0 + h + 0.034, "qualify what is borrowed",
            ha="center", va="center", color=INK, fontsize=6.5, fontweight="bold")

    gate_x = [0.382, 0.452, 0.522, 0.592]
    labels = ["common\ninputs", "matched\nstate", "declared\nrelation", "matched\nfalsifier"]
    for i, (gx, label) in enumerate(zip(gate_x, labels), start=1):
        ax.add_patch(Rectangle((gx - 0.015, y0 + 0.055), 0.030, h - 0.110,
                               facecolor="white", edgecolor="#AEBBC8", lw=0.55))
        ax.add_patch(Circle((gx, y0 + h - 0.048), 0.013, facecolor=NAVY,
                            edgecolor="white", lw=0.4, zorder=4))
        ax.text(gx, y0 + h - 0.048, str(i), ha="center", va="center",
                color="white", fontsize=5.0, fontweight="bold", zorder=5)
        ax.text(gx, y0 - 0.025, label, ha="center", va="top", color=INK,
                fontsize=5.1, linespacing=1.05)

    draw_failed_path(ax, 0.680, gate_x[0])
    draw_failed_path(ax, 0.600, gate_x[1])
    draw_failed_path(ax, 0.520, gate_x[2])
    draw_failed_path(ax, 0.440, gate_x[3])

    ax.add_patch(FancyArrowPatch(
        (0.285, 0.355), (0.657, 0.355), arrowstyle="-|>", mutation_scale=8,
        linewidth=2.0, color=TEAL, zorder=4
    ))
    for gx in gate_x:
        ax.add_patch(Circle((gx, 0.355), 0.008, facecolor=GREEN,
                            edgecolor="white", lw=0.45, zorder=6))
    ax.text(0.299, 0.318, "candidate links", ha="left", va="top", color=MID,
            fontsize=5.2)


def draw_relation_capsule(ax: plt.Axes) -> None:
    rounded_box(ax, (0.648, 0.305), 0.082, 0.100, facecolor="white",
                edgecolor=TEAL, linewidth=0.75, radius=0.018)
    xx = np.linspace(0, 1, 30)
    yy = 0.20 + 0.60 / (1 + np.exp(-7 * (xx - 0.50)))
    ax.plot(0.660 + 0.057 * xx, 0.320 + 0.063 * yy, color=TEAL, lw=1.2)
    ax.scatter([0.667, 0.684, 0.708], [0.337, 0.351, 0.372], s=7,
               facecolor=BLUE, edgecolor="white", lw=0.35, zorder=5)
    ax.text(0.689, 0.430, "relation or order", ha="center", va="bottom",
            color=INK, fontsize=5.4, fontweight="bold")


def draw_ood_recipient(ax: plt.Axes) -> None:
    # Sparse target region with a visible experimental frontier.
    ax.add_patch(Ellipse((0.858, 0.505), 0.245, 0.570, facecolor=PALE_BLUE,
                         edgecolor="#A7B4C1", lw=0.65, ls=(0, (3, 2)), zorder=0))
    ax.add_patch(Ellipse((0.806, 0.505), 0.135, 0.340, facecolor="white",
                         edgecolor="#C6D1DC", lw=0.55, zorder=1))
    ax.plot([0.855, 0.855], [0.245, 0.770], color="#98A5B2", lw=0.6,
            ls=(0, (3, 2)), zorder=2)
    ax.text(0.855, 0.792, "experimental frontier", ha="center", va="bottom",
            color=INK, fontsize=5.2)

    measured = np.array([
        [0.770, 0.410], [0.790, 0.535], [0.808, 0.455],
        [0.820, 0.620], [0.835, 0.565],
    ])
    candidates = np.array([
        [0.882, 0.365], [0.895, 0.485], [0.908, 0.585],
        [0.923, 0.690], [0.942, 0.615], [0.957, 0.525],
        [0.968, 0.430], [0.938, 0.325],
    ])
    ax.scatter(measured[:, 0], measured[:, 1], s=22, marker="o",
               facecolor=BLUE, edgecolor="white", linewidth=0.55, zorder=5)
    ax.scatter(candidates[:, 0], candidates[:, 1], s=24, marker="o",
               facecolor="white", edgecolor=ORANGE, linewidth=0.85, zorder=5)

    xx = np.linspace(0.745, 0.975, 90)
    yy = 0.33 + 0.36 / (1 + np.exp(-24 * (xx - 0.868)))
    ax.plot(xx, yy, color=TEAL, lw=1.9, zorder=4)
    ax.fill_between(xx, yy - 0.035, yy + 0.035, color=TEAL, alpha=0.10, zorder=3)

    for rank, idx in enumerate([3, 4, 2], start=1):
        x, y = candidates[idx]
        ax.text(x + 0.010, y + 0.022, str(rank), ha="left", va="bottom",
                color=INK, fontsize=5.0, fontweight="bold")
    ax.text(0.795, 0.285, "5 measured anchors", ha="center", va="center",
            color=INK, fontsize=5.2)
    ax.text(0.931, 0.285, "unmeasured candidates", ha="center", va="center",
            color=INK, fontsize=5.2)


def panel_a(ax: plt.Axes) -> None:
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    panel_label(ax, "a", 0.0, 1.005)
    ax.text(0.035, 1.010, "A transferable object is qualified before it enters the OOD target",
            transform=ax.transAxes, ha="left", va="bottom", color=INK,
            fontsize=7.0, fontweight="bold")

    ax.text(0.025, 0.915, "Neighbouring experimental programmes", ha="left",
            va="center", color=INK, fontsize=6.3, fontweight="bold")
    ax.text(0.340, 0.915, "Borrowing contract", ha="left", va="center",
            color=INK, fontsize=6.3, fontweight="bold")
    ax.text(0.745, 0.915, "Sparse OOD recipient", ha="left", va="center",
            color=INK, fontsize=6.3, fontweight="bold")

    draw_programme(ax, 0.020, 0.655, "solid transport", "transport", BLUE)
    draw_programme(ax, 0.020, 0.420, "electrocatalysis", "catalysis", GREEN)
    draw_programme(ax, 0.020, 0.185, "molecular mixtures", "mixtures", ORANGE)

    # Candidate links are deliberately thinner than the accepted relation.
    for yy, source_y in zip([0.680, 0.600, 0.520, 0.440, 0.355],
                            [0.745, 0.690, 0.510, 0.330, 0.510]):
        ax.plot([0.255, 0.285], [source_y, yy], color="#C4CDD6", lw=0.55,
                alpha=0.85, zorder=0)
    draw_contract(ax)
    draw_relation_capsule(ax)
    ax.add_patch(FancyArrowPatch(
        (0.730, 0.355), (0.758, 0.410), arrowstyle="-|>", mutation_scale=8,
        linewidth=1.7, color=TEAL, zorder=5
    ))
    draw_ood_recipient(ax)

    ax.text(0.475, 0.075, "The database stays behind; only the tested relation or candidate order crosses.",
            ha="center", va="center", color=INK, fontsize=5.6)


def draw_predict_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.plot([x - 0.030, x - 0.030, x + 0.035], [y + 0.038, y - 0.032, y - 0.032],
            color="#AAB4BF", lw=0.50)
    xx = np.linspace(0, 1, 25)
    yy = 0.12 + 0.66 / (1 + np.exp(-7 * (xx - 0.50)))
    ax.plot(x - 0.024 + 0.053 * xx, y - 0.026 + 0.062 * yy, color=TEAL, lw=1.1)
    ax.scatter([x - 0.014, x + 0.002, x + 0.020],
               [y - 0.010, y + 0.003, y + 0.022], s=8, facecolor=BLUE,
               edgecolor="white", lw=0.35, zorder=4)


def draw_screen_icon(ax: plt.Axes, x: float, y: float) -> None:
    left_y = [y + 0.021, y - 0.022, y + 0.004, y - 0.006]
    right_y = [y + 0.027, y + 0.009, y - 0.009, y - 0.027]
    colours = [TEAL, TEAL, ORANGE, ORANGE]
    for yy, colour in zip(left_y, colours):
        ax.add_patch(Circle((x - 0.028, yy), 0.006, facecolor=colour,
                            edgecolor="white", lw=0.35))
    ax.add_patch(FancyArrowPatch((x - 0.014, y), (x + 0.012, y),
                                 arrowstyle="-|>", mutation_scale=5,
                                 color="#A7B2BD", lw=0.55))
    for yy, colour in zip(right_y, colours):
        ax.add_patch(Circle((x + 0.026, yy), 0.006, facecolor=colour,
                            edgecolor="white", lw=0.35))


def draw_abstain_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.plot([x - 0.030, x + 0.030], [y, y], color="#B8C2CC", lw=1.0)
    ax.plot([x - 0.006, x + 0.006], [y - 0.012, y + 0.012], color=CORAL, lw=1.0)
    ax.plot([x - 0.006, x + 0.006], [y + 0.012, y - 0.012], color=CORAL, lw=1.0)


def metric(data: pd.DataFrame, route: str, name: str) -> float:
    row = data[(data.route == route) & (data.metric == name)]
    if len(row) != 1:
        raise ValueError(f"Expected one row for {route}:{name}; found {len(row)}")
    return float(row.iloc[0].value)


def panel_b(ax: plt.Axes, data: pd.DataFrame) -> None:
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    panel_label(ax, "b", 0.0, 1.005)
    ax.text(0.035, 1.010, "The same contract routes evidence to prediction, screening or abstention",
            transform=ax.transAxes, ha="left", va="bottom", color=INK,
            fontsize=7.0, fontweight="bold")

    ax.plot([0.333, 0.333], [0.08, 0.86], color=GRID, lw=0.65)
    ax.plot([0.666, 0.666], [0.08, 0.86], color=GRID, lw=0.65)

    gain = metric(data, "predict", "relative_log_rmse_gain")
    r2 = metric(data, "predict", "raw_r2")
    rho_pred = metric(data, "predict", "spearman")
    draw_predict_icon(ax, 0.060, 0.615)
    ax.add_patch(Rectangle((0.025, 0.820), 0.012, 0.055, facecolor=TEAL, edgecolor="none"))
    ax.text(0.050, 0.848, "Predict", ha="left", va="center", color=INK,
            fontsize=6.4, fontweight="bold")
    ax.text(0.110, 0.645, f"{gain:.2f}% lower log-RMSE", ha="left", va="center",
            color=INK, fontsize=6.8, fontweight="bold")
    ax.text(0.110, 0.500, "external unseen-salt programme", ha="left", va="center",
            color=INK, fontsize=5.4)
    ax.text(0.110, 0.355, f"raw R2 = {r2:.3f}   |   Spearman = {rho_pred:.3f}",
            ha="left", va="center", color=MID, fontsize=5.2)

    rec_rho = metric(data, "screen", "recipient_spearman")
    donor_rho = metric(data, "screen", "borrowed_spearman")
    rec_p = metric(data, "screen", "recipient_precision_top_quartile")
    donor_p = metric(data, "screen", "borrowed_precision_top_quartile")
    draw_screen_icon(ax, 0.392, 0.615)
    ax.add_patch(Rectangle((0.358, 0.820), 0.012, 0.055, facecolor=GREEN, edgecolor="none"))
    ax.text(0.383, 0.848, "Screen", ha="left", va="center", color=INK,
            fontsize=6.4, fontweight="bold")
    ax.text(0.442, 0.645, f"candidate order {rec_rho:.3f} to {donor_rho:.3f}",
            ha="left", va="center", color=INK, fontsize=6.8, fontweight="bold")
    ax.text(0.442, 0.500, "five measured recipient formulations", ha="left", va="center",
            color=INK, fontsize=5.4)
    ax.text(0.442, 0.355, f"top-quartile precision {rec_p:.3f} to {donor_p:.3f}",
            ha="left", va="center", color=MID, fontsize=5.2)

    n_pass = int(metric(data, "abstain", "generic_edges_passed"))
    donor = metric(data, "abstain", "frozen_donor_score")
    recipient = metric(data, "abstain", "frozen_recipient_score")
    draw_abstain_icon(ax, 0.724, 0.615)
    ax.add_patch(Rectangle((0.691, 0.820), 0.012, 0.055, facecolor=CORAL, edgecolor="none"))
    ax.text(0.716, 0.848, "Abstain", ha="left", va="center", color=INK,
            fontsize=6.4, fontweight="bold")
    ax.text(0.775, 0.645, f"{n_pass}/40 generic edges pass", ha="left", va="center",
            color=INK, fontsize=6.8, fontweight="bold")
    ax.text(0.775, 0.500, "complete OOD-repair gate", ha="left", va="center",
            color=INK, fontsize=5.4)
    ax.text(0.775, 0.355, f"frozen donor {donor:.3f} < recipient {recipient:.3f}",
            ha="left", va="center", color=MID, fontsize=5.2)


def build() -> None:
    data = pd.read_csv(DATA)
    fig = plt.figure(figsize=(7.2047, 4.50), constrained_layout=False)
    ax_a = fig.add_axes([0.035, 0.350, 0.930, 0.600])
    ax_b = fig.add_axes([0.035, 0.065, 0.930, 0.210])
    panel_a(ax_a)
    panel_b(ax_b, data)
    fig.add_artist(mpl.lines.Line2D([0.035, 0.965], [0.310, 0.310],
                                    transform=fig.transFigure, color=GRID, lw=0.65))

    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0.0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0.0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0.0)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0.0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    build()
