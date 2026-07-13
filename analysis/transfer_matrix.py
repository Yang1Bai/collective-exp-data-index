"""Phase 2: cross-domain knowledge transfer test.
Target = OBELiX ionic conductivity (data-poor). Sources = ESTM ZT,
MPEA yield-related, OCx24 fe_h2. Method: stacked feature injection -
source-trained RF's prediction on target compositions becomes an extra
feature; measure few-shot R2 vs element-only baseline."""
import os, re, sqlite3, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
rng = np.random.RandomState(0)
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Ce','Nd','Sm','Gd','Dy','Er','Yb','Hf','Ta','W','Re','Ir','Pt','Au','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}
FRE=re.compile(r"([A-Z][a-z]?)([\d.]*)")
def vec(f):
    v=np.zeros(len(ELS))
    for el,n in FRE.findall(str(f)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.0
    s=v.sum(); return v/s if s>0 else None
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,log=False):
    d=pd.read_sql(f"SELECT material,value FROM measurements WHERE dataset='{ds}' AND property='{prop}' AND value>0",con)
    d=d.groupby("material").value.median().reset_index()
    X,y=[],[]
    for _,r in d.iterrows():
        v=vec(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
Xt,yt=load("obelix-solid-electrolytes","ionic_conductivity",log=True)
print("target OBELiX:",len(yt))
sources={"ESTM_ZT":load("estm-thermoelectric","ZT"),
         "MPEA_hardness":load("mpea-dataset-borg","HV"),
         "OCx24_feh2":load("ocx24-open-catalyst-experiments-2024","fe_h2")}
src_models={}
for name,(Xs,ys) in sources.items():
    if len(ys)<50: print("skip",name,len(ys)); continue
    m=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(Xs,ys)
    src_models[name]=m
    print("source",name,len(ys))
res=[]
for n in (30,60,120,240):
    for rep in range(8):
        Xtr,Xte,ytr,yte=train_test_split(Xt,yt,train_size=n,random_state=rep)
        base=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(Xtr,ytr)
        r2b=r2_score(yte,base.predict(Xte))
        for name,m in src_models.items():
            ftr=np.column_stack([Xtr,m.predict(Xtr)]); fte=np.column_stack([Xte,m.predict(Xte)])
            aug=RandomForestRegressor(200,random_state=0,n_jobs=-1).fit(ftr,ytr)
            res.append({"n":n,"source":name,"delta_r2":r2_score(yte,aug.predict(fte))-r2b,"base_r2":r2b})
r=pd.DataFrame(res)
summ=r.groupby(["n","source"]).agg(mean_delta=("delta_r2","mean"),se=("delta_r2",lambda x:x.std()/np.sqrt(len(x))),base=("base_r2","mean")).round(3)
print(summ.to_string())
r.to_csv("transfer_obelix_results.csv",index=False)
