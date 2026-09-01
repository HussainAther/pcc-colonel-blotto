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
