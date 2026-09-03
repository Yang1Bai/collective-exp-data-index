# OPV optical borrowing: preoutcome implementation alignment amendment

## Trigger

After the infrastructure failures of jobs `71577` and `71578`, the complete
formal code path was re-reviewed before permitting another Balam submission.
Both failed jobs stopped before row-level target outcomes were opened.

## Design-to-code findings

The frozen protocol states that recipient-state encoding is learned from the
available labelled target data.  The initial implementation excluded the
external DOI holdout but fitted categorical frequencies and numeric robust
scaling on the entire unlabeled development pool.  Although this did not use
outcomes, it was a transductive preprocessing choice and did not implement the
stricter frozen wording.

The protocol also declares a secondary physically recombined efficiency,
predicted open-circuit voltage times short-circuit current density times fill
factor divided by 100.  The initial implementation fitted and reported all
four endpoints but had not emitted this secondary recombined metric.

## Alignment changes

For every label budget and repeat, categorical state frequencies, numeric
medians and numeric interquartile ranges are now fitted only on that repeat's
60, 120 or 240 labelled target records.  They are then applied unchanged to
the external DOI holdout.  Molecular fingerprints and frozen optical cards
remain deterministic and outcome independent.

The metrics table now contains `pce_physics_recombined` in addition to direct
PCE, open-circuit voltage, short-circuit current density and fill factor.
Primary prediction files retain all three predicted component endpoints and
the recombined value.  The independent verifier reconstructs both the
recombination identity and its RMSE from those stored predictions.

## Scientific lifecycle

These changes make the implementation conform to the pre-existing protocol;
they do not change the donor, recipient, split, label draws, OOD scopes,
learners, primary endpoint, contrasts, multiplicity correction, success gate
or claim boundary.  No row-level target outcome was read during the review or
implementation.  Synthetic outcomes are used only for workflow tests and
cannot support a scientific conclusion.
