# Edison clean-sheet research task

## Mission

Design a new, executable scientific programme that can demonstrate how knowledge from a neighbouring experimental domain improves cognition or decision-making in a data-poor out-of-distribution (OOD) region.

This is not a manuscript-polishing task and not a request to defend the current experiments. Most completed cross-database transfer attempts in the project are null, harmful, or too small to be scientifically meaningful. Treat those failures as constraints that reveal what ordinary transfer learning gets wrong.

You may replace the current:

- donor-recipient pairs;
- scalar donor-feature injection;
- Random Forest models;
- element-composition representations;
- global RMSE/R2 endpoints;
- definition of neighbouring domains;
- prediction task itself.

Do not preserve a direction because compute has already been spent on it.

The non-negotiable objective is:

> Identify a form of experimentally grounded neighbouring-domain knowledge that is portable, candidate-available, physically interpretable and independently testable, then show how it reduces a recipient domain's OOD knowledge deficit without outcome leakage or negative transfer.

The intended paper contribution is not a universal materials law. It is a mechanism-aware method for deciding **what knowledge can be borrowed, from where, for which OOD region and for which scientific decision**.

## Current evidence boundary

Respect the following status:

- A same-campaign neighbouring-temperature example reduces RMSE by approximately 15%, but it shares experimental programme provenance.
- A same-record mechanical-property example gives approximately 9% additional OOD improvement after state information is restored, but it may exploit tightly coupled measurements from the same specimens.
- Systematic cross-database feature injection over multiple targets is largely null.
- Optical-property knowledge transferred to organic-photovoltaic performance is strongly harmful in the tested implementation.
- Several physically adjacent cross-database edges produce only 0-2% changes and should not be treated as meaningful successes.
- A cross-database ionic-conductor ranking example contains limited retrospective OOD utility, but only one contrast survives the complete multiplicity analysis.
- There is not yet an independently replicated, practically large cross-database predictive improvement.
- An independent strength-to-fatigue experiment has been frozen and submitted as Balam job 71905. Its outcome is unknown and must not be inferred.
- A conductivity-to-battery experiment has no verified formal result available in the local project at the time of this brief.
- An experimental phase/XRD-to-synthesis direction is on hold because the complete attempt-level recipient table, especially failed and partial reactions, has not been verified.

Do not convert pending or proposed work into evidence.

## Core research question

The failed experiments suggest that a neighbouring domain's raw endpoint prediction may not be the portable object. Investigate:

> What representation of knowledge is sufficiently invariant across experimental domains to improve an OOD scientific decision?

Examples of possible portable objects include:

- a physical latent variable shared by donor and recipient;
- a dimensionless group or normalized state coordinate;
- an experimentally learned constitutive relation;
- a process window or phase boundary;
- a failure mode or contraindication;
- a mechanistic residual around a physical baseline;
- a calibrated uncertainty reduction;
- an independent ranking of candidate families;
- a constraint on feasible behaviour;
- a transferable response to temperature, pressure, composition or processing perturbation;
- a local experimental analogue retrieved for a candidate;
- complementary evidence from multiple weak donors.

These are examples, not restrictions.

## Required investigation

### A. Build a taxonomy of portable experimental knowledge

Develop a mechanistic taxonomy of what can transfer between neighbouring experimental fields. For each knowledge type, explain:

1. the physical reason it might remain invariant;
2. which state variables must match;
3. how it is calculated for an unmeasured target candidate;
4. how it differs from simply adding another predicted property;
5. how negative transfer would appear;
6. an explicit abstention criterion;
7. a materials or chemistry example with accessible experimental data.

Distinguish at least:

- property-value transfer;
- physical-state or latent-variable transfer;
- response-curve transfer;
- constraint/boundary transfer;
- failure-mode transfer;
- representation pretraining;
- ranking or exploration-prior transfer;
- multi-source complementary evidence.

### B. Search globally for suitable experimental datasets

Search current primary literature, official repositories and data descriptors. Do not restrict the search to the existing project catalog.

Prioritize open datasets that provide:

- measured experimental outcomes rather than only simulations;
- candidate-time composition, structure, processing or condition inputs;
- explicit temperature, pressure, atmosphere, protocol or device state;
- failed, partial or low-performance outcomes;
- sample, batch, campaign and publication provenance;
- enough independent groups for OOD evaluation;
- a stable download route and licence.

Look across materials and chemistry, including but not limited to:

- mechanics, strength, fatigue and fracture;
- ionic/electrical/thermal transport and battery behaviour;
- phase formation, XRD and inorganic synthesis;
- optical/electronic properties, photocatalysis and photovoltaics;
- catalytic reaction families and electrochemical conditions;
- polymer processing, morphology and device performance;
- degradation, stability and lifetime;
- reaction yield and failed reactions.

Return a verified table of candidate resources with title, DOI, URL, experimental scale, fields, provenance groups, negative outcomes, access status and licence. Separate verified facts from inference.

### C. Generate genuinely new transfer hypotheses

Generate at least 10 non-redundant hypotheses. A valid hypothesis must specify:

- donor domain;
- recipient domain;
- portable knowledge object;
- shared physical mechanism;
- direction of transfer;
- target OOD axis;
- why the effect should be locally large;
- candidate-time inputs;
- observable signature;
- negative and wrong-domain controls;
- falsification criterion;
- data and compute burden.

At least six hypotheses must not be variants of scalar donor-feature injection, rank averaging or a learned borrow/abstain gate.

At least three hypotheses must use a different scientific target from all current flagship examples.

### D. Invent stronger transfer methods

Compare method families capable of transferring mechanisms rather than correlations. Consider:

- dimensionless/mechanism-normalized representation;
- physical-baseline plus learned donor residual;
- hierarchical Bayesian partial pooling across conditions or programmes;
- candidate-specific retrieval of experimental analogues;
- sparse mixture-of-experts with a true null expert;
- invariant risk or causal representation across experimental environments;
- self-supervised or contrastive pretraining on experimental curves, spectra or trajectories;
- multi-task learning with explicitly shared latent factors;
- source-disagreement-aware exploration;
- transfer of response derivatives rather than absolute values;
- physics-constrained Gaussian processes;
- conformal/risk-controlled prediction only where its shift assumptions are justified.

For each method, state:

1. what is transferred;
2. why it should generalize across the proposed boundary;
3. the minimum viable implementation;
4. required ablations;
5. how it can abstain;
6. the decisive comparison against target-only learning;
7. what result would falsify the method.

Do not recommend a complex architecture without explaining why a simpler physical baseline, residual model or retrieval method would be insufficient.

### E. Rank complete research programmes

Convert the best hypotheses into at most five complete programmes. Rank them using an explicit scorecard:

- physical-mechanism strength;
- donor-recipient state compatibility;
- independence of provenance;
- candidate-time feature availability;
- realistic OOD definition;
- negative-outcome availability;
- expected practical effect;
- leakage risk;
- statistical power;
- data-access readiness;
- compute feasibility;
- novelty relative to prior work.

For every programme, provide:

- exact donor and recipient datasets;
- exact endpoint and unit;
- exact OOD grouping;
- preprocessing and entity linkage;
- transferable knowledge representation;
- target-only and physical baselines;
- shuffled, wrong-property, wrong-domain and oracle controls;
- model families;
- uncertainty and multiplicity plan;
- minimum practical effect;
- go/no-go metadata audit;
- staged compute estimate;
- expected manuscript interpretation under positive, null and harmful outcomes.

Use the number of independent samples, chemical systems, campaigns or publications to judge feasibility. Do not count random seeds as replication.

### F. Select one flagship experiment

Choose one programme with the best combination of:

- high probability of a practically meaningful effect;
- independent cross-programme or cross-database evidence;
- clear physical explanation;
- strict candidate-time semantics;
- enough public data to run now;
- a result that would materially strengthen a *Digital Discovery* paper.

Provide a preregistration-ready protocol:

1. scientific hypothesis;
2. causal/decision diagram;
3. donor and recipient inclusion criteria;
4. outcome-free metadata audit;
5. exclusions and leakage firewall;
6. primary OOD split;
7. label budgets;
8. representation and models;
9. frozen hyperparameters or tuning boundary;
10. controls and ablations;
11. primary estimand and practical threshold;
12. cluster-level inference;
13. multiplicity correction;
14. absolute-utility requirement;
15. stop rules;
16. interpretation matrix;
17. local-versus-HPC compute plan;
18. files and outputs required for independent verification.

The design must be frozen before numerical recipient outcomes are inspected.

### G. Design a scientific-discovery endpoint

Prediction improvement is not the only possible benefit. Propose one outcome-unseen test in which neighbouring knowledge helps identify:

- a new high-value chemical family;
- a process or phase boundary;
- a mechanism-changing regime;
- a failure region to avoid;
- a candidate whose value is not obvious from the recipient's existing labels.

Define a fixed experimental or retrospective time-split budget and a prospective hypothesis card. State exactly what would qualify as “stimulating new science” rather than merely re-ranking known outcomes.

## Validity constraints

1. Only information available when a target candidate is selected may enter the formal model or policy.
2. Raw target XRD, spectra, device measurements or other post-experiment information cannot be used to predict whether that same experiment will succeed.
3. Do not select the donor, representation, OOD split, policy, threshold or stopping rule after viewing target outcomes and then label the result confirmatory.
4. Exclude identity, specimen, composition, article, batch and campaign leakage where applicable.
5. Cross-fit every learned donor feature.
6. Use scientific replication units and grouped inference.
7. Correct multiplicity across tried donors, representations, endpoints and policies.
8. Require practical effect and usable absolute prediction, not only a positive mean.
9. Compare against the strongest simple target-only and physical baselines.
10. Null and harmful outcomes must trigger an interpretable boundary or abandonment, not a new round of post-hoc tuning.

## Literature and novelty audit

Compare the proposed programme with real prior work on:

- materials transfer and multi-task learning;
- experimental multi-fidelity learning;
- domain generalization and negative transfer;
- knowledge-integrated materials ML;
- OOD materials benchmarks;
- provenance-aware experimental evaluation;
- self-driving laboratories;
- failed-experiment and synthesis-outcome datasets.

Use primary publisher, DOI, GitHub or repository links. Verify every citation. Identify:

- what has already been demonstrated;
- what is only proposed in prior work;
- what would be genuinely new here;
- whether any proposed claim is already scooped;
- how the paper should distinguish itself.

## Required output

Write the report in Chinese, retaining necessary English technical terms.

Return:

1. **One-paragraph scientific diagnosis** of why the current cross-database methods mostly fail.
2. **Portable-knowledge taxonomy.**
3. **Verified experimental-dataset landscape.**
4. **At least 10 falsifiable new hypotheses.**
5. **At least five materially different transfer methods.**
6. **Ranked top-five research programmes with scorecard.**
7. **One fully specified flagship experiment.**
8. **One scientific-discovery/OOD-exploration experiment.**
9. **Novelty and prior-work comparison.**
10. **A 30-day execution roadmap** separating:
    - metadata-only/outcome-blind audit;
    - local smoke tests;
    - Balam/HPC formal runs;
    - independent verification;
    - manuscript decision.
11. **Three stop recommendations** identifying current directions that should not receive more compute.
12. **A final decision:** what should become the paper's new empirical centre if the proposed experiment succeeds.

For every recommendation label:

- `verified fact`;
- `inference`;
- `new hypothesis`;
- `requires data verification`.

Do not spend report space on stylistic manuscript editing. Optimize for scientific insight, falsifiability and executable progress.

