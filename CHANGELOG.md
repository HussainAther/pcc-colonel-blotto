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
