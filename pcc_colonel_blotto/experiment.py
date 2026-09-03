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
    UniformRandomAgent,
    MeanProfileExploiter,
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


CHAOS_EXPLOITER_ROUNDS = 200
CHAOS_EXPLOITER_SEEDS = 24
CHAOS_MIN_ENTROPY_RATIO = 0.80
CHAOS_MIN_VALUE_ADVANTAGE = 0.05


def run_chaos_exploiter_falsification(
    rounds: int = CHAOS_EXPLOITER_ROUNDS,
    seeds: int = CHAOS_EXPLOITER_SEEDS,
) -> dict:
    """v0.7: separate raw entropy from strategically guarded unpredictability."""
    game = BlottoGame()
    agents = [ValueBaseline(), UniformRandomAgent(), ChaosAgent()]
    opponents = [StaticWeightedOpponent(), MeanProfileExploiter()]
    rows: list[dict] = []
    for agent in agents:
        for opponent in opponents:
            summaries = [
                run_match(agent, opponent, rounds=rounds, seed=s, game=game)
                for s in range(seeds)
            ]
            rows.append({
                "agent": agent.name,
                "opponent": opponent.name,
                "rounds_per_seed": rounds,
                "seeds": seeds,
                "mean_payoff": sum(x.mean_payoff for x in summaries) / seeds,
                "win_rate": sum(x.win_rate for x in summaries) / seeds,
                "allocation_entropy": sum(x.allocation_entropy for x in summaries) / seeds,
                "mean_concentration": sum(x.mean_concentration for x in summaries) / seeds,
            })

    by_key = {(r["agent"], r["opponent"]): r for r in rows}
    policies = ("baseline", "uniform_random", "chaos")
    exploit_penalty = {
        p: by_key[(p, "static_weighted")]["mean_payoff"]
        - by_key[(p, "mean_profile_exploiter")]["mean_payoff"]
        for p in policies
    }
    chaos_entropy = by_key[("chaos", "mean_profile_exploiter")]["allocation_entropy"]
    random_entropy = by_key[("uniform_random", "mean_profile_exploiter")]["allocation_entropy"]
    entropy_ratio = chaos_entropy / random_entropy if random_entropy else None
    chaos_exploiter_payoff = by_key[("chaos", "mean_profile_exploiter")]["mean_payoff"]
    random_exploiter_payoff = by_key[("uniform_random", "mean_profile_exploiter")]["mean_payoff"]
    value_advantage = chaos_exploiter_payoff - random_exploiter_payoff

    checks = {
        "guarded_chaos_retains_at_least_80_percent_random_entropy": {
            "pass": bool(entropy_ratio is not None and entropy_ratio >= CHAOS_MIN_ENTROPY_RATIO),
            "entropy_ratio": entropy_ratio,
            "threshold": CHAOS_MIN_ENTROPY_RATIO,
        },
        "guarded_chaos_beats_uniform_random_vs_exploiter_by_at_least_0_05": {
            "pass": value_advantage >= CHAOS_MIN_VALUE_ADVANTAGE,
            "payoff_advantage": value_advantage,
            "threshold": CHAOS_MIN_VALUE_ADVANTAGE,
        },
        "guarded_chaos_exploit_penalty_no_worse_than_predictable_baseline": {
            "pass": exploit_penalty["chaos"] <= exploit_penalty["baseline"],
            "chaos_exploit_penalty": exploit_penalty["chaos"],
            "baseline_exploit_penalty": exploit_penalty["baseline"],
        },
    }
    return {
        "schema": "pcc-colonel-blotto-chaos-exploiter-falsification-v0.7",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_seed": rounds,
            "seeds": seeds,
            "paired_seeds": True,
            "held_out_exploiter": "MeanProfileExploiter(lookback=12), exact best response to recent mean-profile prediction",
            "uniform_random_support": len(compositions(game.troops, game.battlefields)),
            "primary_success_rule": "all three prespecified checks must pass",
        },
        "results": rows,
        "aggregate": {
            "chaos_entropy_ratio_vs_uniform_random": entropy_ratio,
            "chaos_payoff_advantage_over_uniform_random_vs_exploiter": value_advantage,
            "exploit_penalty": exploit_penalty,
            "all_primary_checks_pass": all(x["pass"] for x in checks.values()),
        },
        "prespecified_checks": checks,
        "claim_scope": "synthetic held-out-exploiter falsification of guarded unpredictability; not observational construct recovery",
    }


def write_chaos_exploiter_falsification(
    output_dir: str | Path,
    rounds: int = CHAOS_EXPLOITER_ROUNDS,
    seeds: int = CHAOS_EXPLOITER_SEEDS,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_chaos_exploiter_falsification(rounds=rounds, seeds=seeds)
    (out / "chaos-exploiter-falsification.json").write_text(json.dumps(result, indent=2) + "\n")
    by_key = {(r["agent"], r["opponent"]): r for r in result["results"]}
    labels = {"baseline": "Value Baseline", "uniform_random": "Uniform Random", "chaos": "Guarded Chaos"}
    lines = [
        "# PCC Colonel Blotto v0.7 Guarded-Chaos Exploiter Falsification",
        "",
        "This experiment separates raw action entropy from strategically adequate unpredictability using a held-out online learner.",
        "",
        "## Results",
        "",
        "| policy | payoff vs static | payoff vs exploiter | entropy vs exploiter | exploit penalty |",
        "|---|---:|---:|---:|---:|",
    ]
    penalties = result["aggregate"]["exploit_penalty"]
    for p in ("baseline", "uniform_random", "chaos"):
        lines.append(
            f"| {labels[p]} | {by_key[(p, 'static_weighted')]['mean_payoff']:.4f} | "
            f"{by_key[(p, 'mean_profile_exploiter')]['mean_payoff']:.4f} | "
            f"{by_key[(p, 'mean_profile_exploiter')]['allocation_entropy']:.4f} | {penalties[p]:.4f} |"
        )
    lines += [
        "",
        f"Guarded-Chaos entropy / Uniform-Random entropy: **{result['aggregate']['chaos_entropy_ratio_vs_uniform_random']:.1%}**",
        "",
        f"Guarded-Chaos payoff advantage over Uniform Random vs exploiter: **{result['aggregate']['chaos_payoff_advantage_over_uniform_random_vs_exploiter']:+.4f}**",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        f"Overall primary rule: **{'PASS' if result['aggregate']['all_primary_checks_pass'] else 'FAIL'}**",
        "",
        "## Interpretation guardrail",
        "",
        "Passing supports a Blotto mechanism of unpredictability constrained by strategic adequacy. It does not identify entropy itself with Chaos, establish minimax optimality, or establish observational PCC recovery.",
    ]
    (out / "CHAOS_EXPLOITER_FALSIFICATION.md").write_text("\n".join(lines) + "\n")
    return result

# ---------------------------------------------------------------------------
# v0.8 observational latent-mixture recovery
# ---------------------------------------------------------------------------

RECOVERY_ROUNDS = 240
RECOVERY_SEEDS_PER_MIXTURE = 4
RECOVERY_OOD_DOMINANCE = 0.75
RECOVERY_RIDGE = 0.25
RECOVERY_MAX_OOD_MAE = 0.15
RECOVERY_MIN_BASELINE_IMPROVEMENT = 0.25


def _simplex_grid(step: int = 10) -> list[tuple[float, float, float]]:
    """Deterministic simplex lattice with coordinates in multiples of 1/step."""
    return [(i / step, j / step, (step - i - j) / step)
            for i in range(step + 1) for j in range(step + 1 - i)]


def _trajectory_observables(actions: list[Allocation], opponents: list[Allocation], payoffs: list[float], game: BlottoGame) -> dict[str, float]:
    n = len(actions)
    if n == 0:
        raise ValueError("trajectory must contain at least one action")
    feats: dict[str, float] = {
        "mean_payoff": sum(payoffs) / n,
        "win_rate": sum(1 for x in payoffs if x > 0) / n,
        "allocation_entropy": entropy(actions),
        "distinct_action_ratio": len(set(actions)) / n,
        "mean_concentration": sum(concentration(a) for a in actions) / n,
        "mean_leverage_targeting": sum(leverage_targeting(game, a) for a in actions) / n,
        "mean_opponent_viable_responses": sum(game.viable_responses(a) for a in actions) / n,
    }
    if n > 1:
        feats["mean_step_l1"] = sum(
            sum(abs(actions[t][i] - actions[t - 1][i]) for i in range(game.battlefields))
            for t in range(1, n)
        ) / (n - 1)
        feats["repeat_rate"] = sum(actions[t] == actions[t - 1] for t in range(1, n)) / (n - 1)
    else:
        feats["mean_step_l1"] = 0.0
        feats["repeat_rate"] = 0.0
    for i in range(game.battlefields):
        vals = [a[i] for a in actions]
        mean = sum(vals) / n
        feats[f"battlefield_{i}_mean"] = mean
        feats[f"battlefield_{i}_variance"] = sum((x - mean) ** 2 for x in vals) / n
        # Public-response alignment: absolute allocation mismatch to the observed
        # opponent on the same battlefield. No private state or mechanism labels.
        feats[f"battlefield_{i}_mean_abs_gap"] = sum(abs(actions[t][i] - opponents[t][i]) for t in range(n)) / n
    return feats


def _run_mixed_trajectory(weights: tuple[float, float, float], *, rounds: int, seed: int, game: BlottoGame) -> dict:
    from .agents import MixedPCCAgent
    agent = MixedPCCAgent(*weights)
    # Use both stationary and adaptive public environments across seeds without
    # exposing opponent-family identity to the recovery model.
    opponent = StaticWeightedOpponent() if seed % 2 == 0 else AdaptiveCounterOpponent()
    rng_a = random.Random(seed + 810_000_007)
    rng_b = random.Random(seed + 910_000_009)
    a_hist: list[Allocation] = []
    b_hist: list[Allocation] = []
    payoffs: list[float] = []
    for _ in range(rounds):
        a = agent.act(game, b_hist, rng_a)
        b = opponent.act(game, a_hist, rng_b)
        a_hist.append(a)
        b_hist.append(b)
        payoffs.append(game.payoff(a, b))
    return {
        "weights": list(weights),
        "features": _trajectory_observables(a_hist, b_hist, payoffs, game),
    }


def _solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    """Small deterministic Gauss-Jordan solver with partial pivoting."""
    n = len(b)
    aug = [list(a[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12:
            raise ValueError("singular linear system")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [x / scale for x in aug[col]]
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor:
                aug[r] = [aug[r][c] - factor * aug[col][c] for c in range(n + 1)]
    return [aug[i][-1] for i in range(n)]


def _fit_ridge(rows: list[dict], feature_names: list[str], target_idx: int, ridge: float) -> dict:
    means = {f: sum(r["features"][f] for r in rows) / len(rows) for f in feature_names}
    scales: dict[str, float] = {}
    for f in feature_names:
        var = sum((r["features"][f] - means[f]) ** 2 for r in rows) / len(rows)
        scales[f] = math.sqrt(var) if var > 1e-12 else 1.0
    x = [[1.0] + [(r["features"][f] - means[f]) / scales[f] for f in feature_names] for r in rows]
    y = [r["weights"][target_idx] for r in rows]
    p = len(feature_names) + 1
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for row, yy in zip(x, y):
        for i in range(p):
            xty[i] += row[i] * yy
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(1, p):  # do not penalize intercept
        xtx[i][i] += ridge
    coef = _solve_linear_system(xtx, xty)
    return {"means": means, "scales": scales, "coef": coef}


def _predict_ridge(model: dict, features: dict[str, float], feature_names: list[str]) -> float:
    x = [1.0] + [(features[f] - model["means"][f]) / model["scales"][f] for f in feature_names]
    return sum(c * v for c, v in zip(model["coef"], x))


def _project_simplex(v: list[float]) -> list[float]:
    """Euclidean projection onto the 3-simplex."""
    u = sorted(v, reverse=True)
    cssv = 0.0
    rho = 0
    for j, uj in enumerate(u, 1):
        cssv += uj
        if uj + (1.0 - cssv) / j > 0:
            rho = j
    theta = (sum(u[:rho]) - 1.0) / rho
    return [max(x - theta, 0.0) for x in v]


def run_observational_recovery(
    rounds: int = RECOVERY_ROUNDS,
    seeds_per_mixture: int = RECOVERY_SEEDS_PER_MIXTURE,
) -> dict:
    """Recover hidden PCC mixture weights from trajectory observables OOD."""
    game = BlottoGame()
    mixtures = _simplex_grid(10)
    train_weights = [w for w in mixtures if max(w) < RECOVERY_OOD_DOMINANCE]
    ood_weights = [w for w in mixtures if max(w) >= RECOVERY_OOD_DOMINANCE]
    train_rows: list[dict] = []
    ood_rows: list[dict] = []
    for mix_index, weights in enumerate(mixtures):
        target = ood_rows if weights in ood_weights else train_rows
        for rep in range(seeds_per_mixture):
            seed = mix_index * 101 + rep
            target.append(_run_mixed_trajectory(weights, rounds=rounds, seed=seed, game=game))
    feature_names = sorted(train_rows[0]["features"])
    models = [_fit_ridge(train_rows, feature_names, k, RECOVERY_RIDGE) for k in range(3)]
    predictions: list[dict] = []
    abs_errors = [[], [], []]
    baseline_errors = [[], [], []]
    for row in ood_rows:
        raw = [_predict_ridge(m, row["features"], feature_names) for m in models]
        pred = _project_simplex(raw)
        true = row["weights"]
        for k in range(3):
            abs_errors[k].append(abs(pred[k] - true[k]))
            baseline_errors[k].append(abs((1.0 / 3.0) - true[k]))
        predictions.append({"true_weights": true, "predicted_weights": pred})
    axis_names = ["pressure", "control", "chaos"]
    axis_mae = {axis_names[k]: sum(abs_errors[k]) / len(abs_errors[k]) for k in range(3)}
    axis_baseline_mae = {axis_names[k]: sum(baseline_errors[k]) / len(baseline_errors[k]) for k in range(3)}
    overall_mae = sum(sum(x) for x in abs_errors) / (3 * len(ood_rows))
    baseline_mae = sum(sum(x) for x in baseline_errors) / (3 * len(ood_rows))
    improvement = 1.0 - overall_mae / baseline_mae
    checks = {
        "ood_overall_mae_at_most_0_15": {
            "pass": overall_mae <= RECOVERY_MAX_OOD_MAE,
            "value": overall_mae,
            "threshold": RECOVERY_MAX_OOD_MAE,
        },
        "beats_uniform_centroid_baseline_by_at_least_25_percent": {
            "pass": improvement >= RECOVERY_MIN_BASELINE_IMPROVEMENT,
            "relative_improvement": improvement,
            "threshold": RECOVERY_MIN_BASELINE_IMPROVEMENT,
        },
        "all_three_axes_beat_centroid_baseline": {
            "pass": all(axis_mae[a] < axis_baseline_mae[a] for a in axis_names),
            "axis_mae": axis_mae,
            "axis_baseline_mae": axis_baseline_mae,
        },
    }
    return {
        "schema": "pcc-colonel-blotto-observational-recovery-v0.8",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_trajectory": rounds,
            "seeds_per_mixture": seeds_per_mixture,
            "simplex_grid_step": 0.1,
            "train_mixtures": len(train_weights),
            "ood_mixtures": len(ood_weights),
            "train_rows": len(train_rows),
            "ood_rows": len(ood_rows),
            "ood_rule": f"max latent axis weight >= {RECOVERY_OOD_DOMINANCE}",
            "recovery_model": f"three standardized ridge regressions (lambda={RECOVERY_RIDGE}) + simplex projection",
            "feature_names": feature_names,
            "forbidden_predictors": ["latent weights", "component-selection labels", "agent internals", "RNG seeds", "opponent-family labels"],
        },
        "aggregate": {
            "ood_overall_mae": overall_mae,
            "centroid_baseline_mae": baseline_mae,
            "relative_improvement_over_centroid": improvement,
            "axis_mae": axis_mae,
            "axis_baseline_mae": axis_baseline_mae,
            "all_primary_checks_pass": all(v["pass"] for v in checks.values()),
        },
        "prespecified_checks": checks,
        "predictions": predictions,
        "claim_scope": "synthetic observational OOD recovery of latent engineered PCC mixtures; not recovery from human play",
    }


def write_observational_recovery(
    output_dir: str | Path,
    rounds: int = RECOVERY_ROUNDS,
    seeds_per_mixture: int = RECOVERY_SEEDS_PER_MIXTURE,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_observational_recovery(rounds=rounds, seeds_per_mixture=seeds_per_mixture)
    (out / "observational-recovery.json").write_text(json.dumps(result, indent=2) + "\n")
    a = result["aggregate"]
    lines = [
        "# PCC Colonel Blotto v0.8 Observational OOD Recovery",
        "",
        "Hidden Pressure/Control/Chaos mixture weights generate behavior; the recovery model receives only trajectory-level observables.",
        "",
        "## Frozen split",
        "",
        f"- training mixtures: **{result['design']['train_mixtures']}** blended simplex points",
        f"- OOD mixtures: **{result['design']['ood_mixtures']}** axis-dominant points (`max(weight) >= {RECOVERY_OOD_DOMINANCE}`)",
        f"- trajectories: **{result['design']['train_rows']} train / {result['design']['ood_rows']} OOD**",
        "",
        "## OOD recovery",
        "",
        f"- overall MAE: **{a['ood_overall_mae']:.4f}**",
        f"- centroid baseline MAE: **{a['centroid_baseline_mae']:.4f}**",
        f"- relative improvement: **{a['relative_improvement_over_centroid']:.1%}**",
        "",
        "| axis | recovery MAE | centroid MAE |",
        "|---|---:|---:|",
    ]
    for axis in ("pressure", "control", "chaos"):
        lines.append(f"| {axis.title()} | {a['axis_mae'][axis]:.4f} | {a['axis_baseline_mae'][axis]:.4f} |")
    lines += ["", "## Prespecified checks", ""]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        f"Overall primary rule: **{'PASS' if a['all_primary_checks_pass'] else 'FAIL'}**",
        "",
        "## Interpretation guardrail",
        "",
        "A pass supports recoverability of hidden engineered PCC mixtures from observable Blotto behavior under this synthetic OOD split. It does not establish recovery from human play or prove that the engineered component policies uniquely instantiate PCC.",
    ]
    (out / "OBSERVATIONAL_RECOVERY.md").write_text("\n".join(lines) + "\n")
    return result

# ---------------------------------------------------------------------------
# v0.9 Pressure-Control boundary falsification
# ---------------------------------------------------------------------------

PC_BOUNDARY_ROUNDS = 240
PC_BOUNDARY_SEEDS_PER_MIXTURE = 6
PC_BOUNDARY_STEP = 0.05
PC_BOUNDARY_TRAIN_LOW = 0.20
PC_BOUNDARY_TRAIN_HIGH = 0.80
PC_BOUNDARY_MAX_OOD_MAE = 0.15
PC_BOUNDARY_MIN_BASELINE_IMPROVEMENT = 0.50
PC_BOUNDARY_MIN_CORRELATION = 0.90

PC_BOUNDARY_FEATURES = [
    "mean_payoff",
    "win_rate",
    "mean_concentration",
    "mean_leverage_targeting",
    "mean_opponent_viable_responses",
    *[f"battlefield_{i}_mean" for i in range(5)],
    *[f"battlefield_{i}_mean_abs_gap" for i in range(5)],
]


def _pc_edge_grid(step: float = PC_BOUNDARY_STEP) -> list[tuple[float, float, float]]:
    """Pressure-Control edge with Chaos fixed exactly at zero."""
    n = int(round(1.0 / step))
    return [(i / n, 1.0 - i / n, 0.0) for i in range(n + 1)]


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or not xs:
        raise ValueError("correlation inputs must be nonempty and equal length")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denom = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    return 0.0 if denom <= 1e-12 else sum(x * y for x, y in zip(dx, dy)) / denom


def _restricted_pc_features(features: dict[str, float]) -> dict[str, float]:
    """Mechanism-facing public observables with entropy/diversity shortcuts removed."""
    return {name: features[name] for name in PC_BOUNDARY_FEATURES}


def _run_pc_boundary_trajectory(
    weights: tuple[float, float, float], *, rounds: int, seed: int, game: BlottoGame
) -> dict:
    row = _run_mixed_trajectory(weights, rounds=rounds, seed=seed, game=game)
    row["features"] = _restricted_pc_features(row["features"])
    return row


def run_pressure_control_boundary(
    rounds: int = PC_BOUNDARY_ROUNDS,
    seeds_per_mixture: int = PC_BOUNDARY_SEEDS_PER_MIXTURE,
) -> dict:
    """OOD recovery on the P<->C edge with Chaos fixed to zero and entropy features forbidden."""
    game = BlottoGame()
    mixtures = _pc_edge_grid()
    train_weights = [w for w in mixtures if PC_BOUNDARY_TRAIN_LOW <= w[0] <= PC_BOUNDARY_TRAIN_HIGH]
    ood_weights = [w for w in mixtures if w not in train_weights]

    train_rows: list[dict] = []
    ood_rows: list[dict] = []
    for mix_index, weights in enumerate(mixtures):
        target = train_rows if weights in train_weights else ood_rows
        for rep in range(seeds_per_mixture):
            seed = 2_000_003 + mix_index * 211 + rep
            target.append(_run_pc_boundary_trajectory(weights, rounds=rounds, seed=seed, game=game))

    feature_names = list(PC_BOUNDARY_FEATURES)
    # Only one scalar needs recovery on the edge: P; C=1-P and Chaos=0.
    model = _fit_ridge(train_rows, feature_names, 0, RECOVERY_RIDGE)
    predictions: list[dict] = []
    errors: list[float] = []
    baseline_errors: list[float] = []
    true_p: list[float] = []
    pred_p: list[float] = []

    for row in ood_rows:
        raw_p = _predict_ridge(model, row["features"], feature_names)
        p = min(1.0, max(0.0, raw_p))
        true = row["weights"]
        err = abs(p - true[0])
        errors.append(err)
        baseline_errors.append(abs(0.5 - true[0]))
        true_p.append(true[0])
        pred_p.append(p)
        predictions.append({
            "true_weights": true,
            "predicted_weights": [p, 1.0 - p, 0.0],
            "pressure_abs_error": err,
        })

    mae = sum(errors) / len(errors)
    baseline_mae = sum(baseline_errors) / len(baseline_errors)
    improvement = 1.0 - mae / baseline_mae
    corr = _pearson(true_p, pred_p)
    checks = {
        "ood_pressure_mae_at_most_0_15": {
            "pass": mae <= PC_BOUNDARY_MAX_OOD_MAE,
            "value": mae,
            "threshold": PC_BOUNDARY_MAX_OOD_MAE,
        },
        "beats_edge_midpoint_baseline_by_at_least_50_percent": {
            "pass": improvement >= PC_BOUNDARY_MIN_BASELINE_IMPROVEMENT,
            "relative_improvement": improvement,
            "threshold": PC_BOUNDARY_MIN_BASELINE_IMPROVEMENT,
        },
        "pressure_ordering_correlation_at_least_0_90": {
            "pass": corr >= PC_BOUNDARY_MIN_CORRELATION,
            "value": corr,
            "threshold": PC_BOUNDARY_MIN_CORRELATION,
        },
        "chaos_is_exactly_zero_everywhere": {
            "pass": all(abs(w[2]) < 1e-12 for w in mixtures),
            "value": 0.0,
            "threshold": 0.0,
        },
    }
    forbidden = [
        "allocation_entropy",
        "distinct_action_ratio",
        "repeat_rate",
        "mean_step_l1",
        *[f"battlefield_{i}_variance" for i in range(game.battlefields)],
    ]
    return {
        "schema": "pcc-colonel-blotto-pressure-control-boundary-v0.9",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "rounds_per_trajectory": rounds,
            "seeds_per_mixture": seeds_per_mixture,
            "edge_step": PC_BOUNDARY_STEP,
            "chaos_weight": 0.0,
            "train_pressure_range": [PC_BOUNDARY_TRAIN_LOW, PC_BOUNDARY_TRAIN_HIGH],
            "ood_rule": f"pressure < {PC_BOUNDARY_TRAIN_LOW} or pressure > {PC_BOUNDARY_TRAIN_HIGH}",
            "train_mixtures": len(train_weights),
            "ood_mixtures": len(ood_weights),
            "train_rows": len(train_rows),
            "ood_rows": len(ood_rows),
            "recovery_model": f"standardized ridge pressure regression (lambda={RECOVERY_RIDGE}); control=1-pressure",
            "feature_names": feature_names,
            "forbidden_entropy_or_diversity_features": forbidden,
            "forbidden_predictors": ["latent weights", "component-selection labels", "agent internals", "RNG seeds", "opponent-family labels"],
        },
        "aggregate": {
            "ood_pressure_mae": mae,
            "edge_midpoint_baseline_mae": baseline_mae,
            "relative_improvement_over_midpoint": improvement,
            "pressure_prediction_correlation": corr,
            "all_primary_checks_pass": all(v["pass"] for v in checks.values()),
        },
        "prespecified_checks": checks,
        "predictions": predictions,
        "claim_scope": "synthetic P-C boundary OOD recovery with Chaos fixed to zero and entropy/diversity features excluded; not recovery from human or independently learned agents",
    }


def write_pressure_control_boundary(
    output_dir: str | Path,
    rounds: int = PC_BOUNDARY_ROUNDS,
    seeds_per_mixture: int = PC_BOUNDARY_SEEDS_PER_MIXTURE,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_pressure_control_boundary(rounds=rounds, seeds_per_mixture=seeds_per_mixture)
    (out / "pressure-control-boundary.json").write_text(json.dumps(result, indent=2) + "\n")
    a = result["aggregate"]
    lines = [
        "# PCC Colonel Blotto v0.9 Pressure-Control Boundary Falsification",
        "",
        "Chaos is fixed exactly at zero. Recovery is restricted to the Pressure-Control edge and broad entropy/diversity shortcuts are excluded from the predictor set.",
        "",
        "## Frozen design",
        "",
        f"- edge spacing: **{PC_BOUNDARY_STEP:.2f}**",
        f"- training Pressure range: **[{PC_BOUNDARY_TRAIN_LOW:.2f}, {PC_BOUNDARY_TRAIN_HIGH:.2f}]**",
        f"- OOD mixtures: **{result['design']['ood_mixtures']}** extreme edge points",
        f"- trajectories: **{result['design']['train_rows']} train / {result['design']['ood_rows']} OOD**",
        f"- Chaos weight: **0.0** everywhere",
        "- entropy/diversity features: **forbidden**",
        "",
        "## OOD boundary recovery",
        "",
        f"- Pressure MAE: **{a['ood_pressure_mae']:.4f}**",
        f"- edge-midpoint baseline MAE: **{a['edge_midpoint_baseline_mae']:.4f}**",
        f"- relative improvement: **{a['relative_improvement_over_midpoint']:.1%}**",
        f"- true-vs-predicted Pressure correlation: **{a['pressure_prediction_correlation']:.4f}**",
        "",
        "## Prespecified checks",
        "",
    ]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        f"Overall primary rule: **{'PASS' if a['all_primary_checks_pass'] else 'FAIL'}**",
        "",
        "## Interpretation guardrail",
        "",
        "A pass supports separability of engineered Pressure versus Control behavior at the low-Chaos boundary using mechanism-facing public observables rather than broad entropy differences. It does not establish spontaneous PCC organization in independently learned agents.",
    ]
    (out / "PRESSURE_CONTROL_BOUNDARY.md").write_text("\n".join(lines) + "\n")
    return result

# ---------------------------------------------------------------------------
# v1.0 emergent structure in independently optimized agents
# ---------------------------------------------------------------------------

EMERGENCE_TRAIN_ROUNDS = 35
EMERGENCE_TRAIN_ITERATIONS = 8
EMERGENCE_EVAL_ROUNDS = 100
EMERGENCE_EVAL_SEEDS = 4
EMERGENCE_MIN_PC3_VARIANCE = 0.70
EMERGENCE_MIN_AXIS_CORRELATION = 0.50
EMERGENCE_MIN_SPLIT_HALF_STABILITY = 0.60


def _zscore_columns(rows: list[dict[str, float]], names: list[str]) -> tuple[list[list[float]], dict, dict]:
    means = {n: sum(r[n] for r in rows) / len(rows) for n in names}
    scales = {}
    for n in names:
        var = sum((r[n] - means[n]) ** 2 for r in rows) / len(rows)
        scales[n] = math.sqrt(var) if var > 1e-12 else 1.0
    matrix = [[(r[n] - means[n]) / scales[n] for n in names] for r in rows]
    return matrix, means, scales


def _matvec(a: list[list[float]], v: list[float]) -> list[float]:
    return [sum(x * y for x, y in zip(row, v)) for row in a]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: list[float]) -> float:
    return math.sqrt(_dot(v, v))


def _pca(matrix: list[list[float]], k: int = 3) -> tuple[list[list[float]], list[float], list[list[float]]]:
    n = len(matrix)
    p = len(matrix[0])
    cov = [[sum(matrix[r][i] * matrix[r][j] for r in range(n)) / max(1, n - 1) for j in range(p)] for i in range(p)]
    work = [row[:] for row in cov]
    vecs: list[list[float]] = []
    vals: list[float] = []
    for comp in range(min(k, p)):
        v = [1.0 + 0.07 * ((i + 1) * (comp + 2) % 5) for i in range(p)]
        nv = _norm(v)
        v = [x / nv for x in v]
        for _ in range(120):
            w = _matvec(work, v)
            nw = _norm(w)
            if nw <= 1e-12:
                break
            v2 = [x / nw for x in w]
            if sum(abs(a - b) for a, b in zip(v, v2)) < 1e-10:
                v = v2
                break
            v = v2
        lam = _dot(v, _matvec(work, v))
        if lam < 1e-10:
            break
        vecs.append(v)
        vals.append(lam)
        for i in range(p):
            for j in range(p):
                work[i][j] -= lam * v[i] * v[j]
    scores = [[_dot(row, v) for v in vecs] for row in matrix]
    return vecs, vals, scores


def _corr(xs: list[float], ys: list[float]) -> float:
    return _pearson(xs, ys)


def _evaluate_learned_agent(agent, opponent_factory, *, game: BlottoGame, rounds: int, seed: int) -> dict:
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 10_000_019)
    opponent = opponent_factory()
    ah: list[Allocation] = []
    bh: list[Allocation] = []
    payoffs: list[float] = []
    for _ in range(rounds):
        a = agent.act(game, bh, rng_a)
        b = opponent.act(game, ah, rng_b)
        ah.append(a)
        bh.append(b)
        payoffs.append(game.payoff(a, b))
    f = _trajectory_observables(ah, bh, payoffs, game)
    q = max(1, rounds // 4)
    f["late_minus_early_payoff"] = sum(payoffs[-q:]) / q - sum(payoffs[:q]) / q
    if len(ah) > 1:
        f["lagged_counter_payoff"] = sum(game.payoff(ah[t], bh[t - 1]) for t in range(1, len(ah))) / (len(ah) - 1)
    else:
        f["lagged_counter_payoff"] = 0.0
    return f


def _mean_feature_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    names = rows[0].keys()
    return {n: sum(r[n] for r in rows) / len(rows) for n in names}


def _signature_scores(agent_rows: list[dict]) -> dict[str, list[float]]:
    raw: list[dict[str, float]] = []
    for row in agent_rows:
        alt = row["contexts"]["alternating_weighted_heldout"]
        exp = row["contexts"]["mean_profile_exploiter"]
        raw.append({
            "p_leverage": (alt["mean_leverage_targeting"] + exp["mean_leverage_targeting"]) / 2,
            "p_constrict": -(alt["mean_opponent_viable_responses"] + exp["mean_opponent_viable_responses"]) / 2,
            "c_counter": (alt["lagged_counter_payoff"] + exp["lagged_counter_payoff"]) / 2,
            "c_gap": -sum(alt[f"battlefield_{i}_mean_abs_gap"] for i in range(5)) / 5,
            "h_entropy": (alt["allocation_entropy"] + exp["allocation_entropy"]) / 2,
            "h_value": exp["mean_payoff"],
        })
    _, means, scales = _zscore_columns(raw, list(raw[0]))
    def z(r, n): return (r[n] - means[n]) / scales[n]
    return {
        "pressure": [0.65 * z(r, "p_leverage") + 0.35 * z(r, "p_constrict") for r in raw],
        "control": [0.75 * z(r, "c_counter") + 0.25 * z(r, "c_gap") for r in raw],
        "chaos": [0.65 * z(r, "h_entropy") + 0.35 * z(r, "h_value") for r in raw],
    }


def run_emergent_learned_agents(
    train_iterations: int = EMERGENCE_TRAIN_ITERATIONS,
    train_rounds: int = EMERGENCE_TRAIN_ROUNDS,
    eval_rounds: int = EMERGENCE_EVAL_ROUNDS,
    eval_seeds: int = EMERGENCE_EVAL_SEEDS,
) -> dict:
    """v1.0: test PCC-like structure in independently optimized agents with no latent PCC generator."""
    from .learned import AlternatingWeightedOpponent, train_linear_agent

    game = BlottoGame()
    objectives = ["payoff", "win_rate", "risk_adjusted", "robust"]
    curricula = {
        "static": [StaticWeightedOpponent],
        "adaptive": [AdaptiveCounterOpponent],
        "mixed": [StaticWeightedOpponent, AdaptiveCounterOpponent],
    }
    trained: list[dict] = []
    idx = 0
    for objective in objectives:
        for curriculum_name, factories in curricula.items():
            seed = 7001 + idx * 313
            agent, metadata = train_linear_agent(
                game=game,
                opponent_factories=factories,
                objective=objective,
                seed=seed,
                iterations=train_iterations,
                rounds=train_rounds,
                eval_seeds=2,
            )
            trained.append({"agent": agent, "objective": objective, "curriculum": curriculum_name, "metadata": metadata})
            idx += 1

    eval_contexts = {
        "mean_profile_exploiter": MeanProfileExploiter,
        "alternating_weighted_heldout": AlternatingWeightedOpponent,
    }
    agent_rows: list[dict] = []
    split_rows = {"even": [], "odd": []}
    for ai, item in enumerate(trained):
        contexts: dict[str, dict[str, float]] = {}
        split_contexts = {"even": {}, "odd": {}}
        for cname, factory in eval_contexts.items():
            reps = []
            even = []
            odd = []
            for rep in range(eval_seeds):
                f = _evaluate_learned_agent(item["agent"], factory, game=game, rounds=eval_rounds, seed=900_001 + ai * 101 + rep)
                reps.append(f)
                (even if rep % 2 == 0 else odd).append(f)
            contexts[cname] = _mean_feature_rows(reps)
            split_contexts["even"][cname] = _mean_feature_rows(even)
            split_contexts["odd"][cname] = _mean_feature_rows(odd)
        public = {
            "agent_id": ai,
            "objective": item["objective"],
            "curriculum": item["curriculum"],
            "contexts": contexts,
        }
        agent_rows.append(public)
        for split in ("even", "odd"):
            split_rows[split].append({**public, "contexts": split_contexts[split]})

    # PCA uses only behavioral observables from held-out contexts; objective and
    # curriculum labels are retained solely for post-hoc description.
    base_features = [
        "mean_payoff", "win_rate", "allocation_entropy", "distinct_action_ratio",
        "mean_concentration", "mean_leverage_targeting", "mean_opponent_viable_responses",
        "mean_step_l1", "repeat_rate", "late_minus_early_payoff", "lagged_counter_payoff",
    ]
    feature_names = [f"{c}:{f}" for c in eval_contexts for f in base_features]
    flat_rows: list[dict[str, float]] = []
    for row in agent_rows:
        flat_rows.append({f"{c}:{f}": row["contexts"][c][f] for c in eval_contexts for f in base_features})
    matrix, means, scales = _zscore_columns(flat_rows, feature_names)
    vecs, eigvals, pc_scores = _pca(matrix, 3)
    total_var = sum(sum(x * x for x in r) for r in matrix) / max(1, len(matrix) - 1)
    explained = [v / total_var if total_var else 0.0 for v in eigvals]
    cumulative3 = sum(explained)

    signatures = _signature_scores(agent_rows)
    correlations: dict[str, list[float]] = {}
    for axis, vals in signatures.items():
        correlations[axis] = [_corr(vals, [s[j] for s in pc_scores]) for j in range(len(eigvals))]
    # Best one-to-one assignment among 3! possibilities.
    perms = [(0,1,2),(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]
    axes = ["pressure", "control", "chaos"]
    assignment = max(perms, key=lambda p: sum(abs(correlations[axes[i]][p[i]]) for i in range(3)))
    assigned_corr = {axes[i]: correlations[axes[i]][assignment[i]] for i in range(3)}

    split_sig = {k: _signature_scores(v) for k, v in split_rows.items()}
    split_stability = {axis: _corr(split_sig["even"][axis], split_sig["odd"][axis]) for axis in axes}
    min_stability = min(split_stability.values())
    min_alignment = min(abs(v) for v in assigned_corr.values())
    checks = {
        "first_three_behavior_pcs_explain_at_least_70_percent": {
            "pass": cumulative3 >= EMERGENCE_MIN_PC3_VARIANCE,
            "value": cumulative3,
            "threshold": EMERGENCE_MIN_PC3_VARIANCE,
        },
        "three_distinct_pcs_align_with_pcc_signatures_at_least_0_50": {
            "pass": min_alignment >= EMERGENCE_MIN_AXIS_CORRELATION,
            "assigned_correlations": assigned_corr,
            "threshold": EMERGENCE_MIN_AXIS_CORRELATION,
        },
        "pcc_signature_split_half_stability_at_least_0_60": {
            "pass": min_stability >= EMERGENCE_MIN_SPLIT_HALF_STABILITY,
            "axis_stability": split_stability,
            "threshold": EMERGENCE_MIN_SPLIT_HALF_STABILITY,
        },
    }
    loadings = []
    for j, v in enumerate(vecs):
        pairs = sorted(zip(feature_names, v), key=lambda x: abs(x[1]), reverse=True)
        loadings.append({"pc": j + 1, "top_loadings": [{"feature": n, "loading": x} for n, x in pairs[:8]]})
    agents_out = []
    for i, row in enumerate(agent_rows):
        agents_out.append({
            "agent_id": row["agent_id"],
            "objective": row["objective"],
            "curriculum": row["curriculum"],
            "training": trained[i]["metadata"],
            "pc_scores": pc_scores[i],
            "pcc_signature_scores": {axis: signatures[axis][i] for axis in axes},
            "heldout_contexts": row["contexts"],
        })
    return {
        "schema": "pcc-colonel-blotto-emergent-learned-agents-v1.0",
        "game": {"troops": game.troops, "values": list(game.values), "battlefields": game.battlefields},
        "design": {
            "learned_agents": len(trained),
            "objectives": objectives,
            "training_curricula": list(curricula),
            "heldout_evaluation_contexts": list(eval_contexts),
            "train_iterations": train_iterations,
            "train_rounds": train_rounds,
            "eval_rounds": eval_rounds,
            "eval_seeds": eval_seeds,
            "latent_pcc_weights_in_generator": False,
            "pcc_component_policies_used_for_training": False,
            "unsupervised_model": "PCA on standardized held-out behavioral observables",
            "behavior_feature_names": feature_names,
        },
        "aggregate": {
            "explained_variance_ratio": explained,
            "first_three_pc_cumulative_variance": cumulative3,
            "signature_pc_correlations": correlations,
            "assigned_pc_by_signature": {axes[i]: assignment[i] + 1 for i in range(3)},
            "assigned_correlations": assigned_corr,
            "split_half_signature_stability": split_stability,
            "all_primary_checks_pass": all(v["pass"] for v in checks.values()),
        },
        "prespecified_checks": checks,
        "pc_loadings": loadings,
        "agents": agents_out,
        "claim_scope": "unsupervised emergence probe in independently optimized synthetic Blotto agents; no latent PCC weights exist in the generator and no human-play claim is made",
    }


def write_emergent_learned_agents(
    output_dir: str | Path,
    train_iterations: int = EMERGENCE_TRAIN_ITERATIONS,
    train_rounds: int = EMERGENCE_TRAIN_ROUNDS,
    eval_rounds: int = EMERGENCE_EVAL_ROUNDS,
    eval_seeds: int = EMERGENCE_EVAL_SEEDS,
) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = run_emergent_learned_agents(train_iterations, train_rounds, eval_rounds, eval_seeds)
    (out / "emergent-learned-agents.json").write_text(json.dumps(result, indent=2) + "\n")
    a = result["aggregate"]
    lines = [
        "# PCC Colonel Blotto v1.0 Emergent Structure in Independently Learned Agents",
        "",
        "No latent PCC weights exist in these agents. Twelve compact policies are independently optimized under generic game objectives and opponent curricula, frozen, then characterized only on held-out opponents.",
        "",
        "## Unsupervised held-out behavior",
        "",
        f"- learned policies: **{result['design']['learned_agents']}**",
        f"- first three PC cumulative variance: **{a['first_three_pc_cumulative_variance']:.1%}**",
        f"- assigned Pressure correlation: **{a['assigned_correlations']['pressure']:+.3f}** (PC{a['assigned_pc_by_signature']['pressure']})",
        f"- assigned Control correlation: **{a['assigned_correlations']['control']:+.3f}** (PC{a['assigned_pc_by_signature']['control']})",
        f"- assigned Chaos correlation: **{a['assigned_correlations']['chaos']:+.3f}** (PC{a['assigned_pc_by_signature']['chaos']})",
        "",
        "## Split-half stability",
        "",
    ]
    for axis, value in a["split_half_signature_stability"].items():
        lines.append(f"- {axis.title()}: **{value:+.3f}**")
    lines += ["", "## Prespecified checks", ""]
    for name, item in result["prespecified_checks"].items():
        lines.append(f"- **{name}**: {'PASS' if item['pass'] else 'FAIL'}")
    lines += [
        "",
        f"Overall primary rule: **{'PASS' if a['all_primary_checks_pass'] else 'FAIL'}**",
        "",
        "## Interpretation guardrail",
        "",
        "This is a stronger evidentiary level than engineered-mixture recovery because PCC weights are absent from the generator. A pass would support reproducible PCC-like organization of independently optimized synthetic behavior, not prove that PCC is the unique latent basis, nor establish human/general-agent validity.",
    ]
    (out / "EMERGENT_LEARNED_AGENTS.md").write_text("\n".join(lines) + "\n")
    return result
