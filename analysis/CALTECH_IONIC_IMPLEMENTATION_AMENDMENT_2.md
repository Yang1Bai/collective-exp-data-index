# Caltech ionic-conductor state-matched backbone amendment

Frozen at `2026-07-16T23:03:19Z`, after a two-seed, three-step software smoke
test but before the 100-seed formal benchmark. Smoke outputs are explicitly
non-inferential and are excluded from all contrasts.

The exact-algorithm freeze said that target-model random seeds included the
policy identifier. That would allow two policies with an identical labelled
target state to receive different cross-validation folds and different
composition-only models. A direct source increment could then contain random
backbone variation.

For the formal run, every target fold and target-model seed is instead a hash
of the campaign seed, acquisition step, and sorted labelled target indices.
It does not contain the policy name or candidate scope. Therefore identical
labelled states have identical target folds, target gate, composition model,
and source-free predictions. Policies may diverge only after their selected
acquisitions differ. Source-specific augmented models use that same state seed.

No data rule, model hyperparameter, admission threshold, source weight,
candidate score, endpoint, comparison, or decision gate changes. The change is
strictly a common-random-numbers correction that makes the source increment
more isolated and the novelty fallback reproducible across policies.
