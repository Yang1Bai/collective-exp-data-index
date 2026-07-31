# Writing and story analysis of the supplied Nature/NMI reference set

## Reference paper

Lai *et al.*, *Reusability report: Exploring the utility and extensibility of
an integrated modelling framework for liquid electrolyte design*, *Nature
Machine Intelligence* (2026), doi:10.1038/s42256-026-01277-x.

This note concerns argument architecture and presentation. It does not adopt
the reference paper's scientific claims, wording, evaluation protocol, or
claim strength.

## What makes its story easy to follow

The paper gives the reader one stable object--an existing electrolyte modelling
framework--and asks four questions in an escalating order:

1. **Can the original result be reproduced?** This establishes a credible
   baseline before any extension is claimed.
2. **What controls performance?** Data volume, feature composition, and
   distribution are perturbed to expose sensitivity.
3. **Does the model generalize?** Zero-shot and progressive few-shot tests move
   from operating-condition shifts to a new salt chemistry.
4. **Can the framework support new endpoints?** The final section expands from
   molecular properties to formulation and device-level targets.

Figure 1 presents these four questions before the Results. Each Results section
then follows the same local rhythm: motivation, declared test, quantitative
observation, interpretation, and limitation or bridge to the next test. The
Discussion returns to the same axes--reproducibility, data dependence,
generalization, and extension--rather than summarizing every panel.

## Writing moves worth transferring

- **A question sequence rather than a case list.** The examples are stages in
  an argument, not independent showcases.
- **A baseline before the positive result.** Readers first learn what the
  unmodified approach can and cannot do.
- **Claim-led subsection openings.** Phrases such as “To establish…”, “To
  clarify…”, and “We next tested…” make the purpose of each experiment explicit.
- **One conceptual overview figure.** The first figure maps the full study,
  allowing later figures to carry evidence rather than repeat the workflow.
- **Escalating transfer distance.** Evaluation progresses from reproduction to
  distribution shift, unseen chemistry, and new target levels.
- **Bounded interpretation at section ends.** Positive results are repeatedly
  tied back to data distribution and task conditions.

## What should not be copied

- The reference abstract lists many contributions and sometimes places several
  claims in one sentence. Our abstract should remain centred on one insight:
  the transferable unit is a task-specific relation or score, not a database.
- Its zero-shot and few-shot sections do not use our matched-falsifier,
  provenance-leakage, or endpoint-specific abstention logic. Those are part of
  our scientific contribution and must remain more explicit than in the
  reference.
- Its four tasks all extend one existing framework. Our paper instead compares
  several experimental programmes, so the recurring object must be the
  borrowing contract rather than a single model architecture.
- The reference sometimes uses broad extrapolation language for threshold
  splits. Our manuscript retains complete held-out systems, formulations,
  articles, or programmes as the primary OOD units.

## Revised story architecture for this manuscript

**One-sentence argument.** When recipient experiments are too sparse for
reliable OOD decisions, neighbouring programmes can supply useful missing
knowledge, but only when the shared relation, experimental state, transferred
object, leakage boundary, and decision endpoint are aligned and the edge may
abstain.

The Results now follow five explicit questions:

1. **Is database similarity or generic donor injection sufficient?** No: 0 of
   40 declared OOD edges passes the complete repair gate.
2. **Can a matched relation survive a controlled chemical perturbation?** Yes,
   selectively: two complete catalyst systems improve, one supports ranking
   only, and one is harmful.
3. **Can the relation cross database and component identity?** Yes: the
   permutation-invariant electrolyte relation predicts an external unseen salt
   and reduces log-scale error by 28.64%.
4. **Can borrowing rescue the decision when numerical calibration fails?** Yes:
   a cross-programme ordinal score raises five-label candidate ordering from
   \(\rho=0.537\) to 0.910 while calibration is rejected.
5. **Does the accepted route generalize automatically?** No: the unchanged
   ordinal score is rejected in a frozen second recipient.

This sequence converts the manuscript from “several transfer examples” into a
single causal narrative: naive reuse fails; the failure identifies what must be
routed; routed relations improve selected prediction and screening tasks; an
unchanged external rejection defines the abstention boundary.

## Concrete revisions applied

- Replaced the abstract's dense case enumeration with a
  challenge--insight--workflow--evidence--boundary sequence.
- Rebuilt the four-paragraph Introduction as:
  scientific OOD problem -> why pooling and generic transfer fail -> operational
  definition of a neighbouring programme and transferable object -> escalating
  evaluation with quantitative outcomes.
- Recast Methods section 2.2 as four reader questions: edge eligibility,
  transferable object, decision endpoint, and falsifier-based decision.
- Rewrote Results headings and opening sentences so every subsection announces
  the test it performs and its place in the evidence ladder.
- Reorganized the Discussion around the scientific insight, the distinction
  between prediction and screening, and the decisive prospective boundary.
- Simplified the title and Figure 1 caption so that prediction, screening, and
  abstention are visible before programme-specific details.

## Remaining presentation priority

Figure 1 should visually reproduce the same five-step study logic, not only the
method modules. A reader who sees the title, abstract, Figure 1, and Results
headings should be able to recover the complete argument without knowing any
dataset abbreviation.

## Cross-paper architecture audit

The additional supplied papers were used as structural references, not as
sources of scientific evidence for this manuscript.

| Reference pattern | Narrative move | Adaptation in this manuscript |
|---|---|---|
| *AI tools expand scientists' impact but contract science's focus* | A finding-led contrast is stated in the title, quantified early, and then explained through progressively wider units of analysis | The title now states the intervention and endpoint; the abstract places 0/40 failure before the two large positive effects |
| Reusability report on integrated electrolyte modelling | One stable object is tested through reproduction, sensitivity, generalization, and extension | The stable object here is the borrowing contract; Results progress from failure to controlled perturbation, external chemistry, endpoint routing, and frozen rejection |
| Molecular deep learning at the edge of chemical space | Unfamiliarity is separated from uncertainty and evaluated on a genuinely independent screening space | OOD is defined by complete scientific units, not random rows, and screening is separated from calibrated prediction |
| Brain-inspired uncertainty calibration | A mechanism-inspired intervention is followed by controlled validation and then an OOD challenge | Matched falsifiers and controlled catalyst perturbations precede the external unseen-salt result |
| Unified predictive and generative liquid-electrolyte framework | A single integrated workflow is introduced before application-level evidence | Figure 1 presents qualification, transfer, routing, and abstention before programme-specific figures |
| Materials and molecular foundation-model papers | Architecture is subordinated to task coverage, ablation, and downstream utility | Model names are retained in Methods and baselines; the main narrative centres on the relation, state, and decision endpoint |
| Research-direction prediction study | Retrospective time splits and human/decision relevance define the evaluation, followed by explicit limitations | The frozen second recipient and the prospective next test are treated as part of the main claim rather than an appendix caveat |

Across the set, the most reusable writing principle is **controlled
escalation**. A strong paper does not alternate between unrelated examples. It
changes one dimension of difficulty at a time and makes the reader understand
why the next test is necessary. The revised manuscript therefore uses the
following bridges:

1. strong fit fails across provenance;
2. the failure motivates transfer of a relation rather than a label;
3. a controlled series tests selectivity of that relation;
4. an independent unseen component tests whether it crosses provenance;
5. failed calibration motivates an ordinal decision endpoint;
6. a frozen second recipient tests whether that narrower route generalizes.

## Figure-language principles extracted from the set

- Use one dominant quantitative panel per figure and make schematics
  subordinate to it.
- Draw scientific objects--catalyst arrays, mixtures, candidate fields--rather
  than generic database cylinders and model boxes.
- Reserve green and red for accepted and rejected routes; use blue and teal for
  experimental programmes and measured effects.
- Put the comparison that changes the scientific conclusion directly on the
  graphic: 0/40, 28.64%, 0.910 versus 0.537, and the frozen rejection.
- Avoid four equally weighted dashboard panels. Later figures now use an
  asymmetric evidence layout: one hero panel, one mechanism or design panel,
  and one boundary panel.
