from __future__ import annotations

from dataclasses import dataclass

# Recognized severities, ordered from least to most urgent. Kept as a small,
# explicit set so downstream consumers (report, gate, JSON) can filter or sort
# without re-deriving the vocabulary from free-form strings.
SEVERITIES = ("info", "warning", "error")


@dataclass(frozen=True)
class EvalWarning:
    """A structured diagnostic raised during evaluation.

    Replaces free-form warning strings (and the fragile substring matching that
    used to detect them) with a stable ``code`` for programmatic handling, a
    ``severity`` for filtering, and a human-readable ``message``. ``__str__``
    returns the message so existing string-formatting call sites keep working.
    """

    code: str
    severity: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"unknown severity '{self.severity}'; expected one of {', '.join(SEVERITIES)}")

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}
