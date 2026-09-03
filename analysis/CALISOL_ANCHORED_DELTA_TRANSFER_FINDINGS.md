# E6 findings: provenance-anchored neighboring-condition contrast transfer

## Verified result

E6 is complete and independently verified. The frozen design SHA-256 is
`04279e568830b14a92199d165c96a6a3b05d55b6c64ce54b5c7eb046eb2c1cfe`.
The verifier reconstructed 33,579 non-anchor predictions, 429 article-level
metrics, 199 shuffled-source permutations and 300 random-anchor sensitivity
rows. The formal decision is `mechanistic-rescue`.

E6 was motivated after the original CALiSol outcome was known. It is therefore
a post-outcome mechanistic reanalysis, not an independent or preregistered
confirmation.

## What changed

The donor, recipient, formulation features and article boundary did not
change. Only the transferred object and deployment contract changed.

- **Original strategy:** predict absolute -30 degrees C conductivity and add
  that prediction to a scarce-label -40 degrees C target model.
- **E6 strategy:** learn how formulation changes alter -30 degrees C
  conductivity within each source article, then use one observed -40 degrees C
  formulation from a new article to restore its absolute scale.

The primary comparator used the same -30 degrees C donor rows and the same
target anchor but transferred an ordinary absolute conductivity function.
Thus the primary contrast isolates the effect of transferring a
within-provenance response relation.

## Primary one-anchor result

The common evaluation scope contained 883 -40 degrees C formulations from 11
held-out articles. Each article had at least eight eligible formulations. One
feature-medoid formulation per article was revealed as an anchor and excluded
from scoring.

| Quantity | Verified value |
|---|---:|
| Macro-RMSE, absolute neighboring model | 0.4901 log10(mS cm-1) |
| Macro-RMSE, neighboring contrast model | 0.4562 log10(mS cm-1) |
| Relative macro-RMSE gain | **6.91%** |
| Article-cluster bootstrap 95% interval | **0.88% to 14.00%** |
| Exact one-sided article sign-flip p | **0.0352** |
| Articles improved | **8 of 11** |
| Pooled non-anchor R2 | **0.234** |
| Gain over anchor-only constant | **29.84%** |

All frozen primary gates passed.

## Falsifiers and robustness

- The median within-article shuffled-donor contrast was -35.06% relative to
  the absolute donor model. The real contrast exceeded this null by 41.97
  percentage points; permutation p=0.005.
- A +20 degrees C wrong-condition contrast had macro-RMSE 0.5553 and negative
  pooled R2 (-0.062), whereas the neighboring -30 degrees C contrast had
  macro-RMSE 0.4562 and positive pooled R2 (0.234).
- Ridge penalties 1, 10 and 100 all retained a 6.4--6.9% primary advantage,
  so the result is not specific to the frozen penalty.
- Across 100 outcome-independent random anchor selections, the contrast model
  beat the absolute donor in 100/100 one-anchor runs. The median gain was
  6.24%, with a 10th--90th percentile range of 3.35--9.98%.
- The deterministic one-, two- and three-anchor contrasts all retained more
  than 5% macro-RMSE advantage over their same-anchor absolute donor. However,
  pooled R2 was not positive for the deterministic two- and three-anchor
  scopes. E6 therefore supports the frozen one-anchor contract and does not
  establish monotonic improvement with more anchors.
- Three of 11 articles were mildly harmful (-0.5% to -4.2%). The result
  supports selective transfer with abstention, not universal benefit.

## Scientific interpretation

The CALiSol pair now supplies a direct method-development result. Experimental
adjacency alone was insufficient: the original absolute donor feature remained
unresolved at +1.61%. After the transfer object was changed from an absolute
property prediction to a within-article response relation, one
target-provenance anchor produced a statistically and practically qualified
6.91% improvement over an otherwise matched absolute donor.

This is consistent with, but does not prove, an additive provenance-nuisance
mechanism. Article-specific offsets can be removed by within-article
contrasts and restored with a target anchor. The harmful +20 degrees C control
shows that anchoring does not make every source relation useful.

The defensible paper claim is:

> In one literature-aggregated electrolyte programme, a neighboring-condition
> response relation transported across held-out articles after a single
> target-article anchor, whereas absolute donor transfer did not. This
> post-outcome-motivated result identifies the transferable object and
> deployment contract that require independent replication.

It is not evidence for zero-shot transfer, universal cross-domain borrowing,
or prospective discovery acceleration.

