# Model and protocol allowlist

These are the model implementations that support the current manuscript. The
allowlist prevents unrelated exploratory architectures elsewhere in the
repository from being mistaken for article evidence.

| Claim | Frozen or authoritative definition | Model used | Transferred object |
|---|---|---|---|
| Broad scalar screen | [`multi_target_ood_borrowing_design.json`](../../analysis/multi_target_ood_borrowing_design.json) and [`run_multi_target_ood_borrowing.py`](../../analysis/run_multi_target_ood_borrowing.py) | Ridge α=10 primary; Random Forest and Extra Trees sensitivities | One leakage-excluded, cross-fitted donor prediction added as a scalar feature |
| LiAsF6 prediction | [`bamboomixer_response_transfer_design.json`](../../analysis/bamboomixer_response_transfer_design.json) and [`run_bamboomixer_response_transfer_development.py`](../../analysis/run_bamboomixer_response_transfer_development.py) | Three-seed RandomForestRegressor ensemble; fixed chemistry/state representation | Absolute log-conductivity response |
| SolventSeg routing | [`bamboomixer_cross_database_interaction_design.json`](../../analysis/bamboomixer_cross_database_interaction_design.json) and [`run_bamboomixer_cross_database_interaction.py`](../../analysis/run_bamboomixer_cross_database_interaction.py) | Three frozen source forests plus an equal-programme percentile-rank consensus; prespecified target Ridge comparator | Candidate ordering, not numerical scale |
| SolventSeg stress test | [`run_bamboomixer_recipient_baseline_stress_test.py`](../../analysis/run_bamboomixer_recipient_baseline_stress_test.py) | Thirteen target-only configurations including RBF kernel ridge, forests, k-nearest neighbours and a rank ensemble | Baseline-sensitivity check only |
| FINALES boundary | [`finales_rank_replication_design.json`](../../analysis/finales_rank_replication_design.json), [`finales_rank_replication_freeze.json`](../../analysis/finales_rank_replication_freeze.json) and [`run_finales_rank_replication.py`](../../analysis/run_finales_rank_replication.py) | Frozen HistGradientBoosting donor score; Extra Trees, HistGradientBoosting and linear target-only comparators | Temperature-matched candidate ordering |

## Interpretation guard

The broad-screen null is specific to the tested one-scalar protocol. It does
not evaluate or refute all multitask, fine-tuning, graph-neural-network,
pretraining or learned-representation strategies. Likewise, the successful
electrolyte routes do not establish that conductivity is universally
transferable: LiAsF6 qualifies for absolute prediction under aligned support,
SolventSeg qualifies only for ranking, and FINALES is withheld.

## Verification entry points

- [`verify_multi_target_ood_borrowing.py`](../../analysis/verify_multi_target_ood_borrowing.py)
- [`verify_bamboomixer_response_transfer_development.py`](../../analysis/verify_bamboomixer_response_transfer_development.py)
- [`verify_bamboomixer_cross_database_interaction.py`](../../analysis/verify_bamboomixer_cross_database_interaction.py)
- [`verify_bamboomixer_recipient_baseline_stress_test.py`](../../analysis/verify_bamboomixer_recipient_baseline_stress_test.py)
- [`verify_finales_rank_replication.py`](../../analysis/verify_finales_rank_replication.py)

Do not replace a prespecified comparator with the best post-outcome model when
quoting the formal result. The 13-model SolventSeg analysis is deliberately
reported as a separate stress test.
