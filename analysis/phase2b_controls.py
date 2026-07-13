"""Phase 2b: rigor controls for the transfer result.
(a) leakage audit + dedup; (b) placebo (shuffled source feature);
(c) chemistry-vs-physics: chalcogenide vs non-chalcogenide target subsets;
(d) MPEA source with corrected column."""
import re, sqlite3, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
rng=np.random.RandomState(0)
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Ce','Nd','Sm','Gd','Dy','Er','Yb','Hf','Ta','W','Re','Ir','Pt','Au','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}; FRE=re.compile(r"([A-Z][a-z]?)([\d.]*)")
def norm(f):
    els={}
    for el,n in FRE.findall(str(f)):
        if el in EI: els[el]=els.get(el,0)+(float(n) if n else 1.)
    t=sum(els.values()) or 1
    return tuple(sorted((e,round(v/t,3)) for e,v in els.items()))
def vec(f):
    v=np.zeros(len(ELS))
    for el,n in FRE.findall(str(f)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.
    s=v.sum(); return v/s if s>0 else None
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,log=False):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop))
    d=d.groupby("material").value.median().reset_index()
    return d
tgt=load("obelix-solid-electrolytes","ionic_conductivity")
src=load("estm-thermoelectric","ZT")
# (a) leakage audit
tn=set(tgt.material.map(norm)); sn=set(src.material.map(norm))
overlap=tn&sn
print(f"LEAKAGE: {len(overlap)} identical normalized compositions shared (of {len(tn)} target)")
tgt=tgt[~tgt.material.map(norm).isin(overlap)]
def XY(d,log):
    X,y=[],[]
    for _,r in d.iterrows():
        v=vec(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
Xt,yt=XY(tgt,True); Xs,ys=XY(src,False)
mS=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(Xs,ys)
mp=load("mpea-dataset-borg","PROPERTY: YS (MPa)")
Xm,ym=XY(mp,False)
mM=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(Xm,ym)
chal=np.array([Xt[:,EI[e]].astype(bool) for e in("S","Se","Te")]).any(0)
print(f"target after dedup: {len(yt)} (chalcogenide-containing: {chal.sum()})")
def run(X,y,extra_fn,n,reps=10):
    ds=[]
    for rep in range(reps):
        if n>=len(y)-30: break
        Xtr,Xte,ytr,yte,itr,ite=train_test_split(X,y,np.arange(len(y)),train_size=n,random_state=rep)
        b=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(Xtr,ytr)
        r2b=r2_score(yte,b.predict(Xte))
        ftr,fte=extra_fn(Xtr,itr),extra_fn(Xte,ite)
        a=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(np.column_stack([Xtr,ftr]),ytr)
        ds.append(r2_score(yte,a.predict(np.column_stack([Xte,fte])))-r2b)
    return np.mean(ds),np.std(ds)/np.sqrt(len(ds))
pred_all=mS.predict(Xt); sh=pred_all.copy(); rng.shuffle(sh)
pm=mM.predict(Xt)
for n in (60,120):
    real=run(Xt,yt,lambda Xp,i:pred_all[i],n)
    plac=run(Xt,yt,lambda Xp,i:sh[i],n)
    mpea=run(Xt,yt,lambda Xp,i:pm[i],n)
    print(f"n={n}: ESTM real {real[0]:+.3f}±{real[1]:.3f} | placebo {plac[0]:+.3f}±{plac[1]:.3f} | MPEA_YS {mpea[0]:+.3f}±{mpea[1]:.3f}")
# (c) chemistry split at n=60
for lbl,mask in (("chalcogenide",chal),("non-chalcogenide",~chal)):
    Xc,yc=Xt[mask],yt[mask]; pc=mS.predict(Xc)
    if len(yc)>100:
        r=run(Xc,yc,lambda Xp,i:pc[i],60)
        print(f"subset {lbl} (n_total={len(yc)}): ESTM transfer {r[0]:+.3f}±{r[1]:.3f}")
    else: print(f"subset {lbl}: too small ({len(yc)})")
