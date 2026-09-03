# Stage 2 metadata-setpoint amendment v3

The first encoding amendment did not resolve the affected archives. A protected
metadata-only inspection of file ID 47629804 then read the raw companion text
and Unicode code points before opening its numeric CSV rows. The observed
setpoint token was exactly `23`, with no degree sign or unit. The earlier error
message displayed the expected value (`23°C`), not the observed token.

The validator is therefore amended to accept exactly `23`, `23°C`, or `23Â°C`
after removing ASCII spaces, while still requiring the unique matching
`*_ET_T23.csv` or `*_AT_T23.csv` filename. All other tokens remain invalid.
There is no numeric tolerance, rounding, unit conversion, regular-expression
guess, or fallback to another file or temperature.

This amendment was made from nonnumeric metadata. The affected capacity rows
remained unopened. Previously successful checkpoints are retained because the
capacity algorithm did not change; metadata-rejected checkpoints are rerun.
The endpoint, source models, applicability, controls, splits, hypotheses, and
inference remain unchanged.
