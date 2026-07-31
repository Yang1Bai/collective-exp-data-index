"""NMI-v3 Figure 3: a qualified relation supports selected OOD prediction."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure3_relation_transfer_nmi_v3"
SOURCE = SOURCE_DIR / "figure3_relation_transfer_nmi_v3.csv"

NAVY = "#173B6C"
BLUE = "#4D8DC5"
TEAL = "#1E9189"
GREEN = "#469A6A"
ORANGE = "#E98A32"
CORAL = "#CF6258"
INK = "#24303D"
MID = "#7A8795"
GRID = "#D9E1E8"
PALE_BLUE = "#EDF4F9"
PALE_TEAL = "#EAF5F1"
PALE_ORANGE = "#FCF0E2"
PALE_CORAL = "#FAECE9"

TARGETS = ["A", "B", "C", "D"]
TARGET_LABELS = {
    "A": "amino-ligand",
    "B": "tricarboxylate",
    "C": "Fe substitution",
    "D": "Mn substitution",
}
ROUTE = {"A": "ranking only", "B": "predict + rank", "C": "reject", "D": "predict + rank"}
ROUTE_COLOR = {"A": ORANGE, "B": GREEN, "C": CORAL, "D": GREEN}

mpl.rcParams.update({
    "font.family": "Arial",
    "font.size": 6.2,
    "axes.titlesize": 6.8,
    "axes.labelsize": 6.2,
    "xtick.labelsize": 5.6,
    "ytick.labelsize": 5.6,
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


def flask(ax: plt.Axes, cx: float, cy: float, scale: float,
          salts: list[str]) -> None:
    verts = [(cx - .11*scale, cy + .34*scale), (cx - .11*scale, cy + .10*scale),
             (cx - .30*scale, cy - .31*scale), (cx + .30*scale, cy - .31*scale),
             (cx + .11*scale, cy + .10*scale), (cx + .11*scale, cy + .34*scale)]
    ax.add_patch(Polygon(verts, closed=True, facecolor="#F2F7FA",
                         edgecolor="#7A9CB3", lw=.55))
    ax.add_patch(Polygon([(cx - .25*scale, cy - .17*scale),
                          (cx + .25*scale, cy - .17*scale),
                          (cx + .28*scale, cy - .28*scale),
                          (cx - .28*scale, cy - .28*scale)],
                         closed=True, facecolor="#DDEBF4", edgecolor="none"))
    xs = np.linspace(-.18, .18, len(salts))
    for dx, colour in zip(xs, salts):
        ax.add_patch(Circle((cx + dx*scale, cy - .21*scale), .044*scale,
                            facecolor=colour, edgecolor="white", lw=.25))


def panel_a(ax: plt.Axes) -> None:
    panel_label(ax, "a", 0.0, 1.02)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.text(.045, 1.025, "A relation, rather than a database, crosses the boundary",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8,
            fontweight="bold", color=INK)

    flask(ax, .10, .50, .55, [NAVY, BLUE, TEAL, ORANGE, "#7560A8"])
    ax.text(.18, .67, "22 source salts", ha="left", va="center",
            fontsize=6.5, color=INK, fontweight="bold")
    ax.text(.18, .45, "10,407 conductivity measurements", ha="left",
            va="center", fontsize=5.6, color=MID)
    ax.text(.18, .25, "temperature, concentration and mixture chemistry",
            ha="left", va="center", fontsize=5.3, color=MID)

    ax.add_patch(FancyArrowPatch((.37, .50), (.49, .50), arrowstyle="-|>",
                                 mutation_scale=9, lw=1.7, color=TEAL))
    relation = FancyBboxPatch((.49, .23), .22, .54,
                              boxstyle="round,pad=.012,rounding_size=.025",
                              facecolor=PALE_TEAL, edgecolor=TEAL, lw=.75)
    ax.add_patch(relation)
    ax.text(.60, .62, "component-order-invariant", ha="center", va="center",
            fontsize=6.1, color=TEAL, fontweight="bold")
    ax.text(.60, .43, "mixture relation", ha="center", va="center",
            fontsize=6.1, color=INK, fontweight="bold")
    ax.text(.60, .28, "zero recipient labels", ha="center", va="center",
            fontsize=5.4, color=MID)
    ax.add_patch(FancyArrowPatch((.71, .50), (.79, .50), arrowstyle="-|>",
                                 mutation_scale=9, lw=1.7, color=TEAL))

    flask(ax, .80, .50, .55, [CORAL])
    ax.text(.86, .67, "unseen LiAsF$_6$", ha="left", va="center",
            fontsize=6.5, color=INK, fontweight="bold")
    ax.text(.86, .45, "176 formulations", ha="left", va="center",
            fontsize=5.6, color=MID)
    ax.text(.86, .25, "1,827 held-out rows", ha="left", va="center",
            fontsize=5.3, color=MID)


def panel_b(ax: plt.Axes, predictions: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    panel_label(ax, "b", -.10, 1.03)
    ax.set_title("Zero-label prediction of an unseen salt", loc="left", pad=7)
    frame = predictions[predictions["scope"].eq("all_source_salts")].copy()
    y_log = frame["y_log10_conductivity"].to_numpy()
    pred_log = frame["prediction_log10_conductivity"].to_numpy()
    y_raw = frame["y_conductivity"].to_numpy()
    pred_raw = frame["prediction_conductivity"].to_numpy()
    metrics = {
        "raw_r2": float(r2_score(y_raw, pred_raw)),
        "log_r2": float(r2_score(y_log, pred_log)),
        "spearman": float(spearmanr(y_log, pred_log).statistic),
        "n": int(len(frame)),
    }
    cmap = LinearSegmentedColormap.from_list("density", ["#E9F2F6", TEAL, NAVY])
    ax.hexbin(y_log, pred_log, gridsize=38, mincnt=1, cmap=cmap,
              linewidths=0, rasterized=True)
    lo = min(y_log.min(), pred_log.min())
    hi = max(y_log.max(), pred_log.max())
    ax.plot([lo, hi], [lo, hi], color=CORAL, lw=.9, ls=(0, (4, 2)))
    ax.set(xlim=(lo, hi), ylim=(lo, hi))
    ax.set_xlabel("measured log$_{10}$ conductivity")
    ax.set_ylabel("borrowed log$_{10}$ prediction")
    ax.grid(color=GRID, lw=.4)
    ax.text(.04, .95,
            f"raw $R^2$ = {metrics['raw_r2']:.3f}\n"
            f"log $R^2$ = {metrics['log_r2']:.3f}\n"
            f"$\\rho$ = {metrics['spearman']:.3f}\n"
            f"$n$ = {metrics['n']:,}",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.5,
            color=INK, linespacing=1.15,
            bbox={"boxstyle": "round,pad=.28", "facecolor": "white",
                  "edgecolor": "none", "alpha": .90})
    return frame.assign(panel="b"), metrics


def interval(values: pd.Series) -> tuple[float, float, float]:
    return float(values.mean()), float(values.quantile(.025)), float(values.quantile(.975))


def panel_c(ax: plt.Axes, bootstrap: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax, "c", -.08, 1.03)
    ax.set_title("Matched falsifiers isolate the chemistry-specific gain", loc="left", pad=7)
    order = ["state_only", "chemistry_permuted", "without_LiPF6", "LiPF6_only",
             "LiBOB_wrong_salt_control", "LiBF4_fluorinated_control"]
    labels = {
        "state_only": "state only",
        "chemistry_permuted": "permuted chemistry",
        "without_LiPF6": "without nearest salt",
        "LiPF6_only": "nearest salt only",
        "LiBOB_wrong_salt_control": "wrong-salt control",
        "LiBF4_fluorinated_control": "fluorinated control",
    }
    y = np.arange(len(order))[::-1]
    ax.axvline(0, color=INK, lw=.7)
    ax.axvspan(0, 50, color=PALE_TEAL, zorder=0)
    rows = []
    for yi, name in zip(y, order):
        values = 100 * bootstrap.loc[bootstrap["comparator"].eq(name),
                                     "relative_log_rmse_gain"]
        mean, low, high = interval(values)
        colour = TEAL if name in {"state_only", "chemistry_permuted"} else BLUE
        ax.plot([low, high], [yi, yi], color=colour, lw=2.0,
                solid_capstyle="round")
        ax.scatter(mean, yi, s=29, color=colour, edgecolor="white",
                   linewidth=.45, zorder=3)
        ax.text(high + 1.0, yi, f"{mean:.1f}%", ha="left", va="center",
                fontsize=5.7, color=colour, fontweight="bold")
        rows.append({"panel": "c", "comparator": name, "estimate": mean/100,
                     "ci95_low": low/100, "ci95_high": high/100})
    ax.set_yticks(y)
    ax.set_yticklabels([labels[name] for name in order])
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-3, 51)
    ax.set_xlabel("full-mixture log-RMSE gain over comparator (%)")
    ax.grid(axis="x", color=GRID, lw=.42)
    return pd.DataFrame(rows)


def controlled_rows(catalyst: pd.DataFrame, measure: str) -> pd.DataFrame:
    return (catalyst[(catalyst["panel"].eq("c")) &
                     (catalyst["measure"].eq(measure))]
            .set_index("target").loc[TARGETS])


def forest(ax: plt.Axes, catalyst: pd.DataFrame, measure: str, scale: float,
           xlabel: str, show_labels: bool) -> None:
    rows = controlled_rows(catalyst, measure)
    y = np.arange(4)[::-1]
    ax.axvline(0, color=INK, lw=.7)
    positive_max = 38 if scale == 100 else .50
    ax.axvspan(0, positive_max, color=PALE_TEAL, zorder=0)
    for yi, (target, row) in zip(y, rows.iterrows()):
        estimate = scale * row["estimate"]
        low = scale * row["ci95_low"]
        high = scale * row["ci95_high"]
        colour = ROUTE_COLOR[target]
        ax.plot([low, high], [yi, yi], color=colour, lw=2.0,
                solid_capstyle="round")
        ax.scatter(estimate, yi, s=28, color=colour, edgecolor="white",
                   linewidth=.45, zorder=3)
        label = f"{estimate:+.1f}%" if scale == 100 else f"{estimate:+.3f}"
        ax.text(high + (.9 if scale == 100 else .012), yi, label,
                ha="left", va="center", fontsize=5.5, color=colour,
                fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{t}  {TARGET_LABELS[t]}" for t in TARGETS]
                       if show_labels else [])
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=.42)


def route_panel(ax: plt.Axes) -> None:
    ax.set(xlim=(0, 1), ylim=(-.5, 3.5))
    ax.axis("off")
    for yi, target in zip(np.arange(4)[::-1], TARGETS):
        ax.text(.02, yi, ROUTE[target], ha="left", va="center", fontsize=5.3,
                color=ROUTE_COLOR[target], fontweight="bold")


def panel_d(ax_left: plt.Axes, ax_right: plt.Axes, ax_route: plt.Axes,
            catalyst: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax_left, "d", -.10, 1.04)
    ax_left.set_title("Controlled perturbations separate prediction, ranking and harm",
                      loc="left", pad=7)
    ax_left.set_xlim(-20, 38)
    forest(ax_left, catalyst, "relative_rmse_gain", 100,
           "relative RMSE gain (%)", True)
    ax_right.set_xlim(-.05, .50)
    forest(ax_right, catalyst, "spearman_gain", 1,
           "Spearman gain", False)
    route_panel(ax_route)
    ax_left.text(.00, -.30,
                 "post-primary composition relation; complete non-anchor systems; bootstrap 95% intervals",
                 transform=ax_left.transAxes, ha="left", va="top",
                 fontsize=5.1, color=MID)
    return catalyst.assign(panel_source="d")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    catalyst = pd.read_csv(RESULTS / "specgen_derivative_oer_figure_source_data.csv")
    predictions = pd.read_csv(RESULTS / "bamboomixer_response_transfer_external_predictions.csv")
    bootstrap = pd.read_csv(RESULTS / "bamboomixer_response_transfer_external_group_bootstrap.csv")
    summary = json.loads((RESULTS / "bamboomixer_response_transfer_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") not in {"verified-complete", "complete",
                                      "complete-method-development"}:
        raise RuntimeError("External unseen-salt result is not complete")

    fig = plt.figure(figsize=(7.204724, 5.708661))  # 183 x 145 mm
    outer = fig.add_gridspec(3, 1, height_ratios=[.18, .49, .33],
                             left=.095, right=.975, bottom=.085, top=.950,
                             hspace=.42)
    ax_a = fig.add_subplot(outer[0, 0])
    middle = outer[1, 0].subgridspec(1, 2, width_ratios=[.47, .53], wspace=.42)
    ax_b = fig.add_subplot(middle[0, 0])
    ax_c = fig.add_subplot(middle[0, 1])
    lower = outer[2, 0].subgridspec(1, 3, width_ratios=[1.04, .93, .22], wspace=.24)
    ax_d1 = fig.add_subplot(lower[0, 0])
    ax_d2 = fig.add_subplot(lower[0, 1])
    ax_dr = fig.add_subplot(lower[0, 2])

    panel_a(ax_a)
    pred_source, metrics = panel_b(ax_b, predictions)
    outputs = [pred_source, panel_c(ax_c, bootstrap),
               panel_d(ax_d1, ax_d2, ax_dr, catalyst)]
    pd.concat(outputs, ignore_index=True, sort=False).to_csv(SOURCE, index=False)
    (RESULTS / "figure3_relation_transfer_nmi_v3_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
