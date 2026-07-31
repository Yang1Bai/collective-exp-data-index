"""Build the battery outcome-unseen temporal knowledge-borrowing figure."""

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
BASE = RESULTS / "multistage_battery_stage2_coverage_sensitivity"
DIAGNOSTIC = BASE / "postrelease_adjacency_diagnostic"
SUMMARY_PATH = DIAGNOSTIC / "POSTRELEASE_ADJACENCY_DIAGNOSTIC_SUMMARY.json"
SENSITIVITY_PATH = BASE / "analysis" / "POSTRELEASE_SENSITIVITY_SUMMARY.json"
MAP_PATH = DIAGNOSTIC / "condition_borrowing_map.csv"
GATE_PATH = BASE / "analysis" / "training_only_gate.csv"
AUDIT_PATH = RESULTS / "multistage_battery_stage2" / "STAGE2_RELEASE_AUDIT.json"
STEM = FIGURES / "battery_continuous_borrowing"

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
TEAL = "#147D73"
TEAL_DARK = "#0E5E57"
TEAL_LIGHT = "#A7D5CF"
BLUE = "#4C78A8"
PURPLE = "#7562A8"
ORANGE = "#D9822B"
RED = "#B64342"
GRAY = "#818991"


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


def draw_box(
    ax: plt.Axes,
    x: float,
    width: float,
    title: str,
    subtitle: str,
    facecolor: str,
) -> None:
    patch = FancyBboxPatch(
        (x, 0.27),
        width,
        0.48,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=0.75,
        edgecolor=INK,
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(x + 0.028, 0.61, title, fontsize=7.6, fontweight="bold", va="center")
    ax.text(x + 0.028, 0.40, subtitle, fontsize=6.15, color=MUTED, va="center")


def panel_a(ax: plt.Axes, audit: dict) -> pd.DataFrame:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "a", -0.02)
    items = [
        ("Stage 1 source", "2021 measurements\nupstream only", "#EAF0F5"),
        ("Freeze prediction", "source model fit before\nStage 2 outcomes", "#E1EDF5"),
        ("Stage 2 target", "2023 condition groups\n138 released cells", "#DDF1ED"),
        ("Outcome-unseen test", "135 endpoints\n22 evaluable groups", "#D7ECE8"),
    ]
    xs = [0.015, 0.245, 0.475, 0.705]
    width = 0.205
    for (title, subtitle, color), x in zip(items, xs):
        draw_box(ax, x, width, title, subtitle, color)
    for left, right in zip(xs[:-1], xs[1:]):
        ax.add_patch(
            FancyArrowPatch(
                (left + width + 0.006, 0.51),
                (right - 0.006, 0.51),
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.85,
                color=INK,
            )
        )
    ax.text(
        0.98,
        0.18,
        "Coverage boundary: one z10 group lacks all three AT_T23 endpoints;\n"
        "the frozen 23-group primary is non-evaluable.",
        ha="right",
        va="top",
        fontsize=6.1,
        color=RED,
        fontweight="bold",
    )
    frame = pd.DataFrame(
        [
            {"step": i + 1, "title": title, "subtitle": subtitle.replace("\n", " ")}
            for i, (title, subtitle, _) in enumerate(items)
        ]
        + [
            {
                "step": 5,
                "title": "coverage boundary",
                "subtitle": (
                    f"{audit['evaluable_stage2_cells']} evaluable of {audit['allowlisted_archives']} Stage 2 cells; "
                    "one condition group excluded"
                ),
            }
        ]
    )
    frame.to_csv(RESULTS / "figure_battery_panel_a.csv", index=False)
    return frame


def forest_frame(summary: dict) -> pd.DataFrame:
    mapping = [
        ("adjacency_only minus target_only", "target-only"),
        ("adjacency_only minus wrong_property", "wrong-property source"),
        ("adjacency_only minus shuffled_source", "shuffled source"),
        ("adjacency_only minus random_features", "random features"),
    ]
    rows = []
    for key, label in mapping:
        record = summary["inference"][key]
        rows.append(
            {
                "comparison": key,
                "label": label,
                "effect_percent": 100 * record["effect"],
                "ci_lo_percent": 100 * record["ci95"][0],
                "ci_hi_percent": 100 * record["ci95"][1],
                "holm_adjusted_p": record["holm_adjusted_p"],
                "inferential_status": record["inferential_status"],
            }
        )
    return pd.DataFrame(rows)


def panel_b(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_battery_panel_b.csv", index=False)
    y = np.arange(len(frame))[::-1]
    for yi, row in zip(y, frame.to_dict("records")):
        ax.plot([row["ci_lo_percent"], row["ci_hi_percent"]], [yi, yi], color=TEAL, lw=1.45)
        ax.scatter(row["effect_percent"], yi, s=39, color=TEAL, edgecolor="white", linewidth=0.55, zorder=3)
        ax.text(
            row["ci_hi_percent"] + 0.7,
            yi,
            f"{row['effect_percent']:+.1f}%  p={row['holm_adjusted_p']:.3f}",
            fontsize=5.75,
            va="center",
            color=TEAL_DARK,
        )
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(y, [f"vs {label}" for label in frame["label"]])
    ax.set_xlim(-3, 29)
    ax.set_ylim(-0.6, len(frame) - 0.4)
    ax.set_xlabel("Relative condition-RMSE gain (%)")
    ax.set_title("Continuous adjacent-source borrowing beats matched controls", loc="left")
    ax.text(0.98, 0.06, "positive favors borrowing", transform=ax.transAxes, ha="right", fontsize=5.6, color=MUTED)
    panel_label(ax, "b")


def panel_c(ax: plt.Axes, frame: pd.DataFrame) -> None:
    out = frame[
        [
            "type",
            "condition_group",
            "source_distance",
            "target_distance",
            "applicability",
            "borrow_allowed",
            "adjacency_relative_rmse_gain_vs_target_only",
            "adjacency_wins_target",
        ]
    ].copy()
    out.to_csv(RESULTS / "figure_battery_panel_c.csv", index=False)
    styles = {
        "k": (BLUE, "o", "calendar"),
        "z": (PURPLE, "s", "cycle"),
    }
    q75 = frame.groupby("type")["source_distance"].quantile(0.75).to_dict()
    for kind, (color, marker, label) in styles.items():
        local = frame[frame["type"].eq(kind)]
        hard = local["source_distance"] >= q75[kind]
        ax.scatter(
            local.loc[~hard, "source_distance"],
            100 * local.loc[~hard, "adjacency_relative_rmse_gain_vs_target_only"],
            s=34,
            marker=marker,
            color=color,
            alpha=0.82,
            edgecolor="white",
            linewidth=0.45,
            label=label,
            zorder=3,
        )
        ax.scatter(
            local.loc[hard, "source_distance"],
            100 * local.loc[hard, "adjacency_relative_rmse_gain_vs_target_only"],
            s=49,
            marker=marker,
            facecolor="white",
            edgecolor=color,
            linewidth=1.25,
            label=f"{label} hard OOD",
            zorder=4,
        )
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xlabel("Distance from Stage 1 source conditions")
    ax.set_ylabel("RMSE gain over target-only (%)")
    ax.set_title("Benefit is frequent, but remains condition-selective", loc="left")
    ax.grid(color=GRID, lw=0.5, zorder=0)
    ax.legend(loc="lower left", ncol=2, handletextpad=0.25, columnspacing=0.8)
    ax.text(
        0.98,
        0.96,
        "17/22 groups improve\nhard OOD: calendar −1.2%; cycle +5.6%",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.0,
        color=TEAL_DARK,
        fontweight="bold",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.88, pad=1.4),
    )
    panel_label(ax, "c")


def gate_frame(gate: pd.DataFrame) -> pd.DataFrame:
    kind = gate["outer_heldout_group"].astype(str).str.split("|", regex=False).str[0]
    rows = []
    for label, mask in (
        ("all groups", pd.Series(True, index=gate.index)),
        ("calendar", kind.eq("k")),
        ("cycle", kind.eq("z")),
    ):
        local = gate.loc[mask]
        passed = int(local["gate_pass"].astype(bool).sum())
        total = int(len(local))
        rows.append(
            {
                "stratum": label,
                "groups_admitted": passed,
                "groups_total": total,
                "admission_percent": 100 * passed / total,
            }
        )
    return pd.DataFrame(rows)


def panel_d(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_battery_panel_d.csv", index=False)
    local = frame.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(local))
    colors = [GRAY, BLUE, TEAL]
    bars = ax.barh(y, local["admission_percent"], color=colors, height=0.62, edgecolor="white", linewidth=0.5)
    for bar, row in zip(bars, local.to_dict("records")):
        x = float(row["admission_percent"])
        ax.text(x + 1.5, bar.get_y() + bar.get_height() / 2, f"{row['groups_admitted']}/{row['groups_total']}", va="center", fontsize=6.3, fontweight="bold", color=INK)
    ax.set_yticks(y, local["stratum"])
    ax.set_xlim(0, 60)
    ax.set_xlabel("Condition groups admitted (%)")
    ax.set_title("Hard qualification gate over-abstains", loc="left")
    ax.grid(axis="x", color=GRID, lw=0.55, zorder=0)
    ax.text(0.98, 0.08, "cycle transfer falls back in all 14 groups", transform=ax.transAxes, ha="right", fontsize=5.8, color=RED, fontweight="bold")
    panel_label(ax, "d")


def hypothesis_frame(sensitivity: dict) -> pd.DataFrame:
    rows = []
    for stratum, record in sensitivity["hypothesis_card_results"].items():
        rows.append(
            {
                "stratum": stratum,
                "lead_condition": record["lead"],
                "control_condition": record["control"],
                "lead_retention": record["lead_retention"],
                "control_retention": record["control_retention"],
                "directional_pass": record["directional_pass"],
            }
        )
    return pd.DataFrame(rows)


def panel_e(ax: plt.Axes, frame: pd.DataFrame) -> None:
    frame.to_csv(RESULTS / "figure_battery_panel_e.csv", index=False)
    y = np.array([1, 0], dtype=float)
    colors = {"calendar": BLUE, "cycle": PURPLE}
    for yi, row in zip(y, frame.to_dict("records")):
        color = colors[row["stratum"]]
        ax.plot([row["lead_retention"], row["control_retention"]], [yi, yi], color=color, lw=2.0, alpha=0.72)
        ax.scatter(row["lead_retention"], yi, marker="o", s=48, color=color, edgecolor="white", linewidth=0.55, zorder=3)
        ax.scatter(row["control_retention"], yi, marker="s", s=42, facecolor="white", edgecolor=color, linewidth=1.1, zorder=3)
        ax.text(row["control_retention"] + 0.45, yi, "pass", color=TEAL_DARK, va="center", fontsize=6.1, fontweight="bold")
    ax.set_yticks(y, ["calendar card", "cycle card"])
    ax.set_xlim(87.5, 98.5)
    ax.set_xlabel("Observed retention (%)  ← lower is better")
    ax.set_title("Prewritten source-inspired contrasts pass directionally", loc="left")
    ax.scatter([], [], marker="o", s=35, color=GRAY, label="lead")
    ax.scatter([], [], marker="s", s=35, facecolor="white", edgecolor=GRAY, label="matched control")
    ax.legend(loc="lower right", handletextpad=0.25)
    panel_label(ax, "e")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    sensitivity = json.loads(SENSITIVITY_PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    condition_map = pd.read_csv(MAP_PATH)
    gate = pd.read_csv(GATE_PATH)

    forest = forest_frame(summary)
    gates = gate_frame(gate)
    hypotheses = hypothesis_frame(sensitivity)

    figure = plt.figure(figsize=(7.2, 6.1), constrained_layout=False)
    grid = figure.add_gridspec(
        3,
        2,
        height_ratios=[0.78, 1.35, 1.12],
        width_ratios=[1.0, 1.0],
        hspace=0.56,
        wspace=0.48,
        left=0.09,
        right=0.985,
        top=0.975,
        bottom=0.08,
    )
    ax_a = figure.add_subplot(grid[0, :])
    ax_b = figure.add_subplot(grid[1, 0])
    ax_c = figure.add_subplot(grid[1, 1])
    ax_d = figure.add_subplot(grid[2, 0])
    ax_e = figure.add_subplot(grid[2, 1])

    panel_a(ax_a, audit)
    panel_b(ax_b, forest)
    panel_c(ax_c, condition_map)
    panel_d(ax_d, gates)
    panel_e(ax_e, hypotheses)

    figure.text(
        0.985,
        0.014,
        "Outcome-guided post-release method development; the continuous policy is nominated for independent confirmation",
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
