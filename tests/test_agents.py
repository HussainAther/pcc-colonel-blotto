import random

from pcc_colonel_blotto.agents import ChaosAgent, ControlAgent, PressureAgent, ValueBaseline
from pcc_colonel_blotto.game import BlottoGame


def test_agents_return_valid_allocations():
    game = BlottoGame()
    history = [(2, 2, 2, 2, 2), (1, 1, 2, 3, 3)]
    for agent in [ValueBaseline(), PressureAgent(), ControlAgent(), ChaosAgent()]:
        allocation = agent.act(game, history, random.Random(7))
        assert game.validate(allocation) == allocation


def test_control_estimator_variants_return_valid_allocations():
    from pcc_colonel_blotto.agents import (
        ChangePointControl,
        ExponentialDecayControl,
        FullHistoryControl,
        SlidingWindowControl,
    )
    import random
    from pcc_colonel_blotto.game import BlottoGame

    game = BlottoGame()
    history = [(1, 1, 1, 3, 4)] * 10 + [(4, 3, 1, 1, 1)] * 10
    for agent in [FullHistoryControl(), SlidingWindowControl(), ExponentialDecayControl(), ChangePointControl()]:
        action = agent.act(game, history, random.Random(1))
        assert game.validate(action) == action
        estimate = agent.estimate(game, history)
        assert len(estimate) == game.battlefields
        assert abs(sum(estimate) - game.troops) < 1e-9


def test_change_point_control_uses_only_observed_history():
    from pcc_colonel_blotto.agents import ChangePointControl
    from pcc_colonel_blotto.game import BlottoGame

    game = BlottoGame()
    agent = ChangePointControl(window=4, threshold=2.0)
    old = [(1, 1, 1, 3, 4)] * 8
    new = [(4, 3, 1, 1, 1)] * 8
    estimate = agent.estimate(game, old + new)
    assert estimate[0] > estimate[4]
