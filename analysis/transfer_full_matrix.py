"""Fig 4 data: pairwise cross-domain transfer matrix over a shared element-
composition feature space (works for both formulas and SMILES), spanning
inorganic and organic domains. Cell[T,S] = mean ΔR2 when source S's prediction
is injected as a feature for data-poor target T (n=60, 5 reps)."""
import re, sqlite3, numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
ELS=['H','Li','Be','B','C','N','O','F','Na','Mg','Al','Si','P','S','Cl','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Rb','Sr','Y','Zr','Nb','Mo','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Cs','Ba','La','Ce','Nd','Sm','Gd','Dy','Er','Yb','Hf','Ta','W','Re','Ir','Pt','Au','Pb','Bi']
EI={e:i for i,e in enumerate(ELS)}
TWO=set(e for e in ELS if len(e)==2)
def fvec(s):
    v=np.zeros(len(ELS))
    for el,n in re.findall(r"([A-Z][a-z]?)([\d.]*)",str(s)):
        if el in EI: v[EI[el]]+=float(n) if n else 1.0
    t=v.sum(); return v/t if t>0 else None
def svec(s):
    s=str(s); v=np.zeros(len(ELS)); i=0
    while i<len(s):
        c=s[i]
        if c=='[':
            j=s.find(']',i); tok=s[i+1:j] if j>0 else ''
            m=re.match(r'\d*([A-Z][a-z]?|[cnops])',tok)
            if m:
                el=m.group(1); el=el.capitalize() if el.islower() else el
                if el in EI: v[EI[el]]+=1
            i=(j+1) if j>0 else i+1; continue
        two=s[i:i+2]
        if two in TWO and two[0].isupper() and two[1].islower():
            v[EI[two]]+=1; i+=2; continue
        if c in 'CNOPSFIBKVYWU' and c in EI: v[EI[c]]+=1
        elif c in 'cnops': v[EI[c.upper()]]+=1
        i+=1
    t=v.sum(); return v/t if t>0 else None
con=sqlite3.connect("/tmp/collective.sqlite")
TARGETS=[("estm-thermoelectric","ZT","TE:ZT",False,"f"),
 ("ocx24-open-catalyst-experiments-2024","fe_h2","Cat:FE_H2",False,"f"),
 ("mpea-dataset-borg","PROPERTY: YS (MPa)","Alloy:YS",False,"f"),
 ("obelix-solid-electrolytes","ionic_conductivity","SE:sigma",True,"f"),
 ("aqsoldb","logS","Mol:logS",False,"s"),
 ("iupac-digitized-pka","pKa(pKa1)","Mol:pKa",False,"s"),
 ("freesolv","dG_hydration","Mol:dGhyd",False,"s"),
 ("photoswitch-dataset","E_pi-pi*_lambda_max","Mol:lambda",False,"s"),
 ("openpoly-benchmark","Tg (K)","Poly:Tg",False,"s")]
def load(ds,prop,log,kind):
    d=pd.read_sql("SELECT material,value FROM measurements WHERE dataset=? AND property=? AND value>0",con,params=(ds,prop))
    d=d.groupby("material").value.median().reset_index()
    parse=fvec if kind=="f" else svec
    X,y=[],[]
    for _,r in d.iterrows():
        v=parse(r.material)
        if v is not None: X.append(v); y.append(np.log10(r.value) if log else r.value)
    return np.array(X),np.array(y)
D={lab:load(ds,pr,lg,kd) for ds,pr,lab,lg,kd in TARGETS}
for lab,(X,y) in D.items(): print(lab,len(y))
labs=[t[2] for t in TARGETS]
src_models={lab:RandomForestRegressor(60,random_state=0,n_jobs=-1).fit(*D[lab]) for lab in labs if len(D[lab][1])>=40}
mat=pd.DataFrame(index=labs,columns=labs,dtype=float)
for tl in labs:
    Xt,yt=D[tl]
    if len(yt)<95: continue
    for sl in labs:
        if sl==tl or sl not in src_models: continue
        ps=src_models[sl].predict(Xt); ds=[]
        for rep in range(4):
            Xtr,Xte,ytr,yte,itr,ite=train_test_split(Xt,yt,np.arange(len(yt)),train_size=60,random_state=rep)
            b=RandomForestRegressor(60,random_state=0,n_jobs=-1).fit(Xtr,ytr); r2b=r2_score(yte,b.predict(Xte))
            a=RandomForestRegressor(60,random_state=0,n_jobs=-1).fit(np.column_stack([Xtr,ps[itr]]),ytr)
            ds.append(r2_score(yte,a.predict(np.column_stack([Xte,ps[ite]])))-r2b)
        mat.loc[tl,sl]=np.mean(ds)
mat.to_csv("transfer_full_matrix.csv")
print("\nΔR2 matrix (rows=target, cols=source):"); print(mat.round(3).to_string())
