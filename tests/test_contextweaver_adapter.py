from agent_routing_eval_lab.adapters.contextweaver_adapter import (
    ContextWeaverAdapter,
    ToolCard,
    card_token_estimate,
)
from agent_routing_eval_lab.evaluation.contextweaver_experiment import run_contextweaver_experiment
from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs

_TOOLS = [
    "crm.search_customer",
    "billing.get_invoice",
    "billing.issue_refund",
    "docs.search_policy",
    "support.search_tickets",
]


def test_build_tool_cards_honors_max_cards() -> None:
    adapter = ContextWeaverAdapter()
    cards = adapter.build_tool_cards(available_tools=_TOOLS, intent="refund_request", max_cards=3)
    assert len(cards) == 3
    assert all(isinstance(card, ToolCard) for card in cards)


def test_build_tool_cards_ranking_is_stable_and_relevant() -> None:
    adapter = ContextWeaverAdapter()
    first = adapter.build_tool_cards(available_tools=_TOOLS, intent="refund_request", max_cards=5)
    second = adapter.build_tool_cards(available_tools=list(reversed(_TOOLS)), intent="refund_request", max_cards=5)
    # Ranking depends only on the tool set + intent, not input order.
    assert [c.name for c in first] == [c.name for c in second]
    # The refund tool shares the "refund" token with the intent, so it ranks first.
    assert first[0].name == "billing.issue_refund"


def test_card_token_estimate_scales_with_card_count() -> None:
    adapter = ContextWeaverAdapter()
    two = adapter.build_tool_cards(available_tools=_TOOLS, intent="policy_lookup", max_cards=2)
    four = adapter.build_tool_cards(available_tools=_TOOLS, intent="policy_lookup", max_cards=4)
    assert card_token_estimate(four) > card_token_estimate(two)


def test_bounded_experiment_reports_fewer_cards_and_tokens_than_unbounded() -> None:
    logs = [record.to_dict() for record in generate_synthetic_logs(rows=120, seed=9)]
    experiment = run_contextweaver_experiment(logs, bounded_max_cards=4)

    # Bounding necessarily shows no more cards and spends no more token budget.
    assert experiment.bounded.avg_cards_shown <= experiment.unbounded.avg_cards_shown
    assert experiment.bounded.avg_token_budget <= experiment.unbounded.avg_token_budget
    assert experiment.token_savings >= 0.0
    # Both arms report a correct-tool rate in [0, 1].
    assert 0.0 <= experiment.bounded.correct_tool_rate <= 1.0
    assert 0.0 <= experiment.unbounded.correct_tool_rate <= 1.0
