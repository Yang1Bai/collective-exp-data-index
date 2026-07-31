"""Create the cross-database electrolyte-ranking manuscript figure."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FIGURES = HERE / "figures"
PREFIX = "bamboomixer_cross_database_interaction"
STRESS = RESULTS / "bamboomixer_recipient_baseline_stress_test_metrics.csv"
ANCHORS = RESULTS / f"{PREFIX}_solventseg_anchor_metrics.csv"
BOOTSTRAP = RESULTS / f"{PREFIX}_solventseg_bootstrap.csv"
FINALES = RESULTS / f"{PREFIX}_finales_metrics.csv"
SUMMARY = RESULTS / f"{PREFIX}_summary.json"
OUTPUT = FIGURES / "cross_database_electrolyte_ranking"


NAVY = "#2B4C7E"
TEAL = "#0B8A8F"
LIGHT_TEAL = "#88C9C6"
ORANGE = "#D98C3F"
RED = "#C75B5B"
GREY = "#8E99A6"
LIGHT_GREY = "#E8ECEF"
DARK = "#263238"


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)


def interval(values: pd.Series) -> tuple[float, float]:
    return float(values.quantile(0.025)), float(values.quantile(0.975))


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.12,
        1.08,
        label,
        transform=axis.transAxes,
        fontsize=9,
        fontweight="bold",
        va="top",
    )


def draw_source_card(
    axis: plt.Axes,
    x: float,
    y: float,
    title: str,
    count: str,
    color: str,
) -> None:
    axis.add_patch(
        mpl.patches.FancyBboxPatch(
            (x, y),
            0.29,
            0.16,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            facecolor=color,
            edgecolor="none",
            alpha=0.16,
        )
    )
    axis.text(x + 0.02, y + 0.105, title, color=DARK, fontweight="bold")
    axis.text(x + 0.02, y + 0.045, count, color=DARK, fontsize=6.5)


def model_label(name: str) -> str:
    replacements = {
        "programme_balanced_source_portfolio": "Source portfolio",
        "recipient_oracle": "Recipient oracle",
        "recipient_rank_ensemble": "Recipient rank ensemble",
        "rbf_kernel_ridge_alpha_10": "RBF kernel ridge, α=10",
        "rbf_kernel_ridge_alpha_1": "RBF kernel ridge, α=1",
        "rbf_kernel_ridge_alpha_0.1": "RBF kernel ridge, α=0.1",
        "random_forest": "Random forest",
        "extra_trees": "Extra trees",
        "ridge_alpha_0.1": "Ridge, α=0.1",
        "ridge_alpha_1": "Ridge, α=1",
        "ridge_alpha_10": "Ridge, α=10",
        "ridge_alpha_100": "Ridge, α=100",
        "knn_1": "1-nearest neighbour",
        "knn_3": "3-nearest neighbours",
        "knn_5": "5-nearest neighbours",
    }
    return replacements[name]


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    stress = pd.read_csv(STRESS)
    anchors = pd.read_csv(ANCHORS)
    bootstrap = pd.read_csv(BOOTSTRAP)
    finales = pd.read_csv(FINALES)
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))

    primary = stress[stress["anchor_budget"].eq(5)].copy()
    source = primary[
        primary["model"].eq("programme_balanced_source_portfolio")
    ].set_index("draw")
    recipient = primary[
        ~primary["model"].eq("programme_balanced_source_portfolio")
    ]
    oracle = (
        recipient.groupby("draw", as_index=False)["spearman"]
        .max()
        .assign(model="recipient_oracle")
    )
    plot_models = pd.concat(
        [
            primary[["draw", "model", "spearman"]],
            oracle[["draw", "model", "spearman"]],
        ],
        ignore_index=True,
    )
    order = (
        plot_models.groupby("model")["spearman"]
        .mean()
        .sort_values()
        .index.tolist()
    )

    figure = plt.figure(figsize=(7.2047, 5.20), constrained_layout=False)
    grid = figure.add_gridspec(
        1,
        2,
        width_ratios=[0.92, 1.38],
        left=0.055,
        right=0.985,
        bottom=0.10,
        top=0.89,
        wspace=0.38,
    )
    left = grid[0, 0].subgridspec(
        3,
        1,
        height_ratios=[1.05, 0.82, 0.72],
        hspace=0.66,
    )
    axis_a = figure.add_subplot(left[0, 0])
    axis_c = figure.add_subplot(left[1, 0])
    axis_d = figure.add_subplot(left[2, 0])
    axis_b = figure.add_subplot(grid[0, 1])

    # a, source construction and overlap boundary
    axis_a.set_axis_off()
    panel_label(axis_a, "a")
    axis_a.set_title(
        "Equal-programme source construction",
        loc="left",
        pad=7,
        fontweight="bold",
    )
    draw_source_card(axis_a, 0.00, 0.69, "BambooMixer", "10,012 rows*", NAVY)
    draw_source_card(axis_a, 0.355, 0.69, "CALiSol", "410 rows", ORANGE)
    draw_source_card(axis_a, 0.71, 0.69, "KIT", "1,089 rows", TEAL)
    axis_a.text(
        0.50,
        0.57,
        "separate models  →  equal programme weight",
        ha="center",
        color=DARK,
        fontsize=6.5,
    )
    axis_a.annotate(
        "",
        xy=(0.50, 0.51),
        xytext=(0.50, 0.61),
        arrowprops={"arrowstyle": "-|>", "lw": 1.1, "color": GREY},
    )
    axis_a.add_patch(
        mpl.patches.FancyBboxPatch(
            (0.24, 0.31),
            0.50,
            0.17,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            facecolor=LIGHT_TEAL,
            edgecolor=TEAL,
            linewidth=0.9,
            alpha=0.30,
        )
    )
    axis_a.text(
        0.50,
        0.410,
        "SolventSeg recipient",
        ha="center",
        va="center",
        color=DARK,
        fontweight="bold",
    )
    axis_a.text(
        0.50,
        0.350,
        "180 measurements · 36 formulations",
        ha="center",
        va="center",
        color=DARK,
        fontsize=6.5,
    )
    axis_a.text(
        0.00,
        0.00,
        "Source–target record overlap: 0\n"
        "BambooMixer–CALiSol overlap: 71 (disclosed)\n"
        "*complete target family removed",
        color=DARK,
        fontsize=5.9,
        va="bottom",
    )

    # b, hero recipient stress test
    panel_label(axis_b, "b")
    axis_b.set_title(
        "Neighbour knowledge exceeds recipient-only learning at five labels",
        loc="left",
        pad=7,
        fontweight="bold",
    )
    for position, name in enumerate(order):
        values = plot_models.loc[
            plot_models["model"].eq(name), "spearman"
        ]
        low, high = interval(values)
        mean = float(values.mean())
        color = (
            TEAL
            if name == "programme_balanced_source_portfolio"
            else ORANGE
            if name == "recipient_oracle"
            else GREY
        )
        axis_b.plot([low, high], [position, position], color=color, lw=2.0)
        axis_b.scatter(
            mean,
            position,
            s=26 if name == "programme_balanced_source_portfolio" else 17,
            color=color,
            edgecolor="white",
            linewidth=0.45,
            zorder=3,
        )
    axis_b.axvline(0, color=LIGHT_GREY, lw=0.8)
    axis_b.set_yticks(range(len(order)))
    axis_b.set_yticklabels([model_label(name) for name in order])
    axis_b.set_xlabel("Spearman candidate-order correlation")
    axis_b.set_xlim(-0.20, 1.01)
    axis_b.grid(axis="x", color=LIGHT_GREY, lw=0.6)
    axis_b.tick_params(axis="y", length=0)
    axis_b.text(
        0.94,
        len(order) - 1,
        "0.910",
        color=TEAL,
        ha="left",
        va="center",
        fontweight="bold",
    )
    axis_b.text(
        0.56,
        order.index("rbf_kernel_ridge_alpha_10"),
        "0.537",
        color=DARK,
        va="center",
    )
    axis_b.text(
        0.98,
        -0.095,
        "points: mean; bars: 2.5th–97.5th percentiles, n=100 anchor selections",
        transform=axis_b.transAxes,
        ha="right",
        fontsize=6.2,
        color=DARK,
    )

    # c, paired source advantages
    panel_label(axis_c, "c")
    axis_c.set_title(
        "Paired ranking advantage",
        loc="left",
        pad=7,
        fontweight="bold",
    )
    strongest = recipient[
        recipient["model"].eq("rbf_kernel_ridge_alpha_10")
    ].set_index("draw")
    broad = anchors[
        anchors["anchor_budget"].eq(5)
        & anchors["model"].eq("bamboo_all_frozen")
    ].set_index("draw")
    source_formal = anchors[
        anchors["anchor_budget"].eq(5)
        & anchors["model"].eq("programme_balanced_portfolio_frozen")
    ].set_index("draw")
    differences = [
        source["spearman"] - strongest["spearman"],
        source["spearman"] - oracle.set_index("draw")["spearman"],
        source_formal["spearman"] - broad["spearman"],
    ]
    labels = [
        "vs strongest\nrecipient",
        "vs recipient\noracle",
        "vs broad\nsingle donor",
    ]
    colors = [TEAL, NAVY, ORANGE]
    for position, (values, color) in enumerate(zip(differences, colors)):
        low, high = interval(values)
        mean = float(values.mean())
        axis_c.plot([position, position], [low, high], color=color, lw=2.0)
        axis_c.scatter(
            position,
            mean,
            s=28,
            color=color,
            edgecolor="white",
            linewidth=0.45,
            zorder=3,
        )
        axis_c.text(
            position,
            high + 0.028,
            f"{mean:+.3f}",
            ha="center",
            color=color,
            fontweight="bold",
            fontsize=6.5,
        )
    axis_c.axhline(0, color=DARK, lw=0.8)
    axis_c.set_xticks(range(3))
    axis_c.set_xticklabels(labels)
    axis_c.set_ylabel(r"$\Delta$ Spearman $\rho$")
    axis_c.set_ylim(-0.05, 0.64)
    axis_c.grid(axis="y", color=LIGHT_GREY, lw=0.6)

    # d, routing and external boundary
    panel_label(axis_d, "d")
    axis_d.set_title(
        "Routing and programme boundary",
        loc="left",
        pad=5,
        fontweight="bold",
    )
    contrasts = summary["solventseg"]["routing"]["prediction_gate"]
    rmse_values = [
        contrasts["portfolio_vs_state_relative_log_rmse_gain"] * 100,
        contrasts["portfolio_vs_permuted_relative_log_rmse_gain"] * 100,
    ]
    rmse_intervals = [
        np.asarray(
            contrasts["portfolio_vs_state_relative_log_rmse_gain_ci95"]
        )
        * 100,
        np.asarray(
            contrasts["portfolio_vs_permuted_relative_log_rmse_gain_ci95"]
        )
        * 100,
    ]
    for position, (value, bounds) in enumerate(
        zip(rmse_values, rmse_intervals)
    ):
        axis_d.plot(bounds, [position, position], color=RED, lw=1.8)
        axis_d.scatter(value, position, color=RED, s=20, zorder=3)
    axis_d.axvline(0, color=DARK, lw=0.8)
    axis_d.set_yticks([0, 1])
    axis_d.set_yticklabels(["vs state-only", "vs permuted"])
    axis_d.set_xlabel("Relative log-RMSE gain (%)")
    axis_d.set_xlim(-50, 35)
    axis_d.grid(axis="x", color=LIGHT_GREY, lw=0.6)
    axis_d.text(
        0.99,
        0.97,
        "absolute prediction: abstain",
        transform=axis_d.transAxes,
        ha="right",
        va="top",
        color=RED,
        fontweight="bold",
        fontsize=6.4,
    )
    finales_scope = "multitask_2023_11|evaluation"
    finales_rows = finales[finales["scope"].eq(finales_scope)].set_index("model")
    source_finales = float(
        finales_rows.loc["programme_balanced_portfolio", "spearman"]
    )
    target_finales = float(finales_rows.loc["target_linear", "spearman"])
    axis_d.text(
        0.99,
        0.48,
        f"FINALES full pool: source {source_finales:.3f} < "
        f"target {target_finales:.3f}  →  abstain",
        transform=axis_d.transAxes,
        ha="right",
        va="center",
        color=DARK,
        fontsize=5.8,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 1.5},
    )

    figure.suptitle(
        "Neighbouring electrolyte programmes transfer candidate order, not calibration",
        x=0.055,
        y=0.975,
        ha="left",
        fontsize=10,
        fontweight="bold",
        color=DARK,
    )
    figure.savefig(f"{OUTPUT}.svg", bbox_inches="tight")
    figure.savefig(f"{OUTPUT}.pdf", bbox_inches="tight")
    figure.savefig(f"{OUTPUT}.png", dpi=300, bbox_inches="tight")
    figure.savefig(
        f"{OUTPUT}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)


if __name__ == "__main__":
    main()
