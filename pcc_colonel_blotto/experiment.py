from __future__ import annotations

import json
import math
import random
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .agents import (
    AdaptiveCounterOpponent,
    ChaosAgent,
    ControlAgent,
    PressureAgent,
    ShuffledHistoryControl,
    StaticWeightedOpponent,
    ValueBaseline,
)
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


@dataclass
class ReplaySummary:
    agent: str
    rounds: int
    mean_payoff: float
    win_rate: float
    allocation_entropy: float
    mean_concentration: float


def generate_adaptive_replay(*, rounds: int, seed: int, game: BlottoGame) -> list[Allocation]:
    """Generate a fixed adaptive-opponent trace against a reference baseline.

    The resulting opponent allocation sequence is then replayed unchanged to every
    evaluation policy.  This paired design isolates information use: true-history
    and shuffled-history Control see exactly the same realized opponent actions.
    """
    reference = ValueBaseline()
    opponent = AdaptiveCounterOpponent()
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 10_000_019)
    a_hist: list[Allocation] = []
    b_hist: list[Allocation] = []
    for _ in range(rounds):
        a = reference.act(game, b_hist, rng_a)
        b = opponent.act(game, a_hist, rng_b)
        a_hist.append(a)
        b_hist.append(b)
    return b_hist


def run_replay(agent, opponent_trace: list[Allocation], *, seed: int, game: BlottoGame) -> ReplaySummary:
    rng = random.Random(seed + 30_000_057)
    observed: list[Allocation] = []
    actions: list[Allocation] = []
    payoffs: list[float] = []
    for b in opponent_trace:
        a = agent.act(game, observed, rng)
        payoffs.append(game.payoff(a, b))
        actions.append(a)
        observed.append(b)
    rounds = len(opponent_trace)
    return ReplaySummary(
        agent=agent.name,
        rounds=rounds,
        mean_payoff=sum(payoffs) / rounds,
        win_rate=sum(1 for x in payoffs if x > 0) / rounds,
        allocation_entropy=entropy(actions),
        mean_concentration=sum(concentration(a) for a in actions) / rounds,
    )


def run_control_history_destruction(rounds: int = 250, seeds: int = 32) -> dict:
    """Prospective paired replay falsification of temporal information use by Control."""
    game = BlottoGame()
    agents = [ValueBaseline(), ShuffledHistoryControl(), ControlAgent()]
    seed_rows: list[dict] = []
    for seed in range(seeds):
        trace = generate_adaptive_replay(rounds=rounds, seed=seed, game=game)
        summaries = {a.name: run_replay(a, trace, seed=seed, game=game) for a in agents}
        row = {"seed": seed}
        for name, summary in summaries.items():
            row[name] = asdict(summary)
        seed_rows.append(row)

    def mean_metric(agent_name: str, metric: str) -> float:
        return sum(r[agent_name][metric] for r in seed_rows) / seeds

    baseline = mean_metric("baseline", "mean_payoff")
    shuffled = mean_metric("control_shuffled_history", "mean_payoff")
    true = mean_metric("control", "mean_payoff")
    true_gain = true - baseline
    shuffled_gain = shuffled - baseline
    if true_gain > 0:
        retained = shuffled_gain / true_gain
        collapsed = 1.0 - retained
    else:
        retained = None
        collapsed = None

    return {
        "schema": "pcc-colonel-blotto-control-history-destruction-v0.2",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_seed": rounds,
            "seeds": seeds,
            "opponent_trace": "AdaptiveCounterOpponent generated against ValueBaseline, then replayed identically across conditions",
            "ablation": "permute complete observed opponent history before Control; preserve history multiset exactly at every decision",
            "control_lookback": ControlAgent().lookback,
            "primary_threshold": "at least 50% of true Control payoff gain over Baseline is eliminated",
        },
        "aggregate": {
            "baseline_mean_payoff": baseline,
            "shuffled_control_mean_payoff": shuffled,
            "true_control_mean_payoff": true,
            "true_control_gain_over_baseline": true_gain,
            "shuffled_control_gain_over_baseline": shuffled_gain,
            "fraction_control_gain_retained_after_shuffle": retained,
            "fraction_control_gain_eliminated_after_shuffle": collapsed,
            "baseline_win_rate": mean_metric("baseline", "win_rate"),
            "shuffled_control_win_rate": mean_metric("control_shuffled_history", "win_rate"),
            "true_control_win_rate": mean_metric("control", "win_rate"),
        },
        "prespecified_checks": {
            "true_control_beats_baseline": {"pass": true_gain > 0.0, "gain": true_gain},
            "history_shuffle_hurts_control": {"pass": shuffled < true, "delta_shuffled_minus_true": shuffled - true},
            "history_shuffle_eliminates_at_least_half_control_gain": {
                "pass": bool(true_gain > 0.0 and collapsed is not None and collapsed >= 0.5),
                "fraction_eliminated": collapsed,
                "threshold": 0.5,
            },
        },
        "seed_results": seed_rows,
        "claim_scope": "paired replay temporal-information falsification; not closed-loop construct recovery",
    }


def write_control_history_destruction(output_dir: str | Path, rounds: int = 250, seeds: int = 32) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_control_history_destruction(rounds=rounds, seeds=seeds)
    (out / "control-history-destruction.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    a = result["aggregate"]
    checks = result["prespecified_checks"]
    lines = [
        "# Control History-Destruction Falsification",
        "",
        "This is a **paired replay** test of whether Control benefits from temporal/recency information rather than merely from the marginal distribution of opponent allocations.",
        "",
        "Every condition faces the exact same opponent allocation sequence. The shuffled condition preserves the complete history multiset at every decision but permutes its order before the ordinary Control policy is evaluated.",
        "",
        "## Prespecified prediction",
        "",
        "At least **50% of true Control's payoff gain over Baseline** should disappear after history order is destroyed.",
        "",
        "## Aggregate result",
        "",
        "| condition | mean payoff | win rate |",
        "|---|---:|---:|",
        f"| Baseline | {a['baseline_mean_payoff']:.4f} | {a['baseline_win_rate']:.3f} |",
        f"| Shuffled-history Control | {a['shuffled_control_mean_payoff']:.4f} | {a['shuffled_control_win_rate']:.3f} |",
        f"| True-history Control | {a['true_control_mean_payoff']:.4f} | {a['true_control_win_rate']:.3f} |",
        "",
        f"True Control gain over Baseline: **{a['true_control_gain_over_baseline']:.4f}**",
        "",
        f"Shuffled Control gain over Baseline: **{a['shuffled_control_gain_over_baseline']:.4f}**",
        "",
        (f"Fraction of Control gain eliminated by shuffling: **{a['fraction_control_gain_eliminated_after_shuffle']:.1%}**"
         if a['fraction_control_gain_eliminated_after_shuffle'] is not None
         else "Fraction of Control gain eliminated by shuffling: **undefined (true Control did not beat Baseline)**"),
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in checks.items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        "## Post-switch window sensitivity (descriptive)",
        "",
        "| window | Baseline | Shuffled Control | True Control | True - shuffled |",
        "|---:|---:|---:|---:|---:|",
    ]
    for width, d in a["post_switch_window_diagnostics"].items():
        lines.append(
            f"| {width} | {d['baseline']:.4f} | {d['control_shuffled_history']:.4f} | "
            f"{d['control']:.4f} | {d['true_minus_shuffled']:.4f} |"
        )
    lines += [
        "",
        "The 16-round true-history edge is not robust across diagnostic window widths: true-history Control is worse than shuffled at 4 and 8 rounds, slightly better at 16, and slightly worse again at 32. Baseline also remains best in every reported post-switch window.",
        "",
        "## Interpretation guardrail",
        "",
        "A failure of the 50% threshold does not invalidate the simulator. It means the current Control policy's advantage is not primarily carried by temporal ordering/recency under this paired replay design, and the Control operationalization should be revised before stronger cross-game claims are made.",
    ]
    (out / "CONTROL_HISTORY_DESTRUCTION.md").write_text("\n".join(lines) + "\n")
    return result


def generate_regime_switching_replay(*, rounds: int, seed: int, game: BlottoGame) -> tuple[list[Allocation], list[int]]:
    """Generate an exogenous three-regime opponent trace.

    Regimes deliberately emphasize different battlefield subsets.  The trace is
    independent of the evaluated policy and is replayed identically across
    Baseline, true-history Control, and shuffled-history Control.
    """
    if rounds < 3:
        raise ValueError("rounds must be at least 3 for three regimes")
    rng = random.Random(seed + 70_000_103)
    # Strategic profiles, not literal allocations. Jitter gives within-regime
    # variation while preserving a clear change in allocation tendencies.
    profiles = (
        (0.55, 0.70, 0.90, 2.80, 4.20),  # late/value-heavy
        (4.20, 2.80, 0.90, 0.70, 0.55),  # early-heavy
        (0.65, 2.50, 4.10, 1.80, 0.65),  # middle-heavy
    )
    trace: list[Allocation] = []
    labels: list[int] = []
    for t in range(rounds):
        regime = min(2, (3 * t) // rounds)
        base = profiles[regime]
        weights = [w * rng.uniform(0.80, 1.20) for w in base]
        # Inline the same largest-remainder allocation rule used by agents, to
        # keep the replay generator independent of any evaluated policy.
        total_w = sum(weights)
        raw = [game.troops * w / total_w for w in weights]
        alloc = [int(x) for x in raw]
        remainder = game.troops - sum(alloc)
        order = sorted(range(game.battlefields), key=lambda i: raw[i] - alloc[i], reverse=True)
        for i in order[:remainder]:
            alloc[i] += 1
        action = tuple(alloc)
        game.validate(action)
        trace.append(action)
        labels.append(regime)
    return trace, labels


def _window_mean(values: list[float], start: int, stop: int) -> float:
    xs = values[max(0, start):min(len(values), stop)]
    return sum(xs) / len(xs) if xs else 0.0


def _run_replay_detailed(agent, opponent_trace: list[Allocation], *, seed: int, game: BlottoGame) -> dict:
    rng = random.Random(seed + 90_000_119)
    observed: list[Allocation] = []
    actions: list[Allocation] = []
    payoffs: list[float] = []
    for b in opponent_trace:
        a = agent.act(game, observed, rng)
        payoffs.append(game.payoff(a, b))
        actions.append(a)
        observed.append(b)
    return {"actions": actions, "payoffs": payoffs}


def run_control_regime_switching(rounds: int = 300, seeds: int = 32, adaptation_window: int = 16) -> dict:
    """Falsify whether Control's advantage depends on recency under regime shifts.

    Primary prediction: destroying temporal order eliminates at least half of
    true-history Control's payoff gain over Baseline. Secondary prediction:
    true-history Control outperforms shuffled-history Control in the
    prespecified post-switch adaptation window, where recent information should matter most.
    """
    if adaptation_window <= 0:
        raise ValueError("adaptation_window must be positive")
    game = BlottoGame()
    agents = [ValueBaseline(), ShuffledHistoryControl(), ControlAgent()]
    seed_rows: list[dict] = []
    switches = sorted(set((rounds // 3, (2 * rounds) // 3)))

    for seed in range(seeds):
        trace, labels = generate_regime_switching_replay(rounds=rounds, seed=seed, game=game)
        details = {a.name: _run_replay_detailed(a, trace, seed=seed, game=game) for a in agents}
        row = {"seed": seed, "regime_labels": labels}
        for name, d in details.items():
            ps = d["payoffs"]
            diagnostic_windows = sorted(set([4, 8, adaptation_window, 32]))
            row[name] = {
                "mean_payoff": sum(ps) / len(ps),
                "win_rate": sum(1 for x in ps if x > 0) / len(ps),
                "post_switch_mean_payoff": sum(
                    _window_mean(ps, sw, sw + adaptation_window) for sw in switches
                ) / len(switches),
                "post_switch_window_diagnostics": {
                    str(width): sum(_window_mean(ps, sw, sw + width) for sw in switches) / len(switches)
                    for width in diagnostic_windows
                },
            }
        seed_rows.append(row)

    def mean_metric(agent_name: str, metric: str) -> float:
        return sum(r[agent_name][metric] for r in seed_rows) / seeds

    baseline = mean_metric("baseline", "mean_payoff")
    shuffled = mean_metric("control_shuffled_history", "mean_payoff")
    true = mean_metric("control", "mean_payoff")
    true_gain = true - baseline
    shuffled_gain = shuffled - baseline
    collapsed = (1.0 - shuffled_gain / true_gain) if true_gain > 0 else None

    baseline_post = mean_metric("baseline", "post_switch_mean_payoff")
    shuffled_post = mean_metric("control_shuffled_history", "post_switch_mean_payoff")
    true_post = mean_metric("control", "post_switch_mean_payoff")
    diagnostic_windows = sorted(set([4, 8, adaptation_window, 32]))
    window_diagnostics = {}
    for width in diagnostic_windows:
        key = str(width)
        means = {}
        for agent_name in ("baseline", "control_shuffled_history", "control"):
            means[agent_name] = sum(
                r[agent_name]["post_switch_window_diagnostics"][key] for r in seed_rows
            ) / seeds
        means["true_minus_shuffled"] = means["control"] - means["control_shuffled_history"]
        means["true_minus_baseline"] = means["control"] - means["baseline"]
        window_diagnostics[key] = means

    return {
        "schema": "pcc-colonel-blotto-control-regime-switching-v0.3",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_seed": rounds,
            "seeds": seeds,
            "regimes": 3,
            "switch_rounds": switches,
            "adaptation_window": adaptation_window,
            "opponent_trace": "exogenous three-regime allocation process replayed identically across conditions",
            "ablation": "shuffle complete observed opponent history before Control, preserving history multiset while destroying recency",
            "primary_threshold": "at least 50% of true Control payoff gain over Baseline is eliminated",
        },
        "aggregate": {
            "baseline_mean_payoff": baseline,
            "shuffled_control_mean_payoff": shuffled,
            "true_control_mean_payoff": true,
            "true_control_gain_over_baseline": true_gain,
            "shuffled_control_gain_over_baseline": shuffled_gain,
            "fraction_control_gain_eliminated_after_shuffle": collapsed,
            "baseline_post_switch_mean_payoff": baseline_post,
            "shuffled_control_post_switch_mean_payoff": shuffled_post,
            "true_control_post_switch_mean_payoff": true_post,
            "post_switch_true_minus_shuffled": true_post - shuffled_post,
            "baseline_win_rate": mean_metric("baseline", "win_rate"),
            "shuffled_control_win_rate": mean_metric("control_shuffled_history", "win_rate"),
            "true_control_win_rate": mean_metric("control", "win_rate"),
            "post_switch_window_diagnostics": window_diagnostics,
        },
        "prespecified_checks": {
            "true_control_beats_baseline": {"pass": true_gain > 0.0, "gain": true_gain},
            "history_shuffle_hurts_control": {"pass": shuffled < true, "delta_shuffled_minus_true": shuffled - true},
            "history_shuffle_eliminates_at_least_half_control_gain": {
                "pass": bool(true_gain > 0.0 and collapsed is not None and collapsed >= 0.5),
                "fraction_eliminated": collapsed,
                "threshold": 0.5,
            },
            "true_control_beats_shuffled_in_prespecified_16_round_window": {
                "pass": true_post > shuffled_post,
                "delta_true_minus_shuffled": true_post - shuffled_post,
            },
        },
        "seed_results": seed_rows,
        "claim_scope": "paired replay recency falsification under nonstationarity; not closed-loop construct recovery",
    }


def write_control_regime_switching(output_dir: str | Path, rounds: int = 300, seeds: int = 32, adaptation_window: int = 16) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_control_regime_switching(rounds=rounds, seeds=seeds, adaptation_window=adaptation_window)
    (out / "control-regime-switching.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    a = result["aggregate"]
    checks = result["prespecified_checks"]
    frac = a["fraction_control_gain_eliminated_after_shuffle"]
    lines = [
        "# Control Regime-Switching Falsification",
        "",
        "This paired replay experiment asks whether Control uses **recent** opponent information when the allocation process is nonstationary.",
        "",
        "The opponent passes through three exogenous regimes that emphasize different battlefield subsets. Every evaluated policy faces the identical realized trace.",
        "",
        "## Prespecified predictions",
        "",
        "1. Destroying temporal order eliminates at least **50%** of true-history Control's payoff gain over Baseline.",
        "2. True-history Control beats shuffled-history Control in the immediate post-switch adaptation windows.",
        "",
        "## Aggregate result",
        "",
        "| condition | mean payoff | post-switch payoff | win rate |",
        "|---|---:|---:|---:|",
        f"| Baseline | {a['baseline_mean_payoff']:.4f} | {a['baseline_post_switch_mean_payoff']:.4f} | {a['baseline_win_rate']:.3f} |",
        f"| Shuffled-history Control | {a['shuffled_control_mean_payoff']:.4f} | {a['shuffled_control_post_switch_mean_payoff']:.4f} | {a['shuffled_control_win_rate']:.3f} |",
        f"| True-history Control | {a['true_control_mean_payoff']:.4f} | {a['true_control_post_switch_mean_payoff']:.4f} | {a['true_control_win_rate']:.3f} |",
        "",
        f"Fraction of Control gain eliminated by shuffling: **{frac:.1%}**" if frac is not None else "Fraction eliminated: **undefined**",
        "",
        f"Post-switch true minus shuffled payoff: **{a['post_switch_true_minus_shuffled']:.4f}**",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in checks.items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        "## Interpretation guardrail",
        "",
        "This test establishes or falsifies recency-sensitive information use for the current Control policy under a deliberately nonstationary environment. It does not by itself establish observational PCC construct recovery.",
    ]
    (out / "CONTROL_REGIME_SWITCHING.md").write_text("\n".join(lines) + "\n")
    return result
