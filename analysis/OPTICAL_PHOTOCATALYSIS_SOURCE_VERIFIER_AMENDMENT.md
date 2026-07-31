# Optical-photocatalysis source verifier amendment

Frozen on 2026-07-25 after the remote donor artifacts had been downloaded but
before any recipient hydrogen-evolution model or aggregate recipient outcome
analysis was run.

## Trigger

The first portable verification reproduced every donor out-of-fold \(R^2\)
exactly. Three of five Spearman correlations were also exact, whereas quantum
yield differed by \(1.5111\times10^{-5}\) and log extinction differed by
\(1.3741\times10^{-7}\) after the OOF floating-point table was written to and
read from CSV. Repeating the frozen scaffold bootstrap from the CSV gave a
maximum absolute interval-bound difference of \(3.0618\times10^{-5}\).

These differences arise from tie-sensitive ranks after floating-point CSV
serialization. They are orders of magnitude smaller than the source admission
margin: the affected quantum-yield Spearman correlation is approximately
0.541 versus the frozen threshold of 0.15, and its lower bootstrap bound is
approximately 0.507 versus the frozen threshold of zero.

## Amendment

Only the portable verifier comparison for Spearman statistics is amended to
use an absolute serialization tolerance of \(5\times10^{-5}\). The verifier
continues to recompute the point estimate and all 1,000 scaffold-bootstrap
replicates from the downloaded OOF rows. It records the observed differences.

No donor model, feature, fold, random seed, OOF prediction, property gate,
admission decision, recipient analysis, or scientific claim is changed.

## Fixed artifact hashes at amendment

- Pre-amendment verifier SHA-256:
  `4160ceee0153af6ba46585a7a746f3eb80bc87ff6b4868c4680e233f6d5318ee`
- Donor summary SHA-256:
  `88c543e77ebbc4961b9d000f189a7cdc28e273f908f10769f1df08f8d62e5570`
- Donor OOF table SHA-256:
  `dca3ac298a877eb73ff785f75a0204fa13468b2bf68ae1a414e8e309af9ee59d`
- Recipient feature table SHA-256:
  `52baab7fa107b43a141e4bfac8cc5a73ae54798b75a3e0a2ba6e3da7358584f9`
