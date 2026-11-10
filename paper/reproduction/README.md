# Reproducing and auditing the submission package

## Fast, offline package audit

From the repository root, run:

```bash
python paper/reproduction/verify_paper_package.py
```

This standard-library-only check verifies that every allowlisted artifact
exists, every article source-data value matches its JSON source, the dataset
manifest agrees with the repository resource ledger, the frozen headline
metrics retain their expected values, and the claim-bearing artifact checksums
have not changed.

## Full scientific rerun and verification

The Git checkout retains code, designs, summaries, selected derived tables and
verification records, but not the large row-level and resampling outputs.
Those outputs do not need to be regenerated to check a reported value: they
are all supplied in the complete Source Data package archived at Zenodo (see
[../ARTICLE_LINKS.md](../ARTICLE_LINKS.md)). To run the claim-specific
verifiers without rerunning the models, unpack that package into the
repository root so that its files land at their recorded paths under
`analysis/results/`. A full rerun, described below, is needed only to
reproduce the outputs independently.

The repository also retains tests for historical or optional model families
that require additional environments such as Torch or Chemprop and some
superseded export assets. Those tests remain useful for their own workflows,
but they are not part of the current manuscript submission gate.

## Software versions used for the reported analyses

| Analysis | Python | NumPy | pandas | SciPy | scikit-learn | RDKit | Other |
|---|---|---|---|---|---|---|---|
| Broad screen (Balam cluster) | 3.11.5 | 1.26.4 | 2.3.3 | 1.17.1 | 1.9.0 | 2026.03.3 | joblib 1.5.3 |
| Other submitted analyses (local) | 3.11.13 | 1.26.4 | 2.3.3 | 1.17.1 | 1.9.0 | 2026.03.3 | matplotlib 3.11.1 |
| Revision (R1) analyses | 3.13 | 2.5.3 | 3.0.5 | 1.18.1 | 1.9.1 | 2026.09.1 | full package list deposited with them |

`analysis/requirements.txt` gives the version ranges of the submitted
environment (NumPy < 2, pandas < 3). An environment file is deposited with
each broad-screen result.

Known limit: the procedure that chooses SolventSeg training formulations
without using conductivity is not reproducible across numerical-library
versions, because most chemistry descriptors of the 36 formulations differ
only by rounding noise that the procedure rescales. The recorded training
formulations of every repetition are therefore deposited and must be reused
when re-evaluating SolventSeg results; refitting the CALiSol source model and
the target-only models on those recorded formulations reproduces the archived
results.

## Environment

Create an environment with Python 3.11 or newer and install the repository
analysis dependencies, including RDKit:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt -r analysis/requirements.txt
```

The submission-facing model contract tests are:

```bash
python -m pytest -q \
  tests/test_multi_target_ood_borrowing.py \
  tests/test_mixture_response_transfer.py \
  tests/test_electrolyte_programme_interaction.py
```

Obtain the upstream archives and caches pinned in each frozen design, then run
the full model jobs:

```bash
python analysis/run_multi_target_ood_borrowing.py
python analysis/run_bamboomixer_response_transfer_development.py
python analysis/run_bamboomixer_cross_database_interaction.py
python analysis/run_bamboomixer_recipient_baseline_stress_test.py
python analysis/run_finales_rank_replication.py
```

The jobs reconstruct the untracked files, such as per-repeat metrics and
bootstrap arrays, that are otherwise supplied in the Zenodo Source Data
package. After those files exist (from the package or from a rerun), run the
independent verifiers:

```bash
python analysis/verify_multi_target_ood_borrowing.py
python analysis/verify_bamboomixer_response_transfer_development.py
python analysis/verify_bamboomixer_cross_database_interaction.py
python analysis/verify_bamboomixer_recipient_baseline_stress_test.py
python analysis/verify_finales_rank_replication.py
```

These reruns can be computationally expensive. Follow the frozen design beside
each runner, and do not present a failed verifier caused by a missing
intermediate CSV or dependency as a changed scientific result. Quick or smoke
outputs must not overwrite formal files in `analysis/results/`.

The SolventSeg 13-model stress test is deliberately separate from the
prespecified Ridge comparison. A successful stress-test result must not be
substituted for the formal route-defining contrast.
