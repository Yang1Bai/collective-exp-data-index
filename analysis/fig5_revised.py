import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,3,figsize=(15,4.4))
# a) transfer curves w/ bootstrap CI
d=pd.read_csv("phase3_power_ci.csv")
col={"TE:ZT":"tab:blue","Alloy:YS":"tab:green","Cat:FE":"tab:gray"}
for src,c in col.items():
    g=d[d.source==src].sort_values("n")
    ax[0].plot(g.n,g["mean"],"o-",c=c,label=src+" (thermoelec./alloy/catal.)" if src=="TE:ZT" else src)
    ax[0].fill_between(g.n,g.ci_lo,g.ci_hi,color=c,alpha=.18)
ax[0].axhline(0,c="k",lw=.6)
ax[0].set_xlabel("n target samples (OBELiX solid electrolytes)"); ax[0].set_ylabel("ΔR² vs baseline (95% bootstrap CI)")
ax[0].set_title("a) Only thermoelectric transfer is significant\n(CI excludes 0 at n=30,120)"); ax[0].legend(fontsize=8)
# b) mechanism: feature importance
feats=["injected\nTE-pred","P","O","Li","La","Sb"]; imps=[0.254,0.195,0.130,0.125,0.066,0.023]
cols=["crimson"]+["#1565c0"]*5
ax[1].bar(feats,imps,color=cols)
ax[1].set_ylabel("RF feature importance"); ax[1].set_title("b) Borrowed knowledge is the #1 feature\nin the solid-electrolyte model (rank 1/54)")
ax[1].tick_params(labelsize=8)
# c) organic control
labs=["element\nfeatures","Morgan\nfingerprint"]; m=[0.002,-0.018]; lo=[-0.059,-0.069]; hi=[0.046,0.032]
ax[2].bar(labs,m,color="#7e57c2",yerr=[np.array(m)-np.array(lo),np.array(hi)-np.array(m)],capsize=6)
ax[2].axhline(0,c="k",lw=.6)
ax[2].set_ylabel("ΔR² (logS ← dG_hydration)"); ax[2].set_ylim(-0.1,0.1)
ax[2].set_title("c) Organic null is physical, not featurization\n(best-case aqueous pair, both ~0)")
plt.tight_layout(); plt.savefig("fig5_mechanism.png",dpi=200); print("saved fig5_mechanism.png")
