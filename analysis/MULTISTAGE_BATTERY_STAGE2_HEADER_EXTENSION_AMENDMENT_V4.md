# Stage 2 CSV-header extension amendment v4

After the unitless-setpoint repair, the affected Stage 2 files passed metadata
validation but stopped at the CSV header. Their header is the six published
columns followed by one additional trailing column, `time_to_sec`. The parser
had not begun iterating over data rows, so no affected numeric outcome had been
opened.

The header validator is amended to accept exactly either:

`run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type`

or

`run_time,c_vol,c_cur,c_surf_temp,amb_temp,step_type,time_to_sec`.

The additional column is ignored. The frozen extractor continues to parse time
only from `run_time`, current only from `c_cur`, and sections only from
`step_type`. Column order, names, and count must match one of the two exact
schemas; arbitrary extra columns and reordered columns remain invalid.

This is a header-only compatibility repair. It changes no numeric extraction,
endpoint, model, feature, applicability value, split, control, hypothesis, or
inference. Metadata/header-rejected checkpoints are rerun under the new hash;
previously successful capacity checkpoints remain unchanged.
