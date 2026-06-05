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


def test_strict_router_refund_fallback_avoids_sensitive_without_approval() -> None:
    # No approval, and neither support.create_task nor docs.search_policy available:
    # the fallback must NOT pick the sensitive billing.issue_refund just because it is first.
    router = StrictPolicyRouter()
    tool = router.route(
        "refund", "refund_request", ["billing.issue_refund", "crm.search_customer"], {"approval_granted": False}
    )
    assert tool == "crm.search_customer"


def test_strict_router_audit_export_avoids_sensitive() -> None:
    router = StrictPolicyRouter()
    tool = router.route(
        "export", "audit_export", ["audit.export_case", "billing.get_invoice"], {"approval_granted": False}
    )
    assert tool == "billing.get_invoice"


def test_contextweaver_router_audit_export_avoids_sensitive_without_approval() -> None:
    router = ContextWeaverRouter()
    tool = router.route(
        "export case", "audit_export", ["audit.export_case", "billing.get_invoice"], {"approval_granted": False}
    )
    assert tool == "billing.get_invoice"
