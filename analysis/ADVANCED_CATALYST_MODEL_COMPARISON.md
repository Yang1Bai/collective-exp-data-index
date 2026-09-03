# Advanced catalyst model comparison

## Decision

The frozen A+B comparison is complete. CrabNet-style composition attention,
repeated-latent Perceiver fusion, their combination, and pinned TabPFN-v2 were
evaluated against the author's tree models and the existing hierarchical
Transformer under the same complete-system or complete-programme holdouts.
None passed the predeclared cross-system development gate.

The correct result is an **advanced-model null**, not a reason to tune weights
against the already revealed recipients. The existing hierarchical
cross-attention model remains the default. The new models remain available as
auditable experts and as frozen candidates for a genuinely new programme.

This is post-outcome architecture development. It cannot confirm prospective
catalyst discovery.

## What the repository author used

The claim-bearing repository analyses are primarily relation-transfer
protocols built from Ridge, Random Forest, ExtraTrees, histogram gradient
boosting, kernel ridge, cross-fitted donor predictions, and simple residual or
anchor calibration. The scientific control surface—grouped OOD units,
wrong/shuffled donors, equal recipient-label budgets, and
predict/rank/abstain routing—is more sophisticated than the learner family.

For SpecGen, the author's promoted composition donor is a 500-tree Random
Forest. Its complete-system zero-label Spearman values are:

| System | Author Random Forest |
| --- | ---: |
| A | 0.552 |
| B | 0.610 |
| C | 0.259 |
| D | 0.748 |

The repository also tested stronger neural models. A task-conditioned
partial-label MLP was unstable at 15–30 target labels. A Chemprop v2.1.2
directed-message-passing encoder learned its source optical tasks, but its
state-aligned representation worsened scaffold-OOD photocatalysis RMSE by
28.12% at the primary label budget. The blind set remained closed.

The author's negative result therefore does not mean that no neural network
was attempted. It means that source skill and model capacity did not repair an
endpoint-contract mismatch.

## Frozen advanced design and audit amendment

The exact design is
`analysis/catalyst_attention_advanced_design.json`, SHA-256
`2c18dff3b11a21b9c7ea81c9d05018ef073a87edb5c009b43e26a9e61a823ad7`.
Its original pre-outcome hash was
`5946812c2ee2ca94473faa807fedf3af0795d03b1649e11e17ece47fdb3a71ef`.
The post-outcome audit amendment copied the already executed, unchanged
per-dataset hyperparameters, seed counts, and reference-artifact hashes into
the manifest. It did not change a prediction, metric, threshold, or decision.

### CrabNet-style composition encoder

The encoder combines learned element identity embeddings, linear and
logarithmic Fourier encodings of element fractions,
permutation-equivariant element self-attention, and invariant learned element
weighting. The cross-attention SpecGen configuration has 391,111 trainable
parameters.

### Perceiver fusion

The Perceiver variant uses a fixed latent array, repeated cross-attention from
latents to all enabled modality tokens, latent self-attention, residual
updates, and final latent pooling. It supports composition, curve, conditions,
task identity, and optional XPS surface composition without flattening them
into one fixed-width row.

The set-Perceiver SpecGen configuration has 528,198 trainable parameters. The
CrabNet-Perceiver configuration has 509,383.

### Modality dropout and support

During source training, whole input modalities can be masked while task tokens
remain present. This prevents every training update from using the same
shortcut. Prediction retains the existing heteroscedastic uncertainty,
latent-support calibration, risk-adjusted recommendation, and explicit
abstention interfaces.

### TabPFN-v2

TabPFN is an optional, pinned research baseline:

- package `tabpfn==8.1.0`;
- model version `v2`;
- regressor SHA-256
  `2ab5a07d5c41dfe6db9aa7ae106fc6de898326c2765be66505a07e2868c10736`;
- Prior Labs v2 licence boundary: Apache-2.0 plus attribution requirement.

Bulk/surface composition, observed conditions, masks, task categories, and a
source-only curve PCA are used. Programme identity is excluded. Recipient
outcomes are never used to fit the PCA or TabPFN.

## Results

All neural results are three-seed prediction ensembles except SECCM, whose
frozen design uses one seed per held-out library. TabPFN-v2 is the pinned
foundation-model prediction.

### SpecGen complete-system transfer

| Model | A | B | C | D | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Existing hierarchical Transformer | 0.543 | 0.624 | 0.250 | 0.737 | Existing default |
| Author Random Forest | 0.552 | 0.610 | 0.259 | 0.748 | Reference |
| CrabNet-cross | 0.520 | 0.558 | 0.273 | 0.708 | Fail |
| Set-Perceiver | 0.492 | 0.613 | 0.344 | 0.724 | Fail |
| CrabNet-Perceiver | 0.570 | 0.615 | 0.182 | 0.729 | Fail |
| TabPFN-v2 | 0.505 | 0.627 | 0.163 | 0.728 | Fail |

The most informative selective effects are:

- Set-Perceiver improves the difficult C system by 0.085 over the stronger
  existing/author reference, but regresses A, B, and D.
- CrabNet-Perceiver improves A by 0.018, but regresses the other systems.
- TabPFN improves B by only 0.003 and regresses A, C, and D.

No model reaches the required median A–D gain of 0.02 with at least three
non-negative systems and no system regression worse than 0.03.

### OCx24 complete-programme transfer

| Model | UofT → VSP | VSP → UofT | Gate |
| --- | ---: | ---: | --- |
| Existing hierarchical Transformer | 0.546 | 0.580 | Existing default |
| Fair ExtraTrees | 0.526 | 0.571 | Reference |
| CrabNet-cross | 0.475 | 0.483 | Fail |
| Set-Perceiver | 0.524 | 0.580 | Fail |
| CrabNet-Perceiver | 0.457 | 0.458 | Fail |
| TabPFN-v2 | 0.586 | 0.490 | Fail |

TabPFN is useful in one direction and harmful in the other. Set-Perceiver
essentially reproduces the existing reverse-direction result but loses 0.021
in the forward direction. This asymmetry is evidence against promoting one
larger model as a universal transfer backbone.

### SECCM complete-library boundary

| Model | Au-rich | Ir-rich | Rh-rich | Median Spearman |
| --- | ---: | ---: | ---: | ---: |
| CrabNet-cross | 0.353 | -0.498 | -0.306 | -0.306 |
| Set-Perceiver | 0.172 | -0.221 | -0.681 | -0.221 |
| CrabNet-Perceiver | 0.116 | -0.489 | -0.510 | -0.489 |
| TabPFN-v2 | -0.076 | 0.164 | -0.351 | -0.076 |

Every model has strongly negative held-library R2. The target `log10(k0)` is
fitted from the input LSV, so even a positive result could only be a
representation test. The observed failure retains the abstention boundary.

## Post-result portfolio diagnostic

After the frozen individual-model gate failed, an explicitly diagnostic,
equal-weight portfolio combined the existing Transformer ensemble,
Set-Perceiver, composition ExtraTrees, and TabPFN-v2.

It improved SpecGen rank on B, C, and D but regressed A. Relative to the
stronger existing/author reference, its gains were approximately
`-0.011/+0.009/+0.039/+0.003`; the median gain was about 0.006, below the
frozen 0.02 threshold. Abstaining on the 20% highest expert-disagreement
candidates did not create a uniform improvement.

No portfolio weights were optimized after this diagnostic. Such optimization
would use already revealed recipient outcomes and would not provide new
transfer evidence.

## What problem was solved

The work resolves the representation-family limitation as an empirical
question:

1. Transformer and foundation-model baselines are now implemented rather than
   left as a manuscript limitation.
2. They share the same data, grouping, target masking, uncertainty, and
   recommendation contracts as the existing model.
3. Their failure is retained and reproducible.
4. Model disagreement can drive target-label-free abstention.
5. The result identifies programme/endpoint alignment and missing scientific
   state as the limiting variables, rather than insufficient parameter count.

## Data required for the decisive next test

### Minimum independent blind programme

- 200–500 unique catalyst candidates;
- preferably at least three experimental repeats per candidate;
- a complete or outcome-independently sampled candidate library;
- recipient outcomes sealed until predictions and exclusions are frozen;
- programme, laboratory, batch, instrument, and physical-sample group IDs.

### Inputs available before the decision

- normalized bulk composition;
- precursor and ligand identity, including SMILES when molecular components
  exist;
- synthesis and processing conditions;
- electrolyte, pH, temperature, pressure, current-density protocol, electrode,
  and reference-electrode metadata;
- pre-reaction UV–Vis, Raman, XPS, XRD, or microscopy when available;
- uncertainty and missingness for every channel.

Post-outcome measurements must not leak into the input. In particular, using
an LSV to predict a kinetic label fitted from the same LSV cannot validate
recommendation.

### Outcomes

- independently measured overpotential, Faradaic efficiency, Tafel slope,
  stability, or turnover metric;
- raw replicate values, detection limits, and uncertainty;
- failed, inactive, and unstable candidates retained;
- measurement timestamps sufficient for a temporal or prospective split.

### Data needed for a graph model

A graph encoder cannot be fairly validated from elemental fractions alone. It
requires ligand/precursor SMILES, crystal or atomistic structures where
available, support and active-site identity, and an explicit mapping from
those objects to each measured catalyst.

## Reproduction

Install the core and optional pinned baseline:

```bash
python3 -m pip install \
  -r analysis/catalyst_attention/requirements-advanced.txt
```

Run the complete comparison:

```bash
PYTHONPATH=analysis python3 analysis/run_advanced_catalyst_benchmark.py \
  --specgen-archive <SpecGen.zip> \
  --ocx24-csv <OCx24.csv> \
  --seccm-archive <SECCM.zip> \
  --edx-archive <EDX.zip> \
  --xps-archive <XPS.zip> \
  --tabpfn-model <tabpfn-v2-regressor.ckpt>
```

That command writes the monolithic execution artifact to
`analysis/results/catalyst_attention_advanced_monolithic.json`; it does not
overwrite the compact hash-binding summary. To rebuild the compact summary
from the three dataset-scoped artifacts, run:

```bash
PYTHONPATH=analysis python3 \
  analysis/aggregate_advanced_catalyst_results.py
```

The authoritative result files are:

- `analysis/results/catalyst_attention_advanced_summary.json`;
- `analysis/results/catalyst_attention_advanced_specgen.json`;
- `analysis/results/catalyst_attention_advanced_ocx24.json`;
- `analysis/results/catalyst_attention_advanced_seccm.json`.

The three dataset files are explicitly marked `partial` because each was
generated as a dataset-scoped run. The compact aggregate summary verifies
their hashes and is the only artifact marked `complete`.
