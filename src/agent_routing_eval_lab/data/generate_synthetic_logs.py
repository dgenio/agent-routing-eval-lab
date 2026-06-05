from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_routing_eval_lab.data.schemas import DecisionRecord, TOOL_CATALOG


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


def _sample_available_tools(rng: random.Random, oracle_tool: str) -> list[str]:
    tools = list(TOOL_CATALOG.keys())
    selected = [tool for tool in tools if rng.random() < 0.65]
    if oracle_tool not in selected and rng.random() < 0.9:
        selected.append(oracle_tool)
    if not selected:
        selected.append("docs.search_policy")
    return sorted(set(selected))


def _logged_policy_choice(rng: random.Random, intent: str, oracle_tool: str, available_tools: list[str]) -> str:
    if intent == "refund_request" and rng.random() < 0.22:
        return "billing.get_invoice" if "billing.get_invoice" in available_tools else available_tools[0]
    if intent == "draft_reply" and rng.random() < 0.18 and "email.send_reply" in available_tools:
        return "email.send_reply"
    if intent == "send_reply" and rng.random() < 0.2 and "email.draft_reply" in available_tools:
        return "email.draft_reply"
    if intent == "ambiguous" and rng.random() < 0.5 and "support.search_tickets" in available_tools:
        return "support.search_tickets"
    if oracle_tool in available_tools and rng.random() < 0.8:
        return oracle_tool
    return rng.choice(available_tools)


def generate_synthetic_logs(rows: int = 300, seed: int = 7) -> list[DecisionRecord]:
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records: list[DecisionRecord] = []

    for idx in range(rows):
        intent, template, oracle_tool = rng.choice(INTENT_BLUEPRINTS)
        customer_id = f"C{10000 + idx}"
        query = template.format(customer_id=customer_id)
        timestamp = (start + timedelta(minutes=idx * 6)).isoformat()
        available_tools = _sample_available_tools(rng, oracle_tool)
        chosen_tool = _logged_policy_choice(rng, intent, oracle_tool, available_tools)

        spec = TOOL_CATALOG[chosen_tool]
        requires_approval = spec.requires_approval
        approval_granted = not requires_approval or (rng.random() < 0.72)

        unsafe_action = (
            (requires_approval and not approval_granted)
            or (chosen_tool == "email.send_reply" and intent in {"refund_request", "draft_reply"})
        )

        wrong_tool = chosen_tool != oracle_tool
        insufficient_coverage = oracle_tool not in available_tools
        expensive_misroute = wrong_tool and spec.avg_cost > TOOL_CATALOG[oracle_tool].avg_cost

        success = not wrong_tool and not unsafe_action and (approval_granted or not requires_approval)
        if success and rng.random() < 0.03:
            success = False

        failure_type = ""
        tool_result = "resolved" if success else "not_resolved"

        if insufficient_coverage:
            failure_type = "insufficient_tool_coverage"
        elif unsafe_action:
            failure_type = "unsafe_action"
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
                policy_version="historical_v1",
            )
        )
    return records


def write_csv(path: Path, records: list[DecisionRecord]) -> None:
    if not records:
        raise ValueError(
            "write_csv requires at least one record to infer CSV headers; "
            "got an empty list (e.g. when --rows is 0)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].to_dict().keys()))
        writer.writeheader()
        for row in records:
            writer.writerow(row.to_dict())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic routing logs")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=300)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = generate_synthetic_logs(rows=args.rows, seed=args.seed)
    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} synthetic rows to {args.output}")


if __name__ == "__main__":
    main()
