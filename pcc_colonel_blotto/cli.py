from __future__ import annotations

import argparse

from .experiment import write_control_estimator_ablation, write_control_history_destruction, write_control_regime_switching, write_pressure_leverage_intervention, write_pressure_matched_intervention, write_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="PCC Colonel Blotto experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("mechanism-probe", help="run the v0.1 synthetic mechanism probe")
    probe.add_argument("--output-dir", default="validation")
    probe.add_argument("--rounds", type=int, default=250)
    probe.add_argument("--seeds", type=int, default=8)
    history = sub.add_parser("control-history-destruction", help="run the paired temporal-order falsification for Control")
    history.add_argument("--output-dir", default="validation")
    history.add_argument("--rounds", type=int, default=250)
    history.add_argument("--seeds", type=int, default=32)
    regime = sub.add_parser("control-regime-switching", help="run the nonstationary recency falsification for Control")
    regime.add_argument("--output-dir", default="validation")
    regime.add_argument("--rounds", type=int, default=300)
    regime.add_argument("--seeds", type=int, default=32)
    regime.add_argument("--adaptation-window", type=int, default=16)
    estimator = sub.add_parser("control-estimator-ablation", help="compare Control history estimators on frozen regime-switching traces")
    estimator.add_argument("--output-dir", default="validation")
    estimator.add_argument("--rounds", type=int, default=300)
    estimator.add_argument("--seeds", type=int, default=32)
    estimator.add_argument("--adaptation-window", type=int, default=16)
    pressure = sub.add_parser("pressure-matched-intervention", help="run the v0.5 matched concentration intervention for Pressure")
    pressure.add_argument("--output-dir", default="validation")
    leverage = sub.add_parser("pressure-leverage-intervention", help="run the v0.6 targeted-leverage Pressure intervention")
    leverage.add_argument("--output-dir", default="validation")
    args = parser.parse_args()
    if args.command == "mechanism-probe":
        result = write_probe(args.output_dir, rounds=args.rounds, seeds=args.seeds)
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "control-history-destruction":
        result = write_control_history_destruction(args.output_dir, rounds=args.rounds, seeds=args.seeds)
        a = result["aggregate"]
        print(f"baseline mean payoff: {a['baseline_mean_payoff']:.6f}")
        print(f"shuffled Control mean payoff: {a['shuffled_control_mean_payoff']:.6f}")
        print(f"true Control mean payoff: {a['true_control_mean_payoff']:.6f}")
        frac = a['fraction_control_gain_eliminated_after_shuffle']
        print(f"fraction Control gain eliminated: {frac:.3%}" if frac is not None else "fraction Control gain eliminated: undefined")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "control-estimator-ablation":
        result = write_control_estimator_ablation(
            args.output_dir, rounds=args.rounds, seeds=args.seeds, adaptation_window=args.adaptation_window
        )
        for name, d in result["aggregate"].items():
            print(f"{name}: mean={d['mean_payoff']:.6f} post_switch={d['post_switch_mean_payoff']:.6f}")
        print("qualifying estimators: " + (", ".join(result["qualifying_estimators"]) if result["qualifying_estimators"] else "none"))
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "pressure-leverage-intervention":
        result = write_pressure_leverage_intervention(args.output_dir)
        a = result["aggregate"]
        print(f"matched pairs: {a['matched_pairs']}")
        print(f"mean leverage: {a['mean_low_leverage']:.6f} -> {a['mean_high_leverage']:.6f}")
        print(f"mean concentration: {a['mean_low_concentration']:.6f} -> {a['mean_high_concentration']:.6f}")
        print(f"mean viable responses: {a['mean_low_viable_responses']:.6f} -> {a['mean_high_viable_responses']:.6f}")
        print(f"relative viable-response reduction: {a['relative_viable_response_reduction']:.3%}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "pressure-matched-intervention":
        result = write_pressure_matched_intervention(args.output_dir)
        a = result["aggregate"]
        print(f"matched pairs: {a['matched_pairs']}")
        print(f"mean concentration: {a['mean_low_concentration']:.6f} -> {a['mean_high_concentration']:.6f}")
        print(f"mean viable responses: {a['mean_low_viable_responses']:.6f} -> {a['mean_high_viable_responses']:.6f}")
        print(f"relative viable-response reduction: {a['relative_viable_response_reduction']:.3%}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "control-regime-switching":
        result = write_control_regime_switching(
            args.output_dir, rounds=args.rounds, seeds=args.seeds, adaptation_window=args.adaptation_window
        )
        a = result["aggregate"]
        print(f"baseline mean payoff: {a['baseline_mean_payoff']:.6f}")
        print(f"shuffled Control mean payoff: {a['shuffled_control_mean_payoff']:.6f}")
        print(f"true Control mean payoff: {a['true_control_mean_payoff']:.6f}")
        frac = a['fraction_control_gain_eliminated_after_shuffle']
        print(f"fraction Control gain eliminated: {frac:.3%}" if frac is not None else "fraction Control gain eliminated: undefined")
        print(f"post-switch true minus shuffled: {a['post_switch_true_minus_shuffled']:.6f}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")


if __name__ == "__main__":
    main()
