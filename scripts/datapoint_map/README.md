# Data-point-level map pipeline

Builds `datapoint_map.html` - every point is one experimental sample/measurement.

1. `make_map.py`  - clones/loads open-licensed datasets (see list in file),
   parses formulas & SMILES into a shared element-composition space,
   embeds with PCA + t-SNE, writes `points.json`.
   Datasets currently included: ESTM thermoelectrics, AqSolDB, IUPAC pKa,
   OCx24 electrocatalysts, MPEA alloys (Borg), FreeSolv, Photoswitches.
2. `make_html.py` - renders `points.json` into the interactive canvas HTML.

Requirements: pandas, numpy, scikit-learn, openpyxl; dataset repos cloned
into a working dir (git clone URLs are in the catalog entries).
To add a dataset: add a loader block in `make_map.py` (formula_vec or
smiles_vec), a color/URL entry in `make_html.py`, rerun both.
