# Endpoint-routed knowledge borrowing selectively improves out-of-distribution decisions from neighboring experiments

**Target journal:** *Digital Discovery*
**Article type:** Full paper, methods-led
**Working status:** Streamlined main-text draft

## Abstract

Materials models are least reliable where experimental evidence is sparse and
candidate distributions differ from the data used for training. Neighboring
experiments may contain missing scientific information, but pooling their
records or injecting a donor prediction does not make that information
portable. We introduce endpoint-routed knowledge borrowing, which matches the
transferred object to provenance distance and the recipient decision while
requiring grouped source skill, leakage exclusion, matched falsifiers,
practical utility, and abstention. Generic donor-feature injection repaired
none of 40 prespecified OOD edges across eight targets. A controlled
system-held-out perturbation series then exposed the required specificity. A
composition-to-OER relation learned from 462 catalysts was transferred to four
126-catalyst derivative systems. With five recipient anchors, two systems
passed the complete gate: pooled RMSE fell by 16.3% and 26.1% relative to the
matched target-only baseline, while Spearman rank gain was 0.347 and 0.407.
One derivative retained ranking utility only and one produced negative
transfer, which the framework rejected. Across articles, a response relation
plus one target-article anchor reduced macro-RMSE by 6.91% relative to the
same-anchor absolute donor. A permutation-invariant relation trained on 10,407
electrolyte measurements predicted an external new-salt programme zero-shot
with raw \(R^2=0.629\) and \(\rho=0.871\), reducing log-RMSE by 28.64%
relative to temperature and concentration alone. Across databases, an
equal-programme conductivity score from three separately trained sources
improved fixed-temperature candidate ordering with five recipient labels:
Spearman \(\rho\) was 0.910 versus 0.537 for the strongest of 13
recipient-only configurations (\(\Delta\rho=0.374\), 95% anchor-coverage
interval, 0.213–0.562). Absolute calibration failed its gate, and the
unchanged edge failed against a three-anchor recipient-only baseline in a
frozen second programme. Thus neighboring knowledge is transferable, but only
as a qualified relation, calibrated prediction, physics-aware mixture
relation, or ordinal score matched to the recipient endpoint; otherwise the
correct action is abstention.

## 1. Introduction

Artificial intelligence increasingly guides scientific prediction and
candidate prioritization, yet scientific progress depends on extending
knowledge beyond explored regimes. This is difficult in experimental science,
where measurements are costly and sparse. Models must extrapolate precisely
where observations, mechanistic guidance, and calibrated uncertainty are
weakest. Neighboring experimental domains may contain partial information about
shared composition, transport, structure, processing, or measurement state.
The central question is whether this information can reduce target-domain
knowledge scarcity without importing spurious relations or negative transfer.

Experimental measurements are not interchangeable property labels. Each value
is embedded in material identity, processing or formulation, measurement
conditions, provenance, and reuse constraints, although these fields are often
incomplete. Distributed records therefore form a partial scientific memory
rather than a smaller analogue of computed training data
[@Draxl2022FAIR; @Akhound2026ExperimentalMemory]. Treating them as
context-free labels can produce a data-only illusion in which a model appears
predictive while remaining detached from synthesis and measurement reality
[@Smit2026DataOnly]. Data infrastructures have improved discovery, exchange,
and metadata standardization
[@Blaiszik2016MDF; @Andersen2021OPTIMADE; @MedinaSmith2021Vocabulary], but
harmonization alone cannot establish which relations are transportable.
Pooled correlations can reflect chemical-family structure, restricted
experimental ranges, or coupled parameter estimation
[@Krug1976Compensation; @CornishBowden2002Phantom; @Bond2000Compensation].

Transfer learning, cross-property models, task maps, and
multi-information-source optimization show that external information can
improve a scarce target
[@Yamada2019Shotgun; @Jha2019DeepTransfer; @Gupta2021CrossProperty;
@Chang2022MixtureExperts; @Zamir2018Taskonomy; @Kandasamy2017Multifidelity].
These methods do not by themselves qualify an experimental neighbor. A related
database is not automatically a calibrated fidelity, and outcome-free
similarity cannot establish recipient utility. The same donor may help
few-shot prediction, fail OOD screening, or lose its signal during sequential
acquisition. A useful framework must therefore separate hypothesis generation
from validation, remove identity and provenance leakage, challenge donors with
matched false sources, and permit abstention. Moreover, many heuristic
materials OOD splits remain interpolation in representation space
[@Li2025OOD], while recent transductive and chemistry-informed approaches show
that relations or transformations can be more portable than raw features or
model weights [@Segal2025KnownUnknowns; @Yahagi2025DomainTransformation].

Here we develop endpoint-routed knowledge borrowing. Donor and recipient are
directed task roles rather than permanent database labels, and the information
that crosses the boundary is chosen according to experimental distance and
decision endpoint. A 40-edge benchmark first establishes that generic
donor-feature injection does not repair OOD prediction. We then separate
transferable objects in a controlled OER perturbation series: the complete
recipient system is held out, a donor composition–performance relation is
carried across a declared ligand or metal substitution, and a small number of
recipient anchors corrects local residuals. Two of four derivative systems
show substantial predictive and ranking gains, whereas a third is
ranking-only and the fourth is harmful. Increasing provenance distance then
weakens what remains portable. Across articles, an absolute prediction fails,
whereas a within-article response relation plus one recipient anchor reduces
macro-RMSE by 6.91%. Across databases, a programme-balanced conductivity score
materially improves fixed-temperature candidate ordering in one programme
despite failing its absolute-calibration gate, but an unchanged edge fails a
frozen second-recipient test. These results yield a
knowledge-borrowing map that routes a qualified relation to prediction,
calibration, ranking, or rejection instead of treating adjacency as evidence.
We further test whether representation can make a relation portable to a new
mixture component. A permutation-invariant source relation trained across
electrolyte formulations transfers zero-shot to an external new-salt programme
and separates the contribution of adjacent chemistry from temperature and
concentration alone.

## 2. Methods

### 2.1 Experimental-resource cohort and source-pinned measurement layer

The primary unit of reuse was a reported measurement together with material
identity, experimental context, provenance, and reuse constraints. A resource
entered the analyzed cohort only when its numerical values contributed to the
normalized measurement layer, a directed borrowing task, an external boundary
test, or the compensation artifact analysis. This criterion produced 21
accessible experimental resources. Thirteen were normalized locally, seven
entered as task-specific external resources, and NIST ISODB was streamed for
artifact analysis. Table S1 lists every resource, role, revision, and reuse
constraint.

The 13 normalized resources were stored in a source-pinned SQLite table with
the fields

`dataset · source row · raw material · canonical entity · property · value · unit · conditions · reference · source revision · quality flags`.

Formulas were converted to normalized element fractions, SMILES were
canonicalized with RDKit, and liquid formulations used a separate mixture
identity. Property labels and units remained source-specific unless an explicit
conversion was implemented. The resulting snapshot contains 96,184
measurements, 230 property labels, and 29,516 canonical formula, molecule, or
mixture entities. External resources remained in their frozen task-specific
representations when the common schema would discard experimental state.

### 2.2 Directed borrowing objects and artifact gates

A resource acted as a donor when a prediction, coefficient, ranking, or
neighboring-condition signal derived from its labels was applied to another
task. A recipient supplied the held-out outcome used to score prediction,
screening, or acquisition. The same resource could occupy both roles in
different directed edges. Donor status denoted an attempted supply of
information, not demonstrated benefit.

We did not define a neighbor by disciplinary label alone. A candidate donor
had to share a recipient-available representation—such as composition,
formulation, structure, or experimental condition—and a falsifiable physical
reason that its endpoint could constrain the recipient decision. Neighborhood
was therefore directional and task-specific: two resources could be adjacent
for formulation ranking but not for absolute-property calibration.

Candidate edges were nominated without recipient test outcomes. Eligibility
required a falsifiable physical or experimental relation, a representation
available for recipient candidates, grouped source out-of-fold skill,
candidate-local coverage, and identity and provenance independence. The
transferred object also had to match the decision endpoint. Missing
representation or failed independence excluded an edge. Remaining edges were
challenged by shuffled, physically inappropriate, or architecture-matched
controls.

For a prediction task \(t\), let \(x\) denote target-available features and
\(y_t\) the measured target property. A source model \(f_s\) generated an
out-of-sample donor-derived feature

\[
z_s(x)=f_s(x).
\]

The target-only model was \(g_0(x)\), and the augmented model was
\(g_1[x,z_s(x)]\). Both models used identical target labels, splits,
hyperparameters, and random seeds. Predictions for target-training rows were
cross-fitted. Source models used for target evaluation excluded every target
evaluation identity or provenance group. Directly measured donor values from
an evaluation target were never injected.

The primary prediction effect was the relative held-out RMSE reduction,

\[
\Delta_{s\rightarrow t}=
\frac{\mathrm{RMSE}(g_0)-\mathrm{RMSE}(g_1)}
{\mathrm{RMSE}(g_0)},
\]

where positive values favored borrowing. Relative improvement was always
reported with held-out augmented-model \(R^2\). This absolute-utility check
prevented a modest improvement over a poor baseline from being described as
useful OOD prediction.

When article or laboratory provenance could shift the absolute property scale,
the transferred object was reduced to a response relation. A donor learned
\(\Delta y_s\) as a function of within-provenance feature differences
\(\Delta x\); one or more recipient measurements supplied an absolute anchor,
and only non-anchor recipient outcomes were scored. The same anchors were
provided to an absolute-donor comparator, so the estimand isolated the value of
transferring a relation rather than the value of revealing target labels.

For a new component in a shared mixture state space, the transferred object
was a physics-aware mixture relation. Solvent components were aggregated as
molar-fraction-weighted descriptor means and variances, salts as
molar-fraction-weighted means, and temperature, concentration, inverse
temperature, log concentration, and their interactions were retained
explicitly. This representation was invariant to component order. The source
model was frozen before external-target scoring. Outcome-independent recipient
anchors could fit only a shrinkage calibration correction; they could not
refit the source chemistry relation.

For OOD exploration, donor predictions were converted to within-pool rankings
and retained outside the target surrogate. Multiple qualified donors supplied
separate shortlists or an unweighted rank consensus. This contract preserved
complementary proposals whose property scales were unrelated. Composition
novelty and uniform random sampling were retained as target-only references.
Prediction, fixed screening, and sequential acquisition were treated as
distinct endpoints and were not allowed to validate one another.

The decision framework grouped gates into four families. Validity gates tested
identity, provenance, and split independence. Utility gates required a
prespecified practical effect and positive absolute performance where
applicable. Robustness gates tested grouped resampling, learner sensitivity,
and repeated target-label draws. Specificity gates compared the real donor
with shuffled, wrong-property, or architecture-matched controls. An edge that
failed its endpoint-specific conjunction was labeled null, harmful, or
unresolved rather than replaced by a more favorable donor.

### 2.3 Controlled system holdout, few-shot prediction, and external boundaries

The controlled electrocatalysis perturbation series comprised a 462-catalyst
donor system and four complete 126-catalyst derivative systems from the
SpecGen robotic OER programme [@Zhou2026SpecGen]. All systems used the same
six-slot composition grid, UV–vis–NIR representation, and OER potential at
10 mA cm\(^{-2}\). Derivatives A and B replaced the terephthalic ligand with
2-aminoterephthalic and 1,3,5-benzenetricarboxylic ligands, respectively;
derivative C replaced Mg with Fe, and derivative D replaced Cd with Mn. The
complete derivative system, rather than a random row subset, was the OOD unit.

The initially frozen analysis selected a spectral donor model by donor-only
five-fold cross-validation and compared static and five-anchor transfer with
target-only interpolation, composition-only transfer, and 500 refitted
shuffled-source models. The spectral primary retained ranking utility only in
derivative B. The prespecified composition-only control was then promoted in
an explicitly post-primary amendment after its A, B and D correlations were
seen. That analysis used a 500-tree donor model on the six declared
composition slots. With five recipient labels, the borrowed prediction was the
static donor estimate plus a three-nearest-neighbour interpolation of donor
residuals; the matched target-only model used the same anchors and distances
without the donor estimate. Candidate identities were bootstrapped and all
four zero-label tests were Holm-corrected against 500 source-label
permutations. A positive predictive edge required positive donor skill,
zero-label \(\rho>0.30\), corrected \(p<0.05\), at least 5% five-label RMSE
reduction, at least 0.10 rank gain, positive intervals for both gains, and
borrowed \(\rho>0.40\).

As a temporal secondary check, the frozen donor was applied without refitting
to the 20 subsequently synthesized candidates in each derivative system.
Supplementary Tables 6–9 were cross-checked against the released figure source
data, and rank tests used 100,000 target-label permutations with Holm
correction. Because these candidates were selected by the source study's own
SpecGen workflow, this test could corroborate ranking beyond the initial 126
samples but could not establish unbiased search acceleration.

The KIT electrolyte data contained 5,035 temperature-specific conductivity
measurements from 504 experiment identifiers and 109 PC/EC/EMC/LiPF6
formulations [@Rahmanian2023Conductivity]. Replicate experiments were reduced
to the median within formulation and temperature. The 108 formulations complete
across all target and control temperatures remained indivisible in five
balanced outer folds. The target was log10 conductivity at −30 °C with 30 target
labels. The primary donor was −20 °C; 0, 30, and 60 °C were increasing-distance
controls, and permuted −20 °C labels supplied the shuffled donor.

Features comprised relative solvent fractions and the LiPF6-to-solvent mass
ratio. Experiment identifiers, total batch mass, Arrhenius parameters, fitted
conductivity vectors, and electrochemical-impedance outputs were excluded
because they encoded the same temperature series as the target. The designated
source and target models were Random Forest regressors. ExtraTrees and
polynomial Ridge supplied learner sensitivities. Source predictions for
target-training formulations were cross-fitted, and source models excluded
target-test formulations. Uncertainty resampled target-label repetitions,
outer folds, and formulations. The exact models, seeds, learning-curve
interpolation, and operational thresholds are reported in Sections S3–S4.

CALiSol-23 supplied a paper-disjoint boundary test
[@deBlasio2024CALiSol; @deBlasio2023CALiSolData]. The target was fixed at
−40 °C before conductivity modeling because it was the coldest 10 °C-grid slice
represented by at least ten articles. The nearest −30 °C donor was primary;
−20, 0, and 20 °C were distance controls. Five outer folds held out complete
article DOIs. Source models also excluded exact target chemistry identities
reported in other articles. Target-training donor predictions were
leave-one-article-out. The article-hierarchical bootstrap resampled
target-label repetitions, articles, and formulations. CALiSol used the same
practical, absolute-utility, learner, distance, and shuffled-control logic as
KIT, but its outcome was evaluated independently.

After that absolute-transfer result was known, CALiSol was reused for a
separately locked mechanistic reanalysis. This analysis was explicitly
post-outcome-motivated. It tested whether the neighboring-condition response
relation, rather than the absolute donor prediction, could cross articles.
The common scope retained 883 target formulations from 11 articles with at
least eight target formulations each. Each article was held out in turn. A
ridge model learned centered formulation-to-log-conductivity responses from
the remaining −30 °C source articles, with equal total weight per article.
One to three −40 °C target-article outcomes were then revealed as anchors and
excluded from scoring. Primary anchors were selected by an outcome-independent
feature medoid, followed by farthest-point traversal. The primary prediction
was \( \widehat y_t=y_a+\widehat{\Delta f}(x_t-x_a) \). An ordinary absolute
−30 °C ridge model, offset-calibrated with the same anchors, isolated the
effect of changing the transferred object. Anchor-only, 199 within-article
shuffles, a +20 °C wrong-condition relation, ridge-penalty sensitivities and
100 random anchor selections supplied falsifiers and robustness tests.
Article RMSE was the independent-unit metric; the primary portfolio metric was
the unweighted mean across articles.

The physics-aware mixture benchmark was developed after the published
LiAsF6 transfer outcome had been inspected and was therefore designated
retrospective method development
[@Yang2026BambooMixer; @Lai2026BambooMixerExtension]. The source comprised
10,407 experimental conductivity measurements from 22 salt identities. The
external target comprised 1,827 measurements from 176 exact LiAsF6
formulations; LiAsF6 was absent from the source. Every temperature and
concentration row sharing an exact component identity and ratio remained in
the same resampling group.

Random Forest source relations used 400 trees and three fixed seeds. The full
mixture model was compared with a temperature-and-concentration-only model, a
chemistry-permuted source, a source excluding LiPF6, LiPF6 alone, and
size-unmatched LiBOB and LiBF4 controls. The external contrasts used 1,000
target-formulation bootstraps. Few-shot tests selected 1, 3, 5, 10, 20, 50, or
100 exact-formulation anchors by outcome-independent maximin coverage across
100 draws. A shrinkage adapter and target-only Ridge received the same anchors.
Leave-one-salt-out tests retained salts with at least 50 target rows.

Alloy transfer provided two additional boundaries. Ultimate tensile strength
(UTS) and yield strength (YS) were paired within the Borg
multi-principal-element alloy data and the independent BIRDSHOT campaign
[@Attari2025Tabular]. Ordinary least-squares lines were fitted in log10 strength
space, and the Borg coefficient was evaluated unchanged on BIRDSHOT. A separate
borrowing test used cross-fitted Borg UTS predictions as a donor-derived
feature for YS. The independent Matbench target retained its official five
folds [@Dunn2020Matbench; @Dunn2020MatbenchCorrection;
@HackingMaterials2018Steel]. Exact target compositions were excluded from the
Borg donor, and same-row UTS and elongation were forbidden target inputs.

### 2.4 Systematic OOD benchmark and state-matched alloy analysis

A systematic benchmark tested whether one fixed donor-derived feature
procedure repaired OOD prediction across multiple targets. The benchmark
retained eight target tasks across seven experimental programs, five real
donors per target, and one shuffled version of the designated donor. This
produced 40 real edges and eight shuffled controls. The protocol was written
after related component outcomes had been inspected, so it tested a fixed
method envelope rather than providing independent confirmation.

OOD groups were defined without recipient outcomes. Formula-indexed tasks used
standardized elemental fractions and composition-distribution descriptors;
distance was the minimum Euclidean distance to the development partition.
Molecular tasks used one minus maximum Morgan-fingerprint Tanimoto similarity.
Intact evaluation groups were ranked by median distance and divided into
quartiles. Q1 was the nearest region and Q4 the farthest OOD region.

Each donor model excluded all recipient-evaluation identities. Its prediction
was added to a target model trained on grouped target-label subsamples from the
development partition. Ridge regression was primary, with Random Forest and
ExtraTrees sensitivities. One hundred target-label draws were paired across
target-only, real-donor, wrong-source, and shuffled-source fits. The primary
effect was Q4 relative RMSE reduction; OOD specificity was Q4 gain minus Q1
gain. A complete OOD-repair decision additionally required positive augmented
Q4 \(R^2\), learner robustness, matched-control superiority, and
multiplicity-adjusted significance. Full gate definitions are provided in
Section S10.

The generic benchmark collapsed Borg records to composition-level targets and
therefore omitted experimental state. A separately frozen robustness analysis
returned to the raw rows. The target comprised 1,067 positive YS records in 150
unordered elemental systems. The neighboring endpoint comprised 539 positive
UTS records in 93 systems, including 495 paired rows. Target features included
composition, processing route, coarse phase family, test mode, test
temperature, and calculated density. Entire elemental systems, rather than rows
or exact formulas, were indivisible split units.

For each of 30 target-label draws, 60 YS labels were sampled from development
systems. UTS predictions for a target-training fold came from an ExtraTrees
donor that excluded every system in that fold and all evaluation systems. The
predicted log10 UTS was appended to the state-aware target features. Random
Forest and ExtraTrees target models provided 60 model-by-draw runs. A donor
outcome permutation was regenerated inside every fold and used in the identical
feature-concatenation architecture. Measured UTS on paired rows was retained
only as an auxiliary information ceiling. Primary intervals used 100,000
two-way cluster-bootstrap replicates over elemental systems and model-by-draw
runs. This post-selection analysis tested stability on one program, not
independent cross-database replication.

### 2.5 OOD screening and exploration

OBELiX ionic conductivity was evaluated on canonical compositions after
removing train–test duplicates revealed by formula normalization
[@Therrien2026OBELIX]. The resulting target contained 390 official-training and
110 official-test compositions. Target inputs were 118 elemental fractions and
eight composition-distribution descriptors. Frozen donor-derived features came
from thermoelectric ZT, alloy YS, and CO2-reduction H2 Faradaic-efficiency
models. Exact target compositions were absent from every donor.

Fixed screening measured the fraction of the candidate pool ranked before the
first true top-5% hit. Sixty repeated 30-label target subsets were evaluated
with Ridge as the primary target model and tree ensembles as sensitivities.
Sequential acquisition used the same initial labels and official-test pool.
An ExtraTrees model was refitted after each acquisition and scored candidates
by ensemble mean plus one ensemble standard deviation. Target-only,
donor-augmented, shuffled-donor, and uniform-random policies were compared over
100 paired campaigns with a 40-acquisition budget. Fixed screening and
sequential acquisition had separate practical and robustness gates.

The Caltech experimental Li-ion-conductivity database supplied a cross-database
OOD-exploration target. Canonical identity and article grouping produced 339
development entities, 144 article-disjoint candidates, and a 58-candidate
hard-OOD subset. Every donor excluded exact target compositions and target
DOIs. Prespecified donors were OBELiX same-property conductivity and ESTM
transport-adjacent thermoelectric data. Mechanical and catalysis data supplied
wrong-domain controls, and shuffled OBELiX ranks supplied a placebo.

Target-refitted residual policies and target-model-independent donor rankings
were evaluated separately. The adaptive policies required grouped
cross-validation improvement before a donor could receive nonzero weight.
Static donor rankings remained fixed and were scored by cumulative recovery of
the true top-5% region through 20 acquisitions. Complementarity was evaluated
by alternating between the two donor shortlists and by unweighted rank
consensus. These combined portfolios were defined after Caltech outcome
inspection and were treated as method-development evidence rather than
independent validation.

The cross-database ordinal-transfer analysis was explicitly post-outcome
method development. Three conductivity sources were fitted separately:
10,012 BambooMixer measurements after removing the complete
LiPF6/ethylene-carbonate/ethyl-methyl-carbonate target family, 410 CALiSol
measurements from three source articles, and 1,089
formulation–temperature aggregates from the controlled KIT programme. Source
models used 400-tree Random Forests and three fixed seeds. Their
log-conductivity predictions were averaged with equal programme weight rather
than pooling records. A strict composition–temperature–outcome audit found 71
near-identical records between BambooMixer and CALiSol but zero between any
source and the 180-row, 36-formulation SolventSeg recipient
[@Wang2022SolventSegregation].

The primary endpoint was fixed at 25 °C so that repeated temperatures of one
formulation were not treated as independent evidence. Three, five, or ten
recipient formulations were selected by outcome-independent maximin coverage
over 100 draws and excluded wholesale from scoring. The source score was
compared with state-only and chemistry-permuted donors and with 13
recipient-only linear, radial-basis kernel, nearest-neighbour, and tree
configurations fitted to the same anchors. A non-deployable per-draw oracle
formed an adversarial recipient-only ceiling. Primary utility was Spearman
candidate-order correlation; top-quartile precision and normalized shortlist
regret were supporting decision metrics. Rank tests used 10,000 target-label
permutations with Holm correction across seven declared source arms.
Formulation-grouped uncertainty used 5,000 resamples. Absolute prediction and
ordinal ranking had separate conjunction gates.

We then froze the unchanged donor model, chemistry conversion, three-anchor
budget, metrics, practical thresholds, and inference before downloading
row-level outcomes from a second recipient. This target was the November 2023
experimental phase of the Fast INtention-Agnostic LEarning Server (FINALES)
LiPF6/ethylene-carbonate/ethyl-methyl-carbonate campaign
[@Vogler2024FINALES; @Steensen2024FINALESData]. The first three chronologically
distinct formulations were recipient anchors; the remaining 16 formulations
formed the primary evaluation pool. Candidate order was scored by pairwise
concordance among measurements within 1 °C. The frozen donor was compared with
the strongest of ExtraTrees, histogram gradient boosting, and linear
recipient-only models fitted to the same three anchors. Uncertainty used
20,000 formulation bootstraps and 2,000 donor-label permutations. No donor,
anchor, split, metric, or threshold was changed after outcome access.

### 2.6 Tests of pooled and transported regularities

The analysis distinguished a strong source-domain relation from a portable
law. The Borg UTS–YS coefficient-transport test used 5,000
composition-cluster bootstrap replicates and audited exact composition overlap.
Thermoelectric Arrhenius series were separated by reference and required
prespecified fit-quality and family-size rules. Meyer–Neldel associations were
evaluated globally and within chemical families with robust inference and
threshold sensitivity.

For adsorption, the hash-pinned NIST ISODB archive was streamed without
extraction [@Siderius2019ISODB]. Eligible pure-component isotherms contained at
least five finite positive points and a monotone pressure–uptake relation. A
system required at least three temperatures and a common uptake interval. One
geometric-midpoint loading was selected per system, pressure was interpolated
at that loading, and ln(p/bar) was fitted against \(1/T\). This produced one
isosteric heat–intercept pair per DOI–adsorbent–adsorbate–unit system. The Krug
null independently permuted fitted heat and intercept values onto observed
temperature grids. DOI-cluster bootstrap and wild-cluster tests evaluated
pooled and adsorbate-family structure.

### 2.7 Outcome-unseen boundary tests

Two targets were frozen before their outcomes were inspected during target
construction, donor fitting, policy ordering, or hypothesis writing.
Starrydata2 tested the reverse transport direction, using ionic-conductivity
donors to predict thermoelectric ZT. Outcome-free identity, sample lineage, DOI,
and composition-cluster rules created 4,427 development, 1,675 validation, and
1,301 evaluation entities. The primary cell used 30 target labels, ExtraTrees,
composition features, and the farthest OOD quartile. Same-domain, adjacent,
wrong-domain, shuffled, source-size, source-skill, and target-coverage controls
were retained.

The second target used the four composition plates in the deposited TRI OER
benchmark. Each plate was held out in turn. Donors represented the same acid
OER reaction, adjacent ORR and OCx electrocatalysis, wrong-domain mechanics and
ionic transport, and within-source shuffles. Three learner families, two
representations, and label budgets of 15, 30, and 60 were evaluated. Prediction
inference resampled target-label repetitions and intact provenance or
composition groups. Named contrasts were Holm-adjusted within target, and TRI
effects were synthesized across the four held-out plates by random effects.
These tests evaluated the fixed strategy's capacity to admit, abstain, or reject
an edge. They were not prospective experiments because the target values
already existed.

### 2.8 Statistical implementation and reproducibility

All claim-bearing designs, compact outputs, source revisions, software
versions, figure source data, and file hashes are recorded in the release
manifest. Random seeds were fixed before formal runs. Unless otherwise stated,
intervals are two-sided 95% intervals and permutation tests are one-sided in
the prespecified beneficial direction.

Multiplicity was controlled within named decision families rather than across
every analysis in the paper. Sampling units followed the data-generating
design. Composition-level analyses resampled compositions, KIT resampled
target subsets, folds, and formulations, CALiSol resampled articles,
Starrydata resampled target-label repetitions and evaluation blocks, TRI
retained the four held-out plates, and ISODB clustered by DOI. Sequential
policy intervals describe paired campaign uncertainty on a fixed candidate
pool. Repeated seeds were not treated as independent target datasets.

## 3. Results and discussion

### 3.1 Experimental integration defines valid borrowing edges

The normalized evidence layer contributed 96,184 source-pinned measurements
across molecular properties, transport, alloy mechanics, catalysis, and
polymers. The broader task-specific layer added only resources used in a
reported transfer, boundary, or artifact test. These counts define audit
coverage; they are not used as evidence that the framework generalizes merely
because many databases were catalogued.

Integration mattered scientifically because it defined the unit that had to
remain independent. Formula normalization removed two official electrolyte
test compositions that duplicated training compositions despite different raw
strings. Mixture identities retained salt, concentration unit, solvent-ratio
convention, and solvent components, while article and experimental-programme
identifiers defined provenance groups. Donor and recipient roles were then
assigned per directed task, and shuffled or wrong-property resources were
registered as falsifiers rather than counted as independent transfer
replications.

### 3.2 Pooled regularities do not imply portable laws

A strong source-domain relation failed its simplest transport test. Borg
contained 495 paired UTS–YS records from 208 canonical compositions, with a
log–log \(R^2=0.790\). The independent BIRDSHOT campaign contained 171 paired
records from 151 compositions and shared no exact composition with Borg. Its
in-domain relation was weaker (\(R^2=0.067\)), and applying the Borg coefficient
unchanged produced \(R^2=-3.006\) (95% composition-cluster interval,
−4.154 to −2.185; Fig. 2a). The median UTS/YS ratio changed from 1.36 to
2.72. A high in-domain association therefore did not define a portable
coefficient.

The compensation tests reached the same conclusion through different failure
modes. Across 112 reference-separated thermoelectric Arrhenius series, the
pooled Meyer–Neldel association was weak (\(R^2=0.107\)) and inclusion-rule
sensitive. Adsorption produced a stronger pooled heat–intercept relation
(\(R^2=0.637\) across 1,103 systems), but DOI-cluster tests retained
adsorbate-family structure (\(p=0.0002\)). The main inference is not that
scientific regularities are absent. It is that association, artifact
resistance, family conditioning, and transport are different claims. The
borrowing framework therefore tests a relation at the recipient endpoint
instead of treating pooled fit as knowledge.

### 3.3 A controlled derivative series isolates a transferable composition relation

The derivative OER systems supplied the clearest controlled test of the
central claim because the endpoint and experimental programme were fixed while
one ligand or metal centre was changed. The initially frozen spectral model
had strong donor skill (\(R^2=0.711\), Spearman \(\rho=0.857\)) but transferred
selectively. Only derivative B passed the zero-label ranking gate
(\(\rho=0.464\), Holm-adjusted \(p=0.008\)); adding five recipient labels
improved rank over the target-only model but worsened RMSE. Full spectra were
therefore not automatically the most portable representation.

The prespecified composition-only control revealed a stronger low-dimensional
relation and motivated the disclosed post-primary analysis (Fig. 3). Donor
out-of-fold \(R^2\) was 0.774 and \(\rho=0.887\). Without recipient labels, the
donor ranked derivatives A, B and D with \(\rho=0.552\), 0.610 and 0.748,
respectively; all three exceeded 500 refitted shuffled-source models after
Holm correction (\(p=0.008\)). Derivative C remained below the practical rank
gate (\(\rho=0.259\)) and retrieved none of its true best 10%.

Five target labels converted the donor relation into useful numerical
prediction in two of four systems. For derivative B, pooled RMSE fell by 16.3%
relative to the matched target-only model (candidate-bootstrap 95% interval,
9.2–22.9%), while pooled Spearman gain was 0.347 (0.260–0.426). For derivative
D, RMSE fell by 26.1% (20.0–31.7%) and Spearman gain was 0.407
(0.352–0.459). Median borrowed rank correlations across the 200 five-label
draws were 0.593 and 0.764. Derivative A remained ranking-only: rank improved,
but its 3.2% pooled RMSE gain had an interval crossing zero
(−1.8 to 9.7%). Derivative C was correctly rejected because borrowing increased
RMSE by 10.4% (3.4–17.2% worse), despite a modest rank increase. The result is
not “composition transfer works”; it is that a declared homologous
composition–performance relation can transfer across some controlled
perturbations and fails under another.

The subsequently synthesized 20-candidate sets supported the ranking
interpretation beyond the original 126-point grids. Unchanged donor rankings
had \(\rho=0.475\), 0.531 and 0.616 in derivatives B, C and D
(Holm-adjusted \(p=0.035\), 0.026 and 0.010), whereas derivative A did not pass
(\(\rho=0.359\), \(p=0.060\)). These restricted candidate sets had been
selected by SpecGen, so the result is temporal ranking corroboration, not an
unbiased discovery trial. In particular, the recovered C ordering did not
repair its failed full-grid RMSE or demonstrate search acceleration. Together,
the four perturbations show why routing must judge prediction and ranking
separately.

### 3.4 Transferable objects contract as provenance distance increases

We organized the positive tests by increasing provenance distance rather than
by property label. The working hypothesis was that less absolute information
would remain portable as donor and recipient moved from the same experimental
campaign, to different articles, and finally to different databases. Physical
adjacency nominated each edge, but did not determine which object, if any,
could cross it.

The shortest-distance test used different temperatures in the same controlled
electrolyte campaign. At 30 target labels, the −20→−30 °C
donor-derived feature reduced held-out RMSE by 15.02% (95% CI,
8.61–21.10%; \(p=0.001\); Fig. 4a). Pooled \(R^2\) increased from 0.739 to
0.811. All five formulation folds improved, and Random Forest, ExtraTrees, and
polynomial Ridge produced gains of 15.02%, 19.63%, and 34.47%, respectively.
The donor model had out-of-fold \(R^2=0.859\). The augmented error corresponded
to a retrospective target-equivalent sample count of 47.9, although the
uncertainty on the precise label-saving fraction crossed the operational 30%
threshold.

Distance and shuffle controls localized the effect. Relative RMSE reductions
were 15.02%, 5.01%, 0.95%, and −0.76% for source-target temperature separations
of 10, 30, 60, and 90 °C. A shuffled adjacent donor was harmful
(−2.96%; 95% CI, −4.32 to −1.44%). These controls rejected a generic advantage
from adding one model-derived feature. They supported a local ordering for this
electrolyte campaign without establishing temperature distance as a universal
metric.

The same strategy did not automatically cross experimental articles. In
CALiSol, the paper-disjoint −30→−40 °C edge reduced RMSE by only 1.61%, with an
article-hierarchical interval of −2.14 to 4.21% (Fig. 4b). The augmented
\(R^2\) remained negative (−0.014), two outer folds were harmful, and the
0 °C control was numerically stronger. The shuffled effect was 0.83% with an
interval crossing zero. Matbench supplied a second boundary: Borg UTS
predictions changed official-fold YS RMSE by −1.23% (−15.88 to 2.48%;
\(p=0.794\)). The contrast with KIT was decisive. A qualified adjacent
condition can materially improve few-shot prediction within one controlled
campaign, but nominal proximity does not remove between-article or
between-program heterogeneity.

Changing the transferred object partly repaired this boundary. With one
outcome-independent target-article anchor, the within-article −30 °C response
relation reduced macro-RMSE from 0.4901 to 0.4562 log10(mS cm\(^{-1}\)), a
6.91% gain over the same-anchor absolute donor (article-bootstrap interval,
0.88–14.00%; exact one-sided article sign-flip \(p=0.035\); 8 of 11 articles
improved). Pooled non-anchor \(R^2\) was 0.234. The contrast model also reduced
macro-RMSE by 29.84% relative to assigning the anchor value to every candidate.
Its gain exceeded the median within-article shuffled contrast by 41.97
percentage points (\(p=0.005\)), while a +20 °C wrong-condition contrast was
harmful and had negative \(R^2\). The advantage was 6.4–6.9% across ridge
penalties and positive in all 100 random one-anchor repetitions. Three articles
remained mildly harmful, and deterministic two- and three-anchor scopes did
not retain positive pooled \(R^2\). The result therefore supports one
few-shot, provenance-anchored neighboring-condition contract; it does not make
cross-article transfer universal. Because the method was formulated after the
original CALiSol null was inspected, independent replication is still
required.

Representation-aware transfer opened a distinct route across component
identity. The frozen 22-salt mixture relation predicted the external LiAsF6
programme without LiAsF6 target labels at log-scale \(R^2=0.732\), raw-scale
\(R^2=0.629\), log-RMSE 0.336, and Spearman \(\rho=0.871\). Relative to
temperature and concentration alone, formulation-grouped bootstrap estimates
gave 28.64% lower log-RMSE (95% CI, 24.03–33.52%), a rank gain of 0.160
(0.132–0.188), and a raw-\(R^2\) gain of 0.230 (0.182–0.279). Relative to a
chemistry-permuted source, log-RMSE fell by 27.16% (22.78–31.90%) and
rank correlation increased by 0.134 (0.108–0.162). The portable signal
therefore contained formulation chemistry rather than only the shared
temperature--concentration response surface.

Source ablations separated local adjacency from data volume. Removing LiPF6,
the closest abundant fluorinated lithium-salt neighbour, worsened log-RMSE by
16.38% (12.66–20.24%) and ranking by 0.041 (0.023–0.062). Yet the complete
source also outperformed LiPF6 alone by 28.76% (22.94–33.88%) in log-RMSE and
0.055 (0.037–0.075) in ranking. Adjacent salt chemistry supplied specific
information, while the broader source portfolio improved solvent and state
coverage. In leave-one-salt-out tests, the full relation beat the state-only
model on both error and ranking for 7 of 9 eligible salts. LiBF4 and LiTDI
retained positive ranking gains but failed the error gate, so they were routed
away from calibrated prediction.

Five recipient anchors did not create the external signal. The frozen relation
already achieved log-RMSE 0.331 and raw \(R^2=0.631\), whereas a target-only
Ridge fitted to the same five anchors had log-RMSE 0.766 and
\(R^2=-0.376\). Shrinkage calibration improved raw \(R^2\) to 0.653 while
leaving rank essentially unchanged. Thus the learned relation transferred
before target calibration; the few labels mainly restored absolute scale.
Because both the external target outcomes and the published transfer result
were known before this benchmark was designed, the result is strong
method-development evidence, not independent confirmation.

### 3.5 Generic donor injection fails; state matching is a bounded mechanism test

The systematic benchmark first tested the stronger hypothesis that generic
donor-derived feature injection repairs OOD prediction. Across eight designated
edges, the strongest effect again involved alloy UTS→YS. It reduced Q4 RMSE by
6.65% (95% CI, 3.53–14.02%) and improved 93% of repetitions. It exceeded wrong
and shuffled controls, remained positive for all three learners, and survived
Holm correction (\(p=0.0008\); Fig. 2c,d). Yet it reduced Q1 error by 7.74%, and its
augmented Q4 \(R^2\) remained −0.666. The effect represented transferable
alloy correlation, not useful OOD prediction.

No designated edge passed the complete OOD-repair gate. The thermoelectric
donor for electrolyte conductivity produced a small positive direction
(0.98%; −3.14 to 3.70%), but its interval, multiplicity, and absolute-utility
gates failed. The reverse solubility–hydration edge was positive but negligible
(0.084%). Treating the seven programs as independent units gave a mean
designated-edge Q4 gain of 0.92% (−0.35 to 2.92%). Generic donor-feature
injection therefore failed as a cross-domain OOD strategy within the tested
representation and learner envelope.

The alloy failure exposed a correctable information mismatch. The generic
benchmark had collapsed raw records to composition-level targets, discarding
processing, phase, test mode, temperature, and density. Restoring these
state-aware features improved Q4 RMSE by 8.25% relative to a composition-only
target model. We then cross-fitted the UTS donor by entire elemental system and
appended its prediction only after the leakage audit.

Under this state-matched contract, predicted UTS reduced Q4 RMSE by a further
9.21% relative to the state-aware target-only model (two-way
cluster-bootstrap 95% CI, 4.43–14.37%). Fifty-five of 60
model-by-draw runs improved. Pooled augmented Q4 \(R^2\) was 0.103, compared with a
negative state-aware target-only baseline. The architecture-matched shuffled donor was null
(−0.26%; −1.81 to 1.01%), and the real-minus-shuffled contrast was 9.47
percentage points (4.80–14.34%). The gain therefore depended on transferable
UTS structure rather than an arbitrary extra covariate.

The corresponding Q1 gain was 7.21% (3.05–11.52%). Q4-minus-Q1 was 2.00
percentage points, but its interval crossed zero (−4.66 to 8.62%).
The evidence demonstrates stable benefit within the chemically farthest region,
not statistically preferential Q4 transfer. The Q4 \(R^2\) bootstrap interval
also crossed zero (−0.151 to 0.291), so the positive point estimate does not
imply uniform calibration across held systems. Directly measured UTS provided a
larger auxiliary ceiling, reducing Q4 RMSE by 47.70% and producing
\(R^2=0.679\). The learned donor captured only part of the neighboring
experimental information that was available.

A later provenance-specificity analysis limited the status of this alloy
result. Each model draw contained 14 Q4 elemental systems (56 distinct systems
across draws), and no primary contrast survived Holm correction after adding
strict source-size and same-property controls. We therefore retain the alloy
analysis as a mechanism-development example showing why experimental state
matters, not as the paper's independent proof of cross-database transfer.

### 3.6 Cross-database ordinal transfer is useful on selected programmes

The longest-distance positive test asked whether calibration could be
discarded while useful candidate order was retained. Three separately fitted
conductivity sources were combined with equal programme weight and applied
unchanged to the 36-formulation SolventSeg programme
[@Wang2022SolventSegregation]. No source record matched a SolventSeg record
under the frozen composition, temperature, and outcome fingerprint. At 25 °C,
the source portfolio achieved Spearman \(\rho=0.918\), top-quartile precision
of 1.000, and zero normalized regret.

Across 100 outcome-independent selections of five labelled recipient
formulations, the unchanged source score retained mean \(\rho=0.910\),
precision 0.933, and regret 0.00047 on the remaining formulations. The
strongest of 13 recipient-only configurations was radial-basis kernel ridge
regression, with mean \(\rho=0.537\), precision 0.490, and regret 0.0393. The
source advantage was \(\Delta\rho=0.374\) (95% anchor-coverage interval,
0.213–0.562). Even an undeployable oracle that selected the best
recipient-only model separately after each held-out draw remained lower:
source-minus-oracle \(\Delta\rho=0.300\) (0.183–0.540). The zero-label source
ordering was non-random under 10,000 target-label permutations
(Holm-adjusted one-sided \(p=0.00070\)).

Database interaction added a smaller but reproducible benefit. The
equal-programme log-prediction portfolio exceeded the broad single
BambooMixer donor by \(\Delta\rho=0.0236\) across five-anchor draws
(0.0069–0.0397), with higher top-quartile precision (0.933 versus 0.826).
However, the portfolio worsened all-temperature log-RMSE by 18.0% relative to
the state-only source (95% formulation-bootstrap interval, −44.0% to 21.1%
gain), and its five-anchor calibration interval crossed zero. The complete
gate therefore routed this edge to ranking, not numerical prediction. The
supported claim is improved retrospective shortlist ordering, not calibrated
conductivity or guaranteed discovery of the optimum.

The frozen second-recipient test prevented this result from becoming an
electrolyte-wide claim. In the November 2023 FINALES experimental campaign,
the unchanged donor ranking achieved pairwise concordance of 0.694 across 98
temperature-matched formulation pairs. The strongest recipient-only model,
fitted to the same three chronological anchors, achieved 0.783 across 92
pairs. The donor advantage was therefore −0.089 (20,000-bootstrap 95% CI,
−0.293–0.096; 2,000-permutation \(p=0.131\)). Top-quartile precision tied at
0.50, while donor regret was worse (0.563 versus 0.180). Chemistry and named
endpoint were matched, but programme state, sampling policy, and measurement
provenance were not. The unchanged edge was rejected rather than retuned. A
later post-outcome application of the three-source portfolio was also inferior
to the target linear model in the complete 16-candidate multitask evaluation
(\(\rho=0.168\) versus 0.759), although several seven-candidate subsets were
positive. Those small subsets were not used to rescue the complete edge.

The predictive and exploration endpoints diverged in OBELiX. Across 60
30-label repeats, adding the thermoelectric ZT donor reduced the mean fraction
of the official-test pool screened before the first true top-5% hit from 12.08%
to 9.98%. The 2.09-percentage-point reduction had a 95% interval of
0.94–3.45 and Holm-adjusted \(p=0.0003\). However, the 17.3% relative reduction
failed the prespecified 25% effect and 80% repeat-consistency gates. The result
was a directional fixed-screening signal rather than qualified OOD repair.

Sequential refitting did not preserve that signal. Target-only and
thermoelectric-augmented UCB required means of 24.34 and 24.09 acquisitions to
reach the first true top-5% hit. The paired saving was 0.25 experiments
(−1.30 to 1.82; \(p=0.389\)), and only 28% of campaigns improved.
Uniform random acquisition required 15.50 acquisitions, close to
its exact censoring-adjusted expectation of 15.30, and outperformed both UCB
policies. This result established a failure of the tested composition-based,
tree-ensemble UCB policies. It did not establish random acquisition as
generally optimal. Average prediction, fixed OOD screening, and iterative
acquisition were distinct decision problems.

The Caltech target supplied limited corroboration that an ordinal score can
survive when target refitting destroys it. In the complete 144-candidate pool,
same-property conductivity and transport-adjacent thermoelectric rankings had
AUC20 values of 33 and 45, respectively, but neither survived four-test Holm
correction against the 100-seed shuffled-source distribution. In the
58-candidate hard-OOD pool, the corresponding values were 38 and 51; only the
transport-adjacent ranking survived correction (adjusted \(p=0.0396\)).
Target-refitted residual policies failed their practical and robustness gates.
The post-outcome portfolio improved AUC20 without improving recall over the
best single donor and is retained as allocation-method development, not as
evidence for donor complementarity. Together with SolventSeg and FINALES,
these results support preserving a qualified donor ordering when the endpoint
is screening, while requiring programme-specific validation before use.

### 3.7 Outcome-unseen tests define abstention and the operational strategy

Outcome-unseen targets prevented the positive cases from defining selectivity
after the fact. In the primary Starrydata reverse-transport cell, the ionic
donor consensus reduced far-OOD RMSE by 0.88% (0.02–1.77%), but Holm adjustment
gave \(p=0.071\). The contrast with the best matched control crossed zero, and
the augmented \(R^2\) was −0.485. Five of six learner–representation cells were
directionally positive, yet the multiplicity, source-specificity, and
absolute-utility gates failed. The edge was therefore retained as directional
but unresolved.

The four-plate TRI OER target rejected the proposed second-family edge. The
random-effects all-neighbor effect was −0.079% (−0.313 to 0.155%), and only one
of four plate effects was positive. All-neighbor borrowing was 1.25% worse than
the best control (−1.75 to −0.75%), and every held-out plate had negative
absolute \(R^2\). Across Starrydata and TRI, the target-level random-effects
mean was 0.30% (−0.62 to 1.22%) with \(I^2=76.7\%\). Neither target passed its
complete prediction gate. These results do not validate a general
cross-database prediction rule. They validate the map's ability to abstain from
an unresolved edge and reject a harmful one.

The combined evidence yields an endpoint- and provenance-matched strategy.
First, represent processing, formulation, phase, temperature, and measurement
state before evaluating a donor. Second, require grouped source skill together
with identity and provenance independence. Third, reduce the transferred
object as provenance distance grows: use a cross-fitted state-conditioned
prediction within a controlled programme, a response relation plus a small
recipient anchor across study-specific scale shifts, or an unchanged ordinal
score when the decision is candidate screening rather than absolute
prediction. For a new component in a shared mixture state space, freeze a
permutation-invariant source relation and restrict target labels to shrinkage
calibration. Fourth, compare each object with a recipient-only baseline and
matched false sources. Finally, abstain when practical utility, absolute
performance, or programme-specific replication fails. This strategy does not
turn adjacency into a universal law. It turns an adjacent resource into a
falsifiable proposal for prediction, calibration, ranking, or rejection.

## 4. Limitations

The positive effects occupy different inferential levels. The derivative OER
series is a complete-system holdout but remains within one robotic programme,
and the composition analysis was promoted only after its planned control was
inspected. Its four perturbations and later candidates are valuable mechanistic
and temporal evidence, not four independent laboratories. The later
20-candidate sets were selected by SpecGen and therefore cannot estimate
unbiased search acceleration. The adjacent-temperature result is a
within-campaign prediction test, the contrast-and-anchor result is post-outcome
method development across articles, and the SolventSeg result is a
retrospective cross-database screening test. None is a prospective laboratory
discovery.

SolventSeg contains only 36 formulations and one chemistry. Its
fixed-temperature rank gain is large and survives 13 matched recipient-only
configurations plus a per-draw oracle envelope, but the candidate partition is
a heuristic composition-based OOD split and its outcomes had been inspected
before this portfolio was designed. FINALES provides a frozen second
recipient rather than positive replication: only 19 primary formulations were
eligible, of which three were anchors.

The CALiSol contrast result is likewise a method-development result. Its design
was locked before contrast predictions were computed, but the method was
motivated by the known +1.61% absolute-transfer boundary. It contains only 11
independent articles in the common scope, uses retrospective anchors, and has
three mildly harmful articles. The article bootstrap and exact sign-flip test
quantify this sample rather than establish a population-wide transfer rate.
A second literature-aggregated or prospectively generated electrolyte
programme must test the unchanged contrast-and-anchor contract.

The new-salt mixture result is also retrospective method development. The
LiAsF6 outcomes and the published transfer claim were available before our
representation, controls, and thresholds were defined. Formulation-grouped
bootstrap inference prevents row-level pseudo-replication, but it does not
convert a public target into prospective confirmation. The same representation
and routing rule must be frozen on a different outcome-sealed salt or newly
measured electrolyte programme.

The model envelope is deliberately limited. Donor-derived features were fitted
from composition and reported experimental state using Ridge and tree
ensembles. Graph models, SOAP or MBTR descriptors, learned chemical embeddings,
calibrated Gaussian-process surrogates, and cost-aware acquisition were not
tested. The donor feature may act as a nonlinear basis or regularizer without
encoding a transferable microscopic mechanism. Feature importance therefore
measures target-model use, not causation.

The remaining cross-database exploration results are retrospective. Only the
transport-adjacent Caltech hard-OOD ranking survives the corrected four-test
Holm family; the same-property donor and complete-pool contrasts do not. Its
combined portfolio was constructed after outcome inspection and did not
improve recall over the best single donor. The Starrydata and TRI tests were
outcome-unseen during design but used already deposited outcomes. No
prospective laboratory campaign tested whether a donor-derived shortlist
accelerates discovery or produces new science.

Finally, experimental-first integration cannot reconstruct unreported
synthesis history, instrument effects, operator choices, or metastable states.
Only 13 of the 21 analyzed resources enter the common SQLite schema, and the
layer is not fully unit-harmonized. Internal design freezes are author-controlled
records rather than external preregistrations. The present map therefore
supports tested edges and endpoint-specific decisions, not a population-wide
probability that any nominated neighbor will transfer.

## 5. Conclusions

Endpoint-routed knowledge borrowing provides an operational way to use
neighboring experiments without assuming that adjacency guarantees transfer.
Generic donor-feature injection repaired none of 40 prespecified OOD edges,
but controlled relation transfer succeeded when the endpoint, composition
slots and experimental perturbation were aligned. In two complete derivative
OER systems, five-label borrowing reduced RMSE by 16.3% and 26.1% while also
improving candidate ranking; a third system was ranking-only and a fourth was
harmful. Across articles, an anchored formulation-response relation improved
macro-RMSE by 6.91% over the matched absolute donor. Across databases, an
invariant mixture relation transferred zero-shot to a new salt with raw
\(R^2=0.629\) and 28.64% lower log-RMSE than state-only prediction. An
equal-programme conductivity score improved five-label fixed-temperature
candidate ordering in SolventSeg from \(\rho=0.537\) for the strongest
recipient-only configuration to 0.910, yet absolute calibration failed and an
unchanged edge failed to beat a three-anchor recipient-only model in the
frozen FINALES replication.

The practical contribution is a routing and rejection rule rather than a
unified model. First identify a supported, endpoint-matched relation rather
than importing a database wholesale. Transfer a calibrated prediction only
when experimental state and provenance are close; use a few recipient anchors
to correct a portable relation when absolute scales shift; freeze a
mixture-invariant response when a new component shares the source state space;
preserve an ordinal score when the decision is shortlist construction; and
reject the edge
when matched controls or programme-specific validation fail. Positive, null,
and harmful edges together form the knowledge-borrowing map. The next decisive
upgrade is a preregistered external catalyst programme that tests the frozen
composition-relation shortlist against a recipient-only policy.

## Data availability

The public catalog, source metadata, normalized-schema definition, resource
revisions, and task-specific provenance records are provided in the repository.
Raw or derived data are redistributed only where source terms permit. External
resources that cannot be redistributed are identified by stable URLs, file
identifiers, commits, and hashes. The independent electrolyte recipients are
available from the SolventSeg archive (doi:10.5281/zenodo.6299956; associated
article doi:10.1016/j.xcrp.2022.101047) and the FINALES Materials Cloud record
doi:10.24435/materialscloud:qt-1s.

## Code availability

All claim-bearing analysis scripts, design records, compact outputs, figure
source data, and portable verification scripts are provided in the repository.
Large row-level prediction tables are reproducible from the pinned inputs and
are not required to verify the reported summary statistics.

## Author contributions

`[Insert CRediT author-contribution statement.]`

## Conflicts of interest

The authors declare no competing interests.

## Acknowledgements

`[Insert funding, institutional, computing, and contributor acknowledgements.]`

## Figure captions

**Figure 1 | Endpoint-routed knowledge borrowing.** **a,** A data-poor
recipient must make decisions in an OOD region where target evidence is
weakest. **b,** Directed donor-to-recipient roles and the provenance ladder
from one campaign to different articles and databases. **c,** The transferred
object contracts with distance: a state-conditioned prediction, an anchored
response relation, an ordinal score, or rejection. **d,** Validity, utility,
robustness, and specificity gates. The experimental-resource cohort appears as
a compact evidence strip rather than as evidence that every resource
transfers.

**Figure 2 | Aggregation and generic donor injection do not establish portable
knowledge.** **a,** A strong source-domain relation and its failed unchanged
transport to a provenance-independent programme. **b,** Artifact and
family-structure checks for pooled compensation relations. **c,** Q4 RMSE
effects for 40 real donor-feature edges across eight targets. **d,** Complete
gate audit: no generic edge repairs the designated OOD task. Matched shuffled
and wrong-property sources distinguish transferred information from the mere
addition of a model-derived covariate.

**Figure 3 | A controlled derivative-system series identifies a portable
composition relation.** **a,** One 462-catalyst OER donor and four complete
126-catalyst ligand or metal perturbations; each complete derivative system is
held out. **b,** Zero-label Spearman correlation. Filled circles and open
squares denote the six-slot composition and 720-feature spectral donors,
respectively; pale violins show 500 refitted composition shuffled-source
models, and the dashed line is the prespecified practical rank gate.
**c,** Five-label pooled RMSE and rank gains over the matched target-only
baseline. Points are pooled effects and lines are candidate-bootstrap 95%
intervals from 500 candidate-identity resamples retaining all predictions from
200 random five-label anchor draws; positive RMSE gain denotes lower error. The
route strip identifies positive B and D edges, ranking-only A, and rejected C.
**d,** Unchanged donor ranking on the subsequently synthesized
20-candidate sets. Labels give Spearman \(\rho\) and Holm-adjusted permutation
\(p\) values from 100,000 target-label permutations. These candidates were
preselected by the source workflow, so panel d is temporal rank corroboration,
not an unbiased discovery trial.

**Figure 4 | The portable object contracts with experimental distance.**
**a,** Within-campaign adjacent-temperature electrolyte prediction and
distance controls. **b,** Failure of absolute cross-article transfer and
recovery by a within-article response relation plus one anchor. **c,**
Cross-database SolventSeg source-versus-recipient rank gain, top-quartile
precision and shortlist regret, including the 13-model recipient stress test
and oracle envelope. **d,** Frozen FINALES second-recipient test, where the
unchanged edge loses to the three-anchor recipient-only baseline.

**Figure 5 | The knowledge-borrowing map routes information or abstains.**
**a,** Decision tree from state and provenance audit to prediction, anchored
relation, independent ranking, or rejection. **b,** Claim-bearing positive,
null, and harmful edges arranged by provenance distance and endpoint.
**c,** Corrected Caltech static-ranking evidence, with the sole four-test Holm
survivor marked. **d,** Outcome-unseen prediction boundaries. **e,** Required
upgrade from retrospective shortlist utility to a preregistered experimental
campaign.
