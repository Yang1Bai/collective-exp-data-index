# Falsification-gated borrowing routes neighbouring experimental knowledge to out-of-distribution prediction, screening or abstention

**Target journal:** *Digital Discovery*  
**Article type:** Full paper, methods-led  
**Working status:** Core-story draft

## Abstract

Models are most valuable to experimental science when they extrapolate beyond
what has already been measured, but this is where data-poor models are least
reliable. Neighbouring experimental programmes could supply missing knowledge,
yet physical similarity between databases does not specify what is portable or
how it should be used. Here we treat knowledge borrowing as a directed,
falsifiable contract: donor and recipient must share candidate-level inputs,
the relevant experimental state, a declared transferable relation, and a
decision endpoint; otherwise the method abstains. Generic injection of a donor
prediction repaired 0 of 40 declared out-of-distribution (OOD) edges across
eight recipients, including all three declared cross-database edges. On
separate recipients, where the transferred object could instead be declared
explicitly, a component-order-invariant electrolyte relation learned from
10,407 measurements across 22 salts predicted 1,660 measurements of a salt
absent from the source with raw \(R^2=0.607\), Spearman \(\rho=0.864\), and
27.4% lower log-scale error than a
temperature--concentration baseline. Where absolute calibration was not
portable, a programme-balanced ordinal score computed without recipient labels
ranked unmeasured formulations at \(\rho=0.910\), whereas the strongest of 13
recipient-only models trained on five measured formulations reached
\(\rho=0.537\) (\(\Delta\rho=0.374\), 95% anchor-selection interval within
this recipient 0.213--0.562). Controlled chemical perturbations separated
predictive, ranking-only, and harmful edges, and the predeclared ordinal route
failed to qualify in a frozen second recipient and was withheld. These
retrospective benchmarks show that neighbouring experiments can materially
improve selected OOD predictions and screening decisions, provided that the
transferred object is qualified against matched falsifiers, routed to the
endpoint it can support, and withheld when the contract fails.

## 1. Introduction

Scientific exploration is intrinsically an out-of-distribution (OOD) problem.
The candidates most likely to extend knowledge lie outside the compositions,
formulations, or operating states already measured, and they are also the
candidates for which a data-poor model has the weakest empirical support,
mechanistic guidance, and uncertainty calibration. The tension is acute in
experimental materials science and chemistry, where measurements are expensive
and distributed across small, heterogeneous programmes. A neighbouring
programme may nevertheless contain partial knowledge of a shared composition
space, transport process, structural motif, or measurement state. The
unresolved question is whether that knowledge can reduce an OOD evidence
deficit without importing a spurious relation or negative transfer.

Larger data collections do not resolve this problem by themselves. An
experimental value is inseparable from material identity, formulation or
processing, test conditions, provenance, and reporting practice. Distributed
databases therefore constitute a partial scientific memory rather than a pool
of interchangeable labels [@Draxl2022FAIR; @Akhound2026ExperimentalMemory].
Harmonized infrastructures make that memory findable and exchangeable
[@Blaiszik2016MDF; @Andersen2021OPTIMADE; @MedinaSmith2021Vocabulary], but
pooled correlations can still be driven by chemical families, restricted
ranges, or coupled parameter estimation
[@Krug1976Compensation; @CornishBowden2002Phantom]. Transfer learning,
cross-property models, task maps, and multi-information-source optimization
offer more active forms of reuse
[@Yamada2019Shotgun; @Jha2019DeepTransfer; @Gupta2021CrossProperty;
@Chang2022MixtureExperts; @Zamir2018Taskonomy; @Kandasamy2017Multifidelity].
Yet a related database is not automatically a calibrated fidelity, and a
strong in-domain fit is not evidence that its knowledge survives a new
experimental programme. That failure mode is itself an established field:
negative transfer has a systematic taxonomy of causes and mitigations
[@Zhang2023NegativeTransfer], reliable prediction has long been bounded by an
explicit applicability domain [@Sahigara2012ApplicabilityDomain], the option to
withhold a decision rather than issue an unreliable one dates to the classical
error--reject trade-off [@Chow1970Reject], and combining independent candidate
orders without calibrated scores is standard rank fusion [@Cormack2009RRF].
What is missing is not any one of these components but their conjunction at the
level of an experimental donor--recipient edge, where the transferred object
and decision endpoint are declared together.

The missing unit is not another database but a qualified relation. We call two
programmes neighbours for a particular task only if they share a
candidate-level representation and a falsifiable physical or experimental
relation to the recipient endpoint. What crosses that directed edge may be a
composition--performance relation, a state-aware mixture response, or an
ordinal score; it need not be a raw feature vector or a calibrated property
value. This definition matters because heuristic OOD splits can remain
interpolative [@Li2025OOD], whereas transformations can be more portable than
raw features or pretrained weights [@Yahagi2025DomainTransformation]. It also
inverts the burden of proof. A borrowing edge must preserve the state that
makes the relation meaningful, beat a matched false donor, improve the
endpoint that will guide the experiment, and be rejected when any required
condition fails.

Here we introduce falsification-gated knowledge borrowing. The method keeps the
source database behind, permits only a qualified relation or candidate order to
cross into the sparse OOD recipient, and routes that object to prediction,
screening, or abstention (Fig. 1). We test the idea along increasing transfer
distance. The obvious alternatives fail first: unchanged coefficient transport
collapses across alloy programmes, and generic donor-feature injection repairs
0 of 40 declared OOD edges. On a separate recipient, a
component-order-invariant relation learned from 10,407 conductivity measurements
then reduces log-scale error by 27.4% for a
salt absent from the source, and a controlled catalyst series shows why the
same kind of relation must be routed separately to prediction, ranking, or
rejection. Finally, where numerical calibration fails, an ordinal score from
three independently trained programmes orders unmeasured formulations at
\(\rho=0.910\), compared with \(\rho=0.537\) for the strongest recipient-only
model trained on five measured formulations, yet the predeclared score fails to
qualify in a frozen second recipient. The result is not a universal transfer
model. It is an operational map from a qualified neighbouring relation to
numerical prediction, candidate screening, or abstention, together with the
falsifiers that define where each route ends.

## 2. Methods

### 2.1 From experimental records to directed donor--recipient edges

The analyzed evidence layer contained 21 accessible experimental resources,
each of which contributed numerical values to at least one reported
integration, borrowing, artifact, or boundary analysis. Thirteen resources
were normalized locally, seven entered through frozen task-specific
representations, and the National Institute of Standards and Technology
(NIST) adsorption archive was streamed for the artifact test. We do not use
the size of the broader catalog as evidence of transfer.
The normalized snapshot contained 96,184 source-pinned measurements, 230
reported property labels, and 29,516 canonical formula, molecule, or mixture
entities.

The reusable unit was a measurement linked to its material identity,
experimental state, provenance, source revision, and quality flags. Formulas
were converted to normalized element fractions, molecular structures were
canonicalized with RDKit, and liquid formulations retained component identity,
ratio, salt, concentration convention, and temperature. Property labels and
units remained source-specific unless an explicit conversion was defined.
Article, laboratory, experimental campaign, and material-system identifiers
were retained because they determined the valid resampling and leakage
boundaries.

Donor and recipient were directed task roles rather than permanent database
labels. A donor supplied a learned relation, prediction, or ordinal score. A
recipient supplied the held-out outcome used to judge numerical prediction or
candidate screening. A resource could be a donor in one edge and a recipient
in another. Calling a resource a donor indicated an attempted information
supply, not demonstrated benefit.

### 2.2 The borrowing contract: qualify, transfer, route, and falsify

Each borrowing attempt was treated as one directed contract and evaluated in
four steps (Fig. 1): require common candidate inputs, align the experimental
state, declare the physical relation and decision endpoint, and challenge the
edge with matched falsifiers. An edge was
eligible only when donor and recipient shared a representation available for
every recipient candidate and a falsifiable physical or experimental relation
connected the donor endpoint to the recipient decision. Adjacency was
therefore task-specific. The same electrolyte resources, for example, could be
neighbours for formulation ranking but not for absolute conductivity
calibration.

The transferred object was selected before fitting the recipient model. Three
forms of knowledge were evaluated in the main text:

1. **Relation-based prediction.** A donor learned a relation between
   recipient-available composition or formulation variables and a measured
   endpoint. A small number of recipient anchors could correct local residuals
   or absolute scale.
2. **Component-order-invariant (permutation-invariant) mixture prediction.** Component descriptors were
   aggregated as molar-fraction-weighted means and variances, while
   temperature, concentration, inverse temperature, log concentration, and
   their interactions were retained explicitly. This allowed a source relation
   to be evaluated on an unseen salt without relying on component order.
3. **Ordinal scoring.** Donor predictions were converted to candidate order
   and retained outside the recipient surrogate. Separately trained programmes
   contributed programme-balanced (equal-programme) weight so that source size
   did not determine the score.
   This route was evaluated only for screening, not as a calibrated property
   prediction.

Every edge was then evaluated at one declared decision endpoint. Numerical
prediction used held-out root-mean-square error (RMSE) and \(R^2\). Screening used
Spearman rank correlation \(\rho\), precision for the true high-performance
quartile, and normalized shortlist regret. Numerical prediction and candidate
screening were evaluated separately and could not validate one another.

A conjunction of gates determined the final route. Validity gates excluded
identity, provenance, and split leakage. Utility gates required a practical
effect and, for numerical prediction, useful absolute performance. Robustness
gates tested intact-group resampling, recipient-label draws, and learner
sensitivity. Specificity gates compared the real donor with shuffled,
wrong-property, state-only, chemistry-permuted, or architecture-matched false
donors. Failure of any endpoint-required gate produced abstention rather than
post hoc donor replacement.

### 2.3 Scientific OOD units, fair baselines, and inference

The OOD unit followed the scientific data-generating process. Complete
composition systems, formulations, articles, or experimental programmes were
held out intact. Repeated measurements from the same formulation or material
were never divided between recipient training and evaluation merely because
their row identifiers differed. Candidate distance and anchor selection were
computed without recipient outcomes.

When a donor-derived prediction entered recipient training, predictions for
recipient-training rows were cross-fitted and source models excluded every
evaluation identity or provenance group. Directly measured donor values from
an evaluation recipient were never injected. Recipient-only and borrowed
models received the same recipient labels, splits, representations,
hyperparameter search, and random seeds.

For the ordinal benchmark, 13 recipient-only configurations covered linear and
radial-basis kernel regression, nearest-neighbour models, Random Forest,
ExtraTrees, and a recipient rank ensemble. A non-deployable per-draw oracle
selected the best recipient-only configuration after each evaluation draw and
therefore provided an adversarial ceiling rather than an operational baseline.

Uncertainty was computed over the independent experimental unit. Candidate or
formulation bootstraps retained all repeated measurements belonging to that
unit. One-sided permutation tests evaluated the declared beneficial direction,
and Holm correction was applied within named contrast families. Repeated
random seeds were treated as algorithmic sensitivity, not as independent
experiments. Unless otherwise stated, intervals are two-sided 95% intervals.

### 2.4 Baselines that test the obvious forms of reuse

We first tested whether aggregation or generic feature transfer was sufficient.
For a direct coefficient-transport test, the relation between ultimate tensile
strength and yield strength in the Borg multi-principal-element alloy database
was fitted in log space and applied unchanged to the independent BIRDSHOT
campaign [@Attari2025Tabular]. Exact compositions did not overlap.
Thermoelectric and adsorption compensation analyses supplied complementary
family-structure and fitted-parameter artifact checks
[@Krug1976Compensation; @Siderius2019ISODB].

The generic OOD benchmark included eight recipient tasks, five real donors per
recipient, and one shuffled version of the designated donor, producing 40 real
edges and eight shuffled controls. Formula tasks used elemental fractions and
composition-distribution descriptors; molecular tasks used Morgan
fingerprints. Intact evaluation groups were ranked by outcome-independent
distance and divided into quartiles. The farthest quartile was the primary OOD
region. Ridge regression was primary, with Random Forest and ExtraTrees
sensitivities. One hundred paired recipient-label draws compared target-only,
real-donor, wrong-donor, and shuffled-donor fits. A complete repair required
lower OOD RMSE, positive augmented OOD \(R^2\), learner robustness,
matched-control superiority, and multiplicity-adjusted support.

### 2.5 Controlled chemical perturbations

The controlled oxygen evolution reaction (OER) series contained a
462-catalyst donor and four complete 126-catalyst derivative systems from the
SpecGen robotic programme [@Zhou2026SpecGen]. All five systems used the same
six-slot composition grid, spectral measurement protocol, and OER potential at
10 mA cm\(^{-2}\). Each derivative replaced one ligand or metal center, and the
complete derivative system was held out as the OOD unit.

The frozen primary analysis selected a spectral donor using donor-only
cross-validation. A prespecified six-slot composition control proved more
portable and was promoted in a disclosed post-primary analysis after its
target correlations had been inspected. The composition donor used a
500-tree Random Forest. Five recipient catalysts were selected without
outcomes. Borrowed prediction combined the frozen donor estimate with
three-nearest-neighbour interpolation of donor residuals; the target-only model
used the same five anchors and distances without the donor estimate. Five
hundred refitted source-label permutations supplied the matched falsifier.
Candidate identities were bootstrapped while retaining all anchor draws.

An accepted numerical edge required positive donor skill, zero-label
\(\rho>0.30\), Holm-adjusted \(p<0.05\), at least 5% RMSE reduction, at least
0.10 rank gain, positive intervals for both gains, and borrowed
\(\rho>0.40\). An edge with supported ranking but failed RMSE was routed to
ordinal use; a harmful edge was rejected.

### 2.6 Cross-database prediction of an unseen electrolyte component

The electrolyte source contained 10,407 experimental conductivity
measurements covering 22 salt identities [@Yang2026BambooMixer]. The downloaded
external archive contained 1,827 measurements, but a semantic audit found that
167 belonged to four reference salts. The declared recipient was therefore
restricted to 1,660 lithium hexafluoroarsenate measurements from 156 exact
formulations; this salt was absent from the source
[@Lai2026BambooMixerExtension]. The archive-level mistake was identified after
the original analysis and corrected without refitting any model. Exact
formulation identities, including all temperature and concentration rows,
remained indivisible during resampling.

Random Forest source relations used 400 trees and three fixed seeds. The full
component-order-invariant mixture relation was compared with temperature and
concentration alone, a chemistry-permuted source, a source excluding the
closest abundant fluorinated lithium salt, that neighbouring salt alone, and
size-mismatched salt controls. External effects used 1,000
formulation-grouped bootstrap replicates. Few-shot analyses selected 1, 3, 5,
10, 20, 50, or 100 recipient formulations by outcome-independent maximin
coverage. Recipient labels were restricted to shrinkage calibration and could
not refit the source chemistry relation.

This benchmark was developed after the public recipient outcomes and the
published transfer observation had been inspected. It is therefore a
retrospective test of whether the declared representation and falsifiers
isolate a portable relation, not an independent prospective confirmation.

### 2.7 Ordinal transfer and a frozen programme boundary

Three conductivity sources were trained separately: 10,012 measurements from
the large electrolyte source after removal of the complete recipient-family
chemistry, 410 measurements from three literature-aggregated source articles,
and 1,089 formulation--temperature aggregates from a controlled conductivity
programme. Their log-conductivity predictions were averaged with equal
programme weight rather than pooling records. A strict
composition--temperature--outcome audit found 71 near-identical records
between two sources and none between any source and the 180-row,
36-formulation SolventSeg recipient [@Wang2022SolventSegregation].

The primary endpoint was candidate ranking at 25 \(^{\circ}\)C. Three, five,
or ten recipient formulations were selected by outcome-independent maximin
coverage over 100 draws and excluded wholesale from scoring. The source score
was compared with state-only and chemistry-permuted donors, the 13
recipient-only configurations, and the per-draw recipient oracle. Rank tests
used 10,000 outcome permutations with Holm correction across seven source
arms. Formulation-grouped uncertainty used 5,000 resamples. Absolute
prediction and ordinal ranking had separate gates.

Before accessing a second recipient's row-level outcomes, we froze the donor
model, chemistry conversion, three-anchor budget, metrics, practical
thresholds, and inference. The second recipient was the November 2023
experimental phase of the Fast INtention-Agnostic LEarning Server (FINALES)
electrolyte campaign [@Vogler2024FINALES; @Steensen2024FINALESData]. The first three
chronologically distinct formulations were anchors and the remaining 16
formed the primary evaluation pool. The donor was compared with the strongest
recipient-only model fitted to the same anchors. No donor, split, metric, or
threshold was changed after outcome access.
The elements frozen identically across the two recipients were the donor
models, chemistry conversion, transferred object, metrics, practical
thresholds, and inferential procedure. Two elements differed: FINALES used the
first three chronologically distinct formulations rather than maximin coverage,
and its contrast used that single anchor set rather than repeated
outcome-independent selections. The chronological rule was chosen before
outcome access to reproduce deployment inside a temporally ordered autonomous
campaign. A disclosed post-outcome maximin sensitivity diagnoses this design
difference but does not replace the frozen result (Supplementary Section
S10.4).

### 2.8 Reproducibility

Claim-bearing designs, source revisions, software versions, random seeds,
compact outputs, figure source data, and file hashes are recorded in the
public release. Independent verification scripts recompute the principal
metrics from row-level outputs and check semantic invariants including split
units, source exclusion, anchor counts, and metric direction. The complete
local test suite contains 118 passing tests. Detailed models, seeds,
thresholds, secondary tasks, and all null and harmful edges are reported in
the Supplementary Information.

## 3. Results

### 3.1 Strong fits and generic features do not yield portable knowledge

The first test asked whether the apparent knowledge in one programme could be
reused without qualifying what was shared. It could not. A strong in-domain
alloy relation failed as soon as experimental provenance changed. The Borg
alloy data contained 495 paired ultimate- and yield-strength records with
log--log \(R^2=0.790\). The independent BIRDSHOT campaign shared no exact
composition and had an in-domain \(R^2=0.067\). Applying the Borg coefficient
unchanged produced \(R^2=-3.006\) (95% composition-cluster interval
\(-4.154\) to \(-2.185\); Fig. 2a). The median strength ratio changed from
1.36 to 2.72. The source relation was real, but not portable as an unchanged
coefficient.

Pooled regularity tests reached the same verdict from the opposite direction:
a strong adsorption heat--intercept association (\(R^2=0.637\) across 1,103
systems) survived a parameter-coupling artifact null yet retained
adsorbate-family structure under article-cluster tests (\(p=0.0002\)).
Association, artifact resistance, family conditioning, and transport therefore
remained distinct claims (Supplementary Section S7).

The same conclusion held at portfolio scale. Generic donor-feature injection
failed the operational test: none of the
40 real edges across eight recipients passed the complete OOD-repair gate
(Fig. 2b,c). The largest apparent edge lowered far-OOD error but retained
negative absolute \(R^2\) and improved the near region by a comparable amount.
Across the seven independent experimental programmes represented in the
benchmark, the mean designated-edge far-OOD gain was 0.92% (95% interval
\(-0.35\) to 2.92%). Five of the eight designated edges paired two properties
measured within the same database, and three crossed a database boundary; none
of the three cross-database edges passed. Adding a physically adjacent model
output was therefore not a reliable way to repair recipient OOD prediction,
either within or across programmes.

Nor was model capacity the explanation. Strong pretrained molecular encoders
that passed every source-skill gate made a scaffold-OOD photocatalysis recipient
28.1% worse on average and failed against their own shuffled controls
(Supplementary Section S10.2).

These negative controls bound the generic mechanism within its tested envelope;
they do not show that the edges themselves are unrepairable, because no
declared-relation route was applied to them. What they identify is the
scientific object that the remaining experiments must preserve: the relation
that survives the boundary, while discarding the absolute scale or state
dependence that does not. The experiments that follow therefore test that
object on separate recipients where it can be declared and falsified, not on
the benchmark edges themselves.

### 3.2 A component-order-invariant relation crosses database and salt identity

The strongest numerical test placed both experimental provenance and component
identity outside the source. The donor contained 10,407 conductivity
measurements spanning 22 salts; the external archive contained 1,827
measurements, of which 1,660 measurements and 156 formulations were strictly
lithium hexafluoroarsenate, a salt absent from the source (Fig. 3a). All
headline estimates below use only that declared salt. Without recipient labels,
the frozen mixture relation achieved log-scale \(R^2=0.718\), raw-scale
\(R^2=0.607\), log-RMSE 0.342, and \(\rho=0.864\) (Fig. 3b).

Matched falsifiers identified what crossed the boundary (Fig. 3c). Relative to
temperature and concentration alone, the full relation reduced log-RMSE by
27.41% (95% formulation-bootstrap interval 21.79--32.92%), increased
\(\rho\) by 0.158 (0.130--0.190), and increased raw \(R^2\) by 0.216
(0.167--0.270). Relative to a chemistry-permuted source, it reduced log-RMSE
by 25.88% (20.73--31.09%) and increased \(\rho\) by 0.129
(0.102--0.159). The portable signal therefore contained formulation chemistry,
not only a shared temperature--concentration surface.

Salt ablations separated local chemical adjacency from source breadth.
Removing the abundant fluorinated LiPF\(_6\) analogue worsened log-RMSE by
16.08% (12.10--19.80%) and ranking by 0.040 (0.022--0.061). Yet LiPF\(_6\)
alone was also insufficient: the complete source improved log-RMSE by 28.50%
(22.25--34.22%) and ranking by 0.047 (0.030--0.067). Local chemical similarity
and source breadth were therefore complementary rather than interchangeable.

The identity split was not an extreme representation-distance split. The
target salt descriptor lay at the 50th percentile of leave-one-salt-out source
distances. Temperature and concentration were entirely inside the source
ranges, whereas only 30.4% of target solvent identities had appeared in the
source; in the combined solvent--state representation, the target median
nearest-source distance was at the 94.8th reference percentile and 50.4% of
rows lay within the source 95th-percentile boundary. The benchmark is thus OOD
in salt identity, solvent coverage, and experimental provenance, but not in
every state variable (Supplementary Section S10.3).

Five recipient anchors mainly restored scale. The frozen relation achieved
mean log-RMSE 0.337 and raw \(R^2=0.609\), whereas a recipient-only Ridge model
fitted to the same five formulations had mean log-RMSE 0.711 and
\(R^2=-0.412\). Shrinkage calibration increased raw \(R^2\) to 0.667 while leaving candidate
order essentially unchanged. This retrospective external benchmark establishes
the feasibility of numerical relation transfer, not prospective confirmation
in a previously unseen programme, and it leaves open whether one qualified
relation should be used the same way in every nearby recipient.

### 3.3 Controlled perturbations separate prediction, ranking and harm

A controlled catalyst series then tested whether one declared composition
relation should be used in the same way for every nearby recipient. The assay,
composition grid and endpoint were held fixed while one chemical factor changed
at a time. The six-slot donor had out-of-fold \(R^2=0.774\) and
\(\rho=0.887\). Before recipient labels were revealed, it ranked three of four
complete derivative systems with \(\rho=0.552\), 0.610 and 0.748; each exceeded
500 refitted shuffled-source models after Holm correction (\(p=0.008\)). The
remaining metal-substitution system had \(\rho=0.259\) and failed the practical
gate.

In the disclosed post-primary composition analysis, five anchors converted the
relation into useful numerical prediction in two systems (Fig. 4b,c). Relative
to the matched target-only model, RMSE fell by 16.3% (95% interval
9.2--22.9%) and 26.1% (20.0--31.7%), while Spearman correlation increased by
0.347 (0.260--0.426) and 0.407 (0.352--0.459), respectively. Each effect was
evaluated on every non-anchor catalyst in the complete held-out system rather
than on random donor-like rows.

The other systems defined the routing boundary. One improved ranking by 0.282,
but its 3.2% RMSE reduction had an interval crossing zero (\(-1.8\) to 9.7%);
it was routed to ranking only. In the other, borrowing increased RMSE by 10.4%
(3.4--17.2% worse), so the edge was rejected. Under otherwise matched
conditions, the same relation therefore produced numerical utility, ordinal
utility and harm. This selectivity experiment explains why the map routes each
edge to prediction, screening or abstention instead of reporting a pooled
transfer effect.

### 3.4 Candidate order transfers when absolute scale does not

Numerical prediction is not the only decision an experiment requires. We
therefore asked a narrower question: can neighbouring knowledge identify which
unseen candidates should be measured first, even when their property values
cannot be calibrated, and can it do so better than any model built from the few
labels the recipient actually has?
The data-poor SolventSeg recipient contained 36 formulations, and no source
record matched a recipient record under the frozen composition, temperature,
and outcome fingerprint. Scoring all 36 formulations at 25 \(^{\circ}\)C, the
unchanged three-programme source order achieved \(\rho=0.918\),
high-performance-quartile precision of 1.000, and zero normalized regret; the
claim below is based instead on anchor-excluded evaluation, in which measured
formulations are withheld from scoring.

Across 100 outcome-independent selections of five measured recipient
formulations, the zero-label source score retained mean \(\rho=0.910\),
precision 0.933, and regret 0.00047 on the remaining candidates. The strongest
of 13 recipient-only configurations trained on those same five formulations
was radial-basis kernel ridge regression, with \(\rho=0.537\), precision 0.490,
and regret 0.0393. The source advantage was \(\Delta\rho=0.374\) (95% interval
0.213--0.562 over anchor selections, conditional on this recipient programme;
Fig. 5a). Even the per-draw oracle, which selected the best
recipient-only model after observing each evaluation, remained below the
source score by \(\Delta\rho=0.300\) (0.183--0.540). The zero-label ordering
was non-random under 10,000 outcome permutations (Holm-adjusted one-sided
\(p=0.00070\)).

The advantage did not close within the tested label budget: across three, five,
and ten measured formulations, no fixed recipient-only configuration reached
the zero-label source score, which itself did not use the added labels (Fig.
5b). Ten formulations exceed one quarter of the recipient candidate pool, so
the borrowed order replaced a substantial measurement campaign rather than one
or two missing observations.

Programme-balanced weighting across separately trained programmes produced a
smaller but reproducible gain over the broad single donor. The
programme-balanced score increased
\(\rho\) by 0.0236 (0.0069--0.0397) and increased high-performance-quartile
precision from 0.826 to 0.933. The large scientific gain, however, was not
multi-source ensembling by itself. It was the recovery of useful candidate
order from neighbouring experiments when five recipient labels could not
support that order.

Absolute prediction gave the opposite decision. The source portfolio worsened
all-temperature log-RMSE by 18.0% relative to the state-only source, and the
five-anchor calibration interval crossed zero. The endpoint-specific
gate therefore accepted ordinal screening and rejected numerical calibration.
The distinction is operational: the score can prioritize experiments, but it
cannot be interpreted as the recipient conductivity. A second programme was
required to test whether even this narrower route was portable.

### 3.5 A frozen second recipient fails to qualify, and the map abstains

The accepted ordinal object and its decision thresholds were frozen before
application to a second experimental programme; the deployment used the first
three chronological recipient formulations rather than repeated maximin anchor
sets. It did not
qualify. In the frozen Fast INtention-Agnostic LEarning Server electrolyte
recipient, the donor ranking achieved pairwise concordance of 0.694, whereas
the strongest recipient-only model fitted to the same three chronological
anchors achieved 0.783. The donor advantage was \(-0.089\) (95% bootstrap
interval \(-0.293\) to 0.096; permutation \(p=0.131\); Fig. 5c), which was
compatible with harm, no effect, or a modest donor advantage. Under the frozen
contract, this is the situation in which the method must withhold the edge
rather than defend it.
High-performance-quartile precision tied at 0.50, and donor regret was worse
(0.563 versus 0.180). The edge was rejected without changing its donor,
anchors, representation, metric, or threshold.

A disclosed post-outcome sensitivity replaced the chronological anchors with
the SolventSeg-style maximin policy over 100 deterministic starts (17 unique
anchor sets). The donor again trailed the strongest average recipient model:
mean concordance was 0.568 versus 0.686 and mean advantage was \(-0.119\)
(2.5th--97.5th anchor-selection interval \(-0.232\) to 0.101), positive in only
9% of draws. This result shows that the directional non-qualification is not
unique to the chronological anchor set, but it cannot replace the frozen test.

Named chemistry and endpoint were matched across the two recipients, but
experimental programme, sampling policy, and measurement provenance were not.
The contrast between the strong SolventSeg result and frozen non-qualification
shows why physical adjacency can nominate an edge but cannot validate it.
Because the recipients also differed in anchor policy and in the number of
evaluated candidates, the comparison is a failure of the fixed donor object and
decision thresholds to qualify in the second programme, not an estimate of how
much of the SolventSeg advantage is programme-specific. A
usable knowledge-borrowing map must encode positive, ranking-only, null, and
harmful outcomes because each leads to a different experimental action.

## 4. Discussion

### 4.1 Experimental knowledge is relational rather than database-level

The common feature of the successful cases was not a model architecture or a
large source. It was that the information allowed to cross the boundary was
narrower than a database. Absolute labels retained programme-specific scale,
measurement state, and provenance effects. What survived was a
composition--performance relation under a controlled perturbation, a mixture
relation invariant to component order, or an ordinal score that did not require
absolute calibration. Generic feature injection failed because it treated one
donor prediction as though it could serve all of these roles.

We therefore do not introduce a transfer model. The contribution is an
endpoint-resolved falsification protocol in which the transferred object, the
decision endpoint, and the matched falsifier are declared before recipient
outcomes are accessed, and null and harmful edges remain in the reported
denominator.

This distinction also explains why neither source size nor physical similarity
alone determined utility. The unseen-salt result combined a local fluorinated
salt analogue with broader, but incomplete, solvent--state support; the
applicability audit shows that neither chemical identity nor state coverage
alone explains the transfer.
The ordinal result benefited modestly from equal weighting across independently
trained programmes, but its main advantage came from preserving source-derived
order rather than adding recipient parameters. Experimental neighbourhood is
therefore operational rather than taxonomic. It exists only for a declared
relation, candidate set, state, and decision endpoint. This is the principal
scientific distinction between borrowing knowledge and merely pooling data.

### 4.2 A borrowing map routes actions, not similarities

The same donor can be useful for one action and invalid for another. The
SolventSeg score produced a large and robust ranking gain while failing
numerical calibration. One catalyst derivative similarly retained ranking
utility without supported RMSE improvement. Treating these cases only as
failed regressions would discard useful screening knowledge; treating them as
calibrated property models would overstate the evidence. Endpoint routing
avoids both errors by deciding in advance what the borrowed information is
allowed to support.

The practical output is consequently a map with three actions. A qualified
relation may enter numerical prediction; an uncalibrated but validated score
may prioritize candidates; and a failed edge is withheld. The governing
question is not "Is this database related?" but "Which relation is shared, for
which candidates, at which endpoint, and against which falsifier?" That change
turns positive and negative transfer into decision-relevant scientific
evidence rather than post hoc model selection.

Two claims must be separated. The evidence-generating protocol--declared
object, declared endpoint, matched falsifier, grouped inference, and retained
null and harmful edges--is what the present experiments exercise. The
edge-selection rule is a different and weaker object. In the leave-one-programme
benchmark (Supplementary Section S9), an outcome-free gate trained on 97 edges
across 13 programme clusters admitted 17 of 20 held-out tasks with one clearly
harmful admission, but retained a clearly beneficial edge in only four of the
ten tasks where one existed and did not outperform never borrowing after Holm
correction; adjacency alone was numerically stronger. The gate therefore
avoids much harm but misses benefit. We do not claim that it identifies useful
untested edges better than a domain expert. The map determines what an
already-tested edge may support; it is not yet a validated selector for new
edges.

### 4.3 Retrospective evidence defines the next prospective test

The strongest cross-programme positive results remain retrospective, and the
asymmetry deserves to be stated plainly. Every independent external validation
whose complete route was frozen before recipient-outcome access ended in null,
rejection, or abstention: the FINALES second recipient and the outcome-unseen
Starrydata and TRI programmes reported in the Supplementary Information. By
contrast, the controlled catalyst composition analysis was promoted after its
planned control was inspected; the unseen-salt representation was designed
after the public recipient outcomes and published transfer observation were
known; and the SolventSeg portfolio and recipient stress test were developed
after earlier outcomes had been inspected. Design freezes, intact-group
inference, matched falsifiers, and independent recalculation protect the
reported estimands, but they cannot convert retrospective method development
into prospective confirmation.

This asymmetry does not erase the retrospective positives, nor does a frozen
negative validate the framework by itself. Together they establish two bounded
facts. First, large OOD improvements are possible under explicit contracts.
Second, a fixed donor object and decision thresholds can fail to qualify in an
independent programme. The current evidence therefore does not estimate the probability
that a newly nominated neighbouring programme will transfer. Positive evidence
is concentrated in selected catalyst and electrolyte programmes, SolventSeg
contains 36 formulations, and the frozen second recipient was withheld. The
map is consequently a falsifiable routing procedure over tested edges, not a
validated predictor of benefit for untested programmes.

The current model envelope is limited to composition descriptors and tree or
kernel learners. Graph representations, mechanistic latent variables,
calibrated Gaussian processes, and cost-aware experimental policies may expose
additional portable relations, but they require the same grouped and
falsifier-controlled evaluation. The decisive next test is therefore not
another retrospective edge. It is a preregistered recipient programme in which
donor selection, transferred object, anchor budget, falsifiers, and decision
endpoint are frozen before any recipient outcome is accessed, followed by
prospective measurement of the proposed shortlist. The present framework
supplies the contract, falsifiers, and failure criteria for that experiment.

## 5. Conclusions

Neighbouring experimental data can materially improve data-poor OOD decisions,
but adjacency is not itself transferable knowledge. Generic donor-feature
injection repaired 0 of 40 declared edges. On separate recipients where the
shared relation and decision endpoint were explicit, a mixture relation reduced
external LiAsF\(_6\) error by 27.41%, and a zero-label ordinal score ordered unmeasured
formulations at \(\rho=0.910\), where the strongest five-label recipient-only
model reached 0.537. Controlled predictive, ranking-only, harmful, and
frozen-abstention cases showed where those gains stopped. The
result is an operational rule for borrowing scientific knowledge: define a
directed edge, preserve its experimental state, transfer the narrowest object
required by the decision, challenge it with recipient-only and matched false
donors, and abstain when the contract fails.

## Data availability

The public catalog, source metadata, normalized-schema definition, source
revisions, and task-specific provenance records are provided in the
repository. Raw or derived data are redistributed only where source terms
permit. External resources that cannot be redistributed are identified by
stable URLs, file identifiers, commits, and hashes. The independent
electrolyte recipients are available from the SolventSeg archive
(doi:10.5281/zenodo.6299956; associated article
doi:10.1016/j.xcrp.2022.101047) and the FINALES Materials Cloud record
doi:10.24435/materialscloud:qt-1s.

## Code availability

All claim-bearing analysis scripts, design records, compact outputs, figure
source data, and portable verification scripts are provided in the
repository. Large row-level prediction tables are reproducible from the
pinned inputs and are not required to verify the reported summary statistics.

## Author contributions

`[Insert CRediT author-contribution statement.]`

## Conflicts of interest

The authors declare no competing interests.

## Acknowledgements

`[Insert funding, institutional, computing, and contributor acknowledgements.]`

## Figure captions

**Figure 1 | Falsification-gated knowledge borrowing into a sparse OOD
recipient.** **a,** Conceptual illustration of three neighbouring experimental
programmes, their measurement records, and a sparse recipient landscape. The
source databases remain in place: only a candidate-level relation or ordering
signal can cross, and only after shared inputs, the relevant experimental
state, a declared physical relation, and a matched falsifier have been
satisfied. Most candidate streams terminate at these checks. The surviving
teal path enters the
recipient landscape, in which filled blue cubes denote measured anchors and
open orange cubes denote unmeasured OOD candidates; the coral branch denotes
abstention. Panel **a** is explanatory rather than quantitative. **b,**
Decision-level evidence from the committed result tables. Numerical prediction
is accepted for the external LiAsF\(_6\) programme: 27.41% lower log-RMSE than
a temperature--concentration baseline, raw \(R^2=0.607\), and \(\rho=0.864\).
Ordinal screening is accepted when a programme-balanced score computed without
recipient labels orders unmeasured formulations at \(\rho=0.910\)
(high-performance-quartile precision 0.933), whereas the strongest
recipient-only model trained on five measured formulations reaches
\(\rho=0.537\) (precision 0.490). Otherwise the method abstains: generic
donor-feature injection passed 0 of 40 complete OOD-repair gates, and the
frozen second-recipient donor concordance of 0.694 was below the recipient-only
value of 0.783.

**Figure 2 | Strong fits and generic donor features do not establish portable
knowledge.** **a,** The relation between ultimate and yield strength is strong
inside one alloy programme (\(R^2=0.790\)) but fails unchanged coefficient
transport to an independent programme (\(R^2=-3.006\)); the dashed orange line
is fitted only to show the recipient shift. **b,** Mean relative far-OOD RMSE
effects for 40 real donor-feature edges across eight recipients. The outlined
column contains the declared donors; positive values denote lower error.
**c,** Collapsed audit of the declared edges. A complete pass requires useful
absolute performance, repeat and learner robustness, OOD- and
donor-specificity, multiplicity-adjusted inference, and exclusion of record
overlap. No real edge passes the complete gate; five of the eight designated
edges are within-database property pairs and three cross a database boundary,
with no cross-database pass. The seven-programme mean far-OOD gain is 0.92%
(95% interval \(-0.35\) to 2.92%).

**Figure 3 | Qualified relations improve selected complete OOD prediction
tasks.** **a,** A component-order-invariant relation trained on 10,407
measurements from 22 salts is applied without recipient labels to 1,660
measurements (156 formulations) of lithium hexafluoroarsenate, a salt absent
from the source. A post-outcome semantic audit excluded 167 archive rows from
four reference salts without refitting the model.
**b,** Zero-label external prediction. Colour density denotes overlapping
observations and the dashed line denotes equality; raw and log-scale \(R^2\)
are reported separately. **c,** Relative log-RMSE gain of the full relation
over matched state-only, chemistry-permuted, salt-exclusion, nearest-salt and
wrong-salt comparators. Points are formulation-grouped bootstrap means and bars
are 95% intervals. This benchmark was designed after the recipient outcomes
were public and is retrospective (Methods 2.6); the split is defined by salt
identity and experimental provenance rather than by representation distance.

**Figure 4 | A controlled chemical perturbation routes one relation to
prediction, ranking or rejection.** **a,** One oxygen-evolution assay,
composition grid and endpoint are retained while a single ligand or metal
factor changes, producing four complete 126-catalyst recipient systems. The
route is assigned from the joint numerical and ordinal gates, not from chemical
adjacency alone. **b,** Relative RMSE gain over the matched target-only model
after five recipient anchors. **c,** Spearman gain on the same non-anchor
candidates. Points are bootstrap means and bars are 95% intervals. The
amino-ligand system is admitted for ranking only, two systems for numerical
prediction and ranking, and the harmful iron-substitution edge is rejected.
These composition-relation analyses are disclosed as post-primary.

**Figure 5 | Cross-programme knowledge recovers candidate ordering but remains
programme-specific.** **a,** The zero-label source ranking compared with 13 recipient-only
configurations trained on five measured formulations and with a non-deployable
per-draw recipient oracle (15 rows in total). Points are means and bars are 2.5th--97.5th
percentiles over 100 outcome-independent anchor selections, conditional on this
recipient programme. **b,** Source and fixed recipient-only ordering across
three, five, and ten measured formulations; shaded regions are the corresponding
percentile intervals, including their negative lower tails. No recipient-only
configuration reaches the source score at any tested budget. **c,** Donor
advantage with 95% intervals in the primary recipient and under a frozen
contract in a second programme, where anchors were the first three
chronologically distinct formulations. The ordinal route is accepted only in
the first; in the second it fails to qualify and is withheld.
