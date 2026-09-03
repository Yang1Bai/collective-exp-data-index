# Pre-outcome label-budget implementation amendment

The frozen design specifies a Stage 2 target-label budget of four calendar
condition groups plus six cycle condition groups, for ten groups total. It also
requires the training-only borrowing gate to show positive cross-validated gain
in both aging strata.

The first generated split file mistakenly selected only groups of the same
aging type as the outer held-out group: four for a calendar test or six for a
cycle test. That implementation could not evaluate the prespecified two-stratum
gate. No Stage 2 numeric outcome had been opened.

The split generator was corrected before Stage 2 release. Every one of the 23
outer tests now receives exactly four calendar and six cycle target-training
groups. The held-out group is excluded from its own stratum. Within each
stratum, selection follows the already frozen deterministic maximin rule and
SHA256 tie breaking. The applicability plan was regenerated for outer-test,
outer-training, and nested-validation scopes, yielding 3,594 fully outcome-free
rows. The 0.20 threshold permits borrowing in 15 outer groups (six calendar and
nine cycle); those locations are now fixed.

No target, endpoint, label count, model, physical feature, threshold, primary
comparison, inferential rule, or claim boundary changed. This amendment aligns
the implementation with the original 4+6 design and makes the two-stratum gate
executable. Stage 2 remained sealed throughout.
