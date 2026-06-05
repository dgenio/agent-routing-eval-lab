from __future__ import annotations

from agent_routing_eval_lab.adapters.contextweaver_adapter import ContextWeaverAdapter
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG


class ContextWeaverRouter:
    name = "contextweaver"

    def __init__(self, adapter: ContextWeaverAdapter | None = None) -> None:
        self.adapter = adapter or ContextWeaverAdapter()

    def route(self, query: str, intent: str, available_tools: list[str], metadata: dict | None = None) -> str:
        approval_granted = bool((metadata or {}).get("approval_granted", False))
        cards = self.adapter.build_tool_cards(available_tools=available_tools, intent=intent, max_cards=4)
        card_names = [card.name for card in cards]
        if intent == "refund_request" and "billing.issue_refund" in card_names and approval_granted:
            return "billing.issue_refund"
        if intent in {"draft_reply", "send_reply"} and "email.draft_reply" in card_names:
            return "email.draft_reply"
        if intent == "policy_lookup" and "docs.search_policy" in card_names:
            return "docs.search_policy"
        if intent == "ticket_status" and "support.search_tickets" in card_names:
            return "support.search_tickets"
        return self._safe_card(card_names, available_tools, approval_granted)

    @staticmethod
    def _safe_card(card_names: list[str], available_tools: list[str], approval_granted: bool) -> str:
        """Return the top-ranked card, but never fall back onto a sensitive or
        approval-gated tool (e.g. ``audit.export_case``) when approval is absent.
        """
        for name in card_names:
            spec = TOOL_CATALOG.get(name)
            if approval_granted or spec is None or not (spec.sensitive or spec.requires_approval):
                return name
        if card_names:
            return card_names[0]
        return available_tools[0]
