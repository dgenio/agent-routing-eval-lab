from __future__ import annotations

from dataclasses import dataclass

# Rough token cost of exposing one tool's schema/card to the model. Used only to
# make the "bounded choices" framing concrete (fewer cards => fewer tokens); it is
# an illustrative constant, not a measured tokenizer output.
TOKENS_PER_CARD = 60


@dataclass(frozen=True)
class ToolCard:
    name: str
    summary: str


def card_token_estimate(cards: list[ToolCard]) -> int:
    """Estimate the prompt-token budget spent exposing ``cards`` to the model."""
    return len(cards) * TOKENS_PER_CARD


class ContextWeaverAdapter:
    """Bounded tool-card selection.

    The ranking here is a **local heuristic**, not the native `contextweaver`
    ranker. If `contextweaver` is installed, native card selection would plug in at
    :meth:`build_tool_cards` (tracked in issue #47); this class never claims a
    native integration it does not have.
    """

    def _relevance(self, tool: str, intent: str) -> tuple[int, int, str]:
        """Deterministic sort key: more intent-relevant tools rank first.

        Relevance is a heuristic over shared tokens between the intent label and
        the dotted tool name (e.g. ``refund_request`` shares ``refund`` with
        ``billing.issue_refund``), with a mild preference for read-only
        ``docs``/``search`` lookups as safe defaults, then the tool name as a
        stable tie-break.
        """
        intent_tokens = {token for token in intent.split("_") if token}
        tool_tokens = {token for part in tool.split(".") for token in part.split("_")}
        overlap = len(intent_tokens & tool_tokens)
        safe_default = tool.startswith("docs") or "search" in tool
        # Negative overlap so higher overlap sorts first under ascending sort.
        return (-overlap, 0 if safe_default else 1, tool)

    def build_tool_cards(self, available_tools: list[str], intent: str, max_cards: int = 4) -> list[ToolCard]:
        """Return at most ``max_cards`` tool cards, most relevant first.

        Bounding the choice set is the whole point of the pattern: exposing every
        tool invites mis-selection and wastes tokens. ``max_cards`` is honored
        exactly; ranking is stable for a fixed input.
        """
        if max_cards < 0:
            raise ValueError("max_cards must be non-negative")
        ranked = sorted(available_tools, key=lambda tool: self._relevance(tool, intent))
        return [ToolCard(name=tool, summary=f"Tool card for {tool}") for tool in ranked[:max_cards]]
