# Optical supervised borrowing verifier amendment

Date: 2026-07-26

## Trigger

Balam job 71572 completed all frozen source-model training but the independent
source verifier stopped before target-model development. Pandas 2.3 had
materialized `target_key` as a NumPy object array in the trusted NPZ archive.
The verifier used `allow_pickle=False`, so NumPy refused to read that string
array. No recipient HER outcome had been accessed.

## Frozen scope

- Producer implementation SHA-256:
  `759998c27339b8c2301834d70fd0701240c04d2d09da3e94f2c5f99e2d649543`
- Pre-amendment verifier SHA-256:
  `d08cb57a4f820f273777456f51af4f7f659dce39b78c4bd0a38751cd8434e112`
- The trained checkpoints, source predictions, embeddings, OOF rows, source
  skill gates, target draws, OOD scopes, development policies and release gate
  are unchanged.
- The source archive SHA-256 remains checked against the producer summary
  before it is opened.

## Amendment

The verifier and downstream development reader may load the already
hash-anchored NPZ archive with pickle support only to recover `target_key`.
They then require that array to have string or object dtype and, for object
dtype, require every member to be a Python string. Every embedding and support
array must have a numeric dtype, the frozen shape, finite values and the
original semantic checks. This amendment changes no scientific method or
acceptance threshold and does not authorize opening the blind recipient
outcomes.

## Float32 boundary amendment

Balam job 71574 reproduced all 21 checkpoint hashes and all packaged result
checksums, then stopped because the verifier upcast support values to float64
before recomputing the reliability gate. Eight of 668 recipients had a stored
float32 support value representing the exact frozen threshold of 0.2. The
upcast interpreted its approximately 3e-9 representation offset as positive,
and the geometric-mean square root amplified it to at most 8.14e-5. The
producer's original float32 computation and the stored reliability vector are
bitwise identical for all 668 rows.

- Pre-amendment verifier SHA-256:
  `e0b844f7429d16833899552fba0aad04bdc30ddf2697649e9166e4ff8706eecf`
- The verifier now reproduces the producer's float32 arithmetic and requires
  exact array equality rather than weakening the tolerance.
- No target OOD result or blind recipient outcome was accessed before this
  amendment.

## Insufficient-scaffold abstention amendment

Balam job 71575 passed the complete source-representation verification, then
stopped during the target-development stage because a frozen 30-label draw had
only one molecular scaffold. Across the 900 outcome-independent frozen draws,
16 have fewer than three training scaffolds. Nested adapter selection requires
at least three: after an outer scaffold is held out, the fit side must retain
at least two scaffolds for inner cross-fitting.

The frozen draws are not replaced. For every draw with fewer than three
training scaffolds, all donor adapters must abstain by selecting exactly zero
correction, so their predictions equal the target-only hurdle baseline. The
target-only prediction is still evaluated normally. These draws remain in all
aggregate metrics and therefore can only dilute, not create, a positive
borrowing result. The rule depends only on molecular scaffold identities, was
defined before any development metric was produced, and does not open the
blind recipient outcomes.
