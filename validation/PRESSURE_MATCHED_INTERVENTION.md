# PCC Colonel Blotto v0.5 Pressure Matched Intervention

This experiment holds troop budget exactly fixed and matches low- versus high-concentration allocations on expected strategic value against one frozen, policy-independent opponent distribution.

## Prespecified checks

- **exact_troop_budget_preserved**: PASS
- **strategic_value_matched_within_tolerance**: PASS
- **concentration_manipulation_succeeded**: PASS
- **pressure_constricts_viable_responses_by_at_least_5_percent**: FAIL

## Aggregate result

- Matched pairs: **310**
- Mean absolute strategic-value gap: **0.004287**
- Mean concentration: **0.3732 -> 0.5555**
- Mean viable responses: **458.48 -> 516.08**
- Relative viable-response reduction: **-12.56%**
- Pairwise fraction with fewer viable responses under high concentration: **39.35%**

## Interpretation guardrail

This isolates **raw allocation concentration**, not the full engineered Pressure policy. If the primary prediction fails, concentration by itself should not be treated as a substrate-general Pressure mechanism; battlefield targeting, leverage, or value-weighted commitment may be necessary parts of the construct.
