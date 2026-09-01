# Control Regime-Switching Falsification

This paired replay experiment asks whether Control uses **recent** opponent information when the allocation process is nonstationary.

The opponent passes through three exogenous regimes that emphasize different battlefield subsets. Every evaluated policy faces the identical realized trace.

## Prespecified predictions

1. Destroying temporal order eliminates at least **50%** of true-history Control's payoff gain over Baseline.
2. True-history Control beats shuffled-history Control in the immediate post-switch adaptation windows.

## Aggregate result

| condition | mean payoff | post-switch payoff | win rate |
|---|---:|---:|---:|
| Baseline | 0.1892 | 0.3298 | 0.662 |
| Shuffled-history Control | 0.3068 | 0.3151 | 0.949 |
| True-history Control | 0.2844 | 0.3246 | 0.864 |

Fraction of Control gain eliminated by shuffling: **-23.5%**

Post-switch true minus shuffled payoff: **0.0095**

## Prespecified checks

- **true_control_beats_baseline**: PASS
- **history_shuffle_hurts_control**: FAIL
- **history_shuffle_eliminates_at_least_half_control_gain**: FAIL
- **true_control_beats_shuffled_in_prespecified_16_round_window**: PASS

## Interpretation guardrail

This test establishes or falsifies recency-sensitive information use for the current Control policy under a deliberately nonstationary environment. It does not by itself establish observational PCC construct recovery.
