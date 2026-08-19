# Catalyst attention Transformer

## Outcome

This package implements and evaluates a hierarchical attention Transformer for
experimental catalyst knowledge transfer. It is not an MD model and does not
flatten atoms or measurement points into one impractically long sequence. The
model aligns three experimental modalities:

```text
composition set + measurement curve + experimental conditions
    -> within-modality self-attention
    -> learned-query cross-modal attention
    -> property, uncertainty, support, and transferable latent state
```

The implementation is a complete train/evaluate/audit path rather than a
single embedding baseline. It includes hash-pinned public-data loaders,
permutation-invariant composition attention, multi-token curve attention,
condition and property-task tokens, optional XPS surface-composition attention,
cross-modal attention, grouped validation, uncertainty and support heads,
few-label adaptation, classical baselines, ablations, saved checkpoints, and
modality-shuffle audits. Feature records may omit the outcome during inference;
supervised training fails closed if an outcome is missing.

The present evidence supports retrospective **ranking transfer**. It does not
yet support a prospective catalyst-discovery or mechanistic-causality claim.

The subsequent frozen advanced-model comparison is reported in
`ADVANCED_CATALYST_MODEL_COMPARISON.md`. CrabNet-style attention, Perceiver
fusion, pinned TabPFN-v2, and a target-label-free expert portfolio were tested.
None passed the complete cross-system promotion gate, so this hierarchical
cross-attention model remains the default rather than being replaced on the
basis of one favorable recipient.

## Data contract

Raw third-party archives are downloaded to a local cache and are not committed.
Every accepted row becomes a `CatalystSample` with:

| Block | Fields |
| --- | --- |
| Identity | sample, programme, physical-sample group, provenance |
| Composition | atomic-number tokens and normalized bulk/surface fractions |
| Curve | continuous axis, primary signal, uncertainty channel, masks |
| Conditions | current density, temperature, pH, ligand descriptors, masks |
| Task | reaction, measurement modality, programme, and property tokens |
| Outcome | optional value and source-specific evidence boundary |

The three exercised resources are:

| Resource | Aligned model rows | Role |
| --- | ---: | --- |
| SpecGen OER | 462 source + 4 x 126 derivative-system rows | Complete-system spectral transfer |
| OCx24 | 1,230 UofT + 940 VSP rows with `fe_co` | Cross-source composition/condition transfer |
| Au-Ir-Rh SECCM | 3 x 322 LSV/EDX/XPS rows | Complete-library negative-transfer boundary |

Downloads are pinned to exact SHA-256 values in
`catalyst_attention/data.py`. A changed upstream file fails closed.
Categorical ID mappings live in the versioned `catalyst_attention/schema.py`;
the complete mapping is embedded in every checkpoint and must exactly match at
load time.

## Model

### Composition encoder

Each non-zero element fraction is represented by an element embedding plus a
continuous fraction embedding. A two-layer set Transformer models element
interactions. Learned-query attention pools the set and is invariant to input
element order; this property is covered by a numerical test.

### Curve encoder

UV-visible spectra and LSVs are split into patches of eight measurement
points. Every patch contains the continuous axis, primary signal, uncertainty,
and channel-availability information. Fourier axis encoding preserves position
without assuming that different instruments use the same grid. Three
Transformer layers produce roughly 90 curve tokens for a 720-point SpecGen
spectrum, so curve attention is genuine token-to-token attention rather than a
one-patch pseudo-Transformer.

### Condition encoder and fusion

Observed condition values and explicit missingness tokens are combined with
reaction, modality, programme, and target-property tokens. At transfer time the
target programme is masked to `unknown`, preventing direct target-programme
lookup. For SECCM, XPS-predicted Au/Ir/Rh surface composition is encoded by a
separate set Transformer rather than hidden in provenance. Four learned fusion
queries attend across all enabled modality tokens.

The prediction stack emits:

- normalized property mean and log variance;
- source-support probability;
- transferable latent state;
- composition-pooling and fusion-attention tensors when audit mode is enabled.

For reverse use, `recommend_candidates` ranks a declared unlabeled candidate
library with an objective direction, uncertainty penalty, latent OOD threshold,
and explicit `recommend`/`abstain` decision. It does not generate unconstrained
new chemistry or claim experimental validation.

Training combines Smooth-L1 regression, heteroscedastic Gaussian NLL, pairwise
ranking loss, support regularization, weight decay, gradient clipping, early
stopping, and deterministic seeds.

## Leakage and evaluation controls

- OCx24 validation is held out by physical sample ID; every recorded
  source-validation group overlap is empty.
- Transfer targets are complete external sources, derivative systems, or
  composition libraries rather than random target rows.
- Target programme identity is unavailable to the model at transfer time.
- SpecGen few-label comparisons use the same five labels for Transformer
  calibration and target-only PCA/KNN.
- The bias-only five-label calibration rule is predeclared and cannot change
  ranking; the target-only comparator may change both representation and rank.
- SpecGen source validation is row-held-out because its 462 source rows have
  only one programme-level group. The stronger evidence is the complete
  held-out A-D evaluation, not that internal split.
- The SECCM `log10(k0)` label is fitted from the input LSV. It is retained only
  as a representation and negative-transfer boundary, not independent
  discovery evidence.

## Results

All numbers below are from versioned JSON summaries. Multi-seed values are
medians over seeds `20260731`, `20260732`, and `20260733`.

| Test | Attention result | Comparator or ablation | Interpretation |
| --- | ---: | ---: | --- |
| SpecGen source validation | Spearman 0.869 | gate >= 0.60 | Strong internal relation learning |
| SpecGen B, zero target labels | Spearman 0.624 | PLS 0.464; composition ExtraTrees 0.611 | Spectral PLS and composition baseline beaten |
| SpecGen B, five labels | +0.352 Spearman and +19.5% relative RMSE vs target-only | gate +0.10 and +5% | Promising few-label transfer |
| OCx24, attention ensemble | median Spearman 0.563 | fair ExtraTrees median 0.549 | Positive ranking signal in both directions |
| OCx24, fixed 50/50 hybrid | median Spearman 0.573 | fair ExtraTrees; median gain 0.024 | Promising attention-enhanced transfer |
| OCx24 without condition tokens | 0.346 UofT->VSP; 0.346 VSP->UofT | with conditions 0.546 and 0.580 | Conditions supply reproducible transfer signal |
| SECCM, held-library median | Spearman -0.242 | composition-only -0.100 | Gate fails; strong negative-transfer boundary |

The full SpecGen model is not uniformly superior to every ablation. Across
A-D, cross-attention Spearman medians are `0.543/0.624/0.250/0.737`;
composition-only is `0.566/0.634/0.172/0.755`; mean pooling is
`0.535/0.599/0.245/0.740`. The defensible result is therefore not "attention
always wins." It is that the complete model transfers useful relations on
multiple held systems, that experimental-condition attention yields a clear
OCx24 cross-source gain when combined with the equal-input tree expert, and
that the SECCM failure is detected rather than silently promoted.

The OCx capacity/loss and hybrid route were developed after inspecting both
cross-source directions; OCx is therefore method-development evidence, not
fresh confirmation. The pure attention ensemble beats the fair
composition-plus-condition tree on UofT-to-VSP (0.546 versus 0.526) and
VSP-to-UofT (0.580 versus 0.571). The fixed 50/50 hybrid is non-harmful in both
directions and reaches 0.567 and 0.579 respectively. A genuinely unseen
programme is still required.

## Attention audit

For the best SpecGen checkpoint on held-out system B, mean fusion mass is:

| Modality | Attention mass |
| --- | ---: |
| Composition | 0.538 |
| Curve | 0.390 |
| Conditions | 0.055 |
| Task | 0.017 |

Twenty independent within-system shuffles show that attention mass is not
causal attribution. Composition shuffling reduces median Spearman from 0.624
to -0.005, a drop of 0.629. Curve shuffling reduces it to 0.610, a drop of
0.014, while predictions move by a median 3.35 mV. The learned ranking
currently uses composition more strongly than the raw attention allocation
alone suggests.

This audit motivates the next model iteration: source-only modality dropout,
cross-modal agreement objectives, and target-free domain invariance should be
tested against the same frozen system-held-out gates. None should be promoted
unless it improves complete-system transfer without erasing the SECCM
abstention boundary.

That first advanced iteration is now complete. Whole-modality dropout and
repeated-latent Perceiver fusion were implemented. Set-Perceiver improved
SpecGen C but regressed A, B, and D; TabPFN-v2 improved only one OCx24
direction. The frozen gates rejected every advanced candidate. Further tuning
against these revealed target outcomes is intentionally stopped; the next
valid iteration requires a sealed external programme.

## Reproduction

Install the isolated requirements and download exact public inputs:

```bash
python3 -m pip install -r analysis/catalyst_attention/requirements.txt
PYTHONPATH=analysis python3 analysis/download_catalyst_attention_data.py \
  --cache-dir <cache-directory>
```

Run the three benchmarks:

```bash
PYTHONPATH=analysis python3 analysis/run_catalyst_attention_experiment.py \
  --specgen-archive <cache-directory>/44160_2025_983_MOESM4_ESM.zip \
  --variants full --seeds 20260731,20260732,20260733 \
  --epochs 100 --patience 20 --draws 30

PYTHONPATH=analysis python3 analysis/run_ocx24_attention_experiment.py \
  --ocx24-csv <cache-directory>/ExpDataDump_241113_clean.csv \
  --seeds 20260731,20260732,20260733 --epochs 100 --patience 20

PYTHONPATH=analysis python3 analysis/run_seccm_attention_experiment.py \
  --seccm-archive <cache-directory>/SECCM_dataset.zip \
  --edx-archive <cache-directory>/EDX_dataset.zip \
  --xps-archive <cache-directory>/XPS_dataset.zip \
  --variants full,composition_only --epochs 80 --patience 15
```

Run the matched SpecGen ablations and repeated-shuffle audit:

```bash
PYTHONPATH=analysis python3 analysis/run_catalyst_attention_experiment.py \
  --specgen-archive <cache-directory>/44160_2025_983_MOESM4_ESM.zip \
  --variants curve_only,composition_only,mean_pool \
  --seeds 20260731 --epochs 100 --patience 20

PYTHONPATH=analysis python3 analysis/audit_catalyst_attention.py \
  --checkpoint analysis/results/catalyst_attention_checkpoints/full_seed20260732.pt \
  --specgen-archive <cache-directory>/44160_2025_983_MOESM4_ESM.zip \
  --shuffle-draws 20
```

Model checkpoints are intentionally ignored by Git and regenerated locally.
Compact result summaries remain versioned:

- `results/catalyst_attention_specgen_summary.json`
- `results/catalyst_attention_specgen_ablation.json`
- `results/catalyst_attention_ocx24_summary.json`
- `results/catalyst_attention_seccm_summary.json`
- `results/catalyst_attention_audit.json`

Run the implementation and claim-contract tests with:

```bash
PYTHONPATH=analysis pytest -q tests/test_catalyst_attention.py
```
