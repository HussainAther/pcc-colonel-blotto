# PCC Colonel Blotto

A repeated weighted Colonel Blotto environment for testing Pressure-Control-Chaos (PCC) hypotheses in a **resource-allocation** game.

This project is intentionally separate from Poker, Liar's Dice, RPS, and Micro-Fighter. Its purpose is to ask whether the structural PCC motifs survive when strategy is expressed as simultaneous allocation of a scarce budget across competing fronts.

## Game

- 10 troops
- 5 battlefields
- values `[1.0, 1.5, 2.0, 2.5, 3.0]`
- simultaneous allocation
- repeated rounds with public history

## PCC hypotheses

- **Pressure:** commitment concentration -> response constriction -> strategic consequence
- **Control:** information uptake -> context alignment -> value-sensitive reallocation
- **Chaos:** allocation unpredictability + independent value guardrail

These are hypotheses, not conclusions.

## Install and test

```bash
python -m pip install -e ".[dev]"
pytest -q
```

## Run the v0.1 mechanism probe

```bash
pcc-blotto mechanism-probe --output-dir validation
# or
python -m pcc_colonel_blotto mechanism-probe --output-dir validation
```

The probe compares Baseline, Pressure, Control, and Chaos policies against a static weighted opponent and an adaptive counter-opponent. See `docs/INITIAL_PROTOCOL.md`.

## Claim discipline

v0.1 is an engineering/mechanism probe only. It does **not** claim construct recovery, universal PCC topology, or human behavioral validity.

## v0.2 Control history-destruction falsification

The first follow-up falsification asks whether the Control policy's advantage depends on **ordered/recency-sensitive opponent history** or mostly on marginal allocation statistics. A paired replay gives Baseline, shuffled-history Control, and true-history Control the exact same realized opponent allocation sequence.

Default 32-seed result:

- Baseline mean payoff: **-0.1900**
- Shuffled-history Control: **+0.1923**
- True-history Control: **+0.2250**
- Control gain eliminated by shuffling: **7.9%**
- Prespecified 50% collapse criterion: **FAIL**

Interpretation: the current Control implementation is genuinely history-responsive, but most of its advantage in this environment is carried by **distributional opponent statistics rather than temporal order/recency**. We therefore do **not** claim a sequential-Control mechanism from this result.

Run it with:

```bash
python -m pcc_colonel_blotto control-history-destruction --output-dir validation
```

See `docs/CONTROL_HISTORY_DESTRUCTION_PROTOCOL.md` and `validation/CONTROL_HISTORY_DESTRUCTION.md`.


## v0.3 Control under regime switching

The second Control falsification deliberately makes the opponent nonstationary. Three exogenous allocation regimes emphasize different battlefield subsets, and the exact realized trace is replayed to Baseline, shuffled-history Control, and true-history Control.

The strong prospective question is whether temporal-order destruction now removes at least **50%** of Control's gain over Baseline. A 16-round post-switch window is also prespecified to test local adaptation.

Run it with:

```bash
python -m pcc_colonel_blotto control-regime-switching \
  --output-dir validation \
  --rounds 300 \
  --seeds 32 \
  --adaptation-window 16
```

See `docs/CONTROL_REGIME_SWITCHING_PROTOCOL.md` and `validation/CONTROL_REGIME_SWITCHING.md`.

Default 32-seed result:

- Baseline mean payoff: **0.1892**
- Shuffled-history Control: **0.3068**
- True-history Control: **0.2844**
- Fraction of true-Control gain eliminated by shuffling: **-23.5%**
- Prespecified >=50% collapse criterion: **FAIL**
- Prespecified 16-round post-switch true-vs-shuffled difference: **+0.0095**

The strong recency hypothesis therefore fails. Shuffling history improves overall payoff, and the small 16-round true-history edge is not robust to descriptive 4/8/32-round window checks. The current Control rule is history-sensitive but not reliably recency-optimal under this regime-switching design.

## v0.4 Control estimator ablation

v0.4 stops changing the environment and makes the **opponent-history estimator** the experimental object. The same frozen three-regime replay is evaluated with Full-history, Sliding-window (8 rounds), Exponential-decay (`alpha=0.35`), and Change-point-aware Control.

Run it with:

```bash
python -m pcc_colonel_blotto control-estimator-ablation \
  --output-dir validation \
  --rounds 300 \
  --seeds 32 \
  --adaptation-window 16
```

Default 32-seed result:

- Baseline: **0.1887** overall / **0.3293** post-switch
- Full-history Control: **0.2496** / **0.3105**
- Sliding-window Control: **0.2843** / **0.3246**
- Exponential-decay Control: **0.1653** / **0.2804**
- Change-point Control: **0.1683** / **0.3021**
- Primary success rule: **FAIL**

Sliding-window Control is the strongest Control estimator overall and improves the 16-round post-switch payoff over Full-history Control by **0.0141**, but this does not reach the prespecified **0.02** margin. Exponential-decay and Change-point Control do not justify promotion under the frozen design.

An important bookkeeping correction is now explicit: the v0.3 `ControlAgent` itself used an 8-round lookback, so it corresponds most closely to the v0.4 Sliding-window estimator rather than Full-history Control.

See `docs/CONTROL_ESTIMATOR_ABLATION_PROTOCOL.md` and `validation/CONTROL_ESTIMATOR_ABLATION.md`.

## v0.5 Pressure matched-concentration intervention

v0.5 moves from engineered-policy comparison to a matched causal probe of **raw allocation concentration**. Every legal allocation spends the same 10-troop budget. Low-concentration and high-concentration allocations are matched without replacement on expected payoff against one frozen, policy-independent reference opponent distribution (absolute expected-payoff gap <= 0.01), then the opponent's viable pure-response count is computed exactly over all 1,001 legal responses.

Run it with:

```bash
python -m pcc_colonel_blotto pressure-matched-intervention --output-dir validation
```

Frozen result:

- matched pairs: **310**
- mean strategic-value gap: **0.00429**
- mean concentration: **0.3732 -> 0.5555**
- mean viable responses: **458.48 -> 516.08**
- relative viable-response reduction: **-12.56%**
- prespecified >=5% constriction criterion: **FAIL**

The direction reverses the raw-concentration prediction: when strategic value is approximately matched, higher concentration leaves the opponent with **more**, not fewer, non-losing pure responses on average. Therefore raw concentration alone is not promoted as the Blotto Pressure mechanism. The earlier engineered `PressureAgent` result may depend on *where* resources are concentrated (battlefield value/leverage), not merely how concentrated the allocation is.

See `docs/PRESSURE_MATCHED_INTERVENTION_PROTOCOL.md` and `validation/PRESSURE_MATCHED_INTERVENTION.md`.

## v0.6 Targeted-leverage Pressure intervention

v0.6 follows the v0.5 failure by separating **raw concentration** from **where concentrated commitment is targeted**. Low- and high-leverage allocations are matched on exact troop budget, expected strategic value (`<= 0.01` gap), and raw concentration (`<= 0.05` gap). The manipulation is troop-weighted targeting toward higher-value battlefields.

Run it with:

```bash
python -m pcc_colonel_blotto pressure-leverage-intervention --output-dir validation
```

Frozen result:

- matched pairs: **50**
- mean leverage targeting: **0.3450 -> 0.6430**
- mean concentration: **0.5020 -> 0.5020**
- mean viable responses: **741.02 -> 385.24**
- relative viable-response reduction: **48.01%**
- prespecified `>=10%` constriction criterion: **PASS**

This sharply distinguishes v0.6 from v0.5: concentration alone increased viable responses, whereas **value-targeted commitment at matched concentration and strategic value strongly constricts the response set**. This promotes value-targeted commitment as a candidate Blotto Pressure mechanism, not yet as a substrate-general construct claim.

See `docs/PRESSURE_LEVERAGE_INTERVENTION_PROTOCOL.md` and `validation/PRESSURE_LEVERAGE_INTERVENTION.md`.

## v0.7 Guarded-Chaos exploiter falsification

v0.7 separates **raw unpredictability** from **strategically adequate unpredictability**. It compares the low-entropy Value Baseline, unconstrained Uniform Random allocation, and the existing guarded `ChaosAgent` against both the frozen static opponent and a held-out online `MeanProfileExploiter` that predicts recent allocation tendencies and computes an exact best response.

Run it with:

```bash
python -m pcc_colonel_blotto chaos-exploiter-falsification \
  --output-dir validation \
  --rounds 200 \
  --seeds 24
```

Frozen result against the held-out exploiter:

- Value Baseline: payoff **-0.3485**, entropy **0.8272**
- Uniform Random: payoff **-0.2098**, entropy **5.1656**
- Guarded Chaos: payoff **+0.0844**, entropy **4.8098**
- Guarded-Chaos entropy / Uniform-Random entropy: **93.1%**
- Guarded-Chaos payoff advantage over Uniform Random: **+0.2943**
- Exploit penalty: Baseline **0.3495**, Uniform Random **-0.0145**, Guarded Chaos **0.0249**
- Prespecified three-part primary rule: **PASS**

The important distinction is that Uniform Random is extremely unpredictable but strategically poor, while Guarded Chaos preserves nearly the same empirical action entropy and remains value-positive against the learner. This supports **unpredictability constrained by strategic adequacy** as the candidate Blotto Chaos mechanism; it does not identify entropy alone with Chaos or establish observational construct recovery.

See `docs/CHAOS_EXPLOITER_PROTOCOL.md` and `validation/CHAOS_EXPLOITER_FALSIFICATION.md`.

## v0.8 Observational PCC recovery

v0.8 connects the Blotto mechanism program back to the central PCC recovery question. Hidden Pressure/Control/Chaos weights generate repeated-game behavior, while the recovery model receives only trajectory-level behavioral observables. Component choices, latent weights, seeds, opponent-family labels, and policy internals are forbidden predictors.

The frozen OOD split uses the 0.1 simplex lattice: blended mixtures with every axis `< 0.75` are training data, while axis-dominant mixtures with `max(weight) >= 0.75` are held out entirely.

Run it with:

```bash
python -m pcc_colonel_blotto observational-recovery \
  --output-dir validation \
  --rounds 240 \
  --seeds-per-mixture 4
```

Frozen result:

- training mixtures: **48** / OOD mixtures: **18**
- trajectories: **192 train / 72 OOD**
- OOD overall MAE: **0.0409**
- centroid-baseline MAE: **0.3556**
- relative improvement over centroid: **88.5%**
- Pressure MAE: **0.0382**
- Control MAE: **0.0532**
- Chaos MAE: **0.0312**
- all three prespecified recovery checks: **PASS**

This supports synthetic observational recoverability of the engineered latent PCC mixture under a genuinely held-out axis-dominant weight region. It does **not** establish recovery from human Blotto play, nor does it prove that learned/natural agents spontaneously factor into PCC components.

See `docs/OBSERVATIONAL_RECOVERY_PROTOCOL.md` and `validation/OBSERVATIONAL_RECOVERY.md`.
