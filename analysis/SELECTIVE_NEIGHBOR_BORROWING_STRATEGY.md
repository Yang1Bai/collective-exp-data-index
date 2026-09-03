# Selective neighborhood-borrowing strategy

## Scientific purpose

Target-only models are weakest in underobserved and OOD regions, where target
labels and mechanistic guidance are sparse. Neighboring experimental domains can
contain useful but incomplete views of the same material space and can therefore
supply constrained priors or candidate orderings for those regions. The goal is
not to force these views into one universal model. It is to preserve each
qualified source as a distinct, testable proposal about where useful target
behavior may occur, then combine complementary proposals without allowing a weak
target surrogate or one harmful source to erase the signal.

“Mutual inspiration” is operationalized as a set of directed, falsifiable
source→target proposals rather than an assumed symmetric relationship. As more
targets are evaluated, the same protocol can test the reverse directions and
assemble a reciprocal network of experimentally supported borrowing edges.

The strategy is an outcome-informed methodological synthesis of the KIT,
OBELiX, and Caltech results. Its components have proof-of-feasibility evidence
in the current study. Its first outcome-unseen Starrydata and TRI tests define
directional and null boundaries rather than a positive policy replication. The
post-result CCA-v2 policy must therefore be frozen on a genuinely temporal or
prospective target before it can support acceleration or new-science claims.

## Experimental-first unit of borrowing

The reusable object is not a context-free composition–property row. It is a
reported measurement linked, where available, to canonical and raw material
identity, synthesis or formulation descriptors, measurement conditions,
article or campaign provenance, identifiers, quality flags, and reuse terms.
Fields that were not reported remain missing rather than being inferred from a
neighboring source.

Chemical knowledge has four explicit roles: nominate a plausible directed
source→target relation before target outcomes; define condition, identity, and
provenance exclusions; construct physically meaningful wrong-source controls;
and write a source-derived hypothesis card for each proposed target region.
Chemical plausibility is not an acceptance criterion by itself. The edge must
still survive the statistical, transport, utility, and endpoint gates below.
This separation prevents experimental labels from becoming another data-only
representation stripped of the context that made them scientifically useful.

## CCA family-first policy

The executable exploration policy has four named decisions:

1. **Credibility:** admit a source only after identity/provenance leakage checks,
   grouped source/target evidence, and wrong-source or shuffled controls. High
   source-only RÂ² is not an admission criterion by itself.
2. **Complementarity:** retain every admitted source as an independent rank.
   Use rank consensus for joint support and round-robin allocation for unique
   proposals; never let a weak target surrogate erase the original lists.
3. **Abstention:** give an unqualified or harmful source zero allocation and
   preserve composition novelty and uniform sampling as target-only safety
   channels.
4. **Family-first exploration:** traverse the portfolio once while taking only
   one representative from each outcome-free identity/provenance or predeclared
   composition-family component. Revisit a component only after the breadth
   pass. Treat OOD distance as a constrained budget or reporting variable, not
   a multiplicative reward that can overwhelm source evidence.

This policy deliberately optimizes discovery breadth. It can lower ordinary
entity-level recall by refusing to count several nearby members of one series
as several independent discoveries. That is a feature when the objective is to
locate distinct regions for mechanistic follow-up, not a claim that every ML
metric improves.

## Strategy

### 1. Declare the neighborhood before target outcomes

Each source→target relation must be justified from shared property physics,
transport mechanism, chemistry, experimental condition, or representation.
Outcome-free adjacency nominates a source; it does not establish usefulness.
Wrong-domain and shuffled sources are declared at the same time.

### 2. Qualify source signal without leakage

Source models are evaluated out of fold under the relevant material, article,
or time grouping. Exact target compositions and target provenance groups are
excluded from source fitting. A source is retained only if it has measurable
source skill or target-fold incremental information and does not reproduce the
gain under source-label shuffling. These checks distinguish reusable signal
from direct retrieval and parameter-estimation artifacts.

### 3. Match the borrowing mechanism to the endpoint

For few-shot prediction, the cross-fitted source prediction is a learnable soft
prior whose target weight can shrink to zero. For OOD exploration, each source
is preserved as an independent rank or shortlist rather than being forced
through a weak target-mean or uncertainty model. Prediction, fixed screening,
adaptive acquisition, and hypothesis discovery receive separate decisions.

### 4. Preserve complementary neighbors as a portfolio

Qualified neighbors retain separate ranked candidate lists. Acquisitions are
allocated by round-robin shortlist interleaving or rank consensus, with
composition novelty and uniform random sampling retained as target-only safety
channels. A neighbor is retired only after observed target labels demonstrate
harm; weak early evidence shrinks its allocation rather than changing its
scientific direction post hoc.

### 5. Require source-specific and safety comparisons

The portfolio is compared with random, composition novelty, each constituent
neighbor, and matched mechanical, catalysis, and shuffled-source portfolios.
Success requires incremental utility over the best valid target-only baseline,
practical separation from every wrong source, and consistency on an independent
target, article block, time block, or prospective campaign.

### 6. Convert a ranked proposal into a scientific hypothesis

Before revealing a shortlisted candidate's target outcome, record the source-
derived hypothesis: the composition family, structural motif, condition, or
mechanistic relation that motivated the candidate. Test it against a matched
target-only or wrong-source control. This step turns cross-domain ranking into
falsifiable scientific inspiration rather than retrospective storytelling.

## Evidence already demonstrated

| Strategy component | Current evidence | Interpretation |
|---|---|---|
| Cross-fitted soft prior can improve a target | KIT −20→−30 °C reduces RMSE by 15.02% [8.61%,21.10%] and raises R² from 0.739 to 0.811; all five folds and all three learners are positive | Material proof that qualified neighboring information can improve few-shot prediction |
| Neighbor signal can survive in external OOD ranking | Prespecified OBELiX and ESTM static rankings on Caltech recover 2/8 and 3/8 external top-5% entities and 3/3 hard-OOD entities after exact formula and DOI exclusions; wrong-domain static controls recover 0/8 externally | External retrospective feasibility of source-derived OOD proposals |
| Neighbor sources can be complementary | The post-outcome round-robin and consensus diagnostics recover 5/8 external top-5% entities and 3/3 hard-OOD entities, versus 2/8 and 3/8 for the individual neighbors | Proof of portfolio complementarity; method selection, not independent confirmation |
| Family-first allocation broadens OOD exploration | CCA family-first consensus recovers 4/4 distinct top external formula/DOI/ICSD components (AUC20 60 versus 47 for entity consensus) and 2/2 hard-OOD components in the first two acquisitions; wrong-source AUC20 is 6/18 and shuffled-rank conditional p=0.0020/0.0030 | Outcome-informed evidence that the discovery unit and allocation rule matter; entity recall falls because repeats are deferred |
| OOD scores can erase useful source evidence | A multiplicative local target-OOD/source-support/concordance policy falls to external AUC20 0.96 versus 69 for static entity consensus | Use OOD as a constrained exploration budget, not an automatic reward |
| Harmful sources can be suppressed | All six Caltech wrong-source admission/weight guards pass | Safety component works under the tested gate |
| Global edge metadata can be tested without target-program outcomes | Across 13 leave-one-program outer tests, CCA obtains +1.58% mean utility [-0.23%,4.27%], 11/13 programme coverage, and 1/17 clearly harmful admissions | Nontrivial safety screen, but not a validated benefit selector: Holm superiority fails and adjacency-only is numerically stronger |
| Naive policy conversion can destroy useful signal | OBELiX UCB is slower than random; Caltech residual injection adds no adaptive AUC20 utility despite stronger static neighbor rankings | Source ranking, target surrogate, uncertainty, and acquisition must not be conflated |

## Present claim

The study demonstrates that neighboring experimental domains can supply useful
and complementary predictive or OOD-ranking information, and it provides an
explicit strategy for qualifying, preserving, combining, and falsifying that
information. CCA family-first allocation additionally demonstrates how to turn
complementary ranks into broader distinct-region proposals. The current results establish component-level and retrospective
proof of feasibility. The cross-program gate further shows that physical
adjacency is a useful first-order prior, while global source skill and coarse
edge metadata are insufficient to select the best neighbor. They do not yet
establish that the integrated portfolio accelerates a prospective laboratory
campaign.

## Decisive next validation

Freeze the CCA-v2 local-applicability portfolio before downloading or revealing
outcomes for a genuinely temporal or prospective target. Its primary efficacy
comparison is against adjacency-only, with target-only superiority, clear-harm,
and nontrivial-coverage guards. For exploration, compare against random,
novelty, each neighbor, entity consensus, and matched wrong-source and shuffled-
source portfolios; report breadth and entity-repeat as separate endpoints.
Freeze the component rule, local-support calculation, abstention margin, and
source-derived hypothesis cards before target reveal. A positive result would
support the stronger claim that the strategy not only preserves neighboring
signal retrospectively but enables independent cross-domain exploration.

The completed outcome-unseen audit is in
`cca_family_first_outcome_unseen_protocol.json`. The post-result improvement is
specified in `CCA_GATE_V2_PROSPECTIVE_PROTOCOL.md` and architecture-frozen in
`cca_gate_v2_architecture.json`; a target-specific appendix remains mandatory.
It cannot be confirmed on the same 13-program development panel.
