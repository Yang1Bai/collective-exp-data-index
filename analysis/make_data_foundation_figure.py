"""Create the submission-grade analysed-resource and evidence-scope figure."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

from common import FIGURES, RESULTS, ensure_output_dirs


plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7.0,
    "axes.labelsize": 7.2,
    "axes.titlesize": 8.2,
    "axes.titleweight": "bold",
    "axes.linewidth": 0.65,
    "xtick.labelsize": 6.2,
    "ytick.labelsize": 6.2,
    "legend.fontsize": 6.1,
    "legend.frameon": False,
    "axes.spines.right": False,
    "axes.spines.top": False,
})

INK = "#252525"
GRAY = "#70757A"
LIGHT = "#E7E9EC"
PALE = "#F5F6F7"
TEAL = "#2A9D8F"
BLUE = "#3E78B2"
ORANGE = "#D58A2F"
PURPLE = "#7A6AA6"
NULL = "#8B9095"

FAMILY_COLORS = {
    "aqueous molecular properties": "#6E9BC7",
    "energy and ionic transport": "#2A9D8F",
    "alloy mechanics": "#D58A2F",
    "catalysis": "#8B79B4",
    "polymers": "#B56A8A",
}

FAMILY_SHORT = {
    "aqueous molecular properties": "aqueous molecular",
    "electrolyte transport": "electrolyte transport",
    "thermoelectric transport": "thermoelectric transport",
    "alloy mechanics": "alloy mechanics",
    "ionic transport": "ionic transport",
    "electrocatalysis": "electrocatalysis",
    "polymers": "polymers",
    "molecular photochemistry": "photochemistry",
    "battery aging": "battery aging",
    "adsorption thermodynamics": "adsorption thermodynamics",
}

ROLE_ORDER = ["both", "donor only", "recipient only", "artifact only"]
ROLE_LABELS = {
    "both": "DONOR + RECIPIENT",
    "donor only": "DONOR ONLY",
    "recipient only": "RECIPIENT ONLY",
    "artifact only": "ARTIFACT GATE ONLY",
}
LAYER_CODES = {"normalized": "N", "external": "E", "analysis-only": "A"}


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.095, 1.035, label, transform=ax.transAxes, fontsize=9.8,
            fontweight="bold", ha="left", va="bottom", color=INK)


def load_and_validate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    inventory = pd.read_csv(RESULTS / "figure_data_foundation_inventory.csv")
    lake = pd.read_csv(RESULTS / "figure_data_foundation_lake.csv")
    scope = pd.read_csv(RESULTS / "figure_data_foundation_scope.csv")
    portfolio = pd.read_csv(
        RESULTS / "figure_data_foundation_portfolio.csv", keep_default_na=False
    )

    for column in ("donor", "recipient", "artifact_gate"):
        inventory[column] = inventory[column].astype(bool)
    assert len(inventory) == 21
    assert inventory["resource"].nunique() == 21
    assert inventory["analysis_layer"].value_counts().to_dict() == {
        "normalized": 13, "external": 7, "analysis-only": 1
    }
    assert int(inventory["donor"].sum()) == 16
    assert int(inventory["recipient"].sum()) == 17
    assert int((inventory["donor"] & inventory["recipient"]).sum()) == 13
    assert int((inventory["donor"] | inventory["recipient"]).sum()) == 20
    assert int(inventory["artifact_gate"].sum()) == 1
    assert inventory["role_group"].value_counts().to_dict() == {
        "both": 13, "recipient only": 4, "donor only": 3, "artifact only": 1
    }

    assert len(lake) == 13 and int(lake["measurements"].sum()) == 96184
    assert set(lake["dataset"]) == set(
        inventory.loc[inventory["analysis_layer"] == "normalized", "resource"]
    )
    assert (lake["measurements"] > 0).all(), "Log-scale measurement counts must be positive"
    lake["measurements_plot"] = lake["measurements"].clip(lower=1)
    assert int(lake["properties"].sum()) == 231  # per-source labels; 230 distinct globally

    indexed_scope = scope.set_index("layer")
    assert int(indexed_scope.loc["analysed cohort", "primary_count"]) == 21
    assert int(indexed_scope.loc["transfer-active cohort", "primary_count"]) == 20
    assert int(indexed_scope.loc["directed benchmark", "primary_count"]) == 97
    assert int(indexed_scope.loc["programme synthesis", "primary_count"]) == 13

    required = {"passed", "directional", "boundary", "null", "diagnostic"}
    assert set(portfolio["status"]).issubset(required)
    assert portfolio.loc[portfolio["role_defining"], "program"].nunique() == 5
    return inventory, lake, scope, portfolio


def panel_a(ax: plt.Axes, inventory: pd.DataFrame) -> None:
    rows: list[tuple[str, str | pd.Series]] = []
    for role in ROLE_ORDER:
        subset = inventory[inventory["role_group"] == role]
        rows.append(("header", f"{ROLE_LABELS[role]}  ({len(subset)})"))
        rows.extend(("resource", row) for _, row in subset.iterrows())

    ax.set_xlim(0, 6.7)
    ax.set_ylim(len(rows) + 0.9, -1.5)
    ax.axis("off")
    panel_label(ax, "a")
    ax.set_title("Exactly 21 experimental resources enter a numerical analysis",
                 loc="left", pad=20)
    ax.text(0.0, 1.035,
            "Twenty form the directed borrowing network; one supplies the independent artifact gate",
            transform=ax.transAxes, fontsize=6.1, color=GRAY, va="bottom")

    x_resource, x_family = 0.08, 2.62
    x_donor, x_recipient, x_gate, x_layer = 4.48, 5.10, 5.72, 6.34
    ax.text(x_resource, -0.78, "RESOURCE", fontsize=5.4, fontweight="bold", color=GRAY)
    ax.text(x_family, -0.78, "SCIENTIFIC FAMILY", fontsize=5.4, fontweight="bold", color=GRAY)
    for x, label in [
        (x_donor, "DONOR"), (x_recipient, "RECIPIENT"),
        (x_gate, "GATE"), (x_layer, "LAYER"),
    ]:
        ax.text(x, -0.78, label, fontsize=5.1, fontweight="bold",
                color=GRAY, ha="center")

    for y, (kind, value) in enumerate(rows):
        if kind == "header":
            ax.axhspan(y - 0.45, y + 0.45, color=PALE, zorder=0)
            ax.text(x_resource, y, str(value), va="center", fontsize=5.45,
                    fontweight="bold", color=INK)
            continue

        row = value
        assert isinstance(row, pd.Series)
        ax.axhline(y + 0.47, color="#ECEDEF", lw=0.42, zorder=0)
        ax.text(x_resource, y, row["display_name"], va="center",
                fontsize=5.45, color=INK)
        ax.text(x_family, y, FAMILY_SHORT[row["family"]], va="center",
                fontsize=5.0, color=GRAY)

        for x, present, color in [
            (x_donor, bool(row["donor"]), TEAL),
            (x_recipient, bool(row["recipient"]), BLUE),
            (x_gate, bool(row["artifact_gate"]), PURPLE),
        ]:
            if present:
                ax.scatter(x, y, s=26, marker="o", color=color,
                           edgecolors=INK, linewidth=0.35, zorder=3)
            else:
                ax.scatter(x, y, s=7, marker=".", color="#D4D7DA", zorder=2)
        ax.text(x_layer, y, LAYER_CODES[row["analysis_layer"]],
                ha="center", va="center", fontsize=5.2, fontweight="bold", color=INK)

    ax.text(6.67, len(rows) + 0.42,
            "N = normalized  |  E = frozen external  |  A = streamed analysis-only",
            fontsize=5.0, color=GRAY, ha="right", va="bottom")


def panel_b(ax: plt.Axes, lake: pd.DataFrame) -> None:
    ordered = lake.sort_values("measurements", ascending=True).reset_index(drop=True)
    y = np.arange(len(ordered))
    colors = [FAMILY_COLORS[x] for x in ordered["family"]]
    bars = ax.barh(y, ordered["measurements_plot"], color=colors, height=0.68,
                   edgecolor="white")
    ax.set_xscale("log")
    ax.set_xlim(400, 48000)
    ax.set_yticks(y, ordered["display_name"])
    ax.set_xlabel("Experimental measurements (log scale)")
    ax.grid(axis="x", which="both", color="#ECEDEF", linewidth=0.55)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, ordered["measurements"]):
        ax.text(value * 1.07, bar.get_y() + bar.get_height() / 2, f"{int(value):,}",
                va="center", ha="left", fontsize=5.7, color=INK)

    handles = [
        Line2D([0], [0], marker="s", linestyle="", markersize=5,
               markerfacecolor=color, markeredgecolor="none", label=family)
        for family, color in FAMILY_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 0.0),
              ncol=1, handletextpad=0.25, labelspacing=0.25, fontsize=5.1)
    ax.text(0.0, 1.12, "96,184", transform=ax.transAxes, fontsize=17.5,
            fontweight="bold", color=TEAL, va="top")
    ax.text(0.415, 1.096, "measurements", transform=ax.transAxes, fontsize=7.4,
            fontweight="bold", color=INK, va="top")
    ax.text(0.415, 1.025, "13 normalized resources | 230 properties | 29,516 entities",
            transform=ax.transAxes, fontsize=5.55, color=GRAY, va="top")
    ax.set_title("The source-pinned measurement core", loc="left", pad=27)
    panel_label(ax, "b")


def panel_c(ax: plt.Axes, scope: pd.DataFrame) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "c")
    ax.set_title("The empirical denominator is explicit", loc="left", pad=5)

    scope_index = scope.set_index("layer")
    cards = [
        ("21", "analysed resources", "13 normalized | 7 external | 1 analysis-only", TEAL),
        ("20", "transfer-active resources", "16 donors | 17 recipients | 13 both", BLUE),
        ("97", "systematic gate-benchmark edges", "20 target tasks", ORANGE),
        ("13", "programme clusters", "positive, null, harmful and unresolved retained", PURPLE),
    ]
    y_positions = [0.79, 0.58, 0.37, 0.16]
    expected = [
        int(scope_index.loc["analysed cohort", "primary_count"]),
        int(scope_index.loc["transfer-active cohort", "primary_count"]),
        int(scope_index.loc["directed benchmark", "primary_count"]),
        int(scope_index.loc["programme synthesis", "primary_count"]),
    ]
    assert expected == [21, 20, 97, 13]

    for y, (number, title, detail, color) in zip(y_positions, cards):
        patch = FancyBboxPatch(
            (0.035, y - 0.075), 0.93, 0.145,
            boxstyle="round,pad=0.009,rounding_size=0.018",
            facecolor="#FAFAFA", edgecolor="#D4D7DA", linewidth=0.7
        )
        ax.add_patch(patch)
        ax.text(0.09, y, number, fontsize=13.5, fontweight="bold",
                color=color, ha="center", va="center")
        ax.text(0.19, y + 0.022, title, fontsize=6.0, fontweight="bold",
                color=INK, ha="left", va="center")
        ax.text(0.19, y - 0.032, detail, fontsize=5.15,
                color=GRAY, ha="left", va="center")


def panel_d(ax: plt.Axes, portfolio: pd.DataFrame) -> None:
    endpoints = [
        "law or coefficient", "few-shot prediction",
        "OOD screening", "sequential or temporal",
    ]
    programs = list(dict.fromkeys(portfolio["program"]))
    n = len(programs)
    lookup = {(r.program, r.endpoint): r.status for r in portfolio.itertuples(index=False)}
    role_defining = set(portfolio.loc[portfolio["role_defining"], "program"])

    ax.set_xlim(-0.55, len(endpoints) - 0.45)
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_xticks(
        np.arange(len(endpoints)),
        ["Law / coefficient\ntransport", "Few-shot\nprediction",
         "OOD\nscreening", "Sequential /\ntemporal"],
    )
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=5)
    ax.set_yticks(np.arange(n), programs)
    ax.tick_params(axis="y", length=0, pad=5)
    for tick, program in zip(ax.get_yticklabels(), programs):
        if program in role_defining:
            tick.set_fontweight("bold")
            tick.set_color(BLUE)

    for x in np.arange(-0.5, len(endpoints), 1):
        ax.axvline(x, color=LIGHT, lw=0.65, zorder=0)
    for y in np.arange(-0.5, n, 1):
        ax.axhline(y, color=LIGHT, lw=0.55, zorder=0)
    for spine in ax.spines.values():
        spine.set_visible(False)

    styles = {
        "passed": dict(marker="o", color=TEAL, edgecolors=INK, label="gate passed"),
        "directional": dict(marker="o", color=BLUE, edgecolors="white",
                            label="directional / internal signal"),
        "boundary": dict(marker="^", color=ORANGE, edgecolors=INK,
                         label="unresolved / conditioned"),
        "diagnostic": dict(marker="D", color=PURPLE, edgecolors=INK,
                           label="method-development diagnostic"),
        "null": dict(marker="X", color=NULL, edgecolors="white",
                     label="null, harm or non-evaluable"),
    }
    for yi, program in enumerate(programs):
        for xi, endpoint in enumerate(endpoints):
            status = lookup.get((program, endpoint))
            if status is None:
                ax.scatter(xi, yi, s=7, color="#DADDE0", marker=".", zorder=2)
                continue
            style = styles[status]
            ax.scatter(xi, yi, s=58, marker=style["marker"], color=style["color"],
                       edgecolors=style["edgecolors"], linewidth=0.65, zorder=3)

    handles = [
        Line2D([0], [0], marker=style["marker"], linestyle="", markersize=5.4,
               markerfacecolor=style["color"], markeredgecolor=style["edgecolors"],
               label=style["label"])
        for style in styles.values()
    ]
    handles.append(
        Line2D([0], [0], marker="s", linestyle="", markersize=4,
               markerfacecolor=BLUE, markeredgecolor="none",
               label="bold row: role-defining example")
    )
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.19),
              ncol=3, columnspacing=0.9, handletextpad=0.35, fontsize=5.5)
    ax.set_title("Favorable and unfavorable outcomes stay in the same evidence portfolio",
                 loc="left", pad=23)
    panel_label(ax, "d")


def save_figure(fig: plt.Figure, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, facecolor="white",
                pil_kwargs={"compression": "tiff_lzw"})


def main() -> None:
    ensure_output_dirs()
    inventory, lake, scope, portfolio = load_and_validate()
    # Current RSC double-column width and maximum-height safe export.
    fig = plt.figure(figsize=(6.73, 8.85), constrained_layout=False)
    gs = fig.add_gridspec(
        3, 2, height_ratios=[3.55, 2.25, 3.05],
        width_ratios=[1.04, 0.96], hspace=0.49, wspace=0.48,
    )
    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_d = fig.add_subplot(gs[2, :])

    panel_a(ax_a, inventory)
    panel_b(ax_b, lake)
    panel_c(ax_c, scope)
    panel_d(ax_d, portfolio)
    fig.subplots_adjust(left=0.245, right=0.985, top=0.94, bottom=0.085)
    save_figure(fig, FIGURES / "data_foundation_scope")
    plt.close(fig)


if __name__ == "__main__":
    main()
