from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agent_routing_eval_lab.adapters.contextweaver_adapter import ContextWeaverAdapter
from agent_routing_eval_lab.data.scenarios import SCENARIOS, Scenario, simulate_tool_result
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG, GovernedDecisionRecord
from agent_routing_eval_lab.governed.action_guard import ALLOW, BLOCK, DOWNGRADE, REQUIRE_APPROVAL, guard_action
from agent_routing_eval_lab.governed.context_firewall import firewall_tool_result

POLICY_VERSION = "governed_v1"

# Bounded choice budget: how many tool cards the agent may see per request. Keeping
# it small is what removes full-catalog distractors before the agent reasons.
MAX_CARDS = 3

# The tool a governed agent reaches for given the request's intent — the minimal
# tool that actually serves the request, not the most capable one available.
_INTENT_PREFERRED_TOOL = {
    "customer_lookup": "crm.search_customer",
    "invoice_question": "billing.get_invoice",
    "refund_request": "billing.issue_refund",
    "ticket_status": "support.search_tickets",
    "new_issue": "support.create_task",
    "draft_reply": "email.draft_reply",
    "send_reply": "email.send_reply",
    "policy_lookup": "docs.search_policy",
    "audit_export": "audit.export_case",
}


def _preferred_pick(intent: str, card_names: list[str]) -> str:
    """Pick the minimal intent-appropriate tool from the bounded card set."""
    preferred = _INTENT_PREFERRED_TOOL.get(intent)
    if preferred is not None and preferred in card_names:
        return preferred
    return card_names[0]


def _run_scenario(
    scenario: Scenario, index: int, adapter: ContextWeaverAdapter
) -> GovernedDecisionRecord:
    available = list(scenario.available_tools)

    # Step 1: bound the choices. Distractors beyond the budget are withheld.
    cards = adapter.build_tool_cards(available_tools=available, intent=scenario.intent, max_cards=MAX_CARDS)
    card_names = [card.name for card in cards]
    withheld = [tool for tool in available if tool not in card_names]

    # Step 2: pick the minimal intent-appropriate tool from the bounded set.
    proposed = _preferred_pick(scenario.intent, card_names)

    # Step 3: context firewall — a read result is treated as untrusted data, so an
    # embedded instruction cannot steer the next step.
    firewall_action = "raw"
    if TOOL_CATALOG[proposed].access == "read":
        firewalled = firewall_tool_result(simulate_tool_result(scenario, proposed))
        firewall_action = firewalled.action

    # Step 4: action guard adjudicates the proposed write/sensitive action.
    verdict = guard_action(
        tool=proposed,
        intent=scenario.intent,
        approval_granted=scenario.approval_granted,
        available_tools=available,
    )

    # The governed agent honors the verdict: it executes only allowed/downgraded
    # actions, and holds/blocks the rest — so it never takes the unsafe action.
    if verdict.verdict in (ALLOW, DOWNGRADE):
        executed_tool = verdict.effective_tool
        executed = True
    else:  # REQUIRE_APPROVAL or BLOCK
        executed_tool = proposed
        executed = False

    spec = TOOL_CATALOG[executed_tool]
    correct_tool = executed and executed_tool == scenario.oracle_tool
    # A downgrade still resolves the request via the safe substitute; a held/blocked
    # action leaves it unresolved (the honest governance trade-off).
    success = correct_tool and executed
    resolved = (executed and (success or spec.resolves_without_success)) or verdict.verdict == DOWNGRADE
    timestamp = (datetime(2026, 3, 1, tzinfo=timezone.utc) + timedelta(minutes=index * 5)).isoformat()

    result_text = simulate_tool_result(scenario, executed_tool) if executed else "[held: not executed]"

    return GovernedDecisionRecord(
        request_id=scenario.request_id,
        timestamp=timestamp,
        user_query=scenario.user_query,
        intent=scenario.intent,
        available_tools="|".join(available),
        chosen_tool=executed_tool,
        oracle_tool=scenario.oracle_tool,
        tool_result=result_text,
        success=success,
        failure_type="" if resolved else "unresolved_pending_governance",
        cost=round(spec.avg_cost, 4) if executed else 0.0,
        latency_ms=spec.avg_latency_ms if executed else 0,
        requires_approval=spec.requires_approval,
        approval_granted=scenario.approval_granted,
        unsafe_action=False,  # governed path honors the guard, so it never acts unsafely
        human_rating=5 if success else 3,
        policy_version=POLICY_VERSION,
        cards_shown="|".join(card_names),
        tools_withheld="|".join(withheld),
        withheld_reason="bounded choice budget" if withheld else "",
        action_verdict=verdict.verdict,
        context_firewall_action=firewall_action,
    )


def run_governed(scenarios: tuple[Scenario, ...] = SCENARIOS) -> list[GovernedDecisionRecord]:
    """Run the governed agent over the scenario set and return auditable logs."""
    adapter = ContextWeaverAdapter()
    return [_run_scenario(scenario, index, adapter) for index, scenario in enumerate(scenarios)]


_VERDICT_EXPLANATIONS = {
    ALLOW: "allowed {tool} (minimal, safe choice).",
    DOWNGRADE: "downgraded to {tool} instead of sending directly.",
    REQUIRE_APPROVAL: "held {tool} for approval rather than acting unilaterally.",
    BLOCK: "blocked {tool} (sensitive write without approval or verification).",
}


def describe_run(records: list[GovernedDecisionRecord]) -> list[str]:
    """Return one plain-language line per governed decision."""
    lines: list[str] = []
    for record in records:
        template = _VERDICT_EXPLANATIONS.get(record.action_verdict, "handled {tool}.")
        detail = template.format(tool=record.chosen_tool)
        firewall = (
            " Tool result was treated as untrusted data."
            if record.context_firewall_action == "sanitized"
            else ""
        )
        lines.append(f"{record.request_id} ({record.intent}): {detail}{firewall}")
    return lines
