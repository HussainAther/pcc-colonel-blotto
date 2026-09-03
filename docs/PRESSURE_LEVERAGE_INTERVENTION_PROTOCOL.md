# v0.6 Targeted-Leverage Pressure Intervention Protocol

## Question

After v0.5 falsified raw concentration as a sufficient Pressure mechanism, does **value-targeted commitment** causally reduce the opponent's viable-response set when troop budget, expected strategic value, and raw concentration are held approximately matched?

## Frozen design

- Game: 10 troops, five battlefields valued `(1.0, 1.5, 2.0, 2.5, 3.0)`.
- Universe: all 1,001 legal pure allocations.
- Strategic-value reference: the same frozen `StaticWeightedOpponent` trace and seed used in v0.5.
- Leverage targeting: troop-weighted normalized battlefield value, mapping the lowest-value battlefield to 0 and highest-value battlefield to 1.
- Low leverage: score `<= 0.40`.
- High leverage: score `>= 0.60`.
- Exact budget: both allocations spend all 10 troops.
- Expected-payoff matching: absolute gap `<= 0.01`.
- Concentration matching: absolute `max(allocation)/10` gap `<= 0.05`.
- Matching: deterministic, without replacement; nearest expected payoff, then nearest concentration.
- Outcome: exact number of opponent pure allocations with payoff `>= 0`, enumerated over all 1,001 responses.

## Prospective primary prediction

High-leverage targeting will reduce the mean opponent viable-response count by **at least 10%** relative to matched low-leverage targeting.

## Interpretation

A pass promotes value-targeted commitment as a candidate Blotto Pressure mechanism, conditional on this environment. A fail means the earlier engineered Pressure effect requires a different or richer notion of leverage. Neither outcome is observational construct recovery.
