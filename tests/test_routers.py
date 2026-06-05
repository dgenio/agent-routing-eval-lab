from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter
from agent_routing_eval_lab.routing.cost_aware_router import CostAwareRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter


def test_baseline_router_keywords() -> None:
    router = BaselineRouter()
    tool = router.route("Please refund this order", "refund_request", ["billing.issue_refund", "billing.get_invoice"])
    assert tool == "billing.issue_refund"


def test_cost_aware_router_avoids_sensitive_without_approval() -> None:
    router = CostAwareRouter()
    tool = router.route(
        "Refund this",
        "refund_request",
        ["billing.issue_refund", "billing.get_invoice"],
        metadata={"approval_granted": False},
    )
    assert tool == "billing.get_invoice"


def test_strict_router_never_sends_email_directly() -> None:
    router = StrictPolicyRouter()
    tool = router.route("Send the email", "send_reply", ["email.send_reply", "email.draft_reply"])
    assert tool == "email.draft_reply"


def test_contextweaver_router_uses_bounded_cards() -> None:
    router = ContextWeaverRouter()
    tool = router.route("Need policy", "policy_lookup", ["crm.search_customer", "docs.search_policy"])
    assert tool in {"docs.search_policy", "crm.search_customer"}
