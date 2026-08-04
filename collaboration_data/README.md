# Collaborator data workspace

This directory is the entry point for collaborators who want to test new
cross-domain transfer, representation-learning, calibration, ranking, or OOD
methods on the datasets assembled for this project.

The large data files are distributed as assets of the private GitHub
pre-release [`collaborator-data-v2026.08.04`](https://github.com/Yang1Bai/collective-exp-data-index/releases/tag/collaborator-data-v2026.08.04).
They are not stored as ordinary Git blobs. This keeps repository clones small
and prevents large binary files from being duplicated in Git history.

## What collaborators receive

| Asset | Contents | Intended use |
|---|---|---|
| `collective-exp-analysis-ready-v2026.08.04.zip` | Unified SQLite snapshot and the locally retained external inputs used by the transfer, null, control, and boundary analyses | Reproduce existing analyses or develop alternative transfer methods |
| `collective-exp-candidate-tables-v2026.08.04.zip` | Tabular datasets from the additional `Dataset/` research collection; PDFs, figures, notebooks, and code are excluded | Search for new donor-recipient pairs and test alternative representations |

Run the PowerShell helper from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File collaboration_data/fetch_collaborator_data.ps1
```

Or download the two assets manually from the release page. After extraction,
start with:

- `data/collective.sqlite` for the harmonized local lake;
- `data/external/` for source-specific inputs and archives;
- `Dataset/` for additional candidate tables;
- [`DATA_FILE_MANIFEST.csv`](DATA_FILE_MANIFEST.csv) for file-level hashes and
  source-family labels;
- [`SOURCE_LICENSE_MATRIX.csv`](SOURCE_LICENSE_MATRIX.csv) for provenance,
  access, and reuse constraints;
- [`research/evidence/ATTEMPT_LEDGER.csv`](../research/evidence/ATTEMPT_LEDGER.csv)
  to avoid unknowingly repeating an existing transfer attempt.

## Required scientific workflow

Before running a new donor-to-recipient experiment, record:

1. donor and recipient datasets;
2. shared representation and proposed transferable object;
3. experimental-state match and provenance boundary;
4. outcome-blind OOD split;
5. recipient-only, shuffled-donor, and matched-false-donor controls;
6. whether the endpoint is numerical prediction, candidate ranking, or
   abstention.

Positive, null, harmful, and non-evaluable results should all be added to the
attempt ledger.

## Licence and visibility boundary

This is a **private collaborator snapshot**, not a public relicensing of all
upstream datasets. Every file retains its upstream terms. Rows marked
`verify-upstream`, `unknown`, or `collaborator-restricted` in the source matrix
must not be redistributed outside the authorized collaboration without a
rights check.

If the GitHub repository is ever made public, remove or replace the private
release assets before changing repository visibility. The public manuscript
release should instead cite the original repositories and deposit only data
whose redistribution rights have been confirmed.

## Rebuilding the assets

From the repository root:

```powershell
python scripts/data/build_collaborator_release.py
```

The build writes the release archives under `tmp/collaborator-data-v2026.08.04/`
and refreshes the file manifest and SHA-256 checksums committed in this
directory.
