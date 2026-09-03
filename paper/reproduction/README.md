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

The compact checkout intentionally retains summaries, selected derived tables
and verification records rather than every large intermediate array. The
legacy claim-specific verifiers therefore require a full rerun first; they are
not substitutes for the fast package audit above.

The repository also retains tests for historical or optional model families
that require additional environments such as Torch or Chemprop and some
superseded export assets. Those tests remain useful for their own workflows,
but they are not part of the current manuscript submission gate.

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

The jobs reconstruct ignored intermediate files such as per-repeat metrics and
bootstrap arrays. After those files exist, run the independent verifiers:

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
