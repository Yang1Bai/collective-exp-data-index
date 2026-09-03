"""Create the submission-grade multi-target OOD borrowing figure."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
DESIGN = ROOT / "analysis" / "multi_target_ood_borrowing_design.json"
STEM = FIGURES / "multi_target_ood_borrowing"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
mpl.rcParams.update(
    {
        "font.size": 7.0,
        "axes.labelsize": 7.2,
        "axes.titlesize": 7.7,
        "axes.titleweight": "bold",
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.labelsize": 6.4,
        "ytick.labelsize": 6.4,
        "legend.fontsize": 6.2,
        "legend.frameon": False,
    }
)

INK = "#20262E"
MUTED = "#66717C"
GRID = "#E2E7EB"
NEUTRAL = "#C7CED4"
NEUTRAL_DARK = "#7B858D"
BLUE = "#2F6F9F"
BLUE_LIGHT = "#8FB7D4"
TEAL = "#2A8C82"
TEAL_LIGHT = "#9BCDC7"
ORANGE = "#D8833A"
RED = "#B85450"
PASS = "#2E8B74"
PASS_LIGHT = "#D5ECE6"
FAIL = "#C46E72"
FAIL_LIGHT = "#F1D9DB"
WHITE = "#FFFFFF"


DISPLAY = {
    "alloy_ys": "Alloy yield strength",
    "alloy_uts": "Ultimate tensile strength",
    "catalysis_h2": "CO$_2$R H$_2$ selectivity",
    "catalysis_voltage": "Cell voltage",
    "electrolyte_conductivity": "Ionic conductivity",
    "te_electrical": "Electronic conductivity",
    "hydration": "Hydration free energy",
    "solubility": "Aqueous solubility",
    "polymer_tensile": "Polymer tensile strength",
    "polymer_young": "Young's modulus",
    "polymer_tm": "Polymer melting $T$",
    "polymer_crystallization": "Crystallization $T$",
    "te_zt": "Thermoelectric $ZT$",
    "te_seebeck": "Seebeck coefficient",
}

SHORT_EDGE = {
    "alloy_ys": "UTS → yield strength",
    "catalysis_h2": "Voltage → H$_2$ selectivity",
    "electrolyte_conductivity": "Electronic → ionic conductivity",
    "hydration": "Solubility → hydration",
    "polymer_tensile": "Young's modulus → tensile strength",
    "polymer_tm": "Crystallization $T$ → melting $T$",
    "solubility": "Hydration → solubility",
    "te_zt": "Seebeck → $ZT$",
}


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=9.5,
        fontweight="bold",
        ha="left",
        va="bottom",
        color=INK,
    )


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    edges = pd.read_csv(RESULTS / "multi_target_ood_edge_summary.csv")
    targets = pd.read_csv(RESULTS / "multi_target_ood_target_summary.csv")
    summary = json.loads(
        (RESULTS / "multi_target_ood_summary.json").read_text(encoding="utf-8")
    )
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    if summary["status"] != "formal-complete":
        raise AssertionError("Only the verified formal result may populate this figure")
    verified = json.loads(
        (RESULTS / "multi_target_ood_VERIFIED.json").read_text(encoding="utf-8")
    )
    if verified["status"] != "verified-complete" or verified["mode"] != "formal":
        raise AssertionError("Formal result package is not independently verified")
    return edges, targets, summary, design


def draw_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    title: str,
    body: str,
    face: str,
    edge: str,
) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        linewidth=0.9,
        facecolor=face,
        edgecolor=edge,
    )
    ax.add_patch(patch)
    ax.text(
        x + 0.035 * width,
        y + 0.73 * height,
        title,
        ha="left",
        va="center",
        fontsize=6.15,
        fontweight="bold",
        linespacing=1.05,
        color=INK,
    )
    ax.text(
        x + 0.035 * width,
        y + 0.27 * height,
        body,
        ha="left",
        va="center",
        fontsize=5.35,
        linespacing=1.25,
        color=MUTED,
    )


def draw_panel_a(ax: plt.Axes) -> None:
    panel_label(ax, "a", x=-0.03, y=1.02)
    ax.set_title(
        "Frozen OOD-versus-ID comparison",
        loc="left",
        pad=7,
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (
            (0.01, 0.57),
            0.44,
            0.28,
            "1  Define support\nwithout outcomes",
            "Complete development\nfeatures fix distance and\nintact groups.",
            "#EEF3F7",
            BLUE_LIGHT,
        ),
        (
            (0.54, 0.57),
            0.45,
            0.28,
            "2  Separate ID-like\nand OOD scopes",
            "Q1: nearest support\nQ4: farthest support",
            "#EAF5F3",
            TEAL_LIGHT,
        ),
        (
            (0.01, 0.13),
            0.44,
            0.28,
            "3  Hold target\nevidence constant",
            "Same grouped label draw:\ntarget-only vs + donor feature",
            "#F5F2EA",
            ORANGE,
        ),
        (
            (0.54, 0.13),
            0.45,
            0.28,
            "4  Require specific,\ncontrolled gain",
            "$G_{OOD}-G_{ID}$; wrong + shuffled\ndonors; 3 learners; Holm",
            "#F5ECEC",
            FAIL,
        ),
    ]
    for spec in boxes:
        draw_box(ax, *spec)
    for start, end in (
        ((0.45, 0.71), (0.54, 0.71)),
        ((0.765, 0.57), (0.765, 0.42)),
        ((0.54, 0.27), (0.45, 0.27)),
    ):
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=8,
                linewidth=0.9,
                color=NEUTRAL_DARK,
            )
        )
    ax.text(
        0.01,
        0.015,
        "8 recipients · 40 real edges · 8 shuffled controls\n"
        "100 grouped target-label draws",
        ha="left",
        va="bottom",
        fontsize=5.65,
        color=MUTED,
    )


def draw_panel_b(ax: plt.Axes, targets: pd.DataFrame) -> None:
    panel_label(ax, "b")
    order = [
        "te_zt",
        "alloy_ys",
        "catalysis_h2",
        "polymer_tensile",
        "polymer_tm",
        "electrolyte_conductivity",
        "solubility",
        "hydration",
    ]
    frame = targets.set_index("target").loc[order].reset_index()
    frame["edge_label"] = frame["target"].map(SHORT_EDGE)
    frame["edge_type"] = np.where(
        frame["primary_edge_class"].eq("cross-database-neighbor"),
        "Cross-database",
        "Within-database",
    )
    frame.to_csv(RESULTS / "figure_multi_target_ood_panel_b.csv", index=False)

    y = np.arange(len(frame))[::-1]
    ax.axvspan(-8, 0, color="#F8EEEE", zorder=0)
    ax.axvline(0, color=INK, linewidth=0.8, zorder=1)
    ax.axvline(5, color=RED, linewidth=0.9, linestyle=(0, (3, 2)), zorder=1)
    for position, row in zip(y, frame.itertuples(index=False)):
        color = TEAL if row.edge_type == "Cross-database" else BLUE
        ax.plot(
            [100 * row.gain_ood_ci_lo, 100 * row.gain_ood_ci_hi],
            [position, position],
            color=color,
            linewidth=1.6,
            solid_capstyle="round",
            zorder=2,
        )
        ax.scatter(
            100 * row.gain_ood_mean,
            position,
            s=35,
            facecolor=color,
            edgecolor=WHITE,
            linewidth=0.7,
            zorder=3,
        )
    ax.axhline(2.5, color=GRID, linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(frame["edge_label"])
    for tick, edge_type in zip(ax.get_yticklabels(), frame["edge_type"]):
        tick.set_color(TEAL if edge_type == "Cross-database" else INK)
    ax.set_xlim(-8, 15)
    ax.set_ylim(-0.7, len(frame) - 0.3)
    ax.set_xlabel("OOD (Q4) relative RMSE gain (%)")
    ax.set_title("Designated OOD gains fail the complete repair gate", loc="left")
    ax.grid(axis="x", color=GRID, linewidth=0.55)
    ax.text(
        5.25,
        -0.54,
        "5% practical threshold",
        fontsize=5.6,
        color=RED,
        ha="left",
    )
    handles = [
        Line2D([0], [0], marker="o", color=BLUE, label="Within-database", lw=1.5),
        Line2D([0], [0], marker="o", color=TEAL, label="Cross-database", lw=1.5),
    ]
    ax.legend(handles=handles, loc="lower right", handlelength=1.6)
    strongest = frame.loc[frame["gain_ood_mean"].idxmax()]
    ax.annotate(
        f"{100 * strongest.gain_ood_mean:.2f}%\n"
        f"[{100 * strongest.gain_ood_ci_lo:.2f}, {100 * strongest.gain_ood_ci_hi:.2f}]",
        xy=(
            100 * strongest.gain_ood_mean,
            y[frame.index[frame["target"].eq(strongest.target)][0]],
        ),
        xytext=(9.0, 5.5),
        textcoords="data",
        fontsize=5.8,
        color=BLUE,
        arrowprops={"arrowstyle": "-", "color": BLUE, "lw": 0.7},
        ha="left",
        va="center",
    )


def relation_family(row: pd.Series) -> str:
    if row["neighborhood"] == 0:
        return "Distant control"
    if row["primary_edge_class"] == "cross-database-neighbor":
        return "Cross-database neighbor"
    return "Within-domain neighbor"


def draw_panel_c(ax: plt.Axes, edges: pd.DataFrame) -> None:
    panel_label(ax, "c")
    frame = edges[~edges["is_shuffled_control"]].copy()
    frame["relation_family"] = frame.apply(relation_family, axis=1)
    frame.to_csv(RESULTS / "figure_multi_target_ood_panel_c.csv", index=False)
    styles = {
        "Within-domain neighbor": (BLUE, 24),
        "Cross-database neighbor": (TEAL, 28),
        "Distant control": (NEUTRAL_DARK, 19),
    }
    lim = 10.0
    ax.axhspan(0, lim, color="#F3F8F7", zorder=0)
    ax.axhline(0, color=NEUTRAL_DARK, linewidth=0.7)
    ax.axvline(0, color=NEUTRAL_DARK, linewidth=0.7)
    ax.plot([-lim, lim], [-lim, lim], color=ORANGE, linestyle=(0, (3, 2)), lw=0.9)
    for family, group in frame.groupby("relation_family"):
        color, size = styles[family]
        ax.scatter(
            100 * group["gain_id_mean"],
            100 * group["gain_ood_mean"],
            s=size,
            facecolor=color,
            edgecolor="white",
            linewidth=0.45,
            alpha=0.78,
            label=family,
            zorder=2,
        )
    primary = frame[frame["is_designated_primary"]]
    ax.scatter(
        100 * primary["gain_id_mean"],
        100 * primary["gain_ood_mean"],
        s=48,
        facecolor="none",
        edgecolor=INK,
        linewidth=1.0,
        label="Designated primary",
        zorder=3,
    )
    for target, dx, dy in (
        ("alloy_ys", 0.20, -0.75),
        ("electrolyte_conductivity", -1.6, 0.25),
    ):
        row = primary[primary["target"].eq(target)].iloc[0]
        ax.text(
            100 * row["gain_id_mean"] + dx,
            100 * row["gain_ood_mean"] + dy,
            "UTS→YS" if target == "alloy_ys" else "TE→OBELiX",
            fontsize=5.5,
            color=INK,
        )
    ax.set_xlim(-4, 10)
    ax.set_ylim(-4, 10)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("ID-like (Q1) RMSE gain (%)")
    ax.set_ylabel("OOD (Q4) RMSE gain (%)")
    ax.set_title("Average transfer and OOD-specific repair are distinct", loc="left")
    ax.grid(color=GRID, linewidth=0.5)
    ax.text(
        9.7,
        9.25,
        "OOD-enriched",
        fontsize=5.7,
        color=TEAL,
        ha="right",
    )
    ax.text(
        9.7,
        8.45,
        "$G_{OOD}>G_{ID}$",
        fontsize=5.5,
        color=MUTED,
        ha="right",
    )
    ax.legend(
        loc="lower right",
        handletextpad=0.35,
        borderpad=0.2,
        labelspacing=0.25,
    )


def build_gate_matrix(
    edges: pd.DataFrame, design: dict
) -> tuple[pd.DataFrame, list[str], list[str]]:
    gate = design["edge_gate"]
    criteria = [
        ("Gain ≥5%", lambda row: row.gain_ood_mean >= gate["mean_ood_relative_rmse_gain_minimum"]),
        ("OOD CI >0", lambda row: row.gain_ood_ci_lo > 0),
        ("OOD $R^2$ >0", lambda row: row.aug_ood_r2_mean > 0),
        ("≥80% repeats", lambda row: row.positive_ood_repeat_fraction >= 0.8),
        ("OOD>ID CI >0", lambda row: row.gain_specific_ci_lo > 0),
        ("> wrong", lambda row: row.primary_minus_wrong_ci_lo > 0),
        ("> shuffle", lambda row: row.primary_minus_shuffled_ci_lo > 0),
        ("≥2/3 learners", lambda row: row.positive_ood_learners >= 2),
        ("Holm $P$<0.05", lambda row: row.holm_p < 0.05),
        ("No overlap", lambda row: row.get("post_exclusion_overlap", 0) == 0),
    ]
    edge_order = [
        "te_zt",
        "alloy_ys",
        "catalysis_h2",
        "polymer_tensile",
        "polymer_tm",
        "electrolyte_conductivity",
        "solubility",
        "hydration",
    ]
    target_rows = (
        edges[edges["is_designated_primary"]]
        .set_index("target")
        .loc[edge_order]
        .reset_index()
    )
    long_rows = []
    for row in target_rows.itertuples(index=False):
        values = row._asdict()
        series = pd.Series(values)
        for label, test in criteria:
            long_rows.append(
                {
                    "target": row.target,
                    "edge_label": SHORT_EDGE[row.target],
                    "criterion": label.replace("\n", " "),
                    "pass": int(bool(test(series))),
                }
            )
    long = pd.DataFrame(long_rows)
    long.to_csv(RESULTS / "figure_multi_target_ood_panel_d.csv", index=False)
    matrix = (
        long.pivot(index="target", columns="criterion", values="pass")
        .reindex(
            index=edge_order,
            columns=[label.replace("\n", " ") for label, _ in criteria],
        )
        .astype(int)
    )
    return matrix, [SHORT_EDGE[value] for value in edge_order], [value[0] for value in criteria]


def draw_panel_d(
    ax: plt.Axes, edges: pd.DataFrame, summary: dict, design: dict
) -> None:
    panel_label(ax, "d")
    matrix, row_labels, column_labels = build_gate_matrix(edges, design)
    cmap = ListedColormap([FAIL_LIGHT, PASS_LIGHT])
    ax.imshow(matrix.to_numpy(), cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(column_labels)))
    ax.set_xticklabels(
        column_labels,
        rotation=37,
        ha="right",
        rotation_mode="anchor",
        fontsize=5.55,
    )
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            passed = bool(matrix.iloc[row, column])
            ax.text(
                column,
                row,
                "P" if passed else "F",
                ha="center",
                va="center",
                fontsize=6.3,
                color=PASS if passed else FAIL,
                fontweight="bold",
            )
    ax.axhline(4.5, color=WHITE, linewidth=1.4)
    ax.set_title("No designated edge satisfies the complete conjunctive gate", loc="left")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    programme = summary["programme_inference"]
    cross = summary["cross_database_inference"]
    ax.text(
        0.0,
        -0.24,
        "Programme mean OOD gain "
        f"{100 * programme['mean_primary_ood_gain']:+.2f}% "
        f"[{100 * programme['ci95'][0]:+.2f}, {100 * programme['ci95'][1]:+.2f}]; "
        f"full passes: {programme['programme_clusters_with_full_pass']}/7 programmes, "
        f"{cross['full_passes']}/{cross['designated_edges']} cross-database edges.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.0,
        color=INK,
    )
    ax.text(
        0.0,
        -0.34,
        "Intervals are conditional on the frozen data snapshot and evaluation groups.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=5.6,
        color=MUTED,
    )


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    edges, targets, summary, design = load_data()
    fig = plt.figure(figsize=(183 / 25.4, 145 / 25.4), constrained_layout=False)
    grid = fig.add_gridspec(
        2,
        2,
        width_ratios=[0.43, 0.57],
        height_ratios=[0.47, 0.53],
        left=0.075,
        right=0.985,
        top=0.955,
        bottom=0.105,
        wspace=0.42,
        hspace=0.43,
    )
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[1, 0])
    ax_d = fig.add_subplot(grid[1, 1])
    draw_panel_a(ax_a)
    draw_panel_b(ax_b, targets)
    draw_panel_c(ax_c, edges)
    draw_panel_d(ax_d, edges, summary, design)

    fig.savefig(STEM.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(STEM.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(STEM.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(
        STEM.with_suffix(".tiff"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    print(
        json.dumps(
            {
                "status": "complete",
                "figure": str(STEM),
                "targets": len(targets),
                "real_edges": int((~edges["is_shuffled_control"]).sum()),
                "primary_edges": int(edges["is_designated_primary"].sum()),
                "full_primary_passes": int(
                    (targets["classification"] == "ood-repair-gate-passed").sum()
                ),
                "outputs": [
                    str(STEM.with_suffix(extension))
                    for extension in (".svg", ".pdf", ".png", ".tiff")
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
