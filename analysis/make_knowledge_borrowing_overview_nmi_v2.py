"""Build the NMI-style overview of falsification-gated knowledge borrowing.

The figure is deliberately schematic-led: panel a is a vector scientific
scene, whereas panels b-d report declared numerical results from the source
CSV.  The AI-generated object layer is retained only as a design record and is
not embedded in the exports.
"""

from __future__ import annotations

from pathlib import Path
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "analysis" / "figures"
DATA = FIG_DIR / "source_data" / "knowledge_borrowing_overview_nmi_v2.csv"
OUT = FIG_DIR / "knowledge_borrowing_overview_nmi_v2"


NAVY = "#173B6C"
BLUE = "#3478BD"
TEAL = "#148A82"
GREEN = "#3C9662"
ORANGE = "#E8872E"
CORAL = "#C95A50"
INK = "#243143"
MID = "#7E8998"
GRID = "#D8DEE8"
PALE = "#F5F8FB"
LIGHT_BLUE = "#DCEAF6"
LIGHT_TEAL = "#DDF1EE"
LIGHT_ORANGE = "#FCEBD7"


mpl.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 7.2,
        "axes.titlesize": 8.2,
        "axes.labelsize": 7.2,
        "xtick.labelsize": 6.6,
        "ytick.labelsize": 6.6,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def add_panel_label(ax: plt.Axes, letter: str, x: float = 0.0, y: float = 1.02) -> None:
    ax.text(x, y, letter, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10, fontweight="bold", color="black")


def draw_crystal(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    """Compact perovskite-like lattice glyph."""
    nodes = []
    for i in range(3):
        for j in range(3):
            x = cx + (i - 1) * s * 0.34 + (j - 1) * s * 0.07
            y = cy + (j - 1) * s * 0.30
            nodes.append((x, y))
    for i, (x1, y1) in enumerate(nodes):
        for x2, y2 in nodes[i + 1 :]:
            d = math.hypot(x2 - x1, y2 - y1)
            if d < s * 0.39:
                ax.plot([x1, x2], [y1, y2], color="#9CB7CC", lw=0.55, zorder=1)
    for k, (x, y) in enumerate(nodes):
        ax.add_patch(Circle((x, y), s * (0.055 if k % 2 else 0.070),
                            facecolor=BLUE if k % 2 else NAVY, edgecolor="white",
                            lw=0.35, zorder=2))
    for x, y in [(cx - 0.10*s, cy + 0.10*s), (cx + 0.16*s, cy - 0.10*s)]:
        ax.add_patch(Circle((x, y), s * 0.075, facecolor="#A66CCB",
                            edgecolor="white", lw=0.35, zorder=3))


def draw_catalyst(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    ax.add_patch(Polygon([(cx - .48*s, cy - .20*s), (cx + .48*s, cy - .20*s),
                          (cx + .40*s, cy - .34*s), (cx - .40*s, cy - .34*s)],
                         closed=True, facecolor="#C9D1D9", edgecolor="#77828D", lw=0.5))
    for row in range(3):
        for col in range(7):
            x = cx + (col - 3) * .115*s + (row % 2) * .045*s
            y = cy - .12*s + row * .09*s + .006*s*math.sin(2.1*col + row)
            colr = ORANGE if (row + col) % 4 == 0 else NAVY
            ax.add_patch(Circle((x, y), .045*s, facecolor=colr,
                                edgecolor="white", lw=.25, zorder=3))
    for dx, dy, rr in [(-.24, .28, .09), (.03, .39, .12), (.31, .24, .075)]:
        ax.add_patch(Circle((cx+dx*s, cy+dy*s), rr*s, facecolor="none",
                            edgecolor="#8AB9D7", lw=.7, alpha=.9))


def draw_flask(ax: plt.Axes, cx: float, cy: float, s: float) -> None:
    verts = [
        (cx-.13*s, cy+.42*s), (cx-.13*s, cy+.14*s), (cx-.42*s, cy-.35*s),
        (cx-.36*s, cy-.48*s), (cx+.36*s, cy-.48*s), (cx+.42*s, cy-.35*s),
        (cx+.13*s, cy+.14*s), (cx+.13*s, cy+.42*s),
    ]
    codes = [MplPath.MOVETO, MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3,
             MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3, MplPath.LINETO]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor="#EEF6FB",
                           edgecolor="#769AB5", lw=.7))
    ax.plot([cx-.15*s, cx+.15*s], [cy+.42*s, cy+.42*s], color="#769AB5", lw=.8)
    ax.add_patch(Ellipse((cx, cy-.29*s), .66*s, .25*s,
                         facecolor="#D9EDF5", edgecolor="none", alpha=.95))
    pts = [(-.22,-.22,NAVY), (-.05,-.33,CORAL), (.17,-.23,ORANGE),
           (.24,-.37,"#7B66B0"), (.02,-.18,GREEN)]
    for dx, dy, c in pts:
        ax.add_patch(Circle((cx+dx*s, cy+dy*s), .055*s, facecolor=c,
                            edgecolor="white", lw=.3, zorder=3))
    for (a, b) in [(0,1),(1,2),(2,3),(1,4)]:
        x1,y1,_=pts[a]; x2,y2,_=pts[b]
        ax.plot([cx+x1*s,cx+x2*s],[cy+y1*s,cy+y2*s],color="#77838E",lw=.55,zorder=2)


def draw_records(ax: plt.Axes, x: float, y: float, w: float, h: float, seed: int) -> None:
    """Tiny abstract measurement records; intentionally non-quantitative."""
    for r in range(3):
        for c in range(4):
            xx = x + c*w*0.26
            yy = y + (2-r)*h*0.34
            ax.add_patch(Rectangle((xx, yy), w*.21, h*.27, facecolor="white",
                                   edgecolor="#B8C5D3", lw=.35))
            xs = np.linspace(xx+w*.03, xx+w*.18, 5)
            phase = seed*0.7 + r*0.9 + c*1.3
            vals = yy+h*.115 + h*.052*np.sin(np.linspace(phase, phase+4.1, 5))
            ax.plot(xs, vals, color=BLUE, lw=.45, alpha=.8, clip_on=False)


def draw_gate(ax: plt.Axes, x: float, y: float, w: float, label: str, icon: str) -> None:
    ax.add_patch(Ellipse((x, y), w, .58, facecolor="white", edgecolor="#B6C1CE", lw=.8))
    ax.add_patch(Ellipse((x, y), w*.72, .44, facecolor=PALE, edgecolor="#E1E6EC", lw=.45))
    if icon == "repr":
        pts = [(x-.018,y+.08),(x+.020,y+.10),(x-.028,y-.05),(x+.028,y-.06),(x,y+.01)]
        for px,py in pts:
            ax.add_patch(Circle((px,py),.010,facecolor=TEAL,edgecolor="white",lw=.25,zorder=4))
        for a,b in [(0,4),(1,4),(2,4),(3,4)]:
            ax.plot([pts[a][0],pts[b][0]],[pts[a][1],pts[b][1]],color="#8094A6",lw=.45)
    elif icon == "state":
        ax.add_patch(Rectangle((x-.018,y-.07),.036,.14,facecolor=LIGHT_BLUE,edgecolor=NAVY,lw=.55))
        ax.add_patch(Circle((x,y-.075),.026,facecolor=BLUE,edgecolor=NAVY,lw=.4))
        ax.plot([x,x],[y-.04,y+.05],color=BLUE,lw=1.1)
        ax.add_patch(Circle((x+.035,y+.09),.018,facecolor=ORANGE,edgecolor="white",lw=.25))
    elif icon == "relation":
        pts=[(x-.035,y+.065),(x+.025,y+.085),(x-.020,y-.065),(x+.040,y-.045)]
        for a,b in [(0,1),(0,2),(1,3),(2,3)]:
            ax.plot([pts[a][0],pts[b][0]],[pts[a][1],pts[b][1]],color="#728596",lw=.6)
        for k,(px,py) in enumerate(pts):
            ax.add_patch(Circle((px,py),.014,facecolor=TEAL if k in (0,3) else "white",edgecolor=NAVY,lw=.55))
    else:
        ax.plot([x-.038,x-.027,x-.008],[y+.048,y+.025,y+.082],color=GREEN,lw=1.15,
                solid_capstyle="round")
        ax.text(x+.022,y-.055,"×",ha="center",va="center",fontsize=8,color=CORAL,fontweight="bold")
        ax.plot([x,x],[y-.12,y+.12],color="#BAC4CE",lw=.55,ls=(0,(2,2)))
    ax.text(x, y-.355, label, ha="center", va="top", fontsize=6.2, color=INK)


def draw_recipient_landscape(ax: plt.Axes) -> None:
    x0, x1 = .735, .995
    y0, y1 = .09, .88
    xx = np.linspace(x0, x1, 120)
    yy = np.linspace(y0, y1, 120)
    X, Y = np.meshgrid(xx, yy)
    Z = np.exp(-(((X-.855)/.075)**2 + ((Y-.50)/.22)**2))
    Z += .50*np.exp(-(((X-.93)/.050)**2 + ((Y-.29)/.15)**2))
    ax.contourf(X, Y, Z, levels=[.08,.18,.32,.50,.72,1.5],
                colors=["#F7FBFC", "#EAF5F3", "#DDF0EE", "#DDEBF5", "#C8DDF0"],
                alpha=.95, zorder=0)
    ax.contour(X, Y, Z, levels=[.20,.40,.60,.80], colors=["#BFDCD6", "#8FC7BE", "#8EB8D4", "#6F9FC4"],
               linewidths=.45, alpha=.9, zorder=1)
    t = np.linspace(0, 2*np.pi, 160)
    r = 1 + .06*np.sin(5*t) + .04*np.cos(3*t)
    bx = .865 + .137*r*np.cos(t)
    by = .49 + .395*r*np.sin(t)
    ax.plot(bx, by, color="#89939E", lw=.65, ls=(0,(3,2)), zorder=2)
    measured = np.array([[.835,.52],[.865,.58],[.889,.49],[.847,.42],[.905,.62],[.910,.37]])
    ood = np.array([[.755,.63],[.780,.78],[.826,.83],[.884,.78],[.947,.72],[.975,.55],
                    [.964,.32],[.927,.18],[.875,.12],[.805,.18],[.758,.33],[.810,.66]])
    for x,y in measured:
        ax.add_patch(Rectangle((x-.008,y-.018),.016,.036,facecolor=BLUE,edgecolor=NAVY,lw=.45,zorder=5))
    for x,y in ood:
        ax.add_patch(Rectangle((x-.008,y-.018),.016,.036,facecolor="white",edgecolor=ORANGE,lw=.75,zorder=5))
    for i in range(len(ood)-1):
        ax.plot([ood[i,0],ood[i+1,0]],[ood[i,1],ood[i+1,1]],color="#F1C99A",lw=.35,ls=(0,(2,2)),zorder=3)
    verts=[(.64,.50),(.70,.50),(.76,.47),(.82,.43),(.87,.41),(.92,.38),(.995,.29)]
    codes=[MplPath.MOVETO]+[MplPath.CURVE4]*6
    ax.add_patch(PathPatch(MplPath(verts,codes),facecolor="none",edgecolor=TEAL,lw=2.4,alpha=.88,zorder=4))
    ax.text(.855,.905,"measured",ha="right",va="bottom",fontsize=6.3,color=BLUE)
    ax.text(.872,.905,"OOD candidates",ha="left",va="bottom",fontsize=6.3,color=ORANGE)


def panel_a(ax: plt.Axes) -> None:
    ax.set(xlim=(0,1), ylim=(0,1))
    ax.axis("off")
    add_panel_label(ax, "a", 0.0, 1.00)
    ax.text(.075, 1.025, "Neighbouring experimental programmes", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.2, color=INK, fontweight="bold")
    ax.text(.445, 1.025, "Only a qualified relation crosses", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.2, color=INK, fontweight="bold")
    ax.text(.790, 1.025, "Sparse OOD recipient", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8.2, color=INK, fontweight="bold")

    # Three experimental object classes and their measurement records.
    draw_crystal(ax, .065, .78, .18)
    draw_catalyst(ax, .065, .49, .18)
    draw_flask(ax, .065, .18, .18)
    draw_records(ax, .145, .70, .13, .16, 1)
    draw_records(ax, .145, .41, .13, .16, 2)
    draw_records(ax, .145, .12, .13, .16, 3)
    ax.text(.065,.655,"solid transport",ha="center",va="top",fontsize=6.1,color=MID)
    ax.text(.065,.365,"catalysis",ha="center",va="top",fontsize=6.1,color=MID)
    ax.text(.065,.055,"molecular mixtures",ha="center",va="top",fontsize=6.1,color=MID)

    # Candidate edges: most are rejected; one remains coherent.
    for y0 in [.22,.36,.50,.64,.78]:
        verts=[(.270,y0),(.34,y0+.02),(.38,.49),(.42,.50)]
        ax.add_patch(PathPatch(MplPath(verts,[MplPath.MOVETO]+[MplPath.CURVE4]*3),
                               facecolor="none",edgecolor="#CFD6DE",lw=.55,alpha=.65,zorder=0))
    for y0 in [.30,.70]:
        verts=[(.270,y0),(.36,y0),(.44,y0-.08),(.52,.24)]
        ax.add_patch(PathPatch(MplPath(verts,[MplPath.MOVETO]+[MplPath.CURVE4]*3),
                               facecolor="none",edgecolor=CORAL,lw=.55,alpha=.32,zorder=0))
    ax.add_patch(FancyArrowPatch((.270,.49),(.735,.49),arrowstyle="-|>",mutation_scale=8,
                                 color=TEAL,lw=2.1,alpha=.9,zorder=2))
    ax.text(.315,.525,"candidate edges",ha="left",va="bottom",fontsize=6.2,color=MID)

    gates=[(.405,"representation","repr"),(.485,"state","state"),(.565,"relation","relation"),(.645,"falsification","test")]
    for x,label,icon in gates:
        draw_gate(ax,x,.49,.070,label,icon)
    ax.text(.52,.76,"shared inputs  ·  matched state  ·  falsifiable physics",ha="center",va="center",fontsize=6.4,color=TEAL)
    ax.text(.665,.435,"qualified prior",ha="left",va="top",fontsize=6.3,color=TEAL,fontweight="bold")
    ax.add_patch(FancyArrowPatch((.61,.24),(.70,.06),arrowstyle="-|>",mutation_scale=7,
                                 color=CORAL,lw=.9,ls=(0,(4,3)),alpha=.75))
    ax.text(.695,.055,"abstain",ha="center",va="center",fontsize=6.2,color=CORAL)
    draw_recipient_landscape(ax)


def panel_b(ax: plt.Axes) -> None:
    add_panel_label(ax, "b", -0.02, 1.02)
    ax.text(.10,1.025,"Generic feature injection",transform=ax.transAxes,ha="left",va="bottom",
            fontsize=8.2,color=INK,fontweight="bold")
    ax.set_xlim(-.5, 7.5); ax.set_ylim(-1.0, 8.2); ax.axis("off")
    for r in range(8):
        for c in range(5):
            ax.add_patch(Circle((c,7-r),.25,facecolor="#F1F3F6",edgecolor="#C8CED6",lw=.45))
            ax.text(c,7-r,"×",ha="center",va="center",fontsize=5.8,color="#9DA5AF")
    ax.text(7.35,5.6,"0/40",ha="right",va="center",fontsize=15,color=NAVY,fontweight="bold")
    ax.text(7.35,4.35,"complete OOD\ngates passed",ha="right",va="top",fontsize=6.4,color=INK,linespacing=1.2)
    ax.text(0,-.65,"8 recipients × 5 real donor edges",ha="left",va="center",fontsize=6.2,color=MID)


def panel_c(ax: plt.Axes, data: pd.DataFrame) -> None:
    add_panel_label(ax, "c", -0.02, 1.02)
    ax.text(.10,1.025,"Endpoint routing is selective",transform=ax.transAxes,ha="left",va="bottom",
            fontsize=8.2,color=INK,fontweight="bold")
    labels=["Catalyst 1","Catalyst 2","External salt","Rank only","Reject"]
    rows=data[data.section.eq("prediction")].reset_index(drop=True)
    y=np.arange(4,-1,-1)
    colors=[GREEN,GREEN,TEAL,BLUE,CORAL]
    for yi,(_,row),color in zip(y,rows.iterrows(),colors):
        ax.plot([row.ci_low,row.ci_high],[yi,yi],color=color,lw=1.7,solid_capstyle="round")
        ax.scatter([row.estimate],[yi],s=27,color=color,edgecolor="white",lw=.6,zorder=4)
        ax.text(row.estimate,yi+.23,f"{row.estimate:g}%",ha="center",va="bottom",fontsize=5.7,color=color)
    ax.axvline(0,color="#AAB2BC",lw=.65,ls=(0,(3,2)))
    ax.set_yticks(y,labels)
    ax.set_xlim(-22,36); ax.set_ylim(-.65,4.65)
    ax.set_xlabel("Relative RMSE reduction (%)", labelpad=2)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.spines["bottom"].set_color("#9DA6B0")
    ax.tick_params(axis="y",length=0,pad=2)
    ax.tick_params(axis="x",length=2,color="#9DA6B0")
    ax.grid(axis="x",color="#EEF1F4",lw=.5,zorder=0)
    for yi,route,color in zip(y,["predict","predict","predict","rank","abstain"],colors):
        ax.text(35.2,yi,route,ha="right",va="center",fontsize=5.8,color=color,fontweight="bold")


def panel_d(ax: plt.Axes, data: pd.DataFrame) -> None:
    add_panel_label(ax, "d", -0.02, 1.02)
    ax.text(.11,1.025,"Screen, or abstain",transform=ax.transAxes,ha="left",va="bottom",
            fontsize=8.2,color=INK,fontweight="bold")
    vals=[.537,.910,.694,.783]
    xs=[0,1,2.35,3.35]
    ax.plot(xs[:2],vals[:2],color=TEAL,lw=1.6,zorder=1)
    ax.scatter(xs[:2],vals[:2],s=[28,38],color=["#B9C4D0",TEAL],edgecolor="white",lw=.6,zorder=3)
    ax.plot(xs[2:],vals[2:],color=CORAL,lw=1.3,zorder=1)
    ax.scatter(xs[2:],vals[2:],s=[34,28],color=[CORAL,"#B9C4D0"],edgecolor="white",lw=.6,zorder=3)
    placements=[(.537,.026),(.910,-.050),(.694,.026),(.783,.026)]
    for x,v,t,c,(_,dy) in zip(xs,vals,["0.537","0.910","0.694","0.783"],[MID,TEAL,CORAL,MID],placements):
        ax.text(x,v+dy,t,ha="center",va="bottom" if dy>0 else "top",fontsize=6.3,color=c,fontweight="bold")
    ax.text(.5,.995,"accepted screening",ha="center",va="top",fontsize=6.0,color=TEAL,fontweight="bold")
    ax.text(.5,.815,"Δρ = +0.374",ha="center",va="top",fontsize=6.6,color=TEAL)
    ax.text(2.85,.995,"frozen recipient",ha="center",va="top",fontsize=6.0,color=CORAL,fontweight="bold")
    ax.text(2.85,.61,"donor loses",ha="center",va="top",fontsize=6.3,color=CORAL)
    ax.set_xticks(xs,["5-label\ntarget","source\nscore","donor","3-label\ntarget"])
    ax.set_xlim(-.45,3.8); ax.set_ylim(.43,1.0)
    ax.set_ylabel("Ordering score",labelpad=2)
    ax.set_yticks([.5,.7,.9])
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#9DA6B0")
    ax.tick_params(axis="x",length=0,pad=3)
    ax.tick_params(axis="y",length=2,color="#9DA6B0")
    ax.grid(axis="y",color="#EEF1F4",lw=.5,zorder=0)


def build() -> None:
    data=pd.read_csv(DATA)
    fig=plt.figure(figsize=(7.15,5.05),constrained_layout=False)
    axa=fig.add_axes([.035,.455,.93,.49])
    axb=fig.add_axes([.045,.105,.225,.255])
    axc=fig.add_axes([.365,.105,.305,.255])
    axd=fig.add_axes([.755,.105,.215,.255])
    panel_a(axa)
    panel_b(axb)
    panel_c(axc,data)
    panel_d(axd,data)
    fig.add_artist(mpl.lines.Line2D([.035,.965],[.405,.405],transform=fig.transFigure,color="#D7DDE4",lw=.7))
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches=None, pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".pdf"), bbox_inches=None, pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".png"), dpi=300, bbox_inches=None, pad_inches=0.02)
    fig.savefig(OUT.with_suffix(".tiff"), dpi=600, bbox_inches=None, pad_inches=0.02,
                pil_kwargs={"compression":"tiff_lzw"})
    plt.close(fig)


if __name__ == "__main__":
    build()
