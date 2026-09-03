"""Build the submission-grade state-matched MPEA borrowing figure."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
from scipy import stats


HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
FIGURES = HERE / "figures"
BOOTSTRAP = RESULTS / "state_matched_mpea_balam_v2_bootstrap_summary.json"
SCREEN = RESULTS / "state_matched_mpea_balam_v2_summary.json"
METRICS = RESULTS / "state_matched_mpea_balam_v2_screen.csv"
SOURCE_DATA = RESULTS / "state_matched_mpea_figure_source_data.csv"
OUTPUT = FIGURES / "state_matched_mpea_borrowing"

NAVY = "#315B7D"
TEAL = "#2A8C82"
TEAL_DARK = "#17675F"
GOLD = "#D49A3A"
GREY = "#9BA6AF"
LIGHT_GREY = "#E9EEF1"
RED = "#B64A4A"
TEXT = "#25313A"


def box(ax, xy, width, height, text, face, edge, size=7.0):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.015,rounding_size=0.025",
        linewidth=0.8,
        edgecolor=edge,
        facecolor=face,
        transform=ax.transAxes,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        color=TEXT,
        transform=ax.transAxes,
        linespacing=1.15,
    )


def arrow(ax, start, end, color=GREY):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=1.0,
            color=color,
            transform=ax.transAxes,
        )
    )


def interval_from_runs(values: np.ndarray) -> tuple[float, float, float]:
    mean = float(np.mean(values))
    sem = float(stats.sem(values))
    critical = float(stats.t.ppf(0.975, len(values) - 1))
    return mean, mean - critical * sem, mean + critical * sem


def forest(ax, labels, means, lows, highs, colors, xlim, title):
    y = np.arange(len(labels))[::-1]
    ax.axvline(0, color="#6D7880", lw=0.8, ls=(0, (2, 2)), zorder=0)
    for index, position in enumerate(y):
        ax.errorbar(
            means[index],
            position,
            xerr=np.array(
                [[means[index] - lows[index]], [highs[index] - means[index]]]
            ),
            fmt="o",
            ms=5.2,
            mfc=colors[index],
            mec="white",
            mew=0.7,
            ecolor=colors[index],
            elinewidth=1.7,
            capsize=2.5,
            zorder=3,
        )
        ax.text(
            highs[index] + (xlim[1] - xlim[0]) * 0.025,
            position,
            f"{means[index]:+.1f}%",
            va="center",
            fontsize=6.8,
            color=TEXT,
        )
    ax.set_yticks(y, labels)
    ax.set_xlim(*xlim)
    ax.set_xlabel("Relative RMSE gain (%)")
    ax.set_title(title, loc="left", fontweight="bold", pad=7)
    ax.grid(axis="x", color=LIGHT_GREY, lw=0.7)
    ax.set_axisbelow(True)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    bootstrap = json.loads(BOOTSTRAP.read_text(encoding="utf-8"))
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    metrics = pd.read_csv(METRICS)
    summary = pd.DataFrame(screen["summaries"])

    obs = bootstrap["observed"]
    ci = bootstrap["bootstrap_ci95"]
    primary = {
        "real_q1": (
            100 * obs["real_q1"]["relative_rmse_gain"],
            100 * ci["real_q1_gain"][0],
            100 * ci["real_q1_gain"][1],
        ),
        "real_q4": (
            100 * obs["real_q4"]["relative_rmse_gain"],
            100 * ci["real_q4_gain"][0],
            100 * ci["real_q4_gain"][1],
        ),
        "shuffled_q4": (
            100 * obs["shuffled_q4"]["relative_rmse_gain"],
            100 * ci["shuffled_q4_gain"][0],
            100 * ci["shuffled_q4_gain"][1],
        ),
        "q4_minus_q1": (
            100 * obs["q4_minus_q1_gain"],
            100 * ci["q4_minus_q1_gain"][0],
            100 * ci["q4_minus_q1_gain"][1],
        ),
        "real_minus_shuffled": (
            100 * obs["real_minus_shuffled_q4_gain"],
            100 * ci["real_minus_shuffled_q4_gain"][0],
            100 * ci["real_minus_shuffled_q4_gain"][1],
        ),
    }

    state_q4 = summary[
        (summary["method"] == "state_only") & (summary["scope"] == "q4")
    ].iloc[0]
    state_ladder = (
        100 * float(state_q4["mean_relative_rmse_gain"]),
        100 * float(state_q4["ci95"][0]),
        100 * float(state_q4["ci95"][1]),
    )
    ceiling_runs = metrics[
        (metrics["method"] == "measured_uts_residual_ceiling")
        & (metrics["scope"] == "q4")
    ]["relative_rmse_gain"].to_numpy(float)
    ceiling = tuple(100 * value for value in interval_from_runs(ceiling_runs))

    source_rows = []
    for name, values in primary.items():
        source_rows.append(
            {
                "panel": "f_or_g",
                "contrast": name,
                "mean_percent": values[0],
                "ci95_low_percent": values[1],
                "ci95_high_percent": values[2],
                "interval": "two-way cluster bootstrap",
            }
        )
    for name, values, interval_name in [
        ("composition_to_planned_state_q4", state_ladder, "descriptive t interval"),
        ("planned_state_to_predicted_uts_q4", primary["real_q4"], "two-way cluster bootstrap"),
        ("planned_state_to_measured_uts_q4", ceiling, "descriptive t interval"),
    ]:
        source_rows.append(
            {
                "panel": "h",
                "contrast": name,
                "mean_percent": values[0],
                "ci95_low_percent": values[1],
                "ci95_high_percent": values[2],
                "interval": interval_name,
            }
        )
    pd.DataFrame(source_rows).to_csv(SOURCE_DATA, index=False)

    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 7,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
        }
    )
    fig = plt.figure(figsize=(7.20, 4.38), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        3,
        width_ratios=[1.18, 1.0, 1.05],
        height_ratios=[1.0, 1.0],
        left=0.055,
        right=0.985,
        bottom=0.13,
        top=0.94,
        wspace=0.55,
        hspace=0.64,
    )
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1:])
    ax_c = fig.add_subplot(grid[1, 1])
    ax_d = fig.add_subplot(grid[1, 2])

    # Panel a: information contract.
    ax_a.set_axis_off()
    ax_a.set_title("State-matched borrowing contract", loc="left", fontweight="bold", pad=7)
    box(
        ax_a,
        (0.05, 0.81),
        0.90,
        0.12,
        "Raw experimental records\ncomposition + process + phase + test state",
        "#EDF4F8",
        NAVY,
    )
    arrow(ax_a, (0.50, 0.81), (0.50, 0.72), NAVY)
    box(
        ax_a,
        (0.05, 0.59),
        0.90,
        0.12,
        "Hold out entire elemental systems\n59 evaluation systems",
        "#F4F6F7",
        GREY,
    )
    arrow(ax_a, (0.50, 0.59), (0.50, 0.50), NAVY)
    box(
        ax_a,
        (0.05, 0.36),
        0.42,
        0.13,
        "UTS donor\nexclude held-out and\nevaluation systems",
        "#E7F4F1",
        TEAL,
        5.8,
    )
    box(
        ax_a,
        (0.53, 0.36),
        0.42,
        0.13,
        "YS recipient\n60 target labels\nstate-aware features",
        "#EDF4F8",
        NAVY,
        5.8,
    )
    arrow(ax_a, (0.27, 0.36), (0.42, 0.26), TEAL)
    arrow(ax_a, (0.74, 0.36), (0.58, 0.26), NAVY)
    box(
        ax_a,
        (0.18, 0.12),
        0.64,
        0.13,
        "Cross-fitted UTS prediction\nappend only after leakage audit",
        "#E7F4F1",
        TEAL_DARK,
        6.0,
    )
    ax_a.text(
        0.50,
        0.035,
        "Same contract for real and shuffled donor",
        ha="center",
        va="center",
        fontsize=6.4,
        color="#59666F",
        transform=ax_a.transAxes,
    )

    forest(
        ax_b,
        ["Real UTS vs state", "Matched shuffled vs state", "Real − shuffled"],
        [primary["real_q4"][0], primary["shuffled_q4"][0], primary["real_minus_shuffled"][0]],
        [primary["real_q4"][1], primary["shuffled_q4"][1], primary["real_minus_shuffled"][1]],
        [primary["real_q4"][2], primary["shuffled_q4"][2], primary["real_minus_shuffled"][2]],
        [TEAL, GREY, TEAL_DARK],
        (-4, 17),
        "Q4 gain is source-specific (R$^2$ = 0.103)",
    )
    ax_b.text(
        0.99,
        1.015,
        "two-way cluster bootstrap: 59 systems × 60 runs",
        ha="right",
        va="bottom",
        transform=ax_b.transAxes,
        fontsize=5.9,
        color="#65717A",
    )

    forest(
        ax_c,
        ["Q1", "Q4", "Q4 − Q1"],
        [primary["real_q1"][0], primary["real_q4"][0], primary["q4_minus_q1"][0]],
        [primary["real_q1"][1], primary["real_q4"][1], primary["q4_minus_q1"][1]],
        [primary["real_q1"][2], primary["real_q4"][2], primary["q4_minus_q1"][2]],
        [NAVY, TEAL, GOLD],
        (-6, 17),
        "Benefit persists in OOD",
    )

    labels = ["State-aware\nfeatures", "Predicted\nUTS", "Measured UTS\n(ceiling)"]
    ladder = [state_ladder, primary["real_q4"], ceiling]
    colors = [NAVY, TEAL, GOLD]
    x = np.arange(3)
    means = np.array([item[0] for item in ladder])
    lower = means - np.array([item[1] for item in ladder])
    upper = np.array([item[2] for item in ladder]) - means
    ax_d.bar(x, means, width=0.62, color=colors, edgecolor="white", linewidth=0.6)
    ax_d.errorbar(
        x,
        means,
        yerr=np.vstack([lower, upper]),
        fmt="none",
        ecolor=TEXT,
        elinewidth=1.0,
        capsize=2.4,
    )
    for position, mean in zip(x, means):
        ax_d.text(position, mean + 2.1, f"{mean:.1f}%", ha="center", fontsize=6.8)
    ax_d.set_xticks(x, labels)
    ax_d.set_ylabel("Q4 relative RMSE gain (%)")
    ax_d.set_ylim(0, max(56, ceiling[2] + 5))
    ax_d.set_title("Neighboring information has headroom", loc="left", fontweight="bold", pad=7)
    ax_d.grid(axis="y", color=LIGHT_GREY, lw=0.7)
    ax_d.set_axisbelow(True)
    ax_d.spines[["top", "right"]].set_visible(False)
    ax_d.tick_params(axis="x", length=0)
    ax_d.tick_params(axis="x", labelsize=5.7, pad=3)

    for label, ax in zip(("e", "f", "g", "h"), (ax_a, ax_b, ax_c, ax_d)):
        ax.text(
            -0.12,
            1.06,
            label,
            transform=ax.transAxes,
            fontsize=9,
            fontweight="bold",
            va="top",
            color="#111820",
        )

    fig.savefig(OUTPUT.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(OUTPUT.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
