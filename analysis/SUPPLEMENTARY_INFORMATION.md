# Supplementary information

## Falsification-gated borrowing routes neighbouring experimental knowledge to out-of-distribution prediction, screening or abstention

This document is the reporting companion to `MANUSCRIPT_DRAFT_STREAMLINED.md`. It records
the evidence hierarchy, frozen decision rules, negative controls, amendments,
and reproducibility entry points. Exact machine-readable values remain in
`analysis/results/`; rounded values below are for readability.

## S1. Evidence hierarchy

The analyses distinguish six claims that are often conflated.

| Level | Question | Minimum evidence used here | What it does not establish |
|---|---|---|---|
| Pooled regularity | Do two fitted or measured quantities co-vary in one assembled sample? | grouped estimates, uncertainty, family and threshold sensitivity, artifact null | coefficient transport or mechanism |
| Coefficient transport | Does an unchanged source coefficient remain calibrated in a held-out campaign? | independent campaign, unchanged source fit, overlap audit, group bootstrap | usefulness of a flexible source-prediction feature |
| Knowledge borrowing | Does an out-of-sample source prediction reduce target error? | identical baseline/augmented target split, cross-fitted source feature, leakage audit, uncertainty and placebo | positive absolute utility or practical label saving |
| OOD screening utility | Does a fixed ranking find a true high-value held-out candidate after screening less of the pool? | fixed outcome-hidden pool, top-5% definition, repeated target subsets, multiplicity, wrong-source and shuffled controls | sequential discovery acceleration |
| Sequential discovery utility | Does the advantage survive acquisition, target-label revelation, and model refitting? | paired initial labels, fixed budget and stopping rule, refit-after-each-step policy, sensitivity learner, random acquisition reference | prospective laboratory acceleration or general acquisition-policy superiority |
| Local task rescue | Does borrowing make a scarce-label task practically usable? | every originally specified frozen gate in Table S3 | cross-campaign or universal transfer |

The term *significant* is reserved for a named inferential procedure. It is not
used as a synonym for rescue. Positive, null, equivalent, harmful, and
unresolved edges remain in the map.

These evidence levels implement a selective neighborhood-borrowing strategy.
Sources are nominated without target outcomes, qualified under identity- and
provenance-aware evaluation, and matched to the decision endpoint. Cross-fitted
soft priors are used for few-shot prediction; independent source rankings are
preserved for OOD proposal generation. Multiple qualified rankings may then be
combined as a shortlist portfolio with novelty, random, shuffled-source, and
wrong-domain references. A source-derived scientific hypothesis must be
recorded before a shortlisted target outcome is revealed. The current study
tests each component and the integrated portfolio on two outcome-unseen targets.
Neither target passes the complete gate; those null and abstaining decisions are
retained as evidence for the map boundary.

### Donor-recipient eligibility checklist

Roles were assigned to directed tasks rather than permanently to databases. A
candidate donor supplied a model prediction, coefficient, fixed ranking, or
neighboring-condition signal; a recipient supplied the held-out outcome used to
score prediction, screening, or acquisition utility. A resource could be both.
Candidate-donor designation did not imply that borrowing was beneficial.

| Dimension | Outcome-blind requirement or recorded feature | Consequence |
|---|---|---|
| Scientific relation | prewritten, falsifiable physical or experimental link | defines the proposed direction but does not establish utility |
| Representation bridge | donor signal computable from features available for every recipient candidate | missing bridge excludes the edge |
| Source quality | grouped out-of-fold skill and independent-unit support | weak quality prevents qualified-source interpretation |
| Applicability | source coverage and candidate-local representation distance | limits where a global donor may be trusted |
| Independence | canonical identity, article, campaign, and provenance overlap audit | unresolved overlap excludes or downgrades the edge |
| Endpoint match | prediction feature, fixed rank, coefficient, or temporal prior matched to the stated decision | evidence cannot be transferred between prediction, screening, and acquisition endpoints |
| Recipient evaluability | target outcome, independent split, outcome-free candidate features, and prespecified metric | missing elements prevent recipient status |

Recipient outcomes were revealed only after the direction, representation,
split, transfer object, controls, and metric were fixed. They classified the
edge as beneficial, null, harmful, or unresolved; they were not used to choose
the donor. Wrong-domain, shuffled, source-size-, source-skill-, and
representation-coverage-matched sources were retained where the corresponding
design specified them.

## S2. Integrated data snapshot and reuse controls

The analysed cohort contains exactly 21 accessible experimental resources.
Thirteen form the normalized SQLite layer, which contains 96,184 measurements,
230 source-level property labels, and 29,516 canonical entities. Seven enter as
frozen external or temporal programmes, and NIST ISODB is streamed only for the
artifact analysis. Nineteen resources participate in directed borrowing: 15 in
candidate-donor roles, 16 as recipients, and 12 in both roles. Two normalized
measurements lack canonical identities; both are flagged and excluded from
modeling.

### Table S1. Complete analysed-resource inventory

| Resource | Analysis layer | Directed role | Analysis use |
|---|---|---|---|
| AqSolDB | normalized, 9,982 measurements | donor + recipient | molecular targets and controls |
| FreeSolv | normalized, 642 measurements | donor + recipient | molecular targets and controls |
| CALiSol-23 | normalized, 13,301 measurements | donor + recipient | paper-disjoint adjacent-temperature replication |
| ESTM thermoelectrics | normalized, 26,025 measurements | donor + recipient | compensation, internal map, and transport priors |
| KIT electrolyte conductivity | normalized, 5,035 measurements | donor + recipient | within-campaign adjacent-temperature test |
| Borg MPEA | normalized, 2,904 measurements | donor + recipient | alloy coefficient transport and borrowing |
| OBELiX | normalized, 599 measurements | donor + recipient | ionic-conductivity prediction and OOD ranking |
| OCx24 | normalized, 6,938 measurements | donor + recipient | catalysis map tasks and source controls |
| Open Polymer Benchmark | normalized, 3,985 measurements | donor + recipient | polymer map tasks |
| Photoswitch dataset | normalized, 974 measurements | donor + recipient | molecular photochemistry map tasks |
| Caltech ionic-conductivity database | frozen external | donor + recipient | external ionic target and reverse-transport donor |
| Multi-stage battery-aging dataset | frozen temporal | donor + recipient | Stage 1 to Stage 2 condition borrowing |
| IUPAC digitized pKa | normalized, 24,017 measurements | donor only | molecular map source |
| Caltech Acid-OER | frozen external | donor only | same-reaction electrocatalysis source |
| Caltech metal-oxide ORR | frozen external | donor only | adjacent oxygen-electrocatalysis source |
| BIRDSHOT alloy campaign | normalized, 855 measurements | recipient only | external rolling-time and coefficient-transport target |
| Matbench steels | normalized, 927 measurements | recipient only | independent official-fold target |
| Starrydata2 | frozen external | recipient only | outcome-unseen reverse-transport target |
| TRI four-plate OER benchmark | frozen external | recipient only | outcome-unseen second-family target |
| SpecGen derivative OER systems | frozen external | donor + recipient | complete-system holdout, composition-relation transfer, and later-candidate ranking check |
| NIST ISODB | streamed analysis-only | artifact gate only | isosteric compensation analysis |

Exact commits, file identifiers, hashes, URLs, and source paths for the
normalized layer are in `scripts/localdb/sources.lock.json`; frozen external
inputs are pinned in their task-specific design and verification records. The
generated SQLite file is intentionally not the redistribution unit. It is
rebuilt from the source lock so that source-specific attribution and reuse terms
remain visible.

### Data-quality exclusions

- OBELiX canonicalization found two official-test rows whose normalized
  compositions occurred in training; both were excluded before confirmation.
- CALiSol contained one negative salt-concentration digitization point. The raw
  row was retained, but it was excluded from normalized measurements.
- CALiSol mixture identities include salt, concentration value and unit,
  solvent-ratio convention, and solvent components. Mass-, volume-, and
  mole-based formulations are not silently collapsed.
- Signed AqSolDB and FreeSolv targets were retained; negative values were not
  treated as missing or invalid.
- ISODB adsorbent names were not coerced into formula or SMILES identities.

## S3. Internally frozen operational local-task-rescue rule

The KIT and CALiSol designs were frozen internally after schema, count, and
data-quality audits but before the first designated target-outcome model. They
were not externally preregistered. Each formal decision required all gates
below; no gate was introduced after seeing a favorable result.

### Table S2. Shared rescue gates

1. Mean relative held-out RMSE reduction at least 5%.
2. Two-sided 95% hierarchical-bootstrap interval entirely above zero.
3. Positive pooled augmented-model R².
4. Positive effect in all five outer folds.
5. At least 30% target-equivalent label fraction saved.
6. Positive mean effect for at least two of three target learners.
7. Positive grouped source out-of-fold R².
8. Zero held-out target identities or provenance groups seen by the source fit.
9. Prespecified mapping-permutation p<0.05.
10. Valid target-only learning curve for sample-equivalence interpolation.
11. Primary effect larger than every prespecified distant control.
12. Strict decrease in effect with increasing task distance.
13. Shuffled-source placebo not positive at the 95% level.
14. Shuffled-source effect smaller than the primary effect.

The 5% and 30% thresholds are prespecified operational screening choices, not
universal constants or empirically optimized cutoffs. Continuous effects and
curves are retained so alternative utility thresholds remain auditable.

### Table S3. Gate-by-gate results

| Gate | KIT −20→−30 °C | CALiSol −30→−40 °C |
|---|---:|---:|
| Relative RMSE effect ≥5% | pass, 15.02% | fail, 1.61% |
| 95% interval above zero | pass, [8.61,21.10]% | fail, [−2.14,4.21]% |
| Positive augmented R² | pass, 0.811 | fail, −0.014 |
| Five of five positive folds | pass | fail, two harmful folds |
| Label fraction saved ≥30% | pass by frozen point rule, 37.35%; post-outcome diagnostic [21.84,49.91]% | fail, 16.93% |
| At least two of three learners positive | pass, 3/3 | pass, 3/3 |
| Positive grouped source R² | pass, 0.859 | pass, 0.119 |
| Test exposure | pass, zero formulations | pass, zero articles and exact chemistries |
| Mapping p<0.05 | pass, 0.001 | pass, 0.004 |
| Valid target-only curve | pass | pass |
| Primary beats every distant control | pass | fail |
| Strict distance decay | pass, Spearman ρ=−1 | fail, Spearman ρ=0 |
| Placebo not positive at 95% | pass | pass |
| Placebo smaller than primary | pass | pass |
| **Frozen decision** | **local task rescue** | **cross-article borrowing unresolved** |

The CALiSol mapping p value demonstrates why the rule is conjunctive: one
fixed-subset statistic can reject a feature-mapping null while the repeated
effect remains small and uncertain, absolute prediction remains worse than a
mean predictor, two outer folds are harmful, and adjacency controls fail.

## S4. KIT within-campaign protocol

The KIT data comprise 5,035 temperature-specific measurements from 504
experiment identifiers and 109 PC/EC/EMC/LiPF6 formulations. Replicates were
collapsed by formulation and temperature median. The 108 formulations complete
at every target and control temperature were indivisible units in five balanced
outer folds. The target was log10 conductivity at −30 °C, the target-label
budget was 30 per fold, and the primary source was −20 °C. Sources at 0, 30,
and 60 °C and a shuffled −20 °C source were fixed controls.

Source predictions for target-training formulations were cross-fitted. Source
models for target-test formulations excluded those formulations. Experiment
identifier, batch mass, Arrhenius and pre-exponential terms, fitted conductivity
vectors, and all EIS-fit outputs were forbidden. The formal run used 100 target
subsets, 5,000 hierarchical bootstrap replicates, 999 mappings, 60 learning-
curve repeats, and 40 sensitivity repeats.

The primary effect was 15.02% [8.61,21.10%], with R² 0.739→0.811. Fold effects
were 15.56%, 10.81%, 18.08%, 2.13%, and 25.75%. Random Forest, ExtraTrees, and
polynomial Ridge effects were 15.02%, 19.63%, and 34.47%. Control effects at
10, 30, 60, and 90 °C distance were 15.02%, 5.01%, 0.95%, and −0.76%; the
shuffled adjacent source gave −2.96% [−4.32,−1.44%]. The source feature's mean
Random-Forest importance was 0.732 with median rank 1/5. Importance is a use
diagnostic, not a mechanism claim.

The target-only point estimate was n=47.884, or 37.35% of equivalent target
labels saved. A post-outcome 5,000-replicate diagnostic resampled formulations
and training-subset repetitions at every learning-curve budget. Its 95%
interval was n=38.38–59.89, corresponding to 21.84–49.91% saved, and 80.52% of
replicates met the frozen 30% point threshold. Thus the direction of improved
sample efficiency is supported, but the magnitude relative to 30% is not
stable enough to be presented as an uncertainty-qualified gate.

## S5. CALiSol paper-disjoint protocol

The downloaded CALiSol file contained 13,825 rows from 27 publications. The
target was fixed at −40 °C and the primary source at −30 °C; −20, 0, and 20 °C
were controls. A ±2.5 °C window assigned rows to nominal tasks. The target
contained 891 paper-specific formulations from 15 articles after excluding two
chemistry identities shared by target articles.

Outer folds held out entire article DOIs. Each source fit excluded held-out
articles and exact held-out chemistries found in other articles. Target-training
priors were leave-one-article-out. Article DOI, temperature, measured
conductivity at another temperature, Arrhenius/VTF quantities, and curve
summaries were forbidden. The formal resampling counts matched KIT.

The primary effect was 1.61% [−2.14,4.21%], with R² −0.049→−0.014. Fold effects
were −0.78%, 0.003%, −3.85%, 3.11%, and 6.45%. The estimated target-equivalent
count was 36.12 from n=30. Control effects at −20, 0, and 20 °C were 0.28%,
2.18%, and 1.27%; the shuffled −30 °C effect was 0.83%
[−1.38,3.79%]. No alternative temperature was promoted after the 0 °C control
appeared numerically stronger.

### S5.1 Post-outcome provenance-anchored contrast reanalysis

The unresolved absolute-transfer result motivated a separate mechanistic
reanalysis. Its design was locked before any contrast-model prediction was
computed, but after the original CALiSol outcomes had been inspected. It is
therefore method-development evidence rather than an independent confirmation.
The frozen design SHA-256 was
`04279e568830b14a92199d165c96a6a3b05d55b6c64ce54b5c7eb046eb2c1cfe`.

The analysis asked whether an article-specific additive offset prevented
absolute transfer while leaving within-article formulation responses partly
portable. The common scope contained 883 −40 °C formulations from the 11
articles having at least eight eligible formulations. Each article was held
out in turn. The −30 °C training rows excluded the target DOI and all exact
target chemistries. Standardization used only the retained source rows.
Within each source article, standardized formulation features and log10
conductivity were centered. Ridge regression without an intercept learned the
centered response, with each article assigned equal total fitting weight.

For each held-out article, the first anchor was its outcome-independent feature
medoid. Additional anchors followed deterministic farthest-point traversal.
Anchor outcomes restored the absolute target-article scale through
\(\widehat y_t=y_a+\widehat{\Delta f}(x_t-x_a)\). Anchor rows were excluded
from scoring. The primary comparator was an ordinary absolute −30 °C ridge
model offset-calibrated using exactly the same anchor. Thus the primary
contrast changed the transferred object while holding the donor, features,
article split and target information fixed.

At one anchor, macro-RMSE decreased from 0.4901 to 0.4562 log10(mS cm\(^{-1}\)),
a relative gain of 6.91%. The 10,000-replicate article-cluster bootstrap
interval was [0.88,14.00%], and the exact one-sided sign-flip test over the 11
article RMSE differences gave \(p=0.0352\). Eight articles improved. Pooled
non-anchor \(R^2\) was 0.234, and the contrast model reduced macro-RMSE by
29.84% relative to the anchor-only constant.

The 199 within-article shuffled-donor contrasts had median relative gain
−35.06%; the real result exceeded that median by 41.97 percentage points and
gave permutation \(p=0.005\). The +20 °C wrong-condition contrast had
macro-RMSE 0.5553 and pooled \(R^2=-0.062\). Primary gains remained 6.4–6.9%
for ridge penalties 1, 10 and 100. Across 100 random one-anchor selections, all
100 gains were positive; the median was 6.24% and the 10th–90th percentile
range was 3.35–9.98%.

Three articles were mildly harmful. Deterministic two- and three-anchor
contrasts retained more than 5% macro-RMSE advantage over their matched
absolute donors but did not retain positive pooled \(R^2\). The frozen
one-anchor contract passed all gates; the analysis does not establish
monotonic benefit from additional anchors or universal cross-article transfer.
Formal verification reconstructed 33,579 non-anchor predictions, 429
article-level metrics, 199 shuffled-null rows and 300 random-anchor rows.

## S6. Alloy transport and map boundaries

The Borg log10 UTS–YS fit used 495 rows and 208 canonical compositions
(R²=0.790). BIRDSHOT used 171 rows and 151 compositions (R²=0.067), with zero
exact composition overlap. Applying the unchanged Borg line to BIRDSHOT gave
R²=−3.006, composition-cluster 95% interval [−4.154,−2.185]. The median UTS/YS
ratio changed from 1.36 to 2.72.

The internal map contained 42 directed non-calibration edges and showed effect
heterogeneity (Cochran Q p=0.00036). The internally admitted Borg UTS→Borg YS
edge yielded 6.46% [3.69,13.03%], Holm p=0.005, but only R² −0.149→0.025.
BIRDSHOT rolling-time confirmation yielded 4.30% [3.36,5.51%] with negative
absolute R² and missed the 5% gate. Matbench official-fold confirmation yielded
−1.23% [−15.88,2.48%], p=0.794; all five primary fold effects were negative.

## S7. Compensation artifact battery

The thermoelectric Meyer–Neldel fit at the prespecified R²≥0.90 Arrhenius
threshold used 112 reference-separated series and gave pooled R²=0.107. At
thresholds 0.80 and 0.95, pooled R² values were 0.124 and 0.077. Small family
fits were treated as exploratory.

The ISODB matched-loading analysis produced 1,103 systems in 512 DOI clusters.
The pooled heat–intercept relation gave R²=0.637 and T_iso=513 K, versus a
median harmonic experimental temperature of 301 K. Under 999 independent-
parameter Krug mappings, median R² was 0.0028 and the add-one p value was
0.000999. This rejects the specified simple parameter-coupling null, not every
possible artifact or a mechanism-free null.

Among 16 major adsorbate families, a 4,999-replicate DOI wild-cluster test
supported unequal family intercepts (p=0.0002) but did not establish
family-specific slopes (p=0.625). The retained interpretation is a strong but
conditional empirical regularity.

## S8. OOD screening and sequential discovery

### Fixed OOD screening

The primary endpoint was the fraction of the fixed candidate pool ranked before
the first observed top-5% target. Holm correction covered the three named
independent edges: BIRDSHOT temporal, CALiSol article-disjoint, and OBELiX
official test. In OBELiX, the thermoelectric prior reduced the mean fraction
screened from 0.1208 to 0.0998. The absolute saving was 0.0209 [0.0094,0.0345],
or 17.3% relative, with Holm-adjusted p=0.0003. Only 38.3% of repeat effects were
strictly positive, the relative saving was below the frozen 25% gate, and the
baseline median was already within the 10% shortlist. The decision was
directional OOD screening, not improvement or rescue.

The farthest 40% of the OBELiX official-test pool was selected by minimum L1
elemental-fraction distance to the official-training reference without target
outcomes. The mean fraction screened changed from 0.2159 to 0.1811; the absolute
saving was 0.0348 [0.0174,0.0542], or 16.1% relative. The median crossed from
0.1023 to 0.0909, but only 36.7% of repeats improved and the 25% effect gate
failed. This result is exploratory because the hard-OOD design was written
after the whole-pool OBELiX direction was known.

### Frozen official-test sequential campaign

The self-contained campaign input contained 500 canonical OBELiX compositions,
126 composition features, the 390/110 official train/test split, the fixed
44-composition hard-OOD subset, and three frozen source predictions. Exact
source–target composition overlap was zero. Every strategy shared group-aware
n=30 initial labels from official training. The primary ExtraTrees UCB policy
used 100 paired seeds, a 40-acquisition budget, and censoring at 41. The
Random-Forest sensitivity used 40 seeds.

In the 110-composition official pool, target-only and thermoelectric-prior UCB
required means of 24.34 and 24.09 acquisitions. The paired saving was 0.25
[−1.30,1.82], p=0.3889; 28% of seeds improved and 49% tied. The corresponding
censoring fractions were 0.40 and 0.41. Every effect, interval, practical,
relative, and repeat-consistency gate failed. Random-Forest sensitivity saved
0.525 [−1.85,3.10], p=0.3538, and did not change the decision.

In the hard-OOD subset, ExtraTrees thermoelectric borrowing saved 2.21
[0.97,3.49] acquisitions, p=0.0004. This was below the frozen five-experiment
and 25% gates; 58% of seeds improved, below the 60% gate. The Random-Forest
sensitivity saved 1.025 [−0.90,2.925], p=0.1608. The result therefore remained
exploratory and failed both OOD-discovery improvement and rescue.

### Random acquisition reference and claim boundary

Uniform random acquisition required a mean of 15.50 acquisitions in the
official pool, compared with 24.34 for target-only UCB. Its prespecified saving
relative to target-only was 8.84 [4.57,12.90] experiments, and censoring fell to
0.08. The empirical random mean agreed with the exact censoring-adjusted random
expectation of 15.30. In a post-result direct diagnostic, random required 8.59
[4.14,12.99] fewer acquisitions than thermoelectric-prior UCB. Random was also
better in the hard-OOD subset. These controls demonstrate failure of the tested
UCB policies in this pool; they do not isolate its cause or establish uniform
random acquisition as generally optimal.

### Post-result policy-development benchmark (non-confirmatory)

After the frozen UCB result and its signal-anatomy diagnostic were known, an
isolated 100-seed benchmark compared target mean, composition novelty, static
source rankings, and adaptive rank fusion. The method family was therefore
outcome-selected and cannot alter the frozen sequential decision. Composition
novelty was the valid target-only policy: it saved 12.08 [9.74,14.52]
acquisitions relative to random in the official pool and 8.82 [7.10,10.58] in
hard OOD. Target-mean greedy was worse than random in both scopes.

Thermoelectric static screening saved 12.50 [10.25,14.90] acquisitions relative
to random in the official pool, but only 2.00 relative to the catalysis static
control, below the frozen five-acquisition source-specificity gate. All 100
static-policy rows are the same deterministic ranking, so the zero-width
static-versus-static intervals are not uncertainty over independent datasets.
The first thermoelectric hit is one Li-Y-Br candidate at step 3.

Target/source/novelty fusion passed its prespecified comparison with target
mean, but target mean is not a valid backbone. In the explicitly post-hoc
comparison with composition novelty, fusion saved -0.77 [-1.68,0.13]
acquisitions on first hit in the official pool and -2.66 [-3.58,-1.75] in hard
OOD. It increased official-pool cumulative-hit AUC by 34.12 [27.64,40.18] and
top-5% recall at acquisition 40 by 0.225 [0.187,0.265], but the breadth signal
did not reproduce in hard OOD. Fusion is therefore retained only as a candidate
for an independently frozen breadth-of-recall endpoint, with composition
novelty as its mandatory comparator.

A legacy exploratory whole-pool RF-UCB control used 50 paired retrospective
campaigns under a different implementation. Baseline and augmented policies
required means of 19.92 and 17.66 acquisitions; the paired difference was 2.26
[−0.38,5.28], p=0.071. It is retained as a sensitivity only and does not enter
the frozen sequential decision. Its null interval is consistent with the main
conclusion that average predictive utility, fixed OOD ranking, and sequential
discovery require separate endpoints.

### Independent Caltech ionic-conductor policy benchmark

The external target was the Caltech experimental Li-ion-conductivity database.
Eligibility filtering and canonicalization produced 483 compositions in 229
identity/article components: 339 development entities, 144 article-disjoint
candidates, and a frozen 58-candidate hard-OOD subset. Exact candidate formulas
and target DOIs were excluded from every source fit, leaving 181 OBELiX, 870
ESTM, 395 Borg, and 212 OCx source entities. The primary endpoint was
cumulative recovery of true top-5% candidates through acquisition 20. Eight
source-increment contrasts were tested in each scope with Holm correction,
paired bootstrap intervals, practical, consistency, first-hit, absolute-recall,
and two-scope gates.

Formal Balam Job 70740 generated 120,000 trajectories, 184,000 gate rows, 3,000
utility rows, and 16 contrast rows. Same-environment verification Job 70767
refitted all source models and replayed every static and shuffled-static
campaign. Portable verification independently recomputed all utilities,
intervals, multiplicity corrections, and gate summaries. The final sentinel
status was `VERIFIED`.

No frozen adaptive source increment passed. Relative to the state-matched
target-only policy, external/hard-OOD AUC20 gains were −0.06
[−0.30,0.12]/+1.10 [−0.38,2.59] for the OBELiX residual, −0.06
[−0.23,0.07]/−0.07 [−1.11,0.91] for ESTM, and −0.09
[−0.34,0.09]/+1.27 [−0.75,3.22] for the multisource residual. Composition
novelty was worse than random in the full external pool; in hard OOD its AUC20
gain was 8.32 [6.12,10.26], Holm p=0.0008, but recall20=0.443 missed the frozen
0.50 gate. Adding target-mean steering was harmful in hard OOD.

Every wrong-source guard passed. Across single-source policies, the two real
neighbors had mean admission 0.355 and mean weight 0.168, compared with 0.168
and 0.063 for the three wrong controls. Source OOF R² was 0.065 for OBELiX,
0.257 for ESTM, 0.164 for Borg, and 0.543 for OCx. Thus the admission ordering
was not an ordering of demonstrated source skill; it supports only the safety
behavior encoded by the gate, not source credibility or acquisition utility.

Static-source policies were prespecified but their attribution comparisons were
not part of the primary frozen family. OBELiX and ESTM static AUC20 values were
33 and 45 in the external pool, with recall20=2/8 and 3/8, and 38 and 51 in
hard OOD, with recall20=3/3 for both. The three-positive hard-OOD denominator
is n-limited. Both sources exceeded random, shuffled, mechanical, and catalysis
references in both scopes. Deterministic static rankings have no dataset-level
uncertainty, and candidate-seed variation cannot create it, so this remains
prespecified retrospective external signal outside the primary contrast family.
A post-result OBELiX/ESTM round-robin or consensus
portfolio reached recall20=0.625 (5/8) externally and 1.000 (3/3) in hard OOD,
compared with 2/8 and 3/8 externally for the individual sources. This
demonstrates source complementarity on the observed target and supplies
component-level strategy evidence. Because the portfolios were created after
Caltech outcome inspection, they are method selection for a new outcome-unseen
target rather than independent confirmation of prospective acceleration.

### Outcome-informed CCA family-first exploration audit

The eight external top-5% entities occupied four connected components formed by
shared canonical formula, DOI, or ICSD identifiers. All three hard-OOD top-5%
entities belonged to one such component. Entity-level recall therefore counted
repeated members of the same provenance/formulation region as separate
discoveries. A post-result credibility–complementarity–abstention (CCA) audit
changed the primary unit to the connected component. The complete pool
contained 63 components and the hard-OOD pool contained 36. Top components were
the top ceil(5%) by the best measured target value within the component; median
and mean outcomes were prespecified sensitivities within this method-development
analysis.

The family-first consensus began with the unweighted OBELiX/ESTM rank-sum order.
It selected the first encountered member of every connected component before
returning to within-component repeats. Thus candidate outcomes could not affect
the order, which was verified by permuting all candidate outcomes and obtaining
identical orders. OOD distance defined the hard-OOD scope but was not multiplied
into the source score. This choice followed a failed local-gate analysis: the
full multiplicative target-OOD/source-support/local-concordance policy obtained
external AUC20=0.96 and hard-OOD AUC20=5.11, compared with 69 and 52 for static
entity consensus. The failure is retained as evidence that an OOD heuristic can
erase a useful neighboring rank.

Family-first consensus increased distinct-component AUC20 from 47 to 60 in the
external pool and recovered all 4/4 top components at positions 3, 4, 5, and 12,
compared with 3/4 for entity consensus. In hard OOD, AUC20 increased from 36 to
39 and both 2/2 top components appeared at positions 1 and 2. The
mechanical/catalysis wrong-source pair obtained AUC20=6 and 18. Across 5,000
independent permutations of both neighbor rankings, shuffled-pair AUC20 had
means 19.93 and 18.72 and 95% ranges 0–45 and 3–36. Conditional randomization
p-values for the observed family-first AUCs were 0.0020 and 0.0030. These are
fixed-pool null comparisons, not external-target confidence intervals.

The result was identical under the median component outcome. Under the mean
outcome, external recovery was 3/4 (AUC20=42), while hard-OOD recovery remained
2/2 (AUC20=39). The strategy deliberately reduced repeated entity-level recall:
external recall20 changed from 5/8 under entity consensus to 2/8 under
family-first consensus, and hard-OOD entity recall changed from 3/3 to 1/3.
This is a breadth policy for distinct target regions, not an across-the-board
improvement in hit rate. Four retrospective source-attribution cards record the
selected formula, source ranks, element set, falsifier, and mechanistic
follow-up. They define the reporting format for an outcome-unseen target and are
not predeclared discoveries on Caltech.

### Post-outcome OOD knowledge-deficit surface

The target-only deficit was quantified on the frozen OBELiX input over target-
label budgets 15, 30, 60, 120, and 240, 100 grouped target-label repeats, and
ExtraTrees/Random-Forest learners. Within each repeat, official-test candidates
were divided into quartiles by nearest selected-target distance using only the
frozen composition representation. At n=30, the ExtraTrees far-minus-near RMSE
gap was 0.373 (conditional 95% interval 0.047–0.669), while absolute-error–
distance Spearman correlation was 0.097 (0.049–0.144). The thermoelectric source
reduced far-quartile RMSE by 3.95% (2.65–5.26%) and exceeded the best alloy,
catalysis, or independently shuffled-source reduction by 1.29 percentage points
(0.21–2.40). The Random-Forest direction was concordant. These repeat-bootstrap
intervals are conditional on one fixed target database and are not external-
target uncertainty. The analysis was specified after OBELiX outcomes and cannot
change the frozen OOD-screening or sequential-discovery decisions.

## S9. Outcome-unseen reverse-transport and second-family programme

### Outcome access and frozen denominators

The programme was constructed as two directed tests and retained both targets
regardless of sign. For Starrydata2, the paper, sample, and curve files were
hash-pinned before outcome access. Outcome-free metadata fixed 7,403 target
entities, 745 composition clusters, and the development/validation/evaluation
partition (4,427/1,675/1,301). Seven entities had an out-of-range selected value
and were reported as missing, leaving 7,396 outcome-bearing entities. The
primary prediction scope was the 738-entity fourth OOD quartile. The target was
thermoelectric ZT; ESTM was the same-domain source, OBELiX and Caltech were
adjacent ionic-transport sources, and Borg and OCx were wrong-domain sources.

For the clean TRI OER benchmark, outcome-free pickle inspection fixed four
paper-defined plates before the `fom` bytes were decoded. Eligibility filtering
left 8,447 entities in 240 outcome-free composition clusters: 2,112, 2,111,
2,112, and 2,112 entities on plates 3496, 3851, 3860, and 4098. Acid OER was the
same-reaction source; ORR and OCx were adjacent sources; Borg mechanical and
OBELiX ionic conductivity were wrong-domain controls. The fifth deposited set
was excluded before outcome decoding because it was absent from the paper's
four-set benchmark. The earlier acid-OER target failed its outcome-free per-
plate minimum and was downgraded to sensitivity/source use before any outcome
comparison.

Both targets used label budgets 15, 30, and 60; 100 target-label repeats per
primary unit; ExtraTrees, Random Forest, and degree-2 Ridge; two non-equivalent
outcome-free representations; target-only, pooling, source-only, stacking,
residual-shrinkage, and mixture-of-experts baselines; source-size, source-skill,
coverage, equal-capacity, wrong-source, and shuffled-source controls; ten
exploration policies; and three source-derived hypothesis cards. No method,
source, plate, card, or result row was removed after outcome access.

### Starrydata reverse-transport result

The primary hierarchical ionic-consensus effect at n=30 was +0.8808%
[0.0165,1.7713%] relative RMSE, one-sided bootstrap p=0.0237 and Holm p=0.0711.
The ionic-versus-best-control contrast was +0.7494%
[-0.1375,1.6568%], Holm p=0.0956; ionic versus the same-domain ESTM source was
-0.0972% [-1.2025,1.0262%], Holm p=0.5680. The augmented-model mean R² was
-0.4847. The primary result therefore passed the positive-interval gate but not
multiplicity, source specificity, or positive absolute utility.

Effects were positive in five of six learner-representation cells: ExtraTrees
composition/context +0.877/+0.289%, Random Forest composition/context
+1.011/+1.110%, and Ridge composition/context -0.366/+2.529%. This passes the
frozen robustness envelope but cannot override failed primary gates. In the
matched-specificity amendment, ionic consensus was +0.804%
[0.040,1.579%], +0.890% [0.021,1.725%] above the equal-capacity control, and
+0.903% [0.091,1.665%] above the skill-matched OCx control. The complete
hierarchical decision family still failed multiplicity and absolute utility.

At the exploration endpoint, CCA family-first AUC20 was 41, below 71 for the
same-domain ESTM policy. The source-rank permutation p value was 0.5463, and no
policy contrast survived Holm correction. The three prewritten hypothesis-card
effects had Holm p values 0.445, 1.0, and 1.0. The Starrydata edge is therefore
directionally positive for one prediction endpoint but unresolved overall.

### TRI OER second-family result

Across the four held-out plates, all-neighbor borrowing gave a random-effects
relative RMSE gain of -0.0787% [-0.3126,0.1552%], exact sign-randomization
p=0.8235 and Holm p=1.0. Plate effects were -0.0922, -0.0528, -0.2343, and
+0.1068%; only one plate was positive. All-neighbor minus the best control was
-1.249% [-1.751,-0.747%], with zero positive plates. All-neighbor minus the
same-reaction source was -0.0107% [-0.1912,0.1698%]. Absolute all-neighbor R²
was negative on every plate (-0.129, -0.111, -0.139, and -0.186).

Learner-representation effects were heterogeneous: ExtraTrees element/periodic
-0.068/+0.560%, Random Forest element/periodic -0.352/+0.195%, and Ridge
element/periodic -4.928/-6.908%. The frozen robustness envelope failed. Every
exploration contrast and all three hypothesis cards had Holm p=1.0. This target
is retained as a null or harmful boundary rather than reclassified by a
favorable sensitivity.

### Multi-target synthesis and verification

The random-effects mean across Starrydata and TRI was +0.3040%
[-0.6168,1.2249%], with tau²=3.53e-5, Q=4.289, and I²=76.7%. Only one target was
directionally concordant and neither passed its complete prediction gate. The
programme therefore does not supply an independent positive replication or a
general transfer law. It demonstrates cross-target heterogeneity and validates
the map's capacity to abstain or reject an edge under the same frozen strategy.

Formal Balam Job 70888 completed with exit code 0. Portable verification
recomputed 117,000 Starrydata metric rows, 2,215,200 Starrydata group-error rows,
468,000 TRI metric rows, 2,904,720 TRI group-error rows, all contrast families,
and the two-target synthesis. In TRI, 3,244 secondary Spearman cells were
undefined because at least one input was constant. The amended verifier retained
and disclosed those missing cells while requiring finite RMSE, MAE, R², gates,
and contrasts; no primary decision used Spearman. Earlier failed jobs and their
implementation-only verifier amendments are retained in the audit trail and did
not change a target, source, policy, representation, endpoint, or gate.

### Leave-one-target-program CCA gate benchmark

After all component outcomes and the CCA method concept were known, a separate
method-development design asked whether outcome-free edge descriptors could
select useful borrowing on a completely held-out programme. The panel contained
97 directed edges, 20 target tasks, and 13 independent programme clusters.
Tasks from one dataset or campaign remained in one cluster; the four TRI plates
were not counted as four independent scientific programmes. Each training
programme received total weight one. Weighted ridge predictions used physical-
neighborhood score, grouped source OOF R², same-domain or condition adjacency,
cross-dataset status, and wrong, distant, or shuffled indicators. Every edge in
the held-out programme was predicted without any outcome from that programme.

The CCA meta-gate admitted 17/20 target tasks across 11/13 programmes. Mean
programme-level relative RMSE utility was +1.5818% [-0.2256,4.2669%] from 10,000
programme-cluster bootstraps. One of 17 admitted selections was clearly harmful,
but only four of ten tasks with an available clearly beneficial edge retained
such an edge. The CCA-minus-best-credibility contrast was +1.4180 percentage
points [-0.2275,4.0755], one-sided sign-flip p=0.1350 and Holm p=0.2700. The
CCA-minus-never-borrow contrast was +1.5818 [-0.2281,4.2947], p=0.1621 and Holm
p=0.2700. The 20% coverage guard passed; the frozen superiority family failed.
Adjacency-only was numerically stronger at +1.7982% [-0.1943,4.5242%] and
retained five of ten available clear benefits.

The fitted meta-gate and fixed CCA rule made nearly identical decisions. Error
inspection showed within-neighborhood source-ranking reversals and false
exclusion of locally useful edges by the global source-skill criterion. The
result therefore supports physical adjacency as a first-order proposal prior
but not global edge metadata as a validated benefit selector. The complete
design, validation narrative, outputs, and independent reconstruction are in
`cca_leave_one_program_gate_design.json`,
`CCA_LEAVE_ONE_PROGRAM_GATE_VALIDATION.md`, and
`results/cca_leave_one_program_VERIFIED.json`. `CCA_GATE_V2_PROSPECTIVE_PROTOCOL.md`
freezes the post-result move to candidate-local applicability and cannot be
evaluated confirmatorily on these same outcomes.

## S10. Systematic multi-target OOD borrowing benchmark

### Design status and scope

The machine-readable design was frozen on 23 July 2026 before the unified formal
run. Earlier component outcomes had already been inspected, so this experiment
is a declared systematic stress test and method-development benchmark, not an
independent confirmation. It reused the exact target definitions, grouped
partitions, and source edges from `knowledge_map_design.json`. Targets required
at least 12 intact evaluation groups. Eight targets across seven independent
programme clusters were eligible; the photoswitch target was excluded because
only five evaluation groups were available. Each eligible target retained five
real sources and one deterministic shuffled version of its designated source,
giving 40 real edges and eight shuffled controls.

OOD labels were outcome-free. Formula-indexed targets used minimum standardized
composition-feature distance to the complete-development reference; molecular
targets used one minus maximum Morgan-fingerprint Tanimoto similarity. Intact
evaluation groups were ordered by median distance, with Q1 designated
in-distribution and Q4 designated OOD. The source prediction was added as one
soft target-model feature. Ridge with α=10 was primary, with Random Forest and
ExtraTrees sensitivities. Target-only, augmented, wrong-source, and shuffled-
source fits shared 100 grouped target-label draws.

### Complete OOD-repair gate

A designated edge passed only if all of the following held:

1. mean Q4 relative RMSE gain was at least 5%;
2. the hierarchical 95% Q4 interval excluded zero;
3. augmented Q4 R² was positive;
4. at least 80% of paired target-label draws improved;
5. the Q4-minus-Q1 gain interval excluded zero in the positive direction;
6. the designated edge beat the prespecified wrong source;
7. the designated edge beat its shuffled-source placebo;
8. at least two of three learner families improved;
9. the one-sided paired sign-flip test survived Holm correction across eight
   designated edges; and
10. exact recipient-evaluation identities were absent from the source fit.

### Table S10. Designated-edge results

| Recipient ← donor | Q1 gain (%) | Q4 OOD gain, 95% CI (%) | Q4−Q1 gain (%) | Augmented Q4 R² | Holm p | Classification |
|---|---:|---:|---:|---:|---:|---|
| Alloy YS ← alloy UTS | +7.74 | +6.65 [3.53,14.02] | −1.09 | −0.666 | 0.0008 | OOD improvement, not OOD-specific |
| Catalysis H₂ selectivity ← voltage | −2.50 | −0.97 [−3.78,11.90] | +1.53 | −3.013 | 1.000 | unresolved |
| Electrolyte conductivity ← thermoelectric electrical conductivity | −0.28 | +0.98 [−3.14,3.70] | +1.25 | −7.683 | 0.203 | directional OOD improvement |
| Hydration free energy ← solubility | +3.67 | −0.35 [−1.80,0.97] | −4.02 | −0.128 | 1.000 | unresolved |
| Polymer tensile strength ← Young's modulus | +1.24 | −0.06 [−0.83,3.18] | −1.29 | −0.343 | 1.000 | unresolved |
| Polymer melting temperature ← crystallization temperature | +0.10 | −0.08 [−1.33,1.14] | −0.18 | −0.732 | 1.000 | unresolved |
| Solubility ← hydration free energy | +0.13 | +0.08 [−0.22,0.31] | −0.05 | −0.092 | 0.049 | directional but practically negligible |
| Thermoelectric ZT ← Seebeck coefficient | −0.09 | +0.15 [−6.31,1.07] | +0.24 | −621.154 | 1.000 | directional OOD improvement |

The alloy edge passed the practical-gain, positive-interval,
repeat-consistency, wrong-source, shuffled-source, learner, multiplicity, and
identity gates. It failed positive absolute OOD R² and OOD-specificity. The
solubility edge illustrates why a multiplicity-adjusted p value alone is
insufficient: its +0.08% effect was trivial, its interval crossed zero, and its
absolute OOD R² remained negative.

### Portfolio-level inference and interpretation

The seven-programme bootstrap mean of the eight designated OOD gains was +0.92%
[−0.35,2.92%]. No programme cluster contained a complete designated-edge pass.
Zero of three designated cross-database edges passed the upgrade gate. Among all
40 real edges, classifications were 10 directional OOD improvements, nine OOD
improvements that were not OOD-specific, ten harmful edges, and eleven
unresolved edges. Non-designated positive edges remain exploratory because they
were identified within the same formal result matrix.

The formal run contained 43,200 metric rows, 14,400 paired-contrast rows, and
63,600 group-error rows. Verification reconstructed all summary files from the
row-level outputs and checked the frozen design hash
`cc911d9d9677e0c523a77632f7866e9e6fedcb5625472f9004ad203fe0512d89`.
The result does not show that neighboring knowledge is useless; it shows that a
generic donor-as-feature mechanism is insufficient for OOD repair. It supports
the endpoint-matched strategy used in the main text: qualified soft priors for
local few-shot prediction, preserved donor rankings or portfolios for OOD
proposal generation, and abstention otherwise.

### S10.1 State-matched MPEA post-selection robustness analysis

The generic benchmark collapsed MPEA records to composition-level targets and
therefore discarded processing route, phase family, test mode, test temperature
and density. A frozen follow-up returned to the raw experimental rows. It
contained 1,067 positive YS records across 150 elemental systems, 539 positive
UTS records across 93 systems, and 495 paired YS–UTS rows. The primary
planned-state contract used composition, processing route, coarse phase family,
test mode, test temperature and calculated density.

No elemental system crossed development and evaluation. For every target
training fold, the UTS donor excluded the held systems and every evaluation
system before producing the target-training feature. The final donor excluded
all evaluation systems. Thirty target-label draws, a budget of 60 YS labels,
Random Forest and ExtraTrees learners, 320 trees, and a newly generated
within-fold shuffled donor were frozen. The primary interval used 100,000
two-way cluster-bootstrap replicates over the 59 evaluation systems and 60
model-by-draw runs.

| Q4 contrast | Relative RMSE gain | Positive runs | Augmented/pooled Q4 R² |
|---|---:|---:|---:|
| state-aware target + predicted UTS vs state-aware target | +9.21% [4.43,14.37%] | 55/60 | 0.103 |
| architecture-matched shuffled UTS vs state-aware target | −0.26% [−1.81,1.01%] | 32/60 | −0.093 |
| real minus architecture-matched shuffled donor | +9.47 percentage points [4.80,14.34] | — | — |
| measured UTS auxiliary ceiling vs state-aware target | +47.70% mean | 60/60 | 0.679 |

The Q1 gain was +7.21% [3.05,11.52%]. Q4 exceeded Q1 by +2.00 percentage
points, but the interval crossed zero [−4.66,8.62%]. The Q4 R² interval also
crossed zero [−0.151,0.291]. Accordingly, this analysis establishes stable
benefit in the hardest OOD quartile and strong source specificity, but not an
OOD-exclusive effect or uniformly positive extrapolative utility. Because the
architecture was selected after earlier MPEA outcomes were inspected, the
verified Balam result is post-selection robustness evidence rather than
independent confirmation. The complete result hashes and gate are recorded in
`results/state_matched_mpea_balam_v2_VERIFIED.json`. V2 supersedes only the V1
shuffled-source contrast; the primary real-versus-target-only result is
numerically identical.

### S10.2 Strong optical source models do not rescue scaffold-OOD photocatalysis

A focused post-benchmark stress test asked whether the molecular null in the
systematic benchmark reflected a weak transfer model. Chemprop directed
message-passing encoders were trained on experimental absorption, emission,
lifetime, quantum-yield, and extinction-coefficient data. Separate
aqueous/small-alcohol and molecular-solid source scopes represented the
photocatalysis medium and suspended molecular phase; an all-environment encoder
was the state-blind control. All five aqueous tasks and all three solid tasks
passed the frozen scaffold-held-out source-skill gate. Shuffled-label encoders
and the original scalar optical predictions supplied matched controls.

The recipient was a zero-inflated molecular hydrogen-evolution task. Across 900
frozen scaffold-separated draws (300 each at 30, 60, and 120 labels), source
representations fitted only a nested cross-fitted correction to an otherwise
unchanged recipient-only hurdle model. Zero correction was an admissible
choice. In 16 draws with fewer than three labelled scaffolds, donor correction
was forced exactly to zero and those draws remained in every aggregate.

At the primary 60-label budget, the state-aligned encoder worsened hard-OOD
RMSE by 28.12% on average and improved only 74/300 draws. It was 25.23
percentage points worse than the shuffled-source encoder and 12.72 points worse
than the state-blind encoder. Whenever the nested selector chose a nonzero
state-aligned correction (190/300 draws), mean harm increased to 44.40%.
Hard-OOD effects at 30 and 120 labels were also negative (-42.11% and -4.51%).
Every frozen utility and specificity gate except correction use failed, so the
96-molecule blind set remained unopened.

This result rules out model weakness as a sufficient explanation for this
edge. Predictable source endpoints and plausible domain adjacency did not make
their latent representation portable to scaffold-OOD hydrogen evolution.
Generic optical supervision omits excited-state redox driving force, charge
separation, catalytic kinetics, formulation, and reaction conditions that
define the recipient endpoint. The edge is therefore retained as a qualified
rejection rather than a negative-transfer result to optimize away. Full
methods, amendments, metrics, and verification are reported in
`OPTICAL_SUPERVISED_BORROWING_PROTOCOL.md`,
`OPTICAL_SUPERVISED_VERIFIER_AMENDMENT.md`, and
`OPTICAL_SUPERVISED_BORROWING_FINDINGS.md`.

### S10.3 Cross-database electrolyte ranking and recipient-baseline stress test

This analysis was specified after SolventSeg and FINALES outcomes had been
inspected and is therefore post-outcome method development. Three conductivity
programmes were fitted separately: 10,012 eligible BambooMixer measurements
after removing the complete LiPF6/ethylene-carbonate/ethyl-methyl-carbonate
target family, 410 CALiSol measurements from three articles, and 1,089
formulation–temperature aggregates from KIT. Each source used a 400-tree
Random Forest with three fixed seeds. The primary programme-balanced score was
the equal arithmetic mean of the three log-conductivity predictions; source
rows were never pooled.

The overlap audit used exact component families, solvent-mole-fraction plus
salt-ratio \(L_1\) distance no greater than \(10^{-4}\), temperature difference
no greater than 0.05 °C, and conductivity difference no greater than
0.01 mS cm\(^{-1}\). Seventy-one of 410 CALiSol rows matched BambooMixer under
this definition. No BambooMixer, CALiSol, or KIT record matched any of the 180
SolventSeg rows, and no other source pair matched. Removing the complete target
family from the BambooMixer portfolio and assigning equal programme weight
prevented those known source-source duplicates from dominating the result.

At 25 °C, the 36-formulation SolventSeg source score had
\(\rho=0.9178\), top-quartile precision 1.000, and normalized regret 0.000.
For each of 100 maximin anchor selections at budgets 3, 5 and 10, the selected
formulations were excluded wholesale from evaluation. At five anchors, the
source score had mean \(\rho=0.9103\), precision 0.9325, and regret 0.00047.
The strongest average recipient-only model among 13 linear, radial-basis
kernel, nearest-neighbour, and tree configurations was radial-basis kernel
ridge with \(\rho=0.5366\). The source-minus-recipient difference was 0.3737
(2.5th–97.5th anchor-coverage percentiles, 0.2126–0.5622). The source also
exceeded a non-deployable per-draw recipient oracle by 0.2999
(0.1834–0.5397). A 10,000-permutation fixed-temperature rank test gave
Holm-adjusted one-sided \(p=0.00070\) across seven declared source arms.

The programme portfolio provided a smaller robustness increment over the
broad single BambooMixer donor: mean five-anchor \(\Delta\rho=0.0236\)
(0.0069–0.0397), positive in all 100 draws, and precision increased from
0.8263 to 0.9325. It did not qualify as a numerical predictor. Its
all-temperature log-RMSE was 0.3423 versus 0.2900 for the state-only source,
and the formulation-bootstrap relative-gain interval crossed zero
(−0.4397 to 0.2106). Five-anchor calibration likewise had a relative
log-RMSE interval of −0.0151 to 0.7460. The frozen route was therefore
ranking-only.

The formal verifier independently recalculated input hashes and overlaps, 180
SolventSeg predictions, 72 metric cells, 45,000 formulation-bootstrap rows,
3,300 anchor metric rows, 1,500 anchor contrasts, seven 10,000-permutation
tests, and 40 FINALES metric cells. The recipient stress-test verifier aligned
all 300 source rows with the formal anchor table and independently reconstructed
the strongest-recipient and oracle contrasts.

## S11. Amendments and outcome-blind boundaries

Implementation-only amendments are recorded in:

- `MATBENCH_STEELS_CONFIRMATION_AMENDMENT.md`;
- `KIT_TEMPERATURE_BORROWING_AMENDMENT.md`;
- `CALISOL_EXTERNAL_BORROWING_AMENDMENT.md`;
- `OOD_DECISION_BORROWING_SPEC.md` and `ood_decision_borrowing_design.json`;
- `hard_ood_composition_design.json`;
- `obelix_ood_discovery_design.json`;
- `CALTECH_IONIC_SCHEMA_AMENDMENT.md`;
- `CALTECH_IONIC_INFERENCE_AMENDMENT.md`;
- `CALTECH_IONIC_IMPLEMENTATION_AMENDMENT_2.md`;
- `CALTECH_IONIC_INFRASTRUCTURE_AMENDMENT_3.md`;
- `CALTECH_IONIC_VERIFIER_AMENDMENT_4.md`;
- `CALTECH_IONIC_REMOTE_VERIFICATION_AMENDMENT_5.md`.
- `local_gated_neighbor_portfolio_design.json`;
- `family_first_neighbor_portfolio_design.json`;
- `STARRYDATA_REVERSE_TRANSPORT_SCHEMA_AMENDMENT.md`;
- `STARRYDATA_FORMAL_EXECUTION_AMENDMENT.md`;
- `STARRYDATA_VERIFIER_AMENDMENT.md`;
- `TRI_OER_CLEAN_REPLACEMENT_PROTOCOL.md`;
- `TRI_OER_PICKLE_SCHEMA_AMENDMENT.md`;
- `TRI_OER_VERIFIER_AMENDMENT.md`;
- `MULTI_TARGET_OOD_BORROWING_PROTOCOL.md` and
  `multi_target_ood_borrowing_design.json`;
- `STATE_MATCHED_MPEA_BORROWING_PROTOCOL.md`,
  `state_matched_mpea_balam_design_v2.json`, and
  `STATE_MATCHED_MPEA_CONTROL_AMENDMENT_V2.md`.
- `OPTICAL_SUPERVISED_BORROWING_PROTOCOL.md`,
  `OPTICAL_SUPERVISED_VERIFIER_AMENDMENT.md`, and
  `optical_supervised_borrowing_config.json`.
- `BAMBOOMIXER_CROSS_DATABASE_INTERACTION_PLAN_2026-07-30.md`,
  `bamboomixer_cross_database_interaction_design.json`, and
  `BAMBOOMIXER_RECIPIENT_BASELINE_STRESS_TEST_2026-07-30.md`.

The amendment rule was that code or schema defects could be corrected without
changing the designated target, source, budget, controls, learner, or decision
gates. Smoke-test outputs are not claim-bearing and are absent from the release
bundle.

## S12. Reproducibility and reporting checklist

- [x] Source revisions and remote files pinned by commit or hash.
- [x] Frozen machine-readable designs retained.
- [x] Discovery and confirmation entities separated for the internal map.
- [x] Exact identities and provenance groups audited at every external split.
- [x] Target-training source feature cross-fitted.
- [x] Test target labels and same-series fitted quantities forbidden.
- [x] Practical, uncertainty, absolute-utility, model, source, leakage,
  learning-curve, distance-control, and placebo gates reported.
- [x] Multiplicity correction applied to the five refined internal candidates.
- [x] Null and harmful edges retained.
- [x] Compact claim-bearing outputs and figure source data versioned.
- [x] Large row-level outputs reproducible and hash-addressed by the release
  process, but not required in the Git working tree.
- [x] Main figure supplied as editable SVG and print PDF, plus 300-dpi PNG and
  600-dpi TIFF.
- [x] State-matched MPEA V2 retains the V1 primary architecture and replaces
  only its architecture-mismatched shuffled control; each draw contains 14 Q4
  elemental systems (56 distinct systems across draws), with 25,680
  predictions, 100,000 bootstrap replicates, and all hashes independently
  verified.
- [x] Post-outcome formulation/subset uncertainty diagnostic reported for the
  interpolated KIT target-label equivalence; it does not redefine the frozen
  point-estimate decision.
- [x] OBELiX fixed-ranking and sequential-discovery endpoints reported
  separately; the hard-OOD subset is labelled exploratory.
- [x] Balam sequential input, design, environment, seed coverage, checksums,
  and completion sentinel verified after download.
- [x] Prespecified uniform-random acquisition retained despite outperforming
  both model-guided policies.
- [x] Caltech external target identity/article components, source composition
  and DOI exclusions, and target/source minimum gates audited before the formal
  run.
- [x] Caltech formal Job 70740 and same-environment verification Job 70767
  retained with hashes, compact summaries, amendments, and final `VERIFIED`
  sentinel.
- [x] Frozen Caltech adaptive null separated from retrospective static-ranking evidence
  and post-result neighbor-portfolio method selection.
- [x] Candidate-outcome permutation invariance, connected-component discovery
  units, shuffled-neighbor nulls, wrong-source controls, and the entity-repeat
  trade-off reported for CCA family-first method development.
- [x] Both outcome-unseen targets, all four TRI plates, all matched controls,
  all six hypothesis cards, and every unfavorable endpoint retained.
- [x] Job 70888 and portable verifiers reproduce the Starrydata, TRI, and
  multi-target compact summaries from frozen hashes.
- [x] Formal multi-target OOD Job 71429 retained all eight targets, 40 real
  edges, eight shuffled controls, three learners, and every unfavorable edge.
- [x] Formal multi-target OOD row-level outputs independently reconstructed to
  `multi_target_ood_VERIFIED.json` with matching design, summary, and completion
  hashes.
- [x] OOD groups defined without recipient outcomes, repeated model fits kept
  below intact evaluation groups and programme clusters in the inferential
  hierarchy, and the strongest relative gain not promoted without positive
  absolute OOD R² and OOD specificity.
- [x] Undefined secondary TRI Spearman cells disclosed without weakening finite
  primary-metric requirements.
- [x] Cross-database electrolyte source-source overlap disclosed; no source
  record overlaps SolventSeg; programme-balanced ranking, absolute-prediction
  abstention, 13-model recipient stress test, and FINALES boundary retained.
- [ ] Archive the exact release in a persistent repository and insert its DOI.
- [ ] Supply author list, affiliations, CRediT roles, funding, and author-
  confirmed conflict statement.
- [ ] Resolve or explicitly exclude the ESTM redistribution ambiguity before
  bundling any derived row-level database.
- [ ] Run the clean-environment build and analysis checks on the archived tag.
