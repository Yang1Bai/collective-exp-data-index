# Collective Experimental Data Index

A community catalog of **published, openly available experimental datasets** in
materials science and chemistry — pointing to the data at its original home,
with a short description, license, and DOI for each.

The goal is simple: make it easy to *find and reuse* the datasets that are
scattered across supporting information, data repositories, and lab websites,
so researchers (and self-driving labs) don't rebuild the same corpus twice.

> **Status: private-first ("dead" repo).** This starts as a private working
> repository. Once the catalog is mature and the metadata has been reviewed, it
> can be opened to the community. Nothing here needs to stay closed for legal
> reasons — see *What this is / isn't* below — it's private only so it can grow
> without half-finished entries being mistaken for vetted ones.

## What this is / isn't

**This is a metadata index, not a data mirror.** For each database we record
*where it lives, what's in it, and how to cite it* — the name, a description,
domain tags, the DOI, the license, and a link. We do **not** re-host the
underlying files.

**Why not just scrape the SI PDFs from Nature / ACS / RSC / Wiley / Science?**
Because that path is both fragile and against those publishers' terms of use.
Even when a supporting-information file is free to *read*, the publisher's
terms typically prohibit bulk/automated downloading, and their sites actively
block crawlers (rate limits, CAPTCHAs, IP bans). The SI files themselves remain
under copyright. So bulk scraping is legally risky, technically brittle, and
would get an institutional IP blocked.

**The better path — and the one this project takes — is to index datasets
through the channels that explicitly allow programmatic access:**

- **Data repositories** where authors deposit datasets under open licenses
  (Zenodo, Figshare, Dryad, Materials Cloud, NOMAD, NIST) — these have proper
  APIs and clear licenses (often CC-BY / CC0).
- **Open scholarly metadata** (DataCite, Crossref, OpenAlex) to *discover*
  which papers have associated datasets and where they are.
- **Established domain databases** (Materials Project, OQMD, PubChem, ChEMBL,
  Open Reaction Database, …) that publish their own bulk-download endpoints.

The real, reusable experimental data almost always lives in one of these — not
locked inside a publisher's SI PDF. Indexing them is legal, sustainable, and
far more complete.

If, for a specific dataset, the *only* copy is inside a publisher's SI, the
right move is to link to the article's DOI and note the location — not to
scrape it.

## What's in the seed catalog

The catalog holds **233 curated databases** across materials
science and chemistry — with particular depth in high-throughput
experimentation, self-driving-lab campaign datasets, and a July 2026
TDM harvest of 115 open datasets from Zenodo and figshare spanning
batteries, photovoltaics, spectroscopy, geophysics, bioactivity, alloys,
magnetic materials, and more — each confirmed against its live landing
page. Browse it three ways:

- **[`CATALOG.md`](CATALOG.md)** — human-readable, grouped by domain and topic
  (start here).
- **[`catalog/catalog.csv`](catalog/catalog.csv)** — flat table for Excel /
  pandas.
- **[`catalog/catalog.json`](catalog/catalog.json)** — the machine-readable
  source of truth.

Coverage includes the **July 2026 TDM harvest** (115 open datasets from
Zenodo and figshare, covering batteries, photovoltaics, spectroscopy,
geophysics, bioactivity, alloys, magnetic materials, mechanical properties,
porous materials, polymers, and catalysis), as well as general
materials-property databases (Materials Project,
OQMD, AFLOW, NOMAD, JARVIS, Materials Cloud), crystallography (COD, AMCSD),
catalysis (Open Catalyst OC20/OC22, Catalysis-Hub), batteries (BatteryArchive,
TRI fast-charging, NASA PCoE, CALCE, Oxford), photovoltaics (The Perovskite
Database, NREL PVDAQ, Emerging-PV), superconductors (SuperCon), thermoelectrics
(ESTM, Starrydata2), 2D materials (C2DB, 2DMatpedia), polymers (PoLyInfo,
Khazana), MOFs & porous materials (CoRE MOF, QMOF, MOFX-DB, CURATED COFs),
glasses (SciGlass), alloys (NIMS MatNavi, MPEA), experimental spectra (RRUFF,
NIST XPS, MAGNDATA), reaction data (Open Reaction Database, USPTO,
Buchwald–Hartwig & Suzuki HTE sets, AstraZeneca ELN), molecular properties
(ESOL, FreeSolv, AqSolDB, BigSolDB, CALiSol-23, Photoswitch, IUPAC pKa),
optical properties (Deep4Chem, ChemFluor), kinetics & thermochemistry (NIST
SRD 17, ATcT, ILThermo), bioactivity (PubChem, ChEMBL, BindingDB, Tox21),
spectroscopy (NIST WebBook, nmrshiftdb2, SDBS, MassBank), self-driving-lab
benchmarks & lab automation (Olympus, Summit, Atlas, mobile robotic chemist,
Chemputer/XDL), data infrastructure (MDF, Foundry-ML, PARADIM), and ML
benchmark suites (Matbench, MoleculeNet, TDC, OGB).

### Experimental-only policy

This is an index of **measured, experimental data**. Purely computational
databases (pure DFT/MD/simulation, e.g. Materials Project, OQMD, QM9) are
**excluded from the catalog by policy** at build time; they are archived in
`catalog/excluded_computational.json` for transparency and can be reinstated
by removing the filter in `scripts/build_seed.py`. Entries tagged `mixed`
remain because they contain measured data alongside computed parts (the
description states which). `CATALOG.md` marks each entry with 🧪 / 🔀.

## Repository layout

```
.
├── README.md               # this file
├── CATALOG.md              # generated, browsable index (do not edit by hand)
├── catalog_map.html        # generated: interactive similarity map (1 point = 1 database)
├── datapoint_map.html      # generated: unified map (1 point = 1 experimental sample)
├── catalog/
│   ├── catalog.json        # source of truth (edit here, or via seed files)
│   ├── catalog.csv         # generated flat export
│   ├── excluded_computational.json  # archived computational-only entries (policy)
│   └── schema.json         # JSON Schema for one entry
├── scripts/
│   ├── seed/               # curated research records (provenance-preserving)
│   ├── build_seed.py       # seed/*.json  -> catalog/catalog.json (+ experimental-only policy)
│   ├── build_exports.py    # catalog.json -> catalog.csv + CATALOG.md + catalog_map.html
│   ├── build_map.py        # interactive similarity map generator
│   ├── validate_catalog.py # schema + duplicate checks (CI-friendly)
│   ├── discover.py         # query open APIs for new candidate datasets
│   ├── datapoint_map/      # data-point-level map pipeline (see its README)
│   ├── discovered/         # auto-discovery candidates awaiting human review (gitignored)
│   ├── tdm/                # PRIVATE harvest pipeline via official publisher APIs
│   ├── common.py           # shared helpers
│   └── requirements.txt    # optional extras (stdlib works without them)
├── docs/
│   └── methodology.md      # sourcing policy, FAIR, legal stance, roadmap
├── CONTRIBUTING.md
├── LICENSE                 # code (MIT)
└── LICENSE-DATA.md         # catalog metadata (CC-BY-4.0) + note on source data
```

## Local unified database (data lake)

`scripts/localdb/build_localdb.py` mirrors the **open-licensed** datasets
locally and builds `data/collective.sqlite` — one native table per dataset
(`raw_*`), a unified cross-domain `measurements` table
(dataset · material · property · value · unit · conditions), and a `datasets`
table carrying each database's short description, license, DOI and link
straight from the catalog. Currently 10 datasets / **105,955 measurements /
319 distinct properties** (thermoelectrics, solubility, pKa, electrocatalysis,
alloys, hydration, photoswitches, solid electrolytes, polymers, adsorption
isotherms); restricted/registration-only databases are indexed in the catalog
but never mirrored. The ISODB loader parses a capped subset per build
(`ISODB_CAP`) — raise it for a full local build.

```bash
python scripts/localdb/build_localdb.py                  # clone + build
python scripts/localdb/build_localdb.py --query "SELECT dataset,property,COUNT(*) FROM measurements GROUP BY 1,2"
```

To add a dataset: add its clone spec to `SOURCES` and a loader block in
`load_all()`. `data/` is gitignored — the mirror stays local.

## Private collaborator data snapshot

Authorized collaborators can download the complete working snapshot from the
private [collaborator data workspace](collaboration_data/README.md). The
snapshot contains the unified SQLite lake, locally retained external inputs,
and additional cross-domain candidate tables for testing new transfer,
representation-learning, calibration, ranking, and OOD methods.

Large files are supplied as verified GitHub pre-release assets rather than
ordinary Git blobs. The workspace includes a 474-file manifest, SHA-256
checksums, a source/licence matrix, and one-command download helpers. This
private access route does not relicense upstream datasets and must be removed
or replaced before the repository is made public unless all redistribution
rights have been confirmed.

## Quick load

```python
import pandas as pd
df = pd.read_csv("catalog/catalog.csv")
# filter by domain
materials = df[df["domain"] == "materials"]
# filter by subdomain
batteries = df[df["subdomain"] == "batteries"]
# load full metadata
import json
with open("catalog/catalog.json") as f:
    cat = json.load(f)
entries = cat["entries"]
```

## Quick start

No dependencies are required for the core tooling (pure standard library).

```bash
# Regenerate the catalog from the curated seed records:
python scripts/build_seed.py

# Regenerate CATALOG.md and catalog.csv from catalog.json:
python scripts/build_exports.py

# Validate before committing:
python scripts/validate_catalog.py
```

### Discovering new datasets (the legitimate way)

`discover.py` queries open APIs and writes candidate entries for you to review
— it never downloads copyrighted SI or bypasses access controls.

```bash
export INDEX_CONTACT_EMAIL="you@your-institution.edu"   # polite API etiquette

python scripts/discover.py --source zenodo   --query "perovskite solar cell"     --domain materials --limit 25
python scripts/discover.py --source datacite --query "electrolyte conductivity"  --domain chemistry --limit 25
python scripts/discover.py --source all      --query "high throughput experiment" --limit 15
```

Candidates land in `scripts/discovered/`. Review them, keep the good ones, drop
them into a `scripts/seed/*_seed.json` file (or straight into `catalog.json`),
then rerun `build_exports.py` and `validate_catalog.py`.

## Roadmap

1. **Seed & review** (now) — curated core of high-value databases. ✅
2. **Expand via discovery** — run `discover.py` across sub-domains; review and
   fold in new entries with descriptions.
3. **Enrich** — add per-entry detail (size, formats, access notes, example
   loading code), and verify licenses.
4. **Automate freshness** — scheduled link-checking and re-discovery; flag dead
   links and new versions.
5. **Open up** — publish the repo publicly (and optionally a small static site
   over `catalog.json`) once entries are reviewed.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). In short: add an entry to a seed file
or `catalog.json` following `catalog/schema.json`, run the build + validate
scripts, and open a PR.

## License

- **Code** (the scripts): MIT — see [`LICENSE`](LICENSE).
- **Catalog metadata** (descriptions, tags, links we wrote): CC-BY-4.0 — see
  [`LICENSE-DATA.md`](LICENSE-DATA.md).
- **The underlying datasets** keep their own licenses (recorded per entry).
  Always check an entry's `license` before reusing its data.
