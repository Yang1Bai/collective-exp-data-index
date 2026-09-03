# Phase 1 findings — pooled laws, transport, and artifact gates

## Thermoelectric Meyer–Neldel test

Literature reference is part of the sample identity, so measurements with the
same nominal formula but different sources are not merged. The primary gate
requires at least four temperatures, a 100 K span, Arrhenius R²≥0.90 and
0<Ea<2 eV.

- n=112 reference-separated series;
- pooled ln A–Ea R²=0.107;
- HC3 slope p=0.0013, but T_iso=2165 K versus median harmonic temperature
  479 K;
- no chemical family with n≥8 survives Holm correction.

Conclusion: a statistically non-zero slope is not a high-explanatory universal
law.

## Direct UTS–yield-strength calibration transport

UTS and yield strength are paired only within the same source row.

- Borg: n=495 rows/208 compositions, log–log R²=0.790;
- BIRDSHOT: n=171 rows/151 compositions, R²=0.067;
- exact cross-dataset composition overlap: zero;
- unchanged Borg line on BIRDSHOT: R²=−3.006, cluster-bootstrap 95% interval
  [−4.154,−2.185];
- Borg-minus-BIRDSHOT slope difference [0.510,0.854];
- median UTS/YS ratio: 1.36 versus 2.72.

Conclusion: a strong source-dataset calibration is not a transportable
unconditional law.

## ISODB matched-loading isosteric analysis

The hash-verified pinned archive is streamed in memory. Pure-component systems
require at least three temperatures, positive monotone isotherms, a common
uptake range, and one geometric-midpoint fit per DOI–adsorbent–adsorbate system.

- 1,103 primary systems from 512 DOIs;
- pooled heat–intercept R²=0.637;
- T_iso=513 K versus median harmonic temperature 301 K;
- independent-parameter Krug null median R²=0.003 and p=0.001 for reaching the
  observed R²;
- adsorbate-family intercept shifts remain significant under DOI wild-cluster
  bootstrap (p=0.0002);
- family-specific slopes are not jointly required after DOI clustering
  (p=0.625), and leave-one-adsorbate-out R²=0.600.

Conclusion: this is a strong conditional empirical regularity, neither a
simple Krug artifact nor an unconditional single-line law. This honest
counterexample narrows the thesis from “global patterns do not exist” to
“aggregation does not automatically establish universal coefficients or
mechanism.”
