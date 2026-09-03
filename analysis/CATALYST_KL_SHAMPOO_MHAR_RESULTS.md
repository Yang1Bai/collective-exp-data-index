# KL-Shampoo and Multi-Head Attention Residual catalyst benchmark

## Decision

The experiment series implemented and tested both requested methods, but it
does **not** support replacing the existing hierarchical cross-attention model
with one universal new default.

- Per-sublayer Delta Multi-Head Attention Residual (Delta-MHAR) is a useful
  specialist. It improved SpecGen C and OCx24 UofT→VSP, but failed the frozen
  cross-dataset promotion gates.
- Official KL-Shampoo without grafting damaged source fit and transfer.
  Adam step-norm grafting restored source fit, but did not improve transfer and
  increased CPU training time.
- Unlabelled-target CORAL alignment improved all four SpecGen systems in one
  screening seed with the standard encoder, but seriously regressed OCx24. It
  is not a universal transfer solution.

The existing hierarchical cross-attention v1 remains the default. The new
Delta-MHAR model is retained as a complementary expert for a future,
target-label-free router that must be frozen before evaluation on a new
programme.

## What was implemented

### Delta-MHAR

`catalyst_attention/model.py` now supports
`depth_routing="delta_mhar_sublayer"`. Each attention and feed-forward
sublayer produces a delta. A four-head router mixes earlier deltas to form the
input to the next sublayer, while the raw new delta is added to the unchanged
residual stream. Random router queries and zero gates make initialization
functionally identical to the ordinary Transformer.

This is intentionally different from concatenating layer outputs or routing a
whole block. It preserves the residual path and exposes both attention and
feed-forward computation histories.

### KL-Shampoo

`catalyst_attention/optimizers.py` wraps Meta's official
`facebookresearch/optimizers` implementation at commit
`f18f735c972d304542af15e62b5acaa503169f2b`.

- Root-inverse KL-Shampoo preconditions eligible two-dimensional weights.
- Embeddings, vectors, biases, and terminal heads use the Adam preconditioner.
- Factor matrices use float64.
- The refinement adds Adam step-norm grafting to the Shampoo matrix group.
- Every training report records the implementation and parameter allocation.

The exact dependency pin is in
`catalyst_attention/requirements-optimizers.txt`.

### Unlabelled target-domain alignment

`catalyst_attention/training.py` also supports CORAL latent alignment. It
matches source/target latent means and covariances after per-sample layer
normalization. Target batches are built with `require_target=False`; target
outcomes never enter the alignment loss.

## Benchmark design

The frozen v1 design tested a 2×2 matrix:

| Depth path | AdamW | KL-Shampoo |
|---|---:|---:|
| Standard Transformer | tested | tested |
| Multi-head residual routing | tested | tested |

After the v1 diagnostics, the v2 refinement restored the previously strongest
encoder depths, corrected routing to the per-sublayer residual formulation,
and added Adam step-norm grafting. The selected Delta-MHAR + AdamW candidate
then received a three-seed confirmation on:

- SpecGen source → systems A, B, C, and D;
- OCx24 UofT → VSP and VSP → UofT.

The primary transfer endpoint is Spearman rank correlation. All candidate
gains are measured against the stronger applicable existing-attention or
author baseline. Exact designs and their evidence boundaries are in:

- `catalyst_optimizer_mhar_design.json`
- `catalyst_optimizer_mhar_refinement_design.json`
- `catalyst_mhar_domain_alignment_design.json`

## Results

### Optimizer screening

| Candidate | Median transfer gain over 6 units | Median source validation Spearman | Decision |
|---|---:|---:|---|
| Standard + AdamW, v1 | -0.0376 | 0.8609 | reject v1 depth |
| Standard + KL-Shampoo | -0.3745 | 0.6456 | reject |
| Block MHAR + AdamW | -0.0299 | 0.8683 | refine routing |
| Block MHAR + KL-Shampoo | -0.3821 | 0.6737 | reject |
| Standard + grafted KL-Shampoo, v2 | -0.0110 | 0.8706 | reject for transfer |
| Sublayer Delta-MHAR + AdamW, v2 | **+0.0107** | 0.8601 | confirm |
| Sublayer Delta-MHAR + grafted KL-Shampoo, v2 | -0.0122 | 0.8744 | reject |

Grafting solved the optimization collapse, not the knowledge-transfer
problem. On this CPU benchmark, grafted KL-Shampoo also took roughly twice the
median time of AdamW in the refined screening.

### Three-seed Delta-MHAR confirmation

| Transfer unit | Delta-MHAR Spearman | Gain over frozen reference |
|---|---:|---:|
| SpecGen A | 0.5424 | -0.0100 |
| SpecGen B | 0.6196 | -0.0045 |
| SpecGen C | **0.2980** | **+0.0390** |
| SpecGen D | **0.7580** | **+0.0101** |
| OCx24 UofT→VSP | **0.6180** | **+0.0724** |
| OCx24 VSP→UofT | 0.5221 | -0.0578 |

The SpecGen median gain was +0.0028 with only two nonnegative systems; the
frozen gate required at least +0.02 and three nonnegative systems. OCx24 median
gain was +0.0073 and the reverse direction failed to beat ExtraTrees. Both
formal gates failed.

The separate three-seed standard-Transformer diagnostic scored 0.4449
UofT→VSP and 0.5860 VSP→UofT. This reveals complementary experts: Delta-MHAR is
stronger forward, standard attention is stronger reverse. Choosing the best
model after seeing these outcomes would yield 0.6180/0.5860, but that is a
post-outcome oracle and is not promotion evidence.

### CORAL screening

Standard attention + CORAL produced SpecGen gains of +0.0043, +0.0202,
+0.0386, and +0.0075 in one seed. Its median gain (+0.0139) remained below the
frozen +0.02 gate, and OCx24 UofT→VSP regressed by -0.2618. Delta-MHAR + CORAL
also failed both dataset gates. Further tuning on these recipients was stopped
to avoid turning known target outcomes into hyperparameters.

## Problem solved

This work answers three concrete questions that the previous repository model
could not answer:

1. Can second-order online preconditioning rescue catalyst knowledge transfer?
   Not here: source optimization and out-of-programme transfer are distinct.
2. Can attention over residual computation history expose reusable transfer
   routes? Partly: it creates meaningful programme-specific gains, but not one
   uniformly better model.
3. Is negative transfer caused only by latent distribution mismatch? No:
   CORAL helps one programme family and harms another.

The result is therefore a safer model-development system, not a cosmetically
more complicated Transformer: optimizers, architectural specialists, target
alignment, frozen gates, input hashes, checkpoints, and negative results are
all auditable.

## Evidence boundary and next confirmation

These are retrospective method-development experiments. Recipient outcomes
had already been inspected before the refinement and domain-alignment stages.
No model in this series is prospectively confirmed.

The next candidate should be a predeclared, target-label-free router between
standard attention and Delta-MHAR. The routing signal may use ensemble
epistemic disagreement and input-domain distance, but not target performance.
It must be frozen on the current programmes and tested once on a new sealed
catalyst programme. Useful new data must contain:

- a new laboratory/programme identity and fully hidden outcomes;
- catalyst composition plus precursor, ligand, synthesis/process, substrate,
  electrolyte, measurement protocol, and active-site descriptors where
  available;
- repeated measurements or uncertainty for calibration;
- enough independent catalyst groups to preserve group-held-out validation;
- at least two transfer directions or recipient programmes, so one lucky
  direction cannot define success.

Architecture and optimizers cannot reconstruct chemical and process variables
that are absent from the source data.

## Reproduce and verify

Run from the repository root:

```bash
PYTHONPATH=analysis:/path/to/facebookresearch/optimizers \
  python analysis/run_catalyst_optimizer_mhar_benchmark.py \
  --specgen-archive /path/to/specgen.zip \
  --ocx24-csv /path/to/ocx24.csv \
  --design analysis/catalyst_optimizer_mhar_refinement_design.json \
  --stage confirmation \
  --candidates sublayer_delta_mhar_adamw \
  --output analysis/results/catalyst_optimizer_mhar_confirmation.json

PYTHONPATH=analysis \
  python analysis/aggregate_catalyst_optimizer_mhar_results.py

PYTHONPATH=analysis pytest -q tests/test_catalyst_attention.py
```

The compact aggregate is
`results/catalyst_optimizer_mhar_summary.json`. It validates every design hash,
records every result hash, and preserves the formal reject/retain decisions.

## Method references

- KL-Shampoo: <https://arxiv.org/abs/2509.03378>
- Official optimizer implementation:
  <https://github.com/facebookresearch/optimizers>
- Multi-Head Attention Residuals: <https://arxiv.org/abs/2607.27230>
- Delta Attention Residuals: <https://arxiv.org/abs/2605.18855>
