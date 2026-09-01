# PCC Colonel Blotto v0.1 Initial Protocol

## Scientific role

Repeated weighted Colonel Blotto is introduced as a **resource-allocation substrate**, not as another bluffing or card-game replication.

The initial structural mappings are hypotheses:

- **Pressure:** commitment concentration -> fewer viable opponent allocations -> downstream value consequence.
- **Control:** opponent-history uptake -> battlefield-specific alignment -> value-sensitive reallocation.
- **Chaos:** allocation unpredictability under an independent payoff/value guardrail.

These mappings are not treated as validated constructs in v0.1.

## Environment

- 10 indivisible troops.
- 5 simultaneous battlefields.
- Battlefield values: `[1.0, 1.5, 2.0, 2.5, 3.0]`.
- Each player must allocate all 10 troops every round.
- Higher allocation wins a battlefield; ties split neither way in the zero-sum payoff.
- Repeated play exposes prior allocations after each round.

## Engineered policies

- **Baseline:** approximately value-proportional allocation with small jitter.
- **Pressure:** deliberately concentrates commitment on high-value fronts.
- **Control:** uses recent opponent allocation history to seek low-cost value-sensitive overmatches.
- **Chaos:** randomizes among sampled allocations satisfying a local payoff guardrail.

## Opponent families

1. **Static weighted:** value-sensitive but history-free.
2. **Adaptive counter:** reallocates toward battlefields the focal agent has recently emphasized.

## v0.1 prespecified checks

1. Pressure has greater allocation concentration than Baseline.
2. Pressure leaves fewer non-losing pure responses available to the opponent than Baseline.
3. Chaos has greater allocation entropy than Baseline.
4. Chaos preserves a payoff guardrail: it does not underperform Baseline in either opponent family.
5. Control has higher mean payoff than Baseline against the adaptive-counter opponent.

Failure is retained. Passing these checks establishes only that the engineered policies express the intended local mechanisms; it does **not** establish observational construct recovery or a universal PCC score.

## Next falsification steps

1. Pressure matched-allocation intervention: hold total commitment and battlefield values fixed while moving concentration across fronts; test viable-response constriction.
2. Control history destruction: shuffle opponent history while preserving marginal allocation frequencies; test whether Control's adaptive advantage collapses.
3. Chaos exploitation test: compare high-entropy random play against guarded Chaos using held-out exploiters.
4. Cross-family construct recovery only after the above mechanism tests survive.
