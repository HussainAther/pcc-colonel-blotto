# Control Estimator Ablation Protocol (v0.4)

## Question

Which representation of opponent history, if any, produces robust Control under the frozen three-regime nonstationary Blotto replay?

## Frozen environment

Use the same exogenous three-regime trace generator introduced in v0.3. Every policy sees the identical realized opponent allocation sequence for a given seed. No environment parameters are tuned after observing estimator performance.

Default evaluation: 300 rounds, 32 seeds, regime switches at rounds 100 and 200, primary post-switch window of 16 rounds.

## Policies

- Baseline: value-weighted allocation with no opponent-history estimator.
- Full-history Control: mean allocation over all observed prior rounds.
- Sliding-window Control: mean allocation over the last 8 rounds.
- Exponential-decay Control: EWMA of prior allocations, alpha = 0.35.
- Change-point Control: two-window L1 shift detector with window = 8 and threshold = 4 troops; observations before the most recent detected shift are discarded.

The change-point policy uses only observed allocation history; it never receives the true regime label or switch times.

## Primary success rule

At least one explicitly recency-aware estimator (sliding-window, exponential-decay, or change-point) must:

1. improve mean payoff in the prespecified 16-round post-switch windows over Full-history Control by at least **0.02**, and
2. lose no more than **0.02** in overall mean payoff relative to Full-history Control.

This is deliberately stricter than merely ranking first among Control variants.

## Secondary readouts

- overall mean payoff
- win rate
- post-switch payoff at 4, 8, 16, and 32 rounds
- normalized L1 prediction error of the opponent's next allocation

Prediction accuracy is diagnostic, not the primary endpoint: a better predictor need not induce a better strategic response.

## Interpretation guardrail

A failed primary rule means the current evidence does not support a robust recency-aware Control estimator under this replay. It does not invalidate distributional/context-sensitive Control, and parameters must not be retuned on the frozen traces and then reported as prospective evidence.
