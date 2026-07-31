# Pre-outcome endpoint-schema amendment for the multi-stage battery test

## Reason for the amendment

The version-4 target design correctly froze ET-to-AT capacity retention before
outcome access, but described the paper-defined capacity as discharge capacity
alone. The authoritative data descriptor states that RPT capacity was computed
as the mean of charge and discharge capacity. This amendment corrects the
endpoint before any numeric Stage 1 or Stage 2 CSV data row is opened. It is a
substantive pre-outcome correction, not a favorable-result-driven change.

The supporting primary sources are the [Scientific Data article](https://www.nature.com/articles/s41597-024-03859-z),
[Table 5](https://www.nature.com/articles/s41597-024-03859-z/tables/5), and
[Table 6](https://www.nature.com/articles/s41597-024-03859-z/tables/6). They
establish that ET and AT contain capacity tests at 10, 45, and 23 degrees
Celsius; current is negative during discharge; `step_type=21` is the capacity
charge and `step_type=22` is the capacity discharge; and reported RPT capacity
is the mean of the two capacities.

## Frozen primary endpoint

The primary reference temperature is 23 degrees Celsius. Exactly one
`*_ET_T23.csv` and one `*_AT_T23.csv` must be present in each mapped cell
archive, with companion metadata confirming the 23-degree setpoint.

Within each file, elapsed time is parsed from `run_time`. Charge and discharge
capacities are trapezoidal current integrals over adjacent records that both
belong to `step_type=21` and `step_type=22`, respectively. Transitions between
step types are not bridged. Current remains signed: charge capacity is the
positive step-21 integral and discharge capacity is the negative of the
step-22 integral. The RPT capacity and cell endpoint are

`Q_RPT = (Q_charge + Q_discharge) / 2`

`Q_rel_end_percent = 100 * Q_RPT_AT_T23 / Q_RPT_ET_T23`.

No smoothing, clipping, interpolation, imputation, or post-outcome file choice
is permitted. A missing or invalid component makes the cell unevaluable with a
reason code. The existing 80% cell-coverage and two-cells-per-condition gates
remain unchanged.

## Header-only evidence and access ledger

Three archives were inspected: one Stage 1 cell, the duplicated-name Stage 2
counterpart, and one independent INT Stage 1 mapping-conflict example. For each
CSV member, the audit read exactly one newline-terminated physical header line.
Complete nonnumeric `*_meta.txt` companions were allowed. All 32 inspected CSV
headers were identical:

`run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type`

Every inspected archive contained unique ET_T23 and AT_T23 files whose metadata
reported a 23-degree setpoint. No numeric CSV data row was opened or parsed.
The machine-readable evidence is
`analysis/results/multistage_battery_header_schema.json`, and the immutable
extractor is `analysis/multistage_battery_endpoint_schema.json`.

## Statistical boundary

Charge-only and discharge-only retentions are prespecified sensitivities, not
alternative primary endpoints. Charge-discharge disagreement and the 10- and
45-degree results are diagnostics. None may rescue a failed 23-degree primary
test. The independent unit remains the Stage 2 condition group, and Holm
correction remains limited to the same two primary efficacy contrasts.
