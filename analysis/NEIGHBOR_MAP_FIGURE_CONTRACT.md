# Neighbor-map exploration figure contract

## Core conclusion

Qualified neighboring sources need not improve the target model to remain useful for OOD exploration. On the Caltech ionic-conductivity benchmark, adaptive residual injection is null, but prespecified neighboring-source rankings retain proposal signal; preserving source complementarity and allocating proposals family-first increases distinct-region recovery.

## Figure architecture

- **Panel a — operational map.** Qualification, source diversity, continuous borrowing, family-first allocation, and abstention are shown as separate decisions.
- **Panel b — qualification is not source skill alone.** Mean admission and weight across the two candidate scopes are shown beside source out-of-fold skill.
- **Panel c — predictive conversion boundary.** AUC20 increments from adaptive residual policies are plotted with frozen confidence intervals; none passes all frozen gates.
- **Panel d — exploration utility.** Static source rankings are compared across the complete external and hard-OOD pools; labels report recovered top-5% entities.
- **Panel e — complementary family-first allocation.** Distinct-group AUC20 compares a wrong-source consensus, entity consensus, and family-first consensus. Conditional randomization p-values are attached only to the family-first result.

## Evidence status

Panels b–d use the prespecified retrospective Caltech benchmark. Panel e is outcome-informed method development on the same target and is not an independent confirmation. The figure supports an edge-selective knowledge-borrowing map; it does not establish a universal transfer policy or prospective laboratory discovery.

## Source data

- `analysis/results/figure_neighbor_map_panel_a.csv`
- `analysis/results/figure_neighbor_map_panel_b.csv`
- `analysis/results/figure_neighbor_map_panel_c.csv`
- `analysis/results/figure_neighbor_map_panel_d.csv`
- `analysis/results/figure_neighbor_map_panel_e.csv`

## Output files

- `analysis/figures/neighbor_map_exploration.svg`
- `analysis/figures/neighbor_map_exploration.pdf`
- `analysis/figures/neighbor_map_exploration.png`
- `analysis/figures/neighbor_map_exploration.tiff`
