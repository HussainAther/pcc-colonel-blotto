# PCC Colonel Blotto v1.0 Emergent Structure in Independently Learned Agents

No latent PCC weights exist in these agents. Twelve compact policies are independently optimized under generic game objectives and opponent curricula, frozen, then characterized only on held-out opponents.

## Unsupervised held-out behavior

- learned policies: **12**
- first three PC cumulative variance: **92.1%**
- assigned Pressure correlation: **+0.949** (PC1)
- assigned Control correlation: **+0.059** (PC3)
- assigned Chaos correlation: **+0.925** (PC2)

## Split-half stability

- Pressure: **+0.998**
- Control: **+0.997**
- Chaos: **+0.996**

## Prespecified checks

- **first_three_behavior_pcs_explain_at_least_70_percent**: PASS
- **three_distinct_pcs_align_with_pcc_signatures_at_least_0_50**: FAIL
- **pcc_signature_split_half_stability_at_least_0_60**: PASS

Overall primary rule: **FAIL**

## Interpretation guardrail

This is a stronger evidentiary level than engineered-mixture recovery because PCC weights are absent from the generator. The strong three-independent-axis rule fails: Pressure and Chaos align cleanly with separate dominant PCs, while Control is stable but not an independent third PC. This supports a narrower claim of reproducible PCC-related low-dimensional organization, not a unique three-axis basis, human validity, or universal agent structure.
