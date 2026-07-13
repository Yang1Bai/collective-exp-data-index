"""Generate human/spreadsheet-friendly exports from catalog/catalog.json.

Writes:
  - catalog/catalog.csv   (flat table for Excel / pandas)
  - CATALOG.md            (browsable index grouped by domain > subdomain)
  - catalog_map.html      (interactive similarity map, via build_map.py)

Run after any change to catalog.json:
    python scripts/build_exports.py
"""
from __future__ import annotations

from collections import defaultdict

import common


def _md_link(text: str, url: str | None) -> str:
    return f"[{text}]({url})" if url else text


def build_markdown(catalog: dict) -> str:
    entries = common.entries_of(catalog)
    by_domain: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for e in entries:
        by_domain[e["domain"]][e["subdomain"]].append(e)

    n_exp = sum(1 for e in entries if e["data_type"] == "experimental")
    n_mixed = sum(1 for e in entries if e["data_type"] == "mixed")
    n_comp = sum(1 for e in entries if e["data_type"] == "computational")

    out: list[str] = []
    out.append("# Catalog\n")
    out.append(
        f"_{catalog.get('entry_count', len(entries))} databases · "
        f"updated {catalog.get('updated', 'n/a')} · "
        f"{n_exp} experimental · {n_mixed} mixed · {n_comp} computational_\n"
    )
    out.append(
        "> This is a metadata index. Each entry links to the dataset at its "
        "original home; nothing is re-hosted here. `data_type` marks whether the "
        "underlying data is measured (**experimental**), simulated "
        "(**computational**), or **mixed**. Purely computational databases are "
        "excluded by policy (see catalog/excluded_computational.json).\n"
    )
    out.append("> Legend: 🧪 experimental · 🧮 computational · 🔀 mixed · "
               "🔓 open · 🔑 registration · 🔒 restricted\n")

    type_icon = {"experimental": "🧪", "computational": "🧮", "mixed": "🔀"}
    access_icon = {"open": "🔓", "registration": "🔑", "restricted": "🔒"}

    # Table of contents
    out.append("## Contents\n")
    for domain in sorted(by_domain):
        out.append(f"- **{domain.capitalize()}**")
        for sub in sorted(by_domain[domain]):
            label = common.SUBDOMAIN_LABELS.get(sub, sub)
            anchor = f"{domain}-{sub}".replace(" ", "-")
            out.append(f"  - [{label}](#{anchor}) ({len(by_domain[domain][sub])})")
    out.append("")

    for domain in sorted(by_domain):
        out.append(f"\n## {domain.capitalize()}\n")
        for sub in sorted(by_domain[domain]):
            label = common.SUBDOMAIN_LABELS.get(sub, sub)
            anchor = f"{domain}-{sub}".replace(" ", "-")
            out.append(f'<a id="{anchor}"></a>')
            out.append(f"### {label}\n")
            for e in sorted(by_domain[domain][sub], key=lambda x: x["name"].lower()):
                ti = type_icon.get(e["data_type"], "")
                ai = access_icon.get(e["access"], "")
                link = _md_link(e["name"], e.get("homepage_url"))
                meta = []
                if e.get("year"):
                    meta.append(str(e["year"]))
                if e.get("license"):
                    meta.append(e["license"])
                if e.get("repository"):
                    meta.append(e["repository"])
                doi = common.doi_url(e.get("doi"))
                out.append(f"#### {ti}{ai} {link}")
                out.append("")
                out.append(e["description"])
                out.append("")
                bits = [f"`{e['data_type']}`", f"`{e['access']}`"]
                if meta:
                    bits.append(" · ".join(meta))
                if doi:
                    bits.append(f"DOI: [{e['doi']}]({doi})")
                if e.get("tags"):
                    bits.append("tags: " + ", ".join(f"`{t}`" for t in e["tags"]))
                out.append("· ".join(bits))
                out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    catalog = common.load_catalog()
    entries = common.entries_of(catalog)

    common.write_csv(entries)
    print(f"Wrote {len(entries)} rows -> catalog/catalog.csv")

    md = build_markdown(catalog)
    with open(common.CATALOG_MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"Wrote CATALOG.md ({len(md)} chars)")

    try:  # regenerate the interactive similarity map alongside the exports
        import build_map
        build_map.main()
    except Exception as exc:
        print(f"[warn] catalog_map.html not regenerated: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
