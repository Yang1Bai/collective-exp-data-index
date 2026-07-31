# Starrydata2 reverse-transport header-only schema amendment

**Frozen:** 2026-07-18T04:03:02Z, after the three files matched the hashes in
`starrydata_reverse_transport_design.json` and after reading only CSV headers
and descriptor/condition columns. No `y` column, target outcome, or high-value
material identity was read for this amendment.

## Verified source schema

- `ThermoelectricMaterials_papers.csv.gz`: `SID`, `DOI`, `URL`, `issued`,
  bibliographic fields, project membership, and creation time.
- `ThermoelectricMaterials_samples.csv.gz`: `sample_name`, `sample_id`,
  `composition`, `composition_details`, `SID`, `DOI`, timestamps, and
  `sample_info`.
- `ThermoelectricMaterials_curves.csv.gz`: `SID`, `DOI`, `composition`,
  `sample_id`, figure identifiers, `prop_x`, `prop_y`, `unit_x`, `unit_y`,
  list-valued `x`, list-valued `y`, timestamps, project membership, and
  comments.

The descriptor-only scan found 20,465 curves with `prop_x=Temperature`,
`prop_y=ZT`, `unit_x=K`, and `unit_y=-`, plus 64 otherwise equivalent curves
with `prop_x=T`. Without reading `y`, 7,568 curves and 7,486 `(SID,sample_id)`
keys had at least one temperature within 25 K of 800 K. This comfortably
exceeds the frozen minimum target size.

## Frozen target extraction

1. Keep curves satisfying:
   - `prop_y == "ZT"`;
   - `unit_y == "-"`;
   - `prop_x in {"Temperature", "T"}`; and
   - `unit_x == "K"`.
2. Parse list-valued `x` and `y` without reordering. Reject a curve when the two
   lists have unequal length or contain no paired finite values.
3. Select the point with temperature closest to 800 K when its distance is at
   most 25 K. Break equal-distance ties by lower temperature, then original
   list position.
4. Retain finite `ZT` in the physically broad, predeclared range `0 <= ZT <=
   10`. Every range exclusion is counted and reported.
5. Join curve records to sample and paper metadata by `(SID,sample_id)` and
   `SID`. Resolve DOI by preferring a nonempty curve DOI, then sample DOI, then
   paper DOI; disagreement is a quality flag and the record is excluded from
   confirmatory inference.
6. Canonicalize `composition` using the repository's scale-invariant formula
   parser. Reject missing or ambiguous formulae rather than inferring them from
   names or comments.
7. For repeated eligible curves belonging to the same
   `(SID,sample_id,canonical_formula)`, use the median selected ZT as the target
   outcome and retain the replicate count, selected temperatures, figure IDs,
   and within-key range.

## Outcome-free split and component construction

- The provenance group is normalized DOI when present and otherwise `SID`.
- Assign complete provenance groups to development, validation, and evaluation
  by SHA-256 hash order in a 60:20:20 ratio. The hash salt is
  `starrydata-reverse-transport-v1`.
- Construct connected components before outcome access using shared canonical
  formula, provenance group, or sample lineage. A second composition-cluster
  resolution is frozen from development-standardized element fractions.
- Exact target formulae and target DOI/SID groups are excluded from every
  source fit. All exclusions are counted by source.
- The primary OOD score is nearest-development-label Euclidean distance in the
  development-standardized element-fraction representation. The primary hard-
  OOD scope is the farthest 40% of the fixed evaluation set; quartiles are
  required for the prediction surface.

## Frozen source and baseline comparisons

- Same-domain reference: ESTM ZT.
- Adjacent transport sources: OBELiX and Caltech ionic conductivity, retained
  as separate ranks.
- Wrong-domain controls: Borg yield strength and OCx H2 Faradaic efficiency.
- Every source receives source-size, source-skill, target-coverage, shuffled-
  rank, and equal-capacity random-feature controls.
- Prediction compares target-only, naive pooling where label units permit,
  source-only, frozen stacking, residual shrinkage, and a mixture-of-experts
  baseline under the identical provenance split.
- Exploration compares CCA family-first consensus and round-robin with random,
  composition novelty, best single source, entity consensus, wrong-source, and
  shuffled-source portfolios.

## Outcome-access sentinel

Target `y` values may be parsed only after an outcome-free metadata table,
formula/provenance exclusions, source predictions, component assignments,
policy orders, and hypothesis cards have been written and SHA-256 hashed. Any
schema change after outcome access is an outcome-informed amendment and cannot
alter the primary endpoints.
