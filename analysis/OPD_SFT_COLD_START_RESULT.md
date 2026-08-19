# OPD SFT cold-start result

## Status

**Teacher implementation gate failed; OPD was not run; no scientific effect is
claimed.**

Two independently seeded, target-label-free SFT attempts made the
SmolLM2-360M teacher produce valid router JSON, but neither taught it the
frozen routing behaviour. The gated runner therefore stopped before loading
or updating the 135M student.

## Real-state correction before training

The previously generated 15 programme-transfer states contained three
material diagnostic errors:

1. `source_validation_spearman` used the full-source apparent metric rather
   than the held-out validation metric;
2. predictive uncertainty read a nonexistent `variance` key, making every
   expert standard deviation zero;
3. `standard_domain_share` duplicated composition coverage instead of using
   the Standard-versus-MHAR latent OOD comparison.

`run_opd_router_states.py` now uses held-out validation Spearman and the
diagnostics returned by `ExpertRouter`. The regenerated states have nonzero
uncertainty and distinct domain-share/coverage fields. This correction changes
actual decisions: the steels donor, for example, has held-out source Spearman
`-0.207` and correctly triggers `low_source_skill` abstention.

## Frozen SFT attempts

| Attempt | Train / held-out | Objective | JSON valid | Held-out expert/action agreement | Result |
|---|---:|---|---:|---:|---|
| v1 | 96 / 48 | ordinary completion loss | 100% | 14.6% | all states became `ensemble + predict` |
| v2 | 140 / 70 | decision-value tokens weighted 8x | 100% | 15.7% | 63/70 became `mhar + predict`; no rank or abstain |

Both datasets were balanced across seven expert/action strata. V2 used a new
train and held-out RNG stream after the v1 collapse was inspected; it did not
reuse the v1 held-out states.

The result separates two capabilities that token loss otherwise conflates:

- format following succeeded (`0% -> 100%` strict JSON validity);
- state-conditioned routing failed by a wide margin (`>=90%` required).

Lower SFT loss therefore is not evidence of a learned router.

## Retrospective real-edge diagnostic

The best frozen single expert remains Standard with median Spearman `0.2938`.
The deterministic target-free policy reached `0.0732`; the v1 teacher reached
`0.2885` by collapsing to ensemble; and the v2 teacher reached `0.1538` by
collapsing primarily to MHAR. None passed the `+0.02` gain gate. Harmful
transfer rates were respectively `0.133`, `0.333`, and `0.200`.

These outcomes were already inspected during method development. They are
retrospective diagnostics, not sealed scientific confirmation.

## Decision

Do not continue tuning this 360M teacher and do not run OPD against it. The
next defensible comparison is the deterministic policy versus a small numeric
router trained on a substantially larger set of programme-held-out edges. A
larger white-box LLM teacher is optional, but only after the extra model and
compute cost is justified.

The compact audit record is
`results/catalyst_opd_sft_cold_start_summary.json`. Regenerable raw reports and
LoRA checkpoints remain in ignored checkpoint directories.
