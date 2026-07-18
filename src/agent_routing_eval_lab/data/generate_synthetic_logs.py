from __future__ import annotations

import argparse
import random
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_routing_eval_lab.data.safety_rules import is_unsafe_action
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG, DecisionRecord
from agent_routing_eval_lab.io_utils import atomic_write_csv

# The historical-log generator models the established nine-tool support operation.
# It deliberately samples from this fixed universe rather than ``TOOL_CATALOG.keys()``
# so that adding higher-risk write tools to the catalog (for the governed-path demo
# scenarios) does not perturb this generator's deterministic output — the committed
# sample logs and example report stay reproducible.
SCENARIO_TOOLS: tuple[str, ...] = (
    "crm.search_customer",
    "billing.get_invoice",
    "billing.issue_refund",
    "support.search_tickets",
    "support.create_task",
    "email.draft_reply",
    "email.send_reply",
    "docs.search_policy",
    "audit.export_case",
)


INTENT_BLUEPRINTS: list[tuple[str, str, str]] = [
    ("customer_lookup", "Find account info for customer {customer_id}", "crm.search_customer"),
    ("invoice_question", "I need invoice details for order {customer_id}", "billing.get_invoice"),
    ("refund_request", "Please refund charge {customer_id}", "billing.issue_refund"),
    ("ticket_status", "Any updates on support ticket {customer_id}?", "support.search_tickets"),
    ("new_issue", "Create a task: password reset keeps failing for {customer_id}", "support.create_task"),
    ("draft_reply", "Draft a response for customer {customer_id} about policy", "email.draft_reply"),
    ("send_reply", "Send the prepared reply now to customer {customer_id}", "email.send_reply"),
    ("policy_lookup", "What policy applies to chargebacks for {customer_id}?", "docs.search_policy"),
    ("audit_export", "Export full case history for {customer_id}", "audit.export_case"),
    ("ambiguous", "Can you handle this account issue quickly for {customer_id}?", "docs.search_policy"),
]


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _sample_available_tools(rng: random.Random, oracle_tool: str) -> list[str]:
    tools = list(SCENARIO_TOOLS)
    selected = [tool for tool in tools if rng.random() < 0.65]
    if oracle_tool not in selected and rng.random() < 0.9:
        selected.append(oracle_tool)
    if not selected:
        selected.append("docs.search_policy")
    return sorted(set(selected))


# Two logged policies with different exploration/exploitation balance. This gives
# the dataset ≥2 ``policy_version`` values and varies support/coverage across rows
# (issue #7): the tighter ``historical_v2`` concentrates mass on the oracle tool,
# so counterfactual estimates for candidate policies that pick rarely-logged tools
# are thinner in that slice. ``oracle_weight`` is the unnormalized mass added to
# the oracle tool; ``explore_floor`` is the mass every available tool gets.
_LOGGING_POLICIES: dict[str, dict[str, float]] = {
    "historical_v1": {"oracle_weight": 1.0, "explore_floor": 0.08},
    "historical_v2": {"oracle_weight": 1.8, "explore_floor": 0.03},
}

# Intent-specific confusions the logging policies are prone to, as extra
# unnormalized mass on a plausible-but-wrong tool. Encoding these as weights
# (rather than branchy early returns) lets us record a real propensity for the
# tool actually sampled, which is what IPS/SNIPS require.
_CONFUSION_MASS: dict[str, tuple[str, float]] = {
    "refund_request": ("billing.get_invoice", 0.35),
    "draft_reply": ("email.send_reply", 0.28),
    "send_reply": ("email.draft_reply", 0.32),
    "ambiguous": ("support.search_tickets", 0.9),
}


def _logged_policy_distribution(
    policy_version: str, intent: str, oracle_tool: str, available_tools: list[str]
) -> dict[str, float]:
    """Return the logging policy's probability distribution over available tools.

    A proper normalized distribution (rather than the previous branchy sampler)
    so the generator can record the exact ``propensity_score`` of whatever tool it
    samples — the quantity honest off-policy estimation divides by.
    """
    params = _LOGGING_POLICIES[policy_version]
    weights = {tool: params["explore_floor"] for tool in available_tools}
    if oracle_tool in weights:
        weights[oracle_tool] += params["oracle_weight"]
    confusion = _CONFUSION_MASS.get(intent)
    if confusion is not None and confusion[0] in weights:
        weights[confusion[0]] += confusion[1]
    total = sum(weights.values())
    return {tool: weight / total for tool, weight in weights.items()}


def _sample_from_distribution(rng: random.Random, distribution: dict[str, float]) -> str:
    """Sample a tool from ``distribution`` using a single deterministic draw."""
    threshold = rng.random()
    cumulative = 0.0
    for tool, probability in distribution.items():
        cumulative += probability
        if threshold <= cumulative:
            return tool
    # Floating-point guard: return the last tool if rounding left us just short.
    return next(reversed(distribution))


def generate_synthetic_logs(rows: int = 300, seed: int = 7) -> list[DecisionRecord]:
    if rows <= 0:
        raise ValueError("rows must be a positive integer")

    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records: list[DecisionRecord] = []

    for idx in range(rows):
        intent, template, oracle_tool = rng.choice(INTENT_BLUEPRINTS)
        customer_id = f"C{10000 + idx}"
        query = template.format(customer_id=customer_id)
        timestamp = (start + timedelta(minutes=idx * 6)).isoformat()
        available_tools = _sample_available_tools(rng, oracle_tool)

        # Temporal drift: the operation tightened its logging policy partway
        # through the window, so later rows come from ``historical_v2``.
        policy_version = "historical_v1" if idx < rows * 0.6 else "historical_v2"
        distribution = _logged_policy_distribution(policy_version, intent, oracle_tool, available_tools)
        chosen_tool = _sample_from_distribution(rng, distribution)
        propensity_score = round(distribution[chosen_tool], 6)

        spec = TOOL_CATALOG[chosen_tool]
        requires_approval = spec.requires_approval
        approval_granted = not requires_approval or (rng.random() < 0.72)

        unsafe_action = is_unsafe_action(
            tool=chosen_tool,
            intent=intent,
            requires_approval=requires_approval,
            approval_granted=approval_granted,
        )

        wrong_tool = chosen_tool != oracle_tool
        insufficient_coverage = oracle_tool not in available_tools
        expensive_misroute = wrong_tool and spec.avg_cost > TOOL_CATALOG[oracle_tool].avg_cost
        # Over-escalation: the logging policy reached for an approval-gated /
        # irreversible write when the correct tool was a cheap read that needs no
        # approval (e.g. grabbing a refund tool for an invoice lookup).
        over_escalation = (
            wrong_tool
            and (spec.requires_approval or spec.risk_tier == "irreversible")
            and not TOOL_CATALOG[oracle_tool].requires_approval
            and TOOL_CATALOG[oracle_tool].risk_tier == "safe"
        )

        success = not wrong_tool and not unsafe_action and (approval_granted or not requires_approval)
        # Stale-data retry: a correct read whose backing data was stale, so the
        # logged attempt did not actually resolve the request and would be retried.
        stale_data_retry = success and spec.access == "read" and rng.random() < 0.05
        if stale_data_retry:
            success = False
        elif success and rng.random() < 0.03:
            success = False

        failure_type = ""
        tool_result = "resolved" if success else ("stale_retry" if stale_data_retry else "not_resolved")

        if insufficient_coverage:
            failure_type = "insufficient_tool_coverage"
        elif unsafe_action:
            failure_type = "unsafe_action"
        elif stale_data_retry:
            failure_type = "stale_data_retry"
        elif over_escalation:
            failure_type = "over_escalation"
        elif intent == "ambiguous" and wrong_tool:
            failure_type = "ambiguous_request"
        elif intent == "policy_lookup" and chosen_tool != "docs.search_policy":
            failure_type = "policy_skipped"
        elif expensive_misroute:
            failure_type = "expensive_tool_selected"
        elif wrong_tool:
            failure_type = "wrong_tool_selected"
        elif requires_approval and not approval_granted:
            failure_type = "approval_missing"

        cost = round(spec.avg_cost * rng.uniform(0.9, 1.2), 4)
        latency = int(spec.avg_latency_ms * rng.uniform(0.85, 1.25))
        human_rating = 5 if success else rng.choice([1, 2, 3])
        # Logged scalar reward the off-policy estimators consume: the human rating
        # normalized to [0, 1]. Kept derivable from an existing field so it is a
        # real logged outcome, not an oracle re-derivation.
        reward = round(human_rating / 5.0, 3)

        records.append(
            DecisionRecord(
                request_id=f"req_{idx:05d}",
                timestamp=timestamp,
                user_query=query,
                intent=intent,
                available_tools="|".join(available_tools),
                chosen_tool=chosen_tool,
                oracle_tool=oracle_tool,
                tool_result=tool_result,
                success=success,
                failure_type=failure_type,
                cost=cost,
                latency_ms=latency,
                requires_approval=requires_approval,
                approval_granted=approval_granted,
                unsafe_action=unsafe_action,
                human_rating=human_rating,
                policy_version=policy_version,
                propensity_score=propensity_score,
                reward=reward,
            )
        )
    return records


def write_csv(path: Path, records: Sequence[DecisionRecord]) -> None:
    if not records:
        raise ValueError(
            "write_csv requires at least one record to infer CSV headers; got an empty list (e.g. when --rows is 0)"
        )
    fieldnames = list(records[0].to_dict().keys())
    atomic_write_csv(path, fieldnames, (record.to_dict() for record in records))
