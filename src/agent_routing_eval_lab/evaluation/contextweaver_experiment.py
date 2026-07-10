"""Bounded vs unbounded ContextWeaver experiment (#8).

The bounded choice-card idea is only compelling if bounding the tool set actually
helps. This runs the *same* ContextWeaver routing logic twice on identical logs —
once with a small bounded card budget, once seeing every available tool — and
reports the measured difference in correct-tool selection, mis-selection, cost,
and the (illustrative) token budget. The numbers are whatever the heuristic
produces; nothing is staged to guarantee the bounded variant wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_routing_eval_lab.adapters.contextweaver_adapter import TOKENS_PER_CARD
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter

# Wide enough that every request's full available-tool set fits, so the "unbounded"
# arm effectively sees all tools (the anti-pattern the bounded cards guard against).
UNBOUNDED_MAX_CARDS = 999


@dataclass(frozen=True)
class ArmResult:
    label: str
    max_cards: int
    correct_tool_rate: float
    mis_selection_rate: float
    average_cost: float
    avg_cards_shown: float
    avg_token_budget: float


@dataclass(frozen=True)
class ContextWeaverExperiment:
    bounded: ArmResult
    unbounded: ArmResult

    @property
    def mis_selection_delta(self) -> float:
        """Unbounded minus bounded mis-selection rate (positive => bounding helps)."""
        return self.unbounded.mis_selection_rate - self.bounded.mis_selection_rate

    @property
    def token_savings(self) -> float:
        """Average tokens saved per request by bounding the card set."""
        return self.unbounded.avg_token_budget - self.bounded.avg_token_budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "bounded": vars(self.bounded),
            "unbounded": vars(self.unbounded),
            "mis_selection_delta": round(self.mis_selection_delta, 6),
            "token_savings": round(self.token_savings, 3),
        }


def _avg_cards_and_tokens(logged_rows: list[dict[str, Any]], max_cards: int) -> tuple[float, float]:
    """Average cards shown and token budget the adapter would use across the logs."""
    adapter = ContextWeaverRouter(max_cards=max_cards).adapter
    total_cards = 0
    for row in logged_rows:
        available = [tool for tool in str(row["available_tools"]).split("|") if tool]
        cards = adapter.build_tool_cards(available_tools=available, intent=str(row["intent"]), max_cards=max_cards)
        total_cards += len(cards)
    n = len(logged_rows) or 1
    avg_cards = total_cards / n
    return avg_cards, avg_cards * TOKENS_PER_CARD


def _arm(label: str, logged_rows: list[dict[str, Any]], evaluator: OfflineEvaluator, max_cards: int) -> ArmResult:
    result = evaluator.evaluate_policy(label, ContextWeaverRouter(max_cards=max_cards))
    metrics = result.metrics
    avg_cards, avg_tokens = _avg_cards_and_tokens(logged_rows, max_cards)
    return ArmResult(
        label=label,
        max_cards=max_cards,
        correct_tool_rate=metrics.correct_tool_selection_rate,
        mis_selection_rate=1.0 - metrics.correct_tool_selection_rate,
        average_cost=metrics.average_cost,
        avg_cards_shown=round(avg_cards, 3),
        avg_token_budget=round(avg_tokens, 3),
    )


def run_contextweaver_experiment(
    logged_rows: list[dict[str, Any]], *, bounded_max_cards: int = 4
) -> ContextWeaverExperiment:
    """Evaluate a bounded vs an unbounded ContextWeaver variant on the same logs."""
    evaluator = OfflineEvaluator(logged_rows)
    bounded = _arm(f"contextweaver_bounded_{bounded_max_cards}", logged_rows, evaluator, bounded_max_cards)
    unbounded = _arm("contextweaver_unbounded", logged_rows, evaluator, UNBOUNDED_MAX_CARDS)
    return ContextWeaverExperiment(bounded=bounded, unbounded=unbounded)
