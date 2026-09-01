from __future__ import annotations

import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .agents import AdaptiveCounterOpponent, ChaosAgent, ControlAgent, PressureAgent, StaticWeightedOpponent, ValueBaseline
from .game import Allocation, BlottoGame


@dataclass
class MatchSummary:
    agent: str
    opponent: str
    rounds: int
    mean_payoff: float
    win_rate: float
    allocation_entropy: float
    mean_concentration: float
    mean_opponent_viable_responses: float


def entropy(items: list[Allocation]) -> float:
    counts = Counter(items)
    n = len(items)
    if not n:
        return 0.0
    return -sum((c / n) * math.log(c / n) for c in counts.values())


def concentration(a: Allocation) -> float:
    total = sum(a)
    return max(a) / total if total else 0.0


def run_match(agent, opponent, *, rounds: int, seed: int, game: BlottoGame) -> MatchSummary:
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 10_000_019)
    a_hist: list[Allocation] = []
    b_hist: list[Allocation] = []
    payoffs: list[float] = []
    constriction: list[int] = []
    for _ in range(rounds):
        a = agent.act(game, b_hist, rng_a)
        b = opponent.act(game, a_hist, rng_b)
        payoffs.append(game.payoff(a, b))
        constriction.append(game.viable_responses(a))
        a_hist.append(a)
        b_hist.append(b)
    return MatchSummary(
        agent=agent.name,
        opponent=opponent.name,
        rounds=rounds,
        mean_payoff=sum(payoffs) / rounds,
        win_rate=sum(1 for x in payoffs if x > 0) / rounds,
        allocation_entropy=entropy(a_hist),
        mean_concentration=sum(concentration(a) for a in a_hist) / rounds,
        mean_opponent_viable_responses=sum(constriction) / rounds,
    )


def run_probe(rounds: int = 250, seeds: int = 8) -> dict:
    game = BlottoGame()
    agents = [ValueBaseline(), PressureAgent(), ControlAgent(), ChaosAgent()]
    opponents = [StaticWeightedOpponent(), AdaptiveCounterOpponent()]
    rows: list[dict] = []
    for agent in agents:
        for opponent in opponents:
            summaries = [run_match(agent, opponent, rounds=rounds, seed=s, game=game) for s in range(seeds)]
            rows.append({
                "agent": agent.name,
                "opponent": opponent.name,
                "rounds_per_seed": rounds,
                "seeds": seeds,
                "mean_payoff": sum(x.mean_payoff for x in summaries) / seeds,
                "win_rate": sum(x.win_rate for x in summaries) / seeds,
                "allocation_entropy": sum(x.allocation_entropy for x in summaries) / seeds,
                "mean_concentration": sum(x.mean_concentration for x in summaries) / seeds,
                "mean_opponent_viable_responses": sum(x.mean_opponent_viable_responses for x in summaries) / seeds,
            })
    by_key = {(r["agent"], r["opponent"]): r for r in rows}
    pressure = sum(by_key[("pressure", o)]["mean_concentration"] for o in ("static_weighted", "adaptive_counter")) / 2
    baseline = sum(by_key[("baseline", o)]["mean_concentration"] for o in ("static_weighted", "adaptive_counter")) / 2
    chaos_entropy = sum(by_key[("chaos", o)]["allocation_entropy"] for o in ("static_weighted", "adaptive_counter")) / 2
    baseline_entropy = sum(by_key[("baseline", o)]["allocation_entropy"] for o in ("static_weighted", "adaptive_counter")) / 2
    control_adaptive = by_key[("control", "adaptive_counter")]["mean_payoff"]
    baseline_adaptive = by_key[("baseline", "adaptive_counter")]["mean_payoff"]
    pressure_viable = sum(by_key[("pressure", o)]["mean_opponent_viable_responses"] for o in ("static_weighted", "adaptive_counter")) / 2
    baseline_viable = sum(by_key[("baseline", o)]["mean_opponent_viable_responses"] for o in ("static_weighted", "adaptive_counter")) / 2
    chaos_min_payoff_advantage = min(
        by_key[("chaos", o)]["mean_payoff"] - by_key[("baseline", o)]["mean_payoff"]
        for o in ("static_weighted", "adaptive_counter")
    )
    return {
        "schema": "pcc-colonel-blotto-mechanism-probe-v0.1",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {"rounds_per_seed": rounds, "seeds": seeds, "opponents": [o.name for o in opponents]},
        "results": rows,
        "prespecified_checks": {
            "pressure_more_concentrated_than_baseline": {"pass": pressure > baseline, "pressure": pressure, "baseline": baseline},
            "pressure_constricts_viable_responses": {"pass": pressure_viable < baseline_viable, "pressure": pressure_viable, "baseline": baseline_viable},
            "chaos_more_allocation_entropy_than_baseline": {"pass": chaos_entropy > baseline_entropy, "chaos": chaos_entropy, "baseline": baseline_entropy},
            "chaos_value_guardrail_vs_baseline": {"pass": chaos_min_payoff_advantage >= 0.0, "minimum_payoff_advantage": chaos_min_payoff_advantage},
            "control_beats_baseline_vs_adaptive": {"pass": control_adaptive > baseline_adaptive, "control": control_adaptive, "baseline": baseline_adaptive},
        },
        "claim_scope": "mechanism probe only; not construct recovery",
    }


def write_probe(output_dir: str | Path, rounds: int = 250, seeds: int = 8) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_probe(rounds=rounds, seeds=seeds)
    (out / "mechanism-probe.json").write_text(json.dumps(result, indent=2) + "\n")
    checks = result["prespecified_checks"]
    lines = [
        "# PCC Colonel Blotto v0.1 Mechanism Probe",
        "",
        "This is a synthetic engineering probe, **not** a frozen construct-recovery claim.",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in checks.items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += ["", "## Match summaries", "", "| agent | opponent | payoff | win rate | entropy | concentration | viable responses |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in result["results"]:
        lines.append(f"| {r['agent']} | {r['opponent']} | {r['mean_payoff']:.4f} | {r['win_rate']:.3f} | {r['allocation_entropy']:.3f} | {r['mean_concentration']:.3f} | {r['mean_opponent_viable_responses']:.1f} |")
    (out / "MECHANISM_PROBE.md").write_text("\n".join(lines) + "\n")
    return result
