"""Test: does the organic-side null in Fig 4 disappear with STRUCTURAL features?
Target = data-poor molecular property; sources = other molecular datasets.
Compare transfer under element-composition vs Morgan fingerprints."""
import re, sqlite3, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import RDLogger; RDLogger.DisableLog("rdApp.*")
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
ELS=['H','Li','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Br','I']
EI={e:i for i,e in enumerate(ELS)}
def evec(s):
    v=np.zeros(len(ELS)); m=Chem.MolFromSmiles(str(s))
    if not m: return None
    for a in m.GetAtoms():
        if a.GetSymbol() in EI: v[EI[a.GetSymbol()]]+=1
    t=v.sum(); return v/t if t>0 else None
def mvec(s):
    m=Chem.MolFromSmiles(str(s))
    if not m: return None
    return np.array(AllChem.GetMorganFingerprintAsBitVect(m,2,nBits=1024),dtype=float)
con=sqlite3.connect("/tmp/collective.sqlite")
def load(ds,prop,featfn,log=False,cap=1500):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop))
    d=d.groupby("material").value.median().reset_index()
    if len(d)>cap: d=d.sample(cap,random_state=0)
    X,y=[],[]
    for _,r in d.iterrows():
        v=featfn(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
def transfer(Xt,yt,srcmodel,n,reps=12):
    ps=srcmodel.predict(Xt); ds=[]
    for rep in range(reps):
        Xtr,Xte,ytr,yte,itr,ite=train_test_split(Xt,yt,np.arange(len(yt)),train_size=n,random_state=rep)
        b=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(Xtr,ytr)
        a=RandomForestRegressor(80,random_state=rep,n_jobs=-1).fit(np.column_stack([Xtr,ps[itr]]),ytr)
        ds.append(r2_score(yte,a.predict(np.column_stack([Xte,ps[ite]])))-r2_score(yte,b.predict(Xte)))
    ds=np.array(ds); return ds.mean(),*np.percentile(ds,[2.5,97.5])
# target: photoswitch lambda (data-poor, molecular); source: aqsoldb logS (big molecular)
for feat,fn in (("element-comp",evec),("morgan-FP",mvec)):
    Xt,yt=load("photoswitch-dataset","E_pi-pi*_lambda_max",fn)
    Xs,ys=load("aqsoldb","logS",fn)
    m=RandomForestRegressor(120,random_state=0,n_jobs=-1).fit(Xs,ys)
    mean,lo,hi=transfer(Xt,yt,m,60)
    sig="*" if (lo>0 or hi<0) else ""
    print(f"{feat:13s}: photoswitch-lambda <- aqsoldb-logS  ΔR²={mean:+.3f} [{lo:+.3f},{hi:+.3f}] {sig}  (Nt={len(yt)},Ns={len(ys)})")
