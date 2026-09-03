# v1.1 Prospective Protocol — Control as Context-Dependent Modulation

## Question

In independently optimized Blotto agents with no latent PCC generator, does Control improve prediction primarily through **context-dependent interactions** rather than as a standalone additive axis?

## Frozen design

- Recreate the v1.0 population of 12 independently optimized agents under generic objectives/curricula.
- Evaluate frozen agents in four contexts: mean-profile exploiter, alternating weighted, front-loaded, and back-loaded held-out opponents.
- Measure PCC behavioral signatures on one seed set and outcome behaviors on a completely disjoint seed set.
- Predict four context-specific outcomes: mean payoff, leverage targeting, opponent viable-response count, and lagged counter-payoff.
- Use leave-one-agent-out cross-validation.
- Compare:
  - additive: `Pressure + Control + Chaos + context`
  - modulatory: additive model + `Control × context`
- Ridge regularization is fixed at 1.0.

## Prespecified success rule

The modulatory interpretation requires both:

1. at least **5% lower** aggregate standardized LOAO MAE than the additive model; and
2. improvement on at least **2 of 4** behavioral targets.

No thresholds will be changed after observing the result.

## Guardrail

A positive result supports a predictive conditional role for Control in this synthetic learned-agent population. It does not show that Control is causal, universally non-orthogonal, or applicable to human behavior.
