# Second-pass Claude Science prompt

Act as an adversarial scientific co-author for a *Digital Discovery* methods-led
full paper. This is a second-pass review after your first audit was selectively
integrated. Do not repeat the first audit and do not rewrite the manuscript from
scratch.

Read these files first:

1. `01_current/MANUSCRIPT_DRAFT_STREAMLINED.md`
2. `01_current/SUPPLEMENTARY_INFORMATION.md`
3. `01_current/PAPER_PACKAGE.md`
4. `02_integration/CLAUDE_MANUSCRIPT_REVIEW_INTEGRATION_2026-07-31.md`
5. `02_integration/MANUSCRIPT_AUDIT_2026-07-31.md`
6. `02_integration/REVISED_SECTIONS_EN_2026-07-31.md`
7. `03_evidence/CORE_STORY_EVIDENCE_SELECTION_2026-07-30.md`
8. `03_evidence/CORE_STORY_EXPERIMENT_MATRIX.md`
9. `03_evidence/ATTEMPT_LEDGER.csv`
10. `03_evidence/main_figures_nmi_v3_VERIFIED.json`
11. the four current figures in `04_figures/`

Confirm which files you accessed before reviewing.

## Fixed scientific objective

The paper tests whether neighbouring experimental programmes can selectively
reduce an out-of-distribution knowledge deficit by transferring a qualified
relation, correction, or candidate order. The contribution is a falsifiable
routing framework that assigns a tested edge to numerical prediction,
candidate screening, or abstention. It is not a universal transfer model or a
claim that physical adjacency guarantees benefit.

## Evidence boundaries that must remain correct

- Generic donor-feature injection repaired 0 of 40 declared OOD edges across
  eight recipients.
- A component-order-invariant electrolyte relation trained on 10,407
  measurements crossed an external unseen-salt boundary with raw R2 = 0.629,
  Spearman rho = 0.871, and 28.64% lower log-RMSE than the state-only baseline.
- The programme-balanced SolventSeg source score is **zero-label**. Five
  measured recipient formulations train the recipient-only comparators; they
  do not enter the source score. The comparison is rho = 0.910 versus 0.537,
  delta rho = 0.374.
- The 0.213--0.562 interval describes anchor-selection variability within one
  36-formulation recipient. It is not cross-programme uncertainty.
- The FINALES result, delta = -0.089 [-0.293, 0.096], p = 0.131, supports
  frozen failure to qualify and abstention. It does not prove non-transfer or
  equivalence.
- All fully frozen independent external validations of the complete route are
  currently null, rejected, or abstaining. Do not broaden this to “all frozen
  analyses are negative”, because the within-campaign KIT analysis used an
  internal freeze and was positive.
- The strongest cross-programme positives remain retrospective. Grouped
  inference and falsifiers protect the estimands but do not create prospective
  confirmation.

## Required second-pass work

### 1. Integration verification

Check whether every accepted first-pass correction was implemented correctly
in the current manuscript, SI, paper package, and figure legends. Report any
remaining contradiction with exact file and section locations. Pay special
attention to zero-label versus five-label wording, interval interpretation,
frozen versus retrospective status, and the three action routes.

### 2. Scientific rejection-risk audit

Identify no more than five remaining issues that could materially affect an
editorial or referee decision. Do not list formatting nits. For each issue give:

- severity: fatal / major / minor;
- exact unsupported inference or missing comparison;
- whether it can be fixed by wording, reanalysis, new compute, or new data;
- the minimum defensible fix;
- whether the bounded retrospective claim remains publishable without it.

Explicitly decide whether the current absence of a positive outcome-frozen
independent external validation is fatal for the manuscript's present bounded
claim, or only prevents a stronger general or prospective claim. Justify the
decision against the actual evidence, not against an idealized paper.

### 3. Novelty and prior-work stress test

Assess whether the contribution is genuinely distinct from ordinary transfer
learning, multi-fidelity learning, domain adaptation, rank fusion, and
applicability-domain estimation. State the shortest defensible novelty claim.
Identify only essential missing citations, with verified DOI or stable
publisher links. Do not invent references.

### 4. Additional-analysis decision

Critically rank these three proposed analyses:

1. outcome-independent anchor-selection sensitivity for the controlled
   catalyst five-anchor results;
2. a disclosed precision or minimum-detectable-effect diagnostic for the
   16-formulation frozen FINALES boundary;
3. anchored-delta or residual transfer on the designated generic OOD edges.

For each, state what rejection risk it resolves, what it cannot resolve, and
whether it belongs in the main text, Supplementary Information, or future work.
Recommend running only analyses with a realistic chance of changing acceptance
probability. If a new prospective recipient is the only experiment that can
resolve the remaining central limitation, say so directly.

### 5. Story and figure logic

Test whether the five-rung sequence remains the clearest argument:

1. generic reuse fails;
2. a qualified relation crosses an unseen-salt boundary;
3. controlled perturbations require endpoint routing;
4. candidate order can transfer when numerical scale does not;
5. a frozen second recipient triggers abstention.

Each main figure must perform one unique logical job. Recommend deletion or
movement to the Supplementary Information if a panel does not advance this
sequence. Do not add cases merely because data are available.

### 6. Targeted manuscript edits

Return only necessary replacements, organized by exact section. Preserve text
that is already correct. Do not alter verified values. Manuscript-ready text
must be polished English; explain major scientific decisions briefly in
Chinese.

## Output order

1. Files accessed
2. Integration QA table
3. Remaining scientific rejection risks
4. Novelty verdict and essential literature
5. Additional-analysis ranking
6. Targeted replacement text
7. One-paragraph accept / major revision / reject verdict
8. Three highest-leverage next actions

Be adversarial. A negative recommendation is useful if it identifies the exact
claim or experiment that must change. Do not reward transparency by itself,
but do not demand prospective discovery for a manuscript that explicitly makes
a bounded retrospective methods claim.
