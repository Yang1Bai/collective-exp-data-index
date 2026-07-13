"""Phase 1: Meyer-Neldel compensation analysis on the unified data lake.
Extracts Arrhenius parameters (ln A vs Ea) per material from T-dependent
measurements, then tests for compensation (ln A = a + Ea/kB*T_iso).
Usage: COLLECTIVE_DB=<path> python mn_compensation.py
"""
import os, re, sqlite3, numpy as np, pandas as pd
KB = 8.617e-5  # eV/K
DB = os.environ.get("COLLECTIVE_DB", "../data/collective.sqlite")
con = sqlite3.connect(DB)
q = "SELECT material, value, conditions FROM measurements WHERE dataset='estm-thermoelectric' AND property LIKE 'electrical_conductivity%' AND value>0"
d = pd.read_sql(q, con)
d["T"] = d.conditions.str.extract(r"T=([\d.]+)K").astype(float)
d = d.dropna()
rows = []
for mat, g in d.groupby("material"):
    g = g.drop_duplicates("T")
    if len(g) < 4: continue
    x = 1.0 / g["T"].values; y = np.log(g["value"].values)
    slope, icept = np.polyfit(x, y, 1)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    Ea = -slope * KB
    if r2 > 0.9 and 0 < Ea < 2:  # activated (semiconducting) branch only
        rows.append({"material": mat, "Ea_eV": Ea, "lnA": icept, "r2": r2, "npts": len(g)})
f = pd.DataFrame(rows)
f.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mn_estm_arrhenius.csv"), index=False)
print(f"materials with T-series: {d.material.nunique()}; activated Arrhenius fits (r2>0.9): {len(f)}")
if len(f) > 10:
    s, i = np.polyfit(f.Ea_eV, f.lnA, 1)
    r2 = np.corrcoef(f.Ea_eV, f.lnA)[0, 1] ** 2
    print(f"COMPENSATION: lnA = {i:.2f} + {s:.2f}*Ea ; r2={r2:.3f} ; T_iso={1/(KB*s):.0f} K" if s > 0 else f"no positive compensation (slope={s:.2f}, r2={r2:.3f})")
