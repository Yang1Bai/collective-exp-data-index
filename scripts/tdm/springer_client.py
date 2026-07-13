"""Springer Nature API client (Open Access + Meta APIs).

Uses the official developer APIs (https://dev.springernature.com/) under the
UofT institutional entitlement. Non-commercial research use only.

- Open Access API: full text (JATS XML or JSON) of OA articles - these are
  CC-licensed, the least restricted content.
- Meta API: metadata/abstracts across all Springer Nature content (no full text).

Examples (run on your machine, on campus or UofT VPN):
    # smoke test: 3 OA hits about perovskite solar cells
    python springer_client.py search --query "perovskite solar cell" --max 3

    # download OA full-text JATS for a query into TDM_DATA_DIR/springer_oa/
    python springer_client.py harvest --query "perovskite solar cell stability" --max 25

    # metadata only (Meta API) - counts and DOIs, no download
    python springer_client.py meta --query "high entropy alloy" --max 10
"""
from __future__ import annotations

import argparse
import json
import re

import common_tdm as T

OA_JSON = "https://api.springernature.com/openaccess/json"
OA_JATS = "https://api.springernature.com/openaccess/jats"
META_JSON = "https://api.springernature.com/meta/v2/json"

limiter = T.RateLimiter(2.0)  # 1 request / 2 s


def _key(name: str) -> str:
    k = T.CFG.get(name, "")
    if not k:
        raise SystemExit(f"{name} missing - add it to scripts/tdm/.env")
    return k


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s)[:80].strip("_")


def oa_page(query: str, start: int, page: int, key: str) -> dict:
    limiter.wait()
    url = f"{OA_JSON}?{T.qs({'q': query, 's': start, 'p': page, 'api_key': key})}"
    return T.http_get_json(url)


def cmd_search(args) -> None:
    key = _key("SPRINGER_OA_KEY")
    data = oa_page(args.query, 1, min(args.max, 20), key)
    total = data.get("result", [{}])[0].get("total", "?")
    print(f"total OA hits: {total}\n")
    for rec in data.get("records", [])[: args.max]:
        print(f"- {rec.get('title','')[:90]}")
        print(f"    doi={rec.get('doi')}  {rec.get('publicationName','')}  "
              f"{rec.get('publicationDate','')}  license={_lic(rec)}")


def _lic(rec: dict) -> str:
    oa = rec.get("openaccess") or {}
    lic = oa.get("license") if isinstance(oa, dict) else None
    return lic or rec.get("copyright", "OA")


def cmd_harvest(args) -> None:
    """Download OA full text as JATS XML, one file per article, with manifest."""
    key = _key("SPRINGER_OA_KEY")
    got, start = 0, 1
    while got < args.max:
        page = min(20, args.max - got)
        data = oa_page(args.query, start, page, key)
        records = data.get("records", [])
        if not records:
            break
        for rec in records:
            doi = rec.get("doi")
            if not doi:
                continue
            limiter.wait()
            url = f"{OA_JATS}?{T.qs({'q': f'doi:{doi}', 'api_key': key})}"
            xml = T.http_get(url)
            name = _slug(doi) + ".jats.xml"
            T.save_with_manifest(
                "springer_oa", name, xml,
                {"doi": doi, "title": rec.get("title"),
                 "journal": rec.get("publicationName"),
                 "date": rec.get("publicationDate"),
                 "license": _lic(rec),
                 "source": "SpringerNature OpenAccess API",
                 "terms": "OA content; check per-article CC license in manifest"})
            got += 1
            print(f"[{got}/{args.max}] {doi}")
            if got >= args.max:
                break
        start += len(records)
    print(f"done - {got} articles -> TDM_DATA_DIR/springer_oa/")


def cmd_meta(args) -> None:
    key = T.CFG.get("SPRINGER_META_KEY") or _key("SPRINGER_OA_KEY")
    limiter.wait()
    url = f"{META_JSON}?{T.qs({'q': args.query, 's': 1, 'p': min(args.max,20), 'api_key': key})}"
    data = T.http_get_json(url)
    total = data.get("result", [{}])[0].get("total", "?")
    print(f"total hits (all SN content): {total}\n")
    for rec in data.get("records", [])[: args.max]:
        print(f"- {rec.get('title','')[:90]}")
        print(f"    doi={rec.get('doi')}  {rec.get('publicationName','')}  "
              f"openaccess={rec.get('openaccess')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in [("search", cmd_search), ("harvest", cmd_harvest), ("meta", cmd_meta)]:
        p = sub.add_parser(name)
        p.add_argument("--query", required=True)
        p.add_argument("--max", type=int, default=10)
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
