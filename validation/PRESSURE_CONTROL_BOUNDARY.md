# PCC Colonel Blotto v0.9 Pressure-Control Boundary Falsification

Chaos is fixed exactly at zero. Recovery is restricted to the Pressure-Control edge and broad entropy/diversity shortcuts are excluded from the predictor set.

## Frozen design

- edge spacing: **0.05**
- training Pressure range: **[0.20, 0.80]**
- OOD mixtures: **8** extreme edge points
- trajectories: **78 train / 48 OOD**
- Chaos weight: **0.0** everywhere
- entropy/diversity features: **forbidden**

## OOD boundary recovery

- Pressure MAE: **0.0493**
- edge-midpoint baseline MAE: **0.4250**
- relative improvement: **88.4%**
- true-vs-predicted Pressure correlation: **0.9915**

## Prespecified checks

- **ood_pressure_mae_at_most_0_15**: PASS
- **beats_edge_midpoint_baseline_by_at_least_50_percent**: PASS
- **pressure_ordering_correlation_at_least_0_90**: PASS
- **chaos_is_exactly_zero_everywhere**: PASS

Overall primary rule: **PASS**

## Interpretation guardrail

A pass supports separability of engineered Pressure versus Control behavior at the low-Chaos boundary using mechanism-facing public observables rather than broad entropy differences. It does not establish spontaneous PCC organization in independently learned agents.
