"""Figure 4: ordinal borrowing rescues screening but remains programme-specific."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure4_ordinal_screening_nmi_v2"
SOURCE = SOURCE_DIR / "figure4_ordinal_screening_nmi_v2.csv"

NAVY = "#173B6C"
BLUE = "#3478BD"
TEAL = "#148A82"
GREEN = "#3C9662"
ORANGE = "#E8872E"
CORAL = "#C95A50"
PURPLE = "#7560A8"
INK = "#243143"
MID = "#7E8998"
GRID = "#D8DEE8"
PALE = "#F5F8FB"
LIGHT_BLUE = "#DCEAF6"
LIGHT_TEAL = "#DDF1EE"
LIGHT_ORANGE = "#FCEBD7"
LIGHT_CORAL = "#F6E1DE"


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


def panel_label(ax: plt.Axes, label: str, x: float = 0.0, y: float = 1.03) -> None:
    ax.text(x, y, label, transform=ax.transAxes, fontsize=8.0, fontweight="bold",
            ha="left", va="bottom", color="black")


def flask(ax: plt.Axes, cx: float, cy: float, s: float, accent: str) -> None:
    verts=[(cx-.12*s,cy+.40*s),(cx-.12*s,cy+.12*s),(cx-.37*s,cy-.34*s),
           (cx+.37*s,cy-.34*s),(cx+.12*s,cy+.12*s),(cx+.12*s,cy+.40*s)]
    ax.add_patch(Polygon(verts,closed=True,facecolor="#EEF6FB",edgecolor="#789AB1",lw=.55))
    ax.add_patch(Rectangle((cx-.27*s,cy-.28*s),.54*s,.15*s,facecolor=LIGHT_BLUE,edgecolor="none"))
    for dx,c in [(-.17,NAVY),(0,accent),(.17,ORANGE)]:
        ax.add_patch(Circle((cx+dx*s,cy-.20*s),.055*s,facecolor=c,edgecolor="white",lw=.25))


def source_card(ax: plt.Axes, y: float, title: str, count: str, color: str) -> None:
    flask(ax,.12,y+.055,.18,color)
    ax.add_patch(FancyBboxPatch((.23,y),.50,.12,boxstyle="round,pad=.012,rounding_size=.018",
                                facecolor=PALE,edgecolor=color,lw=.65))
    ax.text(.26,y+.078,title,fontsize=6.4,color=INK,fontweight="bold",va="center")
    ax.text(.26,y+.034,count,fontsize=5.7,color=MID,va="center")


def candidate_grid(ax: plt.Axes, x: float, y: float, w: float, h: float) -> None:
    # Fixed non-quantitative colour ordering for the schematic candidate field.
    values=np.asarray([.12,.71,.34,.89,.22,.63,.45,.81,.18,.56,.93,.39,.68,.27,.76,.10,
                       .52,.86,.31,.65,.20,.96,.43,.73,.15,.59,.84,.37,.69,.25,.91])
    for i,v in enumerate(values):
        r,c=divmod(i,7)
        xx=x+c*w/7; yy=y+(4-r)*h/5
        face=plt.get_cmap("YlGnBu")(.20+.65*v)
        ax.add_patch(Circle((xx,yy),.010,facecolor=face,edgecolor="white",lw=.2))
    for i in [3,9,18,25,29]:
        r,c=divmod(i,7); xx=x+c*w/7; yy=y+(4-r)*h/5
        ax.add_patch(Circle((xx,yy),.014,facecolor="white",edgecolor=ORANGE,lw=.8))


def panel_a(ax: plt.Axes) -> None:
    panel_label(ax,"a",0.0,1.01)
    ax.text(.09,1.015,"Route knowledge to the supported decision",
            transform=ax.transAxes,fontsize=7.0,fontweight="bold",color=INK,va="bottom")
    ax.set(xlim=(0,1),ylim=(0,1)); ax.axis("off")
    source_card(ax,.77,"large multi-salt source","10,012 measurements",NAVY)
    source_card(ax,.61,"literature mixture source","410 measurements",ORANGE)
    source_card(ax,.45,"controlled-temperature source","1,089 aggregates",TEAL)
    ax.text(.48,.39,"separate models  →  equal programme weight",ha="center",fontsize=6.0,color=INK)
    ax.add_patch(FancyArrowPatch((.48,.38),(.48,.31),arrowstyle="-|>",mutation_scale=7,lw=1.2,color=TEAL))
    candidate_grid(ax,.27,.18,.42,.12)
    ax.text(.48,.15,"36 recipient formulations · 5 measured anchors",ha="center",fontsize=6.2,
            color=INK,fontweight="bold")
    ax.text(.48,.115,"source–recipient record overlap = 0",ha="center",fontsize=5.7,color=MID)
    ax.add_patch(FancyArrowPatch((.43,.10),(.27,.035),arrowstyle="-|>",mutation_scale=7,lw=1.0,color=GREEN))
    ax.add_patch(FancyArrowPatch((.53,.10),(.72,.035),arrowstyle="-|>",mutation_scale=7,lw=1.0,color=CORAL))
    ax.add_patch(FancyBboxPatch((.04,.015),.34,.058,boxstyle="round,pad=.01,rounding_size=.016",
                                facecolor=LIGHT_TEAL,edgecolor=GREEN,lw=.7))
    ax.text(.21,.052,"candidate order",ha="center",va="center",fontsize=6.5,color=GREEN,fontweight="bold")
    ax.text(.21,.028,"accept for screening",ha="center",va="center",fontsize=5.5,color=INK)
    ax.add_patch(FancyBboxPatch((.62,.015),.34,.058,boxstyle="round,pad=.01,rounding_size=.016",
                                facecolor=LIGHT_CORAL,edgecolor=CORAL,lw=.7))
    ax.text(.79,.052,"absolute calibration",ha="center",va="center",fontsize=6.5,color=CORAL,fontweight="bold")
    ax.text(.79,.028,"abstain",ha="center",va="center",fontsize=5.5,color=INK)


def model_label(name: str) -> str:
    return {
        "programme_balanced_source_portfolio":"neighbouring-programme score",
        "recipient_oracle":"per-draw recipient oracle",
        "recipient_rank_ensemble":"recipient rank ensemble",
        "rbf_kernel_ridge_alpha_10":"RBF kernel ridge, α=10",
        "rbf_kernel_ridge_alpha_1":"RBF kernel ridge, α=1",
        "rbf_kernel_ridge_alpha_0.1":"RBF kernel ridge, α=0.1",
        "random_forest":"Random Forest",
        "extra_trees":"ExtraTrees",
        "ridge_alpha_0.1":"Ridge, α=0.1",
        "ridge_alpha_1":"Ridge, α=1",
        "ridge_alpha_10":"Ridge, α=10",
        "ridge_alpha_100":"Ridge, α=100",
        "knn_1":"1-nearest neighbour",
        "knn_3":"3-nearest neighbours",
        "knn_5":"5-nearest neighbours",
    }[name]


def interval(values: pd.Series) -> tuple[float,float,float]:
    return float(values.mean()),float(values.quantile(.025)),float(values.quantile(.975))


def stress_frame(stress: pd.DataFrame, budget: int=5) -> pd.DataFrame:
    primary=stress[stress["anchor_budget"].eq(budget)].copy()
    recipient=primary[~primary["model"].eq("programme_balanced_source_portfolio")]
    oracle=(recipient.groupby("draw",as_index=False)["spearman"].max().assign(model="recipient_oracle"))
    return pd.concat([primary[["draw","model","spearman"]],oracle],ignore_index=True)


def panel_b(ax: plt.Axes, stress: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax,"b",0.0,1.03)
    ax.set_title("Neighbouring programmes outperform every five-label recipient model",loc="left",pad=8,x=.07)
    frame=stress_frame(stress,5)
    order=frame.groupby("model")["spearman"].mean().sort_values().index.tolist()
    rows=[]
    for yi,name in enumerate(order):
        mean,lo,hi=interval(frame.loc[frame["model"].eq(name),"spearman"])
        color=TEAL if name=="programme_balanced_source_portfolio" else ORANGE if name=="recipient_oracle" else "#A5AFB8"
        ax.plot([lo,hi],[yi,yi],color=color,lw=2.1 if name in {"programme_balanced_source_portfolio","recipient_oracle"} else 1.3,
                solid_capstyle="round")
        ax.scatter(mean,yi,s=34 if name=="programme_balanced_source_portfolio" else 19,
                   color=color,edgecolor="white",linewidth=.45,zorder=3)
        rows.append({"panel":"b","model":name,"anchor_budget":5,"estimate":mean,"ci95_low":lo,"ci95_high":hi})
    ax.axvline(0,color=INK,lw=.7); ax.grid(axis="x",color=GRID,lw=.45)
    ax.set_yticks(np.arange(len(order))); ax.set_yticklabels([model_label(x) for x in order]); ax.tick_params(axis="y",length=0)
    ax.set_xlim(-.18,1.02); ax.set_xlabel("Spearman candidate-order correlation")
    source_mean=frame.loc[frame["model"].eq("programme_balanced_source_portfolio"),"spearman"].mean()
    best_name=(frame[~frame["model"].isin(["programme_balanced_source_portfolio","recipient_oracle"])]
               .groupby("model")["spearman"].mean().idxmax())
    best_mean=frame.loc[frame["model"].eq(best_name),"spearman"].mean()
    ax.text(source_mean+.018,order.index("programme_balanced_source_portfolio"),f"{source_mean:.3f}",
            color=TEAL,fontweight="bold",va="center")
    ax.text(best_mean+.018,order.index(best_name),f"{best_mean:.3f}",color=INK,va="center")
    ax.text(.98,.02,"points: means; bars: 2.5th–97.5th percentiles\n100 outcome-independent anchor selections",
            transform=ax.transAxes,ha="right",va="bottom",fontsize=5.7,color=MID)
    return pd.DataFrame(rows)


def panel_c(ax: plt.Axes, stress: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax,"c",0.0,1.04)
    ax.set_title("Borrowed rank survives sparse anchors",loc="left",pad=8,x=.11)
    budgets=[3,5,10]
    series={
        "neighbouring-programme score":("programme_balanced_source_portfolio",TEAL),
        "best fixed recipient model":("rbf_kernel_ridge_alpha_10",NAVY),
        "recipient rank ensemble":("recipient_rank_ensemble",PURPLE),
    }
    rows=[]
    for label,(model,color) in series.items():
        means=[]; lows=[]; highs=[]
        for b in budgets:
            vals=stress[(stress["anchor_budget"].eq(b))&(stress["model"].eq(model))]["spearman"]
            mean,lo,hi=interval(vals); means.append(mean); lows.append(lo); highs.append(hi)
            rows.append({"panel":"c","model":model,"anchor_budget":b,"estimate":mean,"ci95_low":lo,"ci95_high":hi})
        ax.plot(budgets,means,marker="o",color=color,lw=1.8,label=label)
        ax.fill_between(budgets,lows,highs,color=color,alpha=.10,linewidth=0)
    ax.set_xticks(budgets); ax.set_xlabel("measured recipient formulations")
    ax.set_ylabel("Spearman correlation")
    ax.set_ylim(-.1,1.01); ax.grid(color=GRID,lw=.45)
    ax.legend(frameon=False,loc="lower right",handlelength=1.6)
    ax.text(5,.94,"0.910",color=TEAL,ha="center",fontweight="bold")
    ax.text(5,.56,"0.537",color=NAVY,ha="center")
    return pd.DataFrame(rows)


def mini_boundary(ax: plt.Axes, title: str, metric: str, donor: float, target: float,
                  decision: str, color: str, delta_text: str) -> None:
    ax.set_title(title,loc="left",fontsize=6.5,pad=2)
    ax.plot([donor,target],[0,0],color=GRID,lw=3.2,solid_capstyle="round")
    ax.scatter(donor,0,s=43,color=TEAL,edgecolor="white",linewidth=.5,zorder=3)
    ax.scatter(target,0,s=43,color=NAVY,edgecolor="white",linewidth=.5,zorder=3)
    ax.text(donor,.18,f"donor\n{donor:.3f}",ha="center",va="bottom",fontsize=6.1,color=TEAL)
    ax.text(target,-.18,f"recipient\n{target:.3f}",ha="center",va="top",fontsize=6.1,color=NAVY)
    decision_x=.04 if donor>target else .98
    decision_ha="left" if donor>target else "right"
    ax.text(decision_x,.88,decision,transform=ax.transAxes,ha=decision_ha,va="top",fontsize=6.8,
            color=color,fontweight="bold")
    ax.text(decision_x,.66,delta_text,transform=ax.transAxes,ha=decision_ha,va="top",fontsize=5.5,color=MID)
    ax.set_xlim(0.45,1.0); ax.set_ylim(-.52,.52); ax.set_xlabel(metric)
    ax.set_yticks([]); ax.grid(axis="x",color=GRID,lw=.4)


def panel_d(ax_top: plt.Axes, ax_bottom: plt.Axes, finales: dict) -> pd.DataFrame:
    panel_label(ax_top,"d",-0.02,1.17)
    ax_top.text(.08,1.175,"Programme boundary",transform=ax_top.transAxes,
                fontsize=7.0,fontweight="bold",color=INK,ha="left",va="bottom")
    mini_boundary(ax_top,"36-formulation recipient","Spearman correlation",.910,.537,
                  "accept screening",GREEN,"Δρ = +0.374 [0.213, 0.562]")
    p=finales["primary"]
    mini_boundary(ax_bottom,"frozen second recipient","pairwise concordance",
                  p["donor_concordance"],p["strongest_baseline_concordance"],
                  "abstain",CORAL,"Δ = −0.089 [−0.293, 0.096]")
    return pd.DataFrame([
        {"panel":"d","programme":"SolventSeg","model":"donor","estimate":.910},
        {"panel":"d","programme":"SolventSeg","model":"recipient","estimate":.537},
        {"panel":"d","programme":"FINALES","model":"donor","estimate":p["donor_concordance"]},
        {"panel":"d","programme":"FINALES","model":"recipient","estimate":p["strongest_baseline_concordance"]},
    ])


def main() -> None:
    FIGURES.mkdir(parents=True,exist_ok=True); SOURCE_DIR.mkdir(parents=True,exist_ok=True)
    stress=pd.read_csv(RESULTS/"bamboomixer_recipient_baseline_stress_test_metrics.csv")
    finales=json.loads((RESULTS/"finales_rank_replication_summary.json").read_text(encoding="utf-8"))
    if finales.get("status")!="verified-complete":
        raise RuntimeError("Frozen second-recipient result is not verified")
    fig=plt.figure(figsize=(7.2047,5.9055))  # 183 × 150 mm
    outer=fig.add_gridspec(2,2,width_ratios=[.31,.69],height_ratios=[.57,.43],
                           left=.055,right=.985,bottom=.10,top=.94,wspace=.40,hspace=.50)
    ax_a=fig.add_subplot(outer[:,0]); ax_b=fig.add_subplot(outer[0,1])
    lower=outer[1,1].subgridspec(1,2,width_ratios=[.53,.47],wspace=.42)
    ax_c=fig.add_subplot(lower[0,0])
    dgrid=lower[0,1].subgridspec(2,1,hspace=.65)
    ax_d1=fig.add_subplot(dgrid[0,0]); ax_d2=fig.add_subplot(dgrid[1,0])
    panel_a(ax_a)
    data=[panel_b(ax_b,stress),panel_c(ax_c,stress),panel_d(ax_d1,ax_d2,finales)]
    pd.concat(data,ignore_index=True,sort=False).to_csv(SOURCE,index=False)
    fig.savefig(f"{OUT}.svg",bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.pdf",bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.png",dpi=300,bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.tiff",dpi=600,bbox_inches=None,pad_inches=0,
                pil_kwargs={"compression":"tiff_lzw"})
    plt.close(fig)


if __name__=="__main__":
    main()
