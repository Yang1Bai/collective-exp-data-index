# Policy-level knowledge transfer baseline

## Why this package exists

Every transfer method in this repository so far lives in the
**representation layer**: embedding similarity, hierarchical attention,
contrastive objectives, adversarial alignment. They all encode the same
implicit assumption — that a complex donor→recipient relevance relation can
be compressed into a fixed vector space and recovered by attention.

Recent theoretical work (DeepMind/JHU, *On the Theoretical Limitations of
Embedding-Based Retrieval*, arXiv:2508.21038) shows this assumption has a
representational ceiling that more data and bigger encoders do not remove.
For this project the implication is direct: cross-domain transfer should be
reformulated as a **context-conditioned policy decision** — *whether* to
transfer, *what* may cross (point prediction vs. ranking only), and *when*
to abstain — with representation models demoted to candidate generators.

`policy_transfer.py` implements the first **decision-layer** row of the
comparison matrix:

| Method | Where transfer happens |
|---|---|
| Embedding similarity / ExtraTrees | representation |
| Standard attention Transformer | representation |
| Contrastive latent alignment | representation |
| **Frozen transfer policy** | **decision** |
| **Learned policy (GBM, leave-one-pair-out)** | **decision (learned)** |
| **LLM policy (pinned prompt/decision artifact)** | **reasoning** |

The frozen policy is the baseline that any *learned* or *LLM-reasoned*
policy must beat; the learned policy is trained strictly
leave-one-pair-out so a deciding model never sees its own pair's
outcome; the LLM policy replays decisions recorded over
`as_prompt_dict()` JSON only, pinned as a hashed artifact in
`analysis/results/llm_policy_decisions.json`.

## Contract

- `TransferEdgeState` is the only information a policy may see: source fit
  quality, donor-recipient coverage/distance geometry, dataset sizes,
  method identity, feature richness. **No target outcome fields.** The
  `as_prompt_dict()` projection is the exact field set admissible to a
  downstream LLM/agent prompt.
- `FrozenThresholdPolicy` decides `apply / rank_only / abstain` per
  (edge, method) with thresholds fixed a priori from the repo's attempt
  ledger (e.g. contrastive objectives amplify weak-source-fit failure —
  the steel-family rows — so they abstain earlier; attention needs ≥ ~400
  donor rows).
- Evaluation is closed-world: every policy decision on every directed
  edge is scored against realized outcomes *after* decisions are frozen.
  Abstention scores 0 (no claim, no harm); applying into negative ρ is a
  harm edge. `evaluate_policy` fails closed on any missing realized
  outcome.

## Running

```bash
# full suite (15 directed edges: 6 alloy + 2 OCx24 + 3 SECCM + 4 SpecGen)
.venv/bin/python analysis/run_policy_transfer_benchmark.py \
    --alloy-epochs 100 --specgen-epochs 40 \
    --out analysis/results/policy_transfer_benchmark.json

# policy comparison (frozen vs learned vs LLM vs anchors)
.venv/bin/python analysis/run_policy_comparison.py
```

Edge suite:

| Edges | Role |
|---|---|
| 6 alloy bidirectional | composition-only, historically weak/harmful |
| 2 OCx24 uoft↔vsp | cross-lab CO2R, known positive ranking transfer |
| 3 SECCM cross-library | documented negative-transfer boundary |
| 4 SpecGen zero-shot | spectra+conditions, known positive |

Output: `analysis/results/policy_transfer_benchmark.json` with per-edge
geometry, per-method realized ρ, policy decisions, harm accounting, and a
SHA-256 manifest. Tests: `tests/test_policy_transfer.py`.

## Reading the result

The headline numbers are **mean realized Spearman** and **harm edges**,
policy vs. always-transfer for the same representation method:

- If the frozen policy's mean realized ρ beats always-transfer and has
  zero harm edges, the decision layer adds measurable value over pure
  representation transfer — the pilot supports the reformulation.
- `missed_positive_edges` reports abstained edges that would have been
  strongly positive (ρ > 0.3); a large count means the thresholds are too
  conservative and should be re-derived — from an independent edge set,
  not from the same outcomes.

## Frozen thresholds (v1)

| Threshold | Value | Ledger motivation |
|---|---:|---|
| `source_fit_floor` | 0.50 | weak donor fit transfers noise (steel-family rows, src ρ ≈ 0.11 → transfer ρ ≤ 0.19) |
| `source_fit_floor_contrastive` | 0.60 | contrastive amplifies weak-fit failure (steel→birdshot: std +0.539 → contr −0.477) |
| `coverage_floor` | 0.35 | below this the donor does not geometrically cover the recipient |
| `rank_only_coverage_floor` | 0.15 | partial coverage supports at most a ranking claim |
| `min_source_n_attention` | 400 | repo finding: attention needs ≥ ~400 rows + rich features to beat trees |
