# Caltech ionic-conductor cross-platform hash amendment

Frozen after Balam job `70723` failed during validation and before any formal
policy trajectory was calculated. The job started at `2026-07-17T03:29:10`,
ended after 12 seconds, and raised `Target audit hash changed after
implementation freeze` before source fitting or campaign execution.

The audit JSON produced on Windows contained 98 CRLF line endings. The same
deterministic audit is written on Linux with LF line endings, so byte-level
SHA-256 differs even when the parsed JSON object is identical. This is an
execution-provenance defect, not a scientific-protocol change.

The rerun verifies the audit by canonical JSON hashing: parse JSON, serialize
with sorted keys, compact separators, UTF-8 and no ASCII escaping, then compute
SHA-256. The required canonical hash is
`d702792256e7ff3922f969bedd175e444434d7d5706347c29ae5357189181338`.
The audit writer also requests LF output explicitly. Raw target MD5, frozen
design hashes, schema and inference amendments, target/source quality gates,
models, seeds, folds, policies, endpoints, comparisons and decision thresholds
are unchanged.
