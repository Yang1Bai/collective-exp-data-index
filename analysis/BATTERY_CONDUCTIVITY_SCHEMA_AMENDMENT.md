# Battery Conductivity Borrowing Schema Amendment

Frozen before reading any row-level numeric property value.

The released archive stores state information inside the textual metadata
fields `Specifier`, `Tag`, `Type`, and `Info`; it does not expose separate
current-rate, cycle, or temperature columns. The pre-outcome audit therefore
uses fixed regular expressions over those fields to identify:

- dimensionless C-rate or mass-normalized current;
- an explicit cycle reference;
- an explicit temperature;
- a gravimetric-capacity unit family.

This is a schema accommodation, not an endpoint change. The primary endpoint
remains gravimetric capacity with explicit rate and early-cycle state. The
audit may report condition strings because they are predictors/state metadata,
but it remains forbidden from reading `Value`, `Raw_value`, or the lowercase
`value` column.

The frozen maximum exact-duplicate fraction cannot be evaluated without
property values. During the outcome-blind gate, the analysis reports the more
conservative fraction of rows duplicated on all available non-outcome
metadata. Exact outcome duplicates are checked only after the pre-outcome
eligibility gate has passed and the formal analysis release is created.

Before any numeric property value was read, the schema audit also evaluated
the author-provided `battery-2022-merged.csv`. That table removes publication
identifiers, so it cannot support the frozen publication-OOD and donor
exclusion rules. The formal analysis therefore retains `battery-2022.csv` and
collapses exact duplicates only after the outcome release, using publication,
material, property, normalized value, unit, and state together. The
author-merged table is not used for modelling.

The released schema rarely co-reports current and cycle in the same extracted
relation. Requiring both leaves 336 records and would make a
publication-plus-chemistry OOD interval unstable. Therefore, before outcome
access, the formal prediction primary is defined as gravimetric capacity with
an explicit mass-normalized current. Cycle number is included when available
and otherwise represented by an explicit missingness indicator. The frozen
early-cycle subset (cycle number at most 10) remains a mandatory mechanistic
sensitivity and cannot replace or rescue the formal primary result.
