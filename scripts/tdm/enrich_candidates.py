"""Enrich + filter discovered candidates for HTE-scale datasets.

Goal: keep only candidates that look like REAL high-throughput / automated
experimentation databases (hundreds+ of measurements), and drop noise such as
single CCDC structures and auto-deposited SI PDFs.

For each candidate whose DOI/URL points to Zenodo or Figshare, this queries
the repository's public API for the actual file list, then scores:

  + data-format files present (.csv .xlsx .zip .h5 .hdf5 .json .mat .npz
    .parquet .db .sqlite .tar .gz .cif-many)      -> strong positive
  + total size (MB)                                -> positive
  + HTE keywords in title/description ("high-throughput", "combinatorial",
    "autonomous", "robotic", "N samples/devices/reactions/compositions")
  - only .pdf/.docx files (auto-deposited SI)      -> strong negative
  - CCDC single-structure deposits                 -> dropped (with --drop-ccdc, default on)

Usage:
    python enrich_candidates.py --input "..\\discovered\\nature_hybrid_Nature_Materials_20260708.json"
    python enrich_candidates.py --input <file> --min-score 3 --keep-ccdc

Output: <input>_enriched.json (sorted by score, includes files/size/signals)
and a console summary table.
"""
from __future__ import annotations

import argparse
import json
import os
import re

import common_tdm as T

limiter = T.RateLimiter(1.2)

DATA_EXTS = {".csv", ".xlsx", ".xls", ".zip", ".h5", ".hdf5", ".json", ".mat",
             ".npz", ".npy", ".parquet", ".db", ".sqlite", ".tar", ".gz",
             ".tsv", ".txt", ".xml", ".pkl", ".feather"}
DOC_EXTS = {".pdf", ".docx", ".doc", ".pptx"}

HTE_RE = re.compile(
    r"high.?throughput|combinatorial|autonomous|self.?driving|robotic|"
    r"closed.?loop|automated (?:synthesis|screening|experiment|characterization)|"
    r"\b\d{2,}[,\d]*\s+(?:samples?|compositions?|compounds?|devices?|reactions?|"
    r"measurements?|materials?|spectra|cells?|formulations?|catalysts?)", re.I)


def zenodo_files(doi_or_url: str) -> list[dict] | None:
    m = re.search(r"zenodo\.(?:org/records?/|\D*?)(\d+)", doi_or_url) or \
        re.search(r"10\.5281/zenodo\.(\d+)", doi_or_url)
    if not m:
        return None
    limiter.wait()
    try:
        data = T.http_get_json(f"https://zenodo.org/api/records/{m.group(1)}")
        return [{"name": f.get("key", ""), "mb": (f.get("size", 0) or 0) / 1e6}
                for f in data.get("files", [])]
    except Exception:
        return None


def figshare_files(doi_or_url: str) -> list[dict] | None:
    m = re.search(r"figshare\.(?:com/articles/(?:[^/]+/)*|\D*?)(\d{6,})", doi_or_url) or \
        re.search(r"10\.6084/m9\.figshare\.(\d+)", doi_or_url)
    if not m:
        return None
    limiter.wait()
    try:
        data = T.http_get_json(f"https://api.figshare.com/v2/articles/{m.group(1)}")
        return [{"name": f.get("name", ""), "mb": (f.get("size", 0) or 0) / 1e6}
                for f in data.get("files", [])]
    except Exception:
        return None


def enrich(cand: dict) -> dict:
    probe = " ".join(str(x) for x in
                     [cand.get("doi"), cand.get("homepage_url")] if x)
    files = zenodo_files(probe)
    if files is None:
        files = figshare_files(probe)
    exts = sorted({os.path.splitext(f["name"])[1].lower() for f in files or []})
    total_mb = round(sum(f["mb"] for f in files or []), 1)
    text = " ".join(str(cand.get(k) or "") for k in
                    ("name", "description", "associated_paper"))
    signals = sorted(set(m.group(0).lower() for m in HTE_RE.finditer(text)))

    has_data = bool(set(exts) & DATA_EXTS)
    only_docs = bool(exts) and set(exts) <= DOC_EXTS
    score = 0.0
    if has_data:
        score += 3
    if only_docs:
        score -= 3          # auto-deposited SI pdf/docx
    score += min(total_mb / 10, 5)
    score += 2 * min(len(signals), 3)
    if files is None:
        score += 0.5 if signals else 0   # unknown repo: rely on text signals

    cand.update({"files_n": len(files) if files is not None else None,
                 "size_mb": total_mb if files is not None else None,
                 "file_exts": exts, "hte_signals": signals,
                 "score": round(score, 1)})
    return cand


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--min-score", type=float, default=3.0)
    ap.add_argument("--keep-ccdc", action="store_true",
                    help="keep CCDC crystal-structure entries (dropped by default)")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        cands = json.load(fh)
    print(f"{len(cands)} candidates loaded")

    NOISE_REPOS = ("crystallographic data centre",  # single crystal structures
                   "hepdata",                        # particle physics
                   "fiz karlsruhe")                  # ICSD single structures
    kept = []
    for c in cands:
        repo = (c.get("repository") or "").lower()
        if not args.keep_ccdc and any(n in repo for n in NOISE_REPOS):
            continue
        c = enrich(c)
        flag = "KEEP" if c["score"] >= args.min_score else "drop"
        print(f"  [{flag}] score={c['score']:>4}  size={c.get('size_mb')}MB "
              f"files={c.get('files_n')}  {c.get('name','')[:60]}")
        if c["score"] >= args.min_score:
            kept.append(c)

    kept.sort(key=lambda c: -c["score"])
    out = os.path.splitext(args.input)[0] + "_enriched.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(kept, fh, ensure_ascii=False, indent=2)
    print(f"\n{len(kept)}/{len(cands)} kept (score >= {args.min_score}) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
