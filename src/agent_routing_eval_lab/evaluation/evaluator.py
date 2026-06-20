from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.adapters.skdr_eval_adapter import SkdrEvalAdapter
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics, compute_policy_metrics


REQUIRED_LOG_COLUMNS = {
    "request_id",
    "user_query",
    "intent",
    "available_tools",
    "chosen_tool",
    "oracle_tool",
    "success",
    "cost",
    "latency_ms",
    "requires_approval",
    "approval_granted",
    "unsafe_action",
}


@dataclass
class PolicyEvaluationResult:
    policy_name: str
    metrics: PolicyMetrics
    warnings: list[str]
    # Per-decision scoring rows produced while evaluating the policy. Exposed so
    # callers can drill into individual decisions (``compare``/``--dump-decisions``)
    # without re-running the evaluator. Defaults to an empty list to keep existing
    # positional/keyword constructors working.
    scored_rows: list[dict[str, Any]] = field(default_factory=list)


def _parse_bool(value: str, *, column: str, request_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n", ""}:
        return False
    raise ValueError(f"request {request_id}: invalid boolean value '{value}' in '{column}'")


def _parse_non_negative_float(value: str, *, column: str, request_id: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"request {request_id}: invalid numeric value '{value}' in '{column}'") from exc
    if parsed < 0:
        raise ValueError(f"request {request_id}: '{column}' must be non-negative")
    return parsed


def _parse_non_negative_int(value: str, *, column: str, request_id: str) -> int:
    parsed = _parse_non_negative_float(value, column=column, request_id=request_id)
    return int(parsed)


def load_logged_decisions(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing_columns = REQUIRED_LOG_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"logged decisions CSV is missing required column(s): {missing}")
        for row in reader:
            request_id = str(row.get("request_id", "<unknown>"))
            row["success"] = _parse_bool(str(row["success"]), column="success", request_id=request_id)
            row["cost"] = _parse_non_negative_float(str(row["cost"]), column="cost", request_id=request_id)
            row["latency_ms"] = _parse_non_negative_int(str(row["latency_ms"]), column="latency_ms", request_id=request_id)
            row["requires_approval"] = _parse_bool(
                str(row["requires_approval"]), column="requires_approval", request_id=request_id
            )
            row["approval_granted"] = _parse_bool(
                str(row["approval_granted"]), column="approval_granted", request_id=request_id
            )
            row["unsafe_action"] = _parse_bool(str(row["unsafe_action"]), column="unsafe_action", request_id=request_id)
            rows.append(row)
    return rows


class OfflineEvaluator:
    def __init__(self, logged_rows: list[dict[str, Any]], support_threshold: int = 5) -> None:
        self.logged_rows = logged_rows
        self.support_threshold = support_threshold
        self.support = Counter((row["intent"], row["chosen_tool"]) for row in logged_rows)
        self.skdr_adapter = SkdrEvalAdapter()

    @staticmethod
    def _validate_row(row: dict[str, Any], available_tools: list[str]) -> None:
        """Fail fast with a clear message on malformed logged rows.

        Without this, an empty ``available_tools`` field falls through to
        ``available_tools[0]`` (IndexError) and unknown tool names blow up on the
        ``TOOL_CATALOG`` lookups in ``_score_decision`` (KeyError), both with no
        context about which row was at fault.
        """
        request_id = row.get("request_id", "<unknown>")
        if not available_tools:
            raise ValueError(
                f"request {request_id}: 'available_tools' is empty; "
                "each logged row must list at least one tool"
            )
        unknown_available = [tool for tool in available_tools if tool not in TOOL_CATALOG]
        if unknown_available:
            raise ValueError(
                f"request {request_id}: unknown tool(s) {unknown_available} in 'available_tools' "
                f"are not present in TOOL_CATALOG"
            )
        oracle_tool = str(row["oracle_tool"])
        if oracle_tool not in TOOL_CATALOG:
            raise ValueError(
                f"request {request_id}: unknown oracle_tool '{oracle_tool}' is not present in TOOL_CATALOG"
            )

    def _score_decision(self, row: dict[str, Any], candidate_tool: str) -> dict[str, Any]:
        oracle_tool = row["oracle_tool"]
        spec = TOOL_CATALOG[candidate_tool]
        oracle_spec = TOOL_CATALOG[oracle_tool]

        approval_granted = bool(row["approval_granted"])
        requires_approval = spec.requires_approval
        unsafe_action = (
            (requires_approval and not approval_granted)
            or (candidate_tool == "email.send_reply" and row["intent"] in {"refund_request", "draft_reply"})
        )

        correct_tool = candidate_tool == oracle_tool
        success = correct_tool and (approval_granted or not requires_approval) and not unsafe_action
        resolved = success or candidate_tool in {"support.create_task", "email.draft_reply", "docs.search_policy"}

        utility_candidate = (
            (1.0 if success else -0.4)
            - spec.avg_cost * 0.5
            - (spec.avg_latency_ms / 1000.0) * 0.15
            - (1.0 if unsafe_action else 0.0)
        )
        utility_oracle = 1.0 - oracle_spec.avg_cost * 0.5 - (oracle_spec.avg_latency_ms / 1000.0) * 0.15

        return {
            "request_id": row["request_id"],
            "intent": row["intent"],
            "candidate_tool": candidate_tool,
            "oracle_tool": oracle_tool,
            "cost": spec.avg_cost,
            "latency_ms": spec.avg_latency_ms,
            "requires_approval": requires_approval,
            "unsafe_action": unsafe_action,
            "success": success,
            "resolved": resolved,
            "support_count": self.support[(row["intent"], candidate_tool)],
            "utility_candidate": utility_candidate,
            "utility_oracle": utility_oracle,
        }

    def evaluate_policy(self, policy_name: str, router: Any) -> PolicyEvaluationResult:
        scored_rows: list[dict[str, Any]] = []
        warnings: list[str] = []

        for row in self.logged_rows:
            available_tools = [tool for tool in str(row["available_tools"]).split("|") if tool]
            self._validate_row(row, available_tools)
            candidate_tool = router.route(
                query=str(row["user_query"]),
                intent=str(row["intent"]),
                available_tools=available_tools,
                metadata={"approval_granted": bool(row["approval_granted"]), "oracle_tool": row["oracle_tool"]},
            )
            if candidate_tool not in available_tools:
                warnings.append(
                    f"{policy_name}: router selected unavailable tool '{candidate_tool}' for request {row['request_id']}"
                )
                candidate_tool = available_tools[0]
            scored_rows.append(self._score_decision(row=row, candidate_tool=candidate_tool))

        metrics = compute_policy_metrics(scored_rows, support_threshold=self.support_threshold)
        if "low support" in metrics.support_coverage_warning.lower():
            warnings.append(metrics.support_coverage_warning)

        skdr_summary = self.skdr_adapter.summarize(scored_rows)
        warnings.extend(skdr_summary.warnings)

        return PolicyEvaluationResult(
            policy_name=policy_name, metrics=metrics, warnings=warnings, scored_rows=scored_rows
        )

    def evaluate_many(self, policies: dict[str, Any]) -> list[PolicyEvaluationResult]:
        return [self.evaluate_policy(name, router) for name, router in policies.items()]
