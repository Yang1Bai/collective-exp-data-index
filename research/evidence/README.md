# Evidence and attempt policy

The manuscript is selective; the repository is not. Every substantial attempt
is assigned one of the following dispositions in
[`ATTEMPT_LEDGER.csv`](ATTEMPT_LEDGER.csv):

- `main-positive`: carries a primary paper claim;
- `main-boundary`: is required to falsify a universal or generic-transfer claim;
- `supplement-positive`: useful effect with a narrower or provenance-limited interpretation;
- `ranking-only`: useful candidate order without qualified numerical calibration;
- `null`: no qualified improvement;
- `harmful`: negative transfer under the tested contract;
- `abstain`: the support/applicability gate refused borrowing;
- `non-evaluable`: a frozen endpoint could not be calculated as specified; or
- `method-development`: outcome-inspected work that can define a future test but
  cannot provide independent confirmation.

The ledger is not a vote count. Rows differ in independence, leakage unit,
endpoint, and evidentiary weight. The manuscript-facing selection is defined in
[`analysis/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md`](../../analysis/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md),
while the complete executable status is in
[`analysis/core_story_experiment_registry.json`](../../analysis/core_story_experiment_registry.json).
