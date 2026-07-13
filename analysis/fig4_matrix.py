import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
m=pd.read_csv("transfer_full_matrix.csv",index_col=0)
labs=list(m.index)
A=m.values.astype(float)
fig,ax=plt.subplots(figsize=(7.2,6))
vmax=0.09
im=ax.imshow(A,cmap="RdBu_r",vmin=-vmax,vmax=vmax)
ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs,rotation=45,ha="right",fontsize=8)
ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs,fontsize=8)
for i in range(len(labs)):
    for j in range(len(labs)):
        v=A[i,j]
        if not np.isnan(v):
            ax.text(j,i,f"{v:+.02f}",ha="center",va="center",fontsize=7,
                    color="white" if abs(v)>0.05 else "black")
        else:
            ax.text(j,i,"—",ha="center",va="center",color="#bbb")
ax.set_xlabel("SOURCE domain (knowledge lent)"); ax.set_ylabel("TARGET domain (data-poor, n=60)")
ax.set_title("Cross-domain knowledge-borrowing map\nΔR² from injecting source prediction (element-composition space)")
# highlight the hot cell
ti=labs.index("SE:sigma"); si=labs.index("TE:ZT")
ax.add_patch(plt.Rectangle((si-.5,ti-.5),1,1,fill=False,edgecolor="lime",lw=2.5))
plt.colorbar(im,label="ΔR² vs baseline",fraction=.046,pad=.04)
plt.tight_layout(); plt.savefig("fig4_transfer_matrix.png",dpi=200); print("saved fig4_transfer_matrix.png")
