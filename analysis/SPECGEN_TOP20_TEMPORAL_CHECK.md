# SpecGen optimized-candidate temporal check

## Status

The source article and the numerical outcomes of these optimized candidates
were accessible before this check was implemented. The check is consequently
retrospective. The 20 candidates in each derivative system were generated
after the original 126-catalyst library and their electrochemical outcomes were
measured in a subsequent experimental step, but they were selected by the
source study's SpecGen workflow. They are not an independent laboratory or a
prospective test created by this work.

## Question

Does the composition-to-OER relation trained only on the original 462-catalyst
donor library retain candidate-ranking information among the subsequently
synthesized optimized candidates?

## Frozen calculation

- Train the post-primary composition donor exactly as declared: 500 ExtraTrees,
  minimum leaf size 2, all six compositional slots.
- Extract Supplementary Tables 6-9 directly from the source PDF and verify their
  overpotentials against the source-data files for Supplementary Figs. 14a,
  15a, 18a and 19a.
- Apply the donor without target refitting.
- Primary metric: Spearman correlation across the 20 later candidates.
- Secondary metrics: precision among the predicted best four, RMSE and
  normalized simple regret.
- Inferential null: 100,000 fixed target-label permutations, one-sided for
  positive rank concordance, with Holm correction across A-D.

Passing this check establishes only temporal ranking corroboration inside the
same published experimental programme. Because the candidates were themselves
selected by SpecGen, the result cannot establish unbiased search acceleration.
