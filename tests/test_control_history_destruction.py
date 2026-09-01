import random

from pcc_colonel_blotto.agents import ControlAgent, ShuffledHistoryControl
from pcc_colonel_blotto.experiment import (
    generate_adaptive_replay,
    run_control_history_destruction,
    run_replay,
)
from pcc_colonel_blotto.game import BlottoGame


def test_generated_replay_is_valid_and_deterministic():
    game = BlottoGame()
    a = generate_adaptive_replay(rounds=20, seed=7, game=game)
    b = generate_adaptive_replay(rounds=20, seed=7, game=game)
    assert a == b
    assert len(a) == 20
    assert all(game.validate(x) == x for x in a)


def test_shuffled_history_control_preserves_budget():
    game = BlottoGame()
    history = generate_adaptive_replay(rounds=12, seed=3, game=game)
    action = ShuffledHistoryControl().act(game, history, random.Random(99))
    assert game.validate(action) == action


def test_replay_uses_same_trace_for_agents():
    game = BlottoGame()
    trace = generate_adaptive_replay(rounds=25, seed=5, game=game)
    true = run_replay(ControlAgent(), trace, seed=5, game=game)
    shuffled = run_replay(ShuffledHistoryControl(), trace, seed=5, game=game)
    assert true.rounds == shuffled.rounds == len(trace)


def test_history_destruction_result_schema_and_checks():
    result = run_control_history_destruction(rounds=40, seeds=4)
    assert result["schema"] == "pcc-colonel-blotto-control-history-destruction-v0.2"
    assert result["design"]["rounds_per_seed"] == 40
    assert len(result["seed_results"]) == 4
    assert set(result["prespecified_checks"]) == {
        "true_control_beats_baseline",
        "history_shuffle_hurts_control",
        "history_shuffle_eliminates_at_least_half_control_gain",
    }
