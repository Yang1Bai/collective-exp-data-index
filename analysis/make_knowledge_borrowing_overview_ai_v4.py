"""Build the AI-illustrated, data-grounded Nature-style Figure 1.

Panel a uses a generated conceptual illustration only. All scientific labels
are vector overlays. Panel b is rebuilt from the committed source-data table;
no quantitative annotation is read from or inferred from the illustration.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "analysis" / "figures"
HERO = FIG_DIR / "assets" / "knowledge_borrowing_hero_ai_v4.png"
DATA = FIG_DIR / "source_data" / "knowledge_borrowing_overview_ai_v4.csv"
OUT = FIG_DIR / "knowledge_borrowing_overview_ai_v4"

INK = "#24303D"
NAVY = "#173B6C"
BLUE = "#3478BD"
TEAL = "#128A83"
GREEN = "#3B8F5E"
ORANGE = "#E8872E"
CORAL = "#C95A50"
MID = "#74808D"
GRID = "#D9E0E7"
PALE_BLUE = "#F2F7FB"
PALE_TEAL = "#EEF8F5"
PALE_CORAL = "#FCF2F0"


mpl.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 6.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def metric(data: pd.DataFrame, route: str, name: str) -> float:
    row = data[(data.route == route) & (data.metric == name)]
    if len(row) != 1:
        raise ValueError(f"Expected one row for {route}:{name}; found {len(row)}")
    return float(row.iloc[0].value)


def gate_label(ax: plt.Axes, x: float, number: int, label: str) -> None:
    ax.add_patch(
        Circle(
            (x, 0.235),
            0.0105,
            transform=ax.transAxes,
            facecolor=NAVY,
            edgecolor="white",
            linewidth=0.35,
            zorder=10,
        )
    )
    ax.text(x, 0.235, str(number), transform=ax.transAxes, ha="center",
            va="center", fontsize=5.0, fontweight="bold", color="white",
            zorder=11)
    ax.text(x, 0.207, label, transform=ax.transAxes, ha="center", va="top",
            fontsize=5.0, color=INK, zorder=10)


def hero_panel(fig: plt.Figure) -> None:
    ax = fig.add_axes([0.075, 0.325, 0.850, 0.588])
    image = Image.open(HERO)
    ax.imshow(image, interpolation="lanczos")
    ax.set_axis_off()

    fig.text(0.032, 0.970, "a", ha="left", va="top", fontsize=8.2,
             fontweight="bold", color="black")
    fig.text(
        0.067,
        0.970,
        "Falsification-gated knowledge borrowing into a sparse OOD recipient",
        ha="left",
        va="top",
        fontsize=7.3,
        fontweight="bold",
        color=INK,
    )

    # These headings sit in the deliberate white space of the generated asset.
    ax.text(0.155, 0.972, "Neighbouring experimental programmes",
            transform=ax.transAxes, ha="center", va="top", fontsize=5.5,
            fontweight="bold", color=INK)
    ax.text(0.536, 0.972, "Borrowing contract",
            transform=ax.transAxes, ha="center", va="top", fontsize=5.5,
            fontweight="bold", color=INK)
    ax.text(0.835, 0.972, "Sparse OOD recipient",
            transform=ax.transAxes, ha="center", va="top", fontsize=5.5,
            fontweight="bold", color=INK)

    gate_label(ax, 0.428, 1, "Inputs")
    gate_label(ax, 0.505, 2, "State")
    gate_label(ax, 0.574, 3, "Relation")
    gate_label(ax, 0.648, 4, "Falsifier")

    fig.text(
        0.500,
        0.300,
        "The database stays behind; only a qualified relation or candidate order crosses.",
        ha="center",
        va="center",
        fontsize=5.8,
        fontweight="bold",
        color=INK,
    )


def predict_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.plot([x - 0.018, x - 0.018, x + 0.022],
            [y + 0.025, y - 0.020, y - 0.020], color="#AAB5C0", lw=0.50)
    xx = np.linspace(0, 1, 30)
    yy = 0.15 + 0.70 / (1 + np.exp(-7 * (xx - 0.50)))
    ax.plot(x - 0.014 + 0.031 * xx, y - 0.017 + 0.038 * yy,
            color=TEAL, lw=1.05)
    ax.scatter([x - 0.010, x + 0.001, x + 0.013],
               [y - 0.006, y + 0.003, y + 0.013], s=7,
               facecolor=BLUE, edgecolor="white", lw=0.3, zorder=4)


def screen_icon(ax: plt.Axes, x: float, y: float) -> None:
    for i, (yy, colour) in enumerate(
        zip([0.020, -0.017, 0.006, -0.005], [TEAL, TEAL, ORANGE, ORANGE])
    ):
        ax.add_patch(Circle((x - 0.018, y + yy), 0.0047,
                            facecolor=colour, edgecolor="white", lw=0.3))
        target_y = [0.022, 0.006, -0.006, -0.022][i]
        ax.plot([x - 0.011, x + 0.013], [y + yy, y + target_y],
                color="#B4BEC8", lw=0.4)
        ax.add_patch(Circle((x + 0.018, y + target_y), 0.0047,
                            facecolor=colour, edgecolor="white", lw=0.3))


def abstain_icon(ax: plt.Axes, x: float, y: float) -> None:
    ax.plot([x - 0.020, x + 0.020], [y, y], color="#B5C0CA", lw=1.0)
    ax.plot([x - 0.005, x + 0.005], [y - 0.008, y + 0.008], color=CORAL, lw=1.0)
    ax.plot([x - 0.005, x + 0.005], [y + 0.008, y - 0.008], color=CORAL, lw=1.0)


def evidence_card(
    ax: plt.Axes,
    x: float,
    face: str,
    accent: str,
    title: str,
    hero: str,
    detail_1: str,
    detail_2: str,
    icon,
) -> None:
    width = 0.309
    card = FancyBboxPatch(
        (x, 0.08),
        width,
        0.78,
        boxstyle="round,pad=0.007,rounding_size=0.018",
        facecolor=face,
        edgecolor=GRID,
        linewidth=0.55,
    )
    ax.add_patch(card)
    ax.plot([x + 0.016, x + 0.016], [0.68, 0.81], color=accent,
            lw=3.0, solid_capstyle="round")
    icon(ax, x + 0.053, 0.742)
    ax.text(x + 0.088, 0.752, title, ha="left", va="center",
            fontsize=6.2, fontweight="bold", color=INK)
    ax.text(x + 0.023, 0.535, hero, ha="left", va="center",
            fontsize=7.1, fontweight="bold", color=INK)
    ax.text(x + 0.023, 0.330, detail_1, ha="left", va="center",
            fontsize=5.25, color=INK)
    ax.text(x + 0.023, 0.190, detail_2, ha="left", va="center",
            fontsize=5.0, color=MID)


def evidence_panel(fig: plt.Figure, data: pd.DataFrame) -> None:
    ax = fig.add_axes([0.035, 0.045, 0.930, 0.205])
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    fig.add_artist(Line2D([0.035, 0.965], [0.270, 0.270],
                          transform=fig.transFigure, color=GRID, lw=0.65))
    fig.text(0.032, 0.257, "b", ha="left", va="top", fontsize=8.2,
             fontweight="bold", color="black")
    fig.text(0.067, 0.257, "Decision-level evidence", ha="left", va="top",
             fontsize=6.6, fontweight="bold", color=INK)

    gain = metric(data, "predict", "relative_log_rmse_gain")
    r2 = metric(data, "predict", "raw_r2")
    rho_predict = metric(data, "predict", "spearman")
    evidence_card(
        ax, 0.005, PALE_TEAL, TEAL, "Predict",
        f"{gain:.2f}% lower log-RMSE",
        "external unseen-salt programme",
        rf"raw $R^2$ = {r2:.3f}  |  $\rho$ = {rho_predict:.3f}",
        predict_icon,
    )

    rho_rec = metric(data, "screen", "recipient_spearman")
    rho_borrow = metric(data, "screen", "borrowed_spearman")
    p_rec = metric(data, "screen", "recipient_precision_top_quartile")
    p_borrow = metric(data, "screen", "borrowed_precision_top_quartile")
    evidence_card(
        ax, 0.346, PALE_BLUE, BLUE, "Screen",
        rf"zero-label donor order $\rho$ = {rho_borrow:.3f}",
        rf"best five-label recipient: $\rho$ = {rho_rec:.3f}",
        f"top-quartile precision: {p_borrow:.3f} vs {p_rec:.3f}",
        screen_icon,
    )

    n_pass = int(metric(data, "abstain", "generic_edges_passed"))
    donor = metric(data, "abstain", "frozen_donor_score")
    recipient = metric(data, "abstain", "frozen_recipient_score")
    evidence_card(
        ax, 0.687, PALE_CORAL, CORAL, "Abstain",
        f"{n_pass}/40 generic edges pass",
        "complete OOD-repair gate",
        f"frozen donor {donor:.3f} < recipient {recipient:.3f}",
        abstain_icon,
    )


def build() -> None:
    if not HERO.exists():
        raise FileNotFoundError(HERO)
    data = pd.read_csv(DATA)
    # 183 x 132 mm, expressed in inches so the static validator can resolve it.
    fig = plt.figure(figsize=(7.204724, 5.196850), constrained_layout=False)
    hero_panel(fig)
    evidence_panel(fig, data)

    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0.0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0.0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0.0)
    fig.savefig(
        OUT.with_suffix(".tiff"),
        dpi=600,
        bbox_inches=None,
        pad_inches=0.0,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


if __name__ == "__main__":
    build()
