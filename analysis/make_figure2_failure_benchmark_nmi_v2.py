"""Figure 2: why strong fits and generic donor features do not imply OOD transfer."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure2_failure_benchmark_nmi_v2"
SOURCE = SOURCE_DIR / "figure2_failure_benchmark_nmi_v2.csv"

NAVY = "#173B6C"
BLUE = "#3478BD"
TEAL = "#148A82"
ORANGE = "#E8872E"
CORAL = "#C95A50"
INK = "#243143"
MID = "#7E8998"
GRID = "#D8DEE8"
PALE = "#F5F8FB"
LIGHT_BLUE = "#DCEAF6"
LIGHT_CORAL = "#F6E1DE"
GREEN = "#3C9662"

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
    "font.size": 6.4,
    "axes.titlesize": 7.0,
    "axes.labelsize": 6.4,
    "xtick.labelsize": 5.8,
    "ytick.labelsize": 5.8,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
})


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.03) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.0, fontweight="bold",
            ha="left", va="bottom", color="black")


def load() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    alloy = pd.read_csv(RESULTS / "figure_main_panel_a.csv")
    edges = pd.read_csv(RESULTS / "multi_target_ood_edge_summary.csv")
    summary = json.loads((RESULTS / "multi_target_ood_summary.json").read_text(encoding="utf-8"))
    design = json.loads((ROOT / "analysis" / "multi_target_ood_borrowing_design.json").read_text(encoding="utf-8"))
    verified = json.loads((RESULTS / "multi_target_ood_VERIFIED.json").read_text(encoding="utf-8"))
    if verified.get("status") != "verified-complete" or verified.get("mode") != "formal":
        raise RuntimeError("Formal multi-target result is not independently verified")
    return alloy, edges, summary, design


def panel_a(ax: plt.Axes, alloy: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "a", -0.14, 1.02)
    ax.set_title("A strong relation does not survive experimental provenance", loc="left", pad=8)
    source = alloy[alloy["dataset_label"].eq("borg")].copy()
    target = alloy[alloy["dataset_label"].eq("birdshot")].copy()
    donor = LinearRegression().fit(source[["log_uts"]], source["log_ys"])
    recipient = LinearRegression().fit(target[["log_uts"]], target["log_ys"])
    xx = np.linspace(alloy["log_uts"].min() - 0.03, alloy["log_uts"].max() + 0.03, 200)
    ax.scatter(source["log_uts"], source["log_ys"], s=10, color=BLUE, alpha=0.30,
               edgecolor="none", rasterized=True)
    ax.scatter(target["log_uts"], target["log_ys"], s=13, facecolor=ORANGE, alpha=0.58,
               edgecolor="white", linewidth=0.25, rasterized=True)
    ax.plot(xx, donor.predict(xx[:, None]), color=NAVY, lw=1.8)
    ax.plot(xx, recipient.predict(xx[:, None]), color=ORANGE, lw=1.2, ls=(0, (4, 2)))
    r2_source = r2_score(source["log_ys"], donor.predict(source[["log_uts"]]))
    r2_target_internal = r2_score(target["log_ys"], recipient.predict(target[["log_uts"]]))
    r2_transport = r2_score(target["log_ys"], donor.predict(target[["log_uts"]]))
    ax.text(0.035, 0.955, f"source fit  $R^2$ = {r2_source:.3f}", transform=ax.transAxes,
            color=NAVY, fontweight="bold", va="top")
    ax.text(0.035, 0.892, f"recipient fit  $R^2$ = {r2_target_internal:.3f}", transform=ax.transAxes,
            color=ORANGE, va="top")
    ax.text(0.035, 0.815, f"transported coefficient  $R^2$ = {r2_transport:.3f}", transform=ax.transAxes,
            color=CORAL, fontweight="bold", va="top",
            bbox={"boxstyle": "round,pad=0.22", "facecolor": LIGHT_CORAL, "edgecolor": "none"})
    med_source = float(source["uts_ys_ratio"].median())
    med_target = float(target["uts_ys_ratio"].median())
    ax.text(0.965, 0.055, f"median UTS/YS\n{med_source:.2f}  →  {med_target:.2f}",
            transform=ax.transAxes, ha="right", va="bottom", color=INK, linespacing=1.2)
    ax.set_xlabel("log$_{10}$ ultimate tensile strength (MPa)")
    ax.set_ylabel("log$_{10}$ yield strength (MPa)")
    ax.grid(color=GRID, lw=0.45)
    ax.legend(handles=[
        Line2D([0], [0], marker="o", linestyle="none", color=BLUE, label="source programme"),
        Line2D([0], [0], marker="o", linestyle="none", color=ORANGE, label="independent recipient"),
    ], loc="lower left", frameon=False, handletextpad=0.25)
    return pd.DataFrame([
        {"panel": "a", "measure": "source_internal_r2", "estimate": r2_source},
        {"panel": "a", "measure": "recipient_internal_r2", "estimate": r2_target_internal},
        {"panel": "a", "measure": "transported_r2", "estimate": r2_transport},
        {"panel": "a", "measure": "source_median_uts_ys", "estimate": med_source},
        {"panel": "a", "measure": "recipient_median_uts_ys", "estimate": med_target},
    ])


def ordered_real_edges(edges: pd.DataFrame) -> pd.DataFrame:
    real = edges.loc[~edges["is_shuffled_control"].astype(bool)].copy()
    chunks = []
    for target in TARGET_ORDER:
        block = real[real["target"].eq(target)].copy()
        block["slot_order"] = np.where(block["is_designated_primary"], -1, 10 - block["neighborhood"])
        block = block.sort_values(["slot_order", "source"]).reset_index(drop=True)
        if len(block) != 5:
            raise RuntimeError(f"Expected five real edges for {target}, found {len(block)}")
        block["donor_slot"] = np.arange(1, 6)
        chunks.append(block)
    return pd.concat(chunks, ignore_index=True)


def panel_b(ax: plt.Axes, edges: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "b", 0.0, 1.04)
    ax.set_title("Generic donor features do not repair the far-OOD region", loc="left", pad=8, x=0.08)
    frame = ordered_real_edges(edges)
    matrix = frame.pivot(index="target", columns="donor_slot", values="gain_ood_mean").loc[TARGET_ORDER]
    values = 100 * matrix.to_numpy()
    cmap = LinearSegmentedColormap.from_list("gain", [CORAL, "#F8F9FB", TEAL], N=256)
    norm = TwoSlopeNorm(vmin=-5, vcenter=0, vmax=9)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(5))
    ax.set_xticklabels(["declared\ndonor", "candidate\n2", "candidate\n3", "candidate\n4", "distant\ncontrol"])
    ax.set_yticks(np.arange(8))
    ax.set_yticklabels([TARGET_LABELS[t] for t in TARGET_ORDER])
    ax.tick_params(length=0)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            value = values[i, j]
            ax.text(j, i, f"{value:+.1f}", ha="center", va="center", fontsize=6.1,
                    color="white" if abs(value) > 4.7 else INK,
                    fontweight="bold" if j == 0 else "normal")
            if j == 0:
                ax.add_patch(plt.Rectangle((j - .49, i - .49), .98, .98, fill=False,
                                           edgecolor=NAVY, lw=0.85))
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = ax.figure.colorbar(image, ax=ax, orientation="horizontal", fraction=0.08, pad=0.16,
                             aspect=28)
    cbar.set_label("relative far-OOD RMSE gain (%)", labelpad=2)
    cbar.outline.set_visible(False)
    ax.text(1.0, -0.32, "positive values denote lower error", transform=ax.transAxes,
            ha="right", va="top", fontsize=6.0, color=MID)
    export = frame[["target", "source", "donor_slot", "is_designated_primary",
                    "neighborhood", "gain_ood_mean", "gain_ood_ci_lo", "gain_ood_ci_hi",
                    "aug_ood_r2_mean", "classification"]].copy()
    export.insert(0, "panel", "b")
    return export


def collapsed_gate(edges: pd.DataFrame, design: dict) -> pd.DataFrame:
    gate = design["edge_gate"]
    designated = edges[edges["is_designated_primary"].astype(bool)].set_index("target").loc[TARGET_ORDER]
    rows = []
    for target, row in designated.iterrows():
        checks = {
            "utility": (row.gain_ood_mean >= gate["mean_ood_relative_rmse_gain_minimum"] and
                        row.gain_ood_ci_lo > 0 and row.aug_ood_r2_mean > 0),
            "robustness": (row.positive_ood_repeat_fraction >= 0.8 and row.positive_ood_learners >= 2),
            "OOD specificity": (row.gain_specific_ci_lo > 0 and row.primary_minus_wrong_ci_lo > 0 and
                                row.primary_minus_shuffled_ci_lo > 0),
            "adjusted inference": row.holm_p < 0.05,
            "no overlap": row.get("post_exclusion_overlap", 0) == 0,
        }
        for criterion, passed in checks.items():
            rows.append({"target": target, "criterion": criterion, "pass": int(bool(passed))})
    return pd.DataFrame(rows)


def panel_c(ax: plt.Axes, edges: pd.DataFrame, design: dict, summary: dict) -> pd.DataFrame:
    panel_label(ax, "c", 0.0, 1.04)
    ax.set_title("A conjunctive gate rejects every declared edge", loc="left", pad=8, x=0.08)
    long = collapsed_gate(edges, design)
    columns = ["utility", "robustness", "OOD specificity", "adjusted inference", "no overlap"]
    matrix = long.pivot(index="target", columns="criterion", values="pass").loc[TARGET_ORDER, columns]
    ax.imshow(matrix.to_numpy(), cmap=ListedColormap(["#F6E4E1", "#DDF1E7"]), vmin=0, vmax=1,
              aspect="auto")
    ax.set_xticks(np.arange(len(columns)))
    ax.set_xticklabels(["utility", "repeat\nrobust", "OOD/donor\nspecific",
                        "Holm\n$P<0.05$", "no\noverlap"])
    ax.set_yticks(np.arange(len(TARGET_ORDER)))
    ax.set_yticklabels([TARGET_LABELS[t] for t in TARGET_ORDER])
    ax.tick_params(length=0)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            passed = bool(matrix.iloc[i, j])
            if passed:
                ax.scatter(j, i, s=24, facecolor=GREEN, edgecolor="white", linewidth=0.45)
            else:
                ax.text(j, i, "×", ha="center", va="center", fontsize=7.0,
                        color=CORAL, fontweight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)
    programme = summary["programme_inference"]
    ax.set_xlim(-0.5, 7.1)
    ax.text(5.25, 2.1, "0/40", fontsize=7.0, color=NAVY,
            fontweight="bold", ha="left", va="center")
    ax.text(5.25, 2.8, "real edges pass\nthe complete gate",
            fontsize=5.8, color=INK, ha="left", va="top", linespacing=1.2)
    ax.text(5.25, 5.2,
            f"programme mean\n{100*programme['mean_primary_ood_gain']:+.2f}%\n"
            f"[{100*programme['ci95'][0]:+.2f}, {100*programme['ci95'][1]:+.2f}]",
            fontsize=5.6, color=MID, ha="left", va="top", linespacing=1.25)
    return long.assign(panel="c")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    alloy, edges, summary, design = load()
    fig = plt.figure(figsize=(7.2047, 5.6299))  # 183 × 143 mm
    gs = fig.add_gridspec(2, 2, width_ratios=[0.43, 0.57], height_ratios=[0.55, 0.45],
                          left=0.075, right=0.935, bottom=0.10, top=0.94,
                          wspace=0.40, hspace=0.49)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])
    outputs = [panel_a(ax_a, alloy), panel_b(ax_b, edges), panel_c(ax_c, edges, design, summary)]
    pd.concat(outputs, ignore_index=True, sort=False).to_csv(SOURCE, index=False)
    fig.savefig(f"{OUT}.svg", bbox_inches=None, pad_inches=0)
    fig.savefig(f"{OUT}.pdf", bbox_inches=None, pad_inches=0)
    fig.savefig(f"{OUT}.png", dpi=300, bbox_inches=None, pad_inches=0)
    fig.savefig(f"{OUT}.tiff", dpi=600, bbox_inches=None, pad_inches=0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
