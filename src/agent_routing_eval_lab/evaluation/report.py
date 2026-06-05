from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult


def build_markdown_report(results: list[PolicyEvaluationResult]) -> str:
    if not results:
        return "\n".join(
            [
                "# Agent Routing Evaluation Report",
                "",
                f"Generated: {datetime.now(UTC).isoformat()}",
                "",
                "_No policies were evaluated, so there is nothing to report._",
            ]
        )

    ranked = sorted(results, key=lambda item: item.metrics.score, reverse=True)
    winner = ranked[0]

    lines = [
        "# Agent Routing Evaluation Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Policy Comparison",
        "",
        "| Policy | Success | Correct Tool | Avg Cost | Avg Latency (ms) | Unsafe | Unresolved | Regret | Score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for result in ranked:
        m = result.metrics
        lines.append(
            f"| {result.policy_name} | {m.success_rate:.2%} | {m.correct_tool_selection_rate:.2%} | "
            f"${m.average_cost:.3f} | {m.average_latency_ms:.1f} | {m.unsafe_action_rate:.2%} | "
            f"{m.unresolved_request_rate:.2%} | {m.estimated_regret_vs_oracle:.3f} | {m.score:.2f} |"
        )

    lines.extend(
        [
            "",
            f"## Winner: `{winner.policy_name}`",
            "",
            f"- Composite score: **{winner.metrics.score:.2f}**",
            f"- Coverage check: {winner.metrics.support_coverage_warning}",
            "",
            "## Warnings",
            "",
        ]
    )

    warning_count = 0
    for result in ranked:
        for warning in result.warnings:
            lines.append(f"- **{result.policy_name}**: {warning}")
            warning_count += 1
    if warning_count == 0:
        lines.append("- No warnings detected.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is offline replay on synthetic historical-style data.",
            "- Use this report as a pre-rollout gate before online A/B tests.",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(path: Path, results: list[PolicyEvaluationResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown_report(results), encoding="utf-8")
