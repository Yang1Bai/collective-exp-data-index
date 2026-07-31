# TRI OER outcome-free pickle schema amendment

The official file matched MD5 `f84665fd51185cce686e911fbd3bca53` and SHA-256
`31bfd1fee2c56095844daad4aff0fdead298c4dcfb647c1b0b30f6ff2af8a5e1`.
A restricted schema reader replaced NumPy arrays with stubs, recorded only
dictionary keys, dtypes, shapes, and raw byte lengths, and did not decode any
`fom` byte buffer.

The deposited dictionary contains keys 3496, 3851, 3860, 3875, and 4098. The
official paper Table 1 defines the four benchmark datasets and composition
systems as:

- 3496: Mn–Fe–Co–Ni–La–Ce, 2,121 rows;
- 3851: Mn–Fe–Co–Ni–Cu–Ta, 2,119 rows in the deposited file;
- 3860: Mn–Fe–Co–Cu–Sn–Ta, 2,121 rows; and
- 4098: Ca–Mn–Co–Ni–Sn–Sb, 2,121 rows.

Key 3875 is absent from the paper's four-dataset benchmark and is excluded
before outcome access. For the four retained sets, only the `comp` buffers may
be decoded during pre-outcome preparation. `fom` buffers remain undecoded until
metadata, source ranks, policy orders, hypothesis cards, implementation, and
their hashes are frozen. The paper defines `fom` as the negative OER
overpotential at 3 mA cm-2, so larger values are better.

