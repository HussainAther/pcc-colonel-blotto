# Prospective Protocol: Matched Pressure Concentration Intervention

## Question

Holding troop budget exactly fixed and expected strategic value approximately matched, does increasing allocation concentration causally reduce the opponent's viable pure-response set?

## Frozen game

- 10 troops
- 5 battlefields
- values `(1.0, 1.5, 2.0, 2.5, 3.0)`
- all 1,001 legal pure allocations are eligible

## Strategic-value matching

Strategic value is the allocation's mean payoff against 2,048 actions sampled from `StaticWeightedOpponent` with frozen seed `20260903`. This reference distribution is generated independently of every evaluated allocation.

Low-concentration candidates have maximum troop share `<= 0.40`. High-concentration candidates have maximum troop share `>= 0.50`. High allocations are traversed in expected-value order and greedily matched without replacement to the remaining low allocation with the nearest expected payoff, provided the absolute expected-payoff gap is `<= 0.01`.

The troop budget is therefore identical by construction; the expected strategic-value tolerance is fixed before evaluating response constriction.

## Outcome

For each matched allocation, count exactly how many of all 1,001 opponent pure allocations achieve payoff `>= 0` against it. Fewer such allocations means stronger response constriction.

## Primary prediction

High-concentration allocations will reduce the mean opponent viable-response count by at least **5%** relative to their value-matched low-concentration partners.

## Guardrail

This is a causal probe of **raw concentration**, not a test of every aspect of the engineered Pressure agent. Failure means concentration alone is insufficient evidence for the Pressure mechanism; it does not invalidate battlefield targeting, leverage, or other Pressure components.
