from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Sequence

Allocation = tuple[int, ...]


def compositions(total: int, parts: int) -> list[Allocation]:
    if total < 0 or parts <= 0:
        raise ValueError("total must be >= 0 and parts must be > 0")
    out: list[Allocation] = []

    def rec(prefix: list[int], left: int, slots: int) -> None:
        if slots == 1:
            out.append(tuple(prefix + [left]))
            return
        for x in range(left + 1):
            rec(prefix + [x], left - x, slots - 1)

    rec([], total, parts)
    return out


@dataclass(frozen=True)
class BlottoGame:
    troops: int = 10
    values: tuple[float, ...] = (1.0, 1.5, 2.0, 2.5, 3.0)

    @property
    def battlefields(self) -> int:
        return len(self.values)

    def validate(self, allocation: Sequence[int]) -> Allocation:
        alloc = tuple(int(x) for x in allocation)
        if len(alloc) != self.battlefields:
            raise ValueError("allocation has wrong number of battlefields")
        if any(x < 0 for x in alloc):
            raise ValueError("allocation cannot contain negative troops")
        if sum(alloc) != self.troops:
            raise ValueError("allocation must spend exactly all troops")
        return alloc

    def payoff(self, a: Sequence[int], b: Sequence[int]) -> float:
        aa, bb = self.validate(a), self.validate(b)
        score = 0.0
        for av, bv, value in zip(aa, bb, self.values):
            if av > bv:
                score += value
            elif av < bv:
                score -= value
        return score / sum(self.values)

    def won_value(self, a: Sequence[int], b: Sequence[int]) -> float:
        aa, bb = self.validate(a), self.validate(b)
        return sum(v for av, bv, v in zip(aa, bb, self.values) if av > bv) / sum(self.values)

    def viable_responses(self, attack: Sequence[int], threshold: float = 0.0) -> int:
        """Count pure allocations yielding payoff >= threshold against ``attack``."""
        enemy = self.validate(attack)
        return self._viable_responses_cached(enemy, float(threshold))

    @lru_cache(maxsize=None)
    def _viable_responses_cached(self, enemy: Allocation, threshold: float) -> int:
        return sum(
            1 for response in compositions(self.troops, self.battlefields)
            if self.payoff(response, enemy) >= threshold
        )
