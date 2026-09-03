from __future__ import annotations

import argparse

from .experiment import write_chaos_exploiter_falsification, write_control_estimator_ablation, write_control_history_destruction, write_control_regime_switching, write_pressure_leverage_intervention, write_pressure_matched_intervention, write_probe, write_observational_recovery, write_pressure_control_boundary, write_emergent_learned_agents


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
    chaos = sub.add_parser("chaos-exploiter-falsification", help="run the v0.7 guarded-Chaos held-out exploiter falsification")
    chaos.add_argument("--output-dir", default="validation")
    chaos.add_argument("--rounds", type=int, default=200)
    chaos.add_argument("--seeds", type=int, default=24)
    recovery = sub.add_parser("observational-recovery", help="run the v0.8 latent PCC mixture OOD recovery")
    recovery.add_argument("--output-dir", default="validation")
    recovery.add_argument("--rounds", type=int, default=240)
    recovery.add_argument("--seeds-per-mixture", type=int, default=4)
    boundary = sub.add_parser("pressure-control-boundary", help="run the v0.9 low-Chaos Pressure-Control boundary falsification")
    boundary.add_argument("--output-dir", default="validation")
    boundary.add_argument("--rounds", type=int, default=240)
    boundary.add_argument("--seeds-per-mixture", type=int, default=6)
    emergence = sub.add_parser("emergent-learned-agents", help="run the v1.0 independent learned-agent emergence probe")
    emergence.add_argument("--output-dir", default="validation")
    emergence.add_argument("--train-iterations", type=int, default=8)
    emergence.add_argument("--train-rounds", type=int, default=35)
    emergence.add_argument("--eval-rounds", type=int, default=100)
    emergence.add_argument("--eval-seeds", type=int, default=4)
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
    elif args.command == "observational-recovery":
        result = write_observational_recovery(args.output_dir, rounds=args.rounds, seeds_per_mixture=args.seeds_per_mixture)
        a = result["aggregate"]
        print(f"OOD overall MAE: {a['ood_overall_mae']:.6f}")
        print(f"centroid baseline MAE: {a['centroid_baseline_mae']:.6f}")
        print(f"relative improvement: {a['relative_improvement_over_centroid']:.3%}")
        for axis, value in a["axis_mae"].items():
            print(f"{axis} MAE: {value:.6f}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "pressure-control-boundary":
        result = write_pressure_control_boundary(args.output_dir, rounds=args.rounds, seeds_per_mixture=args.seeds_per_mixture)
        a = result["aggregate"]
        print(f"OOD Pressure MAE: {a['ood_pressure_mae']:.6f}")
        print(f"midpoint baseline MAE: {a['edge_midpoint_baseline_mae']:.6f}")
        print(f"relative improvement: {a['relative_improvement_over_midpoint']:.3%}")
        print(f"Pressure correlation: {a['pressure_prediction_correlation']:.6f}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "emergent-learned-agents":
        result = write_emergent_learned_agents(
            args.output_dir, args.train_iterations, args.train_rounds, args.eval_rounds, args.eval_seeds
        )
        a = result["aggregate"]
        print(f"first three PC variance: {a['first_three_pc_cumulative_variance']:.3%}")
        for axis, corr in a["assigned_correlations"].items():
            pc = a["assigned_pc_by_signature"][axis]
            print(f"{axis}: PC{pc} correlation={corr:+.6f}")
        for axis, value in a["split_half_signature_stability"].items():
            print(f"{axis} split-half stability={value:+.6f}")
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")
    elif args.command == "chaos-exploiter-falsification":
        result = write_chaos_exploiter_falsification(args.output_dir, rounds=args.rounds, seeds=args.seeds)
        by_key = {(r["agent"], r["opponent"]): r for r in result["results"]}
        for policy in ("baseline", "uniform_random", "chaos"):
            r = by_key[(policy, "mean_profile_exploiter")]
            print(f"{policy}: payoff={r['mean_payoff']:.6f} entropy={r['allocation_entropy']:.6f}")
        print(f"chaos value advantage over random: {result['aggregate']['chaos_payoff_advantage_over_uniform_random_vs_exploiter']:.6f}")
        print(f"chaos entropy ratio: {result['aggregate']['chaos_entropy_ratio_vs_uniform_random']:.3%}")
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
