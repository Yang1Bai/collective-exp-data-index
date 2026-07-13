# Agent brief: Nature-family dataset harvest (for OpenClaw or similar local agent)

## Objective

Run the Nature-family dataset discovery campaign for the Collective
Experimental Data Index, then report results. The campaign harvests Springer
Nature open-access articles via the official OA API and back-links paywalled
flagship articles to their deposited datasets via DataCite. Everything runs
locally through `run_campaign.cmd`.

## Hard rules (licence compliance — do not violate)

1. **Never read the downloaded article XML into model context.** Files under
   `D:\tdm_private_data\` are publisher-licensed content; UofT licence terms
   prohibit uploading them to third-party AI platforms. Run the harvest as a
   plain command (OpenClaw: command payload, not an agent turn). You MAY read
   `scripts\discovered\*.json` (metadata + links only) and `campaign.log`.
2. Never commit/push anything under `D:\tdm_private_data\`, `scripts\tdm\.env`,
   or `*.log` to git. The .gitignore already excludes them — don't override it.
3. Never scrape publisher websites (nature.com, pubs.acs.org, etc.). The
   scripts only use official APIs; don't "fix" failures by fetching HTML.
4. Keep the built-in rate limits (the scripts sleep between requests). Don't
   parallelize API calls.

## How to run

Working dir: `D:\OneDrive - University of Toronto\AC\Project\Collective exp dataset\scripts\tdm`

- Smoke test (~3 min): `run_campaign.cmd smoke`
- One flagship journal (~30 min): `run_campaign.cmd flagship`
- Full sweep (hours; run overnight): `run_campaign.cmd full`

The wrapper activates Anaconda base itself (plain `python` in PowerShell is a
broken Store stub on this machine — always go through the .cmd).

Recommended schedule: `full` weekly (e.g. Sunday 02:00). Safe to re-run:
already-harvested DOIs are skipped automatically.

## Success criteria & reporting

After a run, check `campaign.log` (tail ~50 lines):

- Success: lines like `[N/max] 10.1038/... links=[...]` and
  `X candidates with dataset links -> ...discovered\nature_oa_*.json`.
- Report to the user: number of new articles harvested, number of candidates
  produced, the newest file names in `scripts\discovered\`, and any error lines
  (`error, moving on: ...`, tracebacks, HTTP 4xx/5xx).
- HTTP 401/403 → API key problem; 429 → rate limited (stop, retry next day).
  Repeated `unknown url type: https` → conda env not activated (must run via
  the .cmd wrapper).

## What happens downstream (not this agent's job unless asked)

A human (or the Cowork weekly task) reviews `scripts\discovered\*.json`,
assigns domain/subdomain/tags, moves keepers into `scripts\seed\`, and runs
`python scripts/build_seed.py && python scripts/build_exports.py &&
python scripts/validate_catalog.py` from the repo root.
