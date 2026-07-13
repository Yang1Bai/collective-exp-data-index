# Contributing

Thanks for helping build the index. Contributions are database *entries*
(metadata + links), not dataset files.

## Adding a database

1. **Check it isn't already listed** — search `catalog/catalog.json` for the
   name or DOI.
2. **Confirm it's real and reachable** — open the homepage/landing page
   yourself and record that URL in `verified_via`. Do not invent DOIs; if you
   can't confirm a DOI, set `"doi": null` and rely on `homepage_url`.
3. **Write the entry** following `catalog/schema.json`. Minimum required fields:
   `id`, `name`, `description`, `domain`, `subdomain`, `data_type`, `access`,
   `homepage_url`. Add a new object to a file in `scripts/seed/` (grouped by
   domain) or directly to the `entries` array in `catalog/catalog.json`.
4. **Rebuild and validate:**
   ```bash
   python scripts/build_seed.py        # only if you edited a seed file
   python scripts/build_exports.py
   python scripts/validate_catalog.py  # must pass
   ```
5. **Open a PR** with the regenerated `catalog.json`, `catalog.csv`, and
   `CATALOG.md`.

## Writing a good `description`

One to three sentences answering: what's in it, roughly how big, and how the
data was generated (measured / simulated / mined). Example:

> "Open dataset of 13,825 experimentally measured ionic-conductivity data
> points for non-aqueous lithium-battery electrolytes, digitized from 27
> publications and covering 14 Li-salts and 38 solvents."

## Field conventions

| Field | Notes |
|-------|-------|
| `id` | kebab-case, stable, unique (e.g. `open-reaction-database`) |
| `domain` | `materials` or `chemistry` (use tags for cross-domain relevance) |
| `subdomain` | topical group, e.g. `catalysis`, `spectroscopy`, `benchmark-ml` |
| `data_type` | `experimental`, `computational`, or `mixed` — be honest; this is the key filter |
| `access` | `open` (free download), `registration` (free account), `restricted` (paywall) |
| `license` | the underlying data's license if known, else `"Unknown"` |
| `doi` | without the `https://doi.org/` prefix; `null` if none |

## What NOT to contribute

- Do **not** upload dataset files, SI PDFs, or scraped copies of publisher
  content. Link to the original instead.
- Do **not** add entries for data behind a login you can't confirm is openly
  licensed — mark `access` accurately if you do include a restricted resource
  (e.g. CSD is listed as `restricted`).
- Do **not** bypass any site's access controls, rate limits, or terms to gather
  metadata. `scripts/discover.py` only uses APIs that permit programmatic use.

## Sourcing policy

See [`docs/methodology.md`](docs/methodology.md) for the full stance on
scraping, licensing, and FAIR principles.
