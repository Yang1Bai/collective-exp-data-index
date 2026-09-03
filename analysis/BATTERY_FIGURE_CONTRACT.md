# Battery continuous-borrowing figure contract

## Core conclusion

In the outcome-unseen temporal battery programme, a continuous upstream Stage 1 prediction improves Stage 2 condition-level RMSE relative to target-only and matched false-source controls across most evaluable condition groups. A hard qualification gate over-abstains. The favorable continuous policy is an outcome-guided nomination for independent testing, not a confirmatory result.

## Figure architecture

- **Panel a — protected temporal design and coverage boundary.** Stage 1 information is frozen before Stage 2 outcomes. Of 138 released Stage 2 cells, 135 endpoints in 22 condition groups are evaluable; one z10 condition group lacks all three AT_T23 endpoints, so the frozen 23-group primary is non-evaluable.
- **Panel b — controlled continuous-borrowing contrasts.** Equal-stratum relative condition-RMSE gains compare the adjacent-source feature with target-only, wrong-property, shuffled-source, and random-feature controls. Intervals and Holm-adjusted p-values are post-hoc/outcome-guided.
- **Panel c — condition-level selectivity.** Each point is a held-out condition group; outlined symbols denote type-specific upper-quartile source distance. Positive values favor borrowing.
- **Panel d — hard-gate coverage.** Training-only CCA-v2 admits four of 22 groups, all calendar groups, and falls back for every cycle group.
- **Panel e — source-inspired hypothesis cards.** The two prewritten lead-versus-control contrasts pass in the predicted direction; lower retention is favorable.

## Evidence status

The original outcome-unseen design is protected, but its frozen primary test is non-evaluable because of endpoint coverage. Panels b–e are post-release method-development analyses on the 22 complete groups. They nominate continuous adjacent-source prediction for a new outcome-unseen benchmark and cannot establish prospective discovery or experiments saved.

## Source data

- `analysis/results/figure_battery_panel_a.csv`
- `analysis/results/figure_battery_panel_b.csv`
- `analysis/results/figure_battery_panel_c.csv`
- `analysis/results/figure_battery_panel_d.csv`
- `analysis/results/figure_battery_panel_e.csv`

## Output files

- `analysis/figures/battery_continuous_borrowing.svg`
- `analysis/figures/battery_continuous_borrowing.pdf`
- `analysis/figures/battery_continuous_borrowing.png`
- `analysis/figures/battery_continuous_borrowing.tiff`
