from __future__ import annotations

from agent_routing_eval_lab.data.schemas import TOOL_CATALOG


class CostAwareRouter:
    name = "cost_aware"

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        metadata = metadata or {}
        approval_granted = bool(metadata.get("approval_granted", False))

        if intent == "refund_request":
            if approval_granted and "billing.issue_refund" in available_tools:
                return "billing.issue_refund"
            if "billing.get_invoice" in available_tools:
                return "billing.get_invoice"

        if intent == "audit_export" and not approval_granted and "docs.search_policy" in available_tools:
            return "docs.search_policy"

        viable = [tool for tool in available_tools if not TOOL_CATALOG[tool].sensitive]
        if not viable:
            viable = available_tools
        return min(viable, key=lambda tool: TOOL_CATALOG[tool].avg_cost)
