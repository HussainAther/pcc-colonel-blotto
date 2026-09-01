import pytest

from pcc_colonel_blotto.game import BlottoGame, compositions


def test_compositions_count():
    # C(10+5-1, 5-1) = 1001
    assert len(compositions(10, 5)) == 1001


def test_zero_sum_payoff():
    game = BlottoGame()
    a = (0, 0, 0, 0, 10)
    b = (2, 2, 2, 2, 2)
    assert game.payoff(a, b) == -game.payoff(b, a)


def test_validate_budget():
    with pytest.raises(ValueError):
        BlottoGame().validate((1, 1, 1, 1, 1))
