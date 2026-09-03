import random

from pcc_colonel_blotto.game import BlottoGame
from pcc_colonel_blotto.learned import LearnedLinearAgent, train_linear_agent
from pcc_colonel_blotto.agents import StaticWeightedOpponent


def test_learned_policy_spends_full_budget():
    game = BlottoGame()
    agent = LearnedLinearAgent((0.0,) * 9, temperature=0.2, candidate_pool=12)
    action = agent.act(game, [], random.Random(3))
    assert len(action) == game.battlefields
    assert sum(action) == game.troops
    assert min(action) >= 0


def test_training_has_no_pcc_target_and_returns_valid_agent():
    game = BlottoGame()
    agent, meta = train_linear_agent(
        game=game,
        opponent_factories=[StaticWeightedOpponent],
        objective="payoff",
        seed=11,
        iterations=1,
        rounds=8,
        eval_seeds=1,
    )
    assert len(agent.coefficients) == 9
    assert meta["objective"] == "payoff"
    assert "pcc" not in " ".join(meta.keys()).lower()
    assert sum(agent.act(game, [], random.Random(5))) == game.troops
