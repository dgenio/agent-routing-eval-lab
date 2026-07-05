from agent_routing_eval_lab.governed.action_guard import (
    ALLOW,
    BLOCK,
    DOWNGRADE,
    REQUIRE_APPROVAL,
    guard_action,
)


def test_read_only_tool_is_allowed() -> None:
    verdict = guard_action(
        tool="crm.search_customer",
        intent="customer_lookup",
        approval_granted=False,
        available_tools=["crm.search_customer"],
    )
    assert verdict.verdict == ALLOW
    assert verdict.effective_tool == "crm.search_customer"


def test_refund_without_approval_requires_approval() -> None:
    verdict = guard_action(
        tool="billing.issue_refund",
        intent="refund_request",
        approval_granted=False,
        available_tools=["billing.issue_refund"],
    )
    assert verdict.verdict == REQUIRE_APPROVAL


def test_refund_with_approval_is_allowed() -> None:
    verdict = guard_action(
        tool="billing.issue_refund",
        intent="refund_request",
        approval_granted=True,
        available_tools=["billing.issue_refund"],
    )
    assert verdict.verdict == ALLOW


def test_payment_method_change_without_approval_requires_approval() -> None:
    verdict = guard_action(
        tool="billing.change_payment_method",
        intent="refund_request",
        approval_granted=False,
        available_tools=["billing.change_payment_method"],
    )
    assert verdict.verdict == REQUIRE_APPROVAL


def test_send_reply_on_draft_intent_downgrades_to_draft() -> None:
    verdict = guard_action(
        tool="email.send_reply",
        intent="draft_reply",
        approval_granted=True,
        available_tools=["email.send_reply", "email.draft_reply"],
    )
    assert verdict.verdict == DOWNGRADE
    assert verdict.effective_tool == "email.draft_reply"


def test_unverified_note_write_without_approval_is_blocked() -> None:
    verdict = guard_action(
        tool="crm.update_customer_note",
        intent="customer_lookup",
        approval_granted=False,
        available_tools=["crm.update_customer_note"],
    )
    assert verdict.verdict == BLOCK


def test_safe_write_is_allowed() -> None:
    verdict = guard_action(
        tool="email.draft_reply",
        intent="draft_reply",
        approval_granted=False,
        available_tools=["email.draft_reply"],
    )
    assert verdict.verdict == ALLOW
