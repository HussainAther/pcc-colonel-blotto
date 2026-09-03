from pcc_colonel_blotto.experiment import (
    PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE,
    PRESSURE_VALUE_TOLERANCE,
    leverage_targeting,
    run_pressure_leverage_intervention,
)
from pcc_colonel_blotto.game import BlottoGame


def test_leverage_targeting_rewards_higher_value_fields():
    game = BlottoGame()
    assert leverage_targeting(game, (10, 0, 0, 0, 0)) == 0.0
    assert leverage_targeting(game, (0, 0, 0, 0, 10)) == 1.0


def test_pressure_leverage_matching_preserves_controls():
    result = run_pressure_leverage_intervention()
    a = result["aggregate"]
    assert a["matched_pairs"] >= 30
    assert a["max_absolute_value_gap"] <= PRESSURE_VALUE_TOLERANCE + 1e-12
    assert a["max_absolute_concentration_gap"] <= PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE + 1e-12
    assert result["prespecified_checks"]["exact_troop_budget_preserved"]["pass"]
    assert result["prespecified_checks"]["strategic_value_matched_within_tolerance"]["pass"]
    assert result["prespecified_checks"]["concentration_matched_within_tolerance"]["pass"]


def test_pressure_leverage_manipulation_separates_targeting():
    result = run_pressure_leverage_intervention()
    a = result["aggregate"]
    assert a["mean_high_leverage"] > a["mean_low_leverage"]
    assert result["prespecified_checks"]["leverage_targeting_manipulation_succeeded"]["pass"]


def test_pressure_leverage_intervention_is_deterministic():
    a = run_pressure_leverage_intervention()
    b = run_pressure_leverage_intervention()
    assert a["aggregate"] == b["aggregate"]
    assert a["pairs"] == b["pairs"]
