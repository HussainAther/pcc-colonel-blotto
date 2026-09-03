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
    ChangePointControl,
    ExponentialDecayControl,
    FullHistoryControl,
    SlidingWindowControl,
    PressureAgent,
    ShuffledHistoryControl,
    StaticWeightedOpponent,
    ValueBaseline,
)
from .game import Allocation, BlottoGame, compositions


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


def _prediction_l1(agent, history: list[Allocation], target: Allocation, game: BlottoGame) -> float | None:
    estimate_fn = getattr(agent, "estimate", None)
    if estimate_fn is None or not history:
        return None
    estimate = estimate_fn(game, history)
    return sum(abs(estimate[i] - target[i]) for i in range(game.battlefields)) / game.troops


def _run_estimator_replay(agent, opponent_trace: list[Allocation], *, seed: int, game: BlottoGame) -> dict:
    rng = random.Random(seed + 120_000_151)
    history: list[Allocation] = []
    payoffs: list[float] = []
    prediction_errors: list[float] = []
    for target in opponent_trace:
        err = _prediction_l1(agent, history, target, game)
        if err is not None:
            prediction_errors.append(err)
        action = agent.act(game, history, rng)
        payoffs.append(game.payoff(action, target))
        history.append(target)
    return {
        "payoffs": payoffs,
        "mean_payoff": sum(payoffs) / len(payoffs),
        "win_rate": sum(1 for x in payoffs if x > 0) / len(payoffs),
        "prediction_l1": sum(prediction_errors) / len(prediction_errors) if prediction_errors else None,
    }


def run_control_estimator_ablation(rounds: int = 300, seeds: int = 32, adaptation_window: int = 16) -> dict:
    """Compare alternative Control estimators on frozen nonstationary traces."""
    if adaptation_window <= 0:
        raise ValueError("adaptation_window must be positive")
    game = BlottoGame()
    agents = [
        ValueBaseline(),
        FullHistoryControl(),
        SlidingWindowControl(lookback=8),
        ExponentialDecayControl(alpha=0.35),
        ChangePointControl(window=8, threshold=4.0),
    ]
    switches = sorted(set((rounds // 3, (2 * rounds) // 3)))
    widths = sorted(set([4, 8, adaptation_window, 32]))
    seed_rows: list[dict] = []

    for seed in range(seeds):
        trace, labels = generate_regime_switching_replay(rounds=rounds, seed=seed, game=game)
        row = {"seed": seed, "regime_labels": labels}
        for agent in agents:
            d = _run_estimator_replay(agent, trace, seed=seed, game=game)
            ps = d["payoffs"]
            row[agent.name] = {
                "mean_payoff": d["mean_payoff"],
                "win_rate": d["win_rate"],
                "prediction_l1": d["prediction_l1"],
                "post_switch_mean_payoff": sum(_window_mean(ps, sw, sw + adaptation_window) for sw in switches) / len(switches),
                "post_switch_window_diagnostics": {
                    str(width): sum(_window_mean(ps, sw, sw + width) for sw in switches) / len(switches)
                    for width in widths
                },
            }
        seed_rows.append(row)

    names = [a.name for a in agents]
    def mean_metric(name: str, metric: str) -> float:
        vals = [r[name][metric] for r in seed_rows if r[name][metric] is not None]
        return sum(vals) / len(vals)

    aggregate = {}
    for name in names:
        aggregate[name] = {
            "mean_payoff": mean_metric(name, "mean_payoff"),
            "win_rate": mean_metric(name, "win_rate"),
            "prediction_l1": None if name == "baseline" else mean_metric(name, "prediction_l1"),
            "post_switch_mean_payoff": mean_metric(name, "post_switch_mean_payoff"),
            "post_switch_window_diagnostics": {
                str(width): sum(r[name]["post_switch_window_diagnostics"][str(width)] for r in seed_rows) / seeds
                for width in widths
            },
        }

    full = aggregate["control_full_history"]
    candidates = ["control_sliding_window", "control_exponential_decay", "control_change_point"]
    best_post = max(candidates, key=lambda n: aggregate[n]["post_switch_mean_payoff"])
    best_overall = max(candidates, key=lambda n: aggregate[n]["mean_payoff"])
    meaningful_margin = 0.02
    maintenance_tolerance = 0.02
    qualifies = []
    for name in candidates:
        post_gain = aggregate[name]["post_switch_mean_payoff"] - full["post_switch_mean_payoff"]
        overall_delta = aggregate[name]["mean_payoff"] - full["mean_payoff"]
        if post_gain >= meaningful_margin and overall_delta >= -maintenance_tolerance:
            qualifies.append(name)

    return {
        "schema": "pcc-colonel-blotto-control-estimator-ablation-v0.4",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_seed": rounds,
            "seeds": seeds,
            "regimes": 3,
            "switch_rounds": switches,
            "adaptation_window": adaptation_window,
            "opponent_trace": "same frozen exogenous three-regime generator as v0.3; replayed identically across estimators",
            "estimators": {
                "control_full_history": "mean of all prior opponent allocations",
                "control_sliding_window": "mean of last 8 allocations",
                "control_exponential_decay": "EWMA with alpha=0.35",
                "control_change_point": "L1 two-window shift detector; window=8, threshold=4 troops; reset to most recent detected segment",
            },
            "prespecified_success_rule": "at least one recency-aware estimator improves 16-round post-switch payoff over full-history by >=0.02 while overall payoff is no worse by more than 0.02",
        },
        "aggregate": aggregate,
        "best_recency_estimator_post_switch": best_post,
        "best_recency_estimator_overall": best_overall,
        "qualifying_estimators": qualifies,
        "prespecified_checks": {
            "at_least_one_recency_estimator_improves_post_switch_without_material_overall_loss": {
                "pass": bool(qualifies),
                "qualifying_estimators": qualifies,
                "post_switch_margin": meaningful_margin,
                "overall_loss_tolerance": maintenance_tolerance,
            },
            "best_recency_estimator_beats_full_history_post_switch": {
                "pass": aggregate[best_post]["post_switch_mean_payoff"] > full["post_switch_mean_payoff"],
                "best": best_post,
                "delta": aggregate[best_post]["post_switch_mean_payoff"] - full["post_switch_mean_payoff"],
            },
        },
        "seed_results": seed_rows,
        "claim_scope": "Control-estimator mechanism ablation under fixed nonstationary replay; not observational construct recovery",
    }


def write_control_estimator_ablation(output_dir: str | Path, rounds: int = 300, seeds: int = 32, adaptation_window: int = 16) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_control_estimator_ablation(rounds=rounds, seeds=seeds, adaptation_window=adaptation_window)
    (out / "control-estimator-ablation.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    a = result["aggregate"]
    order = ["baseline", "control_full_history", "control_sliding_window", "control_exponential_decay", "control_change_point"]
    labels = {
        "baseline": "Baseline",
        "control_full_history": "Full-history Control",
        "control_sliding_window": "Sliding-window Control",
        "control_exponential_decay": "Exponential-decay Control",
        "control_change_point": "Change-point Control",
    }
    lines = [
        "# Control Estimator Ablation",
        "",
        "This v0.4 experiment holds the regime-switching environment fixed and makes the **history estimator itself** the experimental object.",
        "",
        "## Prespecified success rule",
        "",
        "At least one explicitly recency-aware estimator must improve 16-round post-switch payoff over full-history Control by **>=0.02**, while losing no more than **0.02** in overall mean payoff.",
        "",
        "| policy | mean payoff | post-switch payoff | prediction L1 | win rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in order:
        d = a[name]
        pred = "-" if d["prediction_l1"] is None else f"{d['prediction_l1']:.4f}"
        lines.append(f"| {labels[name]} | {d['mean_payoff']:.4f} | {d['post_switch_mean_payoff']:.4f} | {pred} | {d['win_rate']:.3f} |")
    lines += [
        "",
        f"Best recency estimator post-switch: **{result['best_recency_estimator_post_switch']}**",
        "",
        f"Best recency estimator overall: **{result['best_recency_estimator_overall']}**",
        "",
        "Qualifying estimators: **" + (", ".join(result["qualifying_estimators"]) if result["qualifying_estimators"] else "none") + "**",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        "## Interpretation guardrail",
        "",
        "This experiment identifies whether recency-aware belief estimation improves engineered Control under fixed nonstationarity. It does not establish that the selected estimator is universally optimal or that observational PCC recovery has been achieved.",
    ]
    (out / "CONTROL_ESTIMATOR_ABLATION.md").write_text("\n".join(lines) + "\n")
    return result


PRESSURE_MATCH_SEED = 20260903
PRESSURE_REFERENCE_SAMPLES = 2048
PRESSURE_LOW_MAX_CONCENTRATION = 0.40
PRESSURE_HIGH_MIN_CONCENTRATION = 0.50
PRESSURE_VALUE_TOLERANCE = 0.01
PRESSURE_MIN_RELATIVE_CONSTRICTION = 0.05


def _pressure_reference_trace(game: BlottoGame, samples: int = PRESSURE_REFERENCE_SAMPLES) -> list[Allocation]:
    """Frozen policy-independent opponent distribution for strategic-value matching."""
    rng = random.Random(PRESSURE_MATCH_SEED)
    opponent = StaticWeightedOpponent()
    return [opponent.act(game, [], rng) for _ in range(samples)]


def _expected_payoff_against_trace(game: BlottoGame, allocation: Allocation, trace: list[Allocation]) -> float:
    return sum(game.payoff(allocation, b) for b in trace) / len(trace)


def _match_pressure_pairs(game: BlottoGame) -> tuple[list[dict], dict]:
    """Match low- and high-concentration allocations on expected strategic value.

    The match is deterministic and without replacement. High-concentration actions
    are traversed by expected value, and each is paired to the remaining eligible
    low-concentration action with the smallest absolute expected-payoff gap.
    """
    universe = compositions(game.troops, game.battlefields)
    reference = _pressure_reference_trace(game)
    expected_value = {
        a: _expected_payoff_against_trace(game, a, reference)
        for a in universe
    }
    low = [a for a in universe if concentration(a) <= PRESSURE_LOW_MAX_CONCENTRATION]
    high = [a for a in universe if concentration(a) >= PRESSURE_HIGH_MIN_CONCENTRATION]
    available_low = set(low)
    pairs: list[dict] = []
    for high_action in sorted(high, key=lambda a: (expected_value[a], a)):
        candidates = [
            a for a in available_low
            if abs(expected_value[a] - expected_value[high_action]) <= PRESSURE_VALUE_TOLERANCE
        ]
        if not candidates:
            continue
        low_action = min(
            candidates,
            key=lambda a: (abs(expected_value[a] - expected_value[high_action]), a),
        )
        available_low.remove(low_action)
        pairs.append({
            "low_allocation": list(low_action),
            "high_allocation": list(high_action),
            "low_concentration": concentration(low_action),
            "high_concentration": concentration(high_action),
            "concentration_delta": concentration(high_action) - concentration(low_action),
            "low_expected_payoff": expected_value[low_action],
            "high_expected_payoff": expected_value[high_action],
            "absolute_value_gap": abs(expected_value[high_action] - expected_value[low_action]),
            "low_viable_responses": None,
            "high_viable_responses": None,
            "viable_response_delta_high_minus_low": None,
        })
    for p in pairs:
        low_action = tuple(p["low_allocation"])
        high_action = tuple(p["high_allocation"])
        low_viable = game.viable_responses(low_action)
        high_viable = game.viable_responses(high_action)
        p["low_viable_responses"] = low_viable
        p["high_viable_responses"] = high_viable
        p["viable_response_delta_high_minus_low"] = high_viable - low_viable
    meta = {
        "legal_allocations": len(universe),
        "reference_samples": len(reference),
        "low_candidates": len(low),
        "high_candidates": len(high),
    }
    return pairs, meta


def run_pressure_matched_intervention() -> dict:
    """v0.5 causal probe: manipulate concentration while matching strategic value."""
    game = BlottoGame()
    pairs, meta = _match_pressure_pairs(game)
    if not pairs:
        raise RuntimeError("pressure matching produced no pairs")
    n = len(pairs)
    mean_low_value = sum(p["low_expected_payoff"] for p in pairs) / n
    mean_high_value = sum(p["high_expected_payoff"] for p in pairs) / n
    mean_abs_value_gap = sum(p["absolute_value_gap"] for p in pairs) / n
    max_abs_value_gap = max(p["absolute_value_gap"] for p in pairs)
    mean_low_conc = sum(p["low_concentration"] for p in pairs) / n
    mean_high_conc = sum(p["high_concentration"] for p in pairs) / n
    mean_low_viable = sum(p["low_viable_responses"] for p in pairs) / n
    mean_high_viable = sum(p["high_viable_responses"] for p in pairs) / n
    mean_delta = mean_high_viable - mean_low_viable
    relative_reduction = (mean_low_viable - mean_high_viable) / mean_low_viable if mean_low_viable else None
    pairwise_reduction_rate = sum(
        p["high_viable_responses"] < p["low_viable_responses"] for p in pairs
    ) / n
    return {
        "schema": "pcc-colonel-blotto-pressure-matched-intervention-v0.5",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            **meta,
            "reference_distribution": "StaticWeightedOpponent sampled with frozen seed; independent of evaluated allocations",
            "reference_seed": PRESSURE_MATCH_SEED,
            "low_concentration_max": PRESSURE_LOW_MAX_CONCENTRATION,
            "high_concentration_min": PRESSURE_HIGH_MIN_CONCENTRATION,
            "strategic_value_match_tolerance": PRESSURE_VALUE_TOLERANCE,
            "matching": "deterministic nearest expected-payoff match without replacement",
            "primary_prediction": "high concentration reduces mean opponent viable responses by at least 5%",
            "primary_threshold": PRESSURE_MIN_RELATIVE_CONSTRICTION,
        },
        "aggregate": {
            "matched_pairs": n,
            "mean_low_expected_payoff": mean_low_value,
            "mean_high_expected_payoff": mean_high_value,
            "mean_absolute_value_gap": mean_abs_value_gap,
            "max_absolute_value_gap": max_abs_value_gap,
            "mean_low_concentration": mean_low_conc,
            "mean_high_concentration": mean_high_conc,
            "mean_concentration_delta": mean_high_conc - mean_low_conc,
            "mean_low_viable_responses": mean_low_viable,
            "mean_high_viable_responses": mean_high_viable,
            "mean_viable_response_delta_high_minus_low": mean_delta,
            "relative_viable_response_reduction": relative_reduction,
            "pairwise_reduction_rate": pairwise_reduction_rate,
        },
        "prespecified_checks": {
            "exact_troop_budget_preserved": {"pass": all(sum(p["low_allocation"]) == game.troops and sum(p["high_allocation"]) == game.troops for p in pairs)},
            "strategic_value_matched_within_tolerance": {"pass": max_abs_value_gap <= PRESSURE_VALUE_TOLERANCE + 1e-12, "max_gap": max_abs_value_gap, "tolerance": PRESSURE_VALUE_TOLERANCE},
            "concentration_manipulation_succeeded": {"pass": mean_high_conc > mean_low_conc, "delta": mean_high_conc - mean_low_conc},
            "pressure_constricts_viable_responses_by_at_least_5_percent": {
                "pass": bool(relative_reduction is not None and relative_reduction >= PRESSURE_MIN_RELATIVE_CONSTRICTION),
                "relative_reduction": relative_reduction,
                "threshold": PRESSURE_MIN_RELATIVE_CONSTRICTION,
            },
        },
        "pairs": pairs,
        "claim_scope": "matched synthetic causal probe of raw allocation concentration; not a general Pressure construct claim",
    }


def write_pressure_matched_intervention(output_dir: str | Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_pressure_matched_intervention()
    (out / "pressure-matched-intervention.json").write_text(json.dumps(result, indent=2) + "\n")
    a = result["aggregate"]
    lines = [
        "# PCC Colonel Blotto v0.5 Pressure Matched Intervention",
        "",
        "This experiment holds troop budget exactly fixed and matches low- versus high-concentration allocations on expected strategic value against one frozen, policy-independent opponent distribution.",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        "## Aggregate result",
        "",
        f"- Matched pairs: **{a['matched_pairs']}**",
        f"- Mean absolute strategic-value gap: **{a['mean_absolute_value_gap']:.6f}**",
        f"- Mean concentration: **{a['mean_low_concentration']:.4f} -> {a['mean_high_concentration']:.4f}**",
        f"- Mean viable responses: **{a['mean_low_viable_responses']:.2f} -> {a['mean_high_viable_responses']:.2f}**",
        f"- Relative viable-response reduction: **{a['relative_viable_response_reduction']:.2%}**",
        f"- Pairwise fraction with fewer viable responses under high concentration: **{a['pairwise_reduction_rate']:.2%}**",
        "",
        "## Interpretation guardrail",
        "",
        "This isolates **raw allocation concentration**, not the full engineered Pressure policy. If the primary prediction fails, concentration by itself should not be treated as a substrate-general Pressure mechanism; battlefield targeting, leverage, or value-weighted commitment may be necessary parts of the construct.",
    ]
    (out / "PRESSURE_MATCHED_INTERVENTION.md").write_text("\n".join(lines) + "\n")
    return result

PRESSURE_LEVERAGE_LOW_MAX = 0.40
PRESSURE_LEVERAGE_HIGH_MIN = 0.60
PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE = 0.05
PRESSURE_LEVERAGE_MIN_RELATIVE_CONSTRICTION = 0.10


def leverage_targeting(game: BlottoGame, allocation: Allocation) -> float:
    """Troop-mass targeting toward high-value battlefields, scaled to [0, 1]."""
    lo, hi = min(game.values), max(game.values)
    if hi == lo:
        return 0.0
    normalized = [(v - lo) / (hi - lo) for v in game.values]
    return sum(x * w for x, w in zip(allocation, normalized)) / game.troops


def _match_pressure_leverage_pairs(game: BlottoGame) -> tuple[list[dict], dict]:
    """Match low/high leverage-targeting actions on payoff and concentration."""
    universe = compositions(game.troops, game.battlefields)
    reference = _pressure_reference_trace(game)
    expected_value = {a: _expected_payoff_against_trace(game, a, reference) for a in universe}
    leverage = {a: leverage_targeting(game, a) for a in universe}
    conc = {a: concentration(a) for a in universe}
    low = [a for a in universe if leverage[a] <= PRESSURE_LEVERAGE_LOW_MAX]
    high = [a for a in universe if leverage[a] >= PRESSURE_LEVERAGE_HIGH_MIN]
    available_low = set(low)
    pairs: list[dict] = []
    for high_action in sorted(high, key=lambda a: (expected_value[a], conc[a], a)):
        candidates = [
            a for a in available_low
            if abs(expected_value[a] - expected_value[high_action]) <= PRESSURE_VALUE_TOLERANCE
            and abs(conc[a] - conc[high_action]) <= PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE
        ]
        if not candidates:
            continue
        low_action = min(
            candidates,
            key=lambda a: (
                abs(expected_value[a] - expected_value[high_action]),
                abs(conc[a] - conc[high_action]),
                a,
            ),
        )
        available_low.remove(low_action)
        pairs.append({
            "low_leverage_allocation": list(low_action),
            "high_leverage_allocation": list(high_action),
            "low_leverage": leverage[low_action],
            "high_leverage": leverage[high_action],
            "leverage_delta": leverage[high_action] - leverage[low_action],
            "low_concentration": conc[low_action],
            "high_concentration": conc[high_action],
            "absolute_concentration_gap": abs(conc[high_action] - conc[low_action]),
            "low_expected_payoff": expected_value[low_action],
            "high_expected_payoff": expected_value[high_action],
            "absolute_value_gap": abs(expected_value[high_action] - expected_value[low_action]),
            "low_viable_responses": None,
            "high_viable_responses": None,
            "viable_response_delta_high_minus_low": None,
        })
    for p in pairs:
        low_action = tuple(p["low_leverage_allocation"])
        high_action = tuple(p["high_leverage_allocation"])
        low_viable = game.viable_responses(low_action)
        high_viable = game.viable_responses(high_action)
        p["low_viable_responses"] = low_viable
        p["high_viable_responses"] = high_viable
        p["viable_response_delta_high_minus_low"] = high_viable - low_viable
    return pairs, {
        "legal_allocations": len(universe),
        "reference_samples": len(reference),
        "low_leverage_candidates": len(low),
        "high_leverage_candidates": len(high),
    }


def run_pressure_leverage_intervention() -> dict:
    """v0.6 causal probe: manipulate targeting leverage while matching value/concentration."""
    game = BlottoGame()
    pairs, meta = _match_pressure_leverage_pairs(game)
    if not pairs:
        raise RuntimeError("pressure leverage matching produced no pairs")
    n = len(pairs)
    mean = lambda key: sum(p[key] for p in pairs) / n
    low_viable = mean("low_viable_responses")
    high_viable = mean("high_viable_responses")
    relative_reduction = (low_viable - high_viable) / low_viable if low_viable else None
    pairwise_reduction_rate = sum(p["high_viable_responses"] < p["low_viable_responses"] for p in pairs) / n
    max_value_gap = max(p["absolute_value_gap"] for p in pairs)
    max_conc_gap = max(p["absolute_concentration_gap"] for p in pairs)
    return {
        "schema": "pcc-colonel-blotto-pressure-leverage-intervention-v0.6",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            **meta,
            "reference_distribution": "StaticWeightedOpponent sampled with frozen v0.5 seed; independent of evaluated allocations",
            "reference_seed": PRESSURE_MATCH_SEED,
            "low_leverage_max": PRESSURE_LEVERAGE_LOW_MAX,
            "high_leverage_min": PRESSURE_LEVERAGE_HIGH_MIN,
            "strategic_value_match_tolerance": PRESSURE_VALUE_TOLERANCE,
            "concentration_match_tolerance": PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE,
            "leverage_definition": "troop-weighted normalized battlefield value: min-value field=0, max-value field=1",
            "matching": "deterministic nearest expected-payoff then concentration match without replacement",
            "primary_prediction": "high-leverage targeting reduces mean opponent viable responses by at least 10%",
            "primary_threshold": PRESSURE_LEVERAGE_MIN_RELATIVE_CONSTRICTION,
        },
        "aggregate": {
            "matched_pairs": n,
            "mean_low_expected_payoff": mean("low_expected_payoff"),
            "mean_high_expected_payoff": mean("high_expected_payoff"),
            "mean_absolute_value_gap": mean("absolute_value_gap"),
            "max_absolute_value_gap": max_value_gap,
            "mean_low_concentration": mean("low_concentration"),
            "mean_high_concentration": mean("high_concentration"),
            "mean_absolute_concentration_gap": mean("absolute_concentration_gap"),
            "max_absolute_concentration_gap": max_conc_gap,
            "mean_low_leverage": mean("low_leverage"),
            "mean_high_leverage": mean("high_leverage"),
            "mean_leverage_delta": mean("leverage_delta"),
            "mean_low_viable_responses": low_viable,
            "mean_high_viable_responses": high_viable,
            "relative_viable_response_reduction": relative_reduction,
            "pairwise_reduction_rate": pairwise_reduction_rate,
        },
        "prespecified_checks": {
            "exact_troop_budget_preserved": {"pass": all(sum(p["low_leverage_allocation"]) == game.troops and sum(p["high_leverage_allocation"]) == game.troops for p in pairs)},
            "strategic_value_matched_within_tolerance": {"pass": max_value_gap <= PRESSURE_VALUE_TOLERANCE + 1e-12, "max_gap": max_value_gap, "tolerance": PRESSURE_VALUE_TOLERANCE},
            "concentration_matched_within_tolerance": {"pass": max_conc_gap <= PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE + 1e-12, "max_gap": max_conc_gap, "tolerance": PRESSURE_LEVERAGE_CONCENTRATION_TOLERANCE},
            "leverage_targeting_manipulation_succeeded": {"pass": mean("high_leverage") > mean("low_leverage"), "delta": mean("high_leverage") - mean("low_leverage")},
            "targeted_pressure_constricts_viable_responses_by_at_least_10_percent": {"pass": bool(relative_reduction is not None and relative_reduction >= PRESSURE_LEVERAGE_MIN_RELATIVE_CONSTRICTION), "relative_reduction": relative_reduction, "threshold": PRESSURE_LEVERAGE_MIN_RELATIVE_CONSTRICTION},
        },
        "pairs": pairs,
        "claim_scope": "matched synthetic causal probe of value-targeted commitment; not a substrate-general Pressure construct claim",
    }


def write_pressure_leverage_intervention(output_dir: str | Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_pressure_leverage_intervention()
    (out / "pressure-leverage-intervention.json").write_text(json.dumps(result, indent=2) + "\n")
    a = result["aggregate"]
    lines = [
        "# PCC Colonel Blotto v0.6 Targeted-Leverage Pressure Intervention",
        "",
        "This experiment holds troop budget exactly fixed and approximately matches both expected strategic value and raw allocation concentration while manipulating **where troop mass is targeted** across battlefield values.",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        "## Aggregate result",
        "",
        f"- Matched pairs: **{a['matched_pairs']}**",
        f"- Mean absolute strategic-value gap: **{a['mean_absolute_value_gap']:.6f}**",
        f"- Mean concentration: **{a['mean_low_concentration']:.4f} -> {a['mean_high_concentration']:.4f}**",
        f"- Mean leverage targeting: **{a['mean_low_leverage']:.4f} -> {a['mean_high_leverage']:.4f}**",
        f"- Mean viable responses: **{a['mean_low_viable_responses']:.2f} -> {a['mean_high_viable_responses']:.2f}**",
        f"- Relative viable-response reduction: **{a['relative_viable_response_reduction']:.2%}**",
        f"- Pairwise fraction with fewer viable responses under high leverage: **{a['pairwise_reduction_rate']:.2%}**",
        "",
        "## Interpretation guardrail",
        "",
        "A positive result supports **value-targeted commitment** as a candidate Blotto Pressure mechanism after raw concentration failed in v0.5. It does not establish that battlefield value is the only relevant form of leverage, nor that the result generalizes beyond this Blotto parameterization.",
    ]
    (out / "PRESSURE_LEVERAGE_INTERVENTION.md").write_text("\n".join(lines) + "\n")
    return result
