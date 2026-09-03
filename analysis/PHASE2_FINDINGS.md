# Phase 2 findings — selective knowledge borrowing

## Original candidate falsified

The earlier ESTM→OBELiX result used random row splits and too few correlated
repetitions. Under the official DOI/composition-disjoint split, canonical
overlap removal, grouped training samples, source-label permutation, Holm
correction, and model sensitivity, the designated Ridge result is negative and
the tree estimates are model-dependent. It is not evidence for transfer.

## Frozen multi-target map

`knowledge_map_design.json` designates nine targets and five directed sources
per target. Discovery and internal-confirmation entities are disjoint. Source
models exclude target evaluation identities; all post-exclusion exact overlaps
are zero. Five discovery-selected edges receive the same 999-permutation
refinement and Holm correction.

One non-calibration edge passes every internal gate:

- source/target: Borg ultimate tensile strength→yield strength;
- target budget n=30;
- relative RMSE improvement 6.46% [3.69%,13.03%];
- refined raw p=0.001, Holm p=0.005;
- 3/3 learners positive;
- baseline/augmented mean R² −0.149/+0.025;
- target-equivalent sample fraction saved 73.4% on a valid monotone internal
  learning curve.

The power-factor→ZT constitutive calibration also passes but is not counted as
knowledge borrowing.

## Independent BIRDSHOT boundary

The v5 BIRDSHOT table contains 171 paired strength records and 151 unique
nominal compositions. There are zero exact compositions shared with Borg.
Rolling tests use Year 1→2 and Years 1–2→3 with no cross-year canonical overlap.

For Borg UTS→BIRDSHOT yield strength at n=30:

- relative RMSE improvement 4.30% [3.36%,5.51%];
- Year 1→2 +4.39%; Years 1–2→3 +4.12%;
- within-year feature-mapping permutation p=0.003;
- Ridge, random forest, and ExtraTrees all positive;
- no defensible target-equivalent sample count because campaign drift makes the
  rolling-time learning curve nonmonotone.

This is a directional independent replication but misses the frozen 5%
practical threshold. A post-confirmation process-aware sensitivity gives 5.23%
[3.74%,7.03%], yet absolute rolling-time R² remains negative
(−1.216→−0.992). This is relative error robustness, not rescue.

## Independent Matbench negative boundary

`matbench_steels_confirmation_design.json` was frozen before the target run.
The target uses 312 experimental steels and the official five Matbench folds;
same-row tensile strength and elongation are forbidden target inputs, and all
target compositions are removed from source fits.

For Borg UTS→Matbench yield strength at n=30:

- relative RMSE improvement −1.23% [−15.88%,2.48%];
- five fold effects are all negative;
- mapping-permutation p=0.794;
- primary baseline/augmented R² −15.446/−16.533;
- random-forest and ExtraTrees sensitivities have positive absolute R² but
  effects of only +0.36% and +0.60%, far below the frozen 5% gate;
- rescue is false.

Mechanical adjacency alone therefore does not guarantee useful borrowing.

## Frozen KIT local-neighbor rescue

`kit_temperature_borrowing_design.json` was written after descriptive sample
and correlation checks but before any target-outcome model. It is an internal
design lock, not an external preregistration. The raw dataset contains 5,035
runs from 504 experiment IDs and 109 unique PC/EC/EMC/LiPF6 formulations.

The independent unit is a formulation. Replicate experiments are aggregated by
the within-formulation/temperature median. The 108 formulations observed at
all target and control temperatures enter five balanced formulation-group
folds. In every fold, held-out formulations are excluded from the source fit;
source predictions for target-training formulations are cross-fitted.
Arrhenius and EIS fit outputs are forbidden.

For the frozen −20→−30 °C edge at n=30:

- relative RMSE improvement 15.02% [8.61%,21.10%];
- mapping-permutation p=0.001 from 999 mappings;
- baseline/augmented pooled R² 0.739/0.811;
- all five folds positive;
- random forest, ExtraTrees, and degree-2 Ridge all positive;
- source OOF R²=0.859;
- source-feature importance 0.732, median rank 1/5;
- point-equivalent target-only n=47.884, or 37.35% of equivalent target labels
  saved. A post-outcome formulation/subset bootstrap gives n=38.38–59.89 and
  21.84–49.91% saved; 80.52% of replicates meet the frozen 30% point
  threshold, so the saving magnitude is uncertain.

Prespecified real-source effects decrease with temperature distance:

- ΔT=10 °C: +15.02%;
- ΔT=30 °C: +5.01%;
- ΔT=60 °C: +0.95%;
- ΔT=90 °C: −0.76%.

The distance-effect Spearman correlation is −1.0 for these four sources. A
shuffled −20 °C source is harmful: −2.96% [−4.32%,−1.44%]. Every frozen rescue,
adjacency, placebo, leakage, and uncertainty gate passes.

This supports **within-campaign local task rescue**. It is not an independent-
dataset replication and does not establish field-level rescue.

## Frozen CALiSol cross-article boundary

`calisol_external_borrowing_design.json` was frozen after a schema, count, and
data-quality audit but before any conductivity correlation or outcome model.
CALiSol-23 contains 13,825 digitized measurements from 27 publications. The
target is −40 °C, the nearest −30 °C task is primary, and −20, 0, and 20 °C are
prespecified distance controls.

The target contains 891 eligible paper-specific formulations from 15 articles.
Outer folds hold out entire articles. Every source model excludes all rows from
the held-out target articles and all exact held-out chemistry identities;
source priors for target-training rows are leave-one-article-out predictions.
Article DOI, temperature, conductivity at another temperature, and all
Arrhenius/VTF or target-series summaries are forbidden predictors.

For the frozen −30→−40 °C edge at n=30:

- relative RMSE improvement 1.61% [−2.14%,4.21%] under a bootstrap that
  resamples repetitions, articles, and formulations;
- baseline/augmented pooled R² −0.049/−0.014;
- fold effects −0.78%, +0.003%, −3.85%, +3.11%, and +6.45%;
- source article-OOF R²=0.119 and zero article or exact-chemistry leakage;
- random forest, ExtraTrees, and Ridge directions are positive, but none has a
  95% interval bounded above zero;
- equivalent target-only n=36.12, or 16.9% saved, below the frozen 30% gate;
- the four real-source effects are not ordered by temperature distance
  (Spearman ρ=0.0), and the 0 °C control is numerically larger than the primary.

The fixed first-subset within-article mapping test gives p=0.004. That isolated
conditional result cannot override the failed repeated-effect interval,
practical threshold, absolute R², all-fold, sample-saving, and distance gates.
The frozen decision is `cross-article-borrowing-unresolved`; no alternative
temperature edge was selected after seeing the data.

CALiSol therefore supplies the missing independent boundary: KIT demonstrates
that local borrowing can materially improve a controlled task under frozen
point rules, while CALiSol shows that even the same physical neighborhood does not automatically travel across
experimental articles.

## Synthesis

- 42 internal non-calibration edges;
- 15 independent BIRDSHOT edges;
- five independent Matbench edges;
- five KIT condition/placebo edges;
- five independent multi-article CALiSol condition/placebo edges;
- internal Cochran Q p=0.00036;
- BIRDSHOT contains eight harmful and two practically equivalent edges;
- the original 0–3 cross-domain neighborhood score remains unestablished
  (Spearman ρ=0.212, p=0.113).

Conclusion: the evidence establishes that useful borrowing exists, is
directional and can rescue a data-poor local task, while paper-disjoint CALiSol
shows that this rescue is not automatically transportable even within the same
electrolyte property. Independent generalization remains selective and often
fails. The map is a screening/falsification tool, not a universal transfer law.
