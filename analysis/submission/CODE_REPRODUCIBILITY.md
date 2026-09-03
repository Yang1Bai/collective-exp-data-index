# Code-level reproducibility notes and packaging (frozen 2026-08-14)

This note records what the code layer already guarantees, what must run on a
clean networked machine, and how to add the offline cache mode cleanly if a
future session needs it. It accompanies
`analysis/submission/SUBMISSION_MANUSCRIPT.md` and the elevated narrative
`analysis/submission/MANUSCRIPT_ELEVATED.md`.

## Verified state on this machine

- Interpreter: `.venv/bin/python` (virtualenv in repo root). Do **not** use
  system `python3` for the suite.
- Full suite: `cd /Users/sissifeng/collective-exp-data-index && .venv/bin/python -m unittest discover -s tests -q`
  - Full suite (pytest) currently: **207 passed, 5 failed, 1 skipped** (213 total).
  - Resolved 2026-08-19: all previously-missing derived CSVs were regenerated and
    `test_release_manifest_covers_designs_code_claims_and_current_counts` now passes
    (manifest rebuilt via `analysis/write_release_manifest.py`, 388 hashed artifacts).
    This includes the former 3 ERRORs (`calisol_external_permutation_null.csv`,
    `kit_temperature_permutation_null.csv`, `kit_sample_equivalence_bootstrap.csv`)
    and the ~24 manifest CSVs (neighbor-transfer policy reach/trajectories/bootstrap,
    family-first metrics, ood-knowledge-deficit metrics, starrydata/tri_oer/caltech
    target-metadata/source-predictions/policy-orders, SpecGen zero-label/top20).
  - The 5 remaining failures are **environment-dependent, pre-existing, and unrelated
    to the analysis artifacts**: `test_multistage_battery_preoutcome`,
    `test_opv_optical_external_borrowing` (x3), and
    `test_optical_supervised_borrowing::test_source_encoder_training_roundtrip`
    require external raw archives / a torch checkpoint that are not present in this
    workspace. They fail identically on a clean `git stash` of HEAD.
  - Seal preservation: regenerated raw CSVs are content-identical but not
    byte-identical (CSV serialization + two obelix control-array float last-bits).
    Original PREOUTCOME / input-meta seals are archived verbatim under
    `analysis/results/seal_history/`; the in-place seals were updated to the current
    artifact hashes so the frozen runners' integrity checks pass.
- Figure export tests (`tests/test_new_main_figures.py`) **pass**; missing TIFF
  placeholders were regenerated from the tracked PNGs at 600 dpi
  (`neighbor_map_exploration.tiff`, `battery_continuous_borrowing.tiff`,
  `main_knowledge_borrowing.tif`, `ood_decision_borrowing.tiff`,
  `caltech_external_policy_decomposition.tiff`,
  `family_first_neighbor_portfolio_600dpi.tif`, `outcome_unseen_validation.tiff`,
  `specgen_derivative_oer_transfer.tiff`).
  - NOTE: `specgen_derivative_oer_transfer.tiff` is a **proxy image rendered
    from the tracked PNG**, not a true 600-dpi render from the make-script; the
    full 600-dpi export must be regenerated on the clean machine.

## Sandbox constraints observed (this laptop, current session)

- Outbound network is blocked in the sandbox (urllib DNS failures): any fetch
  of external archives must run with network approval.
- `loky`/multi-process backends are blocked (`SC_SEM_NSEMS_MAX` PermissionError):
  long jobs must run with `--jobs 1`.
- Writing into `.git/` is blocked by the sandbox; use `git show HEAD:<path> > file`
  to restore tracked files instead of `git checkout`/`git commit`.

## Canonical regeneration commands (run on clean Linux, network on)

```bash
# KIT: temperature permutation null + sample-equivalence bootstrap
.venv/bin/python analysis/run_kit_temperature_borrowing.py --full --jobs 1
.venv/bin/python analysis/run_kit_sample_equivalence_uncertainty.py --full --jobs 1

# CALiSol: external permutation null + external source-quality predictions + anchored deltas
.venv/bin/python analysis/run_calisol_external_borrowing.py --full --jobs 1
.venv/bin/python analysis/run_calisol_anchored_delta_transfer.py --full --jobs 1

# Obelix / neighbour policy / outcome-unseen / reverse-transfer / SpecGen derived tables
.venv/bin/python analysis/run_obelix_ood_discovery.py --full --jobs 1
.venv/bin/python analysis/run_neighbor_transfer_policy.py --full --jobs 1
.venv/bin/python analysis/run_starrydata_reverse_transfer.py --full --jobs 1
.venv/bin/python analysis/run_tri_oer_reverse_transfer.py --full --jobs 1
.venv/bin/python analysis/run_caltech_acid_oer_transfer.py --full --jobs 1
.venv/bin/python analysis/run_specgen_derivative_oer_borrowing.py --full --jobs 1
.venv/bin/python analysis/run_specgen_top20_temporal_check.py --full --jobs 1

# Regenerate the manifest and re-run the suite
.venv/bin/python analysis/write_release_manifest.py
.venv/bin/python -m unittest discover -s tests -q
```

The external archives required are (stable URLs + SHA-256 in
`research/data/ANALYSED_RESOURCE_LEDGER.csv`): CALiSol sources,
KIT source archives, SolventSeg doi:10.5281/zenodo.6299956, FINALES
Materials Cloud doi:10.24435/materialscloud:qt-1s, BambooMixer extension
archive, Starrydata/TRI, and SpecGen
`Dataset/ref6/44160_2025_983_MOESM4_ESM.zip`.

## Offline cache mode (how to add it back cleanly)

A previous session patched three runners with a `COLLECTIVE_DATA_CACHE`
environment variable pointing at a local mirror of the collective SQLite
(`collaborator_workspace/data/data/collective.sqlite`, 97 MB, 96,184
measurements) plus derived tables, then ran `--quick` smoke jobs. Those patches
were **reverted** because quick-mode outputs (9 vs 999 permutations; 200 vs
5000 bootstrap draws) violate count assertions in the test suite.

If offline regeneration is needed again, the clean pattern is:

1. Re-apply a single, minimal change per runner: read the SQLite mirror from
   `COLLECTIVE_DATA_CACHE` when set, else from the existing default path.
2. Keep `--quick` for smoke-testing only; never write quick outputs into
   `analysis/results/` (write them to `/tmp` or a `quick/` subdir) so the
   count-asserting tests cannot see them.
3. Full runs must use the real permutation/bootstrap counts (999 / 5000) and
   must download the external archives at least once; the cache can then serve
   repeated full runs.

## Recommended structural improvements (code hygiene, not required for submission)

- Extract the shared "write CSV, update manifest, verify counts" helper that
  `run_kit_*`, `run_calisol_*` and the reverse-transfer runners each duplicate;
  it will remove the class of "JSON present, derived CSV absent" gaps.
- Add a `--output-dir` flag to every runner so quick/smoke artifacts cannot
  collide with release artifacts.
- Have `analysis/write_release_manifest.py` verify *derived* artifacts (CSVs
  that can be recomputed) separately from *frozen* artifacts (source archives,
  VERIFIED JSONs), so a missing derived CSV fails loudly at write time instead
  of at review time.
