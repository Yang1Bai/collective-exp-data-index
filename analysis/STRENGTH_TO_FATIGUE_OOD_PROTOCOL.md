# Frozen protocol: independent static-strength knowledge for fatigue OOD prediction

## Scientific question

This experiment asks whether static mechanical knowledge learned from independent
experimental databases can repair fatigue-life prediction in publication- and
chemistry-disjoint regions of a data-poor fatigue database.

The scientific hypothesis is narrower than a universal strength--fatigue law.
Ultimate tensile strength (UTS) and yield strength (YS) define material-specific
stress scales. A donor prediction is therefore used to normalize the applied
cyclic stress, not merely appended as an unconstrained generic feature.

## Outcome-access boundary

The design in `strength_to_fatigue_ood_design.json` was frozen before any numeric
fatigue-life or stress-amplitude value was inspected. Before freezing, access was
limited to:

- Figshare article and file metadata;
- workbook sheet names and headers;
- the outcome-free `parameter` worksheet, including provenance, composition,
  processing, testing context, and static mechanical-property availability.

The `S-N`, `e-N`, and `dadn` numeric rows remain forbidden until the pre-outcome
audit and an independent verifier both pass.

## Donor and recipient roles

The primary donor is the Borg multi-principal-element-alloy database. It supplies
UTS and YS models learned from composition, broad processing and phase families,
and test temperature. The independent BIRDSHOT campaign supplies a
composition-only UTS support card and a donor-disagreement diagnostic.

The recipient is the MPEA subset of FatigueData-CMA2022 containing stress--life
curves. The primary response is log10 cycles to failure. Run-outs are retained
only in a separately declared censored secondary analysis.

Every DOI appearing in the recipient metadata is excluded from every Borg donor
fit. Recipient measured UTS and YS values are not formal features; they are
reserved as an oracle ceiling and semantic check.

## Physics-aligned borrowing

The target-only model receives composition, processing and phase flags, fatigue
test state, load ratio, frequency, and log stress amplitude.

The borrowed model additionally receives cross-fitted UTS and YS predictions and
stress ratios such as:

\[
\log_{10}\sigma_a-\widehat{\log_{10}\mathrm{UTS}}
\]

and

\[
\widehat{\sigma_{\max}}/\widehat{\mathrm{UTS}}.
\]

Borrowing is allowed only where composition support and agreement between
independent source cards satisfy donor-only thresholds. Outside that region the
policy returns the target-only prediction.

## Leakage boundary and OOD unit

The outer evaluation unit is a connected component of the bipartite graph
linking recipient DOI and canonical composition. This prevents either the same
paper or the same composition from crossing an outer split, including indirect
connections through repeated literature records. Whole S--N curves remain
intact.

The formal analysis uses leave-one-component-out evaluation and predeclared
few-shot budgets measured in whole curves. A hard-OOD subset is reported only if
at least five independent components fall in the highest source-distance
quartile.

## Controls

The frozen controls are:

1. target-only;
2. fold-wise shuffled UTS with the same architecture;
3. size-matched predicted hardness;
4. size-matched predicted elongation;
5. recipient measured UTS/YS as a clearly labelled oracle ceiling.

## Decision rule

A positive edge requires at least 5% relative RMSE improvement, a positive
component-clustered 95% interval, Holm-adjusted one-sided \(P<0.05\), positive
absolute augmented \(R^2\), at least 80% positive algorithmic repeats,
non-negative effects for both target learners, superiority to every matched
control, and at least 25% applicability coverage.

Failure of any gate is reported as null, harmful, or abstaining. It cannot be
repaired by changing the endpoint, split, feature contract, donor, or threshold
after fatigue outcomes are opened.
