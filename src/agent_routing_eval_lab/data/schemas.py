from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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


TOOL_CATALOG: dict[str, ToolSpec] = {
    "crm.search_customer": ToolSpec("crm.search_customer", avg_cost=0.02, avg_latency_ms=80),
    "billing.get_invoice": ToolSpec("billing.get_invoice", avg_cost=0.05, avg_latency_ms=130),
    "billing.issue_refund": ToolSpec(
        "billing.issue_refund", avg_cost=0.5, avg_latency_ms=450, sensitive=True, requires_approval=True
    ),
    "support.search_tickets": ToolSpec("support.search_tickets", avg_cost=0.03, avg_latency_ms=120),
    "support.create_task": ToolSpec(
        "support.create_task", avg_cost=0.08, avg_latency_ms=170, resolves_without_success=True
    ),
    "email.draft_reply": ToolSpec(
        "email.draft_reply", avg_cost=0.01, avg_latency_ms=70, resolves_without_success=True
    ),
    "email.send_reply": ToolSpec("email.send_reply", avg_cost=0.12, avg_latency_ms=100, sensitive=True),
    "docs.search_policy": ToolSpec(
        "docs.search_policy", avg_cost=0.04, avg_latency_ms=90, resolves_without_success=True
    ),
    "audit.export_case": ToolSpec("audit.export_case", avg_cost=0.7, avg_latency_ms=600, sensitive=True, requires_approval=True),
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
