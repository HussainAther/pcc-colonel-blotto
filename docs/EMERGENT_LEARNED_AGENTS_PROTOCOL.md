# PCC Colonel Blotto v1.0 Emergent Learned-Agent Protocol

## Question

Do PCC-like behavioral dimensions appear in independently optimized Blotto agents when **no latent PCC weights or PCC component labels exist in the generator**?

## Agent population

Train 12 independent compact linear allocation policies from distinct random initializations:

- objectives: mean payoff, win rate, risk-adjusted payoff, robust/minimum payoff;
- opponent curricula: static weighted, adaptive counter, and a mixed static+adaptive curriculum;
- one agent for each objective × curriculum combination.

The learner receives no Pressure, Control, or Chaos reward, label, score, mixture weight, or component-policy demonstration. The handcrafted PCC agents are not used during training.

Default training budget:

- 8 mutation-hill-climb iterations;
- 35 rounds per training evaluation;
- 2 evaluation seeds per curriculum opponent.

## Held-out behavioral evaluation

Freeze learned policies. Evaluate them only against opponent families not used as a training curriculum:

1. `MeanProfileExploiter`;
2. an exogenous three-regime `AlternatingWeightedOpponent`.

Use 100 rounds × 4 seeds per held-out context.

Behavioral inputs include payoff/win rate, allocation entropy/diversity, concentration, leverage targeting, viable-response count, temporal action change/repetition, recent-opponent counter payoff, and related public allocation statistics. Training objective and curriculum labels are excluded from the unsupervised model.

## Unsupervised analysis

Standardize held-out behavioral observables across the 12 agents and fit PCA. Separately compute mechanism-facing behavioral signatures based on previously established Blotto observables:

- **Pressure:** value-targeted commitment + response constriction;
- **Control:** strategic alignment against recently observed opponent allocations + response alignment;
- **Chaos:** allocation diversity + strategic adequacy against the held-out exploiter.

The signature definitions do not use training objective/curriculum labels.

## Prespecified primary checks

A strong three-axis emergence claim requires all of:

1. first three behavioral PCs explain at least **70%** of population variance;
2. Pressure, Control, and Chaos each map one-to-one onto **distinct PCs** with absolute correlation at least **0.50**;
3. each PCC behavioral signature has split-half evaluation-seed stability of at least **0.60**.

Failure of check 2 while checks 1 and 3 pass should be interpreted as evidence for stable low-dimensional PCC-related organization **without evidence that all three constructs are independent latent axes**.

## Claim guardrail

This experiment can strengthen the project beyond engineered-mixture recovery because no PCC weights exist in the learned-agent generator. It still does not establish uniqueness of PCC, human validity, or universal agent structure.
