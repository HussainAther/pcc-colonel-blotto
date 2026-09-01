from pcc_colonel_blotto.experiment import (
    generate_regime_switching_replay,
    run_control_regime_switching,
)
from pcc_colonel_blotto.game import BlottoGame


def test_regime_switching_trace_is_valid_deterministic_and_changes_regime():
    game = BlottoGame()
    a, labels_a = generate_regime_switching_replay(rounds=30, seed=7, game=game)
    b, labels_b = generate_regime_switching_replay(rounds=30, seed=7, game=game)
    assert a == b
    assert labels_a == labels_b
    assert set(labels_a) == {0, 1, 2}
    assert len(a) == 30
    assert all(game.validate(x) == x for x in a)


def test_regime_switching_result_schema_and_checks():
    result = run_control_regime_switching(rounds=60, seeds=4, adaptation_window=8)
    assert result["schema"] == "pcc-colonel-blotto-control-regime-switching-v0.3"
    assert result["design"]["rounds_per_seed"] == 60
    assert result["design"]["adaptation_window"] == 8
    assert len(result["seed_results"]) == 4
    assert set(result["prespecified_checks"]) == {
        "true_control_beats_baseline",
        "history_shuffle_hurts_control",
        "history_shuffle_eliminates_at_least_half_control_gain",
        "true_control_beats_shuffled_in_prespecified_16_round_window",
    }


def test_regime_switching_requires_three_rounds():
    game = BlottoGame()
    try:
        generate_regime_switching_replay(rounds=2, seed=1, game=game)
    except ValueError as exc:
        assert "at least 3" in str(exc)
    else:
        raise AssertionError("expected ValueError")
