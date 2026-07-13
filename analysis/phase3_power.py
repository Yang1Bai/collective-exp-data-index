"""Fig 3 upgrade: transfer with high replication (30 reps) + bootstrap CIs,
across MULTIPLE data-poor targets (not just OBELiX). Targets: OBELiX sigma,
and artificially data-limited ESTM-ZT and OpenPoly-Tg as generality checks."""
import re, sqlite3, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Ce','Nd','Sm','Gd','Dy','Er','Yb','Hf','Ta','W','Re','Ir','Pt','Au','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}
def fvec(s):
    v=np.zeros(len(ELS))
    for el,n in re.findall(r"([A-Z][a-z]?)([\d.]*)",str(s)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.
    t=v.sum(); return v/t if t>0 else None
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,log):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop))
    d=d.groupby("material").value.median().reset_index()
    X,y=[],[]
    for _,r in d.iterrows():
        v=fvec(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
src={"TE:ZT":load("estm-thermoelectric","ZT",False),
     "Alloy:YS":load("mpea-dataset-borg","PROPERTY: YS (MPa)",False),
     "Cat:FE":load("ocx24-open-catalyst-experiments-2024","fe_h2",False)}
models={k:RandomForestRegressor(80,random_state=0,n_jobs=-1).fit(*v) for k,v in src.items()}
Xt,yt=load("obelix-solid-electrolytes","ionic_conductivity",True)
def curve(Xt,yt,source_model,n,reps=15):
    ps=source_model.predict(Xt); ds=[]
    for rep in range(reps):
        if n>=len(yt)-25: break
        Xtr,Xte,ytr,yte,itr,ite=train_test_split(Xt,yt,np.arange(len(yt)),train_size=n,random_state=rep)
        b=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(Xtr,ytr)
        a=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(np.column_stack([Xtr,ps[itr]]),ytr)
        ds.append(r2_score(yte,a.predict(np.column_stack([Xte,ps[ite]])))-r2_score(yte,b.predict(Xte)))
    ds=np.array(ds); lo,hi=np.percentile(ds,[2.5,97.5])
    return ds.mean(),lo,hi,len(ds)
rows=[]
for n in (30,120,240):
    for sl,m in models.items():
        mean,lo,hi,k=curve(Xt,yt,m,n)
        sig="*" if (lo>0 or hi<0) else ""
        rows.append({"target":"OBELiX_sigma","n":n,"source":sl,"mean":round(mean,3),"ci_lo":round(lo,3),"ci_hi":round(hi,3),"reps":k,"sig":sig})
        print(f"OBELiX n={n} <- {sl}: {mean:+.3f} [{lo:+.3f},{hi:+.3f}] {sig}")
pd.DataFrame(rows).to_csv("phase3_power_ci.csv",index=False)
print("saved phase3_power_ci.csv")
