# Prospective Protocol: Control Under Regime Switching

## Question

Does the current Blotto Control policy use recency-sensitive opponent information when the environment is explicitly nonstationary?

## Design

- Game: 10 troops across 5 weighted battlefields.
- Opponent trace: an exogenous three-regime allocation process.
- Regime 1 emphasizes later/high-value fronts.
- Regime 2 shifts allocation toward early fronts.
- Regime 3 shifts allocation toward middle fronts.
- The realized opponent trace is generated once per seed and replayed identically to every evaluated policy.
- Conditions: Value Baseline, true-history Control, and shuffled-history Control.
- Shuffled-history Control receives the exact same observed allocations but their order is permuted before the ordinary Control rule sees them.
- Default evaluation: 300 rounds, 32 paired seeds.
- Primary adaptation window: 16 rounds after each regime switch.

## Prespecified predictions

1. True-history Control beats Baseline overall.
2. Destroying history order hurts Control overall.
3. At least 50% of true Control's payoff gain over Baseline is eliminated by history shuffling.
4. True-history Control beats shuffled-history Control in the prespecified 16-round post-switch windows.

Prediction 3 is the primary strong recency criterion.

## Diagnostics

Post-switch windows of 4, 8, 16, and 32 rounds are reported as descriptive sensitivity checks. Only the 16-round window is prespecified for the secondary adaptation prediction; the other widths must not be promoted to confirmatory evidence after observing results.

## Claim guardrail

Even a positive result would establish only recency-sensitive information use for this engineered policy under nonstationarity. It would not establish observational PCC construct recovery, universality, or human validity.
