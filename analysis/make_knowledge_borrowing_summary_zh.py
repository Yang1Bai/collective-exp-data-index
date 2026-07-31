from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures" / "knowledge_borrowing_summary_zh"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "DengXian", "SimHei", "Arial", "DejaVu Sans"],
        "font.size": 7.0,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)

NAVY = "#173B57"
BLUE = "#3977A8"
BLUE_SOFT = "#EAF3FA"
TEAL = "#3D8D8A"
TEAL_SOFT = "#E8F5F3"
GREEN = "#2F7D57"
GREEN_SOFT = "#E9F5EE"
RED = "#B55B5B"
RED_SOFT = "#F9ECEB"
GOLD = "#D39B32"
GOLD_SOFT = "#FBF3DF"
INK = "#20313D"
MID = "#657682"
LIGHT = "#D9E2E8"
PAPER = "#F6F8FA"


def card(ax, xy, width, height, facecolor, edgecolor=LIGHT, radius=0.018, lw=1.0, zorder=1):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.008,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        transform=ax.transAxes,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def arrow(ax, start, end, color=BLUE, lw=1.6, mutation=12, zorder=4):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation,
        linewidth=lw,
        color=color,
        transform=ax.transAxes,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def draw_source_icon(ax, x, y, color, label, sublabel):
    card(ax, (x, y), 0.205, 0.105, "white", edgecolor=color, radius=0.014, lw=1.0, zorder=2)
    ax.add_patch(Circle((x + 0.026, y + 0.054), 0.015, transform=ax.transAxes,
                        facecolor=color, edgecolor="none", zorder=3))
    ax.text(x + 0.052, y + 0.069, label, transform=ax.transAxes, color=INK,
            fontsize=8.2, fontweight="bold", va="center", zorder=4)
    ax.text(x + 0.052, y + 0.036, sublabel, transform=ax.transAxes, color=MID,
            fontsize=6.4, va="center", zorder=4)


def outcome_card(ax, y, title, big, detail, face, edge, symbol):
    card(ax, (0.665, y), 0.292, 0.142, face, edgecolor=edge, radius=0.017, lw=1.1, zorder=2)
    if symbol == "pass":
        ax.add_patch(Circle((0.690, y + 0.108), 0.013, transform=ax.transAxes,
                            facecolor=edge, edgecolor="none", zorder=4))
        ax.text(0.690, y + 0.108, "+", transform=ax.transAxes, color="white",
                fontsize=9, fontweight="bold", ha="center", va="center", zorder=5)
    else:
        ax.add_patch(Circle((0.690, y + 0.108), 0.013, transform=ax.transAxes,
                            facecolor="white", edgecolor=edge, linewidth=1.0, zorder=4))
        ax.text(0.690, y + 0.108, "x", transform=ax.transAxes, color=edge,
                fontsize=8, fontweight="bold", ha="center", va="center", zorder=5)
    ax.text(0.716, y + 0.109, title, transform=ax.transAxes, color=INK,
            fontsize=8.5, fontweight="bold", va="center", zorder=4)
    ax.text(0.688, y + 0.065, big, transform=ax.transAxes, color=edge,
            fontsize=13.0, fontweight="bold", va="center", zorder=4)
    ax.text(0.688, y + 0.027, detail, transform=ax.transAxes, color=MID,
            fontsize=6.5, va="center", zorder=4)


def main():
    fig = plt.figure(figsize=(7.20, 4.05), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0",
                                facecolor=PAPER, edgecolor="none", transform=ax.transAxes))

    ax.text(0.045, 0.938, "相邻实验知识如何修复数据贫乏的 OOD 探索？",
            transform=ax.transAxes, color=NAVY, fontsize=15.5, fontweight="bold", va="center")
    ax.text(0.046, 0.888, "迁移最窄、可证伪的关系或排序，而不是简单合并数据库",
            transform=ax.transAxes, color=MID, fontsize=8.2, va="center")
    card(ax, (0.755, 0.900), 0.202, 0.056, "white", edgecolor=LIGHT, radius=0.014, lw=0.9)
    ax.text(0.856, 0.928, "21 个分析资源  ·  96,184 条实验测量",
            transform=ax.transAxes, ha="center", va="center", color=INK,
            fontsize=6.7, fontweight="bold")

    card(ax, (0.035, 0.175), 0.235, 0.655, BLUE_SOFT, edgecolor="#BED4E5", radius=0.022, lw=1.0)
    ax.text(0.058, 0.790, "相邻实验提供什么？", transform=ax.transAxes,
            color=NAVY, fontsize=9.4, fontweight="bold", va="center")
    ax.text(0.058, 0.755, "分别训练供体，不混合原始标签", transform=ax.transAxes,
            color=MID, fontsize=6.6, va="center")
    draw_source_icon(ax, 0.050, 0.610, BLUE, "组成–性能关系", "受控材料扰动")
    draw_source_icon(ax, 0.050, 0.475, TEAL, "配方–状态关系", "跨盐与温度条件")
    draw_source_icon(ax, 0.050, 0.340, GOLD, "候选相对次序", "跨数据库筛选先验")
    ax.text(0.058, 0.250, "关键：供体只提出可检验的科学假设",
            transform=ax.transAxes, color=NAVY, fontsize=7.0, fontweight="bold")
    ax.text(0.058, 0.218, "相似不等于可迁移", transform=ax.transAxes,
            color=MID, fontsize=6.5)

    card(ax, (0.315, 0.175), 0.295, 0.655, "white", edgecolor=LIGHT, radius=0.022, lw=1.0)
    ax.text(0.340, 0.790, "数据贫乏的受体与 OOD 候选", transform=ax.transAxes,
            color=NAVY, fontsize=9.4, fontweight="bold", va="center")
    ax.text(0.340, 0.754, "少量已测样本必须支持未见区域决策", transform=ax.transAxes,
            color=MID, fontsize=6.6, va="center")

    plot_x0, plot_y0, plot_w, plot_h = 0.340, 0.575, 0.245, 0.135
    ax.add_patch(FancyBboxPatch((plot_x0, plot_y0), plot_w, plot_h,
                                boxstyle="round,pad=0.004,rounding_size=0.01",
                                facecolor="#F9FBFC", edgecolor=LIGHT, linewidth=0.8,
                                transform=ax.transAxes, zorder=2))
    ax.plot([0.455, 0.455], [plot_y0 + 0.012, plot_y0 + plot_h - 0.012],
            transform=ax.transAxes, color="#9AAAB5", lw=0.9, ls=(0, (3, 2)), zorder=3)
    observed = [(0.365, 0.615), (0.387, 0.665), (0.410, 0.625), (0.429, 0.680), (0.397, 0.592)]
    candidates = [(0.486, 0.602), (0.512, 0.672), (0.540, 0.626), (0.564, 0.690), (0.573, 0.586), (0.515, 0.592)]
    for x, y in observed:
        ax.add_patch(Circle((x, y), 0.008, transform=ax.transAxes, facecolor=BLUE,
                            edgecolor="white", linewidth=0.6, zorder=4))
    for x, y in candidates:
        ax.add_patch(Circle((x, y), 0.008, transform=ax.transAxes, facecolor="white",
                            edgecolor=GOLD, linewidth=1.1, zorder=4))
    ax.text(0.392, 0.715, "已测", transform=ax.transAxes, color=BLUE, fontsize=6.2, ha="center")
    ax.text(0.525, 0.715, "OOD 未见候选", transform=ax.transAxes, color=GOLD, fontsize=6.2, ha="center")

    funnel = Polygon([(0.345, 0.515), (0.580, 0.515), (0.535, 0.405), (0.390, 0.405)],
                     closed=True, transform=ax.transAxes, facecolor=TEAL_SOFT,
                     edgecolor=TEAL, linewidth=1.0, zorder=2)
    ax.add_patch(funnel)
    ax.text(0.462, 0.486, "四重门控", transform=ax.transAxes, color=TEAL,
            fontsize=8.3, fontweight="bold", ha="center", va="center")
    ax.text(0.462, 0.445, "状态对齐  ·  无泄漏  ·  强受体基线  ·  匹配伪对照",
            transform=ax.transAxes, color=INK, fontsize=6.2, ha="center", va="center")
    arrow(ax, (0.462, 0.395), (0.462, 0.335), color=TEAL, lw=1.4, mutation=11)
    card(ax, (0.370, 0.225), 0.185, 0.102, GOLD_SOFT, edgecolor="#E4C776", radius=0.014, lw=0.9)
    ax.text(0.462, 0.293, "按决策目标选择迁移形式", transform=ax.transAxes,
            color=NAVY, fontsize=7.2, fontweight="bold", ha="center", va="center")
    ax.text(0.462, 0.252, "数值预测  /  候选排序  /  拒绝", transform=ax.transAxes,
            color=MID, fontsize=6.6, ha="center", va="center")
    arrow(ax, (0.270, 0.505), (0.315, 0.505), color=BLUE, lw=1.7, mutation=12)
    arrow(ax, (0.610, 0.505), (0.655, 0.505), color=TEAL, lw=1.7, mutation=12)

    ax.text(0.665, 0.790, "门控后的三种结局", transform=ax.transAxes,
            color=NAVY, fontsize=9.4, fontweight="bold", va="center")
    ax.text(0.665, 0.754, "正迁移与拒绝共同构成知识借贷地图", transform=ax.transAxes,
            color=MID, fontsize=6.6, va="center")
    outcome_card(ax, 0.570, "数值预测通过｜未见盐", "log-RMSE ↓ 28.64%", "零样本 raw R² = 0.629  ·  ρ = 0.871", GREEN_SOFT, GREEN, "pass")
    outcome_card(ax, 0.395, "候选排序通过｜仅 5 个受体测量", "ρ: 0.537  →  0.910", "Δρ = 0.374 [0.213, 0.562]  ·  精确率 0.490 → 0.933", BLUE_SOFT, BLUE, "pass")
    outcome_card(ax, 0.220, "冻结外部受体｜拒绝迁移", "0.694  <  0.783", "供体排序低于同标签受体模型；不调参、不补救", RED_SOFT, RED, "reject")

    card(ax, (0.035, 0.055), 0.922, 0.073, "white", edgecolor=LIGHT, radius=0.014, lw=0.9)
    ax.text(0.058, 0.091, "为什么必须门控？", transform=ax.transAxes,
            color=RED, fontsize=7.2, fontweight="bold", va="center")
    ax.text(0.196, 0.091, "通用 donor-feature 注入在 40 条真实 OOD 边中 0 条通过完整修复门槛",
            transform=ax.transAxes, color=INK, fontsize=7.0, fontweight="bold", va="center")
    ax.text(0.735, 0.091, "结论：关系与决策匹配，而非数据库越多越好",
            transform=ax.transAxes, color=NAVY, fontsize=6.8, fontweight="bold", va="center")

    fig.savefig(OUT.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches="tight", pad_inches=0.02,
                pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
