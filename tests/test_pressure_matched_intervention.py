from pcc_colonel_blotto.experiment import (
    PRESSURE_VALUE_TOLERANCE,
    run_pressure_matched_intervention,
)


def test_pressure_matching_preserves_budget_and_value_tolerance():
    result = run_pressure_matched_intervention()
    assert result["aggregate"]["matched_pairs"] > 50
    assert result["prespecified_checks"]["exact_troop_budget_preserved"]["pass"]
    assert result["prespecified_checks"]["strategic_value_matched_within_tolerance"]["pass"]
    assert result["aggregate"]["max_absolute_value_gap"] <= PRESSURE_VALUE_TOLERANCE + 1e-12


def test_pressure_intervention_separates_concentration():
    result = run_pressure_matched_intervention()
    a = result["aggregate"]
    assert a["mean_high_concentration"] > a["mean_low_concentration"]
    assert result["prespecified_checks"]["concentration_manipulation_succeeded"]["pass"]


def test_pressure_intervention_is_deterministic():
    a = run_pressure_matched_intervention()
    b = run_pressure_matched_intervention()
    assert a["aggregate"] == b["aggregate"]
    assert a["pairs"] == b["pairs"]
