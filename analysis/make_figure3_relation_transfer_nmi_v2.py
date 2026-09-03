"""Figure 3: qualified relations improve selected complete OOD tasks."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
FIGURES = ROOT / "analysis" / "figures"
SOURCE_DIR = FIGURES / "source_data"
OUT = FIGURES / "figure3_relation_transfer_nmi_v2"
SOURCE = SOURCE_DIR / "figure3_relation_transfer_nmi_v2.csv"

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


def rounded(ax: plt.Axes, xy: tuple[float, float], w: float, h: float,
            face: str, edge: str, title: str, body: str) -> None:
    x, y = xy
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.025",
                                facecolor=face, edgecolor=edge, lw=0.75))
    ax.text(x + .05*w, y + .70*h, title, ha="left", va="center", color=INK,
            fontsize=6.7, fontweight="bold")
    ax.text(x + .05*w, y + .28*h, body, ha="left", va="center", color=MID,
            fontsize=5.8, linespacing=1.15)


def catalyst_glyph(ax: plt.Axes, cx: float, cy: float, scale: float, accent: str) -> None:
    ax.add_patch(Polygon([(cx-.45*scale, cy-.18*scale), (cx+.45*scale, cy-.18*scale),
                          (cx+.36*scale, cy-.31*scale), (cx-.36*scale, cy-.31*scale)],
                         closed=True, facecolor="#D6DCE2", edgecolor="#87929C", lw=.45))
    for r in range(3):
        for c in range(6):
            x = cx + (c-2.5)*.14*scale + (r%2)*.045*scale
            y = cy-.10*scale + r*.10*scale
            color = accent if (r+c)%5 == 0 else NAVY
            ax.add_patch(Circle((x,y), .045*scale, facecolor=color, edgecolor="white", lw=.25))


def flask_glyph(ax: plt.Axes, cx: float, cy: float, scale: float, salt_color: str) -> None:
    verts = [(cx-.12*scale,cy+.38*scale),(cx-.12*scale,cy+.10*scale),
             (cx-.36*scale,cy-.35*scale),(cx+.36*scale,cy-.35*scale),
             (cx+.12*scale,cy+.10*scale),(cx+.12*scale,cy+.38*scale)]
    ax.add_patch(Polygon(verts, closed=True, facecolor="#EEF6FB", edgecolor="#769AB5", lw=.55))
    ax.add_patch(Polygon([(cx-.29*scale,cy-.18*scale),(cx+.29*scale,cy-.18*scale),
                          (cx+.34*scale,cy-.31*scale),(cx-.34*scale,cy-.31*scale)],
                         closed=True, facecolor=LIGHT_BLUE, edgecolor="none"))
    for dx, dy, color in [(-.18,-.18,NAVY),(0,-.25,salt_color),(.18,-.16,ORANGE)]:
        ax.add_patch(Circle((cx+dx*scale,cy+dy*scale),.055*scale,facecolor=color,
                            edgecolor="white",lw=.25))


def panel_a(ax: plt.Axes) -> None:
    panel_label(ax, "a", 0.0, 1.01)
    ax.text(.08, 1.015, "Qualified relations at increasing transfer distance",
            transform=ax.transAxes, fontsize=7.0, fontweight="bold", color=INK, va="bottom")
    ax.set(xlim=(0,1), ylim=(0,1)); ax.axis("off")
    ax.text(.02,.92,"controlled system shift",fontsize=6.2,color=TEAL,fontweight="bold")
    catalyst_glyph(ax,.20,.77,.28,TEAL)
    ax.text(.20,.59,"462-catalyst donor",ha="center",fontsize=6.4,color=INK,fontweight="bold")
    ax.text(.20,.55,"same assay · same six-slot grid",ha="center",fontsize=5.7,color=MID)
    for i,t in enumerate(TARGETS):
        y=.83-i*.115
        color=ROUTE_COLOR[t]
        ax.add_patch(FancyArrowPatch((.36,.70),(.50,y),arrowstyle="-|>",mutation_scale=6,
                                     lw=.65,color=color,alpha=.75))
        rounded(ax,(.51,y-.043),.46,.087,
                LIGHT_TEAL if color==GREEN else LIGHT_ORANGE if color==ORANGE else LIGHT_CORAL,
                color,f"{t}  {TARGET_LABELS[t]}",ROUTE[t])
    ax.plot([.02,.98],[.43,.43],color=GRID,lw=.8)
    ax.text(.02,.39,"cross-database + unseen component",fontsize=6.2,color=TEAL,fontweight="bold")
    for k in range(5):
        flask_glyph(ax,.11+k*.065,.25,.15,[BLUE,TEAL,PURPLE,ORANGE,NAVY][k])
    ax.text(.20,.12,"22 source salts",ha="center",fontsize=6.4,color=INK,fontweight="bold")
    ax.text(.20,.08,"10,407 measurements",ha="center",fontsize=5.7,color=MID)
    ax.add_patch(FancyArrowPatch((.39,.25),(.62,.25),arrowstyle="-|>",mutation_scale=8,
                                 lw=1.6,color=TEAL))
    ax.text(.505,.30,"mixture relation",ha="center",fontsize=6.0,color=TEAL,fontweight="bold")
    ax.text(.505,.18,"component-order invariant",ha="center",fontsize=5.5,color=MID)
    flask_glyph(ax,.78,.25,.29,CORAL)
    ax.text(.78,.08,"unseen LiAsF$_6$",ha="center",fontsize=6.4,color=INK,fontweight="bold")
    ax.text(.78,.04,"176 formulations · 1,827 rows",ha="center",fontsize=5.7,color=MID)


def forest(ax: plt.Axes, source: pd.DataFrame, measure: str, scale: float,
           xlabel: str, show_labels: bool) -> None:
    rows = source[(source["panel"].eq("c")) & (source["measure"].eq(measure))].set_index("target").loc[TARGETS]
    y = np.arange(4)[::-1]
    ax.axvline(0,color=INK,lw=.7)
    ax.axvspan(0, 50 if scale==100 else .5, color=LIGHT_TEAL, alpha=.55, zorder=0)
    for yi,(target,row) in zip(y,rows.iterrows()):
        est,lo,hi=scale*row["estimate"],scale*row["ci95_low"],scale*row["ci95_high"]
        color=ROUTE_COLOR[target]
        ax.plot([lo,hi],[yi,yi],color=color,lw=2.0,solid_capstyle="round")
        ax.scatter(est,yi,s=31,color=color,edgecolor="white",linewidth=.5,zorder=3)
        ax.text(hi+.018*(ax.get_xlim()[1]-ax.get_xlim()[0]) if ax.get_xlim()[1] else hi,yi,
                f"{est:+.1f}%" if scale==100 else f"{est:+.3f}",fontsize=5.8,color=color,
                va="center",ha="left",fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([f"{t}  {TARGET_LABELS[t]}" for t in TARGETS] if show_labels else [])
    ax.tick_params(axis="y",length=0)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x",color=GRID,lw=.45)


def panel_b(ax_left: plt.Axes, ax_right: plt.Axes, source: pd.DataFrame) -> None:
    panel_label(ax_left,"b",0.0,1.06)
    ax_left.set_title("Five anchors separate prediction from ranking",loc="left",pad=9,x=.13)
    ax_left.set_xlim(-20,38)
    forest(ax_left,source,"relative_rmse_gain",100,"relative RMSE gain (%)",True)
    ax_right.set_xlim(-.05,.50)
    forest(ax_right,source,"spearman_gain",1,"Spearman gain",False)
    ax_left.text(.02,-.28,"post-primary composition relation; intervals bootstrap complete candidates",
                 transform=ax_left.transAxes,fontsize=5.6,color=MID,ha="left",va="top")


def panel_c(ax: plt.Axes, predictions: pd.DataFrame) -> pd.DataFrame:
    panel_label(ax,"c",0.0,1.03)
    ax.set_title("Zero-label prediction of an unseen salt",loc="left",pad=8,x=.10)
    frame=predictions[predictions["scope"].eq("all_source_salts")].copy()
    hb=ax.hexbin(frame["y_log10_conductivity"],frame["prediction_log10_conductivity"],
                 gridsize=34,mincnt=1,cmap=LinearSegmentedColormap.from_list("density",["#E8F3F6",TEAL,NAVY]),
                 linewidths=0,rasterized=True)
    lo=min(frame["y_log10_conductivity"].min(),frame["prediction_log10_conductivity"].min())
    hi=max(frame["y_log10_conductivity"].max(),frame["prediction_log10_conductivity"].max())
    ax.plot([lo,hi],[lo,hi],color=CORAL,lw=.9,ls=(0,(4,2)))
    ax.set_xlim(lo,hi); ax.set_ylim(lo,hi)
    ax.set_xlabel("measured log$_{10}$ conductivity")
    ax.set_ylabel("borrowed prediction")
    ax.grid(color=GRID,lw=.4)
    ax.text(.04,.95,"$R^2$ = 0.732\n$\\rho$ = 0.871\n$n$ = 1,827",
            transform=ax.transAxes,ha="left",va="top",fontsize=7.0,color=INK,
            bbox={"boxstyle":"round,pad=.28","facecolor":"white","edgecolor":"none","alpha":.88})
    return frame.assign(panel="c")


def interval(values: pd.Series) -> tuple[float,float,float]:
    return float(values.mean()),float(values.quantile(.025)),float(values.quantile(.975))


def panel_d(ax: plt.Axes, bootstrap: pd.DataFrame, summary: dict) -> pd.DataFrame:
    panel_label(ax,"d",0.0,1.03)
    ax.set_title("Matched falsifiers",loc="left",pad=8,x=.10)
    order=["state_only","chemistry_permuted","without_LiPF6","LiPF6_only",
           "LiBOB_wrong_salt_control","LiBF4_fluorinated_control"]
    labels={
        "state_only":"state only",
        "chemistry_permuted":"permuted chemistry",
        "without_LiPF6":"without nearest salt",
        "LiPF6_only":"nearest salt only",
        "LiBOB_wrong_salt_control":"wrong-salt control",
        "LiBF4_fluorinated_control":"fluorinated control",
    }
    y=np.arange(len(order))[::-1]
    ax.axvline(0,color=INK,lw=.75)
    ax.axvspan(0,50,color=LIGHT_TEAL,alpha=.55)
    rows=[]
    for yi,name in zip(y,order):
        vals=100*bootstrap.loc[bootstrap["comparator"].eq(name),"relative_log_rmse_gain"]
        mean,lo,hi=interval(vals)
        color=TEAL if name in {"state_only","chemistry_permuted"} else BLUE
        ax.plot([lo,hi],[yi,yi],color=color,lw=2.1,solid_capstyle="round")
        ax.scatter(mean,yi,s=32,color=color,edgecolor="white",linewidth=.5,zorder=3)
        ax.text(hi+1.0,yi,f"{mean:.1f}%",ha="left",va="center",fontsize=5.9,color=color,fontweight="bold")
        rows.append({"panel":"d","comparator":name,"estimate":mean/100,"ci95_low":lo/100,"ci95_high":hi/100})
    ax.set_yticks(y); ax.set_yticklabels([labels[x] for x in order]); ax.tick_params(axis="y",length=0)
    ax.set_xlim(-3,51); ax.set_xlabel("relative log-RMSE gain (%)")
    ax.grid(axis="x",color=GRID,lw=.45)
    return pd.DataFrame(rows)


def main() -> None:
    FIGURES.mkdir(parents=True,exist_ok=True); SOURCE_DIR.mkdir(parents=True,exist_ok=True)
    catalyst=pd.read_csv(RESULTS/"specgen_derivative_oer_figure_source_data.csv")
    predictions=pd.read_csv(RESULTS/"bamboomixer_response_transfer_external_predictions.csv")
    bootstrap=pd.read_csv(RESULTS/"bamboomixer_response_transfer_external_group_bootstrap.csv")
    summary=json.loads((RESULTS/"bamboomixer_response_transfer_summary.json").read_text(encoding="utf-8"))
    fig=plt.figure(figsize=(7.2047,5.9449))  # 183 × 151 mm
    outer=fig.add_gridspec(2,2,width_ratios=[.33,.67],height_ratios=[.48,.52],
                           left=.055,right=.985,bottom=.10,top=.94,wspace=.36,hspace=.48)
    ax_a=fig.add_subplot(outer[:,0])
    bgrid=outer[0,1].subgridspec(1,2,width_ratios=[1.15,1.0],wspace=.25)
    ax_b1=fig.add_subplot(bgrid[0,0]); ax_b2=fig.add_subplot(bgrid[0,1])
    bottom=outer[1,1].subgridspec(1,2,width_ratios=[1.05,.95],wspace=.58)
    ax_c=fig.add_subplot(bottom[0,0]); ax_d=fig.add_subplot(bottom[0,1])
    panel_a(ax_a); panel_b(ax_b1,ax_b2,catalyst)
    out=[catalyst.assign(panel_source="b"),panel_c(ax_c,predictions),panel_d(ax_d,bootstrap,summary)]
    pd.concat(out,ignore_index=True,sort=False).to_csv(SOURCE,index=False)
    fig.savefig(f"{OUT}.svg",bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.pdf",bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.png",dpi=300,bbox_inches=None,pad_inches=0)
    fig.savefig(f"{OUT}.tiff",dpi=600,bbox_inches=None,pad_inches=0,
                pil_kwargs={"compression":"tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    main()
