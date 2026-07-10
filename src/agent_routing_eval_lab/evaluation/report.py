from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.evaluation.confidence import intervals_overlap
from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult, rank_results
from agent_routing_eval_lab.evaluation.recommendation import pareto_frontier, recommend_rollout
from agent_routing_eval_lab.io_utils import atomic_write_text

# Support threshold below which a per-(intent, tool) cell is called out as thin.
# Mirrors the evaluator default so the report and the metric agree.
_SUPPORT_THRESHOLD = 5


def _generated_at(explicit: str | None) -> str:
    """Reproducible generation timestamp (issue #75).

    Priority: an explicit value, then ``SOURCE_DATE_EPOCH`` (so ``make demo`` diffs
    stay clean and snapshot tests are stable), then the wall clock.
    """
    if explicit is not None:
        return explicit
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _comparison_table(ranked: list[PolicyEvaluationResult]) -> list[str]:
    lines = [
        "## Policy Comparison",
        "",
        "Oracle-anchored scenario-replay metrics. Higher `Score` is better.",
        "",
        "| Policy | Success | Correct Tool | Approval Req | Avg Cost | Avg Latency (ms) | Unsafe | "
        "Unresolved | Regret | Score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in ranked:
        m = result.metrics
        lines.append(
            f"| {result.policy_name} | {m.success_rate:.2%} | {m.correct_tool_selection_rate:.2%} | "
            f"{m.approval_required_action_rate:.2%} | ${m.average_cost:.3f} | {m.average_latency_ms:.1f} | "
            f"{m.unsafe_action_rate:.2%} | {m.unresolved_request_rate:.2%} | "
            f"{m.estimated_regret_vs_oracle:.3f} | {m.score:.2f} |"
        )
    return lines


def _winner_section(ranked: list[PolicyEvaluationResult]) -> list[str]:
    winner = ranked[0]
    lines = [f"## Winner: `{winner.policy_name}`", "", f"- Composite score: **{winner.metrics.score:.2f}**"]

    # Is the lead clear? Compare the top two score intervals when available.
    if len(ranked) >= 2 and winner.confidence is not None and ranked[1].confidence is not None:
        top = winner.confidence.intervals["score"]
        runner_up = ranked[1].confidence.intervals["score"]
        if intervals_overlap(top, runner_up):
            lines.append(
                f"- Lead is **not statistically clear**: `{winner.policy_name}` score CI "
                f"[{top.low:.1f}, {top.high:.1f}] overlaps `{ranked[1].policy_name}` "
                f"[{runner_up.low:.1f}, {runner_up.high:.1f}]. Treat the ranking as tentative."
            )
        else:
            lines.append(
                f"- Lead is **clear**: score CI [{top.low:.1f}, {top.high:.1f}] does not overlap "
                f"the runner-up's [{runner_up.low:.1f}, {runner_up.high:.1f}]."
            )
    lines.append(f"- Coverage check: {winner.metrics.support_coverage_warning}")
    lines.append("")
    return lines


def _recommendation_section(ranked: list[PolicyEvaluationResult]) -> list[str]:
    recommendations = recommend_rollout(ranked)
    lines = [
        "## Rollout Recommendation",
        "",
        "Safety and coverage are hard vetoes: a policy that fails them cannot be "
        "`canary`, regardless of score. Thresholds are documented in "
        "`docs/evaluation_methodology.md`.",
        "",
        "| Policy | Verdict | Why |",
        "|---|---|---|",
    ]
    for result in ranked:
        rec = recommendations[result.policy_name]
        lines.append(f"| {result.policy_name} | `{rec.verdict}` | {rec.reason} |")
    lines.append("")
    return lines


def _confidence_section(ranked: list[PolicyEvaluationResult]) -> list[str]:
    if not any(result.confidence is not None for result in ranked):
        return []
    sample = next(result.confidence for result in ranked if result.confidence is not None)
    lines = [
        "## Confidence Intervals",
        "",
        f"Seeded bootstrap, {sample.confidence:.0%} interval over {sample.iterations} resamples.",
        "",
        "| Policy | Score (CI) | Success (CI) | Unsafe (CI) |",
        "|---|---|---|---|",
    ]
    for result in ranked:
        if result.confidence is None:
            continue
        score = result.confidence.intervals["score"]
        success = result.confidence.intervals["success_rate"]
        unsafe = result.confidence.intervals["unsafe_action_rate"]
        lines.append(
            f"| {result.policy_name} | {score.point:.1f} [{score.low:.1f}, {score.high:.1f}] | "
            f"{success.point:.2%} [{success.low:.2%}, {success.high:.2%}] | "
            f"{unsafe.point:.2%} [{unsafe.low:.2%}, {unsafe.high:.2%}] |"
        )
    lines.append("")
    return lines


def _off_policy_section(ranked: list[PolicyEvaluationResult]) -> list[str]:
    if not any(result.off_policy is not None for result in ranked):
        return []
    lines = [
        "## Off-Policy Estimate (IPS / SNIPS)",
        "",
        "Estimated average logged reward per policy, from logged rewards and "
        "propensities — a different question than the oracle-anchored score. "
        "Low-confidence rows rest on thin overlap with the logged actions and "
        "should not be trusted as point estimates.",
        "",
        "| Policy | IPS | SNIPS | Matched/N | Confidence |",
        "|---|---:|---:|---:|---|",
    ]
    for result in ranked:
        estimate = result.off_policy
        if estimate is None:
            continue
        if not estimate.available:
            lines.append(f"| {result.policy_name} | n/a | n/a | 0/{estimate.n} | unavailable (no logged reward) |")
            continue
        ips = "n/a" if estimate.ips is None else f"{estimate.ips:.3f}"
        snips = "n/a" if estimate.snips is None else f"{estimate.snips:.3f}"
        confidence = "⚠️ low-confidence" if estimate.low_confidence else "ok"
        lines.append(f"| {result.policy_name} | {ips} | {snips} | {estimate.matched}/{estimate.n} | {confidence} |")
    lines.append("")
    lines.append(
        "_Low-confidence off-policy estimates are extrapolation, not measurement: "
        "the candidate rarely took the actions the logs recorded, so the "
        "importance-weighted sample is thin. They are reported for transparency, "
        "not as evidence for rollout._"
    )
    lines.append("")
    return lines


def _support_section(winner: PolicyEvaluationResult) -> list[str]:
    """Per-(intent, tool) support for the winner, highlighting thin cells (#9)."""
    if not winner.scored_rows:
        return []
    cells = Counter((row["intent"], row["candidate_tool"]) for row in winner.scored_rows)
    support = {(row["intent"], row["candidate_tool"]): int(row.get("support_count", 0)) for row in winner.scored_rows}
    lines = [
        f"## Support Diagnostics for `{winner.policy_name}`",
        "",
        "How often the winner's chosen `(intent, tool)` pairs appear in the logs. "
        f"Cells below {_SUPPORT_THRESHOLD} historical matches are flagged: the "
        "counterfactual estimate for those decisions is mostly extrapolation and "
        "should not be trusted.",
        "",
        "| Intent | Tool | Decisions | Historical Support | Trust |",
        "|---|---|---:|---:|---|",
    ]
    for (intent, tool), decisions in sorted(cells.items(), key=lambda item: (-item[1], item[0])):
        historical = support.get((intent, tool), 0)
        thin = historical < _SUPPORT_THRESHOLD
        lines.append(f"| {intent} | {tool} | {decisions} | {historical} | {'⚠️ thin' if thin else 'ok'} |")
    lines.append("")
    return lines


def _dataset_profile_section(logged_rows: list[dict[str, Any]]) -> list[str]:
    """Profile the input log so an unrepresentative dataset is visible (#114)."""
    if not logged_rows:
        return []
    n = len(logged_rows)
    intents = Counter(str(row["intent"]) for row in logged_rows)
    failures = Counter(str(row.get("failure_type", "")) for row in logged_rows if row.get("failure_type"))
    approval_required = sum(1 for row in logged_rows if bool(row.get("requires_approval", False)))

    lines = [
        "## Dataset Profile",
        "",
        f"The evaluation read **{n}** logged decisions. Metrics are only as representative as this input.",
        "",
        f"- Approval-required decisions: {approval_required / n:.1%}",
        "",
        "Intent mix:",
        "",
        "| Intent | Share |",
        "|---|---:|",
    ]
    for intent, count in intents.most_common():
        lines.append(f"| {intent} | {count / n:.1%} |")
    if failures:
        lines.extend(["", "Logged failure types:", "", "| Failure type | Share |", "|---|---:|"])
        for failure, count in failures.most_common():
            lines.append(f"| {failure} | {count / n:.1%} |")
    lines.append("")
    return lines


def _segmentation_section(winner: PolicyEvaluationResult) -> list[str]:
    """Per-intent outcome breakdown for the winner (#114)."""
    if not winner.scored_rows:
        return []
    by_intent: dict[str, list[dict[str, Any]]] = {}
    for row in winner.scored_rows:
        by_intent.setdefault(str(row["intent"]), []).append(row)
    lines = [
        f"## Outcomes by Intent for `{winner.policy_name}`",
        "",
        "| Intent | Decisions | Success | Correct Tool | Unresolved |",
        "|---|---:|---:|---:|---:|",
    ]
    for intent in sorted(by_intent):
        rows = by_intent[intent]
        count = len(rows)
        success = sum(1 for row in rows if bool(row["success"])) / count
        correct = sum(1 for row in rows if row["candidate_tool"] == row["oracle_tool"]) / count
        unresolved = sum(1 for row in rows if not bool(row["resolved"])) / count
        lines.append(f"| {intent} | {count} | {success:.1%} | {correct:.1%} | {unresolved:.1%} |")
    lines.append("")
    return lines


def _pareto_section(ranked: list[PolicyEvaluationResult]) -> list[str]:
    frontier = pareto_frontier(ranked)
    lines = [
        "## Pareto Frontier",
        "",
        "Policies not dominated by any other across success (↑), unsafe rate (↓), "
        "cost (↓), and latency (↓). A policy off the frontier is beaten on every "
        "one of those objectives by someone on it.",
        "",
    ]
    for result in ranked:
        on_frontier = result.policy_name in frontier
        marker = "**on frontier**" if on_frontier else "dominated"
        lines.append(f"- `{result.policy_name}`: {marker}")
    lines.append("")
    return lines


def _limits_section() -> list[str]:
    """What offline evaluation cannot prove, in the report itself (#14)."""
    return [
        "## What This Cannot Prove",
        "",
        "- This is offline replay on synthetic, historical-style logs — not "
        "production telemetry. Numbers do not prove production safety.",
        "- Oracle-anchored metrics assume the labelled `oracle_tool` is correct; a "
        "mislabelled oracle silently biases every score.",
        "- Off-policy (IPS/SNIPS) estimates are unreliable where a candidate routes "
        "into actions the logs rarely took; those rows are flagged, not hidden.",
        "- Offline evaluation cannot capture user adaptation, long-term effects, or "
        "live prompt-injection. Pair it with online monitoring, red-teaming, and "
        "human review for high-risk actions.",
        "",
        "### When NOT to rely on this",
        "",
        "- The logs are tiny or unrepresentative of production traffic.",
        "- The winning policy carries a low-support or low-confidence flag.",
        "- The change is high-risk (irreversible writes) and has had no red-team pass.",
        "",
    ]


def build_markdown_report(
    results: list[PolicyEvaluationResult],
    *,
    logged_rows: list[dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> str:
    header = ["# Agent Routing Evaluation Report", "", f"Generated: {_generated_at(generated_at)}", ""]
    if not results:
        return "\n".join(header + ["_No policies were evaluated, so there is nothing to report._"])

    ranked = rank_results(results)
    winner = ranked[0]

    lines: list[str] = list(header)
    lines += _comparison_table(ranked)
    lines.append("")
    lines += _winner_section(ranked)
    lines += _recommendation_section(ranked)
    lines += _confidence_section(ranked)
    lines += _off_policy_section(ranked)
    lines += _support_section(winner)
    if logged_rows:
        lines += _dataset_profile_section(logged_rows)
    lines += _segmentation_section(winner)
    lines += _pareto_section(ranked)
    lines += _limits_section()

    lines += ["## Warnings", ""]
    warning_count = 0
    for result in ranked:
        for warning in result.warnings:
            lines.append(f"- **{result.policy_name}**: {warning}")
            warning_count += 1
    if warning_count == 0:
        lines.append("- No warnings detected.")

    lines += [
        "",
        "## Notes",
        "",
        "- This is offline replay on synthetic historical-style data.",
        "- Use this report as a pre-rollout gate before online A/B tests.",
    ]
    return "\n".join(lines)


def write_markdown_report(
    path: Path,
    results: list[PolicyEvaluationResult],
    *,
    logged_rows: list[dict[str, Any]] | None = None,
    generated_at: str | None = None,
) -> None:
    atomic_write_text(path, build_markdown_report(results, logged_rows=logged_rows, generated_at=generated_at))
