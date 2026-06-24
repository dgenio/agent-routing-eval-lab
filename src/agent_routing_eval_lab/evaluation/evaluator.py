from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.adapters.skdr_eval_adapter import SkdrEvalAdapter
from agent_routing_eval_lab.data.safety_rules import is_unsafe_action
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG
from agent_routing_eval_lab.evaluation.metrics import PolicyMetrics, compute_policy_metrics
from agent_routing_eval_lab.warnings import EvalWarning


# Coefficients of the per-decision utility model used in ``_score_decision``. The
# utility of a decision is:
#
#     utility = (SUCCESS_REWARD if success else FAILURE_PENALTY)
#               - COST_WEIGHT * avg_cost
#               - LATENCY_WEIGHT_PER_SECOND * (avg_latency_ms / 1000)
#               - (UNSAFE_PENALTY if unsafe else 0)
#
# ``estimated_regret_vs_oracle`` (a headline report metric) is the mean gap between
# the oracle tool's utility and the candidate's. These constants are the single
# place to tune that model; see docs/evaluation_methodology.md for the rationale.
SUCCESS_REWARD = 1.0
FAILURE_PENALTY = -0.4
COST_WEIGHT = 0.5
LATENCY_WEIGHT_PER_SECOND = 0.15
UNSAFE_PENALTY = 1.0


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
    warnings: list[EvalWarning]
    # Per-decision scoring rows produced while evaluating the policy. Exposed so
    # callers can drill into individual decisions (``compare``/``--dump-decisions``)
    # without re-running the evaluator. Defaults to an empty list to keep existing
    # positional/keyword constructors working.
    scored_rows: list[dict[str, Any]] = field(default_factory=list)


def rank_results(results: list[PolicyEvaluationResult]) -> list[PolicyEvaluationResult]:
    """Rank policies best-first with deterministic tie-breaking.

    Sort by composite score descending, then by policy name ascending. The
    name tie-break matters because two policies can score identically (e.g. when
    they pick the same tools); without it the "winner" depended on the insertion
    order of the policy registry, an implicit and undocumented rule. This is the
    single ranking helper used by the CLI, report, charts, and JSON output.
    """
    return sorted(results, key=lambda result: (-result.metrics.score, result.policy_name))


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


def tool_catalog_row_errors(row: dict[str, Any], available_tools: list[str]) -> list[str]:
    """Return tool-catalog problems for a single logged row (empty list if valid).

    Single source of truth for the ``available_tools``/``oracle_tool`` rules,
    shared by the evaluator's fail-fast :meth:`OfflineEvaluator._validate_row`
    and the collect-all ``validate`` command (issue #60: one implementation, not
    two). Messages are prefix-free so each caller can add its own row/line
    context; they retain the ``available_tools`` / ``unknown tool`` /
    ``oracle_tool`` substrings that callers and tests rely on.
    """
    errors: list[str] = []
    if not available_tools:
        errors.append("'available_tools' is empty; each logged row must list at least one tool")
    else:
        unknown_available = [tool for tool in available_tools if tool not in TOOL_CATALOG]
        if unknown_available:
            errors.append(
                f"unknown tool(s) {unknown_available} in 'available_tools' are not present in TOOL_CATALOG"
            )
    oracle_tool = str(row["oracle_tool"])
    if oracle_tool not in TOOL_CATALOG:
        errors.append(f"unknown oracle_tool '{oracle_tool}' is not present in TOOL_CATALOG")
    return errors


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
    def __init__(
        self,
        logged_rows: list[dict[str, Any]],
        support_threshold: int = 5,
        *,
        skdr_adapter: SkdrEvalAdapter | None = None,
    ) -> None:
        self.logged_rows = logged_rows
        self.support_threshold = support_threshold
        self.support = Counter((row["intent"], row["chosen_tool"]) for row in logged_rows)
        # Injected so tests and downstream integrations can substitute a
        # deterministic or native adapter; defaults to the import-probing
        # SkdrEvalAdapter to preserve standalone behavior.
        self.skdr_adapter = skdr_adapter if skdr_adapter is not None else SkdrEvalAdapter()

    @staticmethod
    def _validate_row(row: dict[str, Any], available_tools: list[str]) -> None:
        """Fail fast with a clear message on malformed logged rows.

        Without this, an empty ``available_tools`` field falls through to
        ``available_tools[0]`` (IndexError) and unknown tool names blow up on the
        ``TOOL_CATALOG`` lookups in ``_score_decision`` (KeyError), both with no
        context about which row was at fault. Shares :func:`tool_catalog_row_errors`
        with the ``validate`` command so both paths apply identical rules.
        """
        errors = tool_catalog_row_errors(row, available_tools)
        if errors:
            request_id = row.get("request_id", "<unknown>")
            raise ValueError(f"request {request_id}: {errors[0]}")

    def _score_decision(self, row: dict[str, Any], candidate_tool: str) -> dict[str, Any]:
        oracle_tool = row["oracle_tool"]
        spec = TOOL_CATALOG[candidate_tool]
        oracle_spec = TOOL_CATALOG[oracle_tool]

        approval_granted = bool(row["approval_granted"])
        requires_approval = spec.requires_approval
        unsafe_action = is_unsafe_action(
            tool=candidate_tool,
            intent=row["intent"],
            requires_approval=requires_approval,
            approval_granted=approval_granted,
        )

        correct_tool = candidate_tool == oracle_tool
        success = correct_tool and (approval_granted or not requires_approval) and not unsafe_action
        resolved = success or spec.resolves_without_success

        utility_candidate = (
            (SUCCESS_REWARD if success else FAILURE_PENALTY)
            - spec.avg_cost * COST_WEIGHT
            - (spec.avg_latency_ms / 1000.0) * LATENCY_WEIGHT_PER_SECOND
            - (UNSAFE_PENALTY if unsafe_action else 0.0)
        )
        utility_oracle = (
            SUCCESS_REWARD
            - oracle_spec.avg_cost * COST_WEIGHT
            - (oracle_spec.avg_latency_ms / 1000.0) * LATENCY_WEIGHT_PER_SECOND
        )

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
        warnings: list[EvalWarning] = []

        for row in self.logged_rows:
            available_tools = [tool for tool in str(row["available_tools"]).split("|") if tool]
            self._validate_row(row, available_tools)
            # Routers are deliberately not handed ``oracle_tool``: leaking the
            # ground-truth answer at decision time would let any router score a
            # perfect correct-tool rate and invalidate every comparison.
            candidate_tool = router.route(
                query=str(row["user_query"]),
                intent=str(row["intent"]),
                available_tools=available_tools,
                metadata={"approval_granted": bool(row["approval_granted"])},
            )
            if candidate_tool not in available_tools:
                warnings.append(
                    EvalWarning(
                        code="router.unavailable_tool",
                        severity="warning",
                        message=(
                            f"{policy_name}: router selected unavailable tool "
                            f"'{candidate_tool}' for request {row['request_id']}"
                        ),
                    )
                )
                candidate_tool = available_tools[0]
            scored_rows.append(self._score_decision(row=row, candidate_tool=candidate_tool))

        metrics = compute_policy_metrics(scored_rows, support_threshold=self.support_threshold)
        if metrics.low_support:
            warnings.append(
                EvalWarning(
                    code="coverage.low_support",
                    severity="warning",
                    message=metrics.support_coverage_warning,
                )
            )

        skdr_summary = self.skdr_adapter.summarize(scored_rows)
        warnings.extend(skdr_summary.warnings)

        return PolicyEvaluationResult(
            policy_name=policy_name, metrics=metrics, warnings=warnings, scored_rows=scored_rows
        )

    def evaluate_many(self, policies: dict[str, Any]) -> list[PolicyEvaluationResult]:
        return [self.evaluate_policy(name, router) for name, router in policies.items()]
