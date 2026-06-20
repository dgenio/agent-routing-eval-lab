from __future__ import annotations

import csv
from pathlib import Path

from agent_routing_eval_lab.data.schemas import TOOL_CATALOG
from agent_routing_eval_lab.evaluation.evaluator import (
    REQUIRED_LOG_COLUMNS,
    _parse_bool,
    _parse_non_negative_float,
    _parse_non_negative_int,
)

_BOOL_COLUMNS = ("success", "requires_approval", "approval_granted", "unsafe_action")


def validate_logged_decisions(path: Path, *, max_errors: int | None = None) -> list[str]:
    """Check a logged-decisions CSV against the schema and return all problems found.

    Unlike :func:`load_logged_decisions` (which fails fast on the first error), this
    collects every row-level error so a bring-your-own-logs user can fix them in one
    pass. Each message carries the CSV line number and ``request_id`` for context. An
    empty list means the file is valid. ``max_errors`` caps how many are reported.
    """
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing_columns = REQUIRED_LOG_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            # Without the required columns there is nothing meaningful to validate per row.
            return [f"missing required column(s): {missing}"]

        for line_number, row in enumerate(reader, start=2):
            request_id = str(row.get("request_id") or "<unknown>")
            prefix = f"line {line_number} (request {request_id})"

            for column in _BOOL_COLUMNS:
                try:
                    _parse_bool(str(row[column]), column=column, request_id=request_id)
                except ValueError as exc:
                    errors.append(f"{prefix}: {exc}")

            try:
                _parse_non_negative_float(str(row["cost"]), column="cost", request_id=request_id)
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")
            try:
                _parse_non_negative_int(str(row["latency_ms"]), column="latency_ms", request_id=request_id)
            except ValueError as exc:
                errors.append(f"{prefix}: {exc}")

            available_tools = [tool for tool in str(row["available_tools"]).split("|") if tool]
            if not available_tools:
                errors.append(f"{prefix}: 'available_tools' is empty; list at least one tool")
            else:
                unknown = [tool for tool in available_tools if tool not in TOOL_CATALOG]
                if unknown:
                    errors.append(f"{prefix}: unknown tool(s) {unknown} in 'available_tools'")

            oracle_tool = str(row["oracle_tool"])
            if oracle_tool and oracle_tool not in TOOL_CATALOG:
                errors.append(f"{prefix}: unknown oracle_tool '{oracle_tool}'")

            if max_errors is not None and len(errors) >= max_errors:
                return errors[:max_errors]

    return errors
