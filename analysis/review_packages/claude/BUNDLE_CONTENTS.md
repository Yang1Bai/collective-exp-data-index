# Bundle contents and review order

## Recommended reading order

1. `analysis/ADVERSARIAL_REVIEW_RESPONSE.md`
2. `analysis/review_packages/claude/ADVERSARIAL_REFEREE_REPORT_ORIGINAL.md`
3. `analysis/review_packages/claude/PROMPT_FOR_CLAUDE.md`
4. `analysis/SELECTIVE_NEIGHBOR_BORROWING_STRATEGY.md`
5. `analysis/CCA_FAMILY_FIRST_PROTOCOL.md`
6. `analysis/MANUSCRIPT_DRAFT.md`
7. `analysis/SUPPLEMENTARY_INFORMATION.md`
8. `analysis/PAPER_PACKAGE.md`
9. `analysis/CALTECH_IONIC_EXTERNAL_POLICY_VALIDATION.md`
10. `analysis/CORE_STORY_EXPERIMENT_MATRIX.md`
11. `analysis/PRESUBMISSION_REVIEW.md`
12. the five main PNG or PDF figures under `analysis/figures/`
13. panel-source and family-first metric CSVs under `analysis/results/`
14. the portable Starrydata, TRI, and multi-target validation summaries
15. the 13-program leave-one-program CCA benchmark, reconstruction verifier,
    failure anatomy, and post-result CCA-v2 architecture
16. frozen designs, method-development failures, and outcome-unseen amendments
    if a policy or outcome-access detail is disputed

## Included material

- original adversarial referee report, issue-by-issue response, and second-pass
  adversarial prompt;
- current manuscript, Supplementary Information, claim ledger, prior-work and
  citation audits, terminology rules, and pre-submission review;
- methodology, figure contracts, and visual QA records;
- frozen machine-readable designs and implementation/inference amendments;
- compact JSON/CSV result summaries and verification sentinels;
- the five main figures in PDF and PNG, including CCA family-first exploration
  and outcome-unseen validation;
- all panel-source CSVs for Figures 1--3 and Figure 5, including
  `figure_main_panel_a.csv` through `figure_main_panel_d.csv`;
- compact Starrydata reverse-transport, TRI OER, matched-specificity,
  hypothesis-card, Balam completion, and cross-target synthesis outputs;
- complete compact CCA gate panel, predictions, policy summaries, contrasts,
  validation narrative, and independent reconstruction sentinel;
- release manifest and public repository README.

## Deliberately excluded

- `data/collective.sqlite` and all raw source records;
- credentials, caches, virtual environments, logs, and cluster scratch files;
- large row-level prediction, trajectory, bootstrap, or gate tables;
- source data whose redistribution rights are uncertain;
- any interpretation of the outcome-selected CCA portfolio as confirmatory
  evidence; its files are included specifically so the post-result boundary,
  failed local gate, breadth-versus-repeat trade-off, and unsuccessful
  outcome-unseen confirmation can be audited.
- any interpretation of CCA-v2 as already validated; its architecture is a
  post-result commitment for a new temporal or prospective programme.
- the obsolete pre-review HTML/JSON handoff surface, whose summary language was
  superseded by the referee response and revised manuscript.

The exclusions do not change the reported decisions: compact verification
files, checksums, frozen designs, and the reproducible scripts remain in the
repository. Raw or large outputs should be regenerated from their pinned
sources rather than redistributed in this review handoff.
