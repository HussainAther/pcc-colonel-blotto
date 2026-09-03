# Changelog

## 1.1.0 - Control as context-dependent modulation

- Reframed the v1.0 Control non-orthogonality result as a prospective interaction test rather than forcing a third PCA axis.
- Added two new exogenous held-out opponent contexts and evaluated four contexts total.
- Measured PCC signatures and prediction outcomes on disjoint seed sets.
- Added leave-one-agent-out ridge comparison between an additive `P + C + H + context` model and a `Control x context` interaction model.
- Frozen result: standardized LOAO MAE falls from **0.3265** to **0.2774**, a **15.04%** improvement versus the prespecified >=5% threshold.
- All four behavioral targets improve; the largest gain is leverage targeting (**28.78%**), while viable-response count changes only **0.46%**.
- Both prespecified checks PASS. This supports a predictive modulatory role for Control in this learned-agent population, not a human or universal causal claim.
- Added protocol, CLI command, validation output, and regression tests.

## 0.9.0 - Pressure-Control boundary falsification

- Restricted latent mixtures to the exact Pressure-Control edge with Chaos fixed at zero.
- Trained only on central edge mixtures (`P` in `[0.20, 0.80]`) and evaluated OOD on the extreme P/C endpoints.
- Explicitly removed entropy, distinct-action ratio, repeat rate, step-to-step volatility, and per-battlefield variance from the predictor set.
- Frozen default result: OOD Pressure MAE **0.0493** vs edge-midpoint baseline **0.4250** (**88.4%** improvement), with true-vs-predicted Pressure correlation **0.9915**.
- All four prespecified checks PASS. Pure Pressure remains the hardest endpoint, averaging about **0.888** predicted Pressure across replicates.
- Added protocol, CLI command, frozen validation output, and three tests; full suite now contains 33 tests.
- Claim remains synthetic separability of engineered Pressure and Control, not spontaneous PCC organization in learned or human agents.

## 0.8.0 - Observational latent-mixture OOD recovery

- Added `MixedPCCAgent`, which generates behavior from fixed hidden Pressure/Control/Chaos mixture weights while withholding component selections from recovery.
- Added a deterministic 0.1 simplex benchmark with 48 blended training mixtures and 18 axis-dominant OOD mixtures.
- Added 24 trajectory-level observable features with latent weights, component labels, policy internals, RNG seeds, and opponent-family labels explicitly forbidden.
- Added dependency-free standardized ridge recovery with simplex projection.
- Frozen default result across 192 training and 72 OOD trajectories: overall OOD MAE **0.0409** vs centroid baseline **0.3556** (**88.5%** improvement).
- Per-axis OOD MAE: Pressure **0.0382**, Control **0.0532**, Chaos **0.0312**; all prespecified checks PASS.
- Added protocol, CLI command, frozen validation output, and four tests; full suite now contains 30 tests.
- Claim remains synthetic observational recovery of an engineered mixture, not recovery from human or naturally learned behavior.

## 0.7.0 - Guarded-Chaos exploiter falsification

- Added an unconstrained Uniform Random baseline to separate raw entropy from strategic adequacy.
- Added a held-out `MeanProfileExploiter` that learns recent allocation tendencies and computes exact best responses.
- Prespecified a three-part success rule: >=80% of random entropy, >=0.05 payoff advantage over random versus the exploiter, and exploit penalty no worse than the predictable baseline.
- Frozen 24-seed result: Guarded Chaos retains 93.1% of random entropy and beats Uniform Random by +0.2943 payoff against the exploiter.
- Exploit penalty is 0.0249 for Guarded Chaos versus 0.3495 for the predictable baseline.
- All three primary checks PASS; interpretation remains mechanism-level and does not equate entropy alone with Chaos.
- Added protocol, CLI command, frozen validation output, and three tests; full suite now contains 26 tests.

## 0.6.0 - Targeted-leverage Pressure intervention

- Added a prospective matched intervention separating raw concentration from value-targeted commitment.
- Matched exact troop budget, expected strategic value (<=0.01 gap), and concentration (<=0.05 gap).
- Added leverage-targeting metric, CLI command, protocol, frozen validation output, and tests.
- Frozen result: 50 matched pairs; leverage 0.3450 -> 0.6430 at identical mean concentration 0.5020; viable responses 741.02 -> 385.24 (48.01% reduction).
- Prespecified >=10% response-constriction criterion: PASS.
- Interpretation remains mechanism-level: value-targeted commitment is a candidate Blotto Pressure mechanism.

## 0.5.0 - Pressure matched-concentration intervention

- Added a deterministic matched causal probe of raw allocation concentration.
- Held the 10-troop budget exactly fixed and matched low- vs high-concentration allocations on expected payoff against a frozen independent opponent distribution (tolerance <=0.01).
- Counted opponent viable pure responses exactly over all 1,001 legal allocations.
- Froze 310 matched pairs: concentration rises 0.3732 -> 0.5555 while viable responses rise 458.48 -> 516.08.
- The prespecified >=5% constriction prediction **fails**; observed relative constriction is **-12.56%**.
- Raw concentration is therefore not promoted as the Pressure mechanism; value-weighted targeting/leverage remains a separate hypothesis.
- Added the `pressure-matched-intervention` CLI command and three tests, bringing the suite to 19 tests.

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

## 1.0.0

- Added independently optimized learned Blotto policies with no latent PCC weights or PCC component supervision.
- Added four generic training objectives across three opponent curricula (12 frozen learned policies total).
- Added held-out evaluation against `MeanProfileExploiter` and an exogenous alternating-regime opponent.
- Added unsupervised PCA over held-out behavioral observables and independent mechanism-facing Pressure/Control/Chaos signatures.
- Added split-half signature stability analysis and frozen v1.0 emergence protocol.
- Frozen result: first three PCs explain 92.1% of behavior variance; Pressure aligns with PC1 (r=0.949) and Chaos with PC2 (r=0.925), while the prespecified distinct-PC Control criterion fails (forced PC3 r=0.059). All three signatures are highly split-half stable (~0.996-0.998).
- Strong three-independent-axis emergence claim is therefore **not supported**; stable low-dimensional PCC-related organization without independent Control is supported as the narrower result.
