# Methodology, sourcing, and verification limits

## Scope

The catalog indexes resources that contain measured materials or chemistry data.
Entries may also include computational values and are then labelled `mixed`.
Purely computational resources are excluded from the active catalog and retained
in `catalog/excluded_computational.json`.

The catalog is a metadata index. It does not certify that a resource is
scientifically correct, currently reachable, openly licensed, or legally
redistributable. Access and license are separate fields because "free to read"
does not imply permission to reuse or redistribute.

## Discovery and review

Candidates originate from:

1. repository APIs such as Zenodo, Figshare, Dryad, Materials Cloud, and NIST;
2. scholarly metadata services such as DataCite, Crossref, and OpenAlex;
3. documented domain databases and their bulk/API endpoints;
4. manual curation from primary dataset papers and repositories.

Automated discovery output is not accepted directly. A record is added only
after a curator inspects an evidence page and assigns scope, data type, access,
license, DOI, domain, and description. `verified_via` stores the evidence URL
used during that review. For many entries this equals the homepage; it is not a
time-stamped independent verification event. A future live-link audit must be
reported separately.

## Structural validation

`scripts/validate_catalog.py` checks JSON schema conformance, required fields,
identifier uniqueness, and duplicate DOI conditions. It does not:

- test every URL on every build;
- resolve licenses marked `Unknown`;
- validate scientific measurements;
- guarantee that a download is machine-readable;
- turn registration or restricted resources into open resources.

The snapshot audit in `analysis/audit_snapshot.py` publishes counts for access,
license completeness, source coverage, entity parsing, and property-specific
exclusions.

## Local integration

The optional SQLite snapshot is built locally and is not committed. Each source
is pinned to a commit in `scripts/localdb/sources.lock.json`. The builder writes
native raw tables and a long-form `measurements` table containing:

- dataset and original source-row identifier;
- raw material representation and canonical formula/SMILES/mixture key;
- property, numeric value, and original unit;
- structured conditions JSON;
- DOI or source reference;
- source commit and machine-readable quality flags.

This schema is a loss-aware integration layer, not a fully harmonized scientific
ontology. Property labels and units remain source-level unless a conversion has
been explicitly implemented. Analyses must therefore select one property/unit
definition at a time and state any validity filters.

### Entity resolution

Conventional and parenthesized chemical formulas are parsed into normalized
element fractions; OCx hyphenated alloy fractions are handled explicitly.
SMILES are canonicalized with RDKit. Unparsed entities remain in the database
with quality flags and are excluded from modeling.

Named-component liquid formulations use a separate `mixture` entity type.
Component amounts are normalized to a scale-invariant key, so changing batch
size without changing PC/EC/EMC/LiPF6 proportions does not create a new
formulation. Mixtures are never encoded as fictitious elemental formulas.
For CALiSol, the key also namespaces the reported salt identity, concentration
unit, and solvent-ratio convention so that molar, mass, and volume ratios are
not silently equated. One digitized row has a negative salt concentration; it
remains in the native raw table but is excluded from normalized measurements.

Entity resolution is applied before train/test auditing. In OBELiX, two test
compositions become identical to training compositions after scale
normalization even though their raw strings differ; those test rows are removed
from the primary benchmark.

### Property validity

Validity rules are property-specific. Positivity is required only where the
physics or transformation requires it (for example, conductivity before a
logarithm). Signed log-solubility and hydration-free-energy values are retained.
The former global `value > 0` rule is prohibited.

### ISODB analysis-only stream

The previous loader selected maximum uptake at maximum pressure from each
isotherm. Those points do not share pressure or loading and cannot yield a valid
van't Hoff/isosteric enthalpy; that normalization remains removed. ISODB still
contributes zero rows to the formula/SMILES measurement table because its
adsorbents use database identifiers rather than chemical formulas and because a
historical path cannot be materialized on Windows.

The corrected analysis uses the commit archive and SHA-256 pinned in
`sources.lock.json`, streams JSON members in memory, and never extracts them.
Pure-component systems are keyed by DOI, adsorbent, adsorbate and units. Each
eligible isotherm has at least five finite positive points and a monotone
pressure–uptake relation; each system has at least three temperatures and a
common uptake interval. The primary fit uses one geometric-midpoint uptake per
system, interpolates pressure at that loading, collapses duplicate temperatures
by the median, and fits `ln(p/bar)` against `1/T`. This produces one primary
enthalpy/intercept pair per system rather than treating multiple uptake levels
as independent observations. Full rules and sensitivity grids are frozen in
`analysis/ISODB_ISOSTERIC_SPEC.md`.

### BIRDSHOT external campaign

The pinned BIRDSHOT v5 table contains 171 experimental rows and 151 unique
nominal compositions. Nominal atomic percentages sum to 100 and are converted
to the same scale-invariant formula key as other inorganic datasets. There is
zero exact composition overlap with Borg. External confirmation uses rolling
campaign time: Year 1 predicts Year 2, and Years 1–2 predict Year 3. Exact
compositions do not cross either temporal boundary. Repeated rows of one
composition within a year are reduced to a median before modeling.

### Matbench steels external boundary

The experimental steel table and the official five-fold Matbench validation
file are pinned independently by SHA-256. Yield strength is the target. Same-row
tensile strength and elongation are forbidden target-model inputs. Every exact
target composition is excluded from each external source fit before the
official test fold is evaluated. This test is an independent negative boundary,
not a source for retuning the internal map.

### KIT electrolyte local-neighbor test

The 5,035-row Zenodo file is pinned by SHA-256 and normalized as temperature-
specific `electrolyte_conductivity` measurements on named-component mixtures.
The raw rows are not independent: 504 experiment IDs represent 109 unique
formulations measured at up to ten temperatures. For modeling, replicate
experiments are reduced to the median within each formulation and temperature.

The frozen target is conductivity at −30 °C with 30 target formulations per
outer fold; the primary source is −20 °C. Exact formulations define five
balanced group folds. The source model is trained only on outer-development
formulations, and its feature values for target-training formulations are
themselves inner-fold cross-fitted. Thus no target-test formulation supplies a
source-temperature label or in-sample source prediction. Composition inputs are
PC, EC, and EMC fractions of total solvent plus LiPF6/solvent mass ratio.

Arrhenius activation energy, pre-exponential factor, fit scores, fitted
conductivity vectors, and every EIS fit output are forbidden because they are
derived from the same temperature series as the target. Frozen controls use 0,
30, and 60 °C sources plus a shuffled −20 °C source-label model. The design and
the transparent implementation amendments are recorded in
`analysis/kit_temperature_borrowing_design.json` and
`analysis/KIT_TEMPERATURE_BORROWING_AMENDMENT.md`.

### CALiSol paper-disjoint external boundary

The CALiSol-23 CSV and DTU item version are pinned by file SHA-256. Of 13,825
raw rows from 27 source articles, 13,301 have a finite conductivity and a
physically valid nonnegative salt concentration and enter the measurement
table. The analysis uses the original source-article DOI as a grouping variable
but never as a predictor.

The frozen target is the −40 °C nominal window (observed temperature within
±2.5 °C), selected before modeling as the coldest 10 °C-grid slice represented
by at least ten articles. The primary source is −30 °C; −20, 0, and 20 °C are
increasing-distance controls. Conductivity values at or below 10⁻¹² mS cm⁻¹
are treated as numerical zeros and excluded before the log10 transform. Two
chemistry identities reported by multiple target articles are removed before
fold assignment.

Five outer folds hold out complete source articles and balance target row
counts. For a target-test article, every source-temperature row from that
article and every exact test chemistry identity reported anywhere else are
excluded from the source fit. Priors for target-training formulations are
leave-one-article-out predictions. The composition model uses reported salt,
concentration and unit, solvent-ratio convention, and all 38 solvent columns;
article DOI, temperature, another measured conductivity, and all Arrhenius/VTF
or target-series-derived values are forbidden.

The primary interval hierarchically resamples target-label repetitions,
articles, and formulations. The feature-mapping null is stratified within
article. Rescue uses the same practical, absolute-utility, fold, label-saving,
learner, source-quality, leakage, learning-curve, distance, and placebo gates as
KIT. The frozen result fails multiple gates and is retained without selecting a
different temperature edge. Design and implementation history are in
`analysis/calisol_external_borrowing_design.json` and
`analysis/CALISOL_EXTERNAL_BORROWING_AMENDMENT.md`.

## Statistical claim gate

Candidate cross-domain claims require:

1. canonical entity-overlap audit;
2. group or official split that preserves provenance and repeated entities;
3. a designated target, sample size, learner, endpoint, and source family;
4. adequate repetitions with saved per-repeat results;
5. uncertainty that reflects both training-sample and held-out-group variation;
6. a source-label or matched-feature null;
7. multiplicity correction across source hypotheses;
8. learner/feature sensitivity reported separately;
9. independent target confirmation before generalizing beyond an audited edge
   inventory.

All freezes in the current study are internal, author-controlled, and self-
attested rather than externally preregistered. A design fixed after inspection
of a related endpoint is described as prespecified given prior screening, not
independently confirmatory.

A **local rescue** claim additionally requires a prespecified practical effect,
confidence interval above zero, positive absolute R², all group folds in the
same direction, target-label equivalence above threshold, learner robustness,
positive source OOF performance, zero test-formulation exposure, a mapping-
permutation p-value below 0.05, a valid learning curve, correct neighbor-
distance ordering, and a failed shuffled-source placebo. Passing these gates
within one campaign does not establish independent-dataset or field-level
rescue.

The frozen KIT target-label equivalence gate was specified on the interpolated
point estimate. A separate post-outcome diagnostic resamples formulations and
target-training repetitions at every curve budget. Its 21.84--49.91% interval
crosses the 30% point threshold, so the frozen decision is retained but the
label-saving magnitude is not presented as an uncertainty-qualified lower
bound.

A small p-value from one fixed target subset is not sufficient for rescue when
the repeated-effect interval, practical threshold, absolute R², group-fold,
label-saving, or neighbor-ordering gates fail. This rule is material for the
CALiSol result and prevents one favorable conditional test from overriding the
full frozen decision.

The knowledge-map workflow additionally separates discovery and internal
confirmation entities, freezes practical effect and target-equivalence gates,
and applies uniform permutation resolution to every discovery-selected edge.
An independent result may be statistically directional yet fail a practical
gate; this is reported as directional replication rather than external
confirmation. Post-outcome budget or model sensitivities cannot redefine that
decision.

Map-level physical ordering is a separate hypothesis from the existence of one
edge. A significant source–target edge does not establish that an ordinal
distance score predicts effects across targets. Calibration/closure edges are
reported but excluded from the scientific neighborhood-ordering claim.

Feature importance of a derived source prediction is not treated as mechanism.
The source prediction is a function of the same input composition and can act as
a nonlinear basis or regularizer without encoding transferable physics.

## OOD decision endpoints

Average held-out prediction, fixed-ranking OOD screening, and sequential
discovery are evaluated as different endpoints. A favorable predictive metric
does not license a screening or discovery claim. The frozen fixed-ranking test
reports the fraction of a held-out candidate pool inspected before the first
top-5% target, paired uncertainty, multiplicity, repeat consistency, and a
practical-effect threshold. The hard-composition subset is explicitly
exploratory and cannot redefine the official-test decision.

The sequential OBELiX protocol uses paired seeds, a fixed initial target sample,
a 40-acquisition budget, and the official 110-candidate test pool. Target-only,
thermoelectric-prior, shuffled-prior and uniform-random policies share the same
candidate pool and target outcomes. Improvement requires a confidence interval
above zero, at least five acquisitions and 25% saved, at least 60% improving
seeds, acceptable censoring, a failed shuffled placebo, and Random-Forest
sensitivity. No primary or sensitivity result passes all gates. The random
reference is used only to diagnose the tested policy on this retrospective
pool; it is not treated as evidence that random search is generally optimal.
The sequential protocol was fixed after the direction of the earlier fixed-
ranking result was known, so it is not an independent confirmation.

The independent Caltech ionic-conductor protocol tests source admission and
acquisition utility. Exact target formulas and DOIs are
removed from every source fit. Source residual ranks receive nonzero weight
only after article-grouped cross-validation, and mechanical, catalysis, and
shuffled controls must remain below frozen admission and mean-weight ceilings.
The primary cumulative-recovery contrasts require statistical, practical,
consistency, first-hit, absolute-recall, and two-scope success. No adaptive
source increment passes. Prespecified static rankings are reported separately
as descriptive evidence because static-source attribution was not in the
frozen contrast family; the post-result neighbor portfolio is method selection
for a new target, not a Caltech discovery result.
Source OOF R² is 0.065 for OBELiX, 0.257 for ESTM, and 0.543 for the OCx wrong-
domain control. Admission ordering therefore cannot be interpreted as source
credibility, and the adaptive null cannot isolate source weakness from policy
conversion.

## Publisher content and TDM

The project does not bulk-scrape publisher supporting information or bypass
access controls. If a dataset is available only through a publisher, the catalog
links to its DOI or uses an official TDM/API channel under the applicable
agreement. Freely accessible content is not assumed to be licensed for bulk
reuse.

## Licensing

- Repository code: MIT.
- Catalog metadata authored here: CC-BY-4.0.
- Source data: governed by each source. `Unknown` remains an explicit unresolved
  state.
- The generated SQLite file must not be redistributed until every included
  source's terms and attribution requirements have been checked for that use.

## FAIR alignment and limits

The catalog improves findability and records access, provenance, citation, and
license metadata. The pinned builder improves reproducibility. It does not by
itself solve semantic interoperability, unit harmonization, uncertainty
representation, or long-term preservation. These limitations must remain in the
manuscript and data-availability statement.
