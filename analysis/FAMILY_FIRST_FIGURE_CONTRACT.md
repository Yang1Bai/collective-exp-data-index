# Figure contract: CCA family-first exploration

- **Core conclusion:** qualified neighboring ranks become more useful for OOD
  exploration when they are preserved as complementary proposals and the first
  acquisition pass is diversified across independent identity/provenance
  components, rather than multiplied by an OOD score or absorbed into a weak
  target surrogate.
- **Archetype:** schematic-led composite.
- **Target/output:** double-column journal figure, Python/matplotlib, 183 mm
  wide, editable SVG and PDF plus 600 dpi TIFF and PNG preview.
- **Panel a:** credibility, complementarity, family-first allocation, and
  abstention/fallback workflow.
- **Panel b:** complete external-pool distinct-group AUC20 for target-only,
  wrong-source, individual-neighbor, entity-consensus, and family-first
  policies; conditional shuffled-source interval shown explicitly.
- **Panel c:** the same endpoint in the hard-OOD pool.
- **Panel d:** breadth-versus-repeat tradeoff, showing distinct-group recall20
  and entity recall20 for entity consensus and family-first consensus in both
  scopes.
- **Hero evidence:** family-first consensus recovers all four top external
  groups by acquisition 20 (AUC20 60) and both hard-OOD groups in the first two
  acquisitions (AUC20 39).
- **Controls:** wrong-domain consensus, composition novelty, uniform order, and
  5,000 independently shuffled source-rank pairs.
- **Statistics:** the shuffled interval and p-value are conditional on the
  fixed candidate pool; deterministic policies have no dataset-level interval.
- **Source data:** `family_first_neighbor_portfolio_metrics.csv` and
  `family_first_neighbor_portfolio_summary.json`.
- **Reviewer risks:** outcome-informed method selection; connected components
  are identity/provenance components, not guaranteed mechanistic families;
  family-first breadth reduces repeated entity-level top-hit recovery; the
  analysis is not prospective confirmation.

