# PCC Colonel Blotto v0.8 Observational OOD Recovery

Hidden Pressure/Control/Chaos mixture weights generate behavior; the recovery model receives only trajectory-level observables.

## Frozen split

- training mixtures: **48** blended simplex points
- OOD mixtures: **18** axis-dominant points (`max(weight) >= 0.75`)
- trajectories: **192 train / 72 OOD**

## OOD recovery

- overall MAE: **0.0409**
- centroid baseline MAE: **0.3556**
- relative improvement: **88.5%**

| axis | recovery MAE | centroid MAE |
|---|---:|---:|
| Pressure | 0.0382 | 0.3556 |
| Control | 0.0532 | 0.3556 |
| Chaos | 0.0312 | 0.3556 |

## Prespecified checks

- **ood_overall_mae_at_most_0_15**: PASS
- **beats_uniform_centroid_baseline_by_at_least_25_percent**: PASS
- **all_three_axes_beat_centroid_baseline**: PASS

Overall primary rule: **PASS**

## Interpretation guardrail

A pass supports recoverability of hidden engineered PCC mixtures from observable Blotto behavior under this synthetic OOD split. It does not establish recovery from human play or prove that the engineered component policies uniquely instantiate PCC.
