from pcc_colonel_blotto.experiment import (
    PC_BOUNDARY_FEATURES,
    _pc_edge_grid,
    _restricted_pc_features,
    _trajectory_observables,
)
from pcc_colonel_blotto.game import BlottoGame


def test_pc_edge_grid_has_zero_chaos_and_expected_size():
    grid = _pc_edge_grid()
    assert len(grid) == 21
    assert all(abs(sum(w) - 1.0) < 1e-12 for w in grid)
    assert all(w[2] == 0.0 for w in grid)
    assert grid[0] == (0.0, 1.0, 0.0)
    assert grid[-1] == (1.0, 0.0, 0.0)


def test_pc_boundary_feature_contract_excludes_entropy_shortcuts():
    forbidden = {"allocation_entropy", "distinct_action_ratio", "repeat_rate", "mean_step_l1"}
    assert forbidden.isdisjoint(PC_BOUNDARY_FEATURES)
    assert all("variance" not in name for name in PC_BOUNDARY_FEATURES)
    assert "mean_leverage_targeting" in PC_BOUNDARY_FEATURES
    assert "mean_opponent_viable_responses" in PC_BOUNDARY_FEATURES


def test_restricted_features_match_frozen_contract():
    game = BlottoGame()
    actions = [(2, 2, 2, 2, 2), (1, 2, 2, 2, 3)]
    opponents = [(2, 2, 2, 2, 2), (3, 2, 2, 2, 1)]
    full = _trajectory_observables(actions, opponents, [0.0, 0.2], game)
    restricted = _restricted_pc_features(full)
    assert list(restricted) == PC_BOUNDARY_FEATURES
    assert set(restricted).issubset(full)
