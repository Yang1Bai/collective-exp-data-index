"""Build the collaborator-facing database guide.

The project has two intentionally different inventories:

* ``catalog/catalog.json`` is the broad experimental-resource discovery index.
* ``research/data/ANALYSED_RESOURCE_LEDGER.csv`` records resources that entered
  an audit, model, control, readiness screen, or AI-generated research path.

This script joins the two without pretending that catalog presence means paper
use or that every task-specific subset is an independent upstream database.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

try:
    from . import common
except ImportError:  # direct script execution
    import common


ROOT = Path(common.ROOT)
LEDGER_PATH = ROOT / "research" / "data" / "ANALYSED_RESOURCE_LEDGER.csv"
OUTPUT_PATH = ROOT / "research" / "data" / "DATABASE_GUIDE.md"


def _escape(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _link(label: str, url: str | None) -> str:
    label = _escape(label)
    return f"[{label}]({url})" if url else label


def _load_ledger() -> list[dict[str, str]]:
    with LEDGER_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_guide() -> str:
    catalog = common.entries_of(common.load_catalog())
    ledger = _load_ledger()
    catalog_ids = {entry["id"] for entry in catalog}
    overlap = [row for row in ledger if row["resource_id"] in catalog_ids]
    task_specific = [row for row in ledger if row["resource_id"] not in catalog_ids]
    union_count = len(catalog_ids | {row["resource_id"] for row in ledger})

    data_types = Counter(entry["data_type"] for entry in catalog)
    access = Counter(entry["access"] for entry in catalog)
    unknown_licences = sum(
        str(entry.get("license") or "").lower() == "unknown" for entry in catalog
    )
    missing_evidence = sum(not entry.get("verified_via") for entry in catalog)
    homepage_evidence = sum(
        entry.get("verified_via") == entry.get("homepage_url") for entry in catalog
    )

    by_subdomain: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for entry in catalog:
        by_subdomain[(entry["domain"], entry["subdomain"])].append(entry)

    by_project_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ledger:
        by_project_domain[row["domain"]].append(row)

    out: list[str] = []
    out.append("# Database guide")
    out.append("")
    out.append(
        "This page is the collaborator-facing map of every database or data "
        "resource currently connected to the project. It is generated from the "
        "broad discovery catalog and the analysed-resource ledger; edit those "
        "source files rather than this page."
    )
    out.append("")
    out.append("## Scope accounting")
    out.append("")
    out.append("| Inventory | Records | Meaning |")
    out.append("|---|---:|---|")
    out.append(
        f"| Broad discovery catalog | {len(catalog)} | Experimental or mixed "
        "resources curated for scientific scope, access, licence, provenance, "
        "and an original-home link |"
    )
    out.append(
        f"| Analysed-resource ledger | {len(ledger)} | Resources that entered an "
        "audit, donor or recipient model, control, readiness screen, or "
        "AI-generated research path |"
    )
    out.append(
        f"| Exact overlap | {len(overlap)} | Analysed resources already present "
        "under the same identifier in the broad catalog |"
    )
    out.append(
        f"| Task-specific additions | {len(task_specific)} | Project resources, "
        "subsets, extensions, or external recipients not represented by the "
        "same identifier in the broad catalog |"
    )
    out.append(
        f"| Union of project resource identifiers | {union_count} | Index records, "
        "not necessarily physically independent archives |"
    )
    out.append("")
    out.append(
        "A resource can be catalogued without being analysed, analysed without "
        "supporting a positive transfer edge, or represented by a task-specific "
        "subset of a larger upstream archive. These distinctions are retained "
        "rather than collapsed into one inflated database count."
    )
    out.append("")
    out.append("## Broad catalog at a glance")
    out.append("")
    out.append(
        f"The catalog contains **{data_types['experimental']} experimental** and "
        f"**{data_types['mixed']} mixed experimental/computational** resources. "
        f"Access is recorded as **{access['open']} open**, "
        f"**{access['registration']} registration-gated**, and "
        f"**{access['restricted']} restricted**. **{unknown_licences}** records "
        "have an unresolved data licence. Open access must not be interpreted as "
        "permission to redistribute."
    )
    out.append("")
    out.append(
        "Every broad-catalog entry has a one-paragraph scientific summary, "
        "domain and subdomain, data type, access route, licence, source link, "
        "and DOI where available in the [full catalog](../../CATALOG.md)."
    )
    out.append("")
    out.append("### Metadata limitations")
    out.append("")
    out.append(
        f"- **{unknown_licences} licences remain unresolved.** Those entries "
        "must not be described as openly licensed or redistributed without an "
        "upstream rights check."
    )
    out.append(
        f"- **{homepage_evidence} entries currently use the resource homepage "
        "as the curator evidence URL.** This records where the metadata was "
        "checked, but it is not an independent live-link or file-level audit."
    )
    if missing_evidence:
        out.append(
            f"- **{missing_evidence} entries lack a curator evidence URL.** "
            "These records require verification before publication use."
        )
    out.append(
        "- Repository-scale resources can contain files under different "
        "licences and versions. The entry-level licence is a discovery aid, not "
        "a substitute for checking the exact downloaded file."
    )
    out.append(
        "- Dataset sizes and repository contents can change after this snapshot; "
        "claim-bearing analyses use pinned commits, hashes, or archived records "
        "where available."
    )
    out.append("")
    out.append("### Scientific coverage")
    out.append("")
    out.append("| Domain | Scientific family | Resources | Examples |")
    out.append("|---|---|---:|---|")
    for (domain, subdomain), entries in sorted(by_subdomain.items()):
        label = common.SUBDOMAIN_LABELS.get(subdomain, subdomain)
        anchor = f"{domain}-{subdomain}".replace(" ", "-")
        examples = ", ".join(
            _link(entry["name"], entry.get("homepage_url"))
            for entry in sorted(entries, key=lambda item: item["name"].lower())[:3]
        )
        if len(entries) > 3:
            examples += f", [and {len(entries) - 3} more](../../CATALOG.md#{anchor})"
        out.append(
            f"| {_escape(domain.capitalize())} | "
            f"[{_escape(label)}](../../CATALOG.md#{anchor}) | {len(entries)} | "
            f"{examples} |"
        )

    out.append("")
    out.append("## Resources used or audited in this project")
    out.append("")
    out.append(
        "The following resources materially entered the research process. "
        "`Disposition` records their scientific role in this project; it is not "
        "a quality judgement on the upstream database."
    )
    for domain in sorted(by_project_domain):
        out.append("")
        out.append(f"### {domain.capitalize()}")
        out.append("")
        out.append(
            "| Resource | Project role | Disposition | What it contributed | "
            "Access and licence |"
        )
        out.append("|---|---|---|---|---|")
        for row in sorted(by_project_domain[domain], key=lambda item: item["resource_name"].lower()):
            resource = _link(row["resource_name"], row.get("primary_url"))
            access_licence = f"{_escape(row['access'])}; {_escape(row['upstream_license'])}"
            if row.get("doi"):
                doi = _escape(row["doi"])
                access_licence += f"; [DOI](https://doi.org/{doi})"
            out.append(
                f"| {resource} | {_escape(row['project_role'])} | "
                f"{_escape(row['project_disposition'])} | {_escape(row['notes'])} | "
                f"{access_licence} |"
            )

    out.append("")
    out.append("## Task-specific resources outside the broad catalog")
    out.append("")
    out.append(
        "These records are included in the analysed-resource ledger but do not "
        "share an identifier with the broad catalog. Some are experiment-specific "
        "subsets or extensions rather than standalone general-purpose databases."
    )
    out.append("")
    out.append("| Resource | Domain | Why it entered the project | Disposition |")
    out.append("|---|---|---|---|")
    for row in sorted(task_specific, key=lambda item: (item["domain"], item["resource_name"].lower())):
        out.append(
            f"| {_link(row['resource_name'], row.get('primary_url'))} | "
            f"{_escape(row['domain'])} | {_escape(row['notes'])} | "
            f"{_escape(row['project_disposition'])} |"
        )

    out.append("")
    out.append("## How to interpret project status")
    out.append("")
    out.append("- **Main positive**: supports a claim-bearing prediction or screening result.")
    out.append("- **Main boundary**: defines where an unchanged borrowing route fails or abstains.")
    out.append("- **Supplementary positive**: informative evidence that does not lead the paper.")
    out.append("- **Null, harmful, or non-evaluable**: retained evidence against selective reporting.")
    out.append("- **Control or audit-only**: tests specificity, leakage, readiness, or artefacts.")
    out.append("")
    out.append(
        "Edge-level outcomes are recorded separately in the "
        "[attempt ledger](../evidence/ATTEMPT_LEDGER.csv), because one database "
        "can be useful for one endpoint and harmful for another."
    )
    out.append("")
    out.append("## Data access and redistribution")
    out.append("")
    out.append(
        "Third-party raw files are not mirrored here by default. The "
        "[analysed-resource ledger](ANALYSED_RESOURCE_LEDGER.csv) records the "
        "primary URL, DOI, access route, upstream licence, and repository "
        "redistribution decision. The repository retains source-pinned metadata, "
        "analysis code, compact derived summaries, hashes, and small validation "
        "artefacts needed for the audit trail."
    )
    out.append("")
    out.append("## Updating this guide")
    out.append("")
    out.append("1. Add broad resources to `catalog/catalog.json`.")
    out.append(
        "2. Add project-used or audited resources to "
        "`research/data/ANALYSED_RESOURCE_LEDGER.csv`."
    )
    out.append("3. Run `python scripts/build_exports.py`.")
    out.append("4. Run `python scripts/build_database_guide.py`.")
    out.append("5. Run `python scripts/validate_catalog.py` and the repository tests.")
    out.append("")
    out.append(
        "Last generated from the repository inventories; see version control for "
        "the exact source revisions."
    )
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    text = build_guide()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(text)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
