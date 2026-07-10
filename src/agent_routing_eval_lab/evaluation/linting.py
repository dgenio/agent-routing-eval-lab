"""Static policy/data lint for logged decisions (#117).

A fast, replay-free pass that catches safety- and leakage-relevant problems in a
logged-decisions dataset before the full evaluator runs: actions that were not
even available, oracle labels that no candidate can match, propensities that would
break off-policy weighting, and the tell-tale sign of oracle leakage (a logging
policy that is never wrong). Distinct from ``validate`` (which checks the CSV
schema and types); ``lint`` assumes a schema-valid file and checks its meaning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Lint codes (dotted area.detail, stable for --ignore and JSON consumers).
UNAVAILABLE_CHOSEN = "lint.unavailable_chosen"
ORACLE_UNAVAILABLE = "lint.oracle_unavailable"
BAD_PROPENSITY = "lint.bad_propensity"
POSSIBLE_ORACLE_LEAK = "lint.possible_oracle_leak"

_ERROR = "error"
_WARNING = "warning"


@dataclass(frozen=True)
class LintFinding:
    code: str
    severity: str
    request_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "request_id": self.request_id,
            "message": self.message,
        }


def lint_logged_decisions(rows: list[dict[str, Any]]) -> list[LintFinding]:
    """Return lint findings for a schema-valid logged-decisions dataset."""
    findings: list[LintFinding] = []
    n = len(rows)
    matches_oracle = 0

    for row in rows:
        request_id = str(row.get("request_id", "?"))
        available = [tool for tool in str(row["available_tools"]).split("|") if tool]
        chosen = str(row["chosen_tool"])
        oracle = str(row["oracle_tool"])

        if chosen not in available:
            findings.append(
                LintFinding(
                    UNAVAILABLE_CHOSEN,
                    _ERROR,
                    request_id,
                    f"chosen_tool '{chosen}' is not in available_tools — the logged action was impossible",
                )
            )
        if oracle not in available:
            findings.append(
                LintFinding(
                    ORACLE_UNAVAILABLE,
                    _WARNING,
                    request_id,
                    f"oracle_tool '{oracle}' is not in available_tools — no candidate can ever match it",
                )
            )
        if "propensity_score" in row and str(row.get("propensity_score", "")).strip() != "":
            try:
                propensity = float(row["propensity_score"])
            except (TypeError, ValueError):
                propensity = None
            if propensity is not None and not (0.0 < propensity <= 1.0):
                findings.append(
                    LintFinding(
                        BAD_PROPENSITY,
                        _WARNING,
                        request_id,
                        f"propensity_score {propensity} is outside (0, 1] — it breaks IPS/SNIPS weighting",
                    )
                )
        if chosen == oracle:
            matches_oracle += 1

    if n > 0 and matches_oracle == n:
        findings.append(
            LintFinding(
                POSSIBLE_ORACLE_LEAK,
                _WARNING,
                "*",
                f"chosen_tool equals oracle_tool in 100% of {n} rows — the logging policy may have leaked the oracle",
            )
        )
    return findings


def has_errors(findings: list[LintFinding]) -> bool:
    return any(finding.severity == _ERROR for finding in findings)
