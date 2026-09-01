from pcc_colonel_blotto.experiment import run_probe


def test_probe_shape():
    result = run_probe(rounds=10, seeds=2)
    assert result["schema"] == "pcc-colonel-blotto-mechanism-probe-v0.1"
    assert len(result["results"]) == 8
    assert set(result["prespecified_checks"]) == {
        "pressure_more_concentrated_than_baseline",
        "pressure_constricts_viable_responses",
        "chaos_more_allocation_entropy_than_baseline",
        "chaos_value_guardrail_vs_baseline",
        "control_beats_baseline_vs_adaptive",
    }
