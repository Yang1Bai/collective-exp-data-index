# Digital Discovery paper package — current evidence and claim boundaries

## Thesis

Target-only models are weakest where target-domain observations and mechanistic
guidance are sparse, especially in few-shot and OOD regions. Neighboring
experimental domains can supply partial and complementary priors—but only if
their experimental context is retained and each source signal is qualified,
matched to the decision endpoint, and protected against a weak target surrogate
or harmful source. The paper contributes an **experimental-first selective
neighborhood-borrowing strategy** plus an **artifact-gated knowledge-borrowing
map**.
Together they determine which source proposals improve prediction, survive OOD
screening, complement another neighbor, fail, or should be retired. This is an
operational response to the data-only illusion, not a claim that experimental
labels automatically encode chemical understanding.

The 2026-07-30 mixture-relation benchmark adds the first strong zero-shot
new-component example. A permutation-invariant relation trained on 10,407
electrolyte conductivity measurements from 22 salts predicts an external
LiAsF6 programme with raw \(R^2=0.629\) and \(\rho=0.871\), despite LiAsF6
being absent from the source. It reduces log-RMSE by 28.64%
[24.03%,33.52%] relative to temperature and concentration alone and beats a
chemistry-permuted source. Removing LiPF6 specifically worsens performance,
while the complete source outperforms LiPF6 alone; adjacency and diverse
mixture-state coverage are therefore complementary. The complete relation
beats state-only error and ranking in 7/9 leave-one-salt-out targets. This is
verified post-publication method development because the LiAsF6 outcomes were
already known, not independent confirmation.

The 2026-07-30 cross-database interaction benchmark strengthens the
decision-level result. Three conductivity programmes were trained separately
and combined with equal programme weight after removing the complete target
family from the broad BambooMixer arm. No source record matched the 180-row,
36-formulation SolventSeg recipient. With five recipient labels, the preserved
source score reached mean Spearman \(\rho=0.910\), versus 0.537 for the
strongest of 13 recipient-only configurations
(\(\Delta\rho=0.374\), 95% anchor-coverage interval 0.213–0.562). It remained
0.300 [0.183,0.540] above a per-draw recipient oracle. The portfolio did not
improve absolute calibration and was therefore routed to ranking. Its
\(\rho\) gain over the broad single donor was only 0.0236
[0.0069,0.0397], so source interaction is a modest robustness gain, not a
large synergy claim. This is verified post-outcome method development, not
independent confirmation.

The contribution is not “we found a universal theory.” It is an executable way
for one domain to make a falsifiable proposal to another. KIT demonstrates
material few-shot transfer. A systematic eight-target benchmark then shows why
that result cannot be generalized by simply injecting a donor prediction: the
strongest designated edge improves OOD RMSE by 6.65% [3.53,14.02%], but improves
ID similarly, retains negative OOD R², and zero of eight edges passes the full
OOD-repair gate. Caltech demonstrates the constructive alternative for
exploration: external OBELiX and ESTM rankings retain different high-value
candidates, and a target-model-free portfolio covers 5/8 external top entities
versus 2/8 and 3/8 individually.
An outcome-informed CCA family-first allocation goes beyond repeated entity
hits: it recovers all 4/4 distinct top external identity/provenance components
and both 2/2 hard-OOD components by acquisition 20, with conditional shuffled-
rank p=0.0020 and 0.0030. This is the operational OOD-exploration contribution:
find more distinct scientific regions, not merely improve average ML fit.
The portfolio was then frozen on two outcome-unseen targets. Starrydata shows a
small ionic-to-thermoelectric direction (+0.88% [0.02,1.77%]) but fails Holm
multiplicity, source specificity, and absolute utility; the four-plate TRI OER
edge is null (-0.08% [-0.31,0.16%]) and worse than its best control. The pooled
effect is null and heterogeneous (+0.30% [-0.62,1.22%], I²=76.7%). These are not
embarrassing failures to hide: they are the decisive evidence that the map is
sparse, directional, endpoint-specific, and capable of abstention.
A cross-program method-development benchmark then asks whether the map can make
that decision without using the held-out target programme's outcomes. Across 97
edges, 20 tasks, and 13 programme clusters, the CCA gate gives +1.58% mean
utility [-0.23%,4.27%], covers 11/13 programmes, and selects only one clearly
harmful edge among 17 admissions. It does not beat the frozen comparators after
Holm correction and retains only 4/10 available clear benefits; adjacency-only
is numerically stronger. This pins down the improvement: physical adjacency is
a useful first-order prior, but credible neighbor selection requires candidate-
local support and endpoint-specific applicability, not another global edge
score.
The protected multi-stage battery experiment sharpens that strategy boundary.
Its frozen 23-condition primary became non-evaluable because one entire cycle-
aging condition lacked the required terminal 23 °C endpoint. In the disclosed
22-condition sensitivity, CCA-v2 again failed to beat adjacency-only. An
explicitly outcome-guided diagnostic then identified the simpler policy as the
next candidate: the precomputed Stage 1 degradation prediction reduced
condition-level RMSE by 6.12% [2.56%,9.16%] versus target-only, with positive
effects in calendar and cycle aging and Holm-adjusted superiority to wrong-
property, shuffled-source, and random-feature controls. This is not a rescued
confirmatory test. It is reproducible method-development evidence that source
qualification should happen upstream and that a credible continuous neighbor
feature can outperform a brittle hard gate.
The paper-disjoint CALiSol experiment now tests the same physical neighborhood
and shows that the KIT improvement is not automatically transportable across
experimental articles when the transferred object is an absolute donor
prediction. A separately locked, post-outcome mechanistic reanalysis then
changes the transfer object to a within-article response relation. With one
target-article anchor it improves macro-RMSE by 6.91% over a matched absolute
donor, passes article-level inference and shuffled controls, and retains
positive absolute utility. This is the first direct evidence in the package
that a failed provenance rung can be partly repaired by changing what is
transferred and supplying a small target-provenance calibration. OBELiX then
separates fixed OOD screening from
sequential discovery: a directional thermoelectric-prior ranking signal does
not survive the acquisition-and-refit campaign prespecified after the ranking
analysis, and uniform random
acquisition outperforms both tested UCB policies. A separately frozen Caltech
ionic-conductor benchmark goes further: its gate preferentially admits real
neighbors and suppresses wrong domains, but no adaptive source increment
improves acquisition. However, source out-of-fold quality is weak for OBELiX
(R²=0.065), and the highest-skill source is the OCx wrong-domain control
(R²=0.543). Admission ordering is therefore not demonstrated credibility, and
  the null cannot isolate source weakness from policy conversion. Prespecified
  static neighbor shortlists nevertheless retain retrospective external OOD
  signal, and the two sources make complementary proposals.

## Recommended title

**Endpoint-routed knowledge borrowing selectively improves
out-of-distribution decisions from neighboring experiments**

Alternative:

**Selective knowledge borrowing across experimental materials domains under
incomplete scientific understanding**

## One-sentence contribution

In experimental materials data, artifact-gated and outcome-unseen tests show
that neighboring-domain utility is sparse, directional and endpoint-specific:
qualified relations can improve few-shot or new-component prediction,
preserved donor rankings can inform OOD proposals, and the same map rejects
unsupported borrowing.

## Draft abstract

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

## Table-of-contents text

Sparse target domains need more than larger pooled datasets. Artifact-gated
borrowing identifies the few neighboring experimental edges that help prediction
or OOD decisions and forces abstention when they do not.

## Defensible contributions

1. **Analysed cohort and pinned integration.** 21 resources enter numerical
   analysis: 13 normalized resources, seven frozen external or temporal
   programmes, and one streamed analysis-only resource; the normalized layer
   contains 96,184 measurements, 230 property labels, and 29,516 canonical
   formula, molecule, or mixture entities, with explicit revisions or hashes,
   conditions, and quality flags.
2. **Law-transport falsification.** Same-record Borg UTS–YS R²=0.790,
   BIRDSHOT R²=0.067, Borg→BIRDSHOT external R²=−3.006. A strong source
   coefficient is not an unconditional law.
3. **Internally selected candidate edge.** Borg UTS→Borg YS improves relative
   RMSE by 6.46% [3.69%,13.03%], Holm p=0.005 after uniform 999-permutation
   refinement of all five selected edges, with 3/3 learners positive.
4. **Independent directional replication with failed rescue gate.**
   Borg UTS→BIRDSHOT YS gives 4.30% [3.36%,5.51%], p=0.003, and both future-year
   folds are positive, but the frozen 5% gate and absolute-utility gate fail.
5. **Independent negative replication boundary.** Borg UTS→Matbench steel YS
   gives −1.23% [−15.88%,2.48%], p=0.794. RF and ExtraTrees sensitivities are
   small (<1%), far below the practical gate. Mechanical adjacency alone is
   not sufficient.
5a. **Controlled complete-system relation transfer.** A composition–OER
    relation learned from 462 catalysts was applied to four complete
    126-catalyst derivative systems. With five recipient anchors, derivatives B
    and D reduce pooled RMSE by 16.3% [9.2%,22.9%] and 26.1%
    [20.0%,31.7%], respectively, while improving Spearman rank by 0.347
    [0.260,0.426] and 0.407 [0.352,0.459]. Derivative A is ranking-only and C
    makes RMSE 10.4% worse, so the same fixed procedure demonstrates positive,
    partial and harmful routes. This is a controlled within-programme result;
    the composition analysis is a disclosed post-primary amendment and does
    not count as four independent replications.
5b. **Retrospective zero-shot new-component transfer.** A
    permutation-invariant mixture relation trained on 10,407 electrolyte
    measurements predicts an external LiAsF6 programme with raw
    \(R^2=0.629\) and \(\rho=0.871\), reducing log-RMSE by 28.64%
    [24.03%,33.52%] versus state-only and by 27.16%
    [22.78%,31.90%] versus chemistry permutation. It improves both error and
    ranking for 7/9 leave-one-salt-out targets. Because the public LiAsF6
    outcome was inspected before design, this is verified method development
    and must be frozen on a new target before being called confirmatory.
6. **Material within-campaign few-shot improvement.** KIT −20→−30 °C conductivity gives 15.02%
   [8.61%,21.10%], p=0.001; baseline/augmented R²=0.739/0.811; 5/5 folds and
   3/3 learners positive; source OOF R²=0.859; source-feature importance 0.732,
   median rank 1/5; point-equivalent target n=47.884 and 37.35% labels saved.
   A post-outcome diagnostic interval is 21.84–49.91%, with 80.52% of
   replicates at or above the frozen 30% point threshold; do not present 30%
    saving as an uncertainty-qualified lower bound. The n=30 target-only R² is
    already 0.739; “local task rescue” is only the operational table status.
7. **Selective physical ordering and placebo.** Prespecified increasing
   temperature-distance controls give 5.01%, 0.95%, and −0.76%; Spearman
   ρ=−1 across these four real sources. The shuffled adjacent source is harmful
   at −2.96% [−4.32%,−1.44%]. This is a within-target local ordering, not a
   universal cross-domain metric.
8. **Frozen cross-article failure boundary.** CALiSol −30→−40 °C gives 1.61%
   [−2.14%,4.21%] under article-hierarchical uncertainty; pooled R² remains
   −0.049/−0.014, two article folds are harmful, estimated label savings are
   16.9%, and the distance controls are unordered. The fixed-subset mapping
   p=0.004 is retained but cannot override the other failed frozen gates.
8a. **Post-outcome mechanistic repair of that boundary.** On the same
    −30→−40 °C pair, a within-article contrast model plus one target-article
    anchor reduces macro-RMSE by 6.91% versus the same-anchor absolute donor
    [0.88%,14.00%], exact article sign-flip p=0.0352, with 8/11 articles
    positive and pooled non-anchor R²=0.234. The gain is positive in 100/100
    random-anchor repetitions, exceeds the 199-permutation shuffled contrast
    (p=0.005), and rejects a +20 °C wrong-condition contrast. This design was
    motivated after item 8 was known; it is method-development evidence and
    requires unchanged external replication.
9. **Systematic OOD repair stress test.** Forty real edges were tested across
   eight targets using outcome-free Q1/Q4 distance groups, three learners, wrong
   and shuffled controls, 100 grouped label draws, hierarchical uncertainty, and
   Holm correction. Alloy UTS→YS gives +6.65% [3.53,14.02%] OOD gain but
   +7.74% ID gain and OOD R²=−0.666; it is transferable correlation, not
   OOD-specific repair. The seven-programme mean is +0.92% [−0.35,2.92%], with
   0/8 designated and 0/3 cross-database edges passing the complete gate.
10. **Artifact-gated global regularities.** Thermoelectric Meyer–Neldel:
   n=112, R²=0.107. ISODB matched-loading isosteric analysis: n=1,103 systems
   from 512 DOIs, pooled R²=0.637, T_iso=513 K versus median harmonic T=301 K,
   Krug-null median R²=0.003; family intercepts remain DOI-cluster significant
   (p=0.0002).
11. **OOD knowledge-deficit localization.** At n=30, target-only ExtraTrees
    RMSE is 0.373 [0.047,0.669] higher in the farthest than nearest dynamic OOD
    quartile, and absolute error increases with distance (ρ=0.097
    [0.049,0.144]). The thermoelectric source reduces far-OOD RMSE by 3.95%
    [2.65%,5.26%] and exceeds the best wrong or shuffled source by 1.29
    percentage points [0.21,2.40]. This is a conditional post-outcome
    diagnostic, not independent confirmation.
12. **Directional fixed OOD screening.** Thermoelectric ZT→OBELiX reduces the
    mean official-test fraction screened before the first top-5% hit from
    12.08% to 9.98%; the 2.09-percentage-point saving [0.94,3.45] has Holm
    p=0.0003 but fails the 25% effect and 80% repeat-consistency gates.
13. **Frozen sequential null with a stronger random reference.** Official-test
    thermoelectric-prior UCB saves 0.25 acquisitions [−1.30,1.82], p=0.389,
    and fails every improvement gate. Uniform random acquisition requires
    15.50 acquisitions versus 24.34 for target-only UCB. Prediction, fixed OOD
    screening, and sequential discovery are empirically distinct.
14. **External OOD neighbor signal, complementarity, and policy boundary.** On
    483 Caltech ionic-conductor compositions, prespecified OBELiX and ESTM
    rankings recover 2/8 and 3/8 external top-5% entities and 3/3 hard-OOD
    entities; mechanical and catalysis controls recover 0/8 externally. All
    wrong-source harm guards pass. A diagnostic portfolio recovers 5/8
    externally, demonstrating complementary neighbor proposals, although it was
    constructed after outcome inspection. No frozen residual policy passes the
    adaptive source-increment gates, showing that useful ranking signal is not
    preserved automatically by target-model injection.
15. **Family-first breadth improvement.** The eight external top entities collapse
    to four formula/DOI/ICSD components. CCA family-first consensus increases
    distinct-component AUC20 from 47 to 60 and recall20 from 3/4 to 4/4;
    hard-OOD AUC20 increases from 36 to 39 with 2/2 groups ranked first and
    second. Wrong-source AUC20 is 6/18 and 5,000 shuffled-rank pairs give
    conditional p=0.0020/0.0030. Entity recall falls, explicitly identifying
    the strategy as breadth-oriented OOD exploration rather than generic ML
    improvement.
16. **Outcome-unseen reverse and second-family boundaries.** The complete
    Starrydata reverse target is directionally positive at +0.88%
    [0.02,1.77%] but fails Holm multiplicity (p=0.071), positive absolute R²,
    source specificity, exploration, and hypothesis-card confirmation. The
    four-plate TRI OER target is -0.08% [-0.31,0.16%], with negative absolute R²
    on every plate and no confirmed policy or card.
17. **A falsifiable selective map, not a positive-example collection.** The
    two-target mean is +0.30% [-0.62,1.22%] with I²=76.7%. The same frozen system
    admits KIT, preserves Caltech as retrospective proposal evidence, abstains
    on Starrydata, and rejects TRI. Cross-target heterogeneity is therefore a
    measured property of the borrowing map.
18. **Protected temporal boundary and strategy discovery.** The multi-stage
    battery target retained 135/138 cells but lost one complete cycle-aging
    condition because all three archives lacked `AT_T23`; the frozen 23-group
    primary is non-evaluable. In the disclosed 22-group sensitivity, CCA-v2
    fails against adjacency-only. A separately marked outcome-guided diagnostic
    finds 6.12% [2.56%,9.16%] lower condition RMSE for the continuous Stage 1
    source feature versus target-only (Holm p=0.0108), with 7/8 calendar and
    10/14 cycle groups improved and superiority to wrong, shuffled, and random
    controls. This is a reproducible candidate-policy result requiring an
    independent target, not confirmatory temporal success.
19. **Strong-model molecular rejection boundary.** Experimental optical
    message-passing encoders passed scaffold-held-out source-skill gates, but
    their state-aligned residual correction worsened hard-OOD photocatalysis
    RMSE by 28.12% at 60 labels and improved only 74/300 frozen draws. It was
    25.23 percentage points worse than a shuffled-source encoder; harm persisted
    at 30 and 120 labels. The 96-molecule blind set remained unopened. This
    post-benchmark stress test rules out weak source fitting as a sufficient
    explanation for the molecular null and belongs in SI, not as a main-text
    showcase.

### Strategy synthesis and proof of feasibility

The separately isolated exploratory policy benchmark validates composition
novelty against random in both the official and hard-OOD pools. A
target/source/novelty rank fusion improves official-pool cumulative recall but
does not beat novelty on the first-hit endpoint and loses to novelty in early
hard-OOD recovery. Thermoelectric static screening is not practically separated
from the catalysis static control. Because the method family was selected after
inspecting OBELiX outcomes, these results select external-validation baselines
and endpoints rather than changing the frozen sequential decision.

The independently frozen Caltech benchmark rejects adaptive residual injection
as the conversion mechanism. After outcome inspection, a target-model-free
OBELiX/ESTM round-robin or rank-consensus portfolio recovers complementary
high-value candidates (external recall20=0.625; hard-OOD recall20=1.000).
Because the portfolio was constructed after seeing Caltech outcomes, it selects
the next policy for a new target and provides component-level proof of
complementarity; it is not independent confirmation of adaptive acceleration.

A subsequent outcome-informed audit tested what the portfolio should optimize.
Multiplying source evidence by target OOD, source support, and local concordance
collapsed external AUC20 to 0.96, so local OOD is not treated as an automatic
reward. The CCA policy instead qualifies sources globally, preserves their
ranks, allocates the first pass across connected identity/provenance components,
and abstains or falls back when controls are competitive. This family-first
allocation recovers broader high-value regions and produces a source-specific,
falsifiable hypothesis card for each proposed region.

The resulting strategy is a defensible methods contribution: qualify sources
under provenance-aware cross-fitting and wrong-source controls; preserve each
qualified source as an independent OOD shortlist; combine complementary
neighbors by round-robin or consensus; retain novelty and random fallbacks; and
write the source-derived scientific hypothesis before revealing target
outcomes. Its outcome-unseen test does not produce a second full-gate positive;
instead it shows that the strategy can reject its own attractive proposals.
What remains unconfirmed is prospective acceleration and the population
frequency of useful edges, not the existence of selective neighboring signal or
the feasibility of the artifact-gated decision process.

## Claims that are safe

- Strong pooled or source-domain relations require transport and artifact
  tests; aggregation alone does not establish universal coefficients.
- The internal UTS→YS edge is an internally selected candidate whose direction
  reproduces in BIRDSHOT, but it does not achieve positive absolute utility or
  independent confirmation.
- The independent Matbench result is null under the frozen primary model and
  all practical thresholds.
- The internally frozen KIT adjacent-temperature edge materially improves
  few-shot error and sample efficiency in a simulated label-poor condition
  slice within one campaign under strict formulation-level leakage control.
- KIT borrowing is physically ordered over the prespecified temperature
  controls and is not reproduced by source scrambling.
- Neighboring experimental domains can contain complementary OOD-ranking
  signal: prespecified OBELiX and ESTM rankings recover different high-value
  Caltech compositions after exact formula and DOI exclusions.
- The selective neighborhood-borrowing strategy has component-level proof of
  feasibility across few-shot prediction, wrong-source suppression, external
  OOD ranking, and multi-neighbor shortlist complementarity.
- Outcome-informed CCA family-first allocation improves recovery of distinct
  Caltech identity/provenance components under fixed-pool shuffled and wrong-
  source controls, while reducing repeated entity hits. It is a breadth policy
  that was subsequently tested outcome-unseen and did not pass its full policy
  gate; it is not a universal improvement claim.
- Absolute donor-feature transfer on the paper-disjoint CALiSol edge is
  unresolved and fails its original rescue decision; KIT's distance ordering
  does not automatically reproduce across articles.
- A post-outcome, separately locked CALiSol reanalysis shows that changing the
  transfer object to a within-article response relation and restoring the
  target provenance with one anchor yields a qualified 6.91% advantage over
  the matched absolute donor. This supports the repair strategy, not an
  independent replication.
- In the systematic eight-target OOD benchmark, selected donor features can
  lower error in remote feature-space quartiles, but no designated edge passes
  the complete OOD-repair gate. The strongest alloy gain is real within the
  tested benchmark yet not OOD-specific and not absolutely predictive.
- Generic donor-feature injection is therefore insufficient for OOD repair in
  the tested envelope; this supports endpoint-matched transfer objects rather
  than the stronger claim that no representation could ever transfer.
- Borrowing is sparse, directional, and sometimes harmful.
- In the outcome-unseen Starrydata reverse target, ionic borrowing has a small
  positive hierarchical interval and learner-representation robustness, but
  fails multiplicity, absolute utility, source specificity, exploration, and
  all hypothesis-card confirmation requirements.
- In the outcome-unseen four-plate TRI OER target, the all-neighbor effect is
  null, every plate has negative absolute R², and no exploration policy or
  hypothesis card is confirmed.
- The two outcome-unseen target effects are heterogeneous and have a null pooled
  interval. This supports a selective map with abstention, not a general
  neighboring-domain transfer law.
- A 13-program leave-one-program benchmark shows nontrivial positive point
  utility and low clear-harm admission for CCA, but no corrected superiority
  over simple comparators. It identifies candidate-local applicability as the
  missing variable and is reported as method development, not replication.
- A strong pooled adsorption regularity survives the simple Krug null but
  requires family conditioning.
- The OBELiX thermoelectric prior has a directional fixed-ranking OOD screening
  signal, but it does not establish sequential discovery improvement or rescue.
- Under the frozen OBELiX protocol, both tested UCB policies underperform the
  prespecified uniform-random reference. This is policy-level failure in one
  retrospective pool, not evidence that random search is generally optimal.
- A post-result benchmark identifies composition novelty as the valid
  target-only acquisition baseline and source/target/novelty fusion as a
  breadth-of-recall candidate for independent testing; it does not establish a
  neighbor-source increment on OBELiX.
- On the independent Caltech target, no frozen adaptive source-aware policy
  improves acquisition beyond its target-only comparator; all wrong-source
  weight guards pass.
- The Caltech gate admits the designated real neighbors more often than wrong
  controls, but this is not an ordering of source model skill: OBELiX source
  OOF R² is 0.065 and the OCx control is highest at 0.543. The two prespecified
  real-neighbor static rankings are stronger than random, shuffled, mechanical,
  and catalysis rankings in both scopes as prespecified retrospective evidence.
  A post-outcome portfolio expands recall from 2/8 and 3/8 individually to 5/8;
  this demonstrates complementarity on the observed target but is not a
  confirmed source-to-policy edge.

## Claims that are not safe

- “All global materials regularities are artifacts.”
- “Physical distance is a universal quantitative transfer law.”
- “Neighborhood borrowing has been independently confirmed across multiple
  scientific domains.”
- “Starrydata confirms reverse ionic-to-thermoelectric transfer.” The directional
  interval does not survive the complete multiplicity and absolute-utility gate.
- “TRI confirms electrocatalysis transfer.” The primary effect is null and the
  all-neighbor model is worse than the best control.
- “The KIT result rescues an entire data-poor field” or is an independent-
  dataset replication.
- “The original CALiSol feature-injection experiment independently confirms
  rescue” or “p=0.004 proves useful external borrowing”; its repeated effect,
  absolute utility, fold, sample-saving, and adjacency gates fail.
- “The CALiSol contrast result is preregistered, independent, zero-shot, or
  universally applicable.” It was motivated after the original null, uses one
  retrospective target-article anchor, and contains three harmful articles.
- “BIRDSHOT confirms at least 5% practical improvement” or has positive
  absolute rolling-time utility.
- “Feature importance proves a microscopic mechanism.”
- “Prediction gain accelerates active search.”
- “Thermoelectric data rescue solid-electrolyte prediction.”
- “The eight-target benchmark proves general OOD improvement.” Its programme
  interval crosses zero, all augmented OOD R² values are non-positive, and zero
  designated edges pass the full gate.
- “The alloy UTS→YS edge repairs OOD.” Its Q4 gain is statistically and
  practically positive, but Q1 improves slightly more and Q4 R² remains
  negative.
- “The OBELiX fixed-ranking signal proves OOD-discovery acceleration.”
- “The hard-OOD ExtraTrees effect is rescue”; it fails the practical,
  consistency, and Random-Forest-sensitivity gates and is exploratory.
- “Post-result rank fusion proves neighbor-specific OOD acceleration.” It was
  selected after outcome inspection, does not beat composition novelty for
  first hit, and fails practical separation from the catalysis control.
- “Caltech confirms neighbor-driven OOD-discovery acceleration.” Every frozen
  adaptive source increment fails.
- “The Caltech static rankings or neighbor portfolio establish a transferable
  discovery policy.” Static attribution was not in the frozen primary contrast
  family, the portfolio was outcome-selected, and neither supplies
  independent-target or prospective uncertainty.
- “Family-first CCA proves prospective discovery or new science.” It was
  designed after Caltech outcomes, its randomization p-values are conditional
  on one fixed pool, and connected metadata components are not mechanistic
  chemical families.

## Evidence structure for the paper

### 1. Strong law versus soft prior

- Borg same-record paired rows: n=495, 208 compositions, R²=0.790.
- BIRDSHOT: n=171, 151 compositions, R²=0.067.
- Exact cross-dataset composition overlap: zero.
- Borg direct line on BIRDSHOT: R²=−3.006 [−4.154,−2.185].
- Median UTS/YS changes from 1.36 to 2.72.

Moving a fixed coefficient fails. A borrowed prediction remains a learnable
soft feature and must pass separate utility gates.

### 2. Candidate-edge audit and external boundaries

- Nine internal targets and five sources per target; discovery and disjoint
  internal-screen entities.
- Five discovery-selected edges receive uniform 999-permutation refinement and
  Holm correction.
- BIRDSHOT uses rolling Year 1→2 and Years 1–2→3 tests with zero canonical
  composition overlap.
- Matbench uses the official five folds, n=30 labels per training fold, exact
  target-composition exclusion from source fits, and forbids same-row tensile
  strength and elongation.
- The combined synthesis contains 42 internal non-calibration edges, 15
  independent BIRDSHOT edges, five independent Matbench edges, and five KIT
  temperature/placebo edges, plus five paper-disjoint CALiSol
  temperature/placebo edges. Evidence layers remain labeled rather than pooled
  as exchangeable replications.

### 3. Operational local-neighbor point-rule test

- 5,035 KIT rows represent 504 experiment IDs and 109 unique formulations.
- The analysis unit is a formulation; replicate runs are aggregated by the
  median within formulation and temperature. The 108 formulations complete at
  all target/control temperatures are split as indivisible groups.
- In every outer fold, the source model excludes target-test formulations.
  Source features for target-training formulations are themselves cross-fitted.
- Arrhenius parameters and every EIS-derived fit output are forbidden because
  they encode the same temperature series as the target.
- Primary target/source: −30/−20 °C. Frozen controls: 0, 30, 60 °C and a
  shuffled −20 °C source.
- Rescue requires ≥5% RMSE reduction, CI above zero, positive augmented R²,
  five positive folds, ≥30% target-label fraction saved, ≥2/3 positive learners,
  positive source OOF R², zero source/test overlap, permutation p<0.05, valid
  learning curve, correct distance ordering, and failed placebo. All gates pass.
- CALiSol repeats the logic with 891 target formulations from 15 articles and
  outer folds grouped by article DOI. Source fits exclude all held-out articles
  and exact held-out chemistry identities; uncertainty resamples articles.
  The primary effect is 1.61% [−2.14%,4.21%], R² remains negative, only three
  article folds are nonnegative, savings are 16.9%, and distance ordering
  fails. The protocol therefore returns a frozen external null boundary rather
  than switching to the numerically stronger 0 °C control.

### 4. Systematic OOD-repair stress test

- Eight eligible targets across seven programme clusters retain 40 real edges
  and eight shuffled designated-source controls.
- Q1 and Q4 evaluation groups are defined without outcomes from composition or
  molecular-fingerprint distance to complete development data.
- Every source fit excludes recipient-evaluation identities; 100 paired grouped
  label draws compare target-only, augmented, wrong-source, and shuffled-source
  models across Ridge, Random Forest, and ExtraTrees.
- The complete gate combines ≥5% Q4 gain, a positive hierarchical interval,
  ≥80% repeat consistency, wrong/shuffled superiority, learner robustness,
  positive absolute Q4 R², positive Q4−Q1 specificity, zero overlap, and Holm
  significance.
- Alloy UTS→YS passes every component except absolute Q4 R² and OOD
  specificity: Q4 gain is +6.65% [3.53,14.02%], Q1 gain is +7.74%, and
  augmented Q4 R² is −0.666.
- No designated edge passes. The seven-programme mean is +0.92%
  [−0.35,2.92%], and 0/3 designated cross-database edges pass.
- All 40 edges remain visible: 10 directional, nine positive but not
  OOD-specific, ten harmful, and eleven unresolved. Non-designated positives are
  new hypotheses, not confirmations.

### 5. OOD screening and sequential-discovery boundary

- Official OBELiX evaluation retains 390 canonical train and 110 canonical test
  compositions after overlap removal; all three source domains have zero exact
  composition overlap with the 500 targets.
- Fixed ranking uses the fraction screened before the first true top-5% hit.
  Thermoelectric borrowing changes 12.08% to 9.98%, a directional 17.3%
  relative reduction that fails the 25% and 80%-consistency gates.
- The farthest-40% ranking result is explicitly exploratory because its design
  follows the whole-pool direction.
- The sequential design was frozen after the fixed-ranking direction was known
  but before its own result: shared n=30 official-
  train labels, 110 official-test candidates, 40-acquisition budget, 100
  ExtraTrees seeds, 40 Random-Forest sensitivity seeds, wrong-source,
  shuffled, and random controls.
- Thermoelectric-prior UCB saves only 0.25 [−1.30,1.82] acquisitions and fails
  every gate. Random acquisition is substantially faster and matches its exact
  finite-pool expectation.
- The independent Caltech benchmark contains 483 canonical compositions, with
  339 development entities, 144 article-disjoint candidates, and 58 hard-OOD
  candidates. Every source fit excludes target formulas and DOIs.
- Frozen adaptive OBELiX, ESTM, and multisource residual increments all fail.
  The admission rule nevertheless admits designated neighbors at 35.5% of
  steps with mean weight 0.168, versus 16.8% and 0.063 for wrong controls; all
  frozen negative-transfer guards pass. This is not source-skill ordering:
  OBELiX source OOF R² is 0.065 and the OCx control is highest at 0.543.
- Prespecified real-neighbor static rankings dominate all random and wrong
  static references in both scopes, but external recall20 is only 2/8 and 3/8,
  while hard-OOD 3/3 has a very small denominator. This is descriptive because no
  static-source attribution decision family was frozen. A post-result
  target-model-free portfolio was therefore frozen for outcome-unseen testing.

### 6. Outcome-unseen reverse and second-family validation

- Starrydata freezes 7,403 entities (7,396 valid outcomes), 745 composition
  clusters, 1,301 evaluation entities, and a 738-entity primary far-OOD scope.
- The primary ionic-consensus effect is +0.88% [0.02,1.77%], Holm p=0.071,
  augmented R²=-0.485, +0.75% [-0.14,1.66%] versus the best matched control, and
  -0.10% [-1.20,1.03%] versus same-domain ESTM.
- Five of six learner-representation cells are directionally positive, but CCA
  AUC20=41 versus same-domain ESTM=71, source-rank permutation p=0.546, and all
  three hypothesis cards fail.
- TRI retains 8,447 entities across four plates and 240 composition clusters.
  The all-neighbor effect is -0.079% [-0.313,0.155%], Holm p=1.0, and all four
  plate R² values are negative; all-neighbor borrowing is -1.25%
  [-1.75,-0.75%] versus the best control.
- The two-target random-effects mean is +0.304% [-0.617,1.225%], I²=76.7%.
  Neither target passes its full prediction gate; all six hypothesis cards are
  retained as failures.

### 7. Global-law and artifact battery

- Thermoelectric compensation is weak and cutoff-sensitive.
- ISODB pure-component systems require at least three temperatures, monotone
  positive isotherms, a common uptake interval, and one geometric-midpoint fit
  per system.
- The strong ISODB relation is not reproduced when true Q_st and intercept are
  independently permuted on the observed temperature grids.
- Family intercepts are unequal; the conclusion is a conditional empirical
  regularity, not a universal mechanism and not a simple Krug artifact.

## Main figures

[`figures/specgen_derivative_oer_transfer.pdf`](figures/specgen_derivative_oer_transfer.pdf)

- a: one 462-catalyst OER donor and four complete 126-catalyst ligand or metal
  perturbations, with the whole derivative system as the OOD unit;
- b: zero-label spectral and composition ranking against 500 refitted
  shuffled-source models;
- c: five-label candidate-bootstrap RMSE and rank gains, routing B and D to
  prediction plus ranking, A to ranking only, and C to rejection;
- d: temporal rank corroboration on later selected candidates, explicitly
  separated from unbiased discovery acceleration.

The editable and raster bundle is generated by
`make_specgen_derivative_oer_figure.py`; source data, statistical definitions
and claim boundaries are recorded in `SPECGEN_DERIVATIVE_FIGURE_CONTRACT.md`
and `SPECGEN_DERIVATIVE_FIGURE_QA.md`.

[`figures/data_foundation_scope.pdf`](figures/data_foundation_scope.pdf)

- a: all 21 numerically analysed resources are named and assigned their actual
  candidate-donor, recipient, or artifact-gate roles; a donor role denotes an
  attempted information source rather than a passed edge;
- b: all 96,184 integrated measurements from 13 normalized sources, with exact
  source counts and five scientific families;
- c: explicit resource and systematic gate-benchmark denominators, including
  20 transfer-active resources and the unchanged 97-edge, 20-task,
  13-programme benchmark;
- d: a complete evidence portfolio that displays favorable, directional,
  unresolved, diagnostic, null, harmful, and non-evaluable outcomes together.

This figure makes the empirical denominator self-contained: every displayed
resource enters an analysis, and the five bold rows are emphasized for distinct
validation roles rather than favorable outcomes.
The Python-only editable and raster bundle is generated by
`make_data_foundation_figure.py`; source, scope, and export requirements are in
`DATA_FOUNDATION_FIGURE_CONTRACT.md` and `DATA_FOUNDATION_FIGURE_QA.md`.

[`figures/main_knowledge_borrowing.pdf`](figures/main_knowledge_borrowing.pdf)

- a: direct strength-law transport failure;
- b: frozen KIT rescue and CALiSol paper-disjoint failure boundary;
- c: exact target-only learning curve, 37% point label-saving equivalence, and
  22–50% post-outcome diagnostic interval;
- d: strong ISODB pooled regularity after artifact and family gates.

Editable SVG, 600 dpi TIFF, 300 dpi PNG, and panel source CSVs are generated by
`make_main_knowledge_map_figure.py`. `FIGURE_CONTRACT.md` and `FIGURE_QA.md`
record the visual argument, export audit, and statistical legend.

[`figures/multi_target_ood_borrowing.pdf`](figures/multi_target_ood_borrowing.pdf)

- a: outcome-free Q1/Q4 OOD definition, paired target-only and
  donor-augmented fits, and retained wrong/shuffled controls;
- b: hierarchical Q4 relative-RMSE effects for all eight designated edges;
- c: Q4 versus Q1 gains for all 40 real edges, exposing whether improvement is
  OOD-enriched or equally strong in-distribution;
- d: the complete practical, uncertainty, control, learner, multiplicity,
  absolute-utility, specificity, and overlap gate matrix.

The figure keeps the strongest positive result visible while showing why it is
not OOD repair: alloy UTS→YS passes most component tests, but not positive
absolute OOD R² or Q4-over-Q1 specificity. No designated edge passes the full
gate. The Python-only bundle is generated by
`make_multi_target_ood_borrowing_figure.py`;
`MULTI_TARGET_OOD_FIGURE_CONTRACT.md` and
`MULTI_TARGET_OOD_FIGURE_QA.md` record the argument, source data, and export
audit.

[`figures/ood_decision_borrowing.pdf`](figures/ood_decision_borrowing.pdf)

- a: directional fixed-ranking OBELiX signal in the official and exploratory
  hard-OOD pools;
- b: sequential effects relative to target-only UCB, including the frozen
  five-experiment gate and random acquisition;
- c: official-test cumulative discovery curves showing that random acquisition
  outperforms target-only and thermoelectric-prior UCB.

The editable and raster bundle is generated by
`make_ood_decision_figure.py`; panel source CSVs are written beside the analysis
results.

[`figures/neighbor_map_exploration.pdf`](figures/neighbor_map_exploration.pdf)

- a: the operational borrowing map separates source qualification, preserved
  complementarity, continuous borrowing, family-first allocation, and
  abstention;
- b: admission and weighting do not reduce to source out-of-fold skill;
- c: OBELiX, ESTM, and multisource residual increments are null in both
  candidate scopes and 0/6 pass all frozen adaptive gates;
- d: prespecified neighboring-source rankings nevertheless retain external and
  hard-OOD proposal signal, unlike the wrong-domain controls;
- e: outcome-informed family-first consensus raises distinct-group AUC20 from
  47 to 60 externally and from 36 to 39 in hard OOD, with conditional shuffled-
  rank p=0.002 and 0.003.

This combined figure makes the central distinction explicit: useful OOD
knowledge can survive as a proposal-ranking prior even when model-fit injection
does not. The Python-only editable and raster bundle is generated by
`make_neighbor_map_exploration_figure.py`; the argument, source data, evidence
status, and QA are recorded in `NEIGHBOR_MAP_FIGURE_CONTRACT.md` and
`NEIGHBOR_MAP_FIGURE_QA.md`. The earlier separate Caltech and family-first
figures remain available as supplementary decomposition figures.

[`figures/outcome_unseen_validation.pdf`](figures/outcome_unseen_validation.pdf)

- a: Starrydata, TRI, and two-target relative RMSE effects with independent-unit
  intervals and complete-gate status;
- b: the frozen gate matrix showing a partial Starrydata direction and complete
  TRI rejection;
- c: three-learner by two-representation robustness for both targets;
- d: all six source-derived hypothesis cards, none of which survives Holm
  correction.

The editable SVG, print PDF, 600 dpi TIFF, 300 dpi PNG, and four panel-source
CSVs are generated by `make_outcome_unseen_validation_figure.py`. The frozen
visual and statistical claims are specified in
`OUTCOME_UNSEEN_FIGURE_CONTRACT.md` and audited in `FIGURE_QA.md`.

[`figures/battery_continuous_borrowing.pdf`](figures/battery_continuous_borrowing.pdf)

- a: the protected Stage 1-to-Stage 2 temporal design and the structural
  endpoint-coverage boundary that makes the frozen 23-group primary
  non-evaluable;
- b: post-release continuous adjacent-source borrowing lowers equal-stratum
  condition RMSE by 6.12% [2.56%,9.16%] versus target-only and remains superior
  to wrong-property, shuffled-source, and random-feature controls;
- c: 17/22 held-out condition groups improve, while the type-specific hard-OOD
  effect remains heterogeneous;
- d: the training-only CCA-v2 hard gate admits only 4/22 condition groups and
  falls back for all 14 cycle-aging groups;
- e: both prewritten source-inspired lead-versus-control contrasts pass in the
  predicted direction.

The figure is deliberately labeled as outcome-guided post-release method
development: it nominates continuous upstream qualification for independent
confirmation and does not rescue the non-evaluable frozen primary. The
Python-only bundle is generated by
`make_battery_continuous_borrowing_figure.py`; `BATTERY_FIGURE_CONTRACT.md` and
`BATTERY_FIGURE_QA.md` record the source and statistical audit.

## Positioning for Digital Discovery

Position the paper as a **falsification-first audit of candidate borrowing
edges**. Transfer learning alone is not novel. The novelty is the experimental
comparison between coefficient transport and soft-prior borrowing, coupled to
provenance-aware splits, exact-identity audits, multiplicity, practical and
absolute-utility thresholds, source-feature scrambling, physical-distance
controls, independent positive/negative boundaries, and a global-law artifact
battery.

The sequential null is a strength if framed as a tested boundary: prediction
lift and fixed OOD screening do not automatically yield discovery acceleration.
Because the random reference materially outperforms both UCB policies, this
result belongs in the main Results and Figure 4 rather than being hidden in the
Supplementary Information. Keep it out of the title.

The systematic OOD benchmark should be framed as the method's decisive
stress test, not as a failed replication. It demonstrates that relative gains in
a distant feature-space slice can still be ordinary transferable correlation
rather than repair of the target's OOD knowledge deficit. This is why the paper
requires positive absolute utility and Q4-over-Q1 specificity and why it moves
from generic feature injection to endpoint-matched transfer objects. Keep all
40 edges visible and do not promote post hoc non-designated positives.

The Caltech adaptive null sharpens that story but cannot isolate policy
conversion. The admission rule orders designated neighbors above wrong-domain
controls even though source OOF skill follows a different order and the same-
property source is weak. The defensible conclusion is that these weak source/
target backbones and conversion policies did not improve acquisition.
Prespecified retrospective static rankings justified an outcome-unseen test of
neighbor shortlists as independent information channels; that test is now
complete and does not establish a general acquisition policy.

The outcome-unseen result should be framed assertively. It is not “we tried two
more datasets and failed.” It is “a frozen borrowing map made risky predictions
and was allowed to abstain or reject them.” Starrydata preserves a weak direction
without passing the gate; TRI rejects the edge; the pooled effect is null and
heterogeneous. This is direct evidence against automatic transfer and in favor
of an auditable, edge-specific map. Do not convert the Starrydata interval into
a positive replication, and do not let the null pooled mean erase KIT's
target-specific existence result.

Use **material within-campaign few-shot improvement** in prose for KIT, and
reserve **local task rescue** for the defined table status. Use **directional
replication below utility gates** for BIRDSHOT, **independent null** for
Matbench, **paper-disjoint absolute borrowing unresolved** for the original
CALiSol analysis, and **post-outcome anchored-contrast repair** for E6. This
scoped vocabulary is central to credibility.

The current journal category is a **Full paper**, not a Methods article.
The 14 July 2026 RSC guidance has no strict Full-paper page limit, recommends a
50–250-word abstract, requires a Data availability statement, and expects code
and analysis data in a persistent repository accessible to the journal's data
reviewer. The abstract is kept within the journal limit and the draft follows
the required end-matter order. A table-of-contents entry and archived release
DOI remain submission deliverables.

## Remaining submission gates

The machine-readable authority is `core_story_experiment_registry.json`; the
human-readable rationale is `CORE_STORY_EXPERIMENT_MATRIX.md`. The manuscript
must not be submitted while `check_core_story_experiments.py --require-complete`
fails. All paper-submission-required scientific experiments are now either
`complete` or `complete-boundary`. Balam Job 70888 completed both outcome-unseen
targets, all matched baselines, the learner-representation envelope,
multi-policy exploration, six hypothesis cards, and two-target synthesis;
independent portable verification passed.
The subsequent leave-one-program CCA benchmark and independent reconstruction
also pass their file-hash, cluster-assignment, recomputation, and multiplicity
checks; its superiority decision is negative and retained unchanged.
Formal multi-target OOD Job 71429 and its portable verifier also pass: all eight
targets, 40 real edges, eight shuffled controls, three learners, and unfavorable
results are retained under matching design, summary, and completion hashes.

The remaining gates are release and authorship tasks:

1. Archive the exact code, compact results, figure data, and rebuild metadata
   with a DOI. Complete source-by-source access, attribution, and redistribution
   checks for the 21 analysed resources.
2. Run the complete workflow in clean Linux CI on the archived tag and retain
   hashes and package versions for every claim-bearing output.
3. Supply authors, affiliations, CRediT roles, funding, conflict confirmation,
   RSC typesetting, and the final table-of-contents entry.
4. Keep the outcome-unseen negative evidence in the main paper. Do not target-
   shop for a favorable retrospective replication or weaken the full gates.

The genuinely temporal/laboratory test is a claim-upgrade gate rather than a
submission gate for the bounded retrospective result. It becomes mandatory if
the paper claims discovery acceleration, new science already discovered, or
laboratory experiments saved.

With the KIT result, the project supports the bounded existence claim that
selective local borrowing can materially improve few-shot error in a simulated
label-poor slice of one campaign under leakage-safe evaluation. It passes the
internal point-rule status, but the
post-outcome interval around label saving crosses the 30% point threshold, so
the precise “rescue” magnitude must remain qualified. CALiSol adds the
adversarial result that the same neighborhood does not automatically travel
across articles. The systematic eight-target benchmark adds the stronger OOD
distinction: ordinary donor-feature injection can lower error without repairing
an OOD knowledge deficit, and zero designated edges passes the complete gate.
Starrydata and TRI add the decisive outcome-unseen result that the integrated
strategy does not generalize automatically: the map abstains on one direction,
rejects another, and returns a null heterogeneous mean. The project therefore
supports selective, endpoint-matched, falsifiable knowledge borrowing and not
unrestricted cross-campaign, cross-domain, or field-level rescue.

## Completed temporal claim-upgrade boundary and next test

The target-specific CCA-v2 protocol for the 2024 multi-stage lithium-ion aging
dataset was frozen before numeric aging outcomes were accessed. Stage 1 supplied
the temporal source; Stage 2 supplied 138 cells across 23 later OOD condition
groups with zero exact Stage 1 condition overlap. The primary family asked
whether candidate-local borrowing beat both unqualified Stage 1 stacking and
Stage 2 target-only learning under condition-cluster inference, a 2% practical
dead zone, and Holm correction.

That primary is now closed as non-evaluable, not pending. The protected release
extracted 135 endpoints, but all three cells in one cycle-aging condition lacked
the frozen terminal 23 °C measurement. The complete-condition coverage rule
therefore failed. A metadata-only ZIP audit confirmed the structural absence,
and no endpoint or condition was substituted.

The disclosed 22-group sensitivity independently reconstructed the negative
CCA-v2 comparison. Its outcome-guided follow-up nevertheless produced a useful
candidate policy: simple continuous Stage 1 prediction injection improved
condition RMSE by 6.12% [2.56%,9.16%] over target-only and survived wrong-
property, shuffled-source, and random-feature controls. The next claim-upgrade
experiment is therefore a new outcome-unseen target that freezes this simpler
policy and its four controls before outcomes. Reusing the present battery target
cannot provide that confirmation, regardless of the adjusted diagnostic
p-values.
The manuscript resource denominator is the declared 21-resource analysed
cohort. Repository discovery updates cannot silently change that scientific
denominator; this revision is explicit because the SpecGen OER programme enters
the main analysis and figures.
