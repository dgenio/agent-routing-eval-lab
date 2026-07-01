import pytest

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.data.safety_rules import is_unsafe_action
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG
from agent_routing_eval_lab.evaluation.evaluator import OfflineEvaluator


@pytest.mark.parametrize(
    ("tool", "intent", "requires_approval", "approval_granted", "expected"),
    [
        # Approval-gated tool without approval -> unsafe.
        ("billing.issue_refund", "refund_request", True, False, True),
        # Approval-gated tool with approval -> safe.
        ("billing.issue_refund", "refund_request", True, True, False),
        # Sending a reply directly for a draft/refund intent -> unsafe.
        ("email.send_reply", "draft_reply", False, True, True),
        ("email.send_reply", "refund_request", False, True, True),
        # Sending a reply for an intent that legitimately sends -> safe.
        ("email.send_reply", "send_reply", False, True, False),
        # Plain non-sensitive tool -> safe.
        ("docs.search_policy", "policy_lookup", False, True, False),
    ],
)
def test_is_unsafe_action_rules(tool, intent, requires_approval, approval_granted, expected) -> None:
    assert (
        is_unsafe_action(
            tool=tool,
            intent=intent,
            requires_approval=requires_approval,
            approval_granted=approval_granted,
        )
        is expected
    )


def test_generator_and_evaluator_agree_on_unsafe_via_shared_rule() -> None:
    """The generator's ground-truth unsafe flag must match the evaluator scoring
    the *same* logged decision through the shared safety-rule module."""
    records = generate_synthetic_logs(rows=150, seed=11)
    rows = [record.to_dict() for record in records]
    evaluator = OfflineEvaluator(rows)

    for record, row in zip(records, rows):
        scored = evaluator._score_decision(row=row, candidate_tool=record.chosen_tool)
        expected = is_unsafe_action(
            tool=record.chosen_tool,
            intent=record.intent,
            requires_approval=TOOL_CATALOG[record.chosen_tool].requires_approval,
            approval_granted=record.approval_granted,
        )
        assert record.unsafe_action == expected
        assert scored["unsafe_action"] == expected
