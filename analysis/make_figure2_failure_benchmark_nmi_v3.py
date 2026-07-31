"""NMI-v3 Figure 2: fit strength and generic features do not imply transfer."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure2_failure_benchmark_nmi_v3"
SOURCE = SOURCE_DIR / "figure2_failure_benchmark_nmi_v3.csv"

NAVY = "#173B6C"
BLUE = "#5B9BD0"
TEAL = "#27958D"
ORANGE = "#E98A32"
CORAL = "#CF6258"
GREEN = "#469A6A"
INK = "#24303D"
MID = "#7A8795"
GRID = "#D9E1E8"
PALE_BLUE = "#EDF4F9"
PALE_CORAL = "#FAECE9"
PALE_TEAL = "#EAF5F1"

TARGET_ORDER = [
    "te_zt", "alloy_ys", "catalysis_h2", "polymer_tensile",
    "polymer_tm", "electrolyte_conductivity", "solubility", "hydration",
]
TARGET_LABELS = {
    "te_zt": "Thermoelectric figure of merit",
    "alloy_ys": "Alloy yield strength",
    "catalysis_h2": "Catalytic H$_2$ selectivity",
    "polymer_tensile": "Polymer tensile strength",
    "polymer_tm": "Polymer melting temperature",
    "electrolyte_conductivity": "Ionic conductivity",
    "solubility": "Aqueous solubility",
    "hydration": "Hydration free energy",
}

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 6.2,
    "axes.titlesize": 6.8,
    "axes.labelsize": 6.2,
    "xtick.labelsize": 5.6,
    "ytick.labelsize": 5.6,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.03) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.0,
            fontweight="bold", ha="left", va="bottom", color="black")


def load() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    alloy = pd.read_csv(RESULTS / "figure_main_panel_a.csv")
    edges = pd.read_csv(RESULTS / "multi_target_ood_edge_summary.csv")
    summary = json.loads((RESULTS / "multi_target_ood_summary.json").read_text(encoding="utf-8"))
    design = json.loads((ROOT / "analysis" / "multi_target_ood_borrowing_design.json").read_text(encoding="utf-8"))
    verified = json.loads((RESULTS / "multi_target_ood_VERIFIED.json").read_text(encoding="utf-8"))
    if verified.get("status") != "verified-complete" or verified.get("mode") != "formal":
        raise RuntimeError("Formal multi-target result is not independently verified")
    return alloy, edges, summary, design


def metric_pill(ax: plt.Axes, x: float, y: float, text: str, color: str,
                face: str = "white", bold: bool = False) -> None:
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=5.7, color=color, fontweight="bold" if bold else "normal",
            bbox={"boxstyle": "round,pad=0.22,rounding_size=0.7",
                  "facecolor": face, "edgecolor": "none", "alpha": 0.94})


def panel_a(ax: plt.Axes, alloy: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "a", -0.14, 1.03)
    ax.set_title("A real in-programme relation fails unchanged transport", loc="left", pad=7)
    source = alloy[alloy["dataset_label"].eq("borg")].copy()
    target = alloy[alloy["dataset_label"].eq("birdshot")].copy()
    donor = LinearRegression().fit(source[["log_uts"]], source["log_ys"])
    recipient = LinearRegression().fit(target[["log_uts"]], target["log_ys"])
    xx = np.linspace(alloy["log_uts"].min() - 0.03, alloy["log_uts"].max() + 0.03, 200)

    ax.scatter(source["log_uts"], source["log_ys"], s=8.5, color=BLUE,
               alpha=0.24, edgecolor="none", rasterized=True)
    ax.scatter(target["log_uts"], target["log_ys"], s=11, color=ORANGE,
               alpha=0.52, edgecolor="white", linewidth=0.2, rasterized=True)
    xx_frame = pd.DataFrame({"log_uts": xx})
    ax.plot(xx, donor.predict(xx_frame), color=NAVY, lw=1.8, zorder=4)
    ax.plot(xx, recipient.predict(xx_frame), color=ORANGE, lw=1.15,
            ls=(0, (4, 2)), zorder=4)

    r2_source = r2_score(source["log_ys"], donor.predict(source[["log_uts"]]))
    r2_target = r2_score(target["log_ys"], recipient.predict(target[["log_uts"]]))
    r2_transport = r2_score(target["log_ys"], donor.predict(target[["log_uts"]]))
    med_source = float(source["uts_ys_ratio"].median())
    med_target = float(target["uts_ys_ratio"].median())

    metric_pill(ax, .035, .965, f"source fit  $R^2$ = {r2_source:.3f}", NAVY,
                PALE_BLUE, True)
    metric_pill(ax, .035, .875, f"recipient refit  $R^2$ = {r2_target:.3f}", ORANGE)
    metric_pill(ax, .035, .785, f"unchanged transfer  $R^2$ = {r2_transport:.3f}",
                CORAL, PALE_CORAL, True)
    ax.text(.965, .055, f"median UTS/YS\n{med_source:.2f} to {med_target:.2f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.6,
            color=INK, linespacing=1.15)
    ax.set_xlabel("log$_{10}$ ultimate tensile strength (MPa)")
    ax.set_ylabel("log$_{10}$ yield strength (MPa)")
    ax.grid(color=GRID, lw=0.42)
    ax.legend(handles=[
        Line2D([0], [0], marker="o", linestyle="none", color=BLUE,
               label="source programme"),
        Line2D([0], [0], marker="o", linestyle="none", color=ORANGE,
               label="independent recipient"),
    ], loc="lower left", frameon=False, handletextpad=.25, borderpad=0)
    return pd.DataFrame([
        {"panel": "a", "measure": "source_internal_r2", "estimate": r2_source},
        {"panel": "a", "measure": "recipient_internal_r2", "estimate": r2_target},
        {"panel": "a", "measure": "transported_r2", "estimate": r2_transport},
        {"panel": "a", "measure": "source_median_uts_ys", "estimate": med_source},
        {"panel": "a", "measure": "recipient_median_uts_ys", "estimate": med_target},
    ])


def ordered_real_edges(edges: pd.DataFrame) -> pd.DataFrame:
    real = edges.loc[~edges["is_shuffled_control"].astype(bool)].copy()
    blocks = []
    for target in TARGET_ORDER:
        block = real[real["target"].eq(target)].copy()
        block["slot_order"] = np.where(block["is_designated_primary"], -1,
                                       10 - block["neighborhood"])
        block = block.sort_values(["slot_order", "source"]).reset_index(drop=True)
        if len(block) != 5:
            raise RuntimeError(f"Expected five real edges for {target}; found {len(block)}")
        block["donor_slot"] = np.arange(1, 6)
        blocks.append(block)
    return pd.concat(blocks, ignore_index=True)


def panel_b(ax: plt.Axes, edges: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "b", -0.08, 1.03)
    ax.set_title("Relative gains are small, unstable or non-specific", loc="left", pad=7)
    frame = ordered_real_edges(edges)
    matrix = frame.pivot(index="target", columns="donor_slot", values="gain_ood_mean").loc[TARGET_ORDER]
    values = 100 * matrix.to_numpy()
    cmap = LinearSegmentedColormap.from_list("gain", [CORAL, "#FAFAFB", TEAL], N=256)
    norm = TwoSlopeNorm(vmin=-14, vcenter=0, vmax=14)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(["declared\ndonor", "candidate\n2", "candidate\n3",
                        "candidate\n4", "distant\ncontrol"])
    ax.set_yticks(np.arange(8))
    ax.set_yticklabels([TARGET_LABELS[t] for t in TARGET_ORDER])
    ax.tick_params(length=0)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            value = values[i, j]
            ax.text(j, i, f"{value:+.1f}", ha="center", va="center",
                    fontsize=5.6, color="white" if abs(value) > 7 else INK,
                    fontweight="bold" if j == 0 else "normal")
            if j == 0:
                ax.add_patch(Rectangle((j - .49, i - .49), .98, .98, fill=False,
                                       edgecolor=NAVY, lw=.75))
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = ax.figure.colorbar(image, ax=ax, orientation="horizontal",
                             fraction=.07, pad=.17, aspect=30)
    cbar.set_label("relative far-OOD RMSE gain (%)   |   positive means lower error",
                   labelpad=1)
    cbar.outline.set_visible(False)
    export = frame[["target", "source", "donor_slot", "is_designated_primary",
                    "neighborhood", "gain_ood_mean", "gain_ood_ci_lo",
                    "gain_ood_ci_hi", "aug_ood_r2_mean", "classification"]].copy()
    export.insert(0, "panel", "b")
    return export


def collapsed_gate(edges: pd.DataFrame, design: dict) -> pd.DataFrame:
    gate = design["edge_gate"]
    designated = edges[edges["is_designated_primary"].astype(bool)].set_index("target").loc[TARGET_ORDER]
    rows = []
    for target, row in designated.iterrows():
        checks = {
            "utility": (row.gain_ood_mean >= gate["mean_ood_relative_rmse_gain_minimum"]
                        and row.gain_ood_ci_lo > 0 and row.aug_ood_r2_mean > 0),
            "robustness": (row.positive_ood_repeat_fraction >= .8
                           and row.positive_ood_learners >= 2),
            "OOD specificity": (row.gain_specific_ci_lo > 0
                                and row.primary_minus_wrong_ci_lo > 0
                                and row.primary_minus_shuffled_ci_lo > 0),
            "adjusted inference": row.holm_p < .05,
            "no overlap": row.get("post_exclusion_overlap", 0) == 0,
        }
        rows.extend({"target": target, "criterion": key,
                     "pass": int(bool(value))} for key, value in checks.items())
    return pd.DataFrame(rows)


def panel_c(ax: plt.Axes, edges: pd.DataFrame, design: dict, summary: dict) -> pd.DataFrame:
    panel_label(ax, "c", -0.02, 1.03)
    ax.set_title("The complete gate rejects every declared edge", loc="left", pad=7)
    long = collapsed_gate(edges, design)
    columns = ["utility", "robustness", "OOD specificity", "adjusted inference", "no overlap"]
    matrix = long.pivot(index="target", columns="criterion", values="pass").loc[TARGET_ORDER, columns]
    ax.set_xlim(-.55, 7.65)
    ax.set_ylim(7.65, -.85)
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(["useful absolute\nprediction", "repeat + learner\nrobustness",
                        "OOD + donor\nspecificity", "Holm-adjusted\n$P<0.05$",
                        "zero record\noverlap"])
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=2)
    ax.set_yticks(np.arange(8))
    ax.set_yticklabels(["Thermoelectric", "Alloy strength", "Catalytic H$_2$",
                        "Polymer tensile", "Polymer melting", "Ionic conductivity",
                        "Aqueous solubility", "Hydration free energy"])
    ax.tick_params(axis="y", length=0)
    for i in range(8):
        if i % 2 == 0:
            ax.axhspan(i - .5, i + .5, color="#F7F9FB", zorder=0)
        for j in range(5):
            passed = bool(matrix.iloc[i, j])
            if passed:
                ax.scatter(j, i, s=25, facecolor=GREEN, edgecolor="white",
                           linewidth=.45, zorder=3)
                ax.plot([j - .040, j - .008, j + .055],
                        [i, i + .050, i - .060], color="white", lw=.65,
                        solid_capstyle="round", zorder=4)
            else:
                ax.scatter(j, i, s=20, facecolor=PALE_CORAL, edgecolor="none", zorder=2)
                ax.text(j, i, "×", ha="center", va="center", color=CORAL,
                        fontsize=6.4, fontweight="bold", zorder=4)
    for j, count in enumerate(matrix.sum(axis=0).astype(int)):
        ax.text(j, -.63, f"{count}/8", ha="center", va="bottom", fontsize=5.2,
                color=GREEN if count else CORAL, fontweight="bold")
    ax.plot([5.35, 5.35], [-.45, 7.45], color=GRID, lw=.7)
    programme = summary["programme_inference"]
    card = FancyBboxPatch((5.62, .55), 1.72, 4.15,
                          boxstyle="round,pad=.05,rounding_size=.10",
                          facecolor=PALE_CORAL, edgecolor="#E7C9C4", lw=.6)
    ax.add_patch(card)
    ax.text(6.48, 1.25, "0 / 40", ha="center", va="center", fontsize=12,
            color=CORAL, fontweight="bold")
    ax.text(6.48, 2.12, "real edges pass\nthe complete OOD-repair gate",
            ha="center", va="center", fontsize=5.8, color=INK, linespacing=1.25)
    ax.text(6.48, 3.58,
            f"programme mean\n{100*programme['mean_primary_ood_gain']:+.2f}% "
            f"[{100*programme['ci95'][0]:+.2f}, {100*programme['ci95'][1]:+.2f}]",
            ha="center", va="center", fontsize=5.4, color=MID, linespacing=1.2)
    ax.text(6.48, 5.72, "Relative gain alone is\nnot sufficient evidence of transfer.",
            ha="center", va="center", fontsize=5.6, color=INK,
            fontweight="bold", linespacing=1.2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return long.assign(panel="c")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    alloy, edges, summary, design = load()
    fig = plt.figure(figsize=(7.204724, 5.314961))  # 183 x 135 mm
    outer = fig.add_gridspec(2, 1, height_ratios=[.56, .44], left=.130,
                             right=.975, bottom=.075, top=.945, hspace=.43)
    top = outer[0].subgridspec(1, 2, width_ratios=[.43, .57], wspace=.36)
    ax_a = fig.add_subplot(top[0, 0])
    ax_b = fig.add_subplot(top[0, 1])
    ax_c = fig.add_subplot(outer[1, 0])
    outputs = [panel_a(ax_a, alloy), panel_b(ax_b, edges),
               panel_c(ax_c, edges, design, summary)]
    pd.concat(outputs, ignore_index=True, sort=False).to_csv(SOURCE, index=False)
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
