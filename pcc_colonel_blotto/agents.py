from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Protocol

from .game import Allocation, BlottoGame, compositions


class Agent(Protocol):
    name: str
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation: ...


def _weighted_integer_allocation(total: int, weights: list[float]) -> Allocation:
    s = sum(weights)
    raw = [total * w / s for w in weights]
    base = [int(x) for x in raw]
    remainder = total - sum(base)
    order = sorted(range(len(weights)), key=lambda i: raw[i] - base[i], reverse=True)
    for i in order[:remainder]:
        base[i] += 1
    return tuple(base)


@dataclass
class ValueBaseline:
    name: str = "baseline"
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        jitter = [v * rng.uniform(0.85, 1.15) for v in game.values]
        return _weighted_integer_allocation(game.troops, jitter)


@dataclass
class PressureAgent:
    name: str = "pressure"
    concentration: float = 0.65
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        top = sorted(range(game.battlefields), key=lambda i: game.values[i], reverse=True)[:2]
        weights = [0.15 * v for v in game.values]
        for rank, i in enumerate(top):
            weights[i] += self.concentration * (2.0 - 0.35 * rank)
        return _weighted_integer_allocation(game.troops, weights)


@dataclass
class ControlAgent:
    name: str = "control"
    lookback: int = 8
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ValueBaseline().act(game, [], rng)
        hist = opponent_history[-self.lookback:]
        means = [sum(a[i] for a in hist) / len(hist) for i in range(game.battlefields)]
        # Prefer valuable fronts where one extra troop can plausibly create an overmatch.
        desirability = [game.values[i] / (1.0 + means[i]) for i in range(game.battlefields)]
        alloc = [0] * game.battlefields
        remaining = game.troops
        for i in sorted(range(game.battlefields), key=lambda j: desirability[j], reverse=True):
            target = min(remaining, int(math.floor(means[i])) + 1)
            alloc[i] += target
            remaining -= target
            if remaining == 0:
                break
        # Spend leftovers on the most valuable fronts.
        for i in sorted(range(game.battlefields), key=lambda j: game.values[j], reverse=True):
            if remaining <= 0:
                break
            alloc[i] += 1
            remaining -= 1
        return tuple(alloc)


@dataclass
class ChaosAgent:
    name: str = "chaos"
    candidate_pool: int = 80
    temperature: float = 0.20
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        universe = compositions(game.troops, game.battlefields)
        if opponent_history:
            hist = opponent_history[-8:]
            mean = tuple(round(sum(a[i] for a in hist) / len(hist)) for i in range(game.battlefields))
            # Repair rounded mean so it spends exactly the budget.
            mean = list(mean)
            while sum(mean) < game.troops:
                mean[max(range(game.battlefields), key=lambda i: game.values[i])] += 1
            while sum(mean) > game.troops:
                i = max((j for j in range(game.battlefields) if mean[j] > 0), key=lambda j: mean[j])
                mean[i] -= 1
            enemy = tuple(mean)
        else:
            enemy = _weighted_integer_allocation(game.troops, list(game.values))
        sample = rng.sample(universe, min(self.candidate_pool, len(universe)))
        scored = [(game.payoff(a, enemy), a) for a in sample]
        best = max(s for s, _ in scored)
        # Value guardrail: randomize among allocations within a small payoff band of the best sampled action.
        eligible = [a for s, a in scored if s >= best - self.temperature]
        return rng.choice(eligible)


@dataclass
class StaticWeightedOpponent:
    name: str = "static_weighted"
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        weights = [v * rng.uniform(0.7, 1.3) for v in game.values]
        return _weighted_integer_allocation(game.troops, weights)


@dataclass
class AdaptiveCounterOpponent:
    name: str = "adaptive_counter"
    lookback: int = 4
    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return StaticWeightedOpponent().act(game, [], rng)
        hist = opponent_history[-self.lookback:]
        means = [sum(a[i] for a in hist) / len(hist) for i in range(game.battlefields)]
        weights = [game.values[i] * (1.0 + means[i]) for i in range(game.battlefields)]
        return _weighted_integer_allocation(game.troops, weights)

@dataclass
class ShuffledHistoryControl:
    """Control ablation that preserves observed allocations but destroys their order.

    On every decision, the complete observed opponent history is permuted before it
    is passed to the ordinary Control policy.  This preserves the history multiset
    exactly at each round while breaking recency/ordering information.
    """
    name: str = "control_shuffled_history"
    lookback: int = 8

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ControlAgent(lookback=self.lookback).act(game, [], rng)
        shuffled = list(opponent_history)
        rng.shuffle(shuffled)
        return ControlAgent(lookback=self.lookback).act(game, shuffled, rng)


def _control_allocation_from_means(game: BlottoGame, means: list[float]) -> Allocation:
    """Construct the Control response to an estimated opponent allocation profile."""
    desirability = [game.values[i] / (1.0 + means[i]) for i in range(game.battlefields)]
    alloc = [0] * game.battlefields
    remaining = game.troops
    for i in sorted(range(game.battlefields), key=lambda j: desirability[j], reverse=True):
        target = min(remaining, int(math.floor(means[i])) + 1)
        alloc[i] += target
        remaining -= target
        if remaining == 0:
            break
    for i in sorted(range(game.battlefields), key=lambda j: game.values[j], reverse=True):
        if remaining <= 0:
            break
        alloc[i] += 1
        remaining -= 1
    return tuple(alloc)


def _history_means(history: list[Allocation], battlefields: int) -> list[float]:
    if not history:
        return [0.0] * battlefields
    return [sum(a[i] for a in history) / len(history) for i in range(battlefields)]


@dataclass
class FullHistoryControl:
    """Control using the complete observed-history mean."""
    name: str = "control_full_history"

    def estimate(self, game: BlottoGame, opponent_history: list[Allocation]) -> list[float]:
        return _history_means(opponent_history, game.battlefields)

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ValueBaseline().act(game, [], rng)
        return _control_allocation_from_means(game, self.estimate(game, opponent_history))


@dataclass
class SlidingWindowControl:
    """Control using a hard recency window."""
    name: str = "control_sliding_window"
    lookback: int = 8

    def estimate(self, game: BlottoGame, opponent_history: list[Allocation]) -> list[float]:
        return _history_means(opponent_history[-self.lookback:], game.battlefields)

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ValueBaseline().act(game, [], rng)
        return _control_allocation_from_means(game, self.estimate(game, opponent_history))


@dataclass
class ExponentialDecayControl:
    """Control using exponentially decayed opponent-allocation estimates."""
    name: str = "control_exponential_decay"
    alpha: float = 0.35

    def estimate(self, game: BlottoGame, opponent_history: list[Allocation]) -> list[float]:
        if not opponent_history:
            return [0.0] * game.battlefields
        means = [float(x) for x in opponent_history[0]]
        for a in opponent_history[1:]:
            means = [self.alpha * a[i] + (1.0 - self.alpha) * means[i] for i in range(game.battlefields)]
        return means

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ValueBaseline().act(game, [], rng)
        return _control_allocation_from_means(game, self.estimate(game, opponent_history))


@dataclass
class ChangePointControl:
    """Control that discards stale history after a detected distributional shift.

    Detection compares the mean of a recent block against the immediately prior
    block using L1 distance in troop allocations.  No true regime labels are used.
    """
    name: str = "control_change_point"
    window: int = 8
    threshold: float = 4.0

    def _segment(self, game: BlottoGame, opponent_history: list[Allocation]) -> list[Allocation]:
        if len(opponent_history) < 2 * self.window:
            return opponent_history
        # Scan candidate boundaries from newest to oldest and retain observations
        # after the most recent strong shift.
        for boundary in range(len(opponent_history) - self.window, self.window - 1, -1):
            before = opponent_history[boundary - self.window:boundary]
            after = opponent_history[boundary:min(len(opponent_history), boundary + self.window)]
            if len(after) < self.window:
                continue
            mb = _history_means(before, game.battlefields)
            ma = _history_means(after, game.battlefields)
            distance = sum(abs(ma[i] - mb[i]) for i in range(game.battlefields))
            if distance >= self.threshold:
                return opponent_history[boundary:]
        return opponent_history

    def estimate(self, game: BlottoGame, opponent_history: list[Allocation]) -> list[float]:
        return _history_means(self._segment(game, opponent_history), game.battlefields)

    def act(self, game: BlottoGame, opponent_history: list[Allocation], rng: random.Random) -> Allocation:
        if not opponent_history:
            return ValueBaseline().act(game, [], rng)
        return _control_allocation_from_means(game, self.estimate(game, opponent_history))
