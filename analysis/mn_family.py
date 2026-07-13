import re, numpy as np, pandas as pd
KB = 8.617e-5
f = pd.read_csv("mn_estm_arrhenius.csv")
FRE = re.compile(r"([A-Z][a-z]?)([\d.]*)")
def family(formula):
    els = {}
    for el, n in FRE.findall(str(formula)):
        if el: els[el] = els.get(el, 0) + (float(n) if n else 1.0)
    tot = sum(els.values()) or 1
    major = sorted([e for e, v in els.items() if v / tot >= 0.15])
    return "-".join(major[:3]) if major else "?"
f["family"] = f.material.map(family)
out = []
for fam, g in f.groupby("family"):
    if len(g) < 8: continue
    s, i = np.polyfit(g.Ea_eV, g.lnA, 1)
    r2 = np.corrcoef(g.Ea_eV, g.lnA)[0, 1] ** 2
    out.append({"family": fam, "n": len(g), "slope": s, "r2": r2,
                "T_iso_K": 1/(KB*s) if s > 0 else np.nan})
r = pd.DataFrame(out).sort_values("r2", ascending=False)
r.to_csv("mn_estm_families.csv", index=False)
print(r.to_string(index=False))
print("\npooled r2 = 0.053 (baseline); family-median r2 =", round(r.r2.median(), 3))
