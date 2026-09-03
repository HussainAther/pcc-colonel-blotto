## 0.4.0 - Control estimator ablation

- Held the v0.3 three-regime replay fixed and compared Full-history, Sliding-window, Exponential-decay, and Change-point Control estimators.
- Added next-allocation L1 prediction diagnostics and 4/8/16/32-round post-switch windows.
- Prespecified success as >=0.02 post-switch improvement over Full-history Control with no more than 0.02 overall-payoff loss.
- Froze the 32-seed result: Sliding-window Control is best overall (0.2843) and improves 16-round post-switch payoff by 0.0141, but the primary threshold **fails**.
- Exponential-decay and Change-point estimators underperform and are not promoted.
- Clarified that the v0.3 `ControlAgent` was already an 8-round sliding-window policy, not a full-history estimator.
- Added the `control-estimator-ablation` CLI command and four additional tests, bringing the suite to 16 tests.

## 0.3.0 - Control under regime switching

- Added an exogenous three-regime opponent trace to make recent information potentially decision-relevant.
- Added paired Baseline / shuffled-history Control / true-history Control replay under identical nonstationary traces.
- Added a prespecified 16-round post-switch adaptation readout plus descriptive 4/8/32-round sensitivity diagnostics.
- Added the `control-regime-switching` CLI command and three tests.
- Froze the default 32-seed result: shuffled-history Control outperforms true-history Control overall (0.3068 vs 0.2844), so the >=50% recency-collapse prediction fails.
- The prespecified 16-round post-switch true-history edge is small (+0.0095) and not robust across descriptive 4/8/32-round windows.
- Preserves failure results rather than retuning the environment after observation.

## 0.2.0 - Control history-destruction falsification

- Added paired replay evaluation for temporal information use by `ControlAgent`.
- Added `ShuffledHistoryControl`, which preserves the observed-history multiset but destroys order before applying the ordinary Control policy.
- Added `control-history-destruction` CLI command and four tests.
- Froze the default 32-seed result: true Control strongly beats Baseline, shuffling hurts Control slightly, but only **7.9%** of the Control payoff gain is eliminated.
- The prespecified >=50% collapse prediction therefore **fails**. Current evidence supports distributional/contextual adaptation more strongly than temporal-order dependence.

# Changelog

## 0.1.0

- Added repeated weighted Colonel Blotto environment.
- Added Baseline, Pressure, Control, and guarded-Chaos policies.
- Added static-weighted and adaptive-counter opponent families.
- Added initial synthetic mechanism probe and prespecified protocol.
- Added tests and CLI.
