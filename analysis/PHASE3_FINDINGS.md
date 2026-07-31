# Phase 3 findings — downstream boundaries and claim discipline

## Molecular control

FreeSolv→AqSolDB removes 525 exact molecule overlaps, uses Morgan fingerprints,
and evaluates a fixed scaffold-disjoint test set. Mean ΔR² is 0.015
[0.008,0.023], inside the prespecified practical-equivalence band |ΔR²|<0.05.
It is a small predictive effect, not a physical null and not a useful borrowing
edge under the current criterion.

## OOD screening and sequential-discovery boundary

The frozen fixed-ranking OBELiX test gives a small directional OOD screening
signal: the mean fraction of the official pool inspected before the first
top-5% hit falls from 0.1208 to 0.0999, an absolute improvement of 0.0209
[0.0094,0.0346] after multiplicity correction. Only 38.3% of repeats improve,
the relative effect is 17.3%, and the target-only median is already within the
first 10% of the pool. The practical and repeat-consistency gates therefore
fail. A post-specified hard-composition subset is also directional but remains
exploratory and below the frozen practical boundary.

The completed frozen sequential experiment uses the official 110-candidate
OBELiX test pool and 100 paired seeds. Target-only and thermoelectric-prior
RF-UCB require means of 24.34 and 24.09 acquisitions to reach a top-5% target,
respectively: 0.25 saved [−1.30,1.82], one-sided sign-flip p=0.3889. Only 28%
of paired seeds improve, 49% tie, and every improvement/rescue gate fails. A
Random-Forest sensitivity is also null. The hard-OOD sensitivity saves 2.21
[0.97,3.49] acquisitions with ExtraTrees, but fails the 5-experiment, 25%,
60%-seed and Random-Forest-sensitivity gates.

Uniform random acquisition reaches the official-pool target in 15.50
acquisitions on average, 8.84 [4.57,12.90] earlier than target-only RF-UCB and
8.59 [4.14,12.99] earlier than thermoelectric-prior RF-UCB. This is a policy
diagnostic: it shows that the tested UCB policies are poorly matched to this
finite retrospective pool. It does not isolate mean ranking, uncertainty
calibration or iterative refitting as the cause, and it does not establish
random search as generally optimal.

Conclusion: average predictive gain, fixed OOD screening and sequential
discovery are distinct endpoints. The present OBELiX evidence establishes at
most a directional fixed-screening signal; it does not establish OOD-discovery
improvement, rescue or prospective laboratory acceleration.

## Claim boundary after the KIT and CALiSol tests

The completed analysis supports:

- failure of a strong direct coefficient to transport;
- one internally selected alloy borrowing candidate with a directionally
  favorable external estimate whose practical and absolute-utility gates fail;
- one independent Matbench null despite mechanical adjacency;
- one frozen, leakage-safe within-campaign adjacent-condition edge that passes
  every originally specified point-rule gate and has a 37.35% label-saving
  point estimate; a post-outcome interval of 21.84–49.91% crosses the 30%
  threshold;
- one frozen paper-disjoint CALiSol replication whose adjacent effect is only
  1.61% [−2.14%,4.21%], retains negative absolute R², saves only 16.9%, and
  fails article-fold and distance-ordering gates;
- monotonic local distance decay and a harmful source-scrambling placebo in
  KIT, explicitly not reproduced across CALiSol source articles;
- strong selectivity, including harmful edges;
- an artifact-gated distinction between weak, strong-conditional,
  non-transportable, and usefully borrowable relations.

It does not support:

- a universal cross-domain distance law;
- independent multi-domain rescue;
- independent cross-campaign rescue, including within liquid electrolytes;
- rescue of an entire scientific field;
- feature importance as microscopic mechanism;
- fixed-ranking OOD screening as sequential-discovery acceleration;
- prediction lift as OOD-discovery improvement or prospective laboratory
  acceleration.

The CALiSol experiment closes the most obvious missing test but closes it with
a null boundary, not a positive replication. “Rescue” is retained only as an
operational gate status, not as the paper's scientific claim. A future positive
independent replication would strengthen transportability, but its absence no
longer sits unexamined: the endpoint-resolved knowledge-borrowing map
quantitatively records the failure rather than hiding it in an average effect.

## Caltech external OOD signal and strategy synthesis

The later Caltech ionic-conductor benchmark adds a distinct positive endpoint.
After exact candidate-formula and target-DOI exclusions, the prespecified
OBELiX and ESTM rankings recover 2/8 and 3/8 external top-5% entities and each
recovers 3/3 in the n-limited hard-OOD subset. Mechanical and catalysis static
controls recover 0/8 externally, and all six wrong-source admission/weight
guards pass. The neighboring rankings therefore carry selective external OOD
proposal signal even though the frozen target-refitted residual policies add no
adaptive utility.

The two real neighbors recover different high-value entities. A post-outcome
round-robin or rank-consensus portfolio covers 5/8 external top-5% entities and
3/3 hard-OOD entities, compared with 2/8 and 3/8 for the individual sources.
This is component-level proof that preserving neighboring proposals can expose
complementary target hypotheses. It is not independent prospective evidence,
because the portfolio was constructed after inspecting Caltech outcomes. The
integrated selective neighborhood-borrowing strategy must next be frozen on an
outcome-unseen target.

## Protected temporal battery boundary and strategy update

The multi-stage lithium-ion program completed its protected release after all
Stage 1 source features, Stage 2 splits, applicability quantities, controls and
hypothesis cards were frozen. The paper-defined 23 °C endpoint was recovered for
135/138 Stage 2 cells. All three cells in one cycle-aging condition lacked the
required terminal `AT_T23` file, which an independent ZIP-member audit confirmed.
Because the frozen rule required at least two cells in every one of 23 condition
groups, the confirmatory temporal test is non-evaluable. No alternative
temperature, endpoint or condition was substituted.

A disclosed 22-group sensitivity retained the endpoint, learner, source
features, policies and condition-cluster inference while regenerating all
maximin training budgets over the observable groups. CCA-v2 improved RMSE by
3.47% versus target-only [-0.59%,9.30%], Holm p=0.3692, and was 2.80% worse than
adjacency-only [-8.79%,5.06%], p=0.766. Its training-only hard gate activated for
only 4/22 conditions and reverted to target-only for every cycle-aging test.

The simpler adjacency policy was therefore selected after outcome inspection
for an explicitly post hoc strategy diagnostic. Adding the precomputed Stage 1
degradation prediction to the target learner reduced equal-stratum condition
RMSE by 6.12% [2.56%,9.16%] versus target-only, Holm p=0.0108. Calendar and cycle
effects were both positive (7.95% and 4.30%), absolute held-out R² was positive
in both strata, and 17/22 condition groups improved. The effect also survived
wrong-property, within-type shuffled-source and equal-capacity random-feature
controls after correction. Independent reconstruction reproduced all estimates,
bootstrap rows, sign-flip p-values and file hashes.

This is not a rescued primary result: the focus on adjacency-only was selected
after seeing the sensitivity summary, and the 22-group plan was necessarily
regenerated after endpoint missingness was known. It is nevertheless a strong
method-development result. The actionable lesson is to qualify a neighboring
experimental source upstream, transfer its continuous prediction, and use local
support as a smooth diagnostic rather than an over-conservative cross-stratum
hard veto. That candidate now requires a new outcome-unseen target.
