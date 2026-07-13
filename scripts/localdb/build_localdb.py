"""Build data/collective.sqlite - a local, unified, multi-domain EXPERIMENTAL database.

Only mirrors datasets whose licenses permit redistribution/local use
(CC-BY / CC0 / MIT / public source repos). For each dataset:
  - clones its GitHub repo into WORKDIR if missing (git clone --depth 1)
  - loads the measured data into a native table  raw_<id>
  - normalizes rows into the unified table  measurements
      (dataset, material, material_kind, property, value, unit, conditions)
  - registers metadata + short description (from catalog/catalog.json) in  datasets

Usage:   python scripts/localdb/build_localdb.py [--workdir /path/for/clones]
Query:   python scripts/localdb/build_localdb.py --query "SELECT property,COUNT(*) FROM measurements GROUP BY property"
"""
from __future__ import annotations
import argparse, json, os, sqlite3, subprocess, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DB = os.environ.get("COLLECTIVE_DB", os.path.join(ROOT, "data", "collective.sqlite"))
CATALOG = os.path.join(ROOT, "catalog", "catalog.json")

SOURCES = {
  "estm-thermoelectric":   {"git": "https://github.com/KRICT-DATA/SIMD.git", "dir": "SIMD"},
  "aqsoldb":               {"git": "https://github.com/mcsorkun/AqSolDB.git", "dir": "AqSolDB"},
  "iupac-digitized-pka":   {"git": "https://github.com/IUPAC/Dissociation-Constants.git", "dir": "Dissociation-Constants"},
  "photoswitch-dataset":   {"git": "https://github.com/Ryan-Rhys/The-Photoswitch-Dataset.git", "dir": "The-Photoswitch-Dataset"},
  "freesolv":              {"git": "https://github.com/MobleyLab/FreeSolv.git", "dir": "FreeSolv"},
  "ocx24-open-catalyst-experiments-2024": {"git": "https://github.com/FAIR-Chem/fairchem.git", "dir": "fairchem", "sparse": "src/fairchem/applications/ocx"},
  "mpea-dataset-borg":     {"git": "https://github.com/vahid2364/DataScribe_DeepTabularLearning.git", "dir": "DataScribe_DeepTabularLearning"},
  "obelix-solid-electrolytes": {"git": "https://github.com/NRC-Mila/OBELiX.git", "dir": "OBELiX"},
  "openpoly-benchmark":    {"git": "https://github.com/WangGroupFDU/Openpoly_benchmark.git", "dir": "Openpoly_benchmark"},
  "nist-isodb":            {"git": "https://github.com/NIST-ISODB/isodb-library.git", "dir": "isodb-library"},
}
ISODB_CAP = 8000  # isotherm files parsed per build; raise on a fast machine

def ensure(workdir, spec):
    p = os.path.join(workdir, spec["dir"])
    if os.path.exists(p): return p
    cmd = ["git", "clone", "--depth", "1"]
    if spec.get("sparse"): cmd += ["--filter=blob:none", "--sparse"]
    subprocess.run(cmd + [spec["git"], p], check=True)
    if spec.get("sparse"):
        subprocess.run(["git", "-C", p, "sparse-checkout", "set", spec["sparse"]], check=True)
    return p

def M(ds, mat, kind, prop, val, unit="", cond=""):
    try: v = float(val)
    except (TypeError, ValueError): return None
    return (ds, str(mat)[:120], kind, prop, v, unit, str(cond)[:120])

def load_all(workdir, con):
    rows = []
    # ESTM thermoelectrics
    p = ensure(workdir, SOURCES["estm-thermoelectric"])
    d = pd.read_excel(os.path.join(p, "dataset/estm.xlsx"))
    d.to_sql("raw_estm", con, if_exists="replace", index=False)
    cols = list(d.columns)
    for _, r in d.iterrows():
        for c in cols[2:]:
            rows.append(M("estm-thermoelectric", r[cols[0]], "formula", str(c)[:40], r[c], "", f"T={r[cols[1]]}K"))
    # AqSolDB
    p = ensure(workdir, SOURCES["aqsoldb"])
    import glob as g
    aq = pd.concat([pd.read_csv(f) for f in sorted(g.glob(os.path.join(p, "data/dataset-[A-I].csv")))]).drop_duplicates("InChIKey")
    aq.to_sql("raw_aqsoldb", con, if_exists="replace", index=False)
    for _, r in aq.iterrows():
        rows.append(M("aqsoldb", r["SMILES"], "smiles", "logS", r["Solubility"], "log mol/L"))
    # IUPAC pKa
    p = ensure(workdir, SOURCES["iupac-digitized-pka"])
    d = pd.read_csv(os.path.join(p, "iupac_high-confidence_v2_3.csv"))
    d.to_sql("raw_iupac_pka", con, if_exists="replace", index=False)
    for _, r in d.iterrows():
        rows.append(M("iupac-digitized-pka", r["SMILES"], "smiles", f"pKa({r['pka_type']})", r["pka_value"], "", f"T={r['T']}"))
    # Photoswitches
    p = ensure(workdir, SOURCES["photoswitch-dataset"])
    d = pd.read_csv(os.path.join(p, "dataset/photoswitches.csv"))
    d.to_sql("raw_photoswitches", con, if_exists="replace", index=False)
    wl = [c for c in d.columns if "pi-pi* wavelength" in c][0]
    for _, r in d.iterrows():
        rows.append(M("photoswitch-dataset", r["SMILES"], "smiles", "E_pi-pi*_lambda_max", r[wl], "nm"))
    # FreeSolv
    p = ensure(workdir, SOURCES["freesolv"])
    fs = [l.split(";") for l in open(os.path.join(p, "database.txt")) if not l.startswith("#")]
    fsd = pd.DataFrame([r[:5] for r in fs if len(r) > 4], columns=["id","smiles","iupac","expt","d_expt"])
    fsd.to_sql("raw_freesolv", con, if_exists="replace", index=False)
    for r in fs:
        if len(r) > 4: rows.append(M("freesolv", r[1].strip(), "smiles", "dG_hydration", r[3], "kcal/mol"))
    # OCx24
    p = ensure(workdir, SOURCES["ocx24-open-catalyst-experiments-2024"])
    d = pd.read_csv(os.path.join(p, "src/fairchem/applications/ocx/data/experimental_data/ExpDataDump_241113_clean.csv"))
    d.to_sql("raw_ocx24", con, if_exists="replace", index=False)
    for _, r in d.iterrows():
        for prop in ("fe_h2", "fe_co", "voltage"):
            if prop in d.columns:
                rows.append(M("ocx24-open-catalyst-experiments-2024", r["composition"], "formula", prop, r[prop], "", f"{r['reaction']} @{r['current density']}"))
    # Borg MPEA
    p = ensure(workdir, SOURCES["mpea-dataset-borg"])
    d = pd.read_csv(os.path.join(p, "datasets/BorgHEA-DATA/data/MPEA_dataset.csv"))
    d.to_sql("raw_mpea", con, if_exists="replace", index=False)
    fcol = [c for c in d.columns if "formula" in c.lower()][0]
    props = [c for c in d.columns if any(k in c.upper() for k in ("YS", "UTS", "HV", "ELONG"))]
    for _, r in d.iterrows():
        for c in props:
            rows.append(M("mpea-dataset-borg", r[fcol], "formula", str(c)[:40], r[c]))
    # OBELiX solid electrolytes
    p = ensure(workdir, SOURCES["obelix-solid-electrolytes"])
    d = pd.read_csv(os.path.join(p, "data/processed.csv"))
    d.to_sql("raw_obelix", con, if_exists="replace", index=False)
    for _, r in d.iterrows():
        rows.append(M("obelix-solid-electrolytes", r["Composition"], "formula",
                      "ionic_conductivity", r["Ionic conductivity (S cm-1)"], "S/cm"))
    # OpenPoly polymer benchmark (wide -> long)
    p = ensure(workdir, SOURCES["openpoly-benchmark"])
    d = pd.read_csv(os.path.join(p, "data/final_polymer_properties_fromliterature.csv"))
    d.to_sql("raw_openpoly", con, if_exists="replace", index=False)
    for _, r in d.iterrows():
        for c in d.columns:
            if c in ("Name", "PSMILES"): continue
            rows.append(M("openpoly-benchmark", r.get("PSMILES", r.get("Name")), "smiles", str(c)[:50], r[c]))
    # NIST ISODB (one summary row per isotherm: max uptake at max pressure)
    import glob as g, json as j
    p = ensure(workdir, SOURCES["nist-isodb"])
    files = g.glob(os.path.join(p, "**", "*.json"), recursive=True)
    parsed = 0
    for f in files:
        if parsed >= ISODB_CAP: break
        try:
            o = j.load(open(f, encoding="utf-8"))
            pts = o.get("isotherm_data")
            if not pts: continue
            ads = (o.get("adsorbates") or [{}])[0].get("name", "?")
            mat = (o.get("adsorbent") or {}).get("name", "?")
            T = o.get("temperature", "?")
            best = max(pts, key=lambda x: x.get("pressure", 0) or 0)
            upt = (best.get("species_data") or [{}])[0].get("adsorption", best.get("total_adsorption"))
            rows.append(M("nist-isodb", mat, "name", f"uptake_{ads}", upt,
                          str(o.get("adsorptionUnits", "")), f"T={T}K P={best.get('pressure')} {o.get('pressureUnits','')}"))
            parsed += 1
        except Exception:
            continue
    return [r for r in rows if r]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", default=os.path.expanduser("~/.collective_data_cache"))
    ap.add_argument("--query")
    a = ap.parse_args()
    if a.query:
        con = sqlite3.connect(DB)
        for row in con.execute(a.query).fetchall(): print(row)
        return
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    os.makedirs(a.workdir, exist_ok=True)
    con = sqlite3.connect(DB)
    cat = {e["id"]: e for e in json.load(open(CATALOG, encoding="utf-8"))["entries"]}
    rows = load_all(a.workdir, con)
    con.execute("DROP TABLE IF EXISTS measurements")
    con.execute("CREATE TABLE measurements (dataset TEXT, material TEXT, material_kind TEXT, property TEXT, value REAL, unit TEXT, conditions TEXT)")
    con.executemany("INSERT INTO measurements VALUES (?,?,?,?,?,?,?)", rows)
    con.execute("DROP TABLE IF EXISTS datasets")
    con.execute("CREATE TABLE datasets (id TEXT PRIMARY KEY, name TEXT, description TEXT, domain TEXT, subdomain TEXT, license TEXT, doi TEXT, homepage TEXT, n_measurements INTEGER)")
    for ds in SOURCES:
        e = cat.get(ds, {})
        n = con.execute("SELECT COUNT(*) FROM measurements WHERE dataset=?", (ds,)).fetchone()[0]
        con.execute("INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?)",
                    (ds, e.get("name", ds), e.get("description", ""), e.get("domain", ""),
                     e.get("subdomain", ""), e.get("license", ""), e.get("doi", ""),
                     e.get("homepage_url", ""), n))
    con.execute("CREATE INDEX IF NOT EXISTS ix_m ON measurements(dataset, property)")
    con.commit()
    print("datasets:", con.execute("SELECT COUNT(*) FROM datasets").fetchone()[0])
    print("measurements:", con.execute("SELECT COUNT(*) FROM measurements").fetchone()[0])
    for r in con.execute("SELECT id, n_measurements FROM datasets"): print("  ", r)

if __name__ == "__main__":
    main()
