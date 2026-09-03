# Adversarial review request for Claude

Act as a hostile but technically precise referee for *Digital Discovery* (RSC),
with expertise in materials informatics, transfer learning, active learning,
experimental databases, and statistical inference. Assume rejection unless the
evidence changes your mind. Do not reward transparency by itself; evaluate
whether the scoped claims are actually supported.

This is a second-pass review after the authors implemented the issue
dispositions in `analysis/ADVERSARIAL_REVIEW_RESPONSE.md`. Verify those fixes
rather than assuming they worked. In particular, inspect both primary marks in
Figure 1b, reconcile the Figure 1 source CSVs with the QA record, and test
whether the revised Caltech wording fully reflects the source-quality confound.

## Non-negotiable scientific thesis

When scientific understanding is incomplete, neighboring experimental domains
can still contribute useful and complementary information if the source signal
is qualified, matched to the endpoint, and preserved against negative transfer.
The intended contribution is a selective neighborhood-borrowing strategy plus
an artifact-gated map. The strategy qualifies sources under provenance and
wrong-source controls, uses soft priors for prediction, preserves independent
source ranks for OOD exploration, combines complementary neighbors as a
portfolio, and separates:

1. pooled regularity;
2. unchanged coefficient transport;
3. average predictive borrowing;
4. fixed OOD candidate ranking;
5. adaptive sequential acquisition;
6. prospective or new-science discovery.

The paper does **not** claim that physical adjacency guarantees benefit, that
the map rescues an entire field, or that retrospective screening
establishes prospective acceleration. Source admission, source predictive
skill, and acquisition utility are treated as separate quantities.

The positive thesis is non-negotiable: KIT demonstrates material predictive
transfer; Caltech demonstrates external neighbor-ranking signal; and the
post-outcome portfolio demonstrates complementarity on the observed target.
The added CCA family-first analysis asks a more scientifically relevant OOD
question: whether neighboring ranks recover distinct high-value regions rather
than repeated formulations from one connected provenance component.
Review whether these results support component-level proof of feasibility for
the strategy. Do not silently replace that claim with the stronger and
explicitly excluded claim of independently validated prospective acceleration.

Evaluate the manuscript's explicit definition of “map.” It is a decision map
over tested edges and endpoints, not a learned universal distance function or a
guarantee for untested targets. Do not reject the term merely because most edges
are null; determine whether the retained positive, null, harmful, and endpoint-
changing edges make that operational definition scientifically useful.

The Caltech-derived policy has now been executed on two outcome-unseen targets.
Do not demand that these targets be positive as a condition for evaluating a
selective map. Instead, decide whether their failures make the abstention and
edge-specificity claim genuinely falsifiable, and whether the manuscript avoids
rebranding a directional Starrydata interval as full confirmation.

## Current evidence state

- Catalog: 118 experimental-content resources.
- Pinned integration: 96,184 measurements from 13 normalized sources plus one
  registered analysis-only source; 230 property labels and 29,516 canonical
  entities.
- Alloy transport falsification: Borg UTS–YS same-record R²=0.790, BIRDSHOT
  R²=0.067, unchanged Borg line on BIRDSHOT R²=−3.006.
- Internal borrowing edge: Borg UTS prediction → Borg YS improves relative RMSE
  by 6.46% [3.69%,13.03%], Holm p=0.005, but is not an independent rescue.
- BIRDSHOT: +4.30% [3.36%,5.51%], p=0.003, but below the 5% practical gate and
  with negative absolute R².
- Matbench steels: −1.23% [−15.88%,2.48%], p=0.794; independent null.
- KIT within-campaign adjacent-temperature edge: +15.02%
  [8.61%,21.10%], p=0.001; R² 0.739→0.811. The 37.35% label-saving point
  estimate has a post-outcome diagnostic interval of 21.84–49.91%.
- CALiSol paper-disjoint test: +1.61% [−2.14%,4.21%], negative R², failed
  article-fold, sample-saving, and distance-ordering gates.
- Thermoelectric Meyer–Neldel: n=112, pooled R²=0.107.
- ISODB matched-loading compensation: n=1,103 systems from 512 DOIs, pooled
  R²=0.637, T_iso=513 K versus median harmonic T=301 K; Krug-null median
  R²=0.003; family intercepts remain DOI-cluster significant.
- OBELiX fixed ranking: fraction screened before first top-5% hit improves from
  12.08% to 9.98%, but fails the 25% practical and 80% consistency gates.
- OBELiX sequential campaign: thermoelectric-prior UCB saves 0.25 acquisitions
  [−1.30,1.82], p=0.389. Random requires 15.50 acquisitions versus 24.34 for
  target-only UCB.
- Independent Caltech ionic-conductor target: 483 canonical compositions, 339
  development entities, 144 article-disjoint candidates, and 58 hard-OOD
  candidates. Exact source/target formula and DOI overlaps are removed.
- Caltech primary result: every frozen OBELiX, ESTM, and multisource adaptive
  residual increment fails. All wrong-source harm guards pass.
- Caltech gate ordering: real-neighbor mean admission/weight are 0.355/0.168,
  compared with 0.168/0.063 for wrong controls.
- Caltech source-domain OOF R² is 0.065 for OBELiX, 0.257 for ESTM, 0.164 for
  Borg, and 0.543 for OCx. The wrong-domain OCx control has the largest measured
  source-model skill, so admission ordering is not a credibility measure.
- Caltech prespecified retrospective static rankings: OBELiX/ESTM AUC20 are 33/45
  externally and 38/51 in hard OOD, versus random 11.25/9.87. No primary
  static-source attribution family or independent-target interval was frozen.
- A post-result OBELiX/ESTM portfolio reaches recall20=0.625 externally and
  1.000 in hard OOD, versus 0.250 and 0.375 for the individual external
  shortlists. It is proof of complementarity and method selection; it cannot
  revise the primary adaptive null or establish prospective discovery.
- The eight external top entities occupy four connected formula/DOI/ICSD
  components; all three hard-OOD top entities originally counted belong to one
  component. Family-first CCA consensus recovers 4/4 distinct top external
  components by acquisition 20 (AUC20 60 versus 47 for entity consensus) and
  both 2/2 hard-OOD components at acquisitions 1 and 2 (AUC20 39 versus 36).
- Wrong-source family-first AUC20 is 6 externally and 18 in hard OOD. Across
  5,000 independently shuffled OBELiX/ESTM rank pairs, conditional p=0.0020
  and 0.0030. Candidate-outcome permutation leaves every order unchanged.
- The breadth gain is not hidden as a generic improvement: entity recall falls
  from 5/8 to 2/8 externally and from 3/3 to 1/3 in hard OOD because repeated
  members of one component are deferred.
- A multiplicative local target-OOD/source-support/concordance gate fails badly
  (external AUC20 0.96 versus 69 for static entity consensus). Review whether
  the resulting ruleâ€”qualify sources globally, preserve ranks, use OOD only as
  a quota/scope/tie-breaker, and abstain when controls competeâ€”is a useful and
  sufficiently general methods contribution.
- Outcome-unseen Starrydata reverse transport: 7,403 frozen entities and 1,301
  evaluation entities. The primary ionic-consensus effect is +0.88%
  [0.02,1.77%], but Holm p=0.071, augmented R²=-0.485, +0.75%
  [-0.14,1.66%] versus the best matched control, and -0.10%
  [-1.20,1.03%] versus same-domain ESTM. Five of six learner-representation
  cells are positive, but CCA AUC20=41 versus ESTM=71 and all three hypothesis
  cards fail.
- Outcome-unseen TRI OER: 8,447 entities, 240 composition clusters, and four
  held-out plates. All-neighbor borrowing is -0.079% [-0.313,0.155%], all four
  absolute R² values are negative, the best-control contrast is -1.25%
  [-1.75,-0.75%], and every exploration contrast and hypothesis card has Holm
  p=1.0.
- Cross-target synthesis: +0.304% [-0.617,1.225%], I²=76.7%; one of two targets
  is directionally positive and neither passes the complete prediction gate.
  Balam Job 70888 and portable verification completed; all unfavorable rows and
  six failed cards remain reported.
- Cross-program CCA gate development: 97 directed edges, 20 tasks, and 13
  independent programme clusters. In leave-one-program outer predictions, CCA
  gives +1.58% mean programme utility [-0.23%,4.27%], covers 11/13 programmes,
  and makes one clearly harmful selection among 17 admissions. It retains only
  4/10 available clear benefits. Both frozen superiority contrasts have Holm
  p=0.270; adjacency-only is numerically stronger at +1.80%
  [-0.19%,4.52%]. The complete reconstruction verifier passes. Review whether
  this legitimately supports adjacency as a first-order proposal prior while
  falsifying global source credibility as a sufficient benefit selector.

## Required review output

For every issue, give:

- severity: fatal / major / minor;
- the exact unsupported inference or failure mode;
- the minimum defensible fix;
- whether the fix needs new data, compute, reanalysis, or reframing;
- whether the current manuscript can still be accepted without that fix.

Address, at minimum:

1. leakage, provenance dependence, circular analysis, outcome-selected methods,
   and whether frozen internal protocols are credible without public
   preregistration;
2. bootstrap units, small-n claims, multiple comparisons, dataset-level versus
   seed-level uncertainty, and the Krug test’s limitations;
3. whether the model and representation family is too narrow to support the
   conclusions;
4. whether KIT predictive transfer, external Caltech source ranking, passed
   wrong-source guards, and the diagnostic multi-neighbor portfolio jointly
   support component-level proof of feasibility for the proposed strategy;
5. whether the post-outcome portfolio is clearly quarantined from independent
   validation while still being used legitimately for method development;
6. whether Caltech supports any credibility interpretation at all, given weak
   or uneven source skill and a weak target model/backbone;
7. whether the five main figures visually and statistically support the stated
  hierarchy;
8. novelty relative to materials transfer learning, task similarity/meta-
   learning, multi-fidelity optimization, compensation-law critiques, and
   multi-database integration;
9. data/code availability, licensing, reproducibility, and what *Digital
   Discovery* editors are likely to require.
10. whether the post-result CCA-v2 architecture addresses the observed
    within-neighborhood ranking failures without pretending that it has already
    been validated, and whether its prospective efficacy, safety, coverage, and
    hypothesis-card gates are adequate.

End with:

- a one-paragraph verdict: reject / major revision / minor revision / accept;
- the three highest-leverage actions before submission;
- a claim-by-claim list of wording that must be weakened, deleted, or retained;
- the strongest alternative title and abstract framing you would recommend.

Do not propose additional tuning on the observed Caltech, Starrydata, or TRI
outcomes as a way to create confirmation. The next claim upgrade must be frozen
before a genuinely temporal block or prospective experiment, not obtained by
retrospective target shopping.

Specifically decide whether the CCA family-first result legitimately strengthens
the paper from “some neighboring ranks work” to “a reusable policy can convert
trusted neighboring ranks into broader OOD scientific-region exploration,”
given that it is outcome-informed and conditional on one target. Audit the
completed Starrydata/TRI programme and decide whether its null/boundary outcomes
support a reusable abstaining map even though they do not confirm CCA as a
general exploration policy.
