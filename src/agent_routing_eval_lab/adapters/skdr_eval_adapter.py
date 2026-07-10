from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from agent_routing_eval_lab.warnings import EvalWarning, WarningCode


@dataclass
class SkdrAdapterResult:
    summary: dict[str, float]
    warnings: list[EvalWarning]
    used_native_skdr: bool


class SkdrEvalAdapter:
    """Adapter around skdr-eval with explicit fallback behavior.

    This repo remains runnable without external APIs. If skdr-eval is unavailable,
    this adapter computes transparent local summaries and emits a warning.
    """

    def __init__(self) -> None:
        self._native = None
        try:
            import skdr_eval  # type: ignore

            self._native = skdr_eval
        except Exception:
            self._native = None

    def summarize(self, rows: list[dict[str, Any]]) -> SkdrAdapterResult:
        if self._native is not None:
            # Native skdr-eval (a doubly-robust OPE library) is importable, but
            # wiring its API is tracked separately in issue #47 and intentionally
            # NOT done here — so we never silently claim a native run. The honest
            # local IPS/SNIPS estimate in evaluation/off_policy.py is what the
            # evaluator actually reports; this adapter only summarizes raw rows.
            warnings = [
                EvalWarning(
                    code=WarningCode.SKDR_PENDING,
                    severity="info",
                    message=(
                        "skdr-eval is installed but native doubly-robust wiring is deferred to issue #47; "
                        "reporting the local IPS/SNIPS estimate instead of a native skdr-eval run."
                    ),
                )
            ]
        else:
            warnings = [
                EvalWarning(
                    code=WarningCode.SKDR_MISSING,
                    severity="info",
                    message=(
                        "skdr-eval not installed; reporting the local IPS/SNIPS off-policy estimate. "
                        "Install the 'showcase' extra to enable a native doubly-robust cross-check (issue #47)."
                    ),
                )
            ]

        summary = {
            "success_rate": mean(float(row["success"]) for row in rows) if rows else 0.0,
            "avg_cost": mean(float(row["cost"]) for row in rows) if rows else 0.0,
            "avg_latency_ms": mean(float(row["latency_ms"]) for row in rows) if rows else 0.0,
        }
        return SkdrAdapterResult(summary=summary, warnings=warnings, used_native_skdr=False)
