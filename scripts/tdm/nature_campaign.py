"""Nature-family OA harvest campaign.

Harvests Springer Nature OPEN ACCESS articles (CC-licensed) via the official
OA API, saves the JATS XML privately, then parses each article's
"Data availability" section to extract dataset links (Zenodo, Figshare,
Dryad, Materials Cloud, NOMAD, GitHub, OSF, ...). The extracted LINKS +
metadata are written to scripts/discovered/ as catalog candidates for the
public index - the article XML itself stays in TDM_DATA_DIR.

Free-tier note: Basic API keys reject `journal:"..."` query filters (premium
feature). The harvester detects this and falls back to keyword search with
client-side journal filtering. The `hybrid` mode uses Crossref (fully open)
to enumerate journal articles, so it needs no Springer quota at all.

Usage (on your machine):
    python nature_campaign.py run --topic "perovskite solar cell" --max 10
    python nature_campaign.py preset --max-per-query 15
    python nature_campaign.py hybrid --journal "Nature Materials" --max-per-journal 100
    python nature_campaign.py reparse   # offline re-parse of harvested JATS
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from datetime import date

import common_tdm as T
from springer_client import oa_page, _lic, _slug, OA_JATS

DISCOVERED = os.path.normpath(os.path.join(T.HERE, "..", "discovered"))
SUBDIR = "nature_oa"

REPO_PATTERNS = {
    "Zenodo": r"zenodo\.org/(?:record|records|doi)/[^\s\"<)\]]+",
    "Figshare": r"(?:[a-z]+\.)?figshare\.com/[^\s\"<)\]]+",
    "Dryad": r"datadryad\.org/[^\s\"<)\]]+",
    "OSF": r"osf\.io/[^\s\"<)\]]+",
    "GitHub": r"github\.com/[^\s\"<)\]]+",
    "Materials Cloud": r"(?:archive\.)?materialscloud\.org/[^\s\"<)\]]+",
    "NOMAD": r"nomad-lab\.eu/[^\s\"<)\]]+",
    "Materials Data Facility": r"materialsdatafacility\.org/[^\s\"<)\]]+",
    "Cambridge CCDC": r"ccdc\.cam\.ac\.uk/[^\s\"<)\]]+",
    "PDB": r"rcsb\.org/[^\s\"<)\]]+",
    "GenBank/NCBI": r"ncbi\.nlm\.nih\.gov/[^\s\"<)\]]+",
    "DOI": r"doi\.org/10\.[0-9]{4,9}/[^\s\"<)\]]+",
}

DATA_SEC_RE = re.compile(
    r"<sec[^>]*sec-type=\"data-availability\"[^>]*>(.*?)</sec>"
    r"|<title>\s*(?:Data|Code)\s+[Aa]vailability\s*</title>(.*?)(?=<sec|<title>|</body>)",
    re.S)
TAG_RE = re.compile(r"<[^>]+>")


def parse_jats(xml_text: str) -> dict:
    """Extract data-availability text + repository links from a JATS article."""
    secs = ["".join(m.groups("") or "") for m in DATA_SEC_RE.finditer(xml_text)]
    avail_text = TAG_RE.sub(" ", " ".join(secs))
    avail_text = re.sub(r"\s+", " ", avail_text).strip()[:1200]

    links: dict[str, list[str]] = {}
    scope = " ".join(secs) if secs else xml_text  # prefer availability sections
    for repo, pat in REPO_PATTERNS.items():
        found = sorted(set(re.findall(pat, scope)))
        if not found and secs:  # fall back to whole article for repo domains
            found = sorted(set(re.findall(pat, xml_text)))
        if found:
            links[repo] = ["https://" + u.rstrip(".,;") for u in found[:5]]
    return {"data_availability": avail_text, "dataset_links": links}


def harvest(topic: str, journal: str | None, max_n: int) -> list[dict]:
    key = T.CFG.get("SPRINGER_OA_KEY") or ""
    if not key:
        raise SystemExit("SPRINGER_OA_KEY missing in scripts/tdm/.env")
    q = f'keyword:"{topic}"' + (f' journal:"{journal}"' if journal else "")
    client_filter = None   # set when we fall back to client-side journal filtering
    got, start, scanned, out = 0, 1, 0, []
    seen = _already_harvested()
    while got < max_n and scanned < 400:
        try:
            data = oa_page(q, start, 20, key)
        except RuntimeError as exc:
            if journal and client_filter is None and "premium" in str(exc).lower():
                print("  [notice] journal: filter needs a premium key -> "
                      "falling back to keyword search + client-side journal filter")
                q = f'keyword:"{topic}"'
                client_filter = journal
                start = 1
                continue
            raise
        records = data.get("records", [])
        if not records:
            break
        for rec in records:
            scanned += 1
            doi = rec.get("doi")
            if not doi or doi in seen:
                continue
            if client_filter and (rec.get("publicationName") or "").lower() != client_filter.lower():
                continue
            from springer_client import limiter
            limiter.wait()
            url = f"{OA_JATS}?{T.qs({'q': f'doi:{doi}', 'api_key': key})}"
            xml = T.http_get(url)
            meta = {"doi": doi, "title": rec.get("title"),
                    "journal": rec.get("publicationName"),
                    "date": rec.get("publicationDate"), "license": _lic(rec),
                    "source": "SpringerNature OpenAccess API", "query": q}
            T.save_with_manifest(SUBDIR, _slug(doi) + ".jats.xml", xml, meta)
            parsed = parse_jats(xml.decode("utf-8", "ignore"))
            out.append({**meta, **parsed})
            got += 1
            print(f"[{got}/{max_n}] {doi}  links={list(parsed['dataset_links'])}")
            if got >= max_n:
                break
        start += len(records)
    n_links = sum(1 for r in out if r.get("dataset_links"))
    print(f"  summary: scanned={scanned} harvested={got} with_links={n_links}"
          + (f" (client journal filter: {client_filter})" if client_filter else ""))
    return out


def _already_harvested() -> set:
    seen = set()
    mf = os.path.join(T.CFG.get("TDM_DATA_DIR", ""), SUBDIR, "_manifest.jsonl")
    if os.path.exists(mf):
        with open(mf, encoding="utf-8") as fh:
            for line in fh:
                try:
                    seen.add(json.loads(line).get("doi"))
                except json.JSONDecodeError:
                    pass
    return seen


def write_candidates(results: list[dict], label: str) -> str:
    """Write catalog candidates (metadata + links ONLY - no article content)."""
    os.makedirs(DISCOVERED, exist_ok=True)
    cands = []
    for r in results:
        if not r["dataset_links"]:
            continue
        cands.append({
            "id": _slug(r["doi"]).lower().replace("_", "-"),
            "name": (r.get("title") or "")[:120],
            "description": (r.get("data_availability") or "")[:400],
            "domain": "materials",
            "subdomain": "uncategorized",
            "tags": [],
            "data_type": "experimental",
            "access": "open",
            "license": r.get("license"),
            "doi": r.get("doi"),
            "homepage_url": next(iter(sum(r["dataset_links"].values(), [])), None),
            "repository": " / ".join(r["dataset_links"].keys()),
            "associated_paper": f"{r.get('title','')} ({r.get('journal','')}, {r.get('date','')})",
            "year": int((r.get("date") or "0")[:4]) or None,
            "source": "api-discovery",
            "added": date.today().isoformat(),
            "verified_via": f"https://doi.org/{r['doi']}",
            "_dataset_links_all": r["dataset_links"],
        })
    path = os.path.join(DISCOVERED, f"nature_oa_{label}_{date.today():%Y%m%d}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cands, fh, ensure_ascii=False, indent=2)
    print(f"\n{len(cands)} candidates with dataset links -> {path}")
    print("Review them, fix domain/subdomain/tags, drop '_dataset_links_all',")
    print("then move keepers into scripts/seed/ and rebuild the catalog.")
    return path


# OA-native journals: every article is OA -> full-text harvest works for all
PRESET_JOURNALS = ["Scientific Data", "Nature Communications",
                   "Communications Materials", "Communications Chemistry",
                   "npj Computational Materials", "Scientific Reports"]
# Hybrid flagship journals: only some articles are OA. OA harvest gets those;
# the `hybrid` mode covers ALL articles via Crossref + DataCite back-linking.
PRESET_HYBRID = ["Nature", "Nature Materials", "Nature Chemistry",
                 "Nature Energy", "Nature Nanotechnology", "Nature Catalysis",
                 "Nature Synthesis", "Nature Physics",
                 "Nature Chemical Engineering", "Nature Sustainability"]
PRESET_TOPICS = ["high-throughput experimentation", "combinatorial synthesis",
                 "self-driving laboratory", "autonomous experimentation",
                 "robotic synthesis platform", "closed-loop optimization materials",
                 "automated characterization dataset", "accelerated materials discovery",
                 "high-throughput screening materials", "materials acceleration platform"]

DATACITE = "https://api.datacite.org/dois"
CROSSREF = "https://api.crossref.org/works"
dc_limiter = T.RateLimiter(1.0)


def crossref_journal_recent(journal: str, topic: str | None, max_n: int) -> list[dict]:
    """Enumerate recent journal-articles of a journal via Crossref (open, free)."""
    out: list[dict] = []
    offset = 0
    while len(out) < max_n and offset < 1000:
        params = {"filter": f"container-title:{journal},type:journal-article",
                  "rows": 100,
                  "select": "DOI,title,container-title,published",
                  "sort": "published", "order": "desc",
                  "offset": offset, "mailto": T.CONTACT}
        if topic:
            params["query.bibliographic"] = topic
        dc_limiter.wait()
        data = T.http_get_json(f"{CROSSREF}?{T.qs(params)}")
        items = data.get("message", {}).get("items", [])
        if not items:
            break
        for it in items:
            ct = (it.get("container-title") or [""])[0]
            if ct.lower() != journal.lower():
                continue
            parts = ((it.get("published") or {}).get("date-parts") or [[None]])[0]
            out.append({"doi": it.get("DOI"),
                        "title": (it.get("title") or [""])[0],
                        "date": "-".join(str(p) for p in parts if p)})
            if len(out) >= max_n:
                break
        offset += len(items)
    return out


def datacite_linked_datasets(article_doi: str) -> list[dict]:
    """Datasets in DataCite that declare a relation to this article DOI."""
    dc_limiter.wait()
    q = f'relatedIdentifiers.relatedIdentifier:"{article_doi}"'
    url = f"{DATACITE}?{T.qs({'query': q, 'page[size]': 10, 'resource-type-id': 'dataset'})}"
    try:
        data = T.http_get_json(url)
    except Exception:
        return []
    out = []
    for rec in data.get("data", []):
        a = rec.get("attributes", {})
        titles = a.get("titles") or [{}]
        rights = a.get("rightsList") or [{}]
        pub = a.get("publisher")
        out.append({
            "dataset_doi": a.get("doi"),
            "dataset_title": (titles[0].get("title") or "")[:150],
            "dataset_url": a.get("url") or (f"https://doi.org/{a.get('doi')}" if a.get("doi") else None),
            "repository": pub if isinstance(pub, str) else (pub or {}).get("name"),
            "license": (rights[0].get("rightsIdentifier") or rights[0].get("rights")) if rights else None,
            "year": a.get("publicationYear"),
        })
    return out


def cmd_hybrid(args) -> None:
    """Enumerate articles of hybrid flagship journals via Crossref (free, open
    metadata - includes paywalled articles), then find their deposited
    datasets via DataCite. No Springer API quota used."""
    journals = [args.journal] if args.journal else PRESET_HYBRID
    cands = []
    for j in journals:
        print(f"\n=== {j} ===")
        try:
            articles = crossref_journal_recent(j, args.topic, args.max_per_journal)
        except Exception as exc:
            print(f"  crossref error, skipping journal: {exc}")
            continue
        print(f"  {len(articles)} articles enumerated; checking DataCite back-links...")
        for i, art in enumerate(articles, 1):
            doi = art.get("doi")
            if not doi:
                continue
            hits = datacite_linked_datasets(doi)
            if not hits:
                continue
            # dedupe versioned repository DOIs (e.g. figshare ....v1 / ....v2)
            uniq = {}
            for h in hits:
                k = re.sub(r"\.v\d+$", "", (h.get("dataset_doi") or h["dataset_title"]).lower())
                uniq.setdefault(k, h)
            hits = list(uniq.values())
            # collapse per-structure CCDC deposits into one entry per article
            ccdc = [h for h in hits
                    if "crystallographic data centre" in (h.get("repository") or "").lower()]
            if len(ccdc) > 1:
                agg = dict(ccdc[0])
                agg["dataset_title"] = (f"{len(ccdc)} experimental crystal structures "
                                        f"(CIF) deposited at CCDC")
                agg["dataset_doi"] = None
                agg["dataset_url"] = "https://www.ccdc.cam.ac.uk/structures/"
                hits = [h for h in hits if h not in ccdc] + [agg]
            for h in hits:
                print(f"  [{i}] {doi} -> {h['repository']}: {h['dataset_title'][:60]}")
                cands.append({
                    "id": _slug(h.get("dataset_doi") or doi).lower().replace("_", "-"),
                    "name": h["dataset_title"] or f"Dataset for {art.get('title','')[:80]}",
                    "description": f"Dataset deposited alongside: {art.get('title','')} "
                                   f"({j}, {art.get('date','')}).",
                    "domain": "materials",
                    "subdomain": "uncategorized",
                    "tags": [],
                    "data_type": "experimental",
                    "access": "open",
                    "license": h.get("license"),
                    "doi": h.get("dataset_doi"),
                    "homepage_url": h.get("dataset_url"),
                    "repository": h.get("repository"),
                    "associated_paper": f"{art.get('title','')} ({j}), doi:{doi}",
                    "year": h.get("year"),
                    "source": "api-discovery",
                    "added": date.today().isoformat(),
                    "verified_via": f"https://api.datacite.org/dois?query=relatedIdentifiers.relatedIdentifier:%22{doi}%22",
                })
    os.makedirs(DISCOVERED, exist_ok=True)
    label = _slug(args.journal or "all-flagships")[:30]
    path = os.path.join(DISCOVERED, f"nature_hybrid_{label}_{date.today():%Y%m%d}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(cands, fh, ensure_ascii=False, indent=2)
    print(f"\n{len(cands)} dataset candidates -> {path}")


def cmd_run(args) -> None:
    res = harvest(args.topic, args.journal, args.max)
    write_candidates(res, _slug(args.topic)[:30])


def cmd_preset(args) -> None:
    all_res = []
    for j in ((PRESET_JOURNALS + PRESET_HYBRID) if not args.journal else [args.journal]):
        for t in PRESET_TOPICS:
            print(f"\n=== {j} / {t} ===")
            try:
                all_res.extend(harvest(t, j, args.max_per_query))
            except Exception as exc:
                print(f"  error, moving on: {exc}")
    write_candidates(all_res, "preset")


def cmd_reparse(args) -> None:
    """Re-run link extraction over already-downloaded JATS (offline)."""
    folder = os.path.join(T.data_dir(), SUBDIR)
    results = []
    mf = {}
    mfp = os.path.join(folder, "_manifest.jsonl")
    if os.path.exists(mfp):
        with open(mfp, encoding="utf-8") as fh:
            for line in fh:
                rec = json.loads(line)
                mf[rec["file"]] = rec
    for path in glob.glob(os.path.join(folder, "*.jats.xml")):
        with open(path, encoding="utf-8", errors="ignore") as fh:
            parsed = parse_jats(fh.read())
        meta = mf.get(os.path.basename(path), {"doi": os.path.basename(path)})
        results.append({**meta, **parsed})
    write_candidates(results, "reparse")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run"); p.add_argument("--topic", required=True)
    p.add_argument("--journal", default=None,
                   help="optional journal restriction (on basic keys this filters client-side and costs extra quota)")
    p.add_argument("--max", type=int, default=20); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("preset"); p.add_argument("--journal")
    p.add_argument("--max-per-query", type=int, default=15); p.set_defaults(fn=cmd_preset)
    p = sub.add_parser("hybrid", help="ALL articles of hybrid flagships via Crossref + DataCite back-links")
    p.add_argument("--journal", help="one journal; default: all 10 flagships")
    p.add_argument("--topic", help="optional topic filter")
    p.add_argument("--max-per-journal", type=int, default=100)
    p.set_defaults(fn=cmd_hybrid)
    p = sub.add_parser("reparse"); p.set_defaults(fn=cmd_reparse)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
