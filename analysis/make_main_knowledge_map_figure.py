"""Create the submission-grade main knowledge-borrowing figure."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, RESULTS, ensure_output_dirs

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams.update({
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7.3,
    "axes.labelsize": 7.5,
    "axes.titlesize": 8.4,
    "axes.titleweight": "bold",
    "axes.linewidth": 0.7,
    "xtick.labelsize": 6.8,
    "ytick.labelsize": 6.8,
    "legend.fontsize": 6.5,
    "legend.frameon": False,
    "axes.spines.right": False,
    "axes.spines.top": False,
})

BLUE = "#0F4D92"
BLUE_LIGHT = "#77A9D7"
TEAL = "#2A9D8F"
ORANGE = "#E28E2C"
RED = "#B64342"
GRAY = "#767676"
LIGHT_GRAY = "#D8D8D8"
BLACK = "#272727"


def panel_label(ax, label: str) -> None:
    ax.text(-0.13, 1.05, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def panel_a(ax) -> None:
    pairs = pd.read_csv(RESULTS / "strength_law_paired_rows.csv")
    summary = json.loads((RESULTS / "strength_law_summary.json").read_text(encoding="utf-8"))
    pairs.to_csv(RESULTS / "figure_main_panel_a.csv", index=False)
    styles = {
        "borg": (BLUE, "Borg"),
        "birdshot": (ORANGE, "BIRDSHOT"),
    }
    for label, group in pairs.groupby("dataset_label"):
        color, display = styles[label]
        ax.scatter(group["log_uts"], group["log_ys"], s=8, alpha=0.28 if label == "borg" else 0.52,
                   color=color, edgecolor="none", label=f"{display} (n={len(group)})")
        fit = summary["fits"][label]
        xx = np.linspace(group["log_uts"].min(), group["log_uts"].max(), 100)
        ax.plot(xx, fit["intercept"] + fit["slope"] * xx, color=color, lw=1.8)
    ax.set(
        xlabel=r"log$_{10}$ ultimate tensile strength (MPa)",
        ylabel=r"log$_{10}$ yield strength (MPa)",
        title="A strong source calibration fails to transport",
    )
    ax.legend(loc="lower right", handletextpad=0.4)
    ax.text(0.03, 0.96, f"Borg $R^2$ = {summary['fits']['borg']['r2']:.2f}", transform=ax.transAxes,
            ha="left", va="top", color=BLUE, fontweight="bold")
    ax.text(0.03, 0.88, f"BIRDSHOT $R^2$ = {summary['fits']['birdshot']['r2']:.2f}", transform=ax.transAxes,
            ha="left", va="top", color=ORANGE, fontweight="bold")
    ax.text(0.03, 0.80, f"Borg → BIRDSHOT $R^2$ = {summary['borg_to_birdshot']['external_r2']:.2f}",
            transform=ax.transAxes, ha="left", va="top", color=RED, fontweight="bold")
    ax.text(0.03, 0.70, "median UTS/YS: 1.36 → 2.72", transform=ax.transAxes,
            ha="left", va="top", color=BLACK)
    panel_label(ax, "a")


def panel_b(ax) -> None:
    kit = pd.read_csv(RESULTS / "kit_temperature_edges.csv")
    calisol = pd.read_csv(RESULTS / "calisol_external_edges.csv")
    kit_summary = json.loads(
        (RESULTS / "kit_temperature_summary.json").read_text(encoding="utf-8")
    )
    calisol_summary = json.loads(
        (RESULTS / "calisol_external_summary.json").read_text(encoding="utf-8")
    )
    selections = [
        ("KIT", kit, "temperature_-20_C", "KIT −20 °C (ΔT 10; primary)", TEAL, "o", 8.5, True),
        ("KIT", kit, "temperature_0_C", "KIT 0 °C (ΔT 30)", BLUE_LIGHT, "o", 7.5, False),
        ("KIT", kit, "temperature_30_C", "KIT 30 °C (ΔT 60)", GRAY, "o", 6.5, False),
        ("KIT", kit, "temperature_60_C", "KIT 60 °C (ΔT 90)", GRAY, "o", 5.5, False),
        ("KIT", kit, "shuffled_temperature_-20_C", "KIT shuffled −20 °C", RED, "o", 4.5, False),
        (
            "CALiSol",
            calisol,
            "temperature_-30_C",
            "CALiSol −30 °C (ΔT 10; primary)",
            ORANGE,
            "s",
            2.8,
            True,
        ),
        ("CALiSol", calisol, "temperature_0_C", "CALiSol 0 °C (ΔT 40 control)", GRAY, "s", 1.8, False),
        (
            "CALiSol",
            calisol,
            "shuffled_temperature_-30_C",
            "CALiSol shuffled −30 °C",
            RED,
            "s",
            0.8,
            False,
        ),
    ]
    rows = []
    for evidence_layer, source_frame, source, label, color, marker, y, is_primary in selections:
        row = source_frame[source_frame["source"] == source].iloc[0].to_dict()
        row.update(
            {
                "evidence_layer": evidence_layer,
                "label": label,
                "effect": row["relative_rmse_improvement_mean"],
                "lo": row["relative_rmse_ci_lo"],
                "hi": row["relative_rmse_ci_hi"],
                "color": color,
                "marker": marker,
                "plot_y": y,
                "is_primary": is_primary,
            }
        )
        rows.append(row)
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "figure_main_panel_b.csv", index=False)
    for row in frame.to_dict("records"):
        yi = float(row["plot_y"])
        is_primary = bool(row["is_primary"])
        ax.plot(
            np.asarray([row["lo"], row["hi"]]) * 100,
            [yi, yi],
            color=row["color"],
            lw=2.2 if is_primary else 1.25,
            zorder=4 if is_primary else 2,
        )
        ax.scatter(
            row["effect"] * 100,
            yi,
            s=52 if is_primary else 24,
            marker=row["marker"],
            color=row["color"],
            edgecolor=BLACK if is_primary else "white",
            linewidth=0.8 if is_primary else 0.5,
            zorder=5 if is_primary else 3,
        )
    ax.axvline(0, color=GRAY, lw=0.8)
    ax.axvline(5, color=RED, lw=0.9, ls=(0, (3, 2)))
    ax.axhline(3.65, color=LIGHT_GRAY, lw=0.7)
    ax.set_yticks(frame["plot_y"], frame["label"])
    for tick, is_primary in zip(ax.get_yticklabels(), frame["is_primary"]):
        if bool(is_primary):
            tick.set_fontweight("bold")
    ax.set(xlabel="Relative held-out RMSE reduction (%)",
           title="Only the within-campaign primary clears all gates",
           ylim=(0.2, 9.15), xlim=(-7.0, 23.0))
    ax.text(5.35, 0.24, "frozen 5% gate", color=RED, fontsize=6.1, ha="left")
    # Put the two claim-bearing numerical labels above, not on top of, their
    # confidence intervals. Opaque callouts previously hid these primary marks.
    primary_rows = frame[frame["is_primary"]].set_index("evidence_layer")
    kit_primary = primary_rows.loc["KIT"]
    calisol_primary = primary_rows.loc["CALiSol"]
    ax.text(
        float(kit_primary["effect"]) * 100,
        float(kit_primary["plot_y"]) + 0.30,
        f"{kit_primary['effect'] * 100:.2f}% [{kit_primary['lo'] * 100:.2f},{kit_primary['hi'] * 100:.2f}]; p={kit_summary['primary_permutation_p']:.3f}",
        ha="center",
        va="bottom",
        fontsize=5.9,
        color=TEAL,
        fontweight="bold",
    )
    ax.text(
        float(calisol_primary["effect"]) * 100,
        float(calisol_primary["plot_y"]) + 0.28,
        f"{calisol_primary['effect'] * 100:.2f}% [{calisol_primary['lo'] * 100:.2f},{calisol_primary['hi'] * 100:.2f}]",
        ha="center",
        va="bottom",
        fontsize=5.9,
        color=ORANGE,
        fontweight="bold",
    )
    ax.text(
        22.5,
        2.28,
        f"CALiSol R² {calisol_summary['pooled_base_r2']:.2f} → {calisol_summary['pooled_augmented_r2']:.2f}",
        ha="right",
        va="center",
        fontsize=5.7,
        color=BLACK,
    )
    panel_label(ax, "b")


def panel_c(ax) -> None:
    metrics = pd.read_csv(RESULTS / "calisol_anchored_delta_article_metrics.csv")
    summary = json.loads(
        (RESULTS / "calisol_anchored_delta_summary.json").read_text(
            encoding="utf-8"
        )
    )
    primary = metrics[
        (metrics["anchor_budget"] == 1)
        & (metrics["alpha"] == 10.0)
        & metrics["model"].isin(
            ["neighbor_absolute_ridge", "neighbor_delta_ridge"]
        )
    ].pivot(index="article_doi", columns="model", values="rmse")
    primary = primary.reset_index().sort_values("article_doi", kind="stable")
    primary["article_id"] = [f"A{i:02d}" for i in range(1, len(primary) + 1)]
    primary["improved"] = (
        primary["neighbor_delta_ridge"] < primary["neighbor_absolute_ridge"]
    )
    primary["relative_gain"] = 1.0 - (
        primary["neighbor_delta_ridge"] / primary["neighbor_absolute_ridge"]
    )
    primary.to_csv(RESULTS / "figure_main_panel_c.csv", index=False)

    improved = primary["improved"].to_numpy(bool)
    ax.scatter(
        primary.loc[improved, "neighbor_absolute_ridge"],
        primary.loc[improved, "neighbor_delta_ridge"],
        s=34,
        marker="o",
        color=TEAL,
        edgecolor="white",
        linewidth=0.6,
        label="improved article",
        zorder=3,
    )
    ax.scatter(
        primary.loc[~improved, "neighbor_absolute_ridge"],
        primary.loc[~improved, "neighbor_delta_ridge"],
        s=39,
        marker="X",
        color=RED,
        edgecolor="white",
        linewidth=0.5,
        label="harmful article",
        zorder=4,
    )
    upper = float(
        max(
            primary["neighbor_absolute_ridge"].max(),
            primary["neighbor_delta_ridge"].max(),
        )
        * 1.08
    )
    ax.plot([0, upper], [0, upper], color=GRAY, lw=0.9, ls=(0, (3, 2)))
    label_offsets = {
        "A05": (4, 4),
        "A08": (5, -10),
        "A09": (5, 5),
        "A10": (5, 5),
        "A11": (5, 5),
    }
    for row in primary.itertuples(index=False):
        if not bool(row.improved) or float(row.relative_gain) > 0.15:
            offset = label_offsets.get(str(row.article_id), (3, 3))
            ax.annotate(
                str(row.article_id),
                (row.neighbor_absolute_ridge, row.neighbor_delta_ridge),
                xytext=offset,
                textcoords="offset points",
                fontsize=5.4,
                color=RED if not bool(row.improved) else TEAL,
                fontweight="bold",
            )
    effect = summary["primary"]
    ax.text(
        0.04,
        0.96,
        "macro-RMSE 0.490 → 0.456\n"
        f"gain {effect['relative_macro_rmse_gain_vs_neighbor_absolute'] * 100:.2f}% "
        f"[{effect['article_bootstrap_ci95'][0] * 100:.2f},"
        f"{effect['article_bootstrap_ci95'][1] * 100:.2f}%]\n"
        f"8/11 articles; exact p={effect['exact_one_sided_sign_flip_p']:.3f}\n"
        f"shuffled-contrast p={effect['shuffled_delta_permutation_p']:.3f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.2,
        color=BLACK,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.86, "pad": 1.5},
    )
    ax.set(
        xlabel=r"Absolute donor RMSE (log$_{10}$ mS cm$^{-1}$)",
        ylabel=r"Contrast donor RMSE (log$_{10}$ mS cm$^{-1}$)",
        title="One anchor repairs part of the article boundary",
        xlim=(0, upper),
        ylim=(0, upper),
    )
    ax.set_aspect("equal", adjustable="box")
    ax.legend(loc="lower right", handletextpad=0.4)
    panel_label(ax, "c")


def panel_d(ax) -> None:
    fits = pd.read_csv(RESULTS / "isodb_isosteric_primary_fits.csv")
    summary = json.loads((RESULTS / "isodb_compensation_summary.json").read_text(encoding="utf-8"))
    universality = json.loads((RESULTS / "isodb_universality_summary.json").read_text(encoding="utf-8"))
    fits[[
        "system_id", "doi", "adsorbate_name", "Qst_kJ_mol", "vanthoff_intercept",
        "temperature_harmonic_K",
    ]].to_csv(RESULTS / "figure_main_panel_d.csv", index=False)
    top = fits["adsorbate_name"].value_counts().head(4).index.tolist()
    palette = {top[0]: BLUE, top[1]: TEAL, top[2]: ORANGE, top[3]: "#9A4D8E"}
    other = fits[~fits["adsorbate_name"].isin(top)]
    ax.scatter(other["Qst_kJ_mol"], other["vanthoff_intercept"], s=6, alpha=0.12,
               color=GRAY, edgecolor="none", label="other adsorbates")
    for name in top:
        group = fits[fits["adsorbate_name"] == name]
        ax.scatter(group["Qst_kJ_mol"], group["vanthoff_intercept"], s=7, alpha=0.35,
                   color=palette[name], edgecolor="none", label=name)
    primary = summary["primary"]
    xx = np.linspace(0, min(200, fits["Qst_kJ_mol"].max()), 200)
    ax.plot(xx, primary["intercept"] + primary["slope"] * xx, color=BLACK, lw=1.6, label="pooled fit")
    ax.set(xlabel=r"Isosteric heat $Q_{st}$ (kJ mol$^{-1}$)", ylabel="van’t Hoff intercept",
           title="A strong pooled pattern still needs condition gates")
    ax.legend(loc="lower right", ncol=2, columnspacing=0.8, handletextpad=0.3)
    note_box = {"facecolor": "white", "edgecolor": "none", "alpha": 0.84, "pad": 1.2}
    ax.text(0.03, 0.97, f"pooled $R^2$={primary['r2']:.3f}", transform=ax.transAxes,
            ha="left", va="top", fontweight="bold", bbox=note_box)
    ax.text(0.03, 0.89, f"$T_{{iso}}$={primary['T_iso_K']:.0f} K; median $T_H$={primary['temperature_harmonic_median_K']:.0f} K",
            transform=ax.transAxes, ha="left", va="top", bbox=note_box)
    ax.text(0.03, 0.81, f"Krug-null median $R^2$={summary['krug_null']['r2_median']:.3f}",
            transform=ax.transAxes, ha="left", va="top", bbox=note_box)
    ax.text(0.03, 0.73,
            f"family intercepts: DOI-cluster p={universality['pooled_vs_family_intercepts']['p_doi_wild_cluster']:.4f}",
            transform=ax.transAxes, ha="left", va="top", color=RED, fontweight="bold", bbox=note_box)
    panel_label(ax, "d")


def main() -> None:
    ensure_output_dirs()
    # Allow for the tight-bounding-box expansion from exterior panel labels
    # while keeping the exported width within a 183 mm double-column limit.
    figure = plt.figure(figsize=(6.64, 6.65), layout="constrained")
    grid = figure.add_gridspec(2, 2, width_ratios=[1.08, 0.92], height_ratios=[0.95, 1.05])
    axes = [figure.add_subplot(grid[0, 0]), figure.add_subplot(grid[0, 1]),
            figure.add_subplot(grid[1, 0]), figure.add_subplot(grid[1, 1])]
    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])
    panel_d(axes[3])
    base = FIGURES / "main_knowledge_borrowing"
    figure.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    figure.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    figure.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    figure.savefig(
        base.with_suffix(".tif"),
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)
    print(base)


if __name__ == "__main__":
    main()
