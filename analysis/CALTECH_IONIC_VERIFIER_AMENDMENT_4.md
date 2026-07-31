# Caltech ionic-conductor static-policy verifier amendment

Frozen at `2026-07-17T20:21:11Z` after Balam job `70740` completed the formal
campaign computation but failed in the final independent verifier. No policy
utility or scientific contrast was inspected to make this change.

The verifier incorrectly required each real static-source policy to have one
identical trajectory across all 100 seeds. The frozen acquisition rule ranks
the fixed source score first, but breaks exact source-score ties using
composition novelty relative to the seed-specific labelled target set. Static
policies may therefore vary by seed when a source model produces tied scores;
OCx triggered this valid case.

The corrected verifier refits every leakage-safe source model, reproduces every
static and shuffled-static campaign for all seeds and both candidate scopes,
and compares the selected index, target outcome, hit indicator, acquisition
score and novelty at every step. It also independently checks the source OOF
quality table. This is strictly stronger than demanding a single trajectory
and does not change any source model, campaign, endpoint, contrast, or decision
gate. Hash-keyed formal checkpoints from job `70740` remain valid and are
reused.
