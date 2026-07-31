# Pre-outcome verifier lifecycle amendment

The original pre-outcome verifier and protocol were hashed before Stage 2
release. After the protected experiment closed, the experiment registry
correctly changed CS13 from `preoutcome-frozen` to `complete-boundary`. The
original verifier had treated the transient registry status as an immutable
pre-outcome fact, so rerunning it after legitimate lifecycle progression failed
even though every frozen scientific file retained its original hash.

This post-release verifier amendment preserves and checks the original verifier
hash recorded in the freeze
(`bcf5a6791b7ca788daec45030e2227d660415d65da61ca530eb28ba6a9cb78be`),
continues to require the original protocol and every scientific freeze hash,
and accepts only the two documented lifecycle states: `preoutcome-frozen` or
`complete-boundary`. In the latter state it additionally requires the Stage 2
release audit to exist, to report `non-evaluable-stage2-release`, and to be
registered as evidence.

No endpoint, design, outcome, split, model, comparison, threshold, or original
freeze hash is changed by this lifecycle-only amendment.
