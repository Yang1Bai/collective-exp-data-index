# Artifact-gated mapping of selective knowledge borrowing across experimental materials domains

**Target journal:** *Digital Discovery*  
**Article type:** Full paper (methods-led)  
**Status:** Author draft after formal verification of the systematic
multi-target OOD benchmark and portable verification of the outcome-unseen
validation programmes, including the V2 architecture-matched state-borrowing
control correction.

## Abstract

Materials models are least reliable in data-sparse and out-of-distribution (OOD)
regions, where target-domain evidence is weakest. Neighboring experiments may
supply missing knowledge, but indiscriminate aggregation can create false
regularities and negative transfer. We analyse 20 accessible experimental data
resources: 13 normalized into a source-pinned layer of 96,184 measurements, six
frozen external or temporal programmes, and one streamed artifact-analysis
source. We introduce artifact-gated neighborhood borrowing, which separates
prediction, screening, and acquisition and requires source skill, leakage
controls, practical effect, falsifiers, and positive absolute utility. An
adjacent KIT condition reduced n=30 target RMSE by 15.02% (95% CI,
8.61–21.10%) and increased R² from 0.739 to 0.811. By contrast, a systematic
benchmark of 40 real donor–recipient edges across eight targets found that
generic donor-feature injection repaired none of the designated OOD tasks.
Restoring the planned experimental state and cross-fitting the donor by entire
elemental system converted the strongest alloy edge into a usable
post-selection robustness result: at n=60, predicted tensile strength reduced
yield-strength Q4 RMSE by 9.21% (two-way cluster-bootstrap 95% CI,
4.43–14.37%), produced pooled Q4 R²=0.103, and beat an architecture-matched
shuffled donor by 9.47 percentage points [4.80,14.34]. The Q4-minus-Q1 contrast was not significant,
so this establishes persistence of benefit in the hardest OOD region rather
than an OOD-exclusive effect. Independent neighboring rankings also recovered
complementary high-value regions in a retrospective Caltech pool, whereas
target-refitted corrections and thermoelectric-informed UCB did not; two
outcome-unseen programmes failed their complete gates. Knowledge-borrowing
utility is sparse, directed and endpoint-specific rather than a
general transfer law. The resulting map identifies when neighboring knowledge
supports prediction or exploration, and when abstention is required.

## 1. Introduction

Artificial intelligence increasingly guides scientific prediction and candidate
prioritization, but scientific progress ultimately depends on extending
knowledge beyond explored regimes. This tension is especially acute in
experimental science, where measurements are costly and sparse. Models are
therefore asked to make out-of-distribution (OOD) predictions precisely where
observations, mechanistic guidance, and calibrated uncertainty are weakest.
Even large language models, despite synthesizing vast bodies of prior knowledge,
remain most reliable within patterns represented in existing evidence and
cannot substitute for missing experiments. Neighboring experimental domains may
nevertheless encode partial knowledge of shared compositional, transport,
structural, or processing factors. The central question is whether such
knowledge can reduce target-domain scarcity without importing spurious
relations or negative transfer.

Experimental data are not interchangeable property labels. Each measurement is
embedded in material identity, formulation or processing, measurement
conditions, provenance, and reuse constraints, although these fields are often
incomplete. This context makes distributed experimental records a partial
scientific memory rather than a smaller analogue of computed training data
[@Draxl2022FAIR; @Akhound2026ExperimentalMemory].
Treating such records as context-free labels risks the data-only illusion:
models can appear persuasive while remaining detached from synthesis and
measurement reality [@Smit2026DataOnly]. Data infrastructures have improved
discovery, exchange, and metadata standardization
[@Blaiszik2016MDF; @Andersen2021OPTIMADE; @MedinaSmith2021Vocabulary], but
harmonization alone cannot establish which signals are scientifically
transportable. When heterogeneous observations are pooled, apparent laws may
arise from chemical-family structure, restricted experimental ranges, or
coupled parameter estimation, as compensation relations illustrate
[@Krug1976Compensation; @CornishBowden2002Phantom; @Bond2000Compensation;
@Mianowski2017Adsorption]. Conversely, a larger aggregate can remain redundant
for OOD candidates or reduce predictive performance
[@Li2023Redundancy; @Li2025OOD; @Ottomano2024Aggregation]. Neither a high pooled
correlation nor nominal domain proximity therefore proves that knowledge is
transferable.

Transfer learning, task maps, and multi-information-source optimization show
that external information can improve a scarce target
[@Yamada2019Shotgun; @Jha2019DeepTransfer; @Gupta2021CrossProperty;
@Chang2022MixtureExperts; @Zamir2018Taskonomy; @Kandasamy2017Multifidelity].
Literature mining likewise shows that relationships latent in existing
scientific knowledge can precede their explicit recognition
[@Tshitoyan2019LatentKnowledge; @Marwitz2026ResearchDirections]. For experimental
knowledge borrowing, however, these advances leave a critical gap. An
experimental neighbor is not automatically a calibrated fidelity, and
outcome-free similarity can nominate a source but cannot establish its utility
for a recipient. The same donor may improve few-shot prediction yet fail fixed
OOD screening or sequential acquisition; better average fit does not imply
faster discovery. A rigorous strategy must therefore separate hypothesis
generation from validation, remove identity and provenance leakage, challenge
candidate donors with shuffled and physically inappropriate controls, and
permit abstention. What is missing is a falsifiable experimental procedure that
can qualify, combine, reject, or retire each directed borrowing edge.

Here we introduce an experimental-first, selective neighborhood-borrowing
strategy across 20 analysed experimental resources. Roles are assigned per
directed task rather than permanently to databases: a candidate donor supplies
a prediction, coefficient, fixed ranking, or neighboring-condition signal,
whereas a recipient supplies the held-out outcome used to score prediction,
screening, or acquisition utility. Candidate edges are nominated from
prespecified physical or experimental relations before recipient outcomes are
examined, then audited for representation compatibility, source skill,
candidate-local applicability, endpoint match, and identity or provenance
overlap. Cross-fitted donor predictions act as soft features for few-shot
prediction, while independent donor rankings remain separate for OOD
exploration so that complementary proposals are not forced through a weak target
surrogate. The evaluation treats pooled regularity, coefficient transport,
prediction, fixed screening, and sequential acquisition as distinct evidence
layers and includes paper-disjoint, outcome-unseen, and protected temporal
programmes. Across 97 evaluated source-target edges spanning 20 target tasks and
13 programme clusters, the resulting artifact-gated knowledge-borrowing map
records positive, null, harmful, and unresolved outcomes. In the prespecified
KIT −20→−30 °C edge at n=30, a qualified adjacent donor reduced held-out RMSE by
15.02% (95% CI, 8.61–21.10%; p=0.001) and increased R² from 0.739 to 0.811,
whereas more distant and shuffled sources diminished or reversed the benefit. A
systematic eight-target benchmark then tested whether the same soft-feature
procedure repaired outcome-free OOD quartiles. The strongest designated edge
improved OOD RMSE by 6.65% [3.53,14.02%], but no edge passed the complete
OOD-repair gate because gains were not OOD-specific and absolute OOD R² remained
non-positive. A post-selection mechanism test then restored the experimental
state omitted by the unified schema and generated UTS donor features by
elemental-system cross-fitting. At n=60, this state-matched procedure reduced
the alloy Q4 RMSE by 9.21% [4.43,14.37%], achieved pooled Q4 R²=0.103, and beat
an architecture-matched shuffled donor by 9.47 percentage points
[4.80,14.34]. By contrast, preserving independent neighboring rankings
recovered complementary high-value regions in a retrospective Caltech pool,
while target-refitted corrections and UCB produced no adaptive gain. The
resulting distinction is constructive: use qualified soft priors for local
few-shot prediction, match experimental state before OOD transfer, preserve
donor rankings or portfolios for OOD exploration, and abstain when neither
transfer object passes its endpoint-specific gate.

## 2. Methods

### 2.1 Analysed experimental-resource cohort

The study was designed as experimental-first: its primary reusable unit is a
reported measurement together with material identity, experimental context,
provenance, and reuse constraints, rather than an abstract composition–property
pair. A resource entered the analysed cohort only if its numerical values were
used in at least one locked analysis: the normalized measurement layer, a
directed source or target task, a frozen external or temporal validation, or the
compensation-artifact gate. This criterion produced 20 accessible experimental
resources. Thirteen were normalized locally, six entered as frozen external or
temporal programmes, and NIST ISODB was streamed for artifact analysis.

Nineteen resources entered directed knowledge borrowing. Fifteen acted as
candidate donors whose fitted prediction, coefficient, ranking, or adjacent-
condition signal was transferred; 16 acted as recipients whose outcome was
predicted, screened, or explored. Twelve resources occurred in both roles, three were
donor-only, and four were recipient-only. NIST ISODB was used only for the
artifact battery. Figure 1a and Table S1 name every resource and role. Access
and reuse terms were recorded separately because numerical accessibility does
not imply permission to redistribute a derived database.

### 2.2 Source-pinned local measurement layer

Thirteen resources were normalized into a local SQLite measurement table; NIST
ISODB was registered as an additional streamed analysis-only source. Six
external or temporal resources were kept in their frozen task-specific
representations rather than forced into the common schema. Git-backed data were
fixed to commits, while remote files were fixed to file identifiers and SHA-256
hashes. The long-form schema stores

`dataset · source row · raw material · canonical entity · property · value · unit · conditions · reference · source revision · quality flags`.

Formulas were parsed into normalized element fractions, SMILES were
canonicalized with RDKit, and named liquid formulations used a separate
mixture identity rather than a fictitious elemental formula. Property labels
and units remained source-level unless an explicit conversion was implemented.
The resulting snapshot contains 96,184 measurements, 230 property labels, and
29,516 canonical formula, molecule, or mixture entities. Two measurements have
unresolved canonical identities and are flagged. The database is a loss-aware
integration layer, not a universal scientific ontology.

CALiSol required an additional mixture namespace because concentration units
and solvent ratios were reported by mass, volume, or mole. Salt identity,
concentration unit, ratio convention, and solvent components were retained in
the material key. One raw digitization point had a negative salt concentration;
it remains in the native raw table but was excluded from normalized
measurements. NIST ISODB was streamed directly from a hash-pinned archive
because its adsorbent identifiers do not fit the formula/SMILES/mixture schema.

### 2.3 Directed knowledge borrowing for prediction and exploration

Donor and recipient were assigned at task rather than database level. A
resource was a candidate donor when a model, coefficient, fixed ranking, or
neighboring-condition prediction derived from its labels was applied to another
task; it was a recipient when its held-out outcomes defined prediction,
screening, or acquisition utility. The same resource could occupy both roles in
different directed edges. Donor status therefore denotes an attempted supply of
information, not demonstrated benefit.

Candidate edges were declared without recipient test outcomes. Eligibility
recorded six attributes: a falsifiable physical or experimental relation; a
representation available for recipient candidates; grouped source
out-of-fold skill; representation coverage and candidate-local applicability;
identity and provenance independence; and a transfer object matched to the
decision endpoint. Missing representation or failed independence excluded an
edge. The remaining attributes informed qualification and prespecified
controls, but none guaranteed transfer. Recipient outcomes were used only to
label an evaluated edge as beneficial, null, harmful, or unresolved, never to
nominate its donor.

For target task $t$, let $x$ denote the target-available material features
and $y_t$ the measured target property. A source model $f_s$ was fitted to
source task $s$. Its out-of-sample prediction

\[
z_s(x)=f_s(x)
\]

was injected as one additional target feature. The baseline target model was
$g_0(x)$, and the augmented model was $g_1[x,z_s(x)]$. Both target models
used the same target labels, split, hyperparameters, and random seed. Source
predictions for target-training rows were cross-fitted; source predictions for
target-test rows were generated by a source model from which those identities
or provenance groups had been removed. Directly measured source values from a
test target were never injected.

The primary effect was relative held-out RMSE reduction,

\[
\Delta_{s\rightarrow t}=\frac{\mathrm{RMSE}(g_0)-\mathrm{RMSE}(g_1)}
{\mathrm{RMSE}(g_0)},
\]

for which positive values favor borrowing. This metric was paired with the
augmented model's held-out R² because a smaller error than a poor baseline does
not imply useful absolute prediction. Learning curves were made monotone by
isotonic regression only for sample-equivalence interpolation, not for model
evaluation. If the augmented n-label RMSE intersected the target-only curve at
(n_{eq}), the estimated target-label fraction saved was
((n_{eq}-n)/n_{eq}).

For OOD screening, numerical source predictions were converted to within-pool
ranks so that properties with unrelated scales could contribute comparable
candidate proposals. A qualified source rank was kept separate from the target
surrogate. This distinction matters because a source may identify a useful
region without calibrating the target property, whereas target-model refitting
can erase a fixed ranking. Multiple qualified neighbors were represented as
separate shortlists. Round-robin allocation alternated among their highest
unseen candidates; rank consensus prioritized candidates supported by more than
one source. Composition novelty and uniform random sampling were retained as
target-only safety channels.

### 2.4 Artifact-gated strategy, evidence layers, and decision rules

After outcome-blind eligibility, the strategy removes material and provenance
overlap; qualifies source signal by target-fold increment and shuffled,
wrong-source, or matched controls; matches soft-prior injection to prediction
and independent ranks to OOD screening; preserves complementary sources as a
portfolio with novelty and random fallbacks; and writes the source-derived
scientific hypothesis before revealing the shortlisted target outcome. A source
may shrink to zero or be retired after demonstrated harm, but its direction is
not rewritten after outcome inspection.

Current experiments test different components of this strategy. KIT tests
cross-fitted predictive borrowing. OBELiX tests fixed ranking and sequential
policy conversion. Caltech tests source admission, wrong-source suppression,
static OOD rankings, and complementary neighbor shortlists on an external
target. The round-robin and consensus portfolios were defined after inspecting
Caltech outcomes and are therefore proof-of-feasibility diagnostics, not frozen
external confirmation.

The initial map designated nine target tasks and five directed sources per
target. Discovery and internal-confirmation entities were disjoint. Exact
canonical identities in each target evaluation set were excluded from the
corresponding source fit. Five discovery-selected edges received the same 999-
permutation refinement and Holm correction; the permutation resolution was not
increased only for favorable edges.

External evidence was kept in separate layers rather than pooled as
exchangeable replications. BIRDSHOT used rolling campaign-time tests. Matbench
used its official five folds. KIT used formulation-group folds within one
experimental campaign. CALiSol used complete source articles as the outer
group. An edge could be labelled an internally selected candidate,
directionally replicated below a practical gate, practically equivalent,
harmful, unresolved, or assigned the operational local-task-rescue status.
Post-outcome sensitivities could not redefine a frozen primary decision.

Local task rescue required every one of the following: at least 5% relative
RMSE reduction; a 95% interval above zero; positive augmented R²; positive
effect in all five outer folds; at least 30% target-label fraction saved; at
least two of three target learners with positive effects; positive source
out-of-fold R²; zero test exposure; a mapping-permutation p value below 0.05; a
valid target-only learning curve; an effect larger than every prespecified
distant control with strictly decreasing effect as distance increased; and a
shuffled-source placebo that was not positive and was smaller than the primary
edge. A p value could not override failed practical, absolute-utility, fold,
sample-saving, or adjacency gates.

The 5% error and 30% label-saving thresholds are operational screening
choices, not universal scientific constants. They were fixed before each
designated outcome analysis to exclude negligible relative changes and to
require material target-label replacement. Results remain reported
continuously so readers can apply a different utility threshold without
changing the underlying measurements.

We additionally tested whether the map-level decision could be learned across
programmes. This analysis was frozen only after the component outcomes and CCA
method concept were known and is therefore method development, not independent
confirmation. Ninety-seven directed edges were grouped into 20 target tasks and
13 independent dataset or campaign programmes; tasks sharing a programme,
including the four TRI plates, were kept in one outer cluster. A weighted ridge
gate used only physical-neighborhood indicators, grouped source out-of-fold R²,
same-domain or condition adjacency, cross-dataset status, and wrong, distant,
or shuffled flags. Each programme was predicted by a fit that excluded every
edge outcome from that programme. Programme-level uncertainty used 10,000
cluster bootstrap resamples. Two one-sided paired programme-level sign-flip
contrasts, against always selecting the most credible source and against never
borrowing, were Holm-corrected. A 20% programme-coverage guard prohibited
trivial abstention.

### 2.5 Alloy coefficient transport and borrowing tests

The direct-law test paired ultimate tensile strength (UTS) and yield strength
(YS) within the Borg multi-principal-element alloy data and the independent
BIRDSHOT campaign [@Attari2025Tabular]. Ordinary least-squares lines were fitted
in log10 strength space. The Borg line was then evaluated unchanged on
BIRDSHOT. Uncertainty used 5,000 composition-cluster bootstrap replicates, and
exact canonical-composition overlap was audited.

For knowledge borrowing, the internally selected Borg UTS→YS edge used n=30
target labels. BIRDSHOT confirmation used Year 1→2 and Years 1–2→3, with
canonical compositions prevented from crossing a temporal boundary. A
post-confirmation sensitivity added cold work, holding time, and grain size but
did not redefine the primary decision. The independent Matbench target
contained 312 steels and retained the official five folds
[@Dunn2020Matbench; @Dunn2020MatbenchCorrection;
@HackingMaterials2018Steel]. Same-row tensile strength and elongation were
forbidden target inputs, and every exact target composition was excluded from
the Borg source fit.

### 2.6 KIT within-campaign local-rescue protocol

The KIT data contain 5,035 temperature-specific conductivity measurements from
504 experiment identifiers and 109 PC/EC/EMC/LiPF6 formulations
[@Rahmanian2023Conductivity]. Replicate experiments were reduced to the median
within each formulation and temperature. The 108 formulations complete across
all target and control temperatures formed indivisible units in five balanced
outer folds. Source models excluded target-test formulations, and source
predictions for target-training formulations were fivefold cross-fitted.

The frozen target was log10 conductivity at −30 °C with 30 target labels per
outer fold. The primary source was −20 °C; sources at 0, 30, and 60 °C were
increasing-distance controls, and shuffled −20 °C source labels formed the
placebo. Composition features were the relative PC/EC/EMC solvent fractions
and LiPF6/solvent mass ratio. Experiment identifiers, batch total mass,
Arrhenius activation energy, pre-exponential factor, fit statistics, fitted
conductivity vectors, and all EIS fit outputs were forbidden because they
encode the same temperature series as the target.

The designated source and target learners were 300-tree Random Forest
regressors with minimum leaf size 2 and all features considered at each split.
Target sensitivities used ExtraTrees and degree-2 polynomial Ridge. The full
run used 100 target-label repetitions, 5,000 hierarchical bootstrap
replicates, 999 fixed-subset feature mappings, 60 learning-curve repetitions
(with the exact 100-repeat n=30 baseline anchor), and 40 sensitivity
repetitions.

Because the frozen sample-saving gate used a learning-curve point estimate, a
post-outcome diagnostic separately quantified its stability. For every budget,
target-only squared errors were reconstructed as a repetition-by-formulation
matrix. A 5,000-replicate conditional bootstrap resampled the 108 formulations
and target-training repetitions within each budget, refitted the monotone curve,
and re-interpolated the equivalent sample count. This diagnostic did not
redefine the frozen decision and does not measure cross-campaign uncertainty.

### 2.7 CALiSol paper-disjoint replication protocol

CALiSol-23 contains 13,825 conductivity points curated from 27 publications,
covering 38 solvents, 14 reported lithium-salt labels, concentration, and
temperature [@deBlasio2024CALiSol; @deBlasio2023CALiSolData]. Before any
conductivity model was run, −40 °C was fixed as the target because it was the
coldest 10 °C-grid slice represented by at least ten articles. The nearest
−30 °C task was primary; −20, 0, and 20 °C were increasing-distance controls.
Rows within ±2.5 °C of each nominal temperature were assigned to that task.
Conductivities at or below 10⁻¹² mS cm⁻¹ were treated as numerical zeros and
excluded before the log10 transform.

The target contained 891 eligible paper-specific formulations from 15
articles after two chemistry identities reported by multiple target articles
were removed. Five outer folds held out complete article DOIs and balanced
target row counts. For target-test predictions, all source-temperature rows
from the held-out articles and all exact test chemistry identities reported in
other articles were excluded. Target-training priors were leave-one-article-
out predictions. The model used salt identity, concentration and unit,
solvent-ratio convention, and 38 solvent columns. Article DOI, temperature,
another measured conductivity, Arrhenius/VTF quantities, and any target-series
summary were forbidden predictors.

The CALiSol settings otherwise matched the KIT decision framework. The
article-hierarchical bootstrap resampled target-label repetitions, articles,
and formulations; the mapping null permuted the feature within article. The
full run used 100 target repetitions, 5,000 bootstrap replicates, 999 mappings,
60 curve repetitions, and 40 sensitivity repetitions. The design was frozen
internally rather than externally preregistered, and implementation-only
changes were logged.

### 2.8 Systematic multi-target OOD borrowing benchmark

To test the stronger claim that a fixed borrowing procedure repairs
out-of-distribution prediction, we froze a unified benchmark on 23 July 2026
before its formal run. The protocol was written after outcomes from several
component studies had been inspected and is therefore systematic method
development, not independent confirmation. It reused the exact task definitions
and 60/20/20 discovery, confirmation, and holdout partitions in the
knowledge-borrowing map. Targets required at least 12 intact evaluation groups;
eight targets across seven dataset or campaign programmes were eligible. For
each target, five real donor edges and a shuffled version of the designated
donor were retained, giving 40 real edges and eight shuffled controls.

The evaluation pool combined the discovery and confirmation partitions but was
never used to fit a target model. OOD membership was defined without recipient
outcomes. For formula-indexed tasks, features were standardized elemental
fractions and composition-distribution descriptors fitted on the complete
development partition; the distance of each evaluation entity was its minimum
Euclidean distance to that reference. For molecular tasks, distance was one
minus the maximum Morgan-fingerprint Tanimoto similarity. Intact evaluation
groups were ranked by their median entity distance and split into quartiles; Q1
was treated as in-distribution and Q4 as OOD.

Every source model excluded all recipient-evaluation identities. Its prediction
was added as one soft feature to a target model trained on grouped n-label
subsamples from the complete development partition. Ridge regression with
α=10 was designated as primary; 100-tree Random Forest and ExtraTrees models
with minimum leaf size 2 and `max_features=0.7` were learner sensitivities.
One hundred grouped target-label draws were paired across target-only,
source-augmented, wrong-source, and shuffled-source fits. Relative RMSE gain was
defined as \(100(\mathrm{RMSE}_{target}-\mathrm{RMSE}_{augmented})/
\mathrm{RMSE}_{target}\), and OOD specificity as the Q4 gain minus the Q1 gain.

Intervals used a hierarchical bootstrap over target-label repetitions and
evaluation groups. Primary source contrasts used paired sign-flip tests with
Holm correction across the eight designated edges. A complete OOD-repair pass
required a positive OOD interval, at least 5% OOD gain, improvement in at least
80% of repetitions, superiority to wrong and shuffled controls, positive
effects in all three learners, positive augmented OOD R², positive OOD
specificity, and Holm-adjusted \(p<0.05\). A separate bootstrap treated the
seven programmes, rather than edges or repeats, as the independent units.
Cross-database conclusions were restricted to the three designated
cross-database edges. Because the protocol followed prior component inspection,
it can reject generic OOD repair within the tested envelope and generate
specific hypotheses, but it cannot create retrospective prospective evidence.

#### State-matched alloy robustness analysis

The generic benchmark discarded experimental state when collapsing the Borg
MPEA data to composition-level targets. We therefore performed a separately
frozen, post-selection robustness analysis on the raw experimental rows. The
target comprised 1,067 positive yield-strength (YS) records in 150 unordered
elemental systems; the neighboring endpoint comprised 539 positive ultimate
tensile-strength (UTS) records in 93 systems, including 495 paired rows. The
planned-state contract used composition, processing route, coarse phase family,
test mode, test temperature, and calculated density. Elemental systems, rather
than rows or exact formulas, were indivisible split units.

At each of 30 target-label draws, 60 YS labels were sampled from development
systems. UTS predictions on a target-training fold came from an ExtraTrees
donor that excluded every system in that fold and every evaluation system; the
final donor likewise excluded all evaluation systems. The predicted log10 UTS
was concatenated with the planned-state target features. Random Forest and
ExtraTrees target learners used 320 trees, minimum leaf size 2, and
`max_features=0.7`. A donor-outcome permutation was regenerated inside every
fold. Measured UTS on paired rows was retained only as an auxiliary-measurement
ceiling.

Evaluation systems were ranked by median nearest-neighbor composition distance
to each actually labelled target-training draw and divided intact into
quartiles. The primary estimate used a frozen 100,000-replicate two-way cluster
bootstrap that independently resampled elemental systems and the 60
model-by-draw runs. The procedure was selected after earlier MPEA outcomes had
been inspected; it tests stability on this programme, not independent or
prospective confirmation.

### 2.9 OOD screening and sequential-discovery protocols

OBELiX ionic conductivity was evaluated on canonical compositions after
removing train–test duplicates introduced by formula normalization
[@Therrien2026OBELIX]. The resulting table contained 390 official-training and
110 official-test compositions. Evaluation groups preserved the upstream DOI
grouping and canonical identity, and exact overlap between each source domain
and all 500 target compositions was zero. Target inputs were 118 elemental
fractions plus eight composition-distribution descriptors. Frozen source
features were predictions from thermoelectric ZT, alloy yield strength, and
CO2-reduction H2 Faradaic-efficiency models; a deterministic permutation of the
thermoelectric predictions supplied the shuffled control.

Fixed-ranking OOD screening used the fraction of a held-out candidate pool
ranked before the first true top-5% hit. The primary independent family
contained BIRDSHOT temporal, CALiSol article-disjoint, and OBELiX official-test
edges with Holm correction across exactly those three edges. For OBELiX, 60
repeated n=30 target subsets were evaluated with Ridge as the primary target
learner and Random Forest and ExtraTrees as sensitivities. A positive interval
and adjusted p value were insufficient for an improvement label unless the
relative reduction was at least 25%, at least 80% of repeats improved, the
prespecified controls remained negative, and the result crossed the fixed 10%
shortlist boundary. The farthest 40% of each OOD pool by minimum elemental-
fraction L1 distance to the target training reference was selected without
target outcomes. Because that design was written after the whole-pool OBELiX
direction was known, hard-OOD results are explicitly exploratory.

The sequential OBELiX campaign was frozen before any result under that
definition. Every strategy received the same group-aware n=30 initial labels
from the official training split and acquired only from the 110-composition
official test pool; a secondary analysis used the fixed 44-composition hard-OOD
subset. A true discovery was the first member of the observed top-5% set, the
budget was 40 acquisitions, and no-hit campaigns were censored at 41. The
primary target policy was an 80-tree ExtraTrees regressor refitted after every
acquisition with score equal to ensemble mean plus one ensemble standard
deviation. Strategies comprised target-only features, each of the three frozen
source features, the shuffled thermoelectric feature, and uniform random
acquisition. The primary analysis used 100 paired seeds; a 120-tree Random
Forest sensitivity used 40 paired seeds for target-only and thermoelectric-
prior policies.

OOD-discovery improvement required a one-sided paired sign-flip p≤0.05, a
paired-bootstrap interval above zero, at least five mean experiments saved, at
least 25% relative saving, improvement in at least 60% of paired seeds, a
positive Random-Forest sensitivity, and no wrong-source or shuffled prior
passing the same core gates. Rescue additionally required the target-only
median to exceed 10% of the pool and the prior median to fall within it. The
sequential campaign was executed from a hash-verified, self-contained input on
Balam using 64 CPU workers. Design, input, environment, seed coverage, output
hashes, and completion sentinel were verified after download.

An independent external policy benchmark used the Caltech experimental
Li-ion-conductivity database. After eligibility filtering and canonicalization,
483 compositions were grouped by identity and article into 339 development
entities, 144 article-disjoint candidates, and a fixed 58-candidate hard-OOD
subset. Every source fit excluded exact target compositions and target DOIs.
Prespecified sources were OBELiX same-property conductivity, ESTM
transport-adjacent thermoelectric data, and mechanical and catalysis wrong-domain
controls, plus a shuffled OBELiX control. The primary endpoint was cumulative
recovery of the true top-5% region through 20 acquisitions. Source residual
ranks entered only after article-grouped cross-validation showed positive error
reduction in at least three of five folds, at least 2% median relative RMSE
gain, and positive mean gain; otherwise their weight was zero. Eight source
increment contrasts per candidate scope were Holm-adjusted and additionally
required a 20% practical gain, 60% seed consistency, first-hit
non-inferiority, recall20≥0.50, and success in both scopes. The formal run and
same-environment static-policy replay were completed as Balam Jobs 70740 and
70767, followed by portable recomputation of all utilities and contrasts.
Static OBELiX and ESTM rankings were included before target outcomes, but
source-attribution contrasts for those deterministic rankings were not in the
primary family. After the adaptive result was known, two target-model-free
portfolio diagnostics were defined: round-robin interleaving of the two source
shortlists and rank consensus over their top 40 candidates. They quantify
complementarity and select the integrated strategy for an outcome-unseen target;
they cannot revise the frozen adaptive decision.

An outcome-informed robustness analysis then changed the discovery unit from
individual compositions to connected identity/provenance components. Components
were constructed without target outcomes by joining records that shared a
canonical formula, DOI, or ICSD identifier. The credibility–complementarity–
abstention (CCA) family-first policy first formed the unweighted OBELiX/ESTM
rank-sum order, traversed that order once while retaining only the first member
of each component, and appended within-component repeats only after every
represented component had received one opportunity. OOD distance was retained
as a scope and reporting variable rather than multiplied into the source score.
The primary method-development endpoint was cumulative first recovery of the
top ceil(5%) components, defined by their best observed target value, through
acquisition 20. Median- and mean-component outcomes and the original entity
endpoint were sensitivities. Controls were family-first uniform and composition-
novelty orders, each individual neighbor, a mechanical/catalysis wrong-source
pair, and 5,000 pairs of independently shuffled neighbor ranks. Candidate-
outcome permutation was required to leave every acquisition order invariant.

To quantify the target-domain knowledge deficit rather than assume it, a
separate post-outcome diagnostic refitted target-only and source-augmented
ExtraTrees and Random-Forest models over label budgets 15, 30, 60, 120, and 240.
For every grouped target-label repeat, the 110 official-test compositions were
divided into quartiles by outcome-free Euclidean distance to the nearest selected
target-training composition in the development-standardized 126-dimensional
composition representation. The fixed 44-composition hard-OOD subset was a
sensitivity. Primary diagnostics at n=30 were the target-only RMSE difference
between the farthest and nearest quartiles, the association between absolute
error and distance, the thermoelectric-prior RMSE increment in the farthest
quartile, and its separation from the best alloy, catalysis, or independently
shuffled-source control. Intervals resampled the 100 paired target-label repeats
and are conditional on the single fixed OBELiX test set; this diagnostic cannot
revise the frozen screening or sequential decisions.

### 2.10 Outcome-unseen reverse-transport and second-family validation

The integrated strategy was frozen on two targets whose outcomes had not been
inspected during target construction, source fitting, policy ordering, or
hypothesis writing. Starrydata2 supplied the reverse transport direction:
ionic-conductivity sources were used to predict thermoelectric ZT. Hash-pinned
paper, sample, and curve files yielded 7,403 frozen entities, of which 7,396 had
valid target outcomes. Outcome-free identity, sample-lineage, DOI, and
composition-cluster rules created 4,427 development, 1,675 validation, and 1,301
evaluation entities. The primary cell used n=30 target labels, ExtraTrees,
composition features, and the highest of four frozen OOD quartiles. Same-domain
ESTM, adjacent OBELiX and Caltech ionic-conductivity sources, Borg and OCx wrong-
domain sources, a frozen shuffle, and source-size, source-skill, target-coverage,
and equal-capacity controls were retained. Three learner families, two
representations, label budgets 15, 30, and 60, 100 target-label repeats, ten
exploration policies, and three source-derived hypothesis cards were evaluated.

The second scientific family used the four composition plates in the deposited
TRI OER benchmark. The four paper-defined plates contained 8,447 eligible
entities in 240 outcome-free composition clusters. Each plate was held out in
turn. The same-reaction acid-OER source, adjacent ORR and OCx sources, Borg and
OBELiX wrong-domain controls, source shuffles, three learner families, two
representations, the same label budgets, and three prewritten hypothesis cards
were retained. The earlier acid-OER candidate target was downgraded before
outcome access because its plate sizes failed the frozen quality minimum; it was
not replaced after an unfavorable result.

Prediction inference resampled target-label repeats and independent provenance
or composition groups rather than treating seeds as external replications.
Named contrasts were Holm-adjusted within target. TRI effects were synthesized
across the four held-out plates by random effects, and the two target-level
effects were then synthesized with between-target heterogeneity reported. All
methods and controls remained in the denominator regardless of sign. Of 468,000
TRI metric rows, 3,244 secondary Spearman cells were undefined because one input
was constant. They were retained as missing; every primary RMSE, MAE, R², gate,
and contrast was finite and did not use Spearman. The formal programme completed
on Balam as Job 70888 and was independently replayed by portable verifiers using
the frozen hashes and row families.

### 2.11 Protected temporal multi-stage battery programme

A public two-stage battery-aging programme provided a temporal source-target
test in which Stage 1 measurements were released in 2021 and the paired Stage 2
measurements in 2023. Archive identity, cell identity, operating conditions,
endpoint extraction, source fitting, target grouping, and a 23-condition
leave-one-group-out analysis were frozen without opening Stage 2 outcome files.
The only transferred quantity was a cross-fitted Stage 1 degradation prediction
computed before Stage 2 outcomes. Target-only, wrong-property, shuffled-source,
random-feature, continuous adjacent-source, and training-only gated CCA-v2
policies were retained.

The Stage 2 release contained 138 allowlisted cells. Three archives in one z10
cycle-aging condition group contained no required `AT_T23` terminal file, so the
frozen 23-group primary failed its complete-coverage gate and was declared
non-evaluable. A disclosed post-release sensitivity retained 135 cells in 22
complete condition groups (eight calendar-aging and 14 cycle-aging groups)
without substituting another endpoint. Effects were computed from leave-one-
condition-group-out predictions. The primary metric was the equal-stratum mean
relative reduction in condition-level RMSE, giving calendar and cycle aging
equal weight. Intervals resampled condition groups within stratum; one-sided
sign-flip tests were Holm-adjusted across the four displayed false-source and
target-only comparisons.

CCA-v2 used only outer-training information to decide whether borrowing was
allowed. After that sensitivity showed over-abstention, an explicitly outcome-
guided diagnostic evaluated the simpler continuous adjacent-source feature.
This diagnostic was fixed, replayed by an independent verifier, and reported in
full, but it is method-development evidence and cannot replace the non-evaluable
primary. Two source-inspired lead-versus-control condition cards written before
Stage 2 outcome access were retained as directional checks rather than treated
as independent population-level tests.

### 2.12 Compensation-law artifact battery

Thermoelectric Arrhenius series were separated by reference and required
prespecified fit-quality and family-size rules. The Meyer–Neldel association
was evaluated globally and within chemical families, with heteroskedasticity-
consistent inference, multiplicity control, and threshold sensitivity.

For adsorption, the hash-pinned NIST ISODB archive was streamed without
extraction [@Siderius2019ISODB]. Eligible pure-component isotherms had at least
five finite positive points and a monotone pressure–uptake relation. A system
required at least three temperatures and a common uptake interval. One
geometric-midpoint uptake was selected per system; pressure was interpolated
at that loading, duplicate temperatures were collapsed by the median, and
ln(p/bar) was fitted against 1/T. This yielded one isosteric heat–intercept pair
per DOI–adsorbent–adsorbate–unit system. The Krug null independently permuted
the fitted heat and intercept onto observed temperature grids. DOI-cluster
bootstrap and wild-cluster tests evaluated pooled and adsorbate-family models.

### 2.13 Statistical implementation and reproducibility

All claim-bearing designs, amendments, compact outputs, figure source data,
source revisions, software versions, and file hashes are recorded in the
release manifest. Random seeds were fixed before formal runs. Large row-level
prediction tables are reproducible but need not be versioned. Unless otherwise
specified, reported intervals are two-sided 95% intervals and permutation
tests are one-sided in the prespecified beneficial direction. No alternative
primary edge was selected after a frozen edge failed.

Multiplicity was controlled within explicitly defined decision families: five
internally screened borrowing candidates, three named independent OOD edges,
eight Caltech policy contrasts within each candidate scope, and the named
prediction, exploration, and hypothesis-card contrasts in each outcome-unseen
target. Single-edge KIT, CALiSol, BIRDSHOT, and Matbench boundary tests addressed
separately designated questions. No cross-family error-rate control is claimed
across the entire paper; conclusions are therefore attached to their stated
family and endpoint rather than to an omnibus study-wide discovery rate.

Uncertainty units follow the sampling design rather than a common seed count.
Borg intervals resample compositions, KIT intervals resample target subsets,
folds, and formulations within one campaign, CALiSol intervals resample
articles, Starrydata intervals resample target-label repeats and independent
evaluation blocks, TRI inference retains the four held-out plates, and ISODB
inference clusters by DOI. Sequential-policy intervals are paired campaign-seed
uncertainty on fixed candidate pools. Deterministic Caltech static rankings have
no dataset-level interval; repeated candidate seeds do not substitute for
independent target datasets.

## 3. Results and discussion

### 3.1 Twenty analysed resources define the empirical scope

Every resource shown in Figure 1 enters at least one numerical analysis. The
cohort comprises 13 locally normalized resources, six frozen external or
temporal resources, and one streamed artifact-analysis resource. The normalized
core contains all 96,184 measurements spanning aqueous molecular properties,
energy and ionic transport, alloy mechanics, catalysis, and polymers
(Fig. 1a,b). Two normalized rows retain unresolved canonical identities,
property names and units remain source-level, and ISODB remains analysis-only.
These constraints define which comparisons can be made without silently
inventing a conversion or identity.

The directed benchmark contains 19 transfer-active resources: 15 donors, 16
recipients, and 12 used in both roles. After endpoint, identity, provenance,
leakage, and split gates, the cross-program synthesis contains 97 evaluated
source-target edges, 20 target tasks, and 13 programme clusters (Fig. 1c).
These edges include within-resource cross-property, adjacent-condition,
external cross-dataset, OOD-ranking, and control tests; they are not 97
independent cross-domain replications. Four cases are visually
emphasized because they expose different inferential roles--an internal
cross-domain candidate, a leakage-safe local rescue, an external policy-
conversion boundary, and a protected temporal diagnostic--not because they are
the four most favorable outcomes. The same portfolio retains failed
coefficient transport, organic and mechanical nulls, unresolved cross-article
transfer, outcome-unseen null or harmful targets, and sequential-policy
failures (Fig. 1d). The empirical scope is therefore supported by the complete
analysed cohort, held-out programmes, negative controls, and outcome-unseen
tests rather than by resources that never enter an analysis.

The integration is therefore part of the scientific method rather than a
claim of universal harmonization. It enables row-level provenance, exact-
identity auditing, and source-revision checks while preserving exclusions. In
particular, scale normalization revealed two OBELiX test compositions that
were identical to training compositions despite different raw strings; both
were removed before primary modeling. CALiSol's negative concentration
artifact was retained in the raw table but not promoted to a valid mixture.

### 3.2 A strong alloy calibration does not constitute a transportable law

The Borg data contained 495 paired UTS–YS records from 208 canonical
compositions. Their log–log relation was strong (R²=0.790). The independent
BIRDSHOT campaign contained 171 paired records from 151 compositions, with
zero exact compositions shared with Borg, but its in-domain relation was much
weaker (R²=0.067; Fig. 2a). Applying the Borg line unchanged to BIRDSHOT gave
R²=−3.006, with a composition-cluster 95% interval of −4.154 to −2.185. The
median UTS/YS ratio changed from 1.36 to 2.72.

This is a direct failure of coefficient transport, not a statement that UTS
and YS are unrelated. Both campaigns retained an association, but the fitted
coefficient was not invariant to their chemistry, processing, or measurement
distributions. A pooled or source-domain R² therefore cannot by itself support
an unconditional constitutive claim.

### 3.3 The knowledge-borrowing map is sparse and directional

The internal screen contained 42 directed candidate edges. Edge
heterogeneity was strong (Cochran Q p=0.00036), which rejected the idea that a
single average transfer effect represented the screen. One non-calibration edge
passed every internal gate: Borg UTS→Borg YS reduced n=30 RMSE by 6.46%
(3.69–13.03%), with a refined raw permutation p=0.001, Holm p=0.005, and all
three target learners positive. Mean R² changed from −0.149 to +0.025. Its
target-only learning curve mapped the augmented error to an estimated 73.4%
target-equivalent fraction saved. Because it was selected from the internal
screen and has no external replication with positive absolute utility, it is
retained as an internally selected candidate, not a confirmed edge.

On BIRDSHOT, the same source-prediction feature reduced rolling-time RMSE by
4.30% (3.36–5.51%; p=0.003). Year 1→2 and Years 1–2→3 effects were +4.39% and
+4.12%, and all three learners were positive. Nevertheless, the result missed
the frozen 5% practical threshold, and the rolling-time learning curve was not
monotone. A process-aware sensitivity retained a 5.23% (3.74–7.03%) relative
reduction, but pooled R² remained negative (−1.216→−0.992). The evidence
therefore supported a directional replication below the practical and
absolute-utility gates, not rescue.

Matbench supplied a stronger negative boundary. Under the official five folds,
Borg UTS→Matbench YS changed RMSE by −1.23% (−15.88–2.48%; p=0.794), and all
five primary fold effects were negative. Random Forest and ExtraTrees
sensitivities produced effects below 1%, far short of the practical gate.
Mechanical-property adjacency alone was therefore insufficient. Across the
15 independent BIRDSHOT edges, eight were harmful and two were practically
equivalent. The original 0–3 cross-domain neighborhood score was not
established (Spearman ρ=0.212, p=0.113). A post-map binary direct-neighbor
contrast favored neighbors in 9 of 12 targets (one-sided Wilcoxon p=0.046), but
was leave-one-target-out fragile and remained exploratory.

### 3.4 An adjacent condition materially improves KIT few-shot performance

The KIT −20→−30 °C primary edge passed every internally frozen point-rule
gate as originally operationalized, including the point-estimate sample-saving
gate (Fig. 2b,c).
At n=30, the source-prediction feature reduced held-out RMSE by 15.02%
(8.61–21.10%), with p=0.001 from 999 fixed-subset mappings. Pooled R² increased
from 0.739 to 0.811. All five formulation folds were positive, and the Random
Forest, ExtraTrees, and polynomial Ridge effects were +15.02%, +19.63%, and
+34.47%, respectively. The source model had out-of-fold R²=0.859. In the
augmented Random Forest, the source-prediction feature had mean importance
0.732 and median rank 1 of 5; this diagnostic shows predictive use but does not
identify a microscopic mechanism.

The target-only learning curve decreased monotonically. The augmented n=30
RMSE intersected the curve at n=47.884, corresponding to an estimated 37.35%
of equivalent target labels saved. This quantity is a retrospective
sample-efficiency equivalence, not a count of prospective experiments already
avoided. In the post-outcome formulation/subset bootstrap, the 95% diagnostic
interval was n=38.38–59.89, or 21.84–49.91% saved; 80.52% of replicates met the
frozen 30% threshold. The direction of the efficiency gain was stable, but its
magnitude relative to that threshold was not.

Prespecified controls established selectivity within the campaign. Relative
RMSE reductions were 15.02%, 5.01%, 0.95%, and −0.76% at temperature distances
of 10, 30, 60, and 90 °C, giving Spearman ρ=−1 across the four real sources.
The shuffled adjacent source was harmful (−2.96%, −4.32 to −1.44%). These
controls ruled out a generic benefit from adding one random model-derived
feature and supported a local ordering for this target. They did not establish
temperature distance as a universal transfer metric.

### 3.5 CALiSol shows that the KIT improvement is not automatically portable

The paper-disjoint CALiSol test was designed before outcome modeling to probe
the strongest remaining rival explanation: KIT might succeed only because
source and target came from one tightly controlled campaign. The CALiSol
source model generalized above chance across held-out articles at −30 °C
(source article-out-of-fold R²=0.119), and all three target learners had
positive mean directions. These conditions were nevertheless insufficient for
practical borrowing.

The frozen −30→−40 °C edge reduced RMSE by only 1.61%, with an article-
hierarchical interval of −2.14% to +4.21% (Fig. 2b). Baseline and augmented R²
were −0.049 and −0.014. Fold effects were −0.78%, +0.003%, −3.85%, +3.11%, and
+6.45%; the estimated target-equivalent count was 36.12 and the label fraction
saved was 16.9%. The 0 °C control was numerically stronger (+2.18%), and the
real-source distance ordering had Spearman ρ=0.0. The shuffled source effect
was +0.83% with an interval crossing zero.

The fixed first-subset mapping test gave p=0.004. Interpreted alone, this result
would invite a significance claim. Under the frozen decision rule, however,
it could not override the repeated-effect interval, <5% practical effect,
negative absolute R², two harmful folds, <30% estimated saving, and failed
distance ordering. The edge was therefore retained as cross-article borrowing
unresolved. No alternative CALiSol temperature was promoted after the 0 °C
control appeared numerically larger. The contrast with KIT is central:
adjacent-condition borrowing can materially improve few-shot error within one
controlled campaign, but physical proximity does not erase between-article
measurement and composition heterogeneity.

### 3.6 State-matched neighboring knowledge repairs a selected OOD task where generic injection fails

The unified benchmark evaluated 40 real donor–recipient edges across eight
targets, three learner families, and 100 paired target-label draws (Fig. 3a).
Among the eight designated edges, the strongest result was alloy UTS→YS. It
reduced OOD-quartile RMSE by 6.65% (95% CI, 3.53–14.02%), improved 93% of
repetitions, beat the wrong-property and shuffled controls, remained positive
for all three learners, and retained significance after Holm correction
(\(p=0.0008\); Fig. 3b,d). Yet it also reduced the in-distribution error by
7.74%, giving an OOD-specific difference of −1.09% [−7.00,12.34%], and its
augmented OOD R² remained negative (−0.666). The edge therefore demonstrated
transferable alloy correlation, but not repair specific to the OOD region.

No designated edge passed the complete OOD-repair gate. The electrolyte
conductivity target received a small positive direction from thermoelectric
electrical conductivity (+0.98% [−3.14,3.70%]), but the interval and
multiplicity gates failed and augmented OOD R² was −7.683. The reverse
solubility–hydration edge was positive but practically negligible (+0.084%),
while the remaining designated cross-database edge was null or harmful.
Consequently, zero of three designated cross-database edges and zero of eight
designated edges overall achieved positive absolute OOD utility with the full
control battery.

Treating programmes rather than repeats as the independent units gave a mean
designated-edge OOD gain of +0.92% [−0.35,2.92%] across seven programmes. Across
all 40 real edges, 19 showed a positive OOD direction, but nine were not
OOD-specific, ten were harmful, and eleven remained unresolved (Fig. 3c). Some
non-designated edges produced larger relative gains, yet retained strongly
negative absolute OOD R² or encoded same-family constitutive calibration and
therefore remained hypothesis-generating. The benchmark thus rejects the
shortcut that one model-derived donor feature automatically repairs remote
regions. It instead motivates endpoint matching: qualified soft features can
support local few-shot prediction, whereas OOD exploration should preserve
independent donor rankings or family-level proposal portfolios until they pass
an external utility test.

The state-matched follow-up identified the missing condition for the alloy
edge (Fig. 3e–h). In Q4, predicted UTS reduced state-aware target RMSE by 9.21% (two-way
cluster-bootstrap 95% CI, 4.43–14.37%); 55 of 60 frozen model-by-draw runs
improved. Pooled augmented Q4 R² was 0.103, compared with a negative state-only
baseline. The architecture-matched shuffled donor was null (−0.26%
[−1.81,1.01%]), and the real-minus-shuffled Q4 contrast was +9.47 percentage
points [4.80,14.34%].
Thus, the benefit depended on transferable UTS structure rather than merely an
additional covariate.

The corresponding Q1 gain was +7.21% [3.05,11.52%]. The Q4-minus-Q1 point
difference was +2.00 percentage points, but its interval crossed zero
[−4.66,8.62%]. The result therefore demonstrates stable benefit *within* the
most distant OOD region, not statistically exclusive or preferential OOD
benefit. The Q4 R² bootstrap interval also crossed zero [−0.151,0.291], so the
positive point estimate is evidence of practical repair on this programme,
not a claim of uniformly calibrated extrapolation. Directly measured UTS
provided a much larger Q4 ceiling: 47.70% mean RMSE reduction and augmented
R²=0.679. The learned donor currently recovers only part of the neighboring
endpoint information available in experiment.

### 3.7 Artifact gates prevent both false universality and false dismissal

The thermoelectric Meyer–Neldel analysis produced only a weak pooled
association across 112 reference-separated series (R²=0.107). The estimate was
sensitive to inclusion thresholds, and small chemical-family fits could not
support a domain-wide law. The correct conclusion was weak evidence for one
pooled coefficient, not proof that compensation is physically absent.

ISODB produced the opposite case. The matched-loading procedure yielded 1,103
one-fit-per-system estimates from 512 DOI clusters. The pooled isosteric heat–
intercept relation had R²=0.637. The geometric separation between T_iso=513 K
and the median harmonic experimental temperature of 301 K was the primary
artifact diagnostic (Fig. 2d). The independent-parameter Krug null had median
R²=0.003 and reproduced an R² at least as large with p≤0.001. Thus the observed
association was not consistent with this simple independent-parameter coupling
null. The test does not exclude correlated measurement error, DOI-specific
limited-temperature-range coupling, or selection induced by fit-quality
filters.

Surviving that artifact gate did not make the relation universal. Adsorbate-
family intercepts remained unequal under a 4,999-replicate DOI wild-cluster
test (p=0.0002), whereas family-specific slope heterogeneity was not
established (p=0.625). The defensible result was a strong but conditional
empirical regularity. The gatekeeping workflow can therefore separate weak from
strong-but-conditioned outcomes while remaining able to reject
artifact-consistent patterns; it is not designed to
declare every pooled pattern either universal or spurious.

### 3.8 A directional OOD screening signal does not become discovery acceleration

Fixed-ranking analysis supported a directional, but sub-threshold, OBELiX OOD
screening signal (Fig. 4a). Across 60 n=30 repeats, adding the thermoelectric ZT
prior reduced the mean fraction of the 110-composition official-test pool
screened before the first true top-5% hit from 12.08% to 9.98%. The absolute
reduction was 2.09 percentage points (0.94–3.45), or 17.3% relative, with Holm-
adjusted p=0.0003 across the three named independent OOD edges. Random Forest
and ExtraTrees sensitivities had the same positive direction. The edge
nevertheless failed the frozen 25% relative-effect and 80% repeat-consistency
gates, and the baseline median was already within the 10% shortlist boundary;
its status was therefore directional OOD screening, not rescue. In the
outcome-free farthest-40% subset, the corresponding mean changed from 21.59% to
18.11% and crossed the 10% median shortlist boundary, but the 16.1% relative
reduction and 36.7% positive-repeat rate again failed the gates. Because this
subset was specified after the whole-pool direction was known, it remains
exploratory.

The sequential campaign prespecified after fixed-ranking inspection did not
retain that signal
(Fig. 4b,c). In the official test pool, target-only ExtraTrees UCB and the
thermoelectric-prior policy required means of 24.34 and 24.09 acquisitions,
respectively. The paired saving was 0.25 experiments (−1.30 to 1.82; p=0.389),
only 28% of seeds improved, and censoring at the 40-acquisition budget was 40%
and 41%. Every primary improvement gate failed. The Random-Forest sensitivity
was also null: 0.525 experiments saved (−1.85 to 3.10; p=0.354). In the hard-OOD
subset, ExtraTrees gave a smaller but statistically positive 2.21-experiment
effect (0.97–3.49; p=0.0004); it still failed the five-experiment, 25% relative,
and 60% consistency gates, and the Random-Forest sensitivity interval crossed
zero. It cannot be promoted to improvement or rescue.

Uniform random acquisition exposed a policy-level failure rather than a
missing-prior problem. It required 15.50 acquisitions in the official pool,
compared with 24.34 for target-only UCB and 24.09 for thermoelectric-prior UCB;
its 8.84-experiment advantage over target-only UCB had a prespecified paired
interval of 4.57–12.90. The empirical random mean agreed with the exact
censoring-adjusted random expectation of 15.30, arguing against an anomalously
lucky control draw. Random acquisition also outperformed both UCB policies in
the hard-OOD subset. These data establish failure of the tested composition-
based UCB policies under this retrospective pool, but do not distinguish poor
mean ranking, uncalibrated ensemble spread, or iterative-refit instability, and
do not establish random search as generally optimal. For these composition
representations, tree-ensemble learners, and mean-plus-standard-deviation UCB
policy, average predictive utility, fixed OOD screening, and sequential
discovery behaved as distinct endpoints. Random superiority is also consistent
with miscalibrated ensemble spread rather than a general property of UCB or
neighbor priors.

An isolated post-result method-development benchmark further identified
composition novelty as a stronger target-only acquisition baseline and
source/target/novelty rank fusion as a possible breadth-of-recall policy.
However, fusion did not beat novelty for the first-hit endpoint, its hard-OOD
breadth advantage did not reproduce, and thermoelectric static ranking was not
practically separated from the catalysis control. Because the policy family was
selected after inspecting OBELiX outcomes, this analysis is reported only as
candidate-method selection and does not revise the frozen sequential null.

The post-outcome knowledge-deficit audit nevertheless localized the weakness
that motivates borrowing. At n=30, target-only ExtraTrees RMSE in the farthest
composition-distance quartile exceeded that in the nearest quartile by 0.373
(conditional 95% interval 0.047–0.669), and absolute error increased with
distance (mean Spearman ρ=0.097, 0.049–0.144). In that farthest quartile, the
thermoelectric source reduced RMSE by 3.95% (2.65–5.26%) and exceeded the best
alloy, catalysis, or shuffled-source reduction by 1.29 percentage points
(0.21–2.40). The Random-Forest sensitivity had the same qualitative direction.
These results show that the target-only deficit and a selective neighbor
increment co-occur in the underrepresented region, but they are conditional
post-outcome diagnostics on one target rather than independent transport
evidence.

### 3.9 Preserving neighboring rankings reveals complementary external OOD signal

The Caltech benchmark showed that neighboring domains retained useful external
ranking information when their proposals were preserved rather than absorbed
into the target surrogate (Fig. 5d). In the complete 144-candidate pool, the
prespecified OBELiX same-property and ESTM transport-neighbor rankings obtained
AUC20 values of 33 and 45, versus 11.25 for random, and recovered 2/8 and 3/8
true top-5% entities. Mechanical and catalysis controls recovered 0/8. In the
58-candidate hard-OOD scope, OBELiX and ESTM obtained AUC20 values of 38 and 51
versus 9.87 for random and each recovered all 3/3 top entities by acquisition
20. Exact target compositions and target DOIs were excluded from every source
fit, so these candidates were not direct material or article retrieval.

The two neighbors proposed complementary candidates. After outcome inspection,
round-robin and rank-consensus combinations of their independent shortlists
recovered 5/8 external top-5% entities by acquisition 20 and all 3/3 hard-OOD
entities. The individual neighbors recovered 2/8 and 3/8 externally. This
numerical gain demonstrates portfolio complementarity on the observed target
and selects a target-model-free strategy for a new target. Because the
portfolio was constructed after inspecting Caltech outcomes and deterministic
rankings have no dataset-level interval, it is proof of feasibility rather than
independent confirmation or a Caltech discovery claim.

Entity counts overstated discovery breadth because the eight external top
entities occupied only four connected formula/DOI/ICSD components, and the
three hard-OOD top entities belonged to one component. We therefore evaluated
the outcome-informed CCA family-first policy on 63 external and 36 hard-OOD
components (Fig. 5e). Relative to entity consensus, family-first consensus
increased distinct-component AUC20 from 47 to 60 externally and recovered 4/4
top components at positions 3, 4, 5, and 12 rather than 3/4. In hard OOD it
increased AUC20 from 36 to 39 and placed both top components first and second.
The wrong-source pair obtained AUC20=6 and 18. Independently shuffling both
neighbor rankings 5,000 times gave conditional 95% ranges of 0–45 and 3–36
and randomization p=0.0020 and 0.0030 for the observed family-first AUCs.
Candidate-outcome permutation changed no order. The external result was
unchanged when components were ranked by their median outcome; mean outcome
gave 3/4 recovery, exposing the expected sensitivity to the definition of a
valuable family.

This improvement is specific to exploration breadth. Family-first allocation
reduced external entity recall20 from 5/8 to 2/8 and hard-OOD entity recall
from 3/3 to 1/3 because it deliberately stopped repeatedly sampling one already
represented component. That trade-off is desirable when the scientific goal is
to find distinct high-value regions rather than nearby members of a known
series, but it is not an improvement in conventional entity-level hit rate.
An earlier multiplicative local-gate variant failed: its external AUC20 was
0.96 versus 69 for static entity consensus, showing that rewarding target OOD
distance can erase rather than refine source evidence. The resulting design
rule is to admit sources globally, preserve their ranks, and use OOD or
diversity to allocate a constrained exploration budget, not to multiply away
the proposal.

The failed adaptive policies explain why the borrowing mechanism matters
(Fig. 5c). Composition novelty was worse than random in the complete external
pool, although it improved hard-OOD AUC20 by 8.32 (6.12–10.26; Holm p=0.0008).
Adding target-mean steering reduced hard-OOD AUC20 by 3.86 (−5.45 to −2.30).
OBELiX, ESTM, and multisource residual increments all failed at least one of the
statistical, practical, consistency, first-hit, recall, and two-scope gates.
Thus a useful static proposal did not become useful merely by injecting it into
a weak target-refitted policy.

The safety gate nevertheless suppressed unrelated sources (Fig. 5b). Every
wrong-source admission/weight guard passed; real neighbors were admitted in
35.5% of steps with mean weight 0.168, compared with 16.8% and 0.063 for the
three controls. This admission ordering is not source skill: source out-of-fold
R² was 0.065 for OBELiX and 0.257 for ESTM, while the wrong-domain OCx control
had the highest value, 0.543. The evidence therefore supports preserving and
testing physically nominated proposals, not declaring them credible from the
gate alone.

### 3.10 Credibility, complementarity, abstention, and family-first allocation make borrowing actionable

The combined evidence identifies how neighboring knowledge can be made useful.
First, represent the recipient state before transferring a donor: processing,
phase, and test conditions converted an unusable composition-only alloy edge
into a positive-utility OOD predictor. Second, qualify the source rather than trust adjacency: KIT survives grouped
cross-fitting and source scrambling, while Caltech wrong-source guards suppress
unrelated inputs. Third, match the mechanism to the endpoint: a learnable soft
prior improves KIT prediction, whereas fixed source ranks retain Caltech OOD
signal that target-refitted residual policies lose. Fourth, preserve neighbors
as separate proposals. OBELiX and ESTM recover different high-value Caltech
compositions, and their portfolio covers more of the top region than either
source alone. Fifth, match the discovery unit to the scientific objective:
family-first allocation converts repeated within-series hits into broader
coverage of independently linked target regions. Sixth, abstain rather than
force borrowing when wrong-source or shuffled controls are competitive. Seventh,
treat every shortlist as a falsifiable hypothesis source,
not a discovery claim: composition or mechanism rationales must be recorded
before target reveal and tested against novelty, random, and wrong-source
controls.

This makes mutual scientific inspiration operational without assuming symmetry:
each source→target direction is a separate, falsifiable proposal, and reciprocal
borrowing emerges only when the reverse direction independently passes the same
gates.

Conceptually, neighborhood borrowing addresses OOD knowledge scarcity by
transferring a constrained prior or candidate ordering, not by pretending that
the target labels already span the region. Its benefit need not appear as a
higher global fit: it may instead appear as earlier recovery of distinct high-
value components or as fewer target labels required to reach a fixed error.
These are separate endpoints and are tested separately here.

Experimental-first is therefore not a synonym for training on experimental
labels. It changes the object being transferred and the conditions under which a
transfer is accepted. A source proposal carries its material identity,
experimental provenance, endpoint, and falsifier; a target result is interpreted
only after leakage, wrong-source, practical-utility, and transport checks. This
is an operational response to the data-only illusion: chemical plausibility
nominates a borrowing edge, but experimental evidence is allowed to reject it.
The CALiSol, Matbench, and sequential-acquisition nulls are consequently part of
the method rather than exceptions removed from an average score.

These results establish proof of feasibility at three distinct levels.
Qualified neighboring information materially improves few-shot prediction;
state-matched, cross-fitted endpoint borrowing retains positive utility in a
chemically held-out OOD region; and external neighbor rankings can generate
complementary OOD shortlists after formula and article leakage removal. The
artifact-gated map makes selectivity actionable by locating where borrowing
helps, fails, reverses, or changes with the endpoint. The MPEA state-matched
result remains post-selection robustness evidence, while the integrated
portfolio was frozen for outcome-unseen testing rather than promoted from its
Caltech development performance.

### 3.11 Outcome-unseen validation turns selectivity into a falsifiable result

The reverse Starrydata target produced a small directional prediction effect,
not a validated rescue. In the primary n=30, ExtraTrees, composition-only, far-
OOD cell, the hierarchical ionic-consensus effect was +0.88% [0.02,1.77%]
relative RMSE. Its one-sided bootstrap p value was 0.0237, but Holm adjustment
gave p=0.071. The contrast with the best matched control was +0.75%
[-0.14,1.66%], Holm p=0.096, and the contrast with the same-domain ESTM source
was -0.10% [-1.20,1.03%]. The augmented model's mean R² was -0.485. Five of six
learner-representation cells were directionally positive, so the frozen
robustness envelope passed; multiplicity, source specificity, and absolute-
utility gates did not. The correct map status is therefore directional but
unresolved, not a positive reverse-transfer edge.

The same boundary appeared at the exploration endpoint. Starrydata CCA family-
first AUC20 was 41, below 71 for the same-domain ESTM policy, and its source-rank
permutation p value was 0.546. None of the seven policy contrasts survived Holm
correction. The three source-derived scientific hypothesis cards also failed:
their Holm p values were 0.445, 1.0, and 1.0. A predictive direction therefore
did not imply a useful shortlist or a confirmed target-side scientific
hypothesis.

The four-plate TRI OER programme rejected the proposed second-family borrowing
edge. The random-effects all-neighbor effect was -0.079%
[-0.313,0.155%], Holm p=1.0, and only one of four plate effects was positive.
All-neighbor borrowing was 1.25% worse than the best control
[-1.75,-0.75%], and every plate had negative absolute R² (-0.111 to -0.186).
ExtraTrees and Random Forest changed sign with representation, whereas both
Ridge effects were negative; the robustness gate failed. All seven exploration
contrasts and all three prewritten hypothesis cards had Holm p=1.0. Retaining
these unfavorable outcomes is the operation of the method, not a failed attempt
to find a positive example.

Across the two outcome-unseen targets, the random-effects mean was +0.30%
[-0.62,1.22%], with I²=76.7%; only one target was directionally concordant and
neither passed its complete prediction gate. Thus, the Caltech-derived
integrated strategy is not a generally validated transfer rule, and independent
positive predictive replication remains unsupported. More importantly for the
paper's central thesis, outcome-unseen evidence converts “selective” from a
post-hoc qualifier into a tested result: neighboring-domain utility varies by
edge, direction, representation, and decision endpoint, and the same map that
admits the KIT edge abstains on Starrydata and rejects the TRI edge. Figure 6
summarizes these complete gates and preserves all six failed hypothesis cards.

### 3.12 Cross-program synthesis identifies the missing gate variable

The leave-one-program benchmark shows that adjacency is useful but insufficient
for an operational borrowing policy. The CCA meta-gate borrowed on 17 of 20
tasks across 11 of 13 programmes and achieved a mean programme-level relative
RMSE gain of 1.58% [-0.23%,4.27%]. Only one of 17 admitted decisions selected a
clearly harmful edge, so the policy was neither indiscriminate borrowing nor
trivial abstention. However, it retained only four of ten tasks with an
available clearly beneficial edge. Its contrasts with always selecting the most
credible source (+1.42 percentage points [-0.23,4.08], Holm p=0.270) and never
borrowing (+1.58 [-0.23,4.29], Holm p=0.270) both failed the frozen superiority
family. Adjacency alone was numerically stronger (+1.80% [-0.19%,4.52%]) and
retained five of ten available clear benefits.

The failure is structured rather than a generic absence of transferable
signal. Global source OOF skill was a poor proxy for local borrowing value, and
the fitted meta-layer made almost the same decisions as the fixed adjacency and
credibility rule. Two failures occurred between sources inside the same nominal
neighborhood: for BIRDSHOT hardness the gate selected alloy YS (-5.14%) rather
than alloy UTS (+6.84%), and for polymer melting temperature it selected Tg
(-0.71%) rather than crystallization temperature (+0.34%). Conversely, global
source-skill filtering excluded clearly beneficial polymer tensile and
photoswitch edges. The map therefore already supplies a useful first-order
neighborhood prior, but the missing policy variable is candidate-local and
endpoint-specific applicability. This result motivates a two-stage strategy:
use provenance, matched controls, and physical compatibility as a
contraindication gate, then rank admitted sources using local source support,
target novelty, calibrated uncertainty, and cross-source agreement. That
architecture is frozen before selection of a new temporal or prospective
programme; a target-specific execution appendix must be frozen before outcome
access. It is not tuned here to rescue the present benchmark.

### 3.13 A protected temporal programme nominates continuous borrowing over hard gating

The multi-stage battery programme provided a harder temporal test because its
Stage 1 source measurements and source predictions preceded the Stage 2 target
release (Fig. 7a). The frozen target comprised 138 Stage 2 cells in 23 condition
groups. One z10 cycle-aging group lacked the required terminal `AT_T23` file in
all three member archives. The release audit therefore retained 135 endpoints
but declared the frozen 23-group primary non-evaluable rather than replacing the
endpoint or silently dropping the condition.

The disclosed 22-group sensitivity did not validate the hard-gated CCA-v2
policy. CCA-v2 improved equal-stratum condition RMSE by 3.47%
[-0.59%,9.30%] relative to endpoint-matched target-only, but was 2.80% worse
[-8.79%,5.06%] than the continuous adjacency-only feature. Its training-only
gate admitted only 4/22 held-out groups: 4/8 calendar groups and 0/14 cycle
groups (Fig. 7d). Thus the attempt to prevent negative transfer removed every
cycle-aging opportunity and did not improve the source-to-policy conversion.

An explicitly outcome-guided diagnostic then isolated the simpler mechanism
(Fig. 7b,c). The precomputed continuous Stage 1 prediction reduced equal-
stratum condition RMSE by 6.12% [2.56%,9.16%] relative to target-only (Holm
p=0.0108), by 6.85% [3.50%,10.04%] relative to a wrong-property source
(p=0.0036), by 11.72% [1.72%,24.02%] relative to a shuffled source (p=0.0356),
and by 7.47% [3.42%,10.75%] relative to matched random features (p=0.0140).
Seven of eight calendar and ten of 14 cycle condition groups improved; held-out
R² was 0.334 and 0.462, respectively. The upper-quartile source-distance effect
was heterogeneous (-1.24% calendar and +5.56% cycle), preserving the central
claim that borrowing remains condition-selective rather than distance-
universal.

Both source-inspired condition cards passed in the written direction
(Fig. 7e): calendar retention was 93.51 for the lead versus 96.83 for its
matched control, and cycle retention was 88.93 versus 91.75. These card results
show how a neighboring prediction can generate a falsifiable condition-level
proposal, but they are not independent mechanistic discoveries. Because the
continuous policy was selected after examining the 22-group outcomes, the
result nominates a precise next strategy—qualify the source upstream, retain its
prediction continuously, and compare it with matched false-source controls—
rather than rescuing the failed primary. The temporal design therefore adds a
constructive method result to the map: hard abstention can be too brittle, while
continuous credible-source borrowing can preserve useful OOD information.

## 4. Limitations

The material predictive effect is established in a simulated label-poor slice
of one electrolyte campaign, while Caltech establishes a distinct retrospective
external OOD-proposal endpoint. CALiSol does not reproduce the KIT effect across
experimental articles, and neither outcome-unseen target passed its complete
prediction gate. Starrydata shows only a small directionally positive relative
effect despite negative absolute R², while TRI is null and sometimes harmful.
These two targets are sufficient to test the frozen strategy but not to estimate
a population-wide probability that a nominated neighboring edge will transfer.
Field-wide predictive rescue and reciprocal transfer remain unsupported. The
data-poor budgets are retrospective, and no prospective laboratory campaign was
performed.

The systematic OOD benchmark broadens this boundary to eight targets and 40
real edges, but it was designed after related component outcomes were known. It
uses one outcome-free feature-distance partition per target and a deliberately
simple donor-as-feature mechanism. It therefore rejects generic soft-feature
injection within the tested representation and learner envelope; it does not
prove that every mechanistic representation, domain-adaptation objective, or
causal transfer strategy must fail. Because no designated edge achieved
positive augmented OOD R², relative error reductions cannot be interpreted as
deployment-ready OOD prediction. The larger effects among non-designated edges
were inspected in the same formal run and remain exploratory nominations for a
new external target rather than additional confirmations.

The state-matched MPEA analysis resolves one failure mode of that benchmark but
does not remove its evidence boundary. Experimental-state features and the
UTS-feature architecture were selected after earlier alloy outcomes were
available, and the Balam run resampled the same experimental programme. Its
two-way cluster-bootstrap Q4 gain is robust and its pooled Q4 R² is positive,
but the R² interval and Q4-minus-Q1 interval both cross zero. The result
therefore establishes a reproducible mechanism on this programme, not
independent cross-database replication, field-wide OOD superiority, or
prospective discovery. A new processing- and test-state-resolved mechanical
programme is required for that upgrade.

The OBELiX fixed-ranking result is also retrospective. Its hard-OOD subset is
exploratory because the whole-pool direction was known before that subset
design was frozen. The sequential campaign was prespecified given prior fixed-
ranking inspection, not independently confirmatory. Its null applies to the
tested composition representation,
ExtraTrees and Random-Forest learners, mean-plus-standard-deviation UCB score,
40-acquisition budget, and one experimental target. Uniform random acquisition
outperformed both UCB policies, but the present trajectories cannot identify
whether the failure arose from mean ranking, ensemble-spread calibration, or
iterative refitting. Alternative acquisition functions or representations
require a new design and cannot retroactively rescue this campaign.

The Caltech benchmark is likewise retrospective and represents one external
ionic-conductor target. Its verified null applies to cross-validated residual
rank injection and the tested target-mean steering, not every possible way of
using neighboring domains. The same-property OBELiX source model was weak on
its own grouped out-of-fold test (R²=0.065), while the OCx wrong-domain control
had the highest source out-of-fold R² (0.543); the target backbone was also weak
in the complete external pool. The adaptive null therefore cannot by itself
separate source weakness from policy-conversion failure. The stronger static rankings have no frozen
source-attribution decision family or independent-target interval, and the
round-robin and consensus portfolios were created after outcome inspection.
The CCA family-first policy and its discovery-unit analysis were also motivated
after those outcomes and after a local multiplicative gate failed. Connected
formula/DOI/ICSD components remove obvious repeated evidence but are not
mechanistic chemical families. Their max-value endpoint asks whether a region
contains at least one excellent member; the mean-value sensitivity asks a
different question. The subsequent Starrydata and TRI programmes supply that
outcome-unseen test and do not validate CCA as a general acquisition policy.
They also cannot support prospective acceleration, population-level generality,
or new-science discovery.

The outcome-unseen programme was internally frozen and outcome-blind for the
target construction, rankings, and cards, but it is still retrospective: target
values already existed in deposited datasets. The Starrydata directional
interval does not survive the full multiplicity family, does not beat the same-
domain reference, and coexists with negative absolute R². The TRI null could
reflect absent transferable structure, inadequate source quality, or the tested
composition representations; post-outcome model changes cannot distinguish
these explanations confirmatorily. Testing more retrospective targets after
seeing these outcomes would risk target shopping. A stronger claim now requires
a genuinely temporal or prospective target, not another favorable reanalysis.

The leave-one-program CCA synthesis removes each target programme's outcomes
from its outer fit, but the feature family and gate architecture were chosen
after the component studies were known. Its positive point estimate and low
clear-harm count therefore diagnose reusable structure; they do not validate a
general gate. In particular, the learned layer did not outperform adjacency
alone and missed six of ten available clear benefits. Candidate-local support,
endpoint compatibility, and calibrated abstention require a new outcome-unseen
programme under the post-result CCA-v2 protocol.

The temporal battery programme is protected against Stage 2 outcome leakage,
but its frozen primary is non-evaluable because one complete condition group
lacks the required terminal endpoint. The favorable 22-group continuous-
borrowing result was identified after the coverage failure and after inspecting
post-release policy outcomes. It is therefore a reproducible method-development
nomination, not an independent confirmation. Its condition groups belong to one
battery programme, the hard-OOD effects differ between calendar and cycle
aging, and the two directional condition cards do not establish mechanisms.
A new complete outcome-unseen programme must freeze the continuous policy and
matched controls before target outcomes to test generality.

The 37.35% target-label saving is a point estimate from an interpolated
learning curve. Its post-outcome conditional interval crosses the 30%
practical gate. Consequently, the robust positive result is the error and
absolute-utility improvement; the precise fraction of labels saved remains
uncertain.

The n=30 target-only model already has R²=0.739 and is usable. “Local task
rescue” is retained only as an operational table status under the internally
frozen conjunctive rule; in prose, the supported claim is a material reduction
in few-shot error and improved sample efficiency within one campaign.

Experimental-first does not mean experimentally complete. The normalized layer
retains reported context but cannot reconstruct unreported synthesis history,
instrument effects, operator choices, or metastable states. In the present
workflow, chemical knowledge enters source nomination, condition matching,
identity/provenance grouping, negative-control design, and source-derived
hypothesis cards; it is not claimed to be fully encoded in the predictive
representation.

The source-prediction feature is generated from the same composition variables
available to the target model. It can act as a learned nonlinear basis or
regularizer even without encoding a transferable physical mechanism.
Importance and rank therefore measure target-model use, not causation. The
tested envelope is narrow: Random Forest and ExtraTrees ensembles plus degree-
2 Ridge, using elemental fractions, one-hot descriptors, and eight additional
composition-distribution descriptors only where stated. Graph, SOAP/MBTR,
learned chemical embeddings, calibrated Gaussian-process surrogates, and cost-
aware acquisition were not evaluated. Such representations and learners might
change individual edges, especially in CALiSol, but they would need to be
designated before outcome inspection and would not retroactively change the
present decisions.

All design freezes in this study are internal, author-controlled, and self-
attested. They are not external preregistrations and should not carry that
epistemic weight. Designs frozen after inspection of a related endpoint are
described as prespecified given prior screening, not confirmatory.

The 20-resource cohort is heterogeneous but not exhaustive, and only 13
resources enter the common SQLite schema. That layer is not fully
unit-harmonized, and the generated database should not be redistributed until
source-specific terms and attribution requirements have been audited. Finally,
the Krug battery tests a specified statistical artifact; surviving it does not
establish one mechanism for compensation.

## 5. Conclusions

This work establishes an operational way to borrow knowledge across neighboring
experimental domains without assuming that adjacency guarantees transfer. The
Collective Experimental Data Index provides the experimental-first foundation:
rather than treating reported measurements as interchangeable labels, it
retains identity, conditions, provenance, and reuse constraints, then asks which
directed source signals survive explicit falsification. Provenance-aware cross-
fitting, wrong-source and shuffled controls, separate prediction and exploration
endpoints, independent source shortlists, matched controls, and an abstention
rule turn the resulting knowledge-borrowing map into a decision instrument.

The map identifies both where borrowing works and how the transfer object must
change with the endpoint. An adjacent experimental condition materially
improved few-shot KIT prediction. The systematic eight-target benchmark then
showed that generic donor-feature injection is not OOD repair: even the
strongest designated alloy edge improved ID and OOD similarly, and zero of eight
edges passed the full absolute-utility and OOD-specificity gate. Preserved
OBELiX and ESTM rankings nevertheless proposed complementary high-value Caltech
regions, while target-refitted residual policies and UCB destroyed that
advantage. Outcome-unseen testing found a small but incomplete Starrydata
direction and rejected the TRI OER edge; neither target passed the full gate and
the pooled effect was null and heterogeneous. Together, these results establish
an endpoint-matched strategy: use a qualified soft prior for local few-shot
prediction, preserve independent donor rankings or family-level portfolios for
OOD proposal generation, and abstain when neither survives its controls.

The contribution is therefore neither a grand-unified law nor a claim that
careful transfer always succeeds. It is a tested strategy for generating,
combining, rejecting, and falsifying cross-domain proposals under incomplete
scientific knowledge. The cross-program benchmark further shows that physical
adjacency is a useful first-order prior but that global source credibility
cannot replace candidate-local applicability; this turns the next improvement
into a specific, testable method rather than an open-ended model search.

The temporal battery benchmark adds the corresponding constructive strategy
update: its frozen primary exposed a structural coverage failure, hard CCA-v2
qualification over-abstained, and continuous Stage 1 borrowing was the only
policy that improved most complete condition groups while beating matched
false-source controls. That result is a candidate for independent confirmation,
not a universal success claim, but it shows that the map can improve the
borrowing mechanism rather than merely audit failures. Prospective discovery
acceleration and source-inspired new science remain a separate claim upgrade.

## Author contributions

`[Insert CRediT author-contribution statement after the author list is fixed.]`

## Conflicts of interest

The authors declare no competing interests. `[Author confirmation required.]`

## Data availability

The analysed-resource inventory, source lock, frozen analysis designs, compact
claim-bearing outputs, and figure source data are available in the public repository
`https://github.com/Yang1Bai/collective-exp-data-index`. Before submission, the
release used for this article will be archived and cited here as
`https://doi.org/[repository DOI]`. Training and test records are obtained from
the public source locations and exact revisions or file hashes recorded in the
source lock; their original licenses remain controlling. The generated SQLite
file is not redistributed by default because one normalized source has an
unresolved redistribution status and another is non-commercial. It can be
rebuilt locally from the pinned public sources. NIST ISODB is streamed from its
pinned public-domain archive and is not extracted.

## Code availability

All scripts required to validate the analysed-resource inputs, rebuild the local
snapshot, reproduce the analyses, regenerate the figures, and write the release
manifest are included in the repository. The archived release DOI and version
will be inserted before submission. The manifest records claim-bearing file
hashes, source revisions, database metadata, Python and package versions.

## Acknowledgements

`[Insert funding, institutional, computing, and contributor acknowledgements.]`

## Figure captions

**Figure 1 | Analysed experimental resources and evidential scope.** **a,**
All 20 resources that enter a numerical analysis, grouped by directed role. The
matrix identifies 15 donors, 16 recipients, 12 resources used in both roles,
and one artifact-gate-only resource; layer codes distinguish 13 normalized
resources (N), six frozen external resources (E), and one streamed
analysis-only resource (A). Roles are task-derived and do not imply that a
candidate donor passed the borrowing gates. **b,** All 96,184 measurements in the 13-resource
normalized core, colored by scientific family and plotted on a logarithmic axis
to retain the full 599--26,025 resource range. Exact counts are printed; the
snapshot contains 230 distinct properties and 29,516 canonical entities. **c,**
Empirical denominators for the 20-resource cohort, 19 transfer-active resources,
97 evaluated edges, 20 target tasks, and 13 programme clusters. **d,** Major claim-bearing programmes across coefficient
transport, few-shot prediction, OOD screening, and sequential or temporal
endpoints. Symbols retain gate-passed, directional, unresolved or conditioned,
method-development, and null, harmful, or non-evaluable outcomes. Bold blue rows
identify four role-defining examples selected for distinct validation roles, not
four favorable outcomes. Source data are provided with the release.

**Figure 2 | Artifact-gated evidence for selective knowledge borrowing.**
**a,** A strong log–log UTS–YS calibration in Borg fails unchanged in the
independent BIRDSHOT campaign despite zero exact composition overlap. **b,**
Relative held-out RMSE effects for the KIT primary edge, distance
controls, and shuffled placebo, contrasted with the paper-disjoint CALiSol
primary, 0 °C control, and shuffled placebo. Horizontal lines are 95%
hierarchical bootstrap intervals; positive values favor borrowing and the red
dashed line is the frozen 5% practical gate. **c,** KIT target-only learning
curve and augmented n=30 error. Monotone interpolation gives a point estimate
of target-only n=47.9, or 37% of equivalent target labels saved; a post-outcome
formulation/subset bootstrap spans 22–50%. **d,** Pooled
ISODB isosteric heat–intercept relation. The association survives the simple
independent-parameter Krug null but requires adsorbate-family intercepts. Full
split, resampling, and test definitions are given in Methods.

**Figure 3 | Generic donor injection fails, whereas state-matched borrowing
repairs a selected OOD programme.** **a,** Frozen comparison: complete
development features define outcome-free Q1 in-distribution and Q4 OOD
evaluation groups; paired target-label draws fit target-only and
donor-augmented models while wrong and shuffled donors remain as controls.
**b,** Relative Q4 RMSE gain for the eight designated donor–recipient edges.
Points are means and horizontal lines are hierarchical 95% intervals over
target-label repetitions and intact evaluation groups. The red line marks the
5% practical threshold. **c,** Q4 versus Q1 gain for all 40 real edges. The
diagonal distinguishes OOD-enriched from equally strong or stronger
in-distribution effects; designated edges are outlined. **d,** Conjunctive gate
audit for all eight designated edges, the seven-programme mean, and the three
cross-database designated edges. A complete pass requires practical and
statistical improvement, repeat and learner robustness, superiority to wrong
and shuffled controls, positive absolute OOD R², positive OOD specificity,
identity exclusion, and Holm-adjusted significance. No designated edge passes
the complete gate. The protocol was frozen after related component outcomes had
been inspected and is therefore systematic method development, not independent
prospective confirmation. **e,** State-matched alloy borrowing contract. Entire
elemental systems are held out, the UTS donor excludes the held target fold and
all evaluation systems, and its cross-fitted prediction is appended to the
state-aware YS model only after leakage audit. **f,** Q4 RMSE effects of the
real UTS feature, its architecture-matched shuffled counterpart, and their
paired difference. The real feature reduces RMSE by 9.21% (95% CI,
4.43–14.37%) and exceeds the matched shuffle by 9.47 percentage points
(4.80–14.34%); pooled augmented Q4 R² is 0.103. **g,** Real-donor effects in Q1
and Q4 and their paired difference. The positive Q4 effect persists in the
most distant region, but Q4-minus-Q1 is not significant. **h,** Q4 information
ladder: state-aware features relative to composition-only, predicted UTS
relative to state-only, and measured UTS as an auxiliary-measurement ceiling.
Intervals in **f,g** are 100,000-replicate two-way cluster bootstraps over 59
elemental systems and 60 frozen model-by-draw runs; state and measured-ceiling
intervals in **h** are descriptive t intervals across the 60 runs. Panels
**e–h** are a post-selection, same-programme robustness analysis and do not
constitute independent prospective confirmation.

**Figure 4 | Fixed OOD screening and sequential discovery are distinct
endpoints.** **a,** Mean fraction of the OBELiX candidate pool screened before
the first true top-5% hit under target-only ranking and ranking augmented by the
frozen thermoelectric prediction. The official-test result is directional but
fails the practical and repeat-consistency gates; the farthest-40% subset is
exploratory. Text gives the paired-bootstrap 95% interval for percentage points
saved. **b,** Experiments saved relative to target-only ExtraTrees UCB in the
official and hard-OOD pools. Horizontal lines are paired-bootstrap 95%
intervals; the dashed red line is the frozen five-experiment gate. The
thermoelectric and shuffled priors do not pass the sequential improvement
gates, whereas uniform random acquisition crosses the gate. **c,** Empirical
probability of at least one true top-5% hit versus official-test acquisitions
over 100 paired seeds. At the 40-acquisition budget, target-only UCB,
thermoelectric-prior UCB, and random acquisition were censored in 40%, 41%, and
8% of campaigns, respectively. The sequential experiment is retrospective on a
held-out pool and is not a prospective laboratory campaign.

**Figure 5 | Qualified neighboring rankings remain useful when adaptive model
augmentation fails.** **a,** Operational workflow separating qualification,
preserved complementarity, continuous borrowing, family-first allocation, and
abstention. **b,** Source admission rate, mean weight, and source out-of-fold
R²,
averaged across the complete Caltech external-candidate and hard-OOD scopes,
for the two real neighbors and three wrong controls. The red dashed line is the
frozen 0.20 wrong-source admission ceiling. **c,** AUC20 gains for OBELiX,
ESTM, and multisource residual policies relative to the state-matched
target-only policy. Circles and squares denote the complete external and
hard-OOD scopes; horizontal lines are paired-bootstrap 95% intervals. No
adaptive source increment passes the frozen statistical, practical,
consistency, first-hit, absolute-recall, and two-scope gates. **d,** Static
ranking AUC20 for prespecified real-neighbor, shuffled, random, mechanical, and
catalysis policies. Labels above the real-neighbor bars give recall20 as
absolute counts: 2/8 and 3/8 externally, and 3/3 in the n-limited hard-OOD
scope. This is prespecified retrospective external evidence; source-attribution
contrasts were not in the frozen primary family, and repeated
candidate seeds are not independent-target uncertainty. **e,** Distinct-group
AUC20 for the wrong-source, entity-consensus, and family-first policies.
Family-first obtains AUC20=60 externally and 39 in hard OOD, with conditional
paired-shuffle p=0.002 and 0.003. This panel is outcome-informed method
development on the same fixed target pool.

<!-- Legacy family-first decomposition caption retained for supplementary reuse:
proposals.** **a,** The credibility–complementarity–abstention workflow admits
leakage-audited sources, preserves independent ranks, allocates the first pass
across connected identity/provenance components, and retains target-only
fallbacks. OOD distance constrains exploration rather than multiplying the
source score. **b,c,** Distinct-component AUC20 in the 144-entity external pool
(63 components) and 58-entity hard-OOD pool (36 components). Grey bands and
dashed lines are the 2.5–97.5% range and mean from 5,000 independently shuffled
OBELiX/ESTM rank pairs. The family-first consensus obtains AUC20=60 and 39,
versus 6 and 18 for the wrong-source pair. These are conditional candidate-pool
randomization results, not external-target intervals. **d,** Family-first
allocation increases distinct top-component recall but reduces entity top-5%
recall because it avoids repeated selections from one connected component.
Components join shared canonical formula, DOI, or ICSD identifiers. The policy
was developed after Caltech outcomes were observed and is method-development
evidence; its subsequent outcome-unseen tests are shown in Fig. 6 and do not
support prospective discovery. -->

**Figure 6 | Outcome-unseen validation resolves direction, heterogeneity, and
abstention.** **a,** Primary relative RMSE effects for the Starrydata reverse-
transport and four-plate TRI OER targets, with 95% intervals defined at the
independent evaluation-block or plate level; the two-target random-effects mean
is shown separately. Positive values favor borrowing. Neither target passes its
complete prediction gate. **b,** Frozen gate matrix. Starrydata passes the
directional interval and learner-representation robustness gates but fails Holm
multiplicity, positive absolute R², source specificity, exploration, and
hypothesis confirmation. TRI fails every complete gate. **c,** Relative RMSE
effects across three learner families and two outcome-free representations.
Starrydata is positive in five of six cells; TRI changes sign with representation
and is negative for both Ridge cells. **d,** Holm-adjusted p values for three
source-derived hypothesis cards per target. None is confirmed. The full
programme retained all sources, controls, plates, policies, and cards after
outcome access; Job 70888 and portable replay were verified from frozen hashes.

**Figure 7 | Continuous neighboring-condition borrowing survives where a hard
gate over-abstains.** **a,** Protected temporal design from 2021 Stage 1 source
measurements to 2023 Stage 2 target outcomes. Three cells in one z10 condition
lack the terminal AT_T23 endpoint; the frozen 23-group primary is therefore
non-evaluable, leaving 135 cells in 22 complete groups for a disclosed
sensitivity. **b,** Equal-stratum relative condition-RMSE gain of the continuous
Stage 1 prediction versus target-only, wrong-property, shuffled-source, and
random-feature controls. Horizontal lines are post-release group-bootstrap 95%
intervals; text gives Holm-adjusted one-sided sign-flip p values. **c,** Gain
versus Stage 1 source-condition distance for eight calendar and 14 cycle groups.
Outlined points are in the type-specific upper source-distance quartile; 17/22
groups improve, but hard-OOD effects differ by aging type. **d,** Training-only
CCA-v2 admission coverage: 4/22 overall, 4/8 calendar, and 0/14 cycle groups.
**e,** Both prewritten source-inspired lead-versus-control condition cards pass
in the predicted direction. Panels b–e are explicitly outcome-guided
post-release method development: they nominate continuous borrowing for a new
outcome-unseen programme and do not rescue the non-evaluable primary.

## Table 1 | Claim hierarchy and frozen outcomes

| Evidence layer | Directed relation or test | Relative RMSE effect or transport metric | Absolute utility | Frozen interpretation |
|---|---|---:|---:|---|
| Cross-program gate development | CCA meta-gate, 13 leave-one-program outer tests | +1.58% [-0.23,4.27]; Holm p=0.270 for both primary superiority decisions | 11/13 programme coverage; 1/17 clearly harmful admissions; 4/10 clear benefits retained | Adjacency is a useful first-order prior; global edge metadata does not yet select benefit reliably |
| Coefficient transport | Borg UTS–YS line → BIRDSHOT | external R²=−3.006 | failed | Strong source calibration is not transportable |
| Internal screen | Borg UTS prediction → Borg YS, n=30 | +6.46% [3.69,13.03]; Holm p=0.005 | R² −0.149→+0.025 | Internally selected candidate; not externally replicated with positive utility |
| Independent rolling time | Borg UTS prediction → BIRDSHOT YS | +4.30% [3.36,5.51]; p=0.003 | R² remains negative | Directional replication below practical gate |
| Independent official folds | Borg UTS prediction → Matbench YS | −1.23% [−15.88,2.48]; p=0.794 | primary R² negative | Independent null boundary |
| Within campaign | KIT −20→−30 °C conductivity | +15.02% [8.61,21.10]; p=0.001 | R² 0.739→0.811; 37.35% saved point estimate [21.84,49.91]% diagnostic interval | Material few-shot improvement; operational local-task-rescue status under internal point rules |
| Paper-disjoint | CALiSol −30→−40 °C conductivity | +1.61% [−2.14,4.21]; fixed-subset p=0.004 | R² −0.049→−0.014; 16.9% saved | Cross-article borrowing unresolved |
| Systematic feature-distance OOD benchmark | Eight designated edges across seven programmes | programme mean +0.92% [−0.35,2.92]; strongest UTS→YS +6.65% [3.53,14.02], Holm p=0.0008 | 0/8 designated edges and 0/3 cross-database edges pass; all augmented OOD R² non-positive | Generic donor injection does not establish OOD repair; the strongest alloy gain is not OOD-specific |
| Fixed OOD screening | Thermoelectric ZT prior → OBELiX official test | fraction screened 12.08%→9.98%; 2.09 percentage points saved [0.94,3.45]; Holm p=0.0003 | fails 25% effect and 80% consistency gates | Directional OOD screening signal, not rescue |
| Sequential OOD discovery | Thermoelectric ZT prior → OBELiX official-test UCB | 0.25 acquisitions saved [−1.30,1.82]; p=0.389 | all improvement gates fail; random 15.50 vs target-only 24.34 | Prespecified after fixed-ranking inspection; tested UCB policy underperforms random |
| External adaptive policy | OBELiX/ESTM priors → Caltech ionic-conductor acquisition | all frozen source increments fail in at least one scope | wrong-source guards pass; source OOF R²: OBELiX 0.065, ESTM 0.257, OCx control 0.543 | Verified adaptive null with weak-source/target confound; prespecified static signal supports retrospective OOD feasibility |
| Outcome-informed family-first exploration | OBELiX/ESTM ranks to distinct Caltech identity/provenance components | external/hard-OOD AUC20 60/39; shuffled-rank conditional p=0.0020/0.0030 | 4/4 external and 2/2 hard-OOD top components recovered by 20 | CCA method development; trades repeat entity hits for broader regions; not confirmed by the outcome-unseen policy tests |
| Outcome-unseen reverse transport | OBELiX/Caltech ionic priors → Starrydata thermoelectric ZT | +0.88% [0.02,1.77]; Holm p=0.071 | R²=-0.485; +0.75% vs best matched control [-0.14,1.66] | Directional but unresolved; fails complete prediction, specificity, exploration, and hypothesis gates |
| Outcome-unseen second family | OER/ORR/OCx priors → four TRI OER plates | -0.079% [-0.313,0.155]; Holm p=1.0 | all four plate R² values negative; -1.25% vs best control [-1.75,-0.75] | Independent null/harm boundary; all exploration and hypothesis-card families fail |
| Across-target synthesis | Starrydata + TRI target-level effects | +0.304% [-0.617,1.225]; I²=76.7% | neither target passes its full gate | General neighboring-domain transfer is unsupported; edge-selective map and abstention are supported |
| Protected temporal method development | Stage 1 battery degradation prediction to Stage 2 condition groups | continuous borrowing +6.12% [2.56,9.16] vs target-only; Holm p=0.0108 | 17/22 groups improve; hard gate admits 4/22 | Frozen 23-group primary non-evaluable; continuous policy is an outcome-guided nomination for independent confirmation |

## Assumptions or missing inputs

- Author names, affiliations, corresponding-author details, funding, CRediT
  roles, and acknowledgements were not available and are not inferred.
- A repository archival DOI and release tag are still required.
- The 14 July 2026 *Digital Discovery* guidelines identify this work as a Full
  paper, require a 50–250-word abstract, and require persistent code/data
  deposition. Final typesetting should use the current RSC article template.
- References are represented by BibTeX keys and should be rendered in RSC
  numeric style during typesetting.
