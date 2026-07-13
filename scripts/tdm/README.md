# Private TDM pipeline (do not publish outputs)

Scripts for harvesting publisher content via **official TDM APIs** under
University of Toronto agreements. The *code* here is fine to keep in the repo;
everything it *downloads* is licensed content and must stay private.

## Ground rules (from UofT licence terms)

1. Non-commercial research use only.
2. Downloaded content goes to `TDM_DATA_DIR` — a **local disk, outside OneDrive
   and outside git**. Never commit, upload, or re-share it (including private
   GitHub repos and cloud AI services).
3. Elsevier: store on secure **Canadian** storage.
4. ACS: keep data only for the project duration; don't mix with third-party data.
5. RSC: requires 2-week advance notice (via the library) before any crawling.
6. Run on campus network or UofT VPN — entitlement is IP-based (Wiley: campus
   LAN only).
7. Every download is logged to `_manifest.jsonl` next to the files (DOI, source,
   licence, timestamp) so provenance and cleanup are easy.

Full policy: `docs/methodology.md` and the
[UofT TDM guide](https://guides.library.utoronto.ca/c.php?g=744383&p=5384621).

## Setup

```bash
cd scripts/tdm
copy .env.example .env    # then fill in keys; .env is gitignored
```

## Tools

| Script | What it does | Key needed |
|---|---|---|
| `crossref_si.py` | Find articles with declared SI/data relations (open metadata, discovery step) | none |
| `springer_client.py` | Search + harvest Springer Nature **OA full text** (JATS XML); Meta API metadata | `SPRINGER_OA_KEY` / `SPRINGER_META_KEY` |
| `nature_campaign.py` | Campaign driver: OA harvest + data-availability link extraction → catalog candidates. `hybrid` mode covers **paywalled flagship articles** via Meta API + DataCite back-linking (no full text needed) | Springer keys |
| `elsevier_client.py` | Search ScienceDirect + fetch full-text XML under UofT subscription | `ELSEVIER_KEY` |

Typical flow:

```bash
# 1. discover candidate DOIs (no key needed)
python crossref_si.py --query "perovskite solar cell dataset" --prefix 10.1038 --max 20

# 2. smoke-test your Springer key
python springer_client.py search --query "perovskite solar cell" --max 3

# 3. harvest OA full text (CC-licensed, least restricted)
python springer_client.py harvest --query "perovskite solar cell stability" --max 25

# 4. Elsevier full text (on campus / VPN)
python elsevier_client.py harvest --query "battery electrolyte conductivity" --max 20
```

## Not yet implemented

- **Wiley** client — needs your TDM token first (campus LAN only).
- **ACS / RSC** — approval via the
  [library contact form](https://mdl.library.utoronto.ca/about/contact-form)
  before any code runs.
- SI-file retrieval: publisher APIs mostly serve article XML; SI coverage
  varies. Ask the library when requesting ACS/RSC access.
