# PCC Colonel Blotto v0.8 Observational OOD Recovery Protocol

## Question

Can hidden engineered Pressure/Control/Chaos mixture weights be recovered from observable repeated-Blotto behavior when evaluation mixtures lie outside the latent-weight region used for training?

## Latent generator

Each trajectory has fixed hidden weights `(P, C, H)` summing to one. On each decision, those weights stochastically select the already-frozen Pressure, sliding-window Control, or guarded-Chaos policy. Component identity is never recorded as a predictor.

## Observable features

Recovery receives trajectory aggregates only: payoff/win rate, allocation entropy/diversity, concentration, leverage targeting, exact viable-response counts, temporal allocation change/repetition, battlefield troop means/variances, and public same-round allocation gaps.

Forbidden predictors include latent weights, component-selection labels, policy internals, RNG seeds, and opponent-family labels.

## Frozen OOD split

Use the 0.1 simplex lattice. Train only where every latent weight is `< 0.75`. Hold out every axis-dominant point where `max(weight) >= 0.75`.

Default generation uses 240 rounds and four independent trajectories per mixture. Opponent families vary across trajectories but their identities are hidden from the recovery model.

## Recovery model

Fit one standardized ridge regression per latent axis on training trajectories only (`lambda = 0.25`), then project the three raw predictions onto the probability simplex.

## Prespecified success rule

All must pass:

1. OOD overall component-wise MAE `<= 0.15`.
2. OOD overall MAE improves by at least 25% over always predicting `(1/3, 1/3, 1/3)`.
3. Every individual PCC axis beats its corresponding centroid-baseline MAE.

No thresholds or split rules are to be modified after viewing v0.8 results.

## Claim boundary

A passing result supports synthetic observational recovery of hidden engineered PCC mixtures under this Blotto substrate. It does not establish recovery from human behavior, uniqueness of the PCC decomposition, or cross-game invariance by itself.
