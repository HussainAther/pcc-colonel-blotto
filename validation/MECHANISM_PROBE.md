# PCC Colonel Blotto v0.1 Mechanism Probe

This is a synthetic engineering probe, **not** a frozen construct-recovery claim.

## Prespecified checks

- **pressure_more_concentrated_than_baseline**: PASS
- **pressure_constricts_viable_responses**: PASS
- **chaos_more_allocation_entropy_than_baseline**: PASS
- **chaos_value_guardrail_vs_baseline**: PASS
- **control_beats_baseline_vs_adaptive**: PASS

## Match summaries

| agent | opponent | payoff | win rate | entropy | concentration | viable responses |
|---|---|---:|---:|---:|---:|---:|
| baseline | static_weighted | 0.0024 | 0.339 | 0.839 | 0.302 | 223.4 |
| baseline | adaptive_counter | -0.1916 | 0.006 | 0.839 | 0.302 | 223.4 |
| pressure | static_weighted | 0.1522 | 0.884 | 0.000 | 0.400 | 193.0 |
| pressure | adaptive_counter | 0.0008 | 0.004 | 0.000 | 0.400 | 193.0 |
| control | static_weighted | 0.2018 | 0.938 | 1.696 | 0.359 | 216.2 |
| control | adaptive_counter | 0.0115 | 0.464 | 2.312 | 0.349 | 273.0 |
| chaos | static_weighted | 0.1160 | 0.736 | 4.695 | 0.422 | 344.4 |
| chaos | adaptive_counter | 0.0527 | 0.593 | 4.842 | 0.445 | 387.2 |
