import re, sqlite3, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from rdkit import Chem; from rdkit.Chem import AllChem
from rdkit import RDLogger; RDLogger.DisableLog("rdApp.*")
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Hf','Ta','W','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}
def fvec(s):
    v=np.zeros(len(ELS))
    for el,n in re.findall(r"([A-Z][a-z]?)([\d.]*)",str(s)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.
    t=v.sum(); return v/t if t>0 else None
def evec(s):
    m=Chem.MolFromSmiles(str(s))
    if not m: return None
    v=np.zeros(len(ELS))
    for a in m.GetAtoms():
        if a.GetSymbol() in EI: v[EI[a.GetSymbol()]]+=1
    t=v.sum(); return v/t if t>0 else None
def mvec(s):
    m=Chem.MolFromSmiles(str(s))
    return np.array(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=1024),float) if m else None
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,fn,log=False,cap=1200):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop)).groupby("material").value.median().reset_index()
    if len(d)>cap: d=d.sample(cap,random_state=0)
    X,y=[],[]
    for _,r in d.iterrows():
        v=fn(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
# best-case organic pair: solubility <- hydration free energy (both aqueous)
print("=== organic best-case: aqsoldb-logS <- freesolv-dGhyd ===")
for feat,fn in (("element",evec),("morgan",mvec)):
    Xt,yt=load("aqsoldb","logS",fn); Xs,ys=load("freesolv","dG_hydration",fn)
    m=RandomForestRegressor(120,random_state=0,n_jobs=-1).fit(Xs,ys)
    ps=m.predict(Xt); ds=[]
    for rep in range(12):
        Xtr,Xte,ytr,yte,itr,ite=train_test_split(Xt,yt,np.arange(len(yt)),train_size=60,random_state=rep)
        b=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(Xtr,ytr)
        a=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(np.column_stack([Xtr,ps[itr]]),ytr)
        ds.append(r2_score(yte,a.predict(np.column_stack([Xte,ps[ite]])))-r2_score(yte,b.predict(Xte)))
    ds=np.array(ds); lo,hi=np.percentile(ds,[2.5,97.5])
    print(f"  {feat}: ΔR²={ds.mean():+.3f} [{lo:+.3f},{hi:+.3f}] {'*' if lo>0 or hi<0 else ''}")
# mechanism: in the winning OBELiX augmented model, how important is the injected TE feature?
print("=== mechanism: OBELiX<-TE injected-feature importance ===")
Xt,yt=load("obelix-solid-electrolytes","ionic_conductivity",fvec,log=True)
Xs,ys=load("estm-thermoelectric","ZT",fvec)
mte=RandomForestRegressor(150,random_state=0,n_jobs=-1).fit(Xs,ys)
ps=mte.predict(Xt)
aug=RandomForestRegressor(300,random_state=0,n_jobs=-1).fit(np.column_stack([Xt,ps]),yt)
imp=aug.feature_importances_
inj=imp[-1]; rank=(imp>inj).sum()+1
top_el=sorted([(EI_inv,imp[i]) for EI_inv,i in EI.items()],key=lambda x:-x[1])[:5]
print(f"  injected TE-prediction feature: importance={inj:.3f}, rank {rank}/{len(imp)} (of {len(ELS)} elements + 1)")
print(f"  top element features: {[(e,round(v,3)) for e,v in top_el]}")
# what does the TE source model key on (shared physics)?
te_imp=sorted([(e,mte.feature_importances_[i]) for e,i in EI.items()],key=lambda x:-x[1])[:6]
print(f"  TE source model keys on: {[(e,round(v,3)) for e,v in te_imp]}")
