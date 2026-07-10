from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Access = Literal["read", "write"]
RiskTier = Literal["safe", "sensitive", "irreversible"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    avg_cost: float
    avg_latency_ms: int
    sensitive: bool = False
    requires_approval: bool = False
    # Whether selecting this tool resolves (or appropriately defers) a request even
    # when it is not the oracle "success" tool — e.g. opening a support task or
    # drafting a reply is a legitimate resolution, not an unresolved request. Drives
    # the ``unresolved_request_rate`` metric from catalog data instead of a hardcoded
    # tool-name set buried in the evaluator.
    resolves_without_success: bool = False
    # Coarse risk classification consumed by the governed action guard
    # (``governed/action_guard.py``). ``access`` separates read-only lookups from
    # write actions; ``risk_tier`` grades how damaging a wrong/unapproved write is.
    # These are intentionally additive to the older ``sensitive`` / ``requires_approval``
    # flags rather than replacing them: those two are still consumed by the router
    # scoring path and the shared ``is_unsafe_action`` rule, and consolidating them
    # here would be an unrelated refactor of that path. Keep the two views consistent
    # when editing an entry (e.g. an ``irreversible`` write is also ``sensitive``).
    access: Access = "read"
    risk_tier: RiskTier = "safe"


TOOL_CATALOG: dict[str, ToolSpec] = {
    "crm.search_customer": ToolSpec("crm.search_customer", avg_cost=0.02, avg_latency_ms=80),
    "billing.get_invoice": ToolSpec("billing.get_invoice", avg_cost=0.05, avg_latency_ms=130),
    "billing.issue_refund": ToolSpec(
        "billing.issue_refund",
        avg_cost=0.5,
        avg_latency_ms=450,
        sensitive=True,
        requires_approval=True,
        access="write",
        risk_tier="irreversible",
    ),
    "support.search_tickets": ToolSpec("support.search_tickets", avg_cost=0.03, avg_latency_ms=120),
    "support.create_task": ToolSpec(
        "support.create_task",
        avg_cost=0.08,
        avg_latency_ms=170,
        resolves_without_success=True,
        access="write",
        risk_tier="safe",
    ),
    "email.draft_reply": ToolSpec(
        "email.draft_reply",
        avg_cost=0.01,
        avg_latency_ms=70,
        resolves_without_success=True,
        access="write",
        risk_tier="safe",
    ),
    "email.send_reply": ToolSpec(
        "email.send_reply", avg_cost=0.12, avg_latency_ms=100, sensitive=True, access="write", risk_tier="sensitive"
    ),
    "docs.search_policy": ToolSpec(
        "docs.search_policy", avg_cost=0.04, avg_latency_ms=90, resolves_without_success=True
    ),
    "audit.export_case": ToolSpec(
        "audit.export_case",
        avg_cost=0.7,
        avg_latency_ms=600,
        sensitive=True,
        requires_approval=True,
        access="write",
        risk_tier="irreversible",
    ),
    # Higher-risk write tools that complete the support/ops scenario catalog (#22).
    # They are exercised by the unsafe-baseline / governed-path demo scenarios
    # (``data/scenarios.py``), not by the historical-log generator, whose tool
    # universe stays fixed at the original nine (see ``generate_synthetic_logs``).
    # Costs/latencies stay at or below ``audit.export_case`` so the metric
    # normalizers in ``evaluation/metrics.py`` are unchanged.
    "crm.update_customer_note": ToolSpec(
        "crm.update_customer_note",
        avg_cost=0.09,
        avg_latency_ms=150,
        sensitive=True,
        access="write",
        risk_tier="sensitive",
    ),
    "billing.change_payment_method": ToolSpec(
        "billing.change_payment_method",
        avg_cost=0.6,
        avg_latency_ms=400,
        sensitive=True,
        requires_approval=True,
        access="write",
        risk_tier="irreversible",
    ),
}


@dataclass
class DecisionRecord:
    request_id: str
    timestamp: str
    user_query: str
    intent: str
    available_tools: str
    chosen_tool: str
    oracle_tool: str
    tool_result: str
    success: bool
    failure_type: str
    cost: float
    latency_ms: int
    requires_approval: bool
    approval_granted: bool
    unsafe_action: bool
    human_rating: int
    policy_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GovernedDecisionRecord(DecisionRecord):
    """A decision record plus the governance provenance the governed path produces.

    It is a strict superset of :class:`DecisionRecord`, so a CSV of these rows
    loads through :func:`~agent_routing_eval_lab.evaluation.evaluator.load_logged_decisions`
    unchanged — the extra governance columns are simply ignored by the evaluator
    (extra columns are dropped per docs/input-schema.md) while remaining available
    to auditors and the governed-path report (#30).

    Extra fields:

    - ``cards_shown``: the bounded tool choices the agent actually saw (``|``-joined).
    - ``tools_withheld``: tools present in the request but withheld from the agent.
    - ``withheld_reason``: why those tools were withheld (bounded-choice budget).
    - ``action_verdict``: the action-guard decision — ``allow`` / ``downgrade`` /
      ``require_approval`` / ``block``.
    - ``context_firewall_action``: how the tool result was handled before reuse —
      ``raw`` / ``summarized`` / ``sanitized`` / ``bounded``.
    """

    cards_shown: str = ""
    tools_withheld: str = ""
    withheld_reason: str = ""
    action_verdict: str = ""
    context_firewall_action: str = ""
