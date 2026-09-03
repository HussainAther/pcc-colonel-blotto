from pcc_colonel_blotto.experiment import run_control_estimator_ablation


def test_control_estimator_ablation_schema():
    result = run_control_estimator_ablation(rounds=60, seeds=4, adaptation_window=8)
    assert result["schema"] == "pcc-colonel-blotto-control-estimator-ablation-v0.4"
    assert result["design"]["rounds_per_seed"] == 60
    assert result["design"]["adaptation_window"] == 8
    assert set(result["aggregate"]) == {
        "baseline",
        "control_full_history",
        "control_sliding_window",
        "control_exponential_decay",
        "control_change_point",
    }
    assert len(result["seed_results"]) == 4


def test_control_estimator_ablation_rejects_nonpositive_window():
    try:
        run_control_estimator_ablation(rounds=60, seeds=2, adaptation_window=0)
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
