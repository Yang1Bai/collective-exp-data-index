# Caltech acid-OER accidental-access exclusion

**Recorded:** 2026-07-18, immediately after the first archive inspection and
before any target model, source rank, candidate order, or target-wide outcome
analysis was performed.

The intended header-only archive check printed the first data line as well as
the header for three files. This exposed one row from `oer_all_foms.csv`
(`plate=5411`, composition Mn=0.58, Sb=0.09, Sn=0.26, Ti=0.07, Co=0) and one
raw electrochemistry row (`plate=5029`, `Sample=3522`). The XRD line contained
no target OER activity. No other target row was displayed or summarized.

The exposed information cannot be erased. The following exclusions are fixed
before further target access:

1. plate 5029 is removed in full from confirmatory target inference;
2. the exact exposed plate-5411 composition row is removed in full, including
   every target endpoint; and
3. all exclusions and remaining plate counts are reported.

The remaining plates 5411, 5412, 5413, and 5414 retain the predeclared
leave-one-plate-out structure. If any formal minimum fails after these
exclusions, this target is downgraded to a contamination-sensitivity analysis
and a different second-family target is required. This amendment cannot be
used to remove any additional unfavorable row or plate.

