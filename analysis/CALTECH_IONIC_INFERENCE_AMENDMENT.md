# Caltech ionic-conductor inference-count amendment

Frozen at `2026-07-16T22:56:12Z`, before any source model, policy trajectory,
policy endpoint, or policy contrast was calculated. The exact algorithm file
has SHA-256
`3653c974a6fd7e82a2e4cb879c77b6abf059efb26610fcddf5327698cef924ac`.

The original design says that Holm correction covers seven named primary
AUC20 contrasts per candidate scope, but the explicit comparison lists contain
eight contrasts: two policy-validity, one same-property, one adjacent-
transport, one multisource, and three negative-transfer contrasts.

All eight explicitly named contrasts will therefore be included in one Holm
family within each candidate scope. This resolves the inconsistency in the
more conservative direction. No comparison is deleted, combined, or demoted,
and the exploratory novelty-band policy remains outside this confirmatory
family as originally stated in the implementation freeze.
