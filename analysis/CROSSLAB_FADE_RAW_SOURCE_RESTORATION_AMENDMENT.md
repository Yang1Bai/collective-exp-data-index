# Cross-laboratory fade transfer — raw-source restoration amendment

**Frozen:** 2026-07-29, before downloading either raw source and before reading
any raw HUST recipient file. This amendment restores the data channels required
by the original frozen protocol; it does not change its scientific hypothesis,
recipient, endpoint, candidate-time boundary, controls, seeds, inference, or
success gate.

## Why a restoration run is required

The first execution used a convenience mirror because the original hosts were
unreachable from that execution environment. The mirror omitted the raw
voltage/current trajectories needed for the frozen \(\Delta Q(V)\) features and
truncated the trajectories before the original 80% state-of-health endpoint.
It therefore forced a later 89% milestone and a 51-feature proxy dominated by
laboratory-specific charge summaries. All recipient cells were rejected by the
support gate, and even the within-recipient oracle had negative absolute
\(R^2\). That execution is retained as an audited infrastructure-limited
abstention; none of its files are overwritten.

The original source URLs are now reachable from the local staging machine.
This run restores:

- all four MATR `.mat` batches from `data.matr.io`;
- the HUST `hust_data.zip` release from Mendeley Data;
- the original 80% state-of-health endpoint;
- voltage-resolved \(\Delta Q(V)\) between cycles 10 and 100;
- the compact feature list in `crosslab_fade_transfer_design.json`, rather than
  the mirror-only 51-feature proxy.

## Integrity boundary

The raw HUST files are pickled per-cell dictionaries, so opening a file loads
its full trajectory. A deterministic boundary builder therefore performs one
non-analytic pass that:

1. emits an **early release** containing cycles 1–100 and protocol metadata;
2. emits a separate **sealed outcome release** containing the full capacity
   trajectory and 80%-SOH label;
3. reports only file counts, schema booleans, hashes, and the boolean
   `has_at_least_100_cycles` before the formal stage;
4. never reports total cycle counts, capacity values after cycle 100, or life
   labels during audit or method fitting.

The analyst-facing audit and donor self-check consume only the early release.
The sealed outcome release is opened once, only after the audit, realized
feature intersection, implementation hash, and donor-only gate are frozen.
Because a prior mirror run exposed an approximate HUST milestone, this
restoration is described as a **pre-specified raw-source confirmation**, not as
a never-before-seen recipient. The true 80%-SOH endpoint and restored
\(\Delta Q(V)\) analysis remain untouched until the formal stage.

## Restored feature contract

Only features available for at least 95% of both datasets survive:

- \(\log_{10}\operatorname{Var}[\Delta Q(V)_{100-10}]\);
- \(\log_{10}|\min \Delta Q(V)_{100-10}|\);
- discharge-capacity slope and intercept over cycles 2–100;
- \(Q_d(100)/Q_\mathrm{ref}\);
- mean and standard deviation of coulombic efficiency over cycles 10–100;
- mean charge and discharge C-rate;
- mean temperature only if present in both datasets.

The voltage grid is the overlap of the two declared operating windows,
2.0–3.5 V, with 900 ascending points. Capacity curves are interpolated on the
discharge branch and converted to a relative curve by subtracting their value
at the high-voltage boundary before differencing. Internal resistance and
temperature are donor-only in this pair and are excluded from the formal
intersection.

The applicability gate is computed on the mechanism-response features
(\(\Delta Q(V)\), early capacity trend, normalized capacity, and coulombic
efficiency). Protocol descriptors condition the donor mapping but are not
allowed to dominate the support distance by merely identifying the laboratory.
This is the literal implementation of the original protocol's
"physically anchored response + protocol conditioning" intent and is frozen
before raw recipient access.

## Output isolation

All restored-run artifacts use the prefix `crosslab_fade_raw_`. The prior
mirror results remain immutable. A positive result is accepted only if every
original success gate passes. A null, harmful result, or applicability
abstention remains the reported result; there is no post-outcome model change
or second formal run.

## Donor-only endpoint encoding clarification

The first raw MATR donor self-check was run before opening the HUST archive. It
found 180 donor cells but only 43 whose stored capacity arrays contained a
sample at or below 80% of the cell-specific reference. Inspection was confined
to the donor. The MATR files separately provide the publisher's `cycle_life`
field; for most batches, a trajectory terminates at the declared endpoint
without retaining a sample beyond the threshold. Requiring an observed
post-threshold sample therefore misclassified administrative termination as
right censoring.

For MATR only, the restored implementation uses the released `cycle_life` as
the 80%-SOH outcome and fits degradation coefficients to the capacity samples
available up to that declared endpoint. The five batch-1 cells continued in
batch 2 use the continuation offsets published in the BatteryML preprocessing
code. The HUST recipient endpoint remains the first observed cycle at or below
80% of its own reference and is unchanged. This is a source-schema correction
made from donor-only evidence before recipient access; the donor-count and
batch-out skill gates remain unchanged.

## Donor-only transfer-object selection

Before the HUST archive was opened, 32 candidate combinations were compared by
leave-one-MATR-batch-out validation. The candidate grid crossed response-only
versus response-plus-protocol features, absolute versus within-laboratory
robust alignment, absolute-life versus residual-correction targets, and four
fixed learners. The complete candidate table and out-of-fold predictions are
retained.

Eligibility required both donor batch-out Spearman \(\ge 0.5\) and absolute
log-life \(R^2>0\). Among eligible candidates, the lowest RMSE determined the
primary transfer object. The selected primary is:

- input: the seven response features only (including \(\Delta Q(V)_{100-10}\));
- target: absolute \(\log_{10}\) 80%-SOH life;
- learner: random forest, 800 trees, minimum leaf size 2, `max_features=0.8`;
- donor batch-out performance: Spearman 0.6681, RMSE 0.13187, \(R^2=0.4011\).

The response-only ridge attained higher rank correlation (0.7774) but failed
absolute utility (\(R^2=-3.948\)) and was rejected. The originally frozen
coefficient-posterior model passed its donor skill gate (Spearman 0.6128) and
is retained as a mechanistic sensitivity, not promoted to primary.

This selection uses no HUST file or outcome. The primary therefore transfers a
mapping from each cell's own early **change** to late life, rather than a raw
endpoint value or a laboratory-identifying protocol signature.

## Candidate-covariate normalization amendment

After the first outcome-free HUST early release, the support audit found 77/77
cells outside MATR support. No HUST life label or post-cycle-100 statistic had
been reported or opened. The candidate-time covariates showed a source-specific
capacity calibration (median early intercept about 1.07 Ah in MATR and 1.21 Ah
in HUST), which also scales absolute \(\Delta Q(V)\). A second, outcome-free
feature contract therefore expresses both capacity trend and \(\Delta Q(V)\)
relative to each cell's own early capacity. Coulombic-efficiency mean is
excluded because it showed a laboratory-wide integration offset; its
within-cell standard deviation is retained.

The normalized feature set was then evaluated using MATR only. Among candidates
passing donor Spearman \(\ge0.5\) and absolute \(R^2>0\), the normalized
response random forest had the lowest batch-out RMSE:

- Spearman 0.6497;
- RMSE 0.12721 log-life;
- \(R^2=0.4427\).

This is better in absolute utility than the first absolute-response random
forest (RMSE 0.13187, \(R^2=0.4011\)). The normalized response set is therefore
the primary for the second early-release support audit and, if support passes,
the single formal run. This is explicitly **recipient-covariate-informed domain
harmonization**, not outcome-blind method selection. It can support a
mechanistic transfer demonstration but not a pristine external confirmation.
