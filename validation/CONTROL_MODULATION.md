# PCC Colonel Blotto v1.1 Control as Context-Dependent Modulation

This experiment asks whether Control is better represented as a conditional modifier of behavior than as a standalone orthogonal component. PCC signatures are measured on seeds disjoint from the outcome trajectories.

## Leave-one-agent-out prediction

- additive standardized MAE: **0.3265**
- Control×context standardized MAE: **0.2774**
- relative improvement: **15.04%**
- targets improved: **mean_payoff, mean_leverage_targeting, mean_opponent_viable_responses, lagged_counter_payoff**

## Per-target relative improvement

- mean_payoff: **+19.38%**
- mean_leverage_targeting: **+28.78%**
- mean_opponent_viable_responses: **+0.46%**
- lagged_counter_payoff: **+15.42%**

## Prespecified checks

- **control_context_interactions_reduce_loao_standardized_mae_by_at_least_5_percent**: PASS
- **control_context_interactions_improve_at_least_two_behavioral_targets**: PASS

## Interpretation guardrail

A pass supports a predictive/modulatory interpretation of Control in this learned-agent population. A failure means the v1.0 entanglement should not be rescued by interaction language without further evidence. This is not a causal human-behavior result.
