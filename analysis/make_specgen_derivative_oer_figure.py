"""Build Figure 3: controlled derivative-system OER relation transfer."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FIGURES = HERE / "figures"
OUTPUT = FIGURES / "specgen_derivative_oer_transfer"
SOURCE_DATA = RESULTS / "specgen_derivative_oer_figure_source_data.csv"

ZERO = RESULTS / "specgen_derivative_zero_label_metrics.csv"
COMPOSITION_NULL = RESULTS / "specgen_composition_secondary_shuffle.csv"
SPECTRAL_NULL = RESULTS / "specgen_derivative_shuffled_source_spearman.csv"
COMPOSITION_SUMMARY = RESULTS / "specgen_composition_secondary_summary.json"
TEMPORAL = RESULTS / "specgen_top20_temporal_metrics.csv"

# Palette: one neutral family, one signal family, and restrained route accents.
INK = "#25313A"
NAVY = "#315B7D"
TEAL = "#238A82"
TEAL_DARK = "#17675F"
TEAL_PALE = "#DDEDEA"
GREY = "#8B969E"
GREY_LIGHT = "#D9E0E4"
GREY_PALE = "#F2F5F6"
GOLD = "#C88A2B"
GOLD_PALE = "#F6E8CC"
RED = "#B64A4A"
RED_PALE = "#F3DADA"
GREEN = "#2D806B"
GREEN_PALE = "#DCECE6"

TARGETS = ["A", "B", "C", "D"]
TARGET_NAMES = {
    "A": "A  ligand",
    "B": "B  ligand",
    "C": "C  Mg→Fe",
    "D": "D  Cd→Mn",
}
ROUTES = {
    "A": "ranking only",
    "B": "predict + rank",
    "C": "reject",
    "D": "predict + rank",
}
ROUTE_COLORS = {
    "A": GOLD,
    "B": GREEN,
    "C": RED,
    "D": GREEN,
}
ROUTE_PALE = {
    "A": GOLD_PALE,
    "B": GREEN_PALE,
    "C": RED_PALE,
    "D": GREEN_PALE,
}


def configure_style() -> None:
    """Apply a compact, editable Nature-style plotting theme."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
    plt.rcParams["svg.fonttype"] = "none"
    mpl.rcParams.update(
        {
            "pdf.fonttype": 42,
            "font.size": 7.0,
            "axes.labelsize": 7.0,
            "axes.titlesize": 7.4,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.linewidth": 0.75,
            "legend.fontsize": 6.3,
            "legend.frameon": False,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )


def rounded_box(
    ax,
    xy: tuple[float, float],
    width: float,
    height: float,
    face: str,
    edge: str,
    title: str,
    body: str,
    title_color: str = INK,
) -> None:
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        linewidth=0.8,
        edgecolor=edge,
        facecolor=face,
        transform=ax.transAxes,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + 0.035 * width,
        xy[1] + 0.70 * height,
        title,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=7.0,
        fontweight="bold",
        color=title_color,
    )
    ax.text(
        xy[0] + 0.035 * width,
        xy[1] + 0.31 * height,
        body,
        transform=ax.transAxes,
        ha="left",
        va="center",
        fontsize=6.1,
        color=INK,
        linespacing=1.18,
    )


def add_arrow(ax, start, end, color=GREY, lw=1.0) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=lw,
            color=color,
            transform=ax.transAxes,
            connectionstyle="arc3,rad=0.0",
        )
    )


def style_quant_axis(ax, grid_axis="x") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color=GREY_LIGHT, lw=0.6, zorder=0)
    ax.set_axisbelow(True)


def get_metric(zero: pd.DataFrame, target: str, method: str, field: str) -> float:
    row = zero[(zero["target"] == target) & (zero["method"] == method)]
    if len(row) != 1:
        raise ValueError(f"Expected one {target}/{method} row")
    return float(row.iloc[0][field])


def build_source_data(
    zero: pd.DataFrame,
    comp_null: pd.DataFrame,
    spectral_null: pd.DataFrame,
    summary: dict,
    temporal: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict] = []
    for target in TARGETS:
        for method, null_frame in [
            ("composition_only_donor", comp_null),
            ("static_spectral_donor", spectral_null),
        ]:
            row = zero[
                (zero["target"] == target) & (zero["method"] == method)
            ].iloc[0]
            null_values = pd.to_numeric(null_frame[target], errors="raise")
            rows.append(
                {
                    "panel": "b",
                    "target": target,
                    "measure": method,
                    "estimate": float(row["spearman"]),
                    "ci95_low": np.nan,
                    "ci95_high": np.nan,
                    "null_q95": float(null_values.quantile(0.95)),
                    "holm_p": (
                        float(row["shuffled_holm_p"])
                        if pd.notna(row["shuffled_holm_p"])
                        and str(row["shuffled_holm_p"]).strip()
                        else float(summary["zero_label"][target]["shuffled_holm_p"])
                    ),
                    "n": 126,
                    "route": ROUTES[target],
                }
            )

        five = summary["five_label"][target]["candidate_bootstrap"]
        for measure in ["relative_rmse_gain", "spearman_gain"]:
            values = five[measure]
            rows.append(
                {
                    "panel": "c",
                    "target": target,
                    "measure": measure,
                    "estimate": float(values["point"]),
                    "ci95_low": float(values["ci95"][0]),
                    "ci95_high": float(values["ci95"][1]),
                    "null_q95": np.nan,
                    "holm_p": np.nan,
                    "n": 126,
                    "route": ROUTES[target],
                }
            )

        temp = temporal[temporal["target"] == target].iloc[0]
        rows.append(
            {
                "panel": "d",
                "target": target,
                "measure": "later_selected_candidates_spearman",
                "estimate": float(temp["spearman"]),
                "ci95_low": np.nan,
                "ci95_high": np.nan,
                "null_q95": np.nan,
                "holm_p": float(temp["permutation_holm_p"]),
                "n": 20,
                "route": ROUTES[target],
            }
        )
    return pd.DataFrame(rows)


def panel_a(ax) -> None:
    ax.set_axis_off()
    ax.set_title(
        "Complete-system OOD perturbations",
        loc="left",
        fontweight="bold",
        pad=6,
    )

    rounded_box(
        ax,
        (0.03, 0.70),
        0.38,
        0.22,
        "#E5EFF5",
        NAVY,
        "Donor · n = 462",
        "Co · Ni · Cu · Mg · Cd · Zn\nterephthalate · OER endpoint",
    )
    rounded_box(
        ax,
        (0.03, 0.38),
        0.38,
        0.20,
        TEAL_PALE,
        TEAL_DARK,
        "Borrow the relation",
        "composition → OER performance\nthen correct with 5 recipient labels",
    )
    add_arrow(ax, (0.22, 0.69), (0.22, 0.59), NAVY)

    recipient_specs = [
        ("A", "ligand → amino-terephthalate", 0.74),
        ("B", "ligand → tricarboxylate", 0.53),
        ("C", "metal slot Mg → Fe", 0.32),
        ("D", "metal slot Cd → Mn", 0.11),
    ]
    for target, change, y in recipient_specs:
        rounded_box(
            ax,
            (0.56, y),
            0.41,
            0.15,
            ROUTE_PALE[target],
            ROUTE_COLORS[target],
            f"{target} · n = 126 held out",
            change,
            ROUTE_COLORS[target],
        )
        add_arrow(ax, (0.42, 0.48), (0.555, y + 0.075), ROUTE_COLORS[target], 0.85)

    rounded_box(
        ax,
        (0.03, 0.06),
        0.38,
        0.17,
        GREY_PALE,
        GREY_LIGHT,
        "OOD unit",
        "complete derivative system\nsame endpoint + programme",
        NAVY,
    )


def panel_b(
    ax,
    zero: pd.DataFrame,
    comp_null: pd.DataFrame,
) -> None:
    x = np.arange(len(TARGETS), dtype=float)
    null_values = [pd.to_numeric(comp_null[t], errors="raise").to_numpy() for t in TARGETS]
    violin = ax.violinplot(
        null_values,
        positions=x,
        widths=0.58,
        showmeans=False,
        showmedians=False,
        showextrema=False,
    )
    for body in violin["bodies"]:
        body.set_facecolor(GREY_LIGHT)
        body.set_edgecolor("none")
        body.set_alpha(0.8)

    spectral = [
        get_metric(zero, target, "static_spectral_donor", "spearman")
        for target in TARGETS
    ]
    composition = [
        get_metric(zero, target, "composition_only_donor", "spearman")
        for target in TARGETS
    ]
    ax.scatter(
        x - 0.10,
        spectral,
        marker="s",
        s=26,
        facecolor="white",
        edgecolor=GREY,
        linewidth=1.0,
        zorder=4,
        label="720-feature spectral donor",
    )
    ax.scatter(
        x + 0.10,
        composition,
        marker="o",
        s=32,
        facecolor=TEAL,
        edgecolor="white",
        linewidth=0.7,
        zorder=5,
        label="6-slot composition donor",
    )
    for xi, value, target in zip(x + 0.10, composition, TARGETS):
        ax.text(
            xi,
            value + 0.055,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=5.7,
            color=TEAL_DARK,
            fontweight="bold",
        )

    ax.axhline(0, color=GREY, lw=0.7)
    ax.axhline(0.30, color=GOLD, lw=0.9, ls=(0, (3, 2)))
    ax.text(
        3.48,
        0.315,
        "practical rank gate",
        ha="right",
        va="bottom",
        fontsize=5.8,
        color=GOLD,
    )
    ax.set_xticks(x, TARGETS)
    ax.tick_params(axis="x", rotation=0, length=0)
    ax.set_ylabel("Zero-label Spearman ρ")
    ax.set_ylim(-0.36, 0.93)
    ax.set_title(
        "Composition relation transfers before spectra",
        loc="left",
        fontweight="bold",
        pad=6,
    )
    style_quant_axis(ax, "y")
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="s",
                linestyle="none",
                markerfacecolor="white",
                markeredgecolor=GREY,
                label="spectral donor",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=TEAL,
                markeredgecolor="white",
                label="composition donor",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markerfacecolor=GREY_LIGHT,
                markeredgecolor="none",
                markersize=8,
                label="500 shuffled-source fits",
            ),
        ],
        loc="upper left",
        ncol=1,
        handletextpad=0.45,
        borderaxespad=0.1,
    )


def forest_metric(
    ax,
    summary: dict,
    measure: str,
    title: str,
    xlabel: str,
    xlim: tuple[float, float],
    show_ylabels: bool,
    scale: float = 1.0,
) -> None:
    y = np.arange(len(TARGETS))[::-1]
    ax.axvspan(0, xlim[1], color=GREEN_PALE, alpha=0.35, zorder=0)
    ax.axvline(0, color=GREY, lw=0.85, ls=(0, (3, 2)), zorder=1)
    for target, yi in zip(TARGETS, y):
        values = summary["five_label"][target]["candidate_bootstrap"][measure]
        estimate = scale * float(values["point"])
        lo, hi = [scale * float(value) for value in values["ci95"]]
        color = ROUTE_COLORS[target]
        ax.plot([lo, hi], [yi, yi], color=color, lw=1.8, zorder=3)
        ax.scatter(
            estimate,
            yi,
            s=31,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=4,
        )
        label = f"{estimate:+.1f}%" if measure == "relative_rmse_gain" else f"{estimate:+.3f}"
        offset = 0.018 * (xlim[1] - xlim[0])
        ax.text(
            min(hi + offset, xlim[1] - 0.01 * (xlim[1] - xlim[0])),
            yi,
            label,
            ha="left",
            va="center",
            fontsize=5.9,
            color=color,
            fontweight="bold",
        )

    ax.set_yticks(y)
    if show_ylabels:
        ax.set_yticklabels([TARGET_NAMES[t] for t in TARGETS])
    else:
        ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(*xlim)
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left", fontweight="bold", pad=6)
    style_quant_axis(ax, "x")


def panel_d(ax, temporal: pd.DataFrame) -> None:
    x = np.arange(len(TARGETS), dtype=float)
    values = [
        float(temporal.loc[temporal["target"] == target, "spearman"].iloc[0])
        for target in TARGETS
    ]
    pvals = [
        float(
            temporal.loc[
                temporal["target"] == target, "permutation_holm_p"
            ].iloc[0]
        )
        for target in TARGETS
    ]
    ax.axhspan(0.30, 0.85, color=GREEN_PALE, alpha=0.35, zorder=0)
    ax.axhline(0.30, color=GOLD, lw=0.9, ls=(0, (3, 2)))
    for xi, value, pvalue, target in zip(x, values, pvals, TARGETS):
        ax.scatter(
            xi,
            value,
            s=42,
            facecolor="white",
            edgecolor=ROUTE_COLORS[target],
            linewidth=1.5,
            zorder=3,
        )
        ax.text(
            xi,
            value + 0.055,
            f"ρ={value:.2f}\n$p_{{H}}$={pvalue:.3f}",
            ha="center",
            va="bottom",
            fontsize=5.8,
            color=ROUTE_COLORS[target],
            linespacing=1.05,
        )
    ax.set_xticks(x, TARGETS)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0.20, 0.80)
    ax.set_ylabel("Spearman ρ")
    ax.set_title(
        "Later selected candidates test rank retention",
        loc="left",
        fontweight="bold",
        pad=6,
    )
    style_quant_axis(ax, "y")
    ax.text(
        0.99,
        0.02,
        "Corroboration only: candidates were preselected;\nC rank recovery does not repair full-grid prediction.",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=5.7,
        color=GREY,
        linespacing=1.15,
    )


def main() -> None:
    configure_style()
    FIGURES.mkdir(parents=True, exist_ok=True)

    zero = pd.read_csv(ZERO)
    comp_null = pd.read_csv(COMPOSITION_NULL)
    spectral_null = pd.read_csv(SPECTRAL_NULL)
    summary = json.loads(COMPOSITION_SUMMARY.read_text(encoding="utf-8"))
    temporal = pd.read_csv(TEMPORAL)

    source = build_source_data(zero, comp_null, spectral_null, summary, temporal)
    source.to_csv(SOURCE_DATA, index=False)

    # RSC double-column width: 17.1 cm.
    fig = plt.figure(figsize=(6.73, 5.00), constrained_layout=False)
    outer = fig.add_gridspec(
        2,
        2,
        width_ratios=[1.00, 1.36],
        height_ratios=[1.02, 1.0],
        left=0.075,
        right=0.985,
        bottom=0.105,
        top=0.955,
        wspace=0.34,
        hspace=0.48,
    )
    ax_a = fig.add_subplot(outer[0, 0])
    ax_b = fig.add_subplot(outer[1, 0])
    cgrid = outer[0, 1].subgridspec(1, 2, width_ratios=[1.05, 0.95], wspace=0.43)
    ax_c1 = fig.add_subplot(cgrid[0, 0])
    ax_c2 = fig.add_subplot(cgrid[0, 1])
    ax_d = fig.add_subplot(outer[1, 1])

    panel_a(ax_a)
    panel_b(ax_b, zero, comp_null)
    forest_metric(
        ax_c1,
        summary,
        "relative_rmse_gain",
        "Five-label RMSE gain (%)",
        "",
        (-20, 39),
        True,
        100.0,
    )
    forest_metric(
        ax_c2,
        summary,
        "spearman_gain",
        "Five-label Spearman gain",
        "",
        (-0.02, 0.62),
        False,
    )
    panel_d(ax_d, temporal)

    # Panel labels follow the reading order; c spans the paired forest plots.
    for ax, label, x, y in [
        (ax_a, "a", -0.08, 1.045),
        (ax_b, "b", -0.08, 1.045),
        (ax_c1, "c", -0.16, 1.045),
        (ax_d, "d", -0.07, 1.045),
    ]:
        ax.text(
            x,
            y,
            label,
            transform=ax.transAxes,
            fontsize=8.5,
            fontweight="bold",
            ha="left",
            va="bottom",
            color=INK,
        )

    # Route strip for the hero panel.
    route_y = 0.545
    starts = [0.49, 0.615, 0.74, 0.865]
    for target, start in zip(TARGETS, starts):
        fig.text(
            start,
            route_y,
            f"{target}  {ROUTES[target]}",
            ha="center",
            va="center",
            fontsize=5.8,
            fontweight="bold",
            color=ROUTE_COLORS[target],
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": ROUTE_PALE[target],
                "edgecolor": "none",
            },
        )

    for suffix, kwargs in [
        ("svg", {}),
        ("pdf", {}),
        ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}}),
        ("png", {"dpi": 300}),
    ]:
        fig.savefig(
            OUTPUT.with_suffix(f".{suffix}"),
            facecolor="white",
            **kwargs,
        )
    plt.close(fig)

    print(
        json.dumps(
            {
                "status": "complete",
                "source_data": str(SOURCE_DATA),
                "outputs": [
                    str(OUTPUT.with_suffix(f".{suffix}"))
                    for suffix in ["svg", "pdf", "tiff", "png"]
                ],
                "figure_size_inches": [6.73, 5.00],
                "decisions": ROUTES,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
