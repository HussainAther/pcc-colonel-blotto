from pcc_colonel_blotto.experiment import run_control_modulation


def test_control_modulation_smoke_has_disjoint_measurement_and_cv_models():
    r = run_control_modulation(train_iterations=1, train_rounds=8, eval_rounds=20, signature_seeds=2, outcome_seeds=2)
    assert r["design"]["latent_pcc_weights_in_generator"] is False
    assert r["design"]["signature_and_outcome_seeds_disjoint"] is True
    assert r["design"]["cross_validation"] == "leave-one-agent-out"
    assert set(r["aggregate"]["standardized_mae"]) == {"additive", "control_interaction"}
    assert len(r["per_agent_cv_errors"]) == 12
