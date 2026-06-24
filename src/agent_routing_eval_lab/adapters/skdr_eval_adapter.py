from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

from agent_routing_eval_lab.warnings import EvalWarning


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
            # TODO: Replace placeholder call with official skdr-eval API once stable.
            # We intentionally keep this explicit so behavior is never silently faked.
            warnings = [
                EvalWarning(
                    code="adapter.skdr_pending",
                    severity="info",
                    message="skdr-eval detected, but native API wiring is pending. Using local summary fallback for now.",
                )
            ]
        else:
            warnings = [
                EvalWarning(
                    code="adapter.skdr_missing",
                    severity="info",
                    message="skdr-eval not installed; using local adapter summary fallback.",
                )
            ]

        summary = {
            "success_rate": mean(float(row["success"]) for row in rows) if rows else 0.0,
            "avg_cost": mean(float(row["cost"]) for row in rows) if rows else 0.0,
            "avg_latency_ms": mean(float(row["latency_ms"]) for row in rows) if rows else 0.0,
        }
        return SkdrAdapterResult(summary=summary, warnings=warnings, used_native_skdr=False)
