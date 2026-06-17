from __future__ import annotations

import argparse
from pathlib import Path

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs, positive_int, write_csv
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, load_logged_decisions
from agent_routing_eval_lab.evaluation.report import write_markdown_report
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter
from agent_routing_eval_lab.routing.cost_aware_router import CostAwareRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter
from agent_routing_eval_lab.visualization.charts import ascii_score_chart


def _policies() -> dict[str, object]:
    return {
        "baseline": BaselineRouter(),
        "cost_aware": CostAwareRouter(),
        "strict_policy": StrictPolicyRouter(),
        "contextweaver_v1": ContextWeaverRouter(),
    }


def cmd_generate_data(args: argparse.Namespace) -> None:
    records = generate_synthetic_logs(rows=args.rows, seed=args.seed)
    write_csv(args.output, records)
    print(f"Generated {len(records)} rows at {args.output}")


def _evaluate(input_path: Path):
    logs = load_logged_decisions(input_path)
    evaluator = OfflineEvaluator(logs)
    return evaluator.evaluate_many(_policies())


def cmd_evaluate(args: argparse.Namespace) -> None:
    results = _evaluate(args.input)
    print(ascii_score_chart(results))
    winner = sorted(results, key=lambda x: x.metrics.score, reverse=True)[0]
    print(f"Winner: {winner.policy_name} (score={winner.metrics.score:.2f})")
    for warning in winner.warnings[:3]:
        print(f"warning: {warning}")


def cmd_report(args: argparse.Namespace) -> None:
    results = _evaluate(args.input)
    write_markdown_report(args.output, results)
    print(f"Wrote report to {args.output}")


def cmd_demo(_: argparse.Namespace) -> None:
    data_path = Path("examples/logged_decisions.sample.csv")
    report_path = Path("reports/example_report.md")

    records = generate_synthetic_logs(rows=300, seed=7)
    write_csv(data_path, records)
    results = _evaluate(data_path)
    write_markdown_report(report_path, results)

    ranked = sorted(results, key=lambda item: item.metrics.score, reverse=True)
    winner = ranked[0]

    print(ascii_score_chart(ranked))
    print(f"Winning policy: {winner.policy_name}")
    print(f"Report: {report_path}")
    for result in ranked:
        if result.warnings:
            print(f"{result.policy_name} warnings:")
            for warning in result.warnings[:2]:
                print(f"  - {warning}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent routing offline evaluation lab")
    sub = parser.add_subparsers(required=True)

    generate = sub.add_parser("generate-data", help="Generate synthetic decision logs")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--rows", type=positive_int, default=300)
    generate.add_argument("--seed", type=int, default=7)
    generate.set_defaults(func=cmd_generate_data)

    evaluate = sub.add_parser("evaluate", help="Evaluate candidate policies")
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.set_defaults(func=cmd_evaluate)

    report = sub.add_parser("report", help="Generate markdown report")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    report.set_defaults(func=cmd_report)

    demo = sub.add_parser("demo", help="Generate data, evaluate policies, and write report")
    demo.set_defaults(func=cmd_demo)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
