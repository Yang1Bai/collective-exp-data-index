# Validation of the post-diagnostic neighborhood-transfer policy benchmark

## Overall assessment: share only as exploratory method selection

The Balam result is complete, hash-consistent, and internally reproducible. It
does not establish neighbor-specific OOD discovery acceleration. It identifies
composition novelty as the valid target-only acquisition baseline and selects
target/source/novelty rank fusion as a candidate for an independently frozen
breadth-of-recall experiment. The completed frozen OBELiX UCB null is unchanged.

## Provenance and completeness

- Balam job: `70666`, completed with exit code `0:0` on `balam002`.
- Frozen design SHA-256:
  `4f3d64501630e55d0ae38f2ee1a70519e51a04d5eff72253cfdce08fc0f2744d`.
- Frozen input SHA-256:
  `a2ccdd88de18ccdc4e11d2f87026938d42dfcd3b56567b7cc912a27905f79b7b`.
- Verified coverage: 2,000 first-hit rows, 80,000 trajectory rows, 20 named
  contrasts, 100,000 bootstrap rows, and 2,000 secondary-utility rows.
- Every downloaded artifact matches the remote checksum manifest.

## What the prespecified comparisons show

| Question | Official test | Hard OOD | Decision |
|---|---:|---:|---|
| Target mean vs random | -8.63 saved [-12.93,-4.40] | -4.23 [-6.78,-1.73] | target-mean backbone invalid |
| Composition novelty vs random | +12.08 [9.74,14.52] | +8.82 [7.10,10.58] | passes every development gate |
| Thermoelectric static rank vs random | +12.50 [10.25,14.90] | +8.58 [6.92,10.30] | useful fixed screening on this pool |
| Thermoelectric vs catalysis static rank | +2.00 [2.00,2.00] | +2.00 [2.00,2.00] | fails the five-acquisition specificity gate |
| Target/source/novelty fusion vs target mean | +19.94 [16.54,23.20] | +10.39 [8.66,12.10] | passes, but comparator itself is invalid |

Positive values are acquisitions saved by the first policy. Intervals and
Holm-adjusted tests are conditional on the fixed OBELiX candidate pool and the
100 campaign seeds; they are not uncertainty over new datasets.

## The comparison that determines attribution

The frozen benchmark compared source-aware policies with target-mean greedy,
but target-mean greedy loses to random. Composition novelty is therefore the
appropriate target-only backbone for attributing an incremental source effect.
That comparison was not prespecified and is reported descriptively only.

- Thermoelectric static rank versus composition novelty saves 0.42
  acquisitions [-0.10,0.98] in the official pool and -0.24 [-0.59,0.14] in
  hard OOD.
- Target/source/novelty fusion versus composition novelty saves -0.77
  [-1.68,0.13] acquisitions in the official pool and -2.66 [-3.58,-1.75] in
  hard OOD. Thus fusion does not improve the primary first-hit endpoint.
- In the official pool, fusion does improve breadth: cumulative-hit AUC is
  34.12 higher [27.64,40.18], mean top-5% recall at 40 acquisitions rises by
  0.225 [0.187,0.265], and mean hits at 20 rise by 0.95 [0.71,1.18].
- That breadth advantage does not reproduce in hard OOD: cumulative-hit AUC is
  -2.61 [-5.27,0.01] and hits at 20 are -0.35 [-0.48,-0.22] relative to
  novelty; both policies reach all three hard-OOD hits by 40.

The endpoint therefore changes the method choice. Novelty is best supported
for early OOD exploration. Fusion is only a candidate for broad recovery in an
unseen official-like pool.

## Statistical and scientific blockers

1. **Outcome reuse.** The policy family was selected after inspecting OBELiX
   outcomes. No favorable result is confirmatory on the same pool.
2. **Pseudo-replication for static policies.** Each static policy has exactly
   one trajectory across all 100 seeds. The thermoelectric first hit is the
   same Li-Y-Br candidate at step 3 every time. Zero-width static-vs-static
   intervals describe deterministic ranks, not 100 independent discoveries.
3. **Source specificity fails.** The catalysis control reaches the same
   Li-Y-Br candidate at step 5, so thermoelectric adjacency does not clear the
   frozen practical separation gate.
4. **No source increment over the valid baseline.** Source-only and fusion
   policies do not beat composition novelty on first hit in both scopes.
5. **Single finite target pool.** Campaign seeds vary initialization and model
   randomness, not the target dataset. They cannot establish transport to a
   new electrolyte database.
6. **No new-science endpoint.** Finding a known high-conductivity record in a
   retrospective pool is not a preregistered source-derived hypothesis or a
   prospective discovery.

## Method selected for the next independent test

The next experiment should be frozen on an unseen target dataset, article, or
time block before outcomes are inspected. It must compare:

1. uniform random acquisition;
2. composition novelty as the mandatory target-only baseline;
3. thermoelectric static screening;
4. target/source/novelty rank fusion;
5. catalysis, alloy, and shuffled-source controls.

First-hit efficiency and cumulative recall should be separate prespecified
endpoints with multiplicity control. Neighbor borrowing is admitted only if it
beats composition novelty, separates practically from every wrong-source
control, and repeats across independent target campaigns. A new-science claim
additionally requires a source-derived hypothesis written before revealing the
target outcome and tested against a matched control.
