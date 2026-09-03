# Battery Conductivity Value-Semantics Amendment

This amendment was made after the formal release parser ran but before any
source or recipient model was fit.

The frozen implementation intended to place every property in a canonical
unit. It incorrectly specified parsing `Raw_value`, which is the original
literature text and may contain scientific-notation typography, ranges, or
multiple reported values. For example, `10 − 4` is stored as the canonical
numeric `Value = 0.0001`; tokenizing the raw string produces the invalid
number 7. The released `Value` column is already converted by the database
authors to the dimensional unit reported in `Unit`: S cm-1 for conductivity,
mAh g-1-equivalent for gravimetric capacity, V for voltage, and Wh kg-1 for
energy.

The corrected release therefore:

1. parses the canonical `Value` column only;
2. uses `Raw_unit` only to admit the frozen unit families;
3. applies no second unit multiplier to `Value`;
4. leaves material, DOI, state parsing, physical bounds, deduplication,
   endpoint, OOD split, models, controls, and inference unchanged.

This is a value-semantics correction, not an outcome-dependent method change.
No model result existed when it was made. The invalid first release is
superseded and retained only through its recorded hash in the execution
history.

- Original release-script SHA256:
  `b91bd2ead125a37d5ea549a7773c16c7359ad2858be510db44b4dfc40929523e`
- Corrected release-script SHA256:
  `ec15daadd7a50e8d7691433de7f802bfa6380bafcef88564c211419b3cb6ea4c`
- Invalid first-release SHA256:
  `8ddad32ae46b348b41da09081d314c656580665432c166dd9c540ba570a317a9`

