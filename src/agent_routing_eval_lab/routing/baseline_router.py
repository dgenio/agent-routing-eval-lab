from __future__ import annotations


class BaselineRouter:
    name = "baseline"

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        text = f"{intent} {query}".lower()
        if "refund" in text and "billing.issue_refund" in available_tools:
            return "billing.issue_refund"
        if "invoice" in text and "billing.get_invoice" in available_tools:
            return "billing.get_invoice"
        if "ticket" in text and "support.search_tickets" in available_tools:
            return "support.search_tickets"
        if "draft" in text and "email.draft_reply" in available_tools:
            return "email.draft_reply"
        if "send" in text and "email.send_reply" in available_tools:
            return "email.send_reply"
        if "policy" in text and "docs.search_policy" in available_tools:
            return "docs.search_policy"
        return available_tools[0]
