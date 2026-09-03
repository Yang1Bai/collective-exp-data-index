# Stage 2 metadata-encoding amendment

During the first authorized Stage 2 release, several archives were stopped
before their numeric CSV data rows were opened because the nonnumeric companion
metadata encoded the 23-degree setpoint as `23Â°C` rather than `23°C`. This is
the standard UTF-8/Windows-1252 mojibake representation of the same degree-sign
text. The CSV filename remained `*_ET_T23.csv` or `*_AT_T23.csv`; no numeric
outcome from an affected file was inspected.

The metadata validator is amended to remove ASCII spaces and accept exactly two
tokens for the frozen reference temperature: `23°C` and `23Â°C`. No other
temperature, number, unit, filename, or fuzzy match is accepted. The same rule
is applied to every Stage 2 archive. Previously successful checkpoints remain
valid because the capacity integration algorithm is unchanged. Metadata-
rejected checkpoints are rerun because their numeric rows were never opened.

This amendment changes no endpoint, step code, current integration, condition
group, source feature, applicability value, threshold, model, split, control,
hypothesis card, comparison, or inferential rule. It is a disclosed parsing
repair after target release and before outcome access for the affected files.
