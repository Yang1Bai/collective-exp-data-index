"""Shared helpers for the Collective Experimental Data Index.

Pure-stdlib so the core tooling runs anywhere. The discovery script
(discover.py) additionally uses `requests` if available but falls back
to urllib.
"""
from __future__ import annotations

import csv
import json
import os
from datetime import date

# Paths (repo-root relative) -------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CATALOG_DIR = os.path.join(ROOT, "catalog")
CATALOG_JSON = os.path.join(CATALOG_DIR, "catalog.json")
CATALOG_CSV = os.path.join(CATALOG_DIR, "catalog.csv")
SCHEMA_JSON = os.path.join(CATALOG_DIR, "schema.json")
CATALOG_MD = os.path.join(ROOT, "CATALOG.md")
SEED_DIR = os.path.join(HERE, "seed")

# Canonical field order for CSV / stable JSON -------------------------------
FIELDS = [
    "id", "name", "description", "domain", "subdomain", "tags",
    "data_type", "access", "license", "doi", "homepage_url",
    "repository", "associated_paper", "year", "source", "added", "verified_via",
]

SUBDOMAIN_LABELS = {
    "general-properties": "General materials properties",
    "crystallography": "Crystallography",
    "catalysis": "Catalysis",
    "batteries": "Batteries & energy storage",
    "photovoltaics": "Photovoltaics & solar cells",
    "superconductors": "Superconductors",
    "thermoelectrics": "Thermoelectrics",
    "2d-materials": "2D materials",
    "high-throughput-exp": "High-throughput experimental",
    "benchmark-ml": "ML benchmark datasets",
    "reactions": "Reaction data",
    "molecular-properties": "Molecular properties",
    "bioactivity": "Bioactivity & screening",
    "spectroscopy": "Spectroscopy",
    "quantum-chem": "Quantum chemistry",
    "hte-synthesis": "HTE / synthesis",
    "polymers": "Polymers",
    "mofs-porous": "MOFs & porous materials",
    "glasses": "Glasses",
    "alloys-mechanical": "Alloys & mechanical properties",
    "spectra-exp": "Experimental spectra (XPS/Raman/XRD)",
    "magnetic": "Magnetic materials",
    "organic-electronics": "Organic electronics",
    "thermophysical": "Thermophysical properties",
    "additive-manufacturing": "Additive manufacturing",
    "solubility": "Solubility",
    "physical-properties": "Physical properties",
    "pka": "pKa / dissociation constants",
    "solvation": "Solvation",
    "electrochemistry": "Electrochemistry & redox",
    "optical-properties": "Optical properties & chromophores",
    "kinetics": "Reaction kinetics",
    "thermochemistry": "Thermochemistry",
    "ionic-liquids": "Ionic liquids",
    "membranes": "Membranes & separations",
    "nanomaterials": "Nanomaterials & nanosafety",
    "sdl-benchmarks": "Self-driving-lab benchmarks",
    "electrocatalysis-exp": "Electrocatalysis (experimental HTE)",
    "data-infrastructure": "Data infrastructure & portals",
    "lab-automation": "Lab automation & robotic chemistry",
}


def load_catalog(path: str = CATALOG_JSON) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def entries_of(catalog: dict) -> list:
    return catalog.get("entries", []) if isinstance(catalog, dict) else catalog


def save_catalog(catalog: dict, path: str = CATALOG_JSON) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def doi_url(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    if doi.lower().startswith("http"):
        return doi
    return f"https://doi.org/{doi}"


def normalize_entry(raw: dict) -> dict:
    """Ensure an entry has all canonical fields and sane defaults."""
    e = dict(raw)
    e.setdefault("tags", [])
    e.setdefault("license", None)
    e.setdefault("doi", None)
    e.setdefault("repository", None)
    e.setdefault("associated_paper", None)
    e.setdefault("year", None)
    e.setdefault("source", "curated-seed")
    e.setdefault("added", date.today().isoformat())
    # Do not manufacture verification evidence from the homepage. Discovery
    # candidates may leave this null until a curator records the inspected URL.
    e.setdefault("verified_via", None)
    # keep only known fields, in canonical order
    return {k: e.get(k) for k in FIELDS}


def dedupe(entries: list) -> tuple[list, list]:
    """Dedupe by id (first wins), then flag duplicate DOIs. Returns (kept, warnings)."""
    seen_ids: dict[str, dict] = {}
    warnings: list[str] = []
    for e in entries:
        eid = e["id"]
        if eid in seen_ids:
            warnings.append(f"duplicate id '{eid}' - keeping first occurrence")
            continue
        seen_ids[eid] = e
    kept = list(seen_ids.values())

    seen_doi: dict[str, str] = {}
    for e in kept:
        d = (e.get("doi") or "").lower()
        if d and d in seen_doi:
            warnings.append(f"duplicate DOI '{d}' on '{e['id']}' and '{seen_doi[d]}'")
        elif d:
            seen_doi[d] = e["id"]
    return kept, warnings


def write_csv(entries: list, path: str = CATALOG_CSV) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for e in entries:
            row = []
            for k in FIELDS:
                v = e.get(k)
                if isinstance(v, list):
                    v = "; ".join(v)
                row.append("" if v is None else v)
            w.writerow(row)
