# v0.9 Pressure-Control Boundary Falsification Protocol

## Question

Can observable Blotto behavior distinguish hidden Pressure from hidden Control when Chaos is removed as a source of broad entropy differences?

## Frozen latent family

- Latent mixtures lie exactly on the `Pressure <-> Control` simplex edge.
- Chaos weight is exactly `0.0` for every trajectory.
- Pressure is swept from `0.00` to `1.00` in increments of `0.05`; Control is `1 - Pressure`.

## OOD split

- Training mixtures: Pressure in `[0.20, 0.80]`.
- OOD mixtures: Pressure `< 0.20` or `> 0.80`.
- Default trajectory length: 240 rounds.
- Default replicates: 6 per mixture.

## Predictor guardrail

The recovery model is not allowed to use latent weights, component-selection labels, seeds, opponent-family labels, or policy internals.

To remove the easiest Chaos/randomness shortcuts, it also excludes:

- allocation entropy;
- distinct-action ratio;
- repeat rate;
- mean step-to-step L1 change;
- per-battlefield allocation variance.

Allowed observables are payoff/win rate, allocation concentration, leverage targeting, exact viable-response count, per-battlefield mean allocation, and per-battlefield mean absolute gap to the public opponent allocation.

## Recovery model

Fit a standardized ridge regression on training trajectories to recover Pressure. Clip predictions to `[0,1]`; infer Control as `1 - Pressure` and Chaos as `0`.

## Prespecified success rule

All must pass:

1. OOD Pressure MAE <= 0.15.
2. At least 50% MAE improvement over an edge-midpoint (`Pressure=Control=0.5`) predictor.
3. Pearson correlation between true and predicted OOD Pressure >= 0.90.
4. Chaos is exactly zero throughout the entire generated edge.

No thresholds are changed after observing the result.

## Claim boundary

A pass supports synthetic separability of the engineered Pressure and Control mechanisms in Blotto under a low-Chaos boundary stress test. It does not establish spontaneous PCC axes in independently learned or human agents.
