# From neighborhood borrowing to scientific exploration

## 2026-07-30 upgrade: transfer the mixture relation, not a generic donor feature

The BambooMixer method audit produced a new executable route for formulation
tasks. The source model now represents each liquid formulation as an unordered,
molar-fraction-weighted mixture and explicitly retains temperature,
concentration and state interactions. The learned source relation is frozen
before a new-salt target is scored; a few target labels may fit only a
shrinkage calibration correction.

The formal method-development benchmark uses 10,407 source measurements from
22 salts and an external LiAsF6 programme with 1,827 measurements from 176
exact formulations. LiAsF6 is absent from source training. Zero-shot external
performance is log \(R^2=0.732\), raw \(R^2=0.629\) and
Spearman \(\rho=0.871\). Relative to a state-only model, formulation-grouped
bootstrap estimates give 28.64% lower log-RMSE
[24.03%,33.52%] and a rank gain of 0.160 [0.132,0.188]. Relative to a
chemistry-permuted source, the corresponding gains are 27.16%
[22.78%,31.90%] and 0.134 [0.108,0.162].

Removing LiPF6 worsens log-RMSE by 16.38% [12.66%,20.24%] relative to the
complete source, demonstrating a specific adjacent-salt contribution. Yet the
complete 22-salt portfolio also outperforms LiPF6 alone, showing that
neighbourhood knowledge and diverse state coverage are complementary. The
full model beats state-only prediction on both error and ranking in 7 of 9
leave-one-salt-out targets; the two remaining targets retain rank gains but
fail the error gate and must be routed to ranking or abstention.

This result changes the method priority. For mixture-valued recipients, test a
physics-aware, permutation-invariant response relation before residual feature
injection or generic neural pretraining. The implementation, controls, claim
guard and exact results are recorded in
`BAMBOOMIXER_METHOD_ADOPTION_2026-07-30.md`. Because the external target was
already public and its published result had been inspected, this is verified
method development, not an independent confirmatory edge.

## Decision forced by the completed OBELiX campaign

The current result does not reject neighborhood knowledge. It rejects the
assumption that appending one source prediction to a tree surrogate and using
mean-plus-one-standard-deviation UCB automatically converts that knowledge into
discovery acceleration. Fixed ranking was directionally favorable, sequential
acquisition was null, and uniform random acquisition was substantially faster.
The next method must therefore separate four objects that the first protocol
combined:

1. target-model exploitation;
2. target-model uncertainty;
3. source-task relevance;
4. candidate-space coverage.

No source-aware policy is scientifically interpretable until its target-only
acquisition backbone beats the random reference.

## Methods worth testing, in priority order

### 1. Cross-validated residual shrinkage

Write the target response as a target-only prediction plus a scaled source
prediction or source residual. Estimate the source coefficient only within
target-training folds and shrink it toward zero. This is safer than allowing a
forest to use a source feature through unrestricted interactions: the amount,
direction, and uncertainty of borrowing become explicit. A wrong source should
receive a coefficient near zero.

### 2. Outcome-calibrated rank fusion

Source and target properties have unrelated numerical scales. Convert target
and source predictions to ranks, infer the source direction and usefulness
from the initial target labels, and fuse the ranks with a weight that can
collapse to zero. This directly tests whether a neighbor identifies a useful
region even when it cannot calibrate the target property.

### 3. Safe acquisition portfolio

Treat greedy mean, calibrated exploration, composition diversity, source-aware
ranking, and uniform random sampling as competing policies. Update their weights
online from observed target rewards. This is the most direct response to the
random-control result: random exploration remains available when the learned
surrogate or source prior is misleading. Bayesian model averaging has already
been used to adaptively choose models during materials exploration
([Balachandran et al., 2018](https://doi.org/10.1103/PhysRevMaterials.2.113803)).

### 4. Novelty-gated borrowing

Use source information only in candidate-space regions that are poorly covered
by target data and in which initial target labels support the source direction.
Elsewhere, fall back to the validated target-only policy. This converts a
candidate source-to-target relation from a global edge weight into a local
gate.

### 5. Multi-information-source Bayesian optimization

Co-kriging, multivariate Gaussian processes, and cost-sensitive knowledge
gradient can model multiple information sources explicitly and have improved
materials optimization in controlled examples
([Herbol, Poloczek and Clancy, 2020](https://doi.org/10.1039/D0MH00062K)).
They are not the first method to deploy here. Source and target compositions do
not overlap, the representation is high-dimensional, and task correlation may
be weakly identified. Recent analysis shows that standard multi-task Gaussian
processes can misestimate even simple affine task relationships under finite,
non-co-located designs; learned task-specific means/scales, non-negative task
covariance, and partial co-location are safer variants
([Hvarfner et al., 2026](https://arxiv.org/abs/2607.09073)).

### 6. Shared representations and meta-learned acquisition

A task-conditioned encoder or meta-learned acquisition function could learn
recurring transfer patterns across many campaigns rather than one edge.
Meta-learning an acquisition function has been demonstrated on families of
related optimization tasks
([Volpp et al., 2019](https://arxiv.org/abs/1904.02642)), and active transfer
with gradual design-space expansion has been demonstrated in a materials design
problem
([Kim et al., 2021](https://doi.org/10.1038/s41524-021-00609-2)). This route
requires many source tasks and leave-one-task-out validation; with the current
number of independent campaigns it is a later-stage experiment, not the first
baseline.

## First signal-anatomy result (post-result diagnostic)

The 100-seed diagnostic is recorded in
`results/neighbor_transfer_signal_summary.json`. In the 110-candidate official
pool, exact uniform-random ordering has an expected first-hit rank of 15.86.
The frozen thermoelectric prior alone hit at rank 3; equal target/source rank
fusion averaged 6.64; composition novelty averaged 6.36; target posterior mean
averaged 28.01; and mean-plus-one-spread UCB averaged 34.68. The hard-OOD pool
showed the same ordering tendency.

The ensemble spread was positively associated with absolute target error
(mean Spearman 0.423 in the official pool) but negatively associated with the
target value (−0.279). Thus the spread contains error information, yet adding
it with a positive coefficient steers a maximization policy toward difficult,
low-valued candidates. This is the clearest observed reason that the tested UCB
policy underperformed random acquisition.

The source signal is not globally strong enough to claim discovery. Its
official-pool outcome Spearman correlation is only 0.131, and its first hit at
rank 3 is driven by one Li–Y–Br composition while its first two candidates are
low-valued Li–Ge–S–Se compositions. Only one of six true top-5% candidates lies
in the first 10% of the raw source ranking. Equal rank fusion has broader
top-10% recall and is therefore a more credible method candidate than the
isolated first-hit result.

Estimating source weight from only the initial 30 target labels is also noisy:
the seed-wise source correlation spans approximately −0.15 to 0.63, and the
simple credibility-weighted fusion is worse than equal fusion. Source
credibility should therefore be shrunk using multiple campaigns or a hierarchical
prior, not estimated independently from each small target subset.

These findings selected the exact policy benchmark in
`neighbor_transfer_policy_design.json`. It compares target mean, novelty,
source-only ranking, adaptive target/source rank fusion, wrong-source controls,
the failed UCB policy, and random acquisition. Because these policies were
chosen after seeing the diagnostic, OBELiX can only select a candidate method;
independent validation remains mandatory.

## Completed policy benchmark and decision

The Balam benchmark completed as job 70666 and passed the design, input,
checksum, trajectory, seed-coverage, and completion audits. Composition novelty
is the only validated target-only backbone: it saves 12.08 acquisitions
[9.74,14.52] versus random in the official pool and 8.82 [7.10,10.58] in hard
OOD. Target-mean greedy is worse than random in both pools.

Thermoelectric static screening reaches the first hit at step 3 and beats
random, but its advantage over composition novelty is negligible (0.42
[-0.10,0.98] official; -0.24 [-0.59,0.14] hard OOD). It also saves only two
acquisitions relative to the catalysis static control, below the frozen
five-acquisition source-specificity gate. The 100 static-policy rows are the
same deterministic trajectory, not 100 independent target datasets.

Target/source/novelty fusion passes its prespecified contrast against target
mean, but that comparator is invalid. In the post-hoc comparison that matters
for attribution, fusion is not better than novelty for first hit and is worse
in hard OOD. It does recover more of the official-pool top-5% set by acquisition
40, making it a candidate for an independently frozen breadth-of-recall
endpoint, not evidence of confirmed discovery acceleration. The complete audit
is in `NEIGHBOR_TRANSFER_POLICY_VALIDATION.md` and
`results/neighbor_transfer_policy_validation.json`.

## The recommended benchmark

The benchmark is hierarchical:

1. **Policy validity:** use composition novelty as the current target-only
   baseline and require it to beat uniform random in each held-out campaign.
2. **Incremental borrowing:** compare the source-aware version directly with
   composition novelty, not with the failed target-mean policy.
3. **Negative-transfer safety:** require shuffled and wrong-source weights to
   collapse toward zero and prohibit aggregate harm.
4. **External transport:** freeze the method before a new target, time block,
   article, or prospective campaign.
5. **Scientific insight:** before revealing the selected candidate's outcome,
   state the source-derived hypothesis about a composition family, condition,
   or mechanism and test it against a matched control.

The first implementation is the outcome-aware but explicitly diagnostic signal
anatomy in `analyze_neighbor_transfer_signals.py`. Its purpose is to decide
whether the next executable method should emphasize residual transfer, rank
fusion, diversity, or uncertainty repair. It cannot create a new confirmatory
OBELiX claim.

## Independent external benchmark completed

The next test is no longer another OBELiX reanalysis. The target is the
independent Caltech experimental Li-ion conductivity database: 571 raw rows,
566 eligible measurements, 483 canonical compositions, 229 identity/article
components, 339 development entities, 144 article-disjoint candidates, and 58
hard-OOD candidates. All target gates pass. Removing every target composition
or DOI leaves 181 leakage-safe OBELiX entities; ESTM, Borg, and OCx retain 870,
395, and 212 entities, respectively.

The primary endpoint is cumulative recovery of the true top-5% region through
20 acquisitions, not one lucky first hit. The target-only backbone is
composition novelty. Source influence enters only as the cross-validated rank
correction from a composition-plus-source model relative to the same
composition-only model. A source needs positive error reduction in at least
three of five article-grouped folds, at least 2% median relative RMSE gain, and
positive mean gain; otherwise its weight is exactly zero. At most two sources
enter, and wrong mechanical, catalysis, and shuffled sources must be admitted
in fewer than 20% of steps with mean weight below 0.10.

The 100-seed formal calculation completed as Balam Job 70740 and the source
models and static campaigns were replayed in the same pinned Linux environment
as Job 70767. Portable recomputation then verified 120,000 trajectory rows,
184,000 gate rows, 3,000 campaign-utility rows, and 16 frozen contrasts.

The primary adaptive-policy result is null. None of the OBELiX same-property,
ESTM transport-neighbor, or multisource residual policies passes the frozen
statistical, practical, consistency, first-hit, absolute-recall, and two-scope
requirements. Composition novelty is not a universal backbone: it is worse
than random in the 144-candidate external pool, while improving hard-OOD AUC20
by 8.32 [6.12,10.26] but missing the frozen recall20=0.50 gate. Target-mean
steering is harmful in hard OOD.

The safety mechanism nevertheless behaves selectively. Across single-source
policies, the two real neighbors are admitted in 35.5% of steps with mean
weight 0.168, versus 16.8% and 0.063 for the three wrong controls; every frozen
wrong-source harm guard passes. This supports source-admission selectivity under
the encoded alignment rule, not an ordering of source skill or useful
acquisition.

The prespecified static rankings expose where the policy transformation fails.
OBELiX and ESTM exceed random, shuffled, mechanical, and catalysis rankings in
both scopes after exact composition and DOI exclusions. In the full external
pool their AUC20 values are 33 and 45, versus 11.25 for random; in hard OOD they
are 38 and 51, recover all true top-5% entities by acquisition 20, and exceed
random AUC20=9.87. These are descriptive results because no primary
static-source attribution contrast or independent-dataset interval was frozen.

After outcome inspection, a target-model-free OBELiX/ESTM portfolio recovered
five of eight external top-5% entities by acquisition 20 (recall20=0.625) and
all hard-OOD top entities. This is method selection only. The next test should
freeze round-robin shortlist allocation and rank consensus on outcome-unseen
targets, compare them with each constituent neighbor, composition novelty,
random, and matched wrong-source portfolios, and keep target-model refitting out
of the primary policy. That test was subsequently completed on Starrydata and
TRI; neither target passed the complete policy gate.

Taken together with the KIT predictive result, these observations provide
component-level proof of feasibility for selective neighborhood borrowing:
qualified neighbors can improve prediction, retain external OOD-ranking signal,
remain complementary, and be screened against wrong sources. The integrated
portfolio now has outcome-unseen null/boundary tests but no positive policy
confirmation. A genuinely temporal or prospective target is required before it
can support an independent acceleration claim.

## Completed CCA family-first method development

The local multiplicative gate did not improve transfer. Combining target OOD,
source support, and local concordance as multiplicative rewards reduced
external AUC20 to 0.96, compared with 69 for static entity consensus. In hard
OOD, wrong and shuffled sources could exploit composition geometry. This rules
out the naive idea that farther candidates or more local gates necessarily make
borrowing safer.

The successful redesign separates source admission from exploration allocation:

1. qualify the source globally under leakage, wrong-source, and shuffle tests;
2. preserve the admitted source ranks and combine them only by consensus or
   round-robin;
3. allocate the first pass across connected formula/DOI/ICSD components;
4. use OOD distance as a scope, quota, or tie-breaker rather than a multiplier;
5. abstain or fall back to novelty/random when source controls are competitive;
6. attach a source-specific, prospective falsifier to every proposed region.

On Caltech, this CCA family-first policy increases distinct-component AUC20
from 47 to 60 externally and from 36 to 39 in hard OOD, recovering 4/4 and 2/2
top components by acquisition 20. Wrong-source AUC20 is 6/18; 5,000 shuffled-
rank pairs give conditional p=0.0020/0.0030. Entity recall falls from 5/8 to
2/8 externally and from 3/3 to 1/3 in hard OOD, so the gain is specifically
broader scientific-region exploration rather than generic ML improvement.

This is outcome-informed algorithm selection. The complete rule, component
definition, breadth and entity endpoints, source admission, controls, and
hypothesis cards must now be frozen on an outcome-unseen target.

## What would count as success

Prediction success, OOD screening success, sequential success, and scientific
hypothesis success remain separate. The strongest future result would show that
a safe source-aware policy beats random and target-only policies on an unseen
campaign, then yields a predeclared, independently confirmed relation that the
target data alone would not have suggested. Anything less should be labelled as
method development or directional screening rather than discovery of new
science.
