import random

from pcc_colonel_blotto.agents import MixedPCCAgent
from pcc_colonel_blotto.experiment import _project_simplex, _simplex_grid, _trajectory_observables
from pcc_colonel_blotto.game import BlottoGame


def test_mixed_agent_spends_budget():
    game = BlottoGame()
    agent = MixedPCCAgent(0.2, 0.3, 0.5)
    action = agent.act(game, [], random.Random(7))
    assert len(action) == game.battlefields
    assert sum(action) == game.troops


def test_simplex_grid_and_ood_partition_are_deterministic():
    grid = _simplex_grid(10)
    assert len(grid) == 66
    assert all(abs(sum(w) - 1.0) < 1e-12 for w in grid)
    assert sum(max(w) >= 0.75 for w in grid) > 0
    assert sum(max(w) < 0.75 for w in grid) > 0


def test_simplex_projection_is_valid():
    p = _project_simplex([1.2, -0.1, 0.4])
    assert all(x >= 0 for x in p)
    assert abs(sum(p) - 1.0) < 1e-9


def test_observable_feature_contract_contains_no_latent_metadata():
    game = BlottoGame()
    actions = [(2, 2, 2, 2, 2), (1, 2, 2, 2, 3)]
    opponents = [(2, 2, 2, 2, 2), (3, 2, 2, 2, 1)]
    features = _trajectory_observables(actions, opponents, [0.0, 0.2], game)
    forbidden_tokens = ("weight", "component", "seed", "opponent_family", "internal")
    assert all(not any(tok in name for tok in forbidden_tokens) for name in features)
    assert "allocation_entropy" in features
    assert "mean_leverage_targeting" in features
