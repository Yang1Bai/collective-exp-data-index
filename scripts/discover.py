"""Discover candidate datasets from open scholarly APIs.

This is the *legitimate* alternative to scraping publisher HTML. It queries
open metadata/repository APIs that explicitly allow programmatic access and
returns normalized candidate records for human review. It does NOT download
copyrighted supporting-information files or bypass any access controls.

Supported sources:
  - zenodo      https://developers.zenodo.org/         (records API)
  - figshare    https://docs.figshare.com/             (articles search)
  - datacite    https://support.datacite.org/docs/api  (DOI metadata, type=Dataset)
  - openalex    https://docs.openalex.org/             (works, type=dataset)
  - materialscloud  https://archive.materialscloud.org (OPTIMADE / entries)

Usage:
    python scripts/discover.py --source zenodo   --query "perovskite solar cell" --limit 25
    python scripts/discover.py --source datacite --query "electrolyte conductivity" --limit 25
    python scripts/discover.py --source all       --query "high throughput experiment" --limit 15

Output goes to scripts/discovered/<source>_<timestamp>.json as an array of
candidate entries in the catalog schema (source="api-discovery"). Review,
edit, and move accepted entries into a seed file or directly into catalog.json,
then run build_exports.py + validate_catalog.py.

Etiquette: set a descriptive User-Agent with a contact email, keep --limit
modest, and respect each API's rate limits. Some APIs (e.g. OpenAlex) reward a
`mailto` with faster "polite pool" access.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, date
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import common

CONTACT = os.environ.get("INDEX_CONTACT_EMAIL", "you@example.org")
USER_AGENT = f"CollectiveExpDataIndex/0.1 (mailto:{CONTACT})"
OUT_DIR = os.path.join(common.HERE, "discovered")


def _get_json(url: str, timeout: int = 30) -> dict:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:60] or "untitled"


def _candidate(**kw) -> dict:
    e = {
        "id": kw.get("id") or _slug(kw.get("name", "")),
        "name": kw.get("name", "").strip(),
        "description": (kw.get("description") or "").strip()[:600],
        "domain": kw.get("domain", "materials"),
        "subdomain": kw.get("subdomain", "uncategorized"),
        "tags": kw.get("tags", []),
        "data_type": kw.get("data_type", "experimental"),
        "access": kw.get("access", "open"),
        "license": kw.get("license"),
        "doi": kw.get("doi"),
        "homepage_url": kw.get("homepage_url"),
        "repository": kw.get("repository"),
        "associated_paper": kw.get("associated_paper"),
        "year": kw.get("year"),
        "source": "api-discovery",
        "added": date.today().isoformat(),
        "verified_via": kw.get("homepage_url"),
    }
    return e


# --- source adapters --------------------------------------------------------

def from_zenodo(query: str, limit: int) -> list[dict]:
    params = {"q": query, "size": limit, "type": "dataset", "sort": "mostrecent"}
    url = "https://zenodo.org/api/records?" + urlencode(params)
    data = _get_json(url)
    out = []
    for hit in data.get("hits", {}).get("hits", []):
        meta = hit.get("metadata", {})
        lic = (meta.get("license") or {})
        out.append(_candidate(
            name=meta.get("title", ""),
            description=re.sub("<[^>]+>", "", meta.get("description", "")),
            doi=hit.get("doi") or meta.get("doi"),
            homepage_url=hit.get("links", {}).get("self_html") or f"https://doi.org/{hit.get('doi','')}",
            repository="Zenodo",
            license=lic.get("id") if isinstance(lic, dict) else lic,
            year=int(meta.get("publication_date", "0")[:4]) if meta.get("publication_date") else None,
            tags=[k.get("term", k) if isinstance(k, dict) else k for k in meta.get("keywords", []) or []][:8],
        ))
    return out


def from_figshare(query: str, limit: int) -> list[dict]:
    # Figshare search is a POST; use the simple GET article list with search_for.
    params = {"search_for": query, "page_size": limit, "item_type": 3}  # 3 = dataset
    url = "https://api.figshare.com/v2/articles?" + urlencode(params)
    data = _get_json(url)
    out = []
    for art in data if isinstance(data, list) else []:
        out.append(_candidate(
            name=art.get("title", ""),
            description=art.get("description") or art.get("title", ""),
            doi=art.get("doi"),
            homepage_url=art.get("url_public_html") or art.get("url"),
            repository="Figshare",
            year=int(art.get("published_date", "0")[:4]) if art.get("published_date") else None,
        ))
    return out


def from_datacite(query: str, limit: int) -> list[dict]:
    params = {"query": query, "resource-type-id": "dataset", "page[size]": limit}
    url = "https://api.datacite.org/dois?" + urlencode(params)
    data = _get_json(url)
    out = []
    for rec in data.get("data", []):
        a = rec.get("attributes", {})
        titles = a.get("titles") or [{}]
        descs = a.get("descriptions") or [{}]
        rights = a.get("rightsList") or [{}]
        out.append(_candidate(
            name=(titles[0].get("title") if titles else "") or "",
            description=(descs[0].get("description") if descs else "") or "",
            doi=a.get("doi"),
            homepage_url=a.get("url") or (f"https://doi.org/{a.get('doi')}" if a.get("doi") else None),
            repository=(a.get("publisher") if isinstance(a.get("publisher"), str)
                        else (a.get("publisher", {}) or {}).get("name")),
            license=(rights[0].get("rightsIdentifier") or rights[0].get("rights")) if rights else None,
            year=a.get("publicationYear"),
        ))
    return out


def from_openalex(query: str, limit: int) -> list[dict]:
    params = {
        "search": query,
        "filter": "type:dataset",
        "per-page": min(limit, 50),
        "mailto": CONTACT,
    }
    url = "https://api.openalex.org/works?" + urlencode(params)
    data = _get_json(url)
    out = []
    for w in data.get("results", []):
        out.append(_candidate(
            name=w.get("title") or w.get("display_name", ""),
            description=w.get("abstract_inverted_index") and "(abstract available via OpenAlex)" or "",
            doi=(w.get("doi") or "").replace("https://doi.org/", "") or None,
            homepage_url=w.get("doi") or w.get("id"),
            repository=(w.get("primary_location", {}) or {}).get("source", {}) and
                       ((w.get("primary_location", {}) or {}).get("source", {}) or {}).get("display_name"),
            year=w.get("publication_year"),
        ))
    return out


def from_materialscloud(query: str, limit: int) -> list[dict]:
    # Materials Cloud Archive exposes an entries endpoint.
    url = "https://archive.materialscloud.org/api/records?" + urlencode(
        {"q": query, "size": limit})
    try:
        data = _get_json(url)
    except Exception as exc:  # endpoint shape changes occasionally
        print(f"  materialscloud: {exc}")
        return []
    out = []
    for hit in data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []:
        meta = hit.get("metadata", hit)
        out.append(_candidate(
            name=meta.get("title", ""),
            description=meta.get("description", ""),
            doi=meta.get("doi"),
            homepage_url=meta.get("doi") and f"https://doi.org/{meta.get('doi')}",
            repository="Materials Cloud",
            year=None,
        ))
    return out


SOURCES = {
    "zenodo": from_zenodo,
    "figshare": from_figshare,
    "datacite": from_datacite,
    "openalex": from_openalex,
    "materialscloud": from_materialscloud,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, choices=list(SOURCES) + ["all"])
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--domain", default="materials", choices=["materials", "chemistry"],
                    help="tag candidates with this primary domain (default: materials)")
    args = ap.parse_args()

    sources = list(SOURCES) if args.source == "all" else [args.source]
    all_hits: list[dict] = []
    for src in sources:
        print(f"[{src}] query='{args.query}' limit={args.limit}")
        try:
            hits = SOURCES[src](args.query, args.limit)
        except Exception as exc:
            print(f"  error: {exc}")
            continue
        for h in hits:
            h["domain"] = args.domain
        print(f"  -> {len(hits)} candidates")
        all_hits.extend(hits)
        time.sleep(1)  # be polite between sources

    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(OUT_DIR, f"{args.source}_{stamp}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(all_hits, fh, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(all_hits)} candidates -> {os.path.relpath(out_path, common.ROOT)}")
    print("Review, edit, and promote accepted entries into scripts/seed/ or catalog.json,")
    print("then run: python scripts/build_exports.py && python scripts/validate_catalog.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
