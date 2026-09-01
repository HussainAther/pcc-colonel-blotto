# Control History-Destruction Falsification

This is a **paired replay** test of whether Control benefits from temporal/recency information rather than merely from the marginal distribution of opponent allocations.

Every condition faces the exact same opponent allocation sequence. The shuffled condition preserves the complete history multiset at every decision but permutes its order before the ordinary Control policy is evaluated.

## Prespecified prediction

At least **50% of true Control's payoff gain over Baseline** should disappear after history order is destroyed.

## Aggregate result

| condition | mean payoff | win rate |
|---|---:|---:|
| Baseline | -0.1900 | 0.005 |
| Shuffled-history Control | 0.1923 | 0.988 |
| True-history Control | 0.2250 | 0.979 |

True Control gain over Baseline: **0.4150**

Shuffled Control gain over Baseline: **0.3823**

Fraction of Control gain eliminated by shuffling: **7.9%**

## Prespecified checks

- **true_control_beats_baseline**: PASS
- **history_shuffle_hurts_control**: PASS
- **history_shuffle_eliminates_at_least_half_control_gain**: FAIL

## Interpretation guardrail

A failure of the 50% threshold does not invalidate the simulator. It means the current Control policy's advantage is not primarily carried by temporal ordering/recency under this paired replay design, and the Control operationalization should be revised before stronger cross-game claims are made.
