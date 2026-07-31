# Caltech external ionic-conductor policy validation

## Decision

The verified primary result is a null for adaptive source-aware acquisition.
No same-property, transport-adjacent, or multisource residual policy passes the
frozen statistical, 20% practical, 60% consistency, first-hit non-inferiority,
absolute-recall, and two-scope requirements. The result does not validate a new
source-to-policy edge.

This null does not mean that adjacent sources contain no OOD ranking signal.
Both prespecified real-neighbor static rankings are far stronger than random,
shuffled, mechanical, and catalysis rankings in both candidate scopes. The
static result is prespecified retrospective evidence rather than an independently
confirmed policy edge, however,
and it is not a clean test of source credibility. The adaptive null cannot
separate weak source models, a weak target surrogate, and the residual-gating
policy itself. It therefore rejects the tested policy stack, not a uniquely
identified conversion mechanism.

## Verification

Formal Balam job `70740` produced 120,000 trajectories, 184,000 gate records,
3,000 campaign-utility rows, and 16 primary contrast rows. Job `70767` refit
all source models and replayed every static and shuffled-static campaign in the
same pinned Linux environment. Portable verification then independently
recomputed every trajectory utility, contrast, interval, multiplicity
correction, and gate summary. The final status is `VERIFIED`.

## Frozen primary results

Composition novelty is scope-dependent rather than a generally valid target
backbone. In the complete external candidate pool it obtains AUC20 = 0 versus
11.25 for random and reaches essentially none of the true top 5% by acquisition
20. In hard OOD it obtains AUC20 = 18.19 versus 9.87 for random, a gain of 8.32
[6.12, 10.26], Holm p = 0.0008, but recall at 20 is 0.443 and misses the frozen
0.50 absolute-recall requirement.

Adding target-mean steering to novelty is harmful in hard OOD: AUC20 decreases
from 18.19 to 14.33, with a mean gain of -3.86 [-5.45, -2.30]. It remains near
zero in the complete external pool. Thus `safe_target_novelty` is not a valid
universal comparator despite its cross-validation gate.

Against that target-only policy:

| Source-aware policy | External AUC20 gain | Hard-OOD AUC20 gain | Decision |
|---|---:|---:|---|
| same-property OBELiX residual | -0.06 [-0.30, 0.12] | +1.10 [-0.38, 2.59] | fail |
| transport-adjacent ESTM residual | -0.06 [-0.23, 0.07] | -0.07 [-1.11, 0.91] | fail |
| safe multisource residual | -0.09 [-0.34, 0.09] | +1.27 [-0.75, 3.22] | fail |

All wrong-source weight guards pass. Borg, OCx, and shuffled-source admission
rates range from 0.126 to 0.197, with mean weights from 0.046 to 0.077. This is
a real negative-transfer safety result, although the hard-OOD Borg admission
rate of 0.1965 passes the 0.20 boundary narrowly.

The gate's source-admission ordering is physically plausible but not
decision-effective. Across the
single-source policies, OBELiX and ESTM are admitted in 35.5% of acquisition
steps on average with mean weight 0.168, compared with 16.8% and 0.063 for the
three wrong controls. This ordering is not a measure of fitted source skill:
source-domain out-of-fold R2 is 0.065 for OBELiX, 0.257 for ESTM, 0.164 for
Borg, and 0.543 for OCx. The wrong-domain OCx control therefore has the highest
measured source-model skill. Admission frequency should not be called
credibility, and the experiment does not isolate why plausible source ordering
fails to improve acquisition utility.

## Prespecified static rankings: retrospective external signal

The primary comparison family did not include static-source attribution, so
the following is prespecified-policy but post-result descriptive evidence, not
a new confirmatory edge.

| Policy | External AUC20 / first hit / recall20 | Hard-OOD AUC20 / first hit / recall20 |
|---|---:|---:|
| OBELiX same-property static | 33 / 1 / 0.250 (2/8) | 38 / 2 / 1.000 (3/3) |
| ESTM transport-neighbor static | 45 / 5 / 0.375 (3/8) | 51 / 1 / 1.000 (3/3) |
| shuffled OBELiX static | 11.75 / 15.11 / 0.139 | 11.59 / 13.35 / 0.360 |
| uniform random | 11.25 / 15.77 / 0.139 | 9.87 / 15.30 / 0.323 |
| Borg mechanical static | 0 / 41 / 0 | 3 / 18 / 0.333 |
| OCx catalysis static | 0 / 41 / 0 | 0 / 41 / 0 |

The real neighbors exceed every random or wrong static reference in both
scopes. Exact target compositions and target DOIs were removed from every
source fit, so this pattern cannot be explained by direct material or article
retrieval. However, candidate-seed variation is not independent-dataset
uncertainty, no static-source decision gates were frozen, and the hard-OOD
recall of 1.000 means three of three entities rather than a large-sample ceiling.

## Post-result method selected for independent testing

OBELiX and ESTM recover complementary high-value compositions: within the first
20 external candidates, OBELiX finds two of eight true top-5% entities and ESTM
finds three. A target-model-free round-robin union finds five of eight, giving
recall20 = 0.625, AUC20 = 53, and first hit at acquisition 1. A rank-consensus
union has the same recall, AUC20 = 58, and first hit at acquisition 3. Both
recover all three hard-OOD top entities by acquisition 20.

These portfolio strategies were created after inspecting the verified Caltech
outcome and are method-development only. Their 5/8 versus 2/8 and 3/8 coverage
demonstrates complementarity on the observed target, but not independent
acceleration. Their role is to select the next frozen method:

1. retain each neighbor as an independent shortlist rather than injecting it
   into a weak target surrogate;
2. allocate acquisitions across neighbor shortlists using round-robin or
   consensus ranking;
3. preserve diversity explicitly and use target labels to retire a source only
   after demonstrated harm;
4. compare against random, composition novelty, each individual neighbor, and
   matched wrong-source portfolios on a new outcome-unseen target.

## Manuscript-safe interpretation

Adjacent-domain knowledge can contain selective OOD ranking information even
when it does not improve target-model fitting or survive target-refitted
sequential acquisition. The Caltech result rejects the tested residual-gating
policy stack, not neighborhood borrowing itself; because source and target
predictive quality are weak or uneven, it does not uniquely localize failure to
the gate. It strengthens the paper's
endpoint separation: average prediction, fixed screening, adaptive search, and
new-science discovery are different claims.

Together with the KIT predictive gain, the static and portfolio results provide
component-level proof that neighboring domains can improve a target and generate
complementary candidate proposals when their signals are qualified and
preserved. What remains untested is the integrated portfolio on an outcome-
unseen target.

The external benchmark does not establish prospective acceleration, new
science, independent-dataset population generality, or field-wide rescue. The
next claim-bearing test must freeze the source-portfolio policy on a new target
before revealing its outcomes.
