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
