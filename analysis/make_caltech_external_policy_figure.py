"""Create the external-policy decomposition figure for the Caltech benchmark."""

from __future__ import annotations

import json
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

from common import FIGURES, RESULTS, ensure_output_dirs


plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7.0,
        "axes.labelsize": 7.1,
        "axes.titlesize": 8.0,
        "axes.titleweight": "bold",
        "axes.linewidth": 0.7,
        "xtick.labelsize": 6.3,
        "ytick.labelsize": 6.3,
        "legend.fontsize": 6.1,
        "legend.frameon": False,
        "axes.spines.right": False,
        "axes.spines.top": False,
    }
)

TEAL = "#238B82"
TEAL_DARK = "#17665F"
TEAL_LIGHT = "#8CC9C3"
BLUE = "#4C78A8"
PURPLE = "#7562A8"
ORANGE = "#D9822B"
RED = "#B64342"
GRAY = "#777777"
LIGHT_GRAY = "#D7D7D7"
BLACK = "#252525"

VALIDATION = RESULTS / "caltech_ionic_external_policy_validation.json"


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.25,
        1.05,
        label,
        transform=ax.transAxes,
        fontsize=9.5,
        fontweight="bold",
        va="bottom",
    )


def load_validation() -> dict:
    return json.loads(VALIDATION.read_text(encoding="utf-8"))


def gate_frame(validation: dict) -> pd.DataFrame:
    source_specs = [
        (
            "safe_obelix_residual",
            "obelix_same_property",
            "OBELiX\nsame property",
            "real neighbor",
        ),
        (
            "safe_estm_residual",
            "estm_transport_neighbor",
            "ESTM\ntransport neighbor",
            "real neighbor",
        ),
        (
            "safe_borg_residual_control",
            "borg_mechanical_control",
            "Borg\nmechanical",
            "wrong control",
        ),
        (
            "safe_ocx_residual_control",
            "ocx_catalysis_control",
            "OCx\ncatalysis",
            "wrong control",
        ),
        (
            "safe_shuffled_obelix_control",
            "shuffled_obelix",
            "shuffled\nOBELiX",
            "wrong control",
        ),
    ]
    gates = pd.DataFrame(validation["source_gate_means"])
    source_quality = pd.read_csv(
        RESULTS / "caltech_ionic_external_policy_source_quality.csv"
    ).set_index("source")
    rows = []
    for policy, source, label, source_class in source_specs:
        local = gates[(gates["policy"] == policy) & (gates["source"] == source)]
        if len(local) != 2:
            raise RuntimeError(f"Expected two scopes for {policy}/{source}")
        rows.append(
            {
                "policy": policy,
                "source": source,
                "label": label,
                "source_class": source_class,
                "scopes": len(local),
                "admission_rate_mean": local["admission_rate"].mean(),
                "mean_weight_mean": local["mean_weight"].mean(),
                "source_oof_r2": (
                    float(source_quality.loc[source, "oof_r2"])
                    if source in source_quality.index
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def panel_a(ax, validation: dict) -> None:
    frame = gate_frame(validation)
    frame.to_csv(RESULTS / "figure_caltech_policy_panel_a.csv", index=False)
    y = np.arange(len(frame) - 1, -1, -1)
    for yi, row in zip(y, frame.to_dict("records")):
        color = TEAL if row["source_class"] == "real neighbor" else GRAY
        ax.plot(
            [row["mean_weight_mean"], row["admission_rate_mean"]],
            [yi, yi],
            color=LIGHT_GRAY,
            lw=1.7,
            zorder=1,
        )
        ax.scatter(
            row["admission_rate_mean"],
            yi,
            s=34,
            color=color,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.scatter(
            row["mean_weight_mean"],
            yi,
            s=28,
            marker="s",
            facecolor="white",
            edgecolor=color,
            linewidth=1.1,
            zorder=3,
        )
    ax.axvline(0.20, color=RED, lw=0.8, ls=(0, (3, 2)))
    ax.text(
        0.205,
        -0.55,
        "wrong-source\nadmission ceiling",
        color=RED,
        fontsize=5.6,
        va="bottom",
    )
    skill_labels = [
        f"{row['label']}\nOOF $R^2$={row['source_oof_r2']:.2f}"
        if np.isfinite(row["source_oof_r2"])
        else f"{row['label']}\nOOF $R^2$=n/a"
        for row in frame.to_dict("records")
    ]
    ax.set_yticks(y, skill_labels)
    ax.set_xlim(0, 0.45)
    ax.set_ylim(-0.65, len(frame) - 0.35)
    ax.set_xlabel("Mean rate or weight across two scopes")
    ax.set_title("Admission and source skill disagree")
    ax.scatter([], [], s=34, color=BLACK, label="admission rate")
    ax.scatter(
        [], [], s=28, marker="s", facecolor="white", edgecolor=BLACK,
        label="mean weight"
    )
    ax.legend(loc="center right", handletextpad=0.35)
    panel_label(ax, "a")


def adaptive_frame(validation: dict) -> pd.DataFrame:
    selected_families = {
        "same_property_increment": ("OBELiX residual", TEAL),
        "adjacent_transport_increment": ("ESTM residual", BLUE),
        "safe_multisource_increment": ("multisource residual", PURPLE),
    }
    rows = []
    for row in validation["confirmatory_contrasts"]:
        if row["family"] not in selected_families:
            continue
        label, color = selected_families[row["family"]]
        ci = json.loads(row["auc20_gain_ci95"])
        rows.append(
            {
                "scope": row["scope"],
                "scope_label": (
                    "external" if row["scope"] == "external_candidate" else "hard OOD"
                ),
                "family": row["family"],
                "policy_label": label,
                "color": color,
                "mean_auc20_gain": row["mean_auc20_gain"],
                "ci_lo": ci[0],
                "ci_hi": ci[1],
                "holm_p": row["holm_p"],
                "passes_all_frozen_gates": False,
            }
        )
    return pd.DataFrame(rows)


def panel_b(ax, validation: dict) -> None:
    frame = adaptive_frame(validation)
    frame.to_csv(RESULTS / "figure_caltech_policy_panel_b.csv", index=False)
    policy_order = ["OBELiX residual", "ESTM residual", "multisource residual"]
    y_base = {name: 2 - idx for idx, name in enumerate(policy_order)}
    scope_style = {
        "external_candidate": (0.13, "o", "external"),
        "hard_ood_40pct": (-0.13, "s", "hard OOD"),
    }
    for row in frame.to_dict("records"):
        offset, marker, _ = scope_style[row["scope"]]
        yi = y_base[row["policy_label"]] + offset
        ax.plot([row["ci_lo"], row["ci_hi"]], [yi, yi], color=row["color"], lw=1.35)
        ax.scatter(
            row["mean_auc20_gain"],
            yi,
            s=30,
            marker=marker,
            color=row["color"],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
    ax.axvline(0, color=BLACK, lw=0.8)
    ax.set_yticks([2, 1, 0], policy_order)
    ax.set_xlim(-1.45, 3.5)
    ax.set_ylim(-0.55, 2.55)
    ax.set_xlabel("AUC20 gain versus target-only policy")
    ax.set_title("Adaptive increments are null")
    ax.scatter([], [], s=30, marker="o", color=GRAY, label="external")
    ax.scatter([], [], s=30, marker="s", color=GRAY, label="hard OOD")
    ax.legend(loc="upper right", handletextpad=0.35)
    ax.text(
        0.98,
        0.05,
        "no policy passes\nall frozen gates",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.0,
        color=RED,
        fontweight="bold",
    )
    panel_label(ax, "b")


def static_frame(validation: dict) -> pd.DataFrame:
    policies = {
        "obelix_same_property_static": ("OBELiX", "real neighbor"),
        "estm_transport_neighbor_static": ("ESTM", "real neighbor"),
        "shuffled_obelix_static_control": ("shuffled", "wrong control"),
        "uniform_random": ("random", "random"),
        "borg_mechanical_static_control": ("Borg", "wrong control"),
        "ocx_catalysis_static_control": ("OCx", "wrong control"),
    }
    summary = json.loads(
        (RESULTS / "caltech_ionic_external_policy_summary.json").read_text(
            encoding="utf-8"
        )
    )
    true_top_count = {
        scope: math.ceil(0.05 * int(size))
        for scope, size in summary["candidate_pools"].items()
    }
    rows = []
    for row in validation["policy_utility_means"]:
        if row["policy"] not in policies:
            continue
        label, source_class = policies[row["policy"]]
        rows.append(
            {
                "scope": row["scope"],
                "scope_label": (
                    "external" if row["scope"] == "external_candidate" else "hard OOD"
                ),
                "policy": row["policy"],
                "label": label,
                "source_class": source_class,
                "auc20": row["auc20"],
                "first_hit": row["first_hit"],
                "recall20": row["recall20"],
                "true_top_entities": true_top_count[row["scope"]],
                "recall20_count": int(
                    round(row["recall20"] * true_top_count[row["scope"]])
                ),
            }
        )
    return pd.DataFrame(rows)


def panel_c(ax, validation: dict) -> None:
    frame = static_frame(validation)
    frame.to_csv(RESULTS / "figure_caltech_policy_panel_c.csv", index=False)
    labels = ["OBELiX", "ESTM", "shuffled", "random", "Borg", "OCx"]
    x = np.arange(len(labels))
    width = 0.35
    class_color = {
        "real neighbor": TEAL,
        "wrong control": GRAY,
        "random": ORANGE,
    }
    for scope, offset, alpha, hatch in (
        ("external_candidate", -width / 2, 0.55, None),
        ("hard_ood_40pct", width / 2, 1.0, "//"),
    ):
        local = frame[frame["scope"] == scope].set_index("label").loc[labels]
        colors = [class_color[value] for value in local["source_class"]]
        bars = ax.bar(
            x + offset,
            local["auc20"],
            width,
            color=colors,
            alpha=alpha,
            hatch=hatch,
            edgecolor="white" if hatch is None else colors,
            linewidth=0.55,
        )
        for idx in (0, 1):
            value = float(local.iloc[idx]["auc20"])
            ax.text(
                bars[idx].get_x() + bars[idx].get_width() / 2,
                value - 1.5,
                f"{value:.0f}",
                ha="center",
                va="top",
                fontsize=5.8,
                color=TEAL_DARK if scope == "external_candidate" else "white",
                fontweight="bold",
            )
            count = int(local.iloc[idx]["recall20_count"])
            total = int(local.iloc[idx]["true_top_entities"])
            ax.text(
                bars[idx].get_x() + bars[idx].get_width() / 2,
                value + 1.2,
                f"{count}/{total}",
                ha="center",
                va="bottom",
                fontsize=5.0,
                color=TEAL_DARK,
                fontweight="bold",
            )
    ax.set_xticks(x, labels, rotation=30, ha="right")
    ax.set_ylim(0, 62)
    ax.set_ylabel("Static ranking AUC20")
    ax.set_title(
        "Neighbor rankings retain OOD signal\n"
        "(prespecified retrospective evidence)"
    )
    ax.text(
        0.02,
        0.98,
        "labels above teal bars: recall20 count",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=5.1,
        color=TEAL_DARK,
    )
    ax.legend(
        handles=[
            Patch(facecolor=GRAY, alpha=0.55, edgecolor="none", label="external"),
            Patch(facecolor="white", edgecolor=GRAY, hatch="//", label="hard OOD"),
        ],
        loc="upper right",
        handlelength=1.25,
    )
    panel_label(ax, "c")


def main() -> None:
    ensure_output_dirs()
    validation = load_validation()
    figure, axes = plt.subplots(1, 3, figsize=(6.72, 2.75), layout="constrained")
    panel_a(axes[0], validation)
    panel_b(axes[1], validation)
    panel_c(axes[2], validation)
    base = FIGURES / "caltech_external_policy_decomposition"
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
