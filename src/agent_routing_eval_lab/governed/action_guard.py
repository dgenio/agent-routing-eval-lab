from __future__ import annotations

from dataclasses import dataclass

from agent_routing_eval_lab.data.safety_rules import SEND_REPLY_UNSAFE_INTENTS
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG

# The four possible verdicts for a proposed action.
ALLOW = "allow"
DOWNGRADE = "downgrade"
REQUIRE_APPROVAL = "require_approval"
BLOCK = "block"

VERDICTS = (ALLOW, DOWNGRADE, REQUIRE_APPROVAL, BLOCK)

# Safe substitute a governed agent uses instead of directly sending a reply.
_SEND_DOWNGRADE_TARGET = "email.draft_reply"


@dataclass(frozen=True)
class GuardVerdict:
    """The action guard's decision for one proposed action.

    - ``verdict``: one of ``allow`` / ``downgrade`` / ``require_approval`` / ``block``.
    - ``effective_tool``: the tool that should actually run (differs from the
      proposed tool only on a ``downgrade``).
    - ``reason``: short human-readable justification for logs and the report.
    """

    verdict: str
    effective_tool: str
    reason: str


def guard_action(
    *,
    tool: str,
    intent: str,
    approval_granted: bool,
    available_tools: list[str],
) -> GuardVerdict:
    """Map a proposed action to allow / downgrade / require_approval / block.

    Driven by the catalog's ``access`` / ``risk_tier`` classification (#22, #29):

    - read-only, safe tools are always allowed;
    - sending a customer email for an intent that should be drafted is downgraded to
      a draft when one is available;
    - approval-gated or irreversible writes are allowed only with approval, otherwise
      held for approval;
    - other sensitive writes with no safe substitute are allowed with approval,
      otherwise blocked;
    - remaining safe writes (drafts, task creation) are allowed.

    This guard is a strict superset of the shared ``is_unsafe_action`` rule: every
    action that rule flags (approval bypass, direct send on a draft/refund intent) is
    non-``allow`` here too, plus sensitive/irreversible writes it does not cover.
    """
    spec = TOOL_CATALOG[tool]

    if spec.access == "read" and spec.risk_tier == "safe":
        return GuardVerdict(ALLOW, tool, "read-only, safe tool")

    # Sending a customer-facing reply where the request only warranted a draft.
    if tool == "email.send_reply" and intent in SEND_REPLY_UNSAFE_INTENTS:
        if _SEND_DOWNGRADE_TARGET in available_tools:
            return GuardVerdict(DOWNGRADE, _SEND_DOWNGRADE_TARGET, "downgraded send to draft for review")
        return GuardVerdict(REQUIRE_APPROVAL, tool, "direct send withheld pending approval")

    # Approval-gated or irreversible writes (refunds, payment changes, exports).
    if spec.requires_approval or spec.risk_tier == "irreversible":
        if approval_granted:
            return GuardVerdict(ALLOW, tool, "approval granted for sensitive action")
        return GuardVerdict(REQUIRE_APPROVAL, tool, "sensitive/irreversible action requires approval")

    # Other sensitive writes (e.g. writing an unverified customer note): no safe
    # substitute and no approval workflow -> refuse rather than write blindly.
    if spec.access == "write" and spec.risk_tier == "sensitive":
        if approval_granted:
            return GuardVerdict(ALLOW, tool, "approval granted for sensitive write")
        return GuardVerdict(BLOCK, tool, "sensitive write blocked without approval or verification")

    # Remaining safe writes: drafting a reply, creating a task.
    return GuardVerdict(ALLOW, tool, "safe write")
