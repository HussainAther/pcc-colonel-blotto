import random

from pcc_colonel_blotto.agents import ChaosAgent, ControlAgent, PressureAgent, ValueBaseline
from pcc_colonel_blotto.game import BlottoGame


def test_agents_return_valid_allocations():
    game = BlottoGame()
    history = [(2, 2, 2, 2, 2), (1, 1, 2, 3, 3)]
    for agent in [ValueBaseline(), PressureAgent(), ControlAgent(), ChaosAgent()]:
        allocation = agent.act(game, history, random.Random(7))
        assert game.validate(allocation) == allocation
