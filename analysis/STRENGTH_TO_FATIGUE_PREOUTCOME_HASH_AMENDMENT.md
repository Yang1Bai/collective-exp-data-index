# Pre-outcome recipient-hash transcription amendment

The first execution of the pre-outcome audit stopped before accessing any
numeric fatigue outcome because the Figshare XLSX MD5 had been transcribed with
one missing character in `strength_to_fatigue_ood_design.json`.

- Incorrect transcription: `d4d7456f83a4f55e3aa790acded2b01`
- Figshare and local-file MD5: `d4d7456f83a4f55e3aa790acdedd2b01`

This amendment changes only that identifier. The recipient file, scientific
question, endpoint, eligibility rules, split, models, controls, inferential
plan, and success gates are unchanged. No numeric row from `S-N`, `e-N`, or
`dadn` was read before this correction.
