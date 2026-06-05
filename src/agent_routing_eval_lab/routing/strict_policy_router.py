from __future__ import annotations

from agent_routing_eval_lab.data.schemas import TOOL_CATALOG


def _safe_fallback(available_tools: list[str]) -> str:
    """Pick a tool that is neither sensitive nor approval-gated.

    The strict router must never silently escalate to a sensitive action (e.g.
    ``billing.issue_refund``) just because it happened to be first in
    ``available_tools``. Prefer the first non-sensitive, non-approval tool; only
    if none exists fall back to the first listed tool.
    """
    for tool in available_tools:
        spec = TOOL_CATALOG.get(tool)
        if spec is not None and not spec.sensitive and not spec.requires_approval:
            return tool
    return available_tools[0]


class StrictPolicyRouter:
    name = "strict_policy"

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        metadata = metadata or {}
        approval_granted = bool(metadata.get("approval_granted", False))

        if intent == "refund_request":
            if approval_granted and "billing.issue_refund" in available_tools:
                return "billing.issue_refund"
            if "support.create_task" in available_tools:
                return "support.create_task"
            return "docs.search_policy" if "docs.search_policy" in available_tools else _safe_fallback(available_tools)

        if intent in {"draft_reply", "send_reply"}:
            if "email.draft_reply" in available_tools:
                return "email.draft_reply"

        if intent == "audit_export" and not approval_granted:
            if "support.create_task" in available_tools:
                return "support.create_task"
            if "docs.search_policy" in available_tools:
                return "docs.search_policy"

        if intent == "ambiguous" and "docs.search_policy" in available_tools:
            return "docs.search_policy"

        for preferred in (
            "crm.search_customer",
            "billing.get_invoice",
            "support.search_tickets",
            "support.create_task",
            "docs.search_policy",
        ):
            if preferred in available_tools:
                return preferred
        return _safe_fallback(available_tools)
