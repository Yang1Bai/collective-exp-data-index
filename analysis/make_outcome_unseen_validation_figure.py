"""Build the publication figure for the verified outcome-unseen programmes."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
STEM = FIGURES / "outcome_unseen_validation"

COLORS = {
    "ink": "#20262E",
    "muted": "#66717C",
    "grid": "#E3E7EB",
    "starry": "#3278A6",
    "tri": "#B66A55",
    "pooled": "#604F91",
    "pass": "#2E8B74",
    "fail": "#C78A91",
    "neutral": "#D9DEE3",
    "positive": "#2E8B74",
    "negative": "#B66A55",
}

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
        "xtick.labelsize": 6.3,
        "ytick.labelsize": 6.3,
        "legend.fontsize": 6.2,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)


def load_json(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.075,
        1.06,
        label,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="top",
    )


def build_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    starry = load_json("starrydata_reverse_VALIDATED.json")
    tri = load_json("tri_oer_VALIDATED.json")
    multi = load_json("outcome_unseen_multi_target_summary.json")

    star_effect = starry["hierarchical_primary_prediction"]["ionic_vs_target"]
    tri_effect = tri["prediction_inference"]["across_plates"]["all_vs_target"]
    pooled = multi["random_effects"]
    panel_a = pd.DataFrame(
        [
            {
                "target": "Starrydata reverse transport",
                "effect_percent": 100 * star_effect["mean_ci95"][0],
                "ci_low_percent": 100 * star_effect["mean_ci95"][1],
                "ci_high_percent": 100 * star_effect["mean_ci95"][2],
                "holm_p": star_effect["holm_p"],
                "absolute_utility": "R2 = -0.485",
                "full_gate": "fail",
            },
            {
                "target": "TRI OER (4 plates)",
                "effect_percent": 100 * tri_effect["random_effects"]["mean"],
                "ci_low_percent": 100 * tri_effect["random_effects"]["ci95"][0],
                "ci_high_percent": 100 * tri_effect["random_effects"]["ci95"][1],
                "holm_p": tri_effect["holm_p"],
                "absolute_utility": "0/4 plates R2 > 0",
                "full_gate": "fail",
            },
            {
                "target": "Two-target random effects",
                "effect_percent": 100 * pooled["mean_relative_rmse_gain"],
                "ci_low_percent": 100 * pooled["ci95"][0],
                "ci_high_percent": 100 * pooled["ci95"][1],
                "holm_p": np.nan,
                "absolute_utility": f"I2 = {pooled['i_squared_percent']:.1f}%",
                "full_gate": "boundary",
            },
        ]
    )

    star_rob = pd.DataFrame(starry["learner_representation_robustness"])
    star_rob["target"] = "Starrydata"
    tri_rob = pd.DataFrame(tri["learner_representation_robustness"])
    tri_rob["target"] = "TRI OER"
    panel_c = pd.concat(
        [
            star_rob[["target", "learner", "representation", "mean"]],
            tri_rob[["target", "learner", "representation", "mean"]],
        ],
        ignore_index=True,
    )
    panel_c["mean_effect_percent"] = 100 * panel_c.pop("mean")

    robustness_pass_starry = all(
        (star_rob[star_rob["representation"].eq(rep)]["mean"] > 0).sum() >= 2
        for rep in star_rob["representation"].unique()
    )
    robustness_pass_tri = all(
        (tri_rob[tri_rob["representation"].eq(rep)]["mean"] > 0).sum() >= 2
        for rep in tri_rob["representation"].unique()
    )
    gate_names = [
        "Positive\ninterval",
        "Holm\np < 0.05",
        "Absolute\nutility",
        "Robust\nenvelope",
        "Matched\nspecificity",
        "Exploration\npolicy",
        "Hypothesis\ncards",
    ]
    gate_values = {
        "Starrydata": [1, 0, 0, int(robustness_pass_starry), 0, 0, 0],
        "TRI OER": [0, 0, 0, int(robustness_pass_tri), 0, 0, 0],
    }
    panel_b = pd.DataFrame(
        [
            {"target": target, "gate": gate, "pass": values[index]}
            for target, values in gate_values.items()
            for index, gate in enumerate(gate_names)
        ]
    )

    star_cards = pd.read_csv(RESULTS / "starrydata_reverse_hypothesis_tests.csv")
    star_cards = star_cards.assign(
        target="Starrydata",
        effect=star_cards["mean_paired_difference"],
    )[["target", "card_id", "effect", "holm_p"]]
    tri_cards = pd.read_csv(RESULTS / "tri_oer_hypothesis_tests.csv")
    tri_cards = tri_cards.assign(
        target="TRI OER",
        effect=tri_cards["mean_paired_fom_difference"],
    )[["target", "card_id", "effect", "holm_p"]]
    panel_d = pd.concat([star_cards, tri_cards], ignore_index=True)

    for label, frame in zip("abcd", [panel_a, panel_b, panel_c, panel_d]):
        frame.to_csv(RESULTS / f"figure_outcome_unseen_panel_{label}.csv", index=False)
    return panel_a, panel_b, panel_c, panel_d


def draw_panel_a(ax: plt.Axes, data: pd.DataFrame) -> None:
    panel_label(ax, "a")
    y = np.arange(len(data))[::-1]
    colors = [COLORS["starry"], COLORS["tri"], COLORS["pooled"]]
    ax.axvline(0, color=COLORS["ink"], linewidth=0.8)
    for index, row in data.iterrows():
        yi = y[index]
        ax.errorbar(
            row.effect_percent,
            yi,
            xerr=[[row.effect_percent - row.ci_low_percent], [row.ci_high_percent - row.effect_percent]],
            fmt="o",
            color=colors[index],
            markeredgecolor="white",
            markeredgewidth=0.6,
            markersize=6.5 if index < 2 else 7.5,
            elinewidth=1.4,
            capsize=2.5,
            zorder=3,
        )
        ax.text(
            2.15,
            yi,
            f"{row.effect_percent:+.2f}% [{row.ci_low_percent:+.2f}, {row.ci_high_percent:+.2f}]",
            ha="left",
            va="center",
            fontsize=6.2,
            color=COLORS["ink"],
            clip_on=False,
        )
        ax.text(
            2.15,
            yi - 0.23,
            f"{row.absolute_utility}; full gate: {row.full_gate}",
            ha="left",
            va="center",
            fontsize=5.8,
            color=COLORS["muted"],
            clip_on=False,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(data["target"])
    ax.set_xlabel("Relative RMSE improvement over target-only (%)")
    ax.set_title("Independent-target effects do not pass the full prediction gate", loc="left", fontweight="bold")
    ax.set_xlim(-1.0, 5.1)
    ax.set_ylim(-0.65, 2.55)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6)
    ax.text(
        0.01,
        0.02,
        "Positive values favor borrowing; intervals use independent target units, not seeds alone.",
        transform=ax.transAxes,
        fontsize=5.8,
        color=COLORS["muted"],
    )


def draw_panel_b(ax: plt.Axes, data: pd.DataFrame) -> None:
    panel_label(ax, "b")
    matrix = data.pivot(index="target", columns="gate", values="pass")
    target_order = ["Starrydata", "TRI OER"]
    gate_order = data["gate"].drop_duplicates().tolist()
    matrix = matrix.reindex(index=target_order, columns=gate_order)
    ax.imshow(matrix.to_numpy(), cmap=ListedColormap([COLORS["fail"], COLORS["pass"]]), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(gate_order)))
    ax.set_xticklabels(gate_order)
    ax.set_yticks(np.arange(len(target_order)))
    ax.set_yticklabels(target_order)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = int(matrix.iloc[row, column])
            ax.text(column, row, "pass" if value else "fail", ha="center", va="center", fontsize=5.8, color="white", fontweight="bold")
    ax.set_title("Frozen conjunctive gates prevent weak signals from becoming claims", loc="left", fontweight="bold")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)


def draw_panel_c(ax: plt.Axes, data: pd.DataFrame) -> None:
    panel_label(ax, "c")
    learner_order = ["extra_trees", "random_forest", "ridge"]
    local = data.copy()
    representation_slot = {
        ("Starrydata", "composition"): "base",
        ("Starrydata", "composition_context"): "context",
        ("TRI OER", "element_fraction"): "base",
        ("TRI OER", "periodic_summary"): "context",
    }
    local["representation_slot"] = [
        representation_slot[(target, representation)]
        for target, representation in zip(local["target"], local["representation"])
    ]
    rows = [(learner, slot) for learner in learner_order for slot in ["base", "context"]]
    labels = [
        f"{learner.replace('_', ' ').title()} | {'base' if slot == 'base' else 'context / periodic'}"
        for learner, slot in rows
    ]
    pivot = local.pivot_table(
        index=["learner", "representation_slot"],
        columns="target",
        values="mean_effect_percent",
    ).reindex(rows)
    values = pivot[["Starrydata", "TRI OER"]].to_numpy()
    limit = max(7.5, float(np.nanmax(np.abs(values))))
    image = ax.imshow(values, cmap="RdBu", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Starrydata", "TRI OER"])
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels)
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = values[row, column]
            ax.text(column, row, f"{value:+.2f}%", ha="center", va="center", fontsize=5.8, color="white" if abs(value) > 0.55 * limit else COLORS["ink"])
    ax.set_title("Learner and representation effects are heterogeneous", loc="left", fontweight="bold")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = plt.colorbar(image, ax=ax, fraction=0.035, pad=0.025)
    cbar.set_label("Mean relative RMSE effect (%)", fontsize=6)
    cbar.ax.tick_params(labelsize=5.5)


def draw_panel_d(ax: plt.Axes, data: pd.DataFrame) -> None:
    panel_label(ax, "d")
    labels = [
        "Starry | ionic region",
        "Starry | Caltech region",
        "Starry | consensus",
        "TRI | same OER",
        "TRI | oxygen-electrocatalysis",
        "TRI | consensus",
    ]
    y = np.arange(len(data))[::-1]
    p = data["holm_p"].clip(lower=1e-4).to_numpy(float)
    colors = [COLORS["positive"] if effect > 0 else COLORS["negative"] for effect in data["effect"]]
    ax.axvline(0.05, color=COLORS["ink"], linewidth=0.8, linestyle=(0, (3, 2)))
    ax.scatter(p, y, c=colors, s=32, edgecolor="white", linewidth=0.5, zorder=3)
    for xi, yi, value in zip(p, y, data["holm_p"]):
        if xi >= 0.8:
            ax.text(0.87, yi, f"{value:.3f}", ha="right", va="center", fontsize=5.8, color=COLORS["muted"])
        else:
            ax.text(xi * 1.05, yi, f"{value:.3f}", va="center", fontsize=5.8, color=COLORS["muted"])
    ax.set_xscale("log")
    ax.set_xlim(0.03, 1.25)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Holm-adjusted p value")
    ax.set_title("No prewritten hypothesis is confirmed", loc="left", fontweight="bold")
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.6)
    ax.text(0.05, -0.16, "0.05", transform=ax.get_xaxis_transform(), ha="center", fontsize=5.7, color=COLORS["muted"])


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    panel_a, panel_b, panel_c, panel_d = build_source_data()
    width = 183 / 25.4
    fig = plt.figure(figsize=(width, 7.3), constrained_layout=False)
    grid = fig.add_gridspec(3, 2, height_ratios=[1.05, 0.62, 1.35], width_ratios=[1.05, 0.95])
    draw_panel_a(fig.add_subplot(grid[0, :]), panel_a)
    draw_panel_b(fig.add_subplot(grid[1, :]), panel_b)
    draw_panel_c(fig.add_subplot(grid[2, 0]), panel_c)
    draw_panel_d(fig.add_subplot(grid[2, 1]), panel_d)
    fig.subplots_adjust(left=0.22, right=0.985, top=0.965, bottom=0.075, hspace=0.72, wspace=0.78)
    # Keep the physical canvas at the journal's 183 mm double-column limit.
    # Tight bounding boxes expand beyond that width because of long row labels.
    fig.savefig(STEM.with_suffix(".svg"))
    fig.savefig(STEM.with_suffix(".pdf"))
    fig.savefig(STEM.with_suffix(".tiff"), dpi=600)
    fig.savefig(STEM.with_suffix(".png"), dpi=300)
    print(
        json.dumps(
            {
                "status": "complete",
                "figure": str(STEM),
                "panel_rows": {"a": len(panel_a), "b": len(panel_b), "c": len(panel_c), "d": len(panel_d)},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
