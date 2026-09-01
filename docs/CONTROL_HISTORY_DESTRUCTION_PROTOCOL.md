# Control History-Destruction Protocol

## Question

Does the current Colonel Blotto Control policy benefit primarily from the temporal ordering/recency of observed opponent allocations, rather than only from their marginal distribution?

## Paired replay design

1. Generate an opponent trace with `AdaptiveCounterOpponent` playing against the reference `ValueBaseline`.
2. Freeze that realized opponent allocation sequence.
3. Replay the exact same sequence to three policies:
   - `ValueBaseline`
   - `ControlAgent` with the true ordered history
   - `ShuffledHistoryControl`, which permutes the complete observed history at each decision before passing it to the ordinary Control policy
4. Use identical trace seeds across all conditions.

The shuffle preserves the complete multiset of opponent allocations available at each decision. It destroys which observations are recent, and therefore destroys temporal order as used by Control's finite lookback window.

## Implementation-level prespecified prediction

At least **50% of true Control's payoff gain over Baseline** should be eliminated after history order is destroyed.

This is intentionally a strong falsification threshold. Failure means the current Control advantage should not be interpreted as primarily sequential/recency-sensitive under this environment.

## Primary estimand

Let

- `G_true = payoff(true Control) - payoff(Baseline)`
- `G_shuffle = payoff(shuffled Control) - payoff(Baseline)`

Then

`fraction eliminated = 1 - G_shuffle / G_true`.

The primary check passes only when `G_true > 0` and `fraction eliminated >= 0.50`.

## Scope guardrail

This experiment tests temporal information use in the current policy/environment pairing. It does not test all possible meanings of PCC Control, and it does not imply that a failure of temporal dependence invalidates distributional/contextual adaptation as a distinct mechanism.
