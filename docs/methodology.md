# Methodology & sourcing policy

## Principle: index, don't mirror

The catalog records **metadata and links**, pointing to each dataset at its
original, authoritative home. We do not re-host source files. This keeps the
project legal, low-maintenance, and always pointing at the canonical (and
most up-to-date) copy.

## Where entries come from — allowed channels

We gather entries only through channels that permit programmatic access or
manual curation:

1. **Open data repositories** — Zenodo, Figshare, Dryad, Materials Cloud,
   NOMAD, NIST Materials Data Repository. Authors deposit datasets here with
   explicit (usually CC-BY / CC0) licenses and stable DOIs. All expose APIs.
2. **Open scholarly metadata** — DataCite (dataset DOIs and their metadata),
   Crossref (article ↔ dataset relations), OpenAlex (works of type `dataset`).
   Used to *discover* which papers have associated datasets and where they live.
3. **Established domain databases** — Materials Project, OQMD, AFLOW, PubChem,
   ChEMBL, Open Reaction Database, etc. Each publishes its own documented
   bulk-access or API.
4. **Manual curation** — a human confirms the landing page and writes the
   description. Every seed entry carries a `verified_via` URL.

## Where entries do NOT come from — the scraping question

We deliberately do **not** bulk-scrape publisher websites (Nature/Springer,
ACS, RSC, Wiley, AAAS/Science) to harvest supporting-information files.

- **Terms of use.** Publisher terms generally prohibit systematic or automated
  downloading, even of content that is free to read. "Freely accessible" is not
  the same as "licensed for bulk reuse."
- **Copyright.** Supporting-information files remain under copyright unless the
  article carries an open license (e.g. some CC-BY OA articles). Re-hosting them
  would infringe; even indexing their contents verbatim can.
- **Technical reality.** These sites use rate limits, bot detection, and
  CAPTCHAs. Bulk crawling gets an institutional IP blocked and breaks whenever
  the site changes.
- **It's usually unnecessary.** The genuinely reusable, structured experimental
  data is almost always *also* deposited in a repository (channel 1) or in a
  domain database (channel 3), where it is properly licensed and machine-
  readable. That is what we index.

### Text and data mining (TDM), if ever needed

If a specific dataset exists only inside a publisher's SI, the correct approach
is **not** to scrape it but to:

- link to the article DOI and note the data's location in the entry, and/or
- use the publisher's **official TDM API** under an institutional agreement
  (e.g. via Crossref TDM, or the publisher's own developer program), where the
  license permits.

Manuscript-level TDM rights vary by publisher and subscription; this project
does not assume them.

## Licensing of what we produce

- The **catalog metadata we author** (descriptions, tags, groupings) is offered
  under **CC-BY-4.0**.
- Each entry's `license` field records the **underlying dataset's** license as
  best we can determine it. When unknown, it is marked `Unknown` — reusers must
  verify before use.
- Linking to a resource does not relicense it. Downstream users are responsible
  for complying with each dataset's own terms.

## FAIR alignment

The index supports **F**indability (searchable metadata, DOIs), **A**ccessibility
(direct links to the authoritative source), **I**nteroperability (a consistent
schema and CSV/JSON exports), and **R**eusability (recorded licenses and
provenance). It is itself a small FAIR object over other people's FAIR data.

## Data quality & verification

- Every seed entry was confirmed against its live landing page (`verified_via`).
- `validate_catalog.py` enforces the schema, unique ids, and no duplicate DOIs.
- Planned: automated periodic link-checking to flag dead links and new versions.

## Roadmap notes

Kept in sync with the README roadmap: seed → discover → enrich → automate
freshness → open up. The "private-first / dead repo" phase exists so entries can
be reviewed before the catalog is presented as authoritative.
