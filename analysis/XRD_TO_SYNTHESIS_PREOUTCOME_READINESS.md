# Pre-outcome readiness: experimental phase knowledge to solid-state synthesis

**Assessment date:** 2026-07-29  
**Decision:** **HOLD - do not fit a transfer model yet.**  
**Purpose:** decide whether experimental phase/XRD resources can supply candidate-available knowledge that improves out-of-distribution (OOD) prediction of solid-state synthesis outcomes.

## Scientific question

The useful transfer problem is not “use a target sample's measured XRD pattern to predict whether that same synthesis worked.” XRD is acquired after the experiment and would leak the answer. The admissible question is:

> Can a model trained on independent experimental reactions or phase observations convert precursor identity, composition, process state and thermodynamic context into a pre-experiment estimate of phase formation or impurity risk, and does that estimate improve OOD prediction in a separate synthesis programme?

The donor output must therefore be computable for every candidate before the target experiment is performed.

## Resource audit

| Resource | What it contributes | Pre-experiment usability | Role decision |
|---|---|---|---|
| **Precursor Genome (2026)** | 1,035 pairwise A-Lab solid-state reactions; 46 precursors and 39 elements; complete thermal and mass metadata; four reaction-outcome classes; 1,351 raw XRD scans; 1,950 refinement cases with expert quality scores | Strong. Precursor formulae, stoichiometry, reaction energy, temperature and time are available before synthesis. XRD-derived outcome labels are used only to train the donor | **Best donor and method-development benchmark** |
| **A-Lab target-synthesis campaign (2023)** | 355 recipes for 58 target compounds, with iterative recipe optimization and XRD-defined outcomes | Potentially strong, but the public article and supplement explicitly guarantee refined XRD for successful outcomes; a machine-readable table linking every attempted recipe, including failures, to a target-phase outcome has not yet been verified | **Best proposed recipient, but blocked** |
| **HTEM-DB** | Large thin-film collection with synthesis conditions, composition, XRD and optoelectronic measurements | Candidate metadata are available, but physical-vapour-deposited thin films are not state-matched to ceramic powder reactions | **Wrong-process control or later thin-film recipient; not a primary neighbour** |
| **opXRD** | 92,552 experimental powder diffractograms, including 2,179 labelled patterns, from many laboratories | Valuable for robust post-measurement phase identification. A raw XRD pattern is unavailable before synthesis, and most records do not define a candidate-level precursor/process-to-outcome mapping | **Characterization model only; not a valid pre-synthesis donor by itself** |

## Newly identified opportunity

The Precursor Genome materially improves the feasibility of this programme. Unlike a spectrum-only archive, it contains genuine negative and partial reaction outcomes under a controlled workflow:

- unreacted;
- transformed without forming the target;
- partially reacted;
- completely reacted;
- plus explicit physical-handling failures and expert refinement-quality scores.

This allows a donor model to learn **reaction propensity from precursor and process variables**, rather than using target XRD as an illicit feature. It is also a natural intermediate rung on the provenance ladder: the proposed donor and recipient are different campaigns but share a laboratory platform, solid-state mechanism and XRD outcome definition. A positive result would establish cross-program borrowing under strong state match; it would not by itself establish cross-laboratory generality.

## Proposed donor-to-recipient experiment

### Direction

**Donor:** Precursor Genome pairwise reactions  
**Recipient:** all A-Lab 2023 attempted target-synthesis recipes, if a complete attempt-level table can be recovered

### Candidate-available inputs

- precursor identities and formulae;
- precursor stoichiometry;
- target formula and element set;
- heating temperature, dwell time and atmosphere;
- thermodynamic reaction energy or phase-diagram descriptors calculated without target outcomes;
- furnace or campaign identifier, used for grouping rather than as a shortcut.

### Borrowed knowledge

Fit the donor on Precursor Genome only and generate cross-fitted probabilities for:

1. any reaction versus unreacted;
2. target-forming versus non-target-forming;
3. complete versus partial conversion;
4. physical-handling failure;
5. donor applicability and uncertainty for the candidate precursor pair.

The target-only model receives these probabilities and applicability terms as extra features. Raw recipient XRD, refined target phase fractions and any post-heating measurements are prohibited from the feature set.

### OOD evaluation

The primary test must hold out connected components built from:

- target composition;
- unordered precursor pair;
- experimental campaign or batch;
- article/provenance identifier where available.

No precursor pair, target composition or repeated campaign may cross from training to test. Evaluation units are held-out chemical systems or campaigns, not random rows or random seeds.

### Required comparators

- identical target-only model;
- donor trained with shuffled reaction outcomes;
- thermodynamics-only augmentation;
- temperature/process-only augmentation;
- size- and support-matched wrong-process donor from HTEM thin films;
- donor with target-forming labels replaced by generic “any reaction” labels;
- an oracle using recipient XRD, reported only as an upper bound and never mixed with the formal comparison.

### Acceptance gate

A transfer edge is accepted only if it:

- improves the prespecified proper scoring rule by at least 5% relative to target-only;
- has a cluster-bootstrap 95% lower bound above zero;
- survives Holm correction across declared donor variants;
- improves calibration rather than only rank ordering;
- is positive for both declared model families;
- beats shuffled, wrong-process and thermodynamics-only controls;
- retains at least 25% of the OOD recipient candidates after applicability gating.

Otherwise the method must abstain and the edge is recorded as null or harmful.

## Blocking evidence

The experiment must not be frozen or launched until the following recipient fields are verified for **all 355 attempts**, not only successful targets:

1. unique attempt and target identifiers;
2. precursor identities, amounts and target stoichiometry;
3. temperature, time, atmosphere and iteration order;
4. target-phase fraction or a reproducible success definition;
5. failed and partial outcomes;
6. campaign/batch grouping and repeated-recipe links;
7. a stable download route, licence and checksum.

The 2023 article's Data Availability statement describes refined XRD patterns and structures for successful syntheses. That is insufficient for an unbiased attempt-level recipient. Until the failed and partial attempts are linked to their candidate metadata, fitting this edge would introduce outcome-selection bias.

## Go/no-go rule

- **GO:** a complete 355-attempt outcome table is located and passes the seven field checks. Freeze its checksum, exclusions, OOD groups and primary metric before opening numerical target-phase outcomes.
- **NO-GO:** only successful patterns/structures are available, failures cannot be linked to recipes, or the target label requires viewing candidate XRD at prediction time.
- **Fallback:** use Precursor Genome internally to develop and stress-test the applicability gate with precursor-pair and element-family holdouts. Label this as within-programme method development, not cross-database validation.

## Manuscript use

Do not add this as another showcase until it passes the full gate. If it succeeds, it fills a missing middle rung between same-specimen transfer and fully independent cross-database transfer:

> physically matched, outcome-free knowledge can transfer across experimental campaigns when the donor describes the same reaction state and the model abstains outside its precursor/process support.

If it fails or remains blocked, the readiness audit still supports the paper's method: database scale alone is not enough; transfer requires candidate-time semantics, negative outcomes and provenance-resolved evaluation.

## Sources inspected

- Walters et al., *The Precursor Genome: A Pairwise Reaction Dataset for Solid-State Synthesis*, arXiv:2607.09903 (2026); GitHub `lauren-walters/precursor-genome`; Zenodo 10.5281/zenodo.21285546.
- Szymanski et al., *Nature* **624**, 86-91 (2023), DOI 10.1038/s41586-023-06734-w.
- Zakutayev et al., *Scientific Data* **5**, 180053 (2018), DOI 10.1038/sdata.2018.53.
- Hollarek et al., *Advanced Intelligent Discovery* (2026), DOI 10.1002/aidi.202500044; opXRD Zenodo 10.5281/zenodo.14279434.

