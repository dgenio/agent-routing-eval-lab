from agent_routing_eval_lab.evaluation.report import build_markdown_report


def test_build_markdown_report_handles_empty_results() -> None:
    report = build_markdown_report([])
    assert "# Agent Routing Evaluation Report" in report
    assert "No policies were evaluated" in report
