from __future__ import annotations

import argparse

from .experiment import write_control_history_destruction, write_control_regime_switching, write_probe


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
