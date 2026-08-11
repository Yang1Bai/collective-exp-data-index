# OPD router — real-state teacher preflight result

## Status: implementation gate FAILED; scientific gate not reached; no OPD effect claimed

This is the honest outcome of running the frozen OPD design contract
(`catalyst_opd_router_design.json`) against real, programme-held-out
routing states. The repo's own falsification-gated contract blocks the
scientific claim, exactly as designed.

## What was added

* `run_opd_router_states.py` — trains the frozen Standard / Delta-MHAR
  expert pair on each of the 15 directed transfer edges and emits one
  target-label-free `RouterState` per edge (the 12 allowed fields only),
  plus an evaluation-only payload of realized expert Spearman values and
  the oracle expert. Replaces the 4 synthetic smoke prompts that
  shipped with the pilot with 15 real programme-held-out states.
* `run_opd_router_evaluation.py` — teacher preflight + downstream
  scientific-gate scorer: loads a white-box teacher, generates one
  decision per real state, scores routed Spearman against realized
  outcomes, and checks both the implementation gate (strict JSON ≥ 0.95)
  and the scientific gate (median gain ≥ 0.02 over best frozen single
  expert, no direction regression, harm rate not increased).

## The gate result

```
IMPLEMENTATION GATE: valid_json = 0.000 (≥ 0.95)  -> FAIL
SCIENTIFIC GATE: not reached (implementation gate failed)
```

The strongest offline-available teacher (HuggingFaceTB/SmolLM2-360M-Instruct)
produced **0 / 15** strict-JSON-valid decisions on real routing prompts.

### Failure mode

Every one of the 15 teacher completions was well-formed JSON with the
correct four keys, but the `reason_codes` field contained expert names
(`"mhar"`, `"ensemble"`) instead of valid reason codes. The fail-closed
decoder rejects these and routes the decision to `abstain`:

```
{"expert": "standard", "action": "predict",
 "confidence": 0.0633,
 "reason_codes": ["source_supported", "mhar", "ensemble"]}
                                  ^^^^    ^^^^^^^^  not valid reason codes
```

Valid reason codes are: `source_supported, experts_agree,
high_disagreement, standard_closer, mhar_closer, high_uncertainty,
out_of_support, missing_state, low_source_skill`. The 360M teacher
conflates the expert enum (`standard`/`mhar`/`ensemble`) with the
reason-code enum and echoes the experts it did not select into
`reason_codes`. This is a model-capacity failure: the prompt already
enumerates the valid reason codes, but the model does not follow the
constraint.

## Why no stronger teacher was available offline

| Candidate | Status |
|---|---|
| HuggingFaceTB/SmolLM2-360M-Instruct | cached, usable, **failed gate** (0/15 valid) |
| HuggingFaceTB/SmolLM2-135M-Instruct | cached, weaker than 360M — would also fail |
| GreenBitAI/Qwen3-4B-Instruct-2507-layer-mix-bpw-4.0-mlx | cached but **MLX layer-mix quantization**; `transformers` cannot load it (most weights newly initialized to random) — unusable as a white-box teacher |

The pilot defaults to `local_files_only=True`; no qualifying stronger
instruct model in standard HF format is cached locally.

## What this means

The design contract's `promotion_rule` is explicit: *"Do not replace the
existing router or any numerical expert unless both the implementation
gate and sealed scientific gate pass."* Neither passes. The OPD router
therefore remains at `algorithm-complete-scientific-effect-unverified`,
the same status as before — but now on real programme-held-out states
rather than synthetic smoke prompts, and with the specific blocker
identified (teacher JSON discipline, not the distillation algorithm).

## Paths to unblock (in increasing order of cost)

1. **Allow one curated download.** A standard-HF-format instruct model
   in the 1.5–3B range (e.g. Qwen2.5-3B-Instruct, Llama-3.2-3B-Instruct)
   would likely clear the JSON gate. Requires `--allow-download` and
   user consent for a multi-GB download.
2. **Few-shot prompt (design change).** Add 2–4 worked examples to
   `RouterState.to_prompt()` so the teacher sees the reason-code
   distinction concretely. Bumps `design_version`; would need a new
   frozen design artifact.
3. **Tolerant reason-code parser (design change).** Accept expert names
   in `reason_codes` and map them. Weakens the fail-closed contract;
   not recommended.
4. **Use the LLM policy row (already built) as a black-box teacher.**
   The blind Claude policy from `learned_policy.py` produces valid
   decisions and cleared 0 harm — but it cannot provide white-box
   logits, so it is not an OPD teacher. It is a separate decision-layer
   row, not a distillation source.

Option 1 is the cleanest next step and stays within the frozen contract.
