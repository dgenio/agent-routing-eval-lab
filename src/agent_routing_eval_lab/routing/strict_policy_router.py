from __future__ import annotations


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
            return "docs.search_policy" if "docs.search_policy" in available_tools else available_tools[0]

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
        return available_tools[0]
