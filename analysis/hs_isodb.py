import os, re, sqlite3, numpy as np, pandas as pd
KB = 8.617e-5
con = sqlite3.connect(os.environ.get("COLLECTIVE_DB", "/tmp/collective.sqlite"))
d = pd.read_sql("SELECT material, property, value, conditions FROM measurements WHERE dataset='nist-isodb' AND value>0", con)
d["T"] = d.conditions.str.extract(r"T=([\d.]+)K").astype(float)
d["P"] = d.conditions.str.extract(r"P=([\d.eE+-]+)").astype(float)
d = d.dropna(subset=["T", "P"])
d = d[(d["T"] > 200) & (d["T"] < 700) & (d.P > 0)]
res, temps = [], []
for (mat, prop), g in d.groupby(["material", "property"]):
    g = g.drop_duplicates("T")
    if len(g) < 4 or g.P.max() / g.P.min() > 3: continue
    x = 1.0 / g["T"].values; y = np.log(g["value"].values)
    s, i = np.polyfit(x, y, 1)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    if r2 > 0.9:
        res.append({"system": f"{mat}|{prop}", "dH_slope": s, "lnA": i, "n": len(g)})
        temps.extend(g["T"].values)
f = pd.DataFrame(res)
print("systems with clean van't Hoff fits:", len(f))
if len(f) > 10:
    s, i = np.polyfit(f.dH_slope, f.lnA, 1)
    r2 = np.corrcoef(f.dH_slope, f.lnA)[0, 1] ** 2
    T_iso = 1 / s if s != 0 else np.nan   # lnA vs slope(K units): T_iso = 1/slope
    T_hm = len(temps) / np.sum(1.0 / np.array(temps))
    f.to_csv("hs_isodb_vanthoff.csv", index=False)
    print(f"COMPENSATION: r2={r2:.3f}, T_iso={abs(T_iso):.0f}K vs Krug T_harmonic={T_hm:.0f}K")
    print("KRUG VERDICT:", "ARTIFACT-SUSPECT (T_iso ~ T_hm)" if abs(abs(T_iso)-T_hm) < 0.25*T_hm else "GENUINE compensation (T_iso far from T_hm)")
