import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,3,figsize=(15,4.2))
# P1: family compensation
f=pd.read_csv("mn_estm_arrhenius.csv")
import re
FRE=re.compile(r"([A-Z][a-z]?)([\d.]*)")
def fam(s):
    els={}
    for el,n in FRE.findall(str(s)): els[el]=els.get(el,0)+(float(n) if n else 1)
    t=sum(els.values()) or 1
    return "-".join(sorted([e for e,v in els.items() if v/t>=.15])[:3])
f["fam"]=f.material.map(fam)
top={"Ag-Se":"tab:blue","Ag-Bi-Se":"tab:orange","Co-Li-O":"tab:green"}
ax[0].scatter(f.Ea_eV,f.lnA,c="lightgray",s=18,label="all (pooled R²=0.05)")
for k,c in top.items():
    g=f[f.fam==k]; ax[0].scatter(g.Ea_eV,g.lnA,c=c,s=30,label=f"{k} (R²={np.corrcoef(g.Ea_eV,g.lnA)[0,1]**2:.2f})")
    s,i=np.polyfit(g.Ea_eV,g.lnA,1); xx=np.linspace(g.Ea_eV.min(),g.Ea_eV.max(),9); ax[0].plot(xx,i+s*xx,c=c,lw=1)
ax[0].set_xlabel("Ea (eV)"); ax[0].set_ylabel("ln A"); ax[0].legend(fontsize=7)
ax[0].set_title("a) Meyer-Neldel: family-scoped, not domain-wide")
# P2: ISODB artifact
h=pd.read_csv("hs_isodb_vanthoff.csv")
ax[1].scatter(h.dH_slope,h.lnA,s=22,c="tab:red")
s,i=np.polyfit(h.dH_slope,h.lnA,1); xx=np.linspace(h.dH_slope.min(),h.dH_slope.max(),9)
ax[1].plot(xx,i+s*xx,"k--",lw=1)
ax[1].set_xlabel("van't Hoff slope (K)"); ax[1].set_ylabel("ln A")
ax[1].set_title("b) Adsorption H-S 'compensation' R²=0.89\nKrug: T_iso=303K ≈ T_hm=305K → ARTIFACT")
# P3: transfer learning curves
r=pd.read_csv("transfer_obelix_results.csv")
for src,c in (("ESTM_ZT","tab:blue"),("OCx24_feh2","tab:gray")):
    g=r[r.source==src].groupby("n").delta_r2.agg(["mean","sem"])
    ax[2].errorbar(g.index,g["mean"],yerr=g["sem"],marker="o",c=c,label=src)
ax[2].errorbar([60,120],[-0.036,-0.020],yerr=[0.011,0.005],marker="s",c="tab:red",ls=":",label="placebo (shuffled)")
ax[2].errorbar([60,120],[0.018,0.008],yerr=[0.007,0.008],marker="^",c="tab:green",ls=":",label="MPEA_YS")
ax[2].axhline(0,c="k",lw=.5)
ax[2].set_xlabel("n target samples (OBELiX)"); ax[2].set_ylabel("ΔR² vs element-only baseline")
ax[2].set_title("c) Selective cross-domain transfer + controls"); ax[2].legend(fontsize=7)
plt.tight_layout(); plt.savefig("fig_main.png",dpi=200)
print("saved fig_main.png")
