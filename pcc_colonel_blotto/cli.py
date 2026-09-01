from __future__ import annotations

import argparse

from .experiment import write_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="PCC Colonel Blotto experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("mechanism-probe", help="run the v0.1 synthetic mechanism probe")
    probe.add_argument("--output-dir", default="validation")
    probe.add_argument("--rounds", type=int, default=250)
    probe.add_argument("--seeds", type=int, default=8)
    args = parser.parse_args()
    if args.command == "mechanism-probe":
        result = write_probe(args.output_dir, rounds=args.rounds, seeds=args.seeds)
        for name, item in result["prespecified_checks"].items():
            print(f"{name}: {'PASS' if item['pass'] else 'FAIL'}")


if __name__ == "__main__":
    main()
