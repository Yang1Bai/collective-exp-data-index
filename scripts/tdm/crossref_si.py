"""Find articles that HAVE supplementary/associated data via Crossref.

Crossref metadata is fully open (no key needed; polite pool via mailto).
This is the discovery step before any publisher-API harvesting: it tells you
WHICH DOIs are worth fetching, and which have linked datasets you can get
from repositories instead of publisher SI.

Examples:
    # articles mentioning a topic that declare a data/SI relation
    python crossref_si.py --query "perovskite solar cell dataset" --max 20

    # restrict to a publisher prefix (10.1038 Nature, 10.1021 ACS, 10.1039 RSC,
    # 10.1002 Wiley, 10.1126 Science, 10.1016 Elsevier)
    python crossref_si.py --query "high entropy alloy" --prefix 10.1038 --max 20
"""
from __future__ import annotations

import argparse

import common_tdm as T

API = "https://api.crossref.org/works"
limiter = T.RateLimiter(1.0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", required=True)
    ap.add_argument("--prefix", help="DOI prefix filter, e.g. 10.1038")
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args()

    filters = ["type:journal-article"]
    if args.prefix:
        filters.append(f"prefix:{args.prefix}")
    params = {
        "query": args.query,
        "filter": ",".join(filters),
        "rows": min(args.max, 100),
        "select": "DOI,title,container-title,published,relation,link,license",
        "mailto": T.CONTACT,
    }
    limiter.wait()
    data = T.http_get_json(f"{API}?{T.qs(params)}")
    items = data.get("message", {}).get("items", [])
    print(f"{len(items)} results\n")
    for it in items:
        doi = it.get("DOI")
        title = (it.get("title") or [""])[0][:90]
        rel = it.get("relation") or {}
        # relations that indicate associated data/SI
        data_rels = {k: len(v) for k, v in rel.items()
                     if k in ("has-supplement", "is-supplemented-by",
                              "has-part", "references-dataset", "is-referenced-by")}
        lic = ";".join(sorted({(l.get("URL") or "")[:60] for l in it.get("license", [])})) or "-"
        print(f"- {title}")
        print(f"    doi={doi}  journal={(it.get('container-title') or ['-'])[0][:40]}")
        print(f"    data-relations={data_rels or 'none declared'}  license={lic}")


if __name__ == "__main__":
    main()
