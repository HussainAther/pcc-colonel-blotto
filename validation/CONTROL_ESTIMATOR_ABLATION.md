# Control Estimator Ablation

This v0.4 experiment holds the regime-switching environment fixed and makes the **history estimator itself** the experimental object.

## Prespecified success rule

At least one explicitly recency-aware estimator must improve 16-round post-switch payoff over full-history Control by **>=0.02**, while losing no more than **0.02** in overall mean payoff.

| policy | mean payoff | post-switch payoff | prediction L1 | win rate |
|---|---:|---:|---:|---:|
| Baseline | 0.1887 | 0.3293 | - | 0.659 |
| Full-history Control | 0.2496 | 0.3105 | 0.5167 | 0.791 |
| Sliding-window Control | 0.2843 | 0.3246 | 0.1630 | 0.864 |
| Exponential-decay Control | 0.1653 | 0.2804 | 0.1524 | 0.679 |
| Change-point Control | 0.1683 | 0.3021 | 0.1628 | 0.664 |

Best recency estimator post-switch: **control_sliding_window**

Best recency estimator overall: **control_sliding_window**

Qualifying estimators: **none**

## Prespecified checks

- **at_least_one_recency_estimator_improves_post_switch_without_material_overall_loss**: FAIL
- **best_recency_estimator_beats_full_history_post_switch**: PASS

## Interpretation guardrail

This experiment identifies whether recency-aware belief estimation improves engineered Control under fixed nonstationarity. It does not establish that the selected estimator is universally optimal or that observational PCC recovery has been achieved.
