# Physics-aware mixture relation transfer: method adoption and formal development result

## Decision

The useful lesson from the BambooMixer studies is not to import a larger neural
network into every donor--recipient edge. It is to transfer a representation
and response relation that respect the structure of the recipient problem.
For liquid-electrolyte mixtures, this means:

1. representing a formulation as an unordered, molar-fraction-weighted set of
   solvent and salt components;
2. retaining temperature, salt concentration and their interactions explicitly;
3. learning the source relation once and freezing it before external-target
   prediction;
4. using a few target labels only to shrink a simple calibration correction
   toward zero, rather than refitting the source relation;
5. comparing against target-only, state-only, chemistry-permuted, adjacent-only
   and wrong-salt controls at the same target-label budget.

This is now implemented as the **physics-aware mixture relation** route in the
project. It complements, rather than replaces, the existing anchored-response
and ordinal-ranking routes.

## What was learned from the published ML method

The published architecture separates molecular encoding from formulation
encoding, aggregates components with normalized molar-ratio weights and
attention, and includes an explicit conductivity response block containing
temperature and concentration. Its training curriculum progresses from
molecular properties to computational formulations and then experimental
conductivity. These choices encode three scientifically useful priors:
component-order invariance, state dependence and a transferable intermediate
relation.

The public implementation was treated as a source of design principles, not as
an unquestioned benchmark. We did not inherit its row-level formulation split,
its unmasked attention implementation, or a comparison that gives the
recipient-only model more target labels than the transferred model. The new
benchmark instead groups all rows from an exact formulation, excludes the
external salt identity from the source, preserves identical target-label
budgets and uses chemistry-specific falsifiers.

## Auditable implementation

- `mixture_response_transfer_common.py` constructs a permutation-invariant
  formulation representation from normalized molar weights, molecular
  descriptors, element fractions, Morgan fingerprints, temperature,
  concentration and state interactions.
- `run_bamboomixer_response_transfer_development.py` trains the frozen source
  relation, evaluates an external LiAsF6 programme, runs formulation-grouped
  bootstrap contrasts, tests outcome-independent few-shot anchors and performs
  leave-one-salt-out portfolio checks.
- `bamboomixer_response_transfer_design.json` declares the target, controls,
  group unit, label budgets, resampling and claim guard.
- `verify_bamboomixer_response_transfer_development.py` independently checks
  hashes, row counts, salt exclusion, formulation grouping, metric
  recomputation and completeness.

The source contains 10,407 experimental conductivity measurements from 22 salt
identities. The external LiAsF6 target contains 1,827 measurements from 176
exact formulations. LiAsF6 is absent from the source.

## Formal results

The full mixture relation transfers to the external LiAsF6 programme with
log-scale \(R^2=0.732\), raw-scale \(R^2=0.629\), log-RMSE \(=0.336\) and
Spearman \(\rho=0.871\).

Formulation-grouped bootstrap contrasts show that this performance is not
explained by temperature and concentration alone. Relative to the state-only
model, the full relation reduces log-RMSE by 28.64% (95% CI 24.03--33.52%),
increases Spearman correlation by 0.160 (0.132--0.188), and increases raw
\(R^2\) by 0.230 (0.182--0.279). Relative to a chemistry-permuted source, it
reduces log-RMSE by 27.16% (22.78--31.90%) and increases Spearman correlation
by 0.134 (0.108--0.162).

The source ablations identify both adjacency and diversity. Removing LiPF6,
the closest abundant fluorinated-lithium-salt neighbour, worsens performance:
the complete source improves log-RMSE by 16.38% (12.66--20.24%) and rank
correlation by 0.041 (0.023--0.062) relative to the LiPF6-excluded source.
However, the complete 22-salt source also outperforms a LiPF6-only donor by
28.76% (22.94--33.88%) in log-RMSE and 0.055 (0.037--0.075) in rank
correlation. Thus the adjacent source contributes a real local relation, while
the broader electrolyte portfolio improves coverage of solvent and state
effects.

In leave-one-salt-out tests, the full chemistry-aware relation beats a
state-only model on both log-RMSE and ranking for 7 of 9 eligible salt targets.
The two log-RMSE failures, LiBF4 and LiTDI, retain positive rank gains but have
negative error gains. They should therefore be routed to ranking-only or
abstention rather than called prediction-positive.

At five target anchors, the frozen source already achieves log-RMSE 0.331,
\(\rho=0.873\) and raw \(R^2=0.631\). A target-only ridge model trained on the
same five anchors has log-RMSE 0.766, \(\rho=0.071\) and raw \(R^2=-0.376\).
The shrinkage adapter leaves ranking essentially unchanged and improves raw
\(R^2\) to 0.653. The scientific interpretation is therefore that the source
relation is already portable; the few target labels mainly calibrate absolute
scale. The anchor correction itself is not the source of the large gain.

## What this changes in the project

The project now has a fourth explicit transfer object:

> **Physics-aware mixture relation:** use when donor and recipient share a
> mixture state space and endpoint, but the recipient contains a new component
> identity. Freeze the relation learned across source components; use target
> anchors only for a shrinkage calibration; route to prediction, ranking or
> abstention according to formulation-grouped controls.

This is a stronger mechanistic example than generic donor-feature injection:
the source relation works with zero target labels, its chemistry contribution
survives matched falsification, the closest neighbour is specifically useful,
and the source portfolio generalizes to seven of nine held-out salts. It also
shows why "neighbor" must be operational: it is joint support in molecular
mixture chemistry, concentration, temperature and endpoint, not a verbal
domain label.

## Claim status and next confirmation

The method was designed after the 2026 LiAsF6 outcomes and published transfer
result were inspected. It is therefore a verified method-development result,
not an independent confirmatory edge and not prospective discovery
acceleration. It belongs in the main manuscript as a strong worked example of
representation-aware relation transfer, with this limitation stated directly.

The next decisive test is to freeze the representation, source portfolio,
shrinkage rule, grouping unit and success gate before opening a different
electrolyte programme or a newly measured salt. That test must compare the
frozen source relation against a same-budget recipient-only model and retain
state-only, chemistry-permuted and neighbour-exclusion controls.

## Source record

- Lai et al., *Nature Machine Intelligence* (2026),
  <https://doi.org/10.1038/s42256-026-01277-x>.
- Yang et al., *Nature Machine Intelligence* 8, 186--196 (2026),
  <https://doi.org/10.1038/s42256-025-01173-w>.
- Public extension data:
  <https://huggingface.co/datasets/PKUAIBDA/Dataset_Bamboomixer_extension/tree/main>.
- Public original code and data:
  <https://huggingface.co/ByteDance-Seed/bamboo_mixer>.

