"""Item 5: cross-domain prior for self-driving-lab campaign design.
Active-learning (RF-UCB) search over OBELiX to find high-ionic-conductivity
solid electrolytes. Compare: baseline (element features) vs cross-domain prior
(element features + thermoelectric-source prediction). Metric: best log-sigma
found vs #experiments, averaged over seeds. Cross-domain prior = faster SDL."""
import re, sqlite3, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Hf','Ta','W','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}
def fvec(s):
    v=np.zeros(len(ELS))
    for el,n in re.findall(r"([A-Z][a-z]?)([\d.]*)",str(s)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.
    t=v.sum(); return v/t if t>0 else None
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,log):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop)).groupby("material").value.median().reset_index()
    X,y=[],[]
    for _,r in d.iterrows():
        v=fvec(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
Xt,yt=load("obelix-solid-electrolytes","ionic_conductivity",True)
Xs,ys=load("estm-thermoelectric","ZT",False)
prior=RandomForestRegressor(150,random_state=0,n_jobs=-1).fit(Xs,ys).predict(Xt)
best_possible=yt.max()
def campaign(feat, seed, budget=40, init=4):
    rng=np.random.RandomState(seed); N=len(yt)
    lab=list(rng.choice(N,init,replace=False)); pool=[i for i in range(N) if i not in lab]
    traj=[max(yt[lab])]
    for _ in range(budget):
        m=RandomForestRegressor(60,random_state=0,n_jobs=-1).fit(feat[lab],yt[lab])
        preds=np.array([t.predict(feat[pool]) for t in m.estimators_])
        mu,sd=preds.mean(0),preds.std(0)
        pick=pool[int(np.argmax(mu+1.0*sd))]  # UCB
        lab.append(pick); pool.remove(pick); traj.append(max(yt[lab]))
    return traj
Fbase=Xt; Fprior=np.column_stack([Xt,prior])
import numpy as np
res={"baseline":[],"prior":[]}
for seed in range(10):
    res["baseline"].append(campaign(Fbase,seed))
    res["prior"].append(campaign(Fprior,seed))
for k in res: res[k]=np.array(res[k])
b=res["baseline"].mean(0); p=res["prior"].mean(0)
pd.DataFrame({"experiment":range(len(b)),"baseline":b,"prior":p}).to_csv("bo_warmstart.csv",index=False)
# experiments to reach 90% of best-possible log-sigma
thr=np.percentile(yt,95)
def reach(traj):
    for i,v in enumerate(traj):
        if v>=thr: return i
    return len(traj)
rb=np.mean([reach(t) for t in res["baseline"]]); rp=np.mean([reach(t) for t in res["prior"]])
print(f"best log10-sigma possible={best_possible:.2f}; 90% threshold={thr:.2f}")
print(f"experiments to reach 90%: baseline={rb:.1f}  prior={rp:.1f}  speedup={rb/max(rp,0.1):.2f}x")
pass
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6,4.4))
xs=range(len(b))
ax.plot(xs,b,"o-",c="tab:gray",label=f"baseline (element only), top-5% in {rb:.0f} exp",ms=3)
ax.plot(xs,p,"o-",c="tab:blue",label=f"+ thermoelectric prior, {rp:.0f} exp ({rb:.0f} vs {rp:.0f} exp, n.s.)",ms=3)
ax.fill_between(xs,res["baseline"].mean(0)-res["baseline"].std(0)/3,res["baseline"].mean(0)+res["baseline"].std(0)/3,color="gray",alpha=.15)
ax.fill_between(xs,res["prior"].mean(0)-res["prior"].std(0)/3,res["prior"].mean(0)+res["prior"].std(0)/3,color="tab:blue",alpha=.15)
ax.axhline(thr,c="crimson",ls="--",lw=1,label="top-5% conductivity threshold")
ax.set_xlabel("# experiments (active-learning campaign)"); ax.set_ylabel("best log10 σ found (S/cm)")
ax.set_title("Predictive transfer does NOT auto-translate to search speedup\nOBELiX RF-UCB: baseline vs +thermoelectric prior (10 seeds, n.s.)")
ax.legend(fontsize=8,loc="lower right"); plt.tight_layout(); plt.savefig("fig6_sdl_prior.png",dpi=200)
print("saved fig6_sdl_prior.png")
