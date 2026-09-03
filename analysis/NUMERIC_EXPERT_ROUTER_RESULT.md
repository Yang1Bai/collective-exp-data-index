# Numeric expert-router result

## Status

**The 34-edge retrospective screen failed both frozen group-held-out gates.**
The numeric router remains shadow-only, no existing expert or router is
replaced, and this result does not justify returning to OPD with a larger LLM.

## What was tested

The experiment expanded the edge inventory from 15 selected directions to all
34 compatible directed combinations within four endpoint-consistent suites:

| Suite | Directed edges |
|---|---:|
| Alloy yield strength | 6 |
| OCx24 Fe-Co | 2 |
| SECCM HER | 6 |
| SpecGen | 20 |

Each donor trained one frozen Standard/MHAR pair, reused across its recipients.
The router saw ten target-free features only: sizes, held-out source skill,
feature availability, relative expert uncertainty, disagreement, latent-domain
share, and composition support. Suite and programme identities, target
outcomes, and oracle expert labels were excluded from the feature matrix.

The fixed learner was a standardized three-output Ridge regression predicting
the held-out Spearman of Standard, MHAR, and their ensemble. Alpha was selected
inside each outer training fold. The decoder chose the maximum predicted
utility, abstained below zero, ranked below `0.25`, and predicted otherwise.

## Results

| Evaluation | Numeric median | Standard median | Gain | 90% grouped-bootstrap CI | Harm: numeric / Standard | Gate |
|---|---:|---:|---:|---:|---:|---|
| Leave-one-suite-out | 0.0194 | 0.0256 | -0.0061 | [-0.0863, 0.0340] | 44.1% / 47.1% | fail |
| Leave-one-donor-out | 0.0000 | 0.0256 | -0.0256 | [-0.1016, 0.0251] | 32.4% / 47.1% | fail |

The router reduced harmful transfers, retained `87.5%`/`75.0%` of useful
edges, and avoided trivial always-abstain behavior. It nevertheless failed the
primary benefit requirement and the bootstrap lower-bound requirement in both
splits.

The failure is consistent with weak state signal rather than an aggressive
model choice:

- every primary inner fold selected the strongest Ridge regularization
  (`alpha=100`);
- primary out-of-fold predicted-versus-realized Spearman was `-0.132` for
  Standard, `0.048` for MHAR, and `-0.062` for ensemble;
- OCx24 and SpecGen showed local gains, while Alloy and SECCM regressed, so a
  pooled mean would hide the cross-suite failure;
- the oracle upper-bound median was only `0.0669`, confirming complementarity
  exists but is modest and difficult to identify from the current state.

## Decision

Do not search more model families on these same 34 edges and do not invest in a
larger OPD teacher yet. The next defensible work is upstream: collect genuinely
new independent edges and add target-free variables that describe endpoint
alignment, process conditions, active-site state, and calibrated uncertainty
in source validation. Only then should a numeric or LLM router be retrained.

The detailed auditable output is
`results/catalyst_numeric_expert_router.json`; the compact decision record is
`results/catalyst_numeric_expert_router_summary.json`.

## Verification

The focused numeric-router, OPD-router, attention, learned-policy, and transfer
suite passed with `94 passed, 1 skipped`. Formatting, lint, JSON parsing, and
diff-integrity checks also passed. The full repository run reached `182 passed,
19 skipped, 12 failed`; none of those failures involved this experiment. They
remain the repository's unrelated missing generated artifacts, registry/freeze
mismatches, figure exports, and checkpoint-compatibility failures.
