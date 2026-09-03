# PCC Colonel Blotto v0.6 Targeted-Leverage Pressure Intervention

This experiment holds troop budget exactly fixed and approximately matches both expected strategic value and raw allocation concentration while manipulating **where troop mass is targeted** across battlefield values.

## Prespecified checks

- **exact_troop_budget_preserved**: PASS
- **strategic_value_matched_within_tolerance**: PASS
- **concentration_matched_within_tolerance**: PASS
- **leverage_targeting_manipulation_succeeded**: PASS
- **targeted_pressure_constricts_viable_responses_by_at_least_10_percent**: PASS

## Aggregate result

- Matched pairs: **50**
- Mean absolute strategic-value gap: **0.004222**
- Mean concentration: **0.5020 -> 0.5020**
- Mean leverage targeting: **0.3450 -> 0.6430**
- Mean viable responses: **741.02 -> 385.24**
- Relative viable-response reduction: **48.01%**
- Pairwise fraction with fewer viable responses under high leverage: **100.00%**

## Interpretation guardrail

A positive result supports **value-targeted commitment** as a candidate Blotto Pressure mechanism after raw concentration failed in v0.5. It does not establish that battlefield value is the only relevant form of leverage, nor that the result generalizes beyond this Blotto parameterization.
