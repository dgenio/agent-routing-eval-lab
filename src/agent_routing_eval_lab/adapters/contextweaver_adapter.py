from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCard:
    name: str
    summary: str


class ContextWeaverAdapter:
    """Adapter for bounded tool cards.

    If `contextweaver` is installed, replace the fallback logic in this class with
    native card-selection calls.
    """

    def build_tool_cards(self, available_tools: list[str], intent: str, max_cards: int = 4) -> list[ToolCard]:
        # TODO: Replace with contextweaver native ranking once integration API is finalized.
        ranked = sorted(
            available_tools,
            key=lambda tool: (
                0 if intent.split("_")[0] in tool else 1,
                0 if tool.startswith("docs") else 1,
                tool,
            ),
        )
        return [ToolCard(name=tool, summary=f"Tool card for {tool}") for tool in ranked[:max_cards]]
