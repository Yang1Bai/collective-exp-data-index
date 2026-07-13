"""Elsevier (ScienceDirect) TDM client.

Uses the official Article Retrieval / ScienceDirect Search APIs
(https://dev.elsevier.com/) under UofT's subscription. Entitlement is
IP-based: run on campus or UofT VPN. Non-commercial research only.
UofT terms: downloaded data must be stored on secure CANADIAN storage.

Examples:
    python elsevier_client.py search --query "perovskite solar cell stability" --max 10
    python elsevier_client.py fulltext --doi 10.1016/j.joule.2019.11.003
    python elsevier_client.py harvest --query "battery electrolyte conductivity" --max 20
"""
from __future__ import annotations

import argparse
import json
import re

import common_tdm as T

SEARCH = "https://api.elsevier.com/content/search/sciencedirect"
ARTICLE = "https://api.elsevier.com/content/article/doi/"

limiter = T.RateLimiter(1.5)


def _headers() -> dict:
    key = T.CFG.get("ELSEVIER_KEY", "")
    if not key:
        raise SystemExit("ELSEVIER_KEY missing - add it to scripts/tdm/.env")
    return {"X-ELS-APIKey": key, "Accept": "application/json"}


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:80].strip("_")


def search(query: str, count: int) -> list[dict]:
    limiter.wait()
    url = f"{SEARCH}?{T.qs({'query': query, 'count': min(count, 25)})}"
    data = T.http_get_json(url, _headers())
    return (data.get("search-results", {}) or {}).get("entry", []) or []


def cmd_search(args) -> None:
    for e in search(args.query, args.max):
        print(f"- {e.get('dc:title','')[:90]}")
        print(f"    doi={e.get('prism:doi')}  {e.get('prism:publicationName','')}  "
              f"{e.get('prism:coverDate','')}  oa={e.get('openaccess')}")


def fetch_fulltext_xml(doi: str) -> bytes:
    limiter.wait()
    url = f"{ARTICLE}{doi}"
    return T.http_get(url, {**_headers(), "Accept": "text/xml"})


def cmd_fulltext(args) -> None:
    xml = fetch_fulltext_xml(args.doi)
    path = T.save_with_manifest(
        "elsevier", _slug(args.doi) + ".xml", xml,
        {"doi": args.doi, "source": "Elsevier Article Retrieval API",
         "terms": "UofT licence: non-commercial research; store on secure "
                  "Canadian storage; do not redistribute; no third-party AI platforms"})
    print("saved:", path)


def cmd_harvest(args) -> None:
    entries = search(args.query, args.max)
    got = 0
    for e in entries:
        doi = e.get("prism:doi")
        if not doi:
            continue
        try:
            xml = fetch_fulltext_xml(doi)
        except Exception as exc:
            print(f"  skip {doi}: {exc}")
            continue
        T.save_with_manifest(
            "elsevier", _slug(doi) + ".xml", xml,
            {"doi": doi, "title": e.get("dc:title"),
             "journal": e.get("prism:publicationName"),
             "date": e.get("prism:coverDate"),
             "source": "Elsevier Article Retrieval API",
             "terms": "UofT licence: non-commercial research; secure Canadian "
                      "storage; no redistribution; no third-party AI platforms"})
        got += 1
        print(f"[{got}] {doi}")
    print(f"done - {got} articles -> TDM_DATA_DIR/elsevier/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("search"); p.add_argument("--query", required=True)
    p.add_argument("--max", type=int, default=10); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("fulltext"); p.add_argument("--doi", required=True)
    p.set_defaults(fn=cmd_fulltext)
    p = sub.add_parser("harvest"); p.add_argument("--query", required=True)
    p.add_argument("--max", type=int, default=10); p.set_defaults(fn=cmd_harvest)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
