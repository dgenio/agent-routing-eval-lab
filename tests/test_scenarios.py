from agent_routing_eval_lab.data.scenarios import (
    SCENARIOS,
    infer_domain,
    simulate_tool_result,
)
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG


def test_every_scenario_uses_catalog_tools() -> None:
    for scenario in SCENARIOS:
        assert scenario.oracle_tool in TOOL_CATALOG
        for tool in scenario.available_tools:
            assert tool in TOOL_CATALOG


def test_scenarios_include_tempting_distractors() -> None:
    # The invoice lookup must expose an irreversible billing write as a distractor,
    # or the full-catalog distraction cannot be demonstrated (#26).
    invoice = next(s for s in SCENARIOS if s.request_id == "sc_0001")
    assert invoice.oracle_tool == "billing.get_invoice"
    assert "billing.issue_refund" in invoice.available_tools
    assert TOOL_CATALOG["billing.issue_refund"].risk_tier == "irreversible"


def test_exactly_one_scenario_carries_injection() -> None:
    injected = [s for s in SCENARIOS if s.injected_result is not None]
    assert len(injected) == 1
    scenario = injected[0]
    assert scenario.injection_target == "billing.issue_refund"
    assert scenario.injection_target in scenario.available_tools


def test_simulate_tool_result_surfaces_injection_only_for_oracle_read() -> None:
    scenario = next(s for s in SCENARIOS if s.injected_result is not None)
    # Reading the oracle tool surfaces the payload; any other tool returns benign data.
    assert simulate_tool_result(scenario, scenario.oracle_tool) == scenario.injected_result
    assert simulate_tool_result(scenario, "billing.issue_refund") != scenario.injected_result


def test_infer_domain_matches_expected_families() -> None:
    assert infer_domain("Show me the invoice", "invoice_question") == "billing"
    assert infer_domain("Draft a reply", "draft_reply") == "email"
    assert infer_domain("no known keywords here", "mystery") is None
