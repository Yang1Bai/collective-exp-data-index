import json, math, re, glob
import numpy as np
import pandas as pd

ELEMS = ['H','He','Li','Be','B','C','N','O','F','Ne','Na','Mg','Al','Si','P','S','Cl','Ar','K','Ca','Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn','Ga','Ge','As','Se','Br','Kr','Rb','Sr','Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd','In','Sn','Sb','Te','I','Xe','Cs','Ba','La','Ce','Pr','Nd','Pm','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm','Yb','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi']
EIDX = {e:i for i,e in enumerate(ELEMS)}
FRE = re.compile(r'([A-Z][a-z]?)(\d*\.?\d*)')

def formula_vec(f):
    v = np.zeros(len(ELEMS))
    for el,n in FRE.findall(str(f)):
        if el in EIDX:
            v[EIDX[el]] += float(n) if n else 1.0
    s = v.sum()
    return v/s if s>0 else None

SM_TWO = ['Cl','Br','Si','Se','Na','Li','Mg','Ca','Fe','Zn','Cu','Mn','Al','Sn','Pb','Ag','Au','Pt','Pd','Ni','Co','Cr','Ti','Hg','Cd','Ba','Sr','Sb','Bi','As','B']
def smiles_vec(s):
    v = np.zeros(len(ELEMS)); s = str(s)
    i=0
    while i < len(s):
        c=s[i]
        if c=='[':  # bracket atom
            j=s.find(']',i)
            m=re.match(r'\[\d*([A-Z][a-z]?|[cnops])',s[i:j+1] if j>0 else s[i:])
            if m:
                el=m.group(1)
                el=el.capitalize() if el.islower() else el
                if el in EIDX: v[EIDX[el]]+=1
            i=(j+1) if j>0 else i+1; continue
        two=s[i:i+2]
        if two in SM_TWO and two.isalpha():
            if two in EIDX: v[EIDX[two]]+=1
            i+=2; continue
        if c in 'CNOPSFI':
            if c in EIDX: v[EIDX[c]]+=1
        elif c in 'cnops':
            v[EIDX[c.upper()]]+=1
        i+=1
    tot=v.sum()
    return v/tot if tot>0 else None

pts=[]
def add(ds,label,prop,vec):
    if vec is not None and np.isfinite(vec).all():
        pts.append({'ds':ds,'label':str(label)[:60],'prop':str(prop)[:60],'v':vec})

# 1 ESTM thermoelectrics
d=pd.read_excel('SIMD/dataset/estm.xlsx')
fc, tc = d.columns[0], d.columns[1]
zt = d.columns[6] if len(d.columns)>6 else d.columns[-1]
for _,r in d.iterrows():
    add('ESTM thermoelectrics', r[fc], f"T={r[tc]}K ZT={r[zt]:.2f}" if pd.notna(r[zt]) else f"T={r[tc]}K", formula_vec(r[fc]))

# 2 AqSolDB (merge A-I, dedupe)
frames=[pd.read_csv(f) for f in sorted(glob.glob('AqSolDB/data/dataset-[A-I].csv'))]
aq=pd.concat(frames).drop_duplicates('InChIKey')
aq=aq.sample(n=min(3000,len(aq)),random_state=0)
for _,r in aq.iterrows():
    add('AqSolDB solubility', r.get('Name',r['SMILES']), f"logS={r['Solubility']:.2f}", smiles_vec(r['SMILES']))

# 3 Photoswitches
d=pd.read_csv('The-Photoswitch-Dataset/dataset/photoswitches.csv')
wl=[c for c in d.columns if 'pi-pi* wavelength' in c][0]
for _,r in d.iterrows():
    add('Photoswitches', r['SMILES'], f"λ={r[wl]}nm" if pd.notna(r[wl]) else '', smiles_vec(r['SMILES']))

# 4 FreeSolv
rows=[l.split(';') for l in open('FreeSolv/database.txt') if not l.startswith('#')]
for r in rows:
    if len(r)>4: add('FreeSolv hydration', r[2].strip(), f"dG={r[3].strip()} kcal/mol", smiles_vec(r[1].strip()))

# 5 OCx24 electrocatalysts
d=pd.read_csv('fairchem/src/fairchem/applications/ocx/data/experimental_data/ExpDataDump_241113_clean.csv')
for _,r in d.iterrows():
    add('OCx24 electrocatalysts', r['composition'], f"{r['reaction']} @{r['current density']}", formula_vec(r['composition']))

# 6 Borg MPEA (high-entropy alloys)
d=pd.read_csv('DataScribe_DeepTabularLearning/datasets/BorgHEA-DATA/data/MPEA_dataset.csv')
fcol=[c for c in d.columns if 'formula' in c.lower()]
fcol=fcol[0] if fcol else d.columns[0]
ycol=[c for c in d.columns if 'YS' in c or 'yield' in c.lower()]
for _,r in d.iterrows():
    prop=f"YS={r[ycol[0]]}" if ycol and pd.notna(r[ycol[0]]) else ''
    add('MPEA alloys (Borg)', r[fcol], prop, formula_vec(r[fcol]))

# 7 BIRDSHOT if usable csv exists
try:
    bs=glob.glob('DataScribe_DeepTabularLearning/datasets/BIRDSHOT-HEADATA/**/*.csv',recursive=True)
    if bs:
        d=pd.read_csv(bs[0])
        comp_cols=[c for c in d.columns if c.strip() in ELEMS]
        if len(comp_cols)>=4:
            for _,r in d.iterrows():
                v=np.zeros(len(ELEMS)); ok=False
                for c in comp_cols:
                    x=pd.to_numeric(r[c],errors='coerce')
                    if pd.notna(x) and x>0: v[EIDX[c.strip()]]+=x; ok=True
                if ok:
                    s=v.sum(); add('BIRDSHOT HEA', '-'.join(f'{c}{r[c]}' for c in comp_cols if pd.to_numeric(r[c],errors='coerce') and r[c]>0)[:40], '', v/s)
except Exception as e:
    print('birdshot skip:', e)


# 8 IUPAC pKa
d=pd.read_csv('Dissociation-Constants/iupac_high-confidence_v2_3.csv')
d=d.sample(n=min(3000,len(d)),random_state=0)
for _,r in d.iterrows():
    add('IUPAC pKa', r['SMILES'], f"pKa={r['pka_value']} ({r['pka_type']})", smiles_vec(r['SMILES']))

print('total points:', len(pts))
from collections import Counter
print(Counter(p['ds'] for p in pts))

X=np.array([p['v'] for p in pts])
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
Xp=PCA(n_components=min(30,X.shape[1]), random_state=0).fit_transform(X)
emb=TSNE(n_components=2, perplexity=40, init='pca', random_state=0, max_iter=450).fit_transform(Xp)
for p,(x,y) in zip(pts,emb):
    p['x']=round(float(x),2); p['y']=round(float(y),2); del p['v']
json.dump(pts, open('/tmp/data/points.json','w'))
print('saved /tmp/data/points.json')
