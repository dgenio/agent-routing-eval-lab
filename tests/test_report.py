from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.evaluation.report import build_markdown_report
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter


def test_build_markdown_report_handles_empty_results() -> None:
    report = build_markdown_report([])
    assert "# Agent Routing Evaluation Report" in report
    assert "No policies were evaluated" in report


def _populated_report() -> str:
    logs = [record.to_dict() for record in generate_synthetic_logs(rows=120, seed=5)]
    results = OfflineEvaluator(logs).evaluate_many(
        {"baseline": BaselineRouter(), "strict_policy": StrictPolicyRouter()}
    )
    return build_markdown_report(results, logged_rows=logs, generated_at="2026-01-01T00:00:00+00:00")


def test_populated_report_renders_all_sections() -> None:
    report = _populated_report()
    for heading in (
        "## Policy Comparison",
        "## Winner:",
        "## Rollout Recommendation",
        "## Confidence Intervals",
        "## Off-Policy Estimate",
        "## Support Diagnostics",
        "## Dataset Profile",
        "## Outcomes by Intent",
        "## Pareto Frontier",
        "## What This Cannot Prove",
        "### When NOT to rely on this",
        "## Warnings",
    ):
        assert heading in report, f"missing section: {heading}"


def test_populated_report_shows_approval_column_and_a_verdict() -> None:
    report = _populated_report()
    assert "Approval Req" in report
    # At least one rollout verdict is rendered as an inline code span.
    assert "`hold`" in report or "`revise`" in report or "`canary`" in report


def test_report_timestamp_is_injectable_for_reproducibility() -> None:
    report = build_markdown_report([], generated_at="2020-02-02T00:00:00+00:00")
    assert "Generated: 2020-02-02T00:00:00+00:00" in report
