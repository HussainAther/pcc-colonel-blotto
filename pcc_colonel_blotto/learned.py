from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

from .game import Allocation, BlottoGame, compositions


@lru_cache(maxsize=None)
def _universe(troops: int, battlefields: int) -> tuple[Allocation, ...]:
    return tuple(compositions(troops, battlefields))


def _repair_profile(game: BlottoGame, values: list[float]) -> Allocation:
    rounded = [max(0, int(round(x))) for x in values]
    while sum(rounded) < game.troops:
        i = max(range(game.battlefields), key=lambda j: (values[j] - rounded[j], game.values[j], -j))
        rounded[i] += 1
    while sum(rounded) > game.troops:
        candidates = [j for j in range(game.battlefields) if rounded[j] > 0]
        i = max(candidates, key=lambda j: (rounded[j] - values[j], -game.values[j], -j))
        rounded[i] -= 1
    return tuple(rounded)


def _history_prediction(game: BlottoGame, history: list[Allocation], lookback: int = 8) -> Allocation:
    if not history:
        total_value = sum(game.values)
        raw = [game.troops * v / total_value for v in game.values]
        return _repair_profile(game, raw)
    hist = history[-lookback:]
    means = [sum(a[i] for a in hist) / len(hist) for i in range(game.battlefields)]
    return _repair_profile(game, means)


def _concentration(a: Allocation) -> float:
    return max(a) / sum(a)


def _leverage(game: BlottoGame, a: Allocation) -> float:
    lo, hi = min(game.values), max(game.values)
    norm = [(v - lo) / (hi - lo) if hi > lo else 0.0 for v in game.values]
    return sum(x * w for x, w in zip(a, norm)) / game.troops



@lru_cache(maxsize=None)
def _action_static(troops: int, values: tuple[float, ...]) -> dict[Allocation, tuple[float, float, tuple[float, ...]]]:
    game = BlottoGame(troops=troops, values=values)
    return {a: (_leverage(game, a), _concentration(a), tuple(x / troops for x in a)) for a in _universe(troops, len(values))}


def _fast_payoff(a: Allocation, b: Allocation, values: tuple[float, ...]) -> float:
    score = 0.0
    for av, bv, value in zip(a, b, values):
        if av > bv:
            score += value
        elif av < bv:
            score -= value
    return score / sum(values)

@dataclass
class LearnedLinearAgent:
    """Compact independently learned Blotto policy with no PCC labels or weights."""

    coefficients: tuple[float, ...]
    temperature: float = 0.25
    candidate_pool: int = 64
    name: str = "learned_linear"

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        universe = _universe(game.troops, game.battlefields)
        predicted = _history_prediction(game, opponent_history)
        # Include a deterministic scaffold plus a stochastic candidate set so the
        # policy can learn both stable and diversified responses.
        static = _action_static(game.troops, game.values)
        ranked_value = sorted(universe, key=lambda a: static[a][0], reverse=True)[:12]
        sampled = rng.sample(universe, min(self.candidate_pool, len(universe)))
        candidates = list(dict.fromkeys(ranked_value + sampled))
        scored: list[tuple[float, Allocation]] = []
        for a in candidates:
            lev, conc, alloc_frac = static[a]
            features = [
                lev,
                conc,
                _fast_payoff(a, predicted, game.values),
                sum(abs(a[i] - predicted[i]) for i in range(game.battlefields)) / (2 * game.troops),
                *alloc_frac,
            ]
            score = sum(c * f for c, f in zip(self.coefficients, features))
            scored.append((score, a))
        # Gumbel-max sampling. Temperature is learned by black-box optimization.
        t = max(0.02, self.temperature)
        return max(scored, key=lambda sa: sa[0] + t * (-math.log(-math.log(max(1e-12, min(1 - 1e-12, rng.random()))))))[1]


@dataclass
class TrainingEpisode:
    mean_payoff: float
    win_rate: float
    payoff_std: float


def _episode(agent: LearnedLinearAgent, opponent, *, game: BlottoGame, rounds: int, seed: int) -> TrainingEpisode:
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 10_000_019)
    ah: list[Allocation] = []
    bh: list[Allocation] = []
    payoffs: list[float] = []
    for _ in range(rounds):
        a = agent.act(game, bh, rng_a)
        b = opponent.act(game, ah, rng_b)
        p = game.payoff(a, b)
        ah.append(a)
        bh.append(b)
        payoffs.append(p)
    mean = sum(payoffs) / rounds
    variance = sum((x - mean) ** 2 for x in payoffs) / rounds
    return TrainingEpisode(mean, sum(x > 0 for x in payoffs) / rounds, math.sqrt(variance))


def _objective_value(episodes: list[TrainingEpisode], objective: str) -> float:
    mean_payoff = sum(e.mean_payoff for e in episodes) / len(episodes)
    mean_win = sum(e.win_rate for e in episodes) / len(episodes)
    if objective == "payoff":
        return mean_payoff
    if objective == "win_rate":
        return mean_win
    if objective == "risk_adjusted":
        return mean_payoff - 0.35 * sum(e.payoff_std for e in episodes) / len(episodes)
    if objective == "robust":
        return min(e.mean_payoff for e in episodes)
    raise ValueError(f"unknown objective: {objective}")


def train_linear_agent(
    *,
    game: BlottoGame,
    opponent_factories: list[Callable[[], object]],
    objective: str,
    seed: int,
    iterations: int = 18,
    rounds: int = 60,
    eval_seeds: int = 2,
) -> tuple[LearnedLinearAgent, dict]:
    """Mutation hill-climbing on generic game objectives; no PCC supervision."""
    rng = random.Random(seed)
    dim = 4 + game.battlefields
    coeffs = tuple(rng.uniform(-1.0, 1.0) for _ in range(dim))
    temp = math.exp(rng.uniform(math.log(0.06), math.log(0.8)))

    def score(c: tuple[float, ...], t: float) -> float:
        candidate = LearnedLinearAgent(c, temperature=t, candidate_pool=48)
        episodes: list[TrainingEpisode] = []
        for oi, factory in enumerate(opponent_factories):
            for rep in range(eval_seeds):
                episodes.append(_episode(candidate, factory(), game=game, rounds=rounds, seed=seed * 1009 + oi * 101 + rep))
        return _objective_value(episodes, objective)

    best = score(coeffs, temp)
    accepted = 0
    for it in range(iterations):
        scale = 0.45 * (0.92 ** it)
        proposal = tuple(c + rng.gauss(0.0, scale) for c in coeffs)
        prop_temp = min(1.5, max(0.02, temp * math.exp(rng.gauss(0.0, 0.25))))
        value = score(proposal, prop_temp)
        if value > best:
            coeffs, temp, best = proposal, prop_temp, value
            accepted += 1
    agent = LearnedLinearAgent(coeffs, temperature=temp, candidate_pool=64, name=f"learned_{objective}_{seed}")
    return agent, {
        "objective": objective,
        "seed": seed,
        "training_score": best,
        "accepted_mutations": accepted,
        "temperature": temp,
        "coefficients": list(coeffs),
    }

@dataclass
class AlternatingWeightedOpponent:
    """Held-out exogenous regime opponent; never used by the v1.0 trainer."""
    name: str = "alternating_weighted_heldout"
    phase_length: int = 24
    step: int = 0

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        phase = (self.step // self.phase_length) % 3
        self.step += 1
        multipliers = (
            (1.7, 1.5, 1.0, 0.7, 0.6),
            (0.6, 0.8, 1.1, 1.5, 1.7),
            (0.9, 1.5, 0.7, 1.6, 0.8),
        )[phase]
        weights = [game.values[i] * multipliers[i] * rng.uniform(0.9, 1.1) for i in range(game.battlefields)]
        total = sum(weights)
        raw = [game.troops * w / total for w in weights]
        return _repair_profile(game, raw)
