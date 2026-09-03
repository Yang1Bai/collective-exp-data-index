"""Build the local experimental-data SQLite snapshot from pinned sources.

The generated database is intentionally ignored by git.  The lock file next to
this script pins every source commit; the database records row-level provenance
and never infers thermodynamic quantities from incompatible observations.

Usage
-----
python scripts/localdb/build_localdb.py
python scripts/localdb/build_localdb.py --query "SELECT dataset, COUNT(*) FROM measurements GROUP BY dataset"
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_DB = ROOT / "data" / "collective.sqlite"
DB = Path(os.environ.get("COLLECTIVE_DB", DEFAULT_DB)).resolve()
CATALOG = ROOT / "catalog" / "catalog.json"
LOCK = HERE / "sources.lock.json"

ELEMENT_RE = re.compile(r"[A-Z][a-z]?")
NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")


def run_git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def ensure_source(workdir: Path, spec: dict[str, Any]) -> Path:
    """Materialize exactly the commit named in the lock file."""
    path = workdir / spec["directory"]
    commit = spec["commit"]
    if not (path / ".git").exists():
        clone = ["clone", "--filter=blob:none"]
        if spec.get("read_with_git_show"):
            clone.append("--no-checkout")
        clone.extend([spec["git"], str(path)])
        subprocess.run(["git", *clone], check=True)
    try:
        run_git("cat-file", "-e", f"{commit}^{{commit}}", cwd=path)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "fetch", "--depth", "1", "origin", commit], cwd=path, check=True)
    if not spec.get("read_with_git_show"):
        subprocess.run(["git", "checkout", "--detach", "--force", commit], cwd=path, check=True)
    actual = run_git("rev-parse", commit, cwd=path)
    if actual != commit:
        raise RuntimeError(f"Pinned commit mismatch for {spec['directory']}: {actual} != {commit}")
    return path


def read_csv_from_git(repo: Path, commit: str, relpath: str, **kwargs: Any) -> pd.DataFrame:
    raw = subprocess.check_output(["git", "show", f"{commit}:{relpath}"], cwd=repo)
    return pd.read_csv(io.BytesIO(raw), **kwargs)


def read_remote_pinned_csv(spec: dict[str, Any], **kwargs: Any) -> pd.DataFrame:
    request = urllib.request.Request(spec["raw_url"], headers={"User-Agent": "collective-exp-data-index/0.2"})
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read()
    expected_sha256 = spec.get("raw_sha256")
    if expected_sha256:
        observed_sha256 = hashlib.sha256(raw).hexdigest()
        if observed_sha256 != expected_sha256:
            raise RuntimeError(
                f"Pinned remote-file hash mismatch: {observed_sha256} != {expected_sha256}"
            )
    return pd.read_csv(io.BytesIO(raw), **kwargs)


def source_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_formula_segment(text: str, pos: int = 0) -> tuple[dict[str, float], int]:
    counts: dict[str, float] = defaultdict(float)
    while pos < len(text):
        if text[pos] == ")":
            return dict(counts), pos + 1
        if text[pos] == "(":
            inner, pos = _parse_formula_segment(text, pos + 1)
            match = NUMBER_RE.match(text, pos)
            multiplier = float(match.group()) if match else 1.0
            pos = match.end() if match else pos
            for element, amount in inner.items():
                counts[element] += amount * multiplier
            continue
        match = ELEMENT_RE.match(text, pos)
        if not match:
            raise ValueError(f"unsupported formula token at {text[pos:]}")
        element = match.group()
        pos = match.end()
        number = NUMBER_RE.match(text, pos)
        amount = float(number.group()) if number else 1.0
        pos = number.end() if number else pos
        counts[element] += amount
    return dict(counts), pos


def canonical_formula(formula: Any) -> tuple[str | None, str | None]:
    """Return a scale-invariant composition key, rejecting ambiguous formulas."""
    text = re.sub(r"\s+", "", str(formula))
    if not text or text.lower() == "nan":
        return None, "missing_formula"
    try:
        # OCx encodes alloy fractions as ``Ag-0.2-Pd-0.8`` rather than a
        # conventional chemical formula.
        if re.fullmatch(r"(?:[A-Z][a-z]?-(?:\d+(?:\.\d*)?|\.\d+)-?)+", text):
            tokens = text.strip("-").split("-")
            counts = {tokens[i]: float(tokens[i + 1]) for i in range(0, len(tokens), 2)}
            pos = len(text)
        else:
            counts, pos = _parse_formula_segment(text)
        if pos != len(text) or not counts:
            raise ValueError("unparsed suffix")
        total = sum(counts.values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("non-positive total")
        key = "|".join(f"{el}:{counts[el] / total:.10g}" for el in sorted(counts))
        return key, None
    except (ValueError, OverflowError):
        return None, "unparsed_formula"


def canonical_smiles(smiles: Any) -> tuple[str | None, str | None]:
    text = str(smiles).strip()
    if not text or text.lower() == "nan":
        return None, "missing_smiles"
    try:
        from rdkit import Chem
        from rdkit import RDLogger

        RDLogger.DisableLog("rdApp.*")

        mol = Chem.MolFromSmiles(text)
        if mol is None:
            return None, "invalid_smiles"
        return Chem.MolToSmiles(mol, canonical=True), None
    except ImportError:
        return text, "smiles_not_canonicalized"


def canonical_mixture(mixture: Any) -> tuple[str | None, str | None]:
    """Return a scale-invariant key for a named-component formulation."""
    text = str(mixture).strip()
    if not text or text.lower() == "nan":
        return None, "missing_mixture"
    try:
        amounts: dict[str, float] = {}
        for token in text.split("|"):
            name, raw_amount = token.split(":", 1)
            name = name.strip()
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
                raise ValueError("invalid component name")
            amount = float(raw_amount)
            if not math.isfinite(amount) or amount < 0:
                raise ValueError("invalid component amount")
            amounts[name] = amounts.get(name, 0.0) + amount
        total = sum(amounts.values())
        if total <= 0:
            raise ValueError("non-positive mixture total")
        key = "|".join(
            f"{name}:{amounts[name] / total:.10g}" for name in sorted(amounts)
        )
        return key, None
    except (ValueError, OverflowError):
        return None, "unparsed_mixture"


def json_conditions(**items: Any) -> str:
    clean = {k: v for k, v in items.items() if pd.notna(v) and v not in (None, "")}
    return json.dumps(clean, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def composition_columns_to_formula(row: pd.Series, elements: Iterable[str]) -> str:
    """Encode a table of positive atomic percentages as a parseable formula."""
    parts = []
    for element in elements:
        value = row.get(element)
        if pd.notna(value) and float(value) > 0:
            parts.append(f"{element}{float(value):.10g}")
    return "".join(parts)


def measurement(
    dataset: str,
    source_row_id: Any,
    material: Any,
    material_kind: str,
    prop: str,
    value: Any,
    unit: str,
    conditions: str,
    reference: Any,
    commit: str,
    extra_flags: Iterable[str] = (),
) -> tuple[Any, ...] | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    if material_kind == "formula":
        key, flag = canonical_formula(material)
    elif material_kind == "smiles":
        key, flag = canonical_smiles(material)
    elif material_kind == "mixture":
        key, flag = canonical_mixture(material)
    else:
        raise ValueError(f"Unsupported material kind: {material_kind}")
    flags = sorted(set([*extra_flags, *([flag] if flag else [])]))
    return (
        dataset,
        str(source_row_id),
        str(material),
        key,
        material_kind,
        str(prop),
        numeric,
        unit,
        conditions,
        "" if pd.isna(reference) else str(reference),
        commit,
        json.dumps(flags, separators=(",", ":")),
    )


def add(rows: list[tuple[Any, ...]], row: tuple[Any, ...] | None) -> None:
    if row is not None:
        rows.append(row)


def connected_obelix_groups(frame: pd.DataFrame) -> dict[str, str]:
    """Connected components under shared DOI or exact composition."""
    parent = {str(identifier): str(identifier) for identifier in frame["ID"]}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for _, row in frame.iterrows():
        identifier = str(row["ID"])
        buckets[("composition", str(row["Composition"]))].append(identifier)
        for doi in str(row["DOI"]).split("|"):
            doi = doi.strip().lower()
            if doi and doi != "nan":
                buckets[("doi", doi)].append(identifier)
    for identifiers in buckets.values():
        for other in identifiers[1:]:
            union(identifiers[0], other)
    roots = {identifier: find(identifier) for identifier in parent}
    labels = {root: f"obelix-group-{i:04d}" for i, root in enumerate(sorted(set(roots.values())))}
    return {identifier: labels[root] for identifier, root in roots.items()}


def load_all(workdir: Path, connection: sqlite3.Connection, sources: dict[str, Any]) -> list[tuple[Any, ...]]:
    rows: list[tuple[Any, ...]] = []

    spec = sources["estm-thermoelectric"]
    repo = ensure_source(workdir, spec)
    data = pd.read_excel(repo / spec["data_path"])
    data.to_sql("raw_estm", connection, if_exists="replace", index=False)
    units = {
        "seebeck_coefficient(μV/K)": "μV/K",
        "electrical_conductivity(S/m)": "S/m",
        "thermal_conductivity(W/mK)": "W/(m K)",
        "power_factor(W/mK2)": "W/(m K^2)",
        "ZT": "1",
    }
    for index, row in data.iterrows():
        for prop, unit in units.items():
            add(rows, measurement("estm-thermoelectric", index, row["Formula"], "formula", prop, row[prop], unit,
                                  json_conditions(temperature=row["temperature(K)"], temperature_unit="K"),
                                  row["reference"], spec["commit"]))

    spec = sources["aqsoldb"]
    repo = ensure_source(workdir, spec)
    files = sorted((repo / "data").glob("dataset-[A-I].csv"))
    data = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
    data = data.drop_duplicates("InChIKey", keep="first")
    data.to_sql("raw_aqsoldb", connection, if_exists="replace", index=False)
    for _, row in data.iterrows():
        add(rows, measurement("aqsoldb", row["ID"], row["SMILES"], "smiles", "logS", row["Solubility"],
                              "log10(mol/L)", "{}", row["InChIKey"], spec["commit"]))

    spec = sources["iupac-digitized-pka"]
    repo = ensure_source(workdir, spec)
    data = pd.read_csv(repo / spec["data_path"])
    data.to_sql("raw_iupac_pka", connection, if_exists="replace", index=False)
    for _, row in data.iterrows():
        add(rows, measurement("iupac-digitized-pka", row["unique_ID"], row["SMILES"], "smiles",
                              f"pKa({row['pka_type']})", row["pka_value"], "1",
                              json_conditions(temperature=row["T"], temperature_unit="degC", method=row["method"],
                                              assessment=row["assessment"], cosolvent=row["cosolvent"]),
                              row["ref"], spec["commit"]))

    spec = sources["photoswitch-dataset"]
    repo = ensure_source(workdir, spec)
    data = pd.read_csv(repo / spec["data_path"])
    data.to_sql("raw_photoswitches", connection, if_exists="replace", index=False)
    # Retain the experimentally measured cross-property neighborhood while
    # keeping the DFT columns out of the experimental snapshot.  These fields
    # support leakage-aware tests of local E/Z-state knowledge borrowing.
    photoswitch_properties = {
        "rate of thermal isomerisation from Z-E in s-1": (
            "thermal_isomerization_rate_Z_to_E", "s^-1",
        ),
        "Z PhotoStationaryState": ("Z_photostationary_state", "%"),
        "E PhotoStationaryState": ("E_photostationary_state", "%"),
        "E isomer pi-pi* wavelength in nm": ("E_pi-pi*_lambda_max", "nm"),
        "E isomer n-pi* wavelength in nm": ("E_n-pi*_lambda_max", "nm"),
        "Z isomer pi-pi* wavelength in nm": ("Z_pi-pi*_lambda_max", "nm"),
        "Z isomer n-pi* wavelength in nm": ("Z_n-pi*_lambda_max", "nm"),
    }
    for index, row in data.iterrows():
        for raw_property, (prop, unit) in photoswitch_properties.items():
            conditions = json_conditions(
                thermal_isomerization_solvent=row.get("Solvent used for thermal isomerisation rates")
                if prop == "thermal_isomerization_rate_Z_to_E" else None,
                irradiation_solvent=row.get("Irradiation solvent")
                if prop.endswith("photostationary_state") else None,
                e_to_z_irradiation_wavelength=row.get("E-Z irradiation wavelength in nm")
                if prop.endswith("photostationary_state") else None,
                z_to_e_irradiation_wavelength=row.get("Z-E irradiation wavelength")
                if prop.endswith("photostationary_state") else None,
            )
            add(rows, measurement(
                "photoswitch-dataset", index, row["SMILES"], "smiles", prop,
                row[raw_property], unit, conditions, f"photoswitch-record-{index}", spec["commit"],
            ))

    spec = sources["freesolv"]
    repo = ensure_source(workdir, spec)
    records = []
    with (repo / spec["data_path"]).open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            parts = [part.strip() for part in line.split(";")]
            if len(parts) >= 5:
                records.append(parts[:5])
    data = pd.DataFrame(records, columns=["id", "smiles", "iupac", "expt", "d_expt"])
    data.to_sql("raw_freesolv", connection, if_exists="replace", index=False)
    for _, row in data.iterrows():
        add(rows, measurement("freesolv", row["id"], row["smiles"], "smiles", "dG_hydration", row["expt"],
                              "kcal/mol", json_conditions(uncertainty=row["d_expt"], uncertainty_unit="kcal/mol"),
                              row["id"], spec["commit"]))

    spec = sources["ocx24-open-catalyst-experiments-2024"]
    data = read_remote_pinned_csv(spec)
    data.to_sql("raw_ocx24", connection, if_exists="replace", index=False)
    for index, row in data.iterrows():
        for prop in ("fe_h2", "fe_co", "voltage"):
            if prop in data.columns:
                add(rows, measurement("ocx24-open-catalyst-experiments-2024", index, row["composition"], "formula",
                                      prop, row[prop], "%" if prop.startswith("fe_") else "V",
                                      json_conditions(reaction=row.get("reaction"), current_density=row.get("current density")),
                                      row.get("doi", ""), spec["commit"]))

    spec = sources["mpea-dataset-borg"]
    repo = ensure_source(workdir, spec)
    data = read_csv_from_git(repo, spec["commit"], spec["data_path"])
    data.to_sql("raw_mpea", connection, if_exists="replace", index=False)
    properties = [column for column in data.columns if any(token in column.upper() for token in ("YS", "UTS", "HV", "ELONG"))]
    for index, row in data.iterrows():
        for prop in properties:
            unit = "MPa" if any(token in prop.upper() for token in ("YS", "UTS", "HV")) else "%"
            add(rows, measurement("mpea-dataset-borg", index, row["FORMULA"], "formula", prop, row[prop], unit,
                                  json_conditions(test_temperature=row.get("PROPERTY: Test temperature ($^\\circ$C)"),
                                                  temperature_unit="degC", processing=row.get("PROPERTY: Processing method")),
                                  row.get("REFERENCE: doi", ""), spec["commit"]))

    spec = sources["matbench-steels"]
    data = read_remote_pinned_csv(spec)
    if len(data) != int(spec["n_rows_expected"]):
        raise RuntimeError(
            f"Matbench steels row-count mismatch: {len(data)} != {spec['n_rows_expected']}"
        )
    data.to_sql("raw_matbench_steels", connection, if_exists="replace", index=False)
    steel_properties = {
        "yield strength": "MPa",
        "tensile strength": "MPa",
        "elongation": "%",
    }
    for index, row in data.iterrows():
        for prop, unit in steel_properties.items():
            add(rows, measurement(
                "matbench-steels",
                f"mb-steels-{index + 1:03d}",
                row["formula"],
                "formula",
                prop,
                row[prop],
                unit,
                "{}",
                spec["record_doi"],
                spec["commit"],
            ))

    spec = sources["birdshot-high-entropy-alloy-campaign"]
    repo = ensure_source(workdir, spec)
    data = read_csv_from_git(repo, spec["commit"], spec["data_path"])
    data.to_sql("raw_birdshot", connection, if_exists="replace", index=False)
    elements = ("Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V")
    birdshot_properties = {
        "Hardness, HV": "HV",
        "Yield Strength (MPa)": "MPa",
        "UTS_True (Mpa)": "MPa",
        "Elong_T (%)": "%",
        "Modulus (GPa) SRJT": "GPa",
    }
    for index, row in data.iterrows():
        formula = composition_columns_to_formula(row, elements)
        conditions = json_conditions(
            campaign_year=row.get("Year"),
            cold_work_percent_reduction=row.get("Cold Work (%Reduction)"),
            holding_time_h=row.get("Holding time (h)"),
            grain_size_um=row.get("Grain Size(um)"),
            cracked=row.get("Cracked"),
        )
        for prop, unit in birdshot_properties.items():
            add(rows, measurement(
                "birdshot-high-entropy-alloy-campaign",
                f"birdshot-v5-{index}",
                formula,
                "formula",
                prop,
                row.get(prop),
                unit,
                conditions,
                spec["record_doi"],
                spec["commit"],
            ))

    spec = sources["kit-electrolyte-conductivity-5035"]
    data = read_remote_pinned_csv(spec, sep=";", skiprows=[1, 2])
    if len(data) != int(spec["n_rows_expected"]):
        raise RuntimeError(
            f"KIT electrolyte row-count mismatch: {len(data)} != {spec['n_rows_expected']}"
        )
    required = ["experimentID", "temperature", "PC", "EC", "EMC", "LiPF_6", "EIS_conductivity"]
    if data[required].isna().any().any():
        raise RuntimeError("KIT electrolyte required fields contain missing values")
    data.to_sql("raw_kit_electrolyte", connection, if_exists="replace", index=False)
    for index, row in data.iterrows():
        mixture = "|".join(
            f"{component}:{float(row[component]):.10g}"
            for component in ("PC", "EC", "EMC", "LiPF_6")
        )
        add(rows, measurement(
            "kit-electrolyte-conductivity-5035",
            f"{row['experimentID']}|{float(row['temperature']):g}|{index}",
            mixture,
            "mixture",
            "electrolyte_conductivity",
            row["EIS_conductivity"],
            "S/cm",
            json_conditions(
                temperature=row["temperature"],
                temperature_unit="degC",
                experiment_id=row["experimentID"],
            ),
            spec["record_doi"],
            spec["commit"],
        ))

    spec = sources["calisol-23"]
    data = read_remote_pinned_csv(spec)
    if len(data) != int(spec["n_rows_expected"]):
        raise RuntimeError(
            f"CALiSol row-count mismatch: {len(data)} != {spec['n_rows_expected']}"
        )
    required = ["doi", "k", "T", "c", "salt", "c units", "solvent ratio type"]
    solvent_columns = list(data.columns[data.columns.get_loc("solvent ratio type") + 1 :])
    if data[[column for column in required if column != "k"]].isna().any().any():
        raise RuntimeError("CALiSol identity, composition, or temperature fields contain missing values")
    data.to_sql("raw_calisol23", connection, if_exists="replace", index=False)

    def mixture_token(value: Any) -> str:
        token = re.sub(r"[^A-Za-z0-9_]+", "_", str(value).strip()).strip("_")
        return token or "unknown"

    for index, row in data.iterrows():
        # The source contains one curve-digitization artifact at a negative
        # salt concentration.  Keep it in the raw table but do not invent a
        # normalized formulation identity for a physically invalid mixture.
        if float(row["c"]) < 0:
            continue
        ratio_type = mixture_token(row["solvent ratio type"])
        components = [
            f"SALT_{mixture_token(row['salt'])}:1",
            f"CONC_{mixture_token(row['c units'])}:{float(row['c']):.10g}",
        ]
        components.extend(
            f"SOLV_{mixture_token(column)}_{ratio_type}:{float(row[column]):.10g}"
            for column in solvent_columns
            if pd.notna(row[column]) and float(row[column]) > 0
        )
        source_row = row.get("Unnamed: 0", index)
        add(rows, measurement(
            "calisol-23",
            f"calisol-{int(source_row)}",
            "|".join(components),
            "mixture",
            "electrolyte_conductivity",
            row["k"],
            "mS/cm",
            json_conditions(
                temperature=row["T"],
                temperature_unit="K",
                source_article_doi=row["doi"],
                concentration=row["c"],
                concentration_unit=row["c units"],
                solvent_ratio_type=row["solvent ratio type"],
            ),
            row["doi"],
            spec["commit"],
        ))

    spec = sources["obelix-solid-electrolytes"]
    repo = ensure_source(workdir, spec)
    data = pd.read_csv(repo / spec["data_path"])
    train_ids = set(pd.read_csv(repo / "data" / "train_idx.csv")["ID"].astype(str))
    test_ids = set(pd.read_csv(repo / "data" / "test_idx.csv")["ID"].astype(str))
    data["official_split"] = data["ID"].astype(str).map(lambda value: "train" if value in train_ids else "test" if value in test_ids else "unassigned")
    groups = connected_obelix_groups(data)
    data["source_group"] = data["ID"].astype(str).map(groups)
    data.to_sql("raw_obelix", connection, if_exists="replace", index=False)
    for _, row in data.iterrows():
        add(rows, measurement("obelix-solid-electrolytes", row["ID"], row["Composition"], "formula",
                              "ionic_conductivity", row["Ionic conductivity (S cm-1)"], "S/cm",
                              json_conditions(space_group=row["Space group number"], cif_match=row["CIF"],
                                              official_split=row["official_split"], source_group=row["source_group"]),
                              row["DOI"], spec["commit"]))

    spec = sources["openpoly-benchmark"]
    repo = ensure_source(workdir, spec)
    data = pd.read_csv(repo / spec["data_path"])
    data.to_sql("raw_openpoly", connection, if_exists="replace", index=False)
    for index, row in data.iterrows():
        for prop in data.columns:
            if prop in {"Name", "PSMILES", "PSMILES_2", "PSMILES_4"}:
                continue
            unit_match = re.search(r"\(([^()]*)\)$", prop)
            unit = unit_match.group(1) if unit_match else ""
            add(rows, measurement("openpoly-benchmark", index, row["PSMILES"], "smiles", prop, row[prop], unit,
                                  "{}", row["Name"], spec["commit"]))

    return rows


def build_database(workdir: Path) -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    sources = lock["sources"]
    catalog_entries = {entry["id"]: entry for entry in json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]}
    DB.parent.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="collective-", suffix=".sqlite", delete=False, dir=DB.parent) as tmp:
        tmp_path = Path(tmp.name)
    try:
        connection = sqlite3.connect(tmp_path)
        rows = load_all(workdir, connection, sources)
        connection.execute("DROP TABLE IF EXISTS measurements")
        connection.execute(
            """CREATE TABLE measurements (
               measurement_id INTEGER PRIMARY KEY,
               dataset TEXT NOT NULL,
               source_row_id TEXT NOT NULL,
               material_raw TEXT NOT NULL,
               material_key TEXT,
               material_kind TEXT NOT NULL CHECK(material_kind IN ('formula','smiles','mixture')),
               property TEXT NOT NULL,
               value REAL NOT NULL,
               unit TEXT NOT NULL,
               conditions_json TEXT NOT NULL,
               source_reference TEXT NOT NULL,
               source_commit TEXT NOT NULL,
               quality_flags TEXT NOT NULL
            )"""
        )
        connection.executemany(
            """INSERT INTO measurements (
               dataset,source_row_id,material_raw,material_key,material_kind,property,value,unit,
               conditions_json,source_reference,source_commit,quality_flags
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        connection.execute("DROP TABLE IF EXISTS datasets")
        connection.execute(
            """CREATE TABLE datasets (
               id TEXT PRIMARY KEY, name TEXT, description TEXT, domain TEXT, subdomain TEXT,
               catalog_license TEXT, redistribution_status TEXT, doi TEXT, homepage TEXT,
               source_commit TEXT, n_measurements INTEGER, normalization_status TEXT
            )"""
        )
        for dataset, spec in sources.items():
            entry = catalog_entries.get(spec.get("catalog_id", dataset), {})
            count = connection.execute("SELECT COUNT(*) FROM measurements WHERE dataset=?", (dataset,)).fetchone()[0]
            connection.execute(
                "INSERT INTO datasets VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (dataset, spec.get("name", entry.get("name", dataset)), entry.get("description", ""), entry.get("domain", ""),
                 entry.get("subdomain", ""), entry.get("license", "Unknown"), spec.get("redistribution_status", "unknown"),
                 entry.get("doi", ""), entry.get("homepage_url", ""), spec["commit"], count,
                 spec.get("normalization_status", "included")),
            )
        connection.execute("CREATE INDEX ix_measurements_dataset_property ON measurements(dataset, property)")
        connection.execute("CREATE INDEX ix_measurements_material_key ON measurements(material_key)")
        connection.execute("CREATE INDEX ix_measurements_source_row ON measurements(dataset, source_row_id)")
        connection.execute("CREATE TABLE build_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany("INSERT INTO build_metadata VALUES (?,?)", [
            ("schema_version", "3"),
            ("source_lock_sha256", source_sha256(LOCK)),
            ("row_count", str(len(rows))),
        ])
        connection.commit()
        connection.close()
        os.replace(tmp_path, DB)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        finally:
            raise

    with sqlite3.connect(DB) as connection:
        print(f"database: {DB}")
        print("measurements:", connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0])
        for row in connection.execute("SELECT id,n_measurements,normalization_status FROM datasets ORDER BY id"):
            print(" ", row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, default=Path.home() / ".collective_data_cache")
    parser.add_argument("--query")
    args = parser.parse_args()
    if args.query:
        with sqlite3.connect(DB) as connection:
            for row in connection.execute(args.query):
                print(row)
        return
    build_database(args.workdir.resolve())


if __name__ == "__main__":
    main()
