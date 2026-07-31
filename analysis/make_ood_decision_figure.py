"""Create the publication OOD screening-versus-discovery figure."""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, RESULTS, ensure_output_dirs


plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7.1,
        "axes.labelsize": 7.2,
        "axes.titlesize": 8.1,
        "axes.titleweight": "bold",
        "axes.linewidth": 0.7,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.3,
        "legend.frameon": False,
        "axes.spines.right": False,
        "axes.spines.top": False,
    }
)

TEAL = "#238B82"
TEAL_LIGHT = "#8CC9C3"
ORANGE = "#D9822B"
RED = "#B64342"
GRAY = "#777777"
LIGHT_GRAY = "#D7D7D7"
BLACK = "#252525"


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.16,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=9.5,
        fontweight="bold",
        va="bottom",
    )


def parse_interval(value: str | list[float]) -> list[float]:
    return json.loads(value) if isinstance(value, str) else value


def screening_frame() -> pd.DataFrame:
    official = pd.read_csv(RESULTS / "ood_decision_edges.csv")
    hard = pd.read_csv(RESULTS / "hard_ood_decision_edges.csv")
    official_row = official[
        official["edge_id"]
        == "obelix_official_thermoelectric_zt_to_ionic_conductivity"
    ].iloc[0]
    hard_row = hard[
        hard["edge_id"]
        == "hard_ood_obelix_thermoelectric_zt_to_ionic_conductivity"
    ].iloc[0]
    rows = []
    for scope, label, status, row in (
        ("official_test", "Official test", "directional", official_row),
        ("hard_ood_40pct", "Hard OOD 40%", "exploratory", hard_row),
    ):
        interval = parse_interval(row["effect_fraction_to_first_hit_bootstrap_95"])
        rows.append(
            {
                "scope": scope,
                "label": label,
                "status": status,
                "baseline_percent": 100
                * float(row["baseline_fraction_to_first_hit_mean"]),
                "prior_percent": 100
                * float(row["augmented_fraction_to_first_hit_mean"]),
                "saved_percentage_points": 100
                * float(row["effect_fraction_to_first_hit_mean"]),
                "saved_ci_lo": 100 * float(interval[0]),
                "saved_ci_hi": 100 * float(interval[1]),
                "relative_saved_percent": 100
                * float(row["relative_reduction_fraction_to_first_hit"]),
                "decision_status": row["decision_status"],
            }
        )
    return pd.DataFrame(rows)


def panel_a(ax) -> None:
    frame = screening_frame()
    frame.to_csv(RESULTS / "figure_ood_decision_panel_a.csv", index=False)
    y = np.array([1.0, 0.0])
    for yi, row in zip(y, frame.to_dict("records")):
        ax.plot(
            [row["prior_percent"], row["baseline_percent"]],
            [yi, yi],
            color=LIGHT_GRAY,
            lw=2.2,
            zorder=1,
        )
        ax.scatter(
            row["baseline_percent"], yi, s=28, color=GRAY, zorder=2
        )
        ax.scatter(
            row["prior_percent"],
            yi,
            s=34,
            color=TEAL,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.annotate(
            "",
            xy=(row["prior_percent"], yi),
            xytext=(row["baseline_percent"], yi),
            arrowprops={"arrowstyle": "->", "color": TEAL, "lw": 1.0},
        )
        ax.text(
            24.3,
            yi + 0.18,
            f"saved {row['saved_percentage_points']:.2f} pp\n"
            f"95% CI {row['saved_ci_lo']:.2f} to {row['saved_ci_hi']:.2f}",
            ha="right",
            va="bottom",
            fontsize=5.9,
            color=TEAL,
        )
    ax.set_yticks(y, ["Official test\n(confirmatory)", "Hard OOD 40%\n(exploratory)"])
    ax.set_xlim(0, 25)
    ax.set_ylim(-0.55, 1.55)
    ax.set_xlabel("Pool screened before first top-5% hit (%)")
    ax.set_title("Fixed ranking shows an OOD signal")
    ax.scatter([], [], s=28, color=GRAY, label="target-only")
    ax.scatter([], [], s=34, color=TEAL, label="+ thermoelectric prior")
    ax.legend(loc="lower left", ncol=2, columnspacing=0.8, handletextpad=0.3)
    panel_label(ax, "a")


def sequential_frame() -> pd.DataFrame:
    edges = pd.read_csv(RESULTS / "obelix_ood_discovery_edges.csv")
    selected = edges[
        (edges["model_family"] == "extra-trees-primary")
        & edges["strategy"].isin(
            [
                "thermoelectric_prior",
                "shuffled_thermoelectric_control",
                "random_control",
            ]
        )
    ].copy()
    selected["ci"] = selected["bootstrap_95"].map(parse_interval)
    selected["ci_lo"] = selected["ci"].map(lambda x: x[0])
    selected["ci_hi"] = selected["ci"].map(lambda x: x[1])
    selected["pool"] = selected["scope"].map(
        {"official_test": "Official", "hard_ood_40pct": "Hard OOD"}
    )
    selected["policy"] = selected["strategy"].map(
        {
            "thermoelectric_prior": "TE prior",
            "shuffled_thermoelectric_control": "shuffled prior",
            "random_control": "random",
        }
    )
    selected["label"] = selected["pool"] + ": " + selected["policy"]
    order = [
        "Official: TE prior",
        "Official: shuffled prior",
        "Official: random",
        "Hard OOD: TE prior",
        "Hard OOD: shuffled prior",
        "Hard OOD: random",
    ]
    return selected.set_index("label").loc[order].reset_index()


def panel_b(ax) -> None:
    frame = sequential_frame()
    frame.to_csv(RESULTS / "figure_ood_decision_panel_b.csv", index=False)
    y = np.arange(len(frame) - 1, -1, -1)
    colors = frame["strategy"].map(
        {
            "thermoelectric_prior": TEAL,
            "shuffled_thermoelectric_control": GRAY,
            "random_control": ORANGE,
        }
    )
    markers = frame["scope"].map(
        {"official_test": "o", "hard_ood_40pct": "s"}
    )
    for yi, (_, row), color, marker in zip(y, frame.iterrows(), colors, markers):
        effect = float(row["mean_experiments_saved"])
        ax.plot([row["ci_lo"], row["ci_hi"]], [yi, yi], color=color, lw=1.4)
        ax.scatter(
            effect,
            yi,
            s=28,
            marker=marker,
            color=color,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
    ax.axvline(0, color=BLACK, lw=0.75)
    ax.axvline(5, color=RED, lw=0.9, ls=(0, (3, 2)))
    ax.axhline(2.5, color=LIGHT_GRAY, lw=0.7)
    ax.set_yticks(y, frame["label"])
    ax.set_xlim(-2.8, 14.2)
    ax.set_ylim(-0.6, len(frame) - 0.35)
    ax.set_xlabel("Experiments saved versus target-only UCB")
    ax.set_title("Sequential improvement gates fail")
    ax.text(5.25, -0.47, "frozen practical gate", color=RED, fontsize=5.8)
    ax.text(
        13.7,
        4.75,
        "official TE: +0.25\n95% CI -1.30 to 1.82",
        ha="right",
        va="top",
        color=TEAL,
        fontsize=5.9,
    )
    ax.text(
        13.7,
        0.58,
        "random is the only policy\nto cross the 5-experiment gate",
        ha="right",
        va="bottom",
        color=ORANGE,
        fontsize=5.9,
        fontweight="bold",
    )
    panel_label(ax, "b")


def panel_c(ax) -> None:
    survival = pd.read_csv(RESULTS / "obelix_ood_discovery_survival.csv")
    reaches = pd.read_csv(RESULTS / "obelix_ood_discovery_reach.csv")
    strategies = {
        "target_only": ("target-only UCB", GRAY, "-"),
        "thermoelectric_prior": ("TE-prior UCB", TEAL, "-"),
        "random_control": ("uniform random", ORANGE, "-"),
    }
    source = survival[
        (survival["scope"] == "official_test")
        & survival["strategy"].isin(strategies)
    ].copy()
    source.to_csv(RESULTS / "figure_ood_decision_panel_c.csv", index=False)
    reach_local = reaches[
        (reaches["scope"] == "official_test")
        & (reaches["model_family"] == "extra-trees-primary")
    ]
    for strategy, (label, color, linestyle) in strategies.items():
        local = source[source["strategy"] == strategy]
        ax.step(
            local["step"],
            local["probability_hit"],
            where="post",
            color=color,
            lw=2.0 if strategy != "target_only" else 1.6,
            ls=linestyle,
            label=label,
        )
    medians = (
        reach_local[reach_local["strategy"].isin(strategies)]
        .groupby("strategy")["experiments_to_hit"]
        .median()
    )
    censor = (
        reach_local[reach_local["strategy"].isin(strategies)]
        .groupby("strategy")["censored"]
        .mean()
    )
    ax.set(
        xlim=(0, 40),
        ylim=(0, 1.02),
        xlabel="OOD acquisitions",
        ylabel="Probability of a true top-5% hit",
        title="Random acquisition outperforms both UCB policies",
    )
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.grid(axis="y", color=LIGHT_GRAY, lw=0.5, alpha=0.65)
    ax.legend(loc="upper left")
    ax.text(
        0.97,
        0.06,
        "median acquisitions\n"
        f"target-only {medians['target_only']:.0f} | "
        f"TE prior {medians['thermoelectric_prior']:.0f} | "
        f"random {medians['random_control']:.0f}\n"
        "censored at 40\n"
        f"{censor['target_only']:.0%} | "
        f"{censor['thermoelectric_prior']:.0%} | "
        f"{censor['random_control']:.0%}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.2,
        color=BLACK,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 1.5},
    )
    panel_label(ax, "c")


def main() -> None:
    ensure_output_dirs()
    figure = plt.figure(figsize=(6.66, 4.25), layout="constrained")
    grid = figure.add_gridspec(
        2, 2, width_ratios=[0.96, 1.20], height_ratios=[0.83, 1.17]
    )
    ax_a = figure.add_subplot(grid[0, 0])
    ax_b = figure.add_subplot(grid[1, 0])
    ax_c = figure.add_subplot(grid[:, 1])
    panel_a(ax_a)
    panel_b(ax_b)
    panel_c(ax_c)
    base = FIGURES / "ood_decision_borrowing"
    figure.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    figure.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    figure.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    figure.savefig(
        base.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)
    print(base)


if __name__ == "__main__":
    main()
