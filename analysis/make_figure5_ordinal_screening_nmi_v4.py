"""NMI-v4 Figure 5: ordinal borrowing supports screening, with abstention."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure5_ordinal_screening_nmi_v4"
SOURCE = SOURCE_DIR / "figure5_ordinal_screening_nmi_v4.csv"

NAVY = "#173B6C"
TEAL = "#1E9189"
GREEN = "#469A6A"
ORANGE = "#E98A32"
CORAL = "#CF6258"
PURPLE = "#7560A8"
INK = "#24303D"
MID = "#7A8795"
GRID = "#D9E1E8"
PALE = "#F5F8FB"
PALE_BLUE = "#EDF4F9"
PALE_TEAL = "#EAF5F1"
PALE_CORAL = "#FAECE9"

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 6.2,
    "axes.titlesize": 6.8,
    "axes.labelsize": 6.2,
    "xtick.labelsize": 5.5,
    "ytick.labelsize": 5.4,
    "axes.linewidth": .6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})


def panel_label(ax: plt.Axes, label: str, x: float = 0.0, y: float = 1.03) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.0,
            fontweight="bold", ha="left", va="bottom", color="black")


def interval(values: pd.Series) -> tuple[float, float, float]:
    return (float(values.mean()), float(values.quantile(.025)),
            float(values.quantile(.975)))


def model_label(name: str) -> str:
    labels = {
        "programme_balanced_source_portfolio": "neighbouring-programme score",
        "recipient_oracle": "per-draw recipient oracle",
        "recipient_rank_ensemble": "recipient rank ensemble",
        "rbf_kernel_ridge_alpha_10": "RBF kernel ridge, alpha=10",
        "rbf_kernel_ridge_alpha_1": "RBF kernel ridge, alpha=1",
        "rbf_kernel_ridge_alpha_0.1": "RBF kernel ridge, alpha=0.1",
        "random_forest": "Random Forest",
        "extra_trees": "ExtraTrees",
        "ridge_alpha_0.1": "Ridge, alpha=0.1",
        "ridge_alpha_1": "Ridge, alpha=1",
        "ridge_alpha_10": "Ridge, alpha=10",
        "ridge_alpha_100": "Ridge, alpha=100",
        "knn_1": "1-nearest neighbour",
        "knn_3": "3-nearest neighbours",
        "knn_5": "5-nearest neighbours",
    }
    return labels[name]


def stress_frame(stress: pd.DataFrame, budget: int = 5) -> pd.DataFrame:
    primary = stress[stress["anchor_budget"].eq(budget)].copy()
    recipient = primary[~primary["model"].eq("programme_balanced_source_portfolio")]
    oracle = (recipient.groupby("draw", as_index=False)["spearman"].max()
              .assign(model="recipient_oracle"))
    return pd.concat([primary[["draw", "model", "spearman"]], oracle],
                     ignore_index=True)


def source_card(ax: plt.Axes, y: float, title: str, count: str, colour: str) -> None:
    ax.add_patch(FancyBboxPatch((.02, y), .43, .125,
                                boxstyle="round,pad=.010,rounding_size=.018",
                                facecolor=PALE, edgecolor=GRID, lw=.55))
    ax.add_patch(Rectangle((.02, y), .018, .125, facecolor=colour, edgecolor="none"))
    ax.text(.055, y + .083, title, ha="left", va="center", fontsize=5.4,
            color=INK, fontweight="bold")
    ax.text(.055, y + .036, count, ha="left", va="center", fontsize=5.0,
            color=MID)


def panel_a(ax: plt.Axes) -> None:
    panel_label(ax, "a", 0.0, 1.02)
    ax.text(.075, 1.025, "Borrow relations, then route the decision",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8,
            color=INK, fontweight="bold")
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    source_card(ax, .72, "multi-salt data", "10,012 measurements", NAVY)
    source_card(ax, .565, "literature data", "410 measurements", ORANGE)
    source_card(ax, .41, "temperature data", "1,089 aggregates", TEAL)

    for y in [.782, .627, .472]:
        ax.plot([.45, .50], [y, y], color=GRID, lw=.8)
    ax.plot([.50, .50], [.472, .782], color=GRID, lw=.8)
    ax.add_patch(FancyArrowPatch((.50, .627), (.57, .72), arrowstyle="-|>",
                                 mutation_scale=7, lw=1.2, color=TEAL))
    ax.add_patch(FancyBboxPatch((.57, .60), .39, .25,
                                boxstyle="round,pad=.012,rounding_size=.025",
                                facecolor=PALE_TEAL, edgecolor=TEAL, lw=.7))
    ax.text(.765, .735, "programme-\nbalanced score", ha="center", va="center",
            fontsize=5.1, color=TEAL, fontweight="bold", linespacing=1.0)
    ax.text(.765, .625, "no shared records", ha="center", va="center",
            fontsize=5.0, color=MID)
    ax.add_patch(FancyArrowPatch((.765, .60), (.765, .535), arrowstyle="-|>",
                                 mutation_scale=7, lw=1.2, color=TEAL))
    ax.add_patch(FancyBboxPatch((.57, .385), .39, .145,
                                boxstyle="round,pad=.010,rounding_size=.018",
                                facecolor=PALE_BLUE, edgecolor=GRID, lw=.6))
    ax.text(.765, .475, "36 candidates", ha="center", va="center",
            fontsize=5.6, color=INK, fontweight="bold")
    ax.text(.765, .420, "5 anchors", ha="center", va="center",
            fontsize=5.1, color=MID)

    ax.add_patch(FancyArrowPatch((.70, .385), (.66, .245), arrowstyle="-|>",
                                 mutation_scale=7, lw=1.0, color=GREEN))
    ax.add_patch(FancyArrowPatch((.83, .385), (.87, .245), arrowstyle="-|>",
                                 mutation_scale=7, lw=1.0, color=CORAL))
    ax.add_patch(FancyBboxPatch((.57, .08), .18, .16,
                                boxstyle="round,pad=.010,rounding_size=.020",
                                facecolor=PALE_TEAL, edgecolor=GREEN, lw=.65))
    ax.text(.66, .175, "ORDER", ha="center", va="center",
            fontsize=5.6, color=GREEN, fontweight="bold")
    ax.text(.66, .120, "screen", ha="center", va="center", fontsize=5.0,
            color=INK)
    ax.add_patch(FancyBboxPatch((.78, .08), .18, .16,
                                boxstyle="round,pad=.010,rounding_size=.020",
                                facecolor=PALE_CORAL, edgecolor=CORAL, lw=.65))
    ax.text(.87, .175, "VALUE", ha="center", va="center",
            fontsize=5.3, color=CORAL, fontweight="bold")
    ax.text(.87, .120, "abstain", ha="center", va="center", fontsize=5.0,
            color=INK)


def panel_b(ax: plt.Axes, stress: pd.DataFrame, summary: dict) -> pd.DataFrame:
    panel_label(ax, "a", -.13, 1.03)
    ax.set_title("Neighbouring programmes recover order beyond five-label models",
                 loc="left", pad=7)
    frame = stress_frame(stress, 5)
    order = frame.groupby("model")["spearman"].mean().sort_values().index.tolist()
    rows = []
    for yi, name in enumerate(order):
        mean, low, high = interval(frame.loc[frame["model"].eq(name), "spearman"])
        if name == "programme_balanced_source_portfolio":
            colour, lw, size = TEAL, 2.2, 34
        elif name == "recipient_oracle":
            colour, lw, size = ORANGE, 1.8, 25
        else:
            colour, lw, size = "#A5AFB8", 1.25, 18
        ax.plot([low, high], [yi, yi], color=colour, lw=lw,
                solid_capstyle="round")
        ax.scatter(mean, yi, s=size, color=colour, edgecolor="white",
                   linewidth=.45, zorder=3)
        rows.append({"panel": "a", "model": name, "anchor_budget": 5,
                     "estimate": mean, "ci95_low": low, "ci95_high": high})
    ax.axvline(0, color=INK, lw=.7)
    ax.grid(axis="x", color=GRID, lw=.42)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([model_label(name) for name in order])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-.52, 1.03)
    ax.set_xlabel("Spearman candidate-order correlation")

    source_mean = summary["five_anchor"]["source_portfolio"]["spearman"]
    strongest = summary["five_anchor"]["strongest_average_recipient_model"]
    best_mean = next(item["spearman"] for item in summary["five_anchor"]["recipient_macro"]
                     if item["model"] == strongest)
    delta = summary["five_anchor"]["source_minus_strongest_spearman"]
    ax.text(source_mean + .018, order.index("programme_balanced_source_portfolio"),
            f"{source_mean:.3f}", color=TEAL, fontweight="bold", va="center")
    ax.text(best_mean + .018, order.index(strongest), f"{best_mean:.3f}",
            color=INK, va="center")
    ax.text(.99, .055,
            rf"$\Delta\rho$ = {delta['mean']:+.3f} "
            rf"[{delta['ci95'][0]:.3f}, {delta['ci95'][1]:.3f}]",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=5.7,
            color=TEAL, fontweight="bold")
    return pd.DataFrame(rows)


def panel_c(ax: plt.Axes, stress: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "b", -.12, 1.04)
    ax.set_title("Borrowed order persists across sparse anchor budgets",
                 loc="left", pad=7)
    budgets = [3, 5, 10]
    series = {
        "neighbouring-programme score": ("programme_balanced_source_portfolio", TEAL),
        "best fixed recipient model": ("rbf_kernel_ridge_alpha_10", NAVY),
        "recipient rank ensemble": ("recipient_rank_ensemble", PURPLE),
    }
    rows = []
    for label, (model, colour) in series.items():
        means, lows, highs = [], [], []
        for budget in budgets:
            values = stress[(stress["anchor_budget"].eq(budget)) &
                            (stress["model"].eq(model))]["spearman"]
            mean, low, high = interval(values)
            means.append(mean)
            lows.append(low)
            highs.append(high)
            rows.append({"panel": "b", "model": model,
                         "anchor_budget": budget, "estimate": mean,
                         "ci95_low": low, "ci95_high": high})
        ax.plot(budgets, means, marker="o", ms=3.4, color=colour, lw=1.65,
                label=label)
        ax.fill_between(budgets, lows, highs, color=colour, alpha=.10,
                        linewidth=0)
    ax.set_xticks(budgets)
    ax.set_xlabel("measured recipient formulations")
    ax.set_ylabel("Spearman correlation")
    ax.set_ylim(-.40, 1.03)
    ax.grid(color=GRID, lw=.42)
    ax.legend(frameon=False, loc="lower right", handlelength=1.6,
              labelspacing=.35)
    return pd.DataFrame(rows)


def panel_d(ax: plt.Axes, summary: dict, finales: dict) -> pd.DataFrame:
    panel_label(ax, "c", -.12, 1.04)
    ax.set_title("A frozen second recipient defines the boundary", loc="left", pad=7)
    solvent = summary["five_anchor"]["source_minus_strongest_spearman"]
    frozen = finales["primary"]
    rows = [
        {
            "programme": "SolventSeg",
            "estimate": solvent["mean"],
            "ci95_low": solvent["ci95"][0],
            "ci95_high": solvent["ci95"][1],
            "decision": "screen",
            "detail": (f"donor {summary['five_anchor']['source_portfolio']['spearman']:.3f} "
                       f"vs recipient {summary['five_anchor']['recipient_macro'][0]['spearman']:.3f}"),
        },
        {
            "programme": "FINALES",
            "estimate": frozen["concordance_advantage"],
            "ci95_low": frozen["bootstrap_ci95"][0],
            "ci95_high": frozen["bootstrap_ci95"][1],
            "decision": "abstain",
            "detail": (f"donor {frozen['donor_concordance']:.3f} "
                       f"vs recipient {frozen['strongest_baseline_concordance']:.3f}"),
        },
    ]
    y = [1, 0]
    colours = [GREEN, CORAL]
    labels = ["primary recipient\n36 formulations",
              "frozen recipient\n16 formulations"]
    ax.axvline(0, color=INK, lw=.7)
    ax.axvspan(0, .65, color=PALE_TEAL, zorder=0)
    for yi, row, colour in zip(y, rows, colours):
        ax.plot([row["ci95_low"], row["ci95_high"]], [yi, yi],
                color=colour, lw=2.1, solid_capstyle="round")
        ax.scatter(row["estimate"], yi, s=32, color=colour, edgecolor="white",
                   linewidth=.45, zorder=3)
        ax.text(row["estimate"], yi + .20, f"{row['estimate']:+.3f}",
                ha="center", va="bottom", fontsize=5.7, color=colour,
                fontweight="bold")
        ax.text(.61, yi, row["decision"], ha="right", va="center",
                fontsize=5.7, color=colour, fontweight="bold",
                bbox={"boxstyle": "round,pad=.14", "facecolor": "white",
                      "edgecolor": "none", "alpha": .90})
        ax.text(-.34, yi - .22, row["detail"], ha="left", va="top",
                fontsize=5.0, color=MID)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-.35, .65)
    ax.set_ylim(-.55, 1.48)
    ax.set_xlabel("donor advantage in candidate order")
    ax.grid(axis="x", color=GRID, lw=.42)
    return pd.DataFrame([dict(panel="c", **row) for row in rows])


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    stress = pd.read_csv(RESULTS / "bamboomixer_recipient_baseline_stress_test_metrics.csv")
    summary = json.loads((RESULTS / "bamboomixer_recipient_baseline_stress_test_summary.json")
                         .read_text(encoding="utf-8"))
    finales = json.loads((RESULTS / "finales_rank_replication_summary.json")
                         .read_text(encoding="utf-8"))
    if summary.get("status") != "complete-post-outcome-recipient-baseline-stress-test":
        raise RuntimeError("Recipient stress test is not complete")
    if finales.get("status") != "verified-complete":
        raise RuntimeError("Frozen second-recipient result is not verified")

    fig = plt.figure(figsize=(7.204724, 4.409449))  # 183 x 112 mm
    ax_b = fig.add_axes([.235, .59, .735, .34])
    ax_c = fig.add_axes([.115, .105, .38, .34])
    ax_d = fig.add_axes([.65, .105, .32, .34])

    outputs = [panel_b(ax_b, stress, summary), panel_c(ax_c, stress),
               panel_d(ax_d, summary, finales)]
    pd.concat(outputs, ignore_index=True, sort=False).to_csv(SOURCE, index=False)
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
