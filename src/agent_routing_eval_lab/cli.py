from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from agent_routing_eval_lab import __version__
from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs, positive_int, write_csv
from agent_routing_eval_lab.evaluation.diff import DiffResult, compute_decision_diffs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator, load_logged_decisions
from agent_routing_eval_lab.evaluation.gates import GatePolicy, apply_gates, load_gate_policy, violations_to_dict
from agent_routing_eval_lab.evaluation.report import write_markdown_report
from agent_routing_eval_lab.evaluation.serialization import results_to_json
from agent_routing_eval_lab.evaluation.validation import validate_logged_decisions
from agent_routing_eval_lab.io_utils import atomic_write_csv, atomic_write_text
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter
from agent_routing_eval_lab.routing.cost_aware_router import CostAwareRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter
from agent_routing_eval_lab.visualization.charts import ascii_score_chart

# Exit-code contract (documented in docs/cli.md and shared with the gate command):
#   0 = success / gate passed
#   1 = gate violation or validation failure (the run worked; the result is "no-go")
#   2 = usage or data error (bad input, missing file, unknown policy)
EXIT_OK = 0
EXIT_GATE_FAILED = 1
EXIT_USAGE = 2

logger = logging.getLogger("agent_routing_eval_lab")


def _policies() -> dict[str, object]:
    return {
        "baseline": BaselineRouter(),
        "cost_aware": CostAwareRouter(),
        "strict_policy": StrictPolicyRouter(),
        "contextweaver_v1": ContextWeaverRouter(),
    }


def _configure_logging(*, verbose: bool, quiet: bool) -> None:
    level = logging.WARNING
    if verbose:
        level = logging.DEBUG
    elif quiet:
        level = logging.ERROR
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def _emit_warnings(warnings: list[str], *, verbose: bool, limit: int = 3) -> None:
    if not warnings:
        return
    shown = warnings if verbose else warnings[:limit]
    for warning in shown:
        logger.warning("warning: %s", warning)
    hidden = len(warnings) - len(shown)
    if hidden > 0:
        logger.warning("... and %d more warning(s); re-run with -v to see all", hidden)


def _evaluate(input_path: Path, policies: dict[str, object] | None = None):
    logs = load_logged_decisions(input_path)
    evaluator = OfflineEvaluator(logs)
    return logs, evaluator.evaluate_many(policies if policies is not None else _policies())


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", name)


def _dump_decisions(results, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        if not result.scored_rows:
            continue
        target = output_dir / f"{_sanitize_filename(result.policy_name)}_decisions.csv"
        fieldnames = list(result.scored_rows[0].keys())
        atomic_write_csv(target, fieldnames, result.scored_rows)
        logger.info("wrote %d decisions to %s", len(result.scored_rows), target)


def cmd_generate_data(args: argparse.Namespace) -> int:
    records = generate_synthetic_logs(rows=args.rows, seed=args.seed)
    write_csv(args.output, records)
    print(f"Generated {len(records)} rows at {args.output}")
    return EXIT_OK


def cmd_evaluate(args: argparse.Namespace) -> int:
    logs, results = _evaluate(args.input)
    if args.dump_decisions is not None:
        _dump_decisions(results, args.dump_decisions)

    if args.format == "json":
        print(results_to_json(results, input_path=args.input, row_count=len(logs)), end="")
        return EXIT_OK

    print(ascii_score_chart(results))
    winner = sorted(results, key=lambda x: x.metrics.score, reverse=True)[0]
    print(f"Winner: {winner.policy_name} (score={winner.metrics.score:.2f})")
    _emit_warnings(winner.warnings, verbose=args.verbose)
    return EXIT_OK


def cmd_report(args: argparse.Namespace) -> int:
    logs, results = _evaluate(args.input)
    write_markdown_report(args.output, results)
    print(f"Wrote report to {args.output}")
    if args.json_output is not None:
        atomic_write_text(args.json_output, results_to_json(results, input_path=args.input, row_count=len(logs)))
        print(f"Wrote JSON results to {args.json_output}")
    return EXIT_OK


def cmd_demo(args: argparse.Namespace) -> int:
    output_dir = (args.output_dir or Path.cwd()).resolve()
    data_path = output_dir / "examples" / "logged_decisions.sample.csv"
    report_path = output_dir / "reports" / "example_report.md"

    records = generate_synthetic_logs(rows=300, seed=7)
    write_csv(data_path, records)
    _, results = _evaluate(data_path)
    write_markdown_report(report_path, results)

    ranked = sorted(results, key=lambda item: item.metrics.score, reverse=True)
    winner = ranked[0]

    print(ascii_score_chart(ranked))
    print(f"Winning policy: {winner.policy_name}")
    print(f"Data: {data_path}")
    print(f"Report: {report_path}")
    for result in ranked:
        _emit_warnings(result.warnings, verbose=args.verbose, limit=2)
    return EXIT_OK


def cmd_gate(args: argparse.Namespace) -> int:
    _, results = _evaluate(args.input)
    if args.config is not None:
        policy = load_gate_policy(args.config)
    else:
        policy = GatePolicy(
            max_unsafe_rate=args.max_unsafe_rate,
            min_success_rate=args.min_success_rate,
            max_low_support_share=args.max_low_support_share,
            max_avg_cost=args.max_avg_cost,
            policy_name=args.policy_name,
        )
    if not policy.has_active_thresholds():
        raise ValueError(
            "gate requires at least one threshold "
            "(e.g. --max-unsafe-rate, --min-success-rate, --max-low-support-share, --max-avg-cost) "
            "or a --config file that sets one; a gate with no thresholds always passes"
        )
    violations = apply_gates(results, policy)

    if args.format == "json":
        print(json.dumps(violations_to_dict(violations), indent=2, sort_keys=True))
    elif violations:
        print("Gate FAILED:")
        for violation in violations:
            print(f"  - {violation.message()}")
    else:
        print("Gate PASSED")
    return EXIT_GATE_FAILED if violations else EXIT_OK


def _diff_to_dict(diff: DiffResult, *, limit: int, only_regressions: bool) -> dict:
    rows = diff.diffs
    if only_regressions:
        rows = [d for d in rows if d.classification == "regression"]
    return {
        "policy_a": diff.policy_a,
        "policy_b": diff.policy_b,
        "summary": {"regressed": diff.regressed, "improved": diff.improved, "neutral": diff.neutral},
        "diffs": [
            {
                "request_id": d.request_id,
                "intent": d.intent,
                "classification": d.classification,
                "tool_a": d.tool_a,
                "tool_b": d.tool_b,
                "success_a": d.success_a,
                "success_b": d.success_b,
                "unsafe_a": d.unsafe_a,
                "unsafe_b": d.unsafe_b,
                "cost_delta": d.cost_delta,
                "latency_delta": d.latency_delta,
            }
            for d in rows[:limit]
        ],
    }


def cmd_compare(args: argparse.Namespace) -> int:
    available = _policies()
    for name in (args.policy_a, args.policy_b):
        if name not in available:
            raise ValueError(
                f"unknown policy '{name}'; available policies: {', '.join(sorted(available))}"
            )
    selected = {args.policy_a: available[args.policy_a], args.policy_b: available[args.policy_b]}
    _, results = _evaluate(args.input, selected)
    result_a = next(r for r in results if r.policy_name == args.policy_a)
    result_b = next(r for r in results if r.policy_name == args.policy_b)
    diff = compute_decision_diffs(result_a, result_b)

    if args.format == "json":
        print(json.dumps(_diff_to_dict(diff, limit=args.limit, only_regressions=args.only_regressions), indent=2))
        return EXIT_OK

    print(f"Comparing {diff.policy_a} (A) vs {diff.policy_b} (B)")
    print(f"Summary: {diff.regressed} regressed, {diff.improved} improved, {diff.neutral} neutral")
    rows = [d for d in diff.diffs if d.classification == "regression"] if args.only_regressions else diff.diffs
    if not rows:
        print("No per-request differences to show.")
        return EXIT_OK
    print(f"Showing up to {args.limit} differing requests:")
    for d in rows[: args.limit]:
        print(
            f"  [{d.classification}] {d.request_id} ({d.intent}): "
            f"{d.tool_a} -> {d.tool_b} | success {d.success_a}->{d.success_b} | "
            f"unsafe {d.unsafe_a}->{d.unsafe_b} | dcost {d.cost_delta:+.3f} | dlatency {d.latency_delta:+.0f}ms"
        )
    return EXIT_OK


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_logged_decisions(args.input, max_errors=args.max_errors)
    if not errors:
        print(f"OK: {args.input} matches the logged-decisions schema")
        return EXIT_OK
    print(f"FAILED: {len(errors)} problem(s) found in {args.input}", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    return EXIT_GATE_FAILED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agent routing offline evaluation lab",
        epilog="Exit codes: 0 success / gate passed, 1 gate or validation failure, 2 usage or data error.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all diagnostics on stderr")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress warning diagnostics")
    sub = parser.add_subparsers(required=True)

    generate = sub.add_parser("generate-data", help="Generate synthetic decision logs")
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--rows", type=positive_int, default=300)
    generate.add_argument("--seed", type=int, default=7)
    generate.set_defaults(func=cmd_generate_data)

    evaluate = sub.add_parser("evaluate", help="Evaluate candidate policies")
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    evaluate.add_argument(
        "--dump-decisions", type=Path, default=None, metavar="DIR", help="Write per-policy scored-row CSVs to DIR"
    )
    evaluate.set_defaults(func=cmd_evaluate)

    report = sub.add_parser("report", help="Generate markdown report")
    report.add_argument("--input", type=Path, required=True)
    report.add_argument("--output", type=Path, required=True)
    report.add_argument(
        "--json-output", type=Path, default=None, metavar="PATH", help="Also write machine-readable JSON results to PATH"
    )
    report.set_defaults(func=cmd_report)

    demo = sub.add_parser("demo", help="Generate data, evaluate policies, and write report")
    demo.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory for examples/ and reports/ artifacts (default: current directory)",
    )
    demo.set_defaults(func=cmd_demo)

    gate = sub.add_parser("gate", help="Evaluate policies and fail (exit 1) on threshold violations")
    gate.add_argument("--input", type=Path, required=True)
    gate.add_argument("--max-unsafe-rate", type=float, default=None)
    gate.add_argument("--min-success-rate", type=float, default=None)
    gate.add_argument("--max-low-support-share", type=float, default=None)
    gate.add_argument("--max-avg-cost", type=float, default=None)
    gate.add_argument("--policy-name", type=str, default=None, help="Gate only this policy (default: all)")
    gate.add_argument("--config", type=Path, default=None, metavar="PATH", help="Load thresholds from a JSON config")
    gate.add_argument("--format", choices=["text", "json"], default="text")
    gate.set_defaults(func=cmd_gate)

    compare = sub.add_parser("compare", help="Show per-request decision diffs between two policies")
    compare.add_argument("--input", type=Path, required=True)
    compare.add_argument("--policy-a", type=str, required=True)
    compare.add_argument("--policy-b", type=str, required=True)
    compare.add_argument("--limit", type=positive_int, default=20, help="Max differing requests to show (default: 20)")
    compare.add_argument("--only-regressions", action="store_true")
    compare.add_argument("--format", choices=["text", "json"], default="text")
    compare.set_defaults(func=cmd_compare)

    validate = sub.add_parser("validate", help="Validate a logged-decisions CSV against the schema")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--max-errors", type=positive_int, default=None, help="Stop after this many errors")
    validate.set_defaults(func=cmd_validate)

    return parser


def get_cli_surface() -> dict[str, list[str]]:
    """Map each subcommand name to its sorted option strings.

    Used by the docs parity test so a newly added flag cannot land undocumented.
    """
    parser = build_parser()
    surface: dict[str, list[str]] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, subparser in action.choices.items():
                options: list[str] = []
                for sub_action in subparser._actions:
                    options.extend(sub_action.option_strings)
                surface[name] = sorted(set(options))
    return surface


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(verbose=getattr(args, "verbose", False), quiet=getattr(args, "quiet", False))
    try:
        return args.func(args) or EXIT_OK
    except (ValueError, OSError) as exc:
        # Expected failure classes get a concise stderr message and a documented
        # exit code. Genuine bugs (anything else) keep their traceback.
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
