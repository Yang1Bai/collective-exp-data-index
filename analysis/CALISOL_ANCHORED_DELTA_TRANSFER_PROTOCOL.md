# E6 protocol: provenance-anchored contrast transfer in CALiSol

## Purpose and evidential status

E6 tests a mechanism suggested after the original CALiSol result was known.
The original absolute donor-feature strategy reduced paper-disjoint RMSE by
only 1.61% (95% interval, -2.14% to 4.21%) and failed the frozen rescue gate.
E6 is therefore a **post-outcome-motivated mechanistic reanalysis**, not a
preregistered confirmation or an independent replication. The complete E6
design is locked before any E6 prediction or effect is computed.

The mechanism is specific. Experimental articles can differ by approximately
additive offsets arising from laboratory, protocol, instrument, reporting and
other provenance-dependent factors. Such offsets can destroy transfer of
absolute property values even when the response to a formulation change is
partly stable. E6 therefore transfers a within-article response relation and
uses a small number of target-article measurements to restore the absolute
scale.

This is inspired by bilinear transduction and chemistry-informed domain
transformation, but it is not an implementation or claimed reproduction of
MatEx. MatEx predicts a target value from an anchor and a feature difference
under an output-tail OOD construction. E6 instead tests an article-level
additive-nuisance hypothesis under an outcome-independent provenance split.

## Data and OOD contract

The analysis reuses the hash-pinned CALiSol-23 table and the exact
formulation representation frozen for the original analysis. The recipient is
log10 conductivity at -40 degrees C. The neighboring donor is conductivity at
-30 degrees C. The OOD unit is an entire source article DOI.

The original eligible recipient table contains 891 paper-specific
formulations from 15 articles. E6 uses a fixed common scope of the 11 articles
having at least eight eligible -40 degrees C formulations. This leaves at
least seven, six and five scored non-anchor formulations per article at
anchor budgets one, two and three, respectively. The common scope contains
883 formulations. The four smaller articles remain disclosed but cannot
support a stable common-budget article-level RMSE.

For every held-out article:

1. all rows from that DOI are removed from donor training;
2. every exact held-out recipient chemistry is removed from donor training,
   even if found under another DOI;
3. preprocessing is fitted only on remaining donor rows;
4. one to three recipient outcomes are revealed as anchors;
5. all remaining recipient outcomes stay hidden until predictions are fixed;
6. anchor rows are never included in the reported test error.

This is few-shot adaptation to a new provenance unit, not zero-shot
prediction.

## Outcome-independent anchor selection

The primary anchors are selected without conductivity values. Formulation
features are standardized using only source-training rows. The first anchor is
the feature medoid of the held-out article. Additional anchors follow a
deterministic farthest-point traversal. Ties are resolved by the frozen unit
key. Predictions from multiple anchors are averaged without outcome-derived
precision weights.

One hundred random, outcome-independent anchor selections are retained as a
sensitivity analysis. They cannot replace the deterministic primary result.

## Transfer estimators

### Neighboring-condition contrast model

The primary model uses -30 degrees C rows from non-held-out articles. Within
each source article, standardized formulation features and log conductivity
are centered. A ridge model with no intercept learns the centered response,
with rows weighted so each article contributes equal total weight. For anchor
\(a\) and candidate \(t\),

\[
\widehat y_t = y_a + \widehat{\Delta f}(x_t-x_a).
\]

Multiple-anchor predictions are averaged. The transferred object is thus a
response relation, not an absolute donor prediction.

### Same-contract comparators

- **Absolute neighboring-condition model:** an ordinary ridge model trained
  on the same -30 degrees C rows, then offset-calibrated with the same target
  anchors. This is the primary comparator because it changes only the
  transferred object.
- **Anchor constant:** the mean anchor outcome predicts every candidate. This
  isolates the information supplied by the anchor itself.

### Falsifiers and diagnostics

- **Shuffled contrast:** donor outcomes are permuted within source article
  before contrast fitting. This preserves article sizes and outcome
  distributions while destroying the formulation-response relation.
- **Wrong-condition contrast:** the same method is trained at +20 degrees C.
- **Same-condition contrast ceiling:** the same method is trained on -40
  degrees C rows from other articles. It diagnoses whether a response
  relation can cross articles at all, but cannot support a
  neighboring-condition claim.
- Ridge penalties 1 and 100 are reported as model sensitivities around the
  frozen primary penalty 10.

## Estimand and inference

The independent unit is the source article, not a formulation, pair, anchor or
model seed. For each article, RMSE is computed over non-anchor formulations.
The portfolio RMSE is the unweighted mean of the 11 article RMSE values. The
primary effect is

\[
1-\frac{\mathrm{macro\ RMSE}_{\mathrm{neighbor\ contrast}}}
        {\mathrm{macro\ RMSE}_{\mathrm{absolute\ neighbor}}}
\]

at one anchor. This isolates the benefit of transferring a within-provenance
response relation rather than an absolute function.

Uncertainty is obtained by 10,000 article-cluster bootstrap resamples.
Because only 11 independent articles are available, the paired article-RMSE
difference is also tested with an exact one-sided sign-flip enumeration. There
is one primary comparison. Anchor-budget, wrong-condition, same-condition,
random-anchor and ridge-penalty results are secondary and cannot be promoted
after inspection.

## Frozen decision rule

E6 is called a mechanistic rescue only if all of the following hold at one
anchor:

- relative macro-RMSE gain over the absolute neighboring model is at least
  5%;
- the article-bootstrap interval has lower bound above zero;
- the exact one-sided sign-flip \(p\) value is at most 0.05;
- at least 8 of 11 articles improve;
- pooled non-anchor \(R^2\) is positive;
- relative macro-RMSE gain over the anchor constant is at least 5%;
- the gain exceeds the median shuffled-contrast gain by at least 3 percentage
  points and the 199-permutation \(p\) value is at most 0.05;
- held-out-article and exact-chemistry leakage counts remain zero.

A positive result supports one few-shot, neighboring-condition transfer
contract. A null result means that additive article offsets are insufficient
to explain the provenance boundary or that the -30 to -40 degrees C response
relation is not stable. A negative result means the response relation itself
does not cross articles and the method must abstain at this rung.

