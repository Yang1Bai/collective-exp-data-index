# Claude second-pass integration record

## Outcome

The second-pass review was accepted as a scientific audit, not as a source of
unchanged replacement prose. Risks R1--R5 were checked against the current
results, and all wording-only corrections were integrated. Two requested
reanalyses were completed. A third audit uncovered a previously unreported
target-semantics error that required correction of the headline prediction
case.

## Dispositions

| Review risk | Disposition | Evidence or change |
|---|---|---|
| R1: generic-failure and qualified-success sets are disjoint | Accepted | Abstract and Results now state that the 0/40 benchmark and the positive demonstrations use separate recipients. The manuscript no longer implies that a declared relation repaired those same failed edges. |
| R2: FINALES anchor policy differs | Accepted and reanalysed | Methods disclose the frozen-identical and differing elements. A 100-start maximin sensitivity over 17 unique anchor sets remained negative on average; this is explicitly post-outcome and does not replace the frozen result. |
| R3: unseen salt may be representation-interpolative | Accepted and extended | A descriptor-space applicability audit shows identity/provenance OOD but partial representation support: all target temperatures and concentrations lie within source ranges, only 30.4% of target solvent identities occur in the source, and 60.8% of target rows lie inside the source 95th-percentile full-representation distance boundary. |
| R4: protocol and edge selector were blurred | Accepted | Discussion now reports that the outcome-free selector retained 4/10 available benefits, did not beat never-borrowing after Holm correction, and was numerically weaker than adjacency. The protocol is claim-bearing; the selector is not. |
| R5: 0/40 composition was hidden | Accepted | Main text and Figure 2 caption now state five within-database and three cross-database designated edges, with no cross-database pass. |

## Additional semantic correction

The file named `LiAsF6_conductivity.json` contains 1,827 rows from five salts,
not only LiAsF6. The original retrospective analysis inadvertently evaluated
all rows as the declared target. Existing predictions were therefore filtered
without refitting or tuning to the 1,660 strict LiAsF6 rows (156
formulations). Corrected headline values are raw (R^2=0.607), log
(R^2=0.718), Spearman (ho=0.864), and a 27.41% formulation-grouped
log-RMSE gain over the state-only comparator (95% interval 21.79--32.92%).
The correction is disclosed as post-outcome and is propagated to the
manuscript, Supplementary Information, paper package, README, Figure 1,
Figure 3 and the semantic verifier.

## Figure restructuring

The four-figure layout was replaced by a five-figure evidence sequence:

1. falsification-gated workflow and three decision routes;
2. failure of strong fits and generic donor-feature injection;
3. strict LiAsF6 numerical relation transfer;
4. controlled catalyst routing to prediction, ranking or rejection;
5. zero-label ordinal screening and frozen-recipient abstention.

All five canonical figures have editable SVG and PDF exports plus 300 dpi PNG
and 600 dpi LZW TIFF files. Their quantitative anchors are checked by
`analysis/verify_main_figures_v4.py` and recorded in
`analysis/results/main_figures_v4_verification.json`.

## Deferred item

The proposed generic anchored-delta arm was not treated as a drop-in model
variant. Subtracting an anchor constant is algebraically inert for several of
the existing learners, while fitting an outcome-informed correction without a
declared pairing rule would silently change the estimand. A valid follow-up
must freeze a cross-row anchor-pairing rule, a delta target, the anchor budget,
and comparators before execution. Until that design exists, the manuscript
uses the defensible R1 wording fix and does not claim that relation transfer
repairs the 0/40 benchmark edges.

## Remaining release blockers

The persistent data/code DOI, clean-environment reproduction, author metadata,
and redistribution decision remain open and are not scientific-analysis
results.
