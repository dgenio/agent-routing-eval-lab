from agent_routing_eval_lab.evaluation.linting import (
    BAD_PROPENSITY,
    ORACLE_UNAVAILABLE,
    POSSIBLE_ORACLE_LEAK,
    UNAVAILABLE_CHOSEN,
    has_errors,
    lint_logged_decisions,
)


def _row(**overrides):
    row = {
        "request_id": "r1",
        "available_tools": "a|b",
        "chosen_tool": "a",
        "oracle_tool": "a",
    }
    row.update(overrides)
    return row


def test_unavailable_chosen_is_an_error() -> None:
    findings = lint_logged_decisions([_row(chosen_tool="z", available_tools="a|b", oracle_tool="a")])
    codes = {f.code for f in findings}
    assert UNAVAILABLE_CHOSEN in codes
    assert has_errors(findings) is True


def test_oracle_unavailable_is_a_warning() -> None:
    findings = lint_logged_decisions([_row(oracle_tool="z", available_tools="a|b", chosen_tool="a")])
    codes = {f.code for f in findings}
    assert ORACLE_UNAVAILABLE in codes
    assert has_errors(findings) is False


def test_bad_propensity_flagged() -> None:
    findings = lint_logged_decisions([_row(propensity_score=1.5)])
    assert BAD_PROPENSITY in {f.code for f in findings}


def test_possible_oracle_leak_when_never_wrong() -> None:
    rows = [_row(request_id=f"r{i}", chosen_tool="a", oracle_tool="a") for i in range(5)]
    assert POSSIBLE_ORACLE_LEAK in {f.code for f in lint_logged_decisions(rows)}


def test_no_leak_flag_when_sometimes_wrong() -> None:
    rows = [_row(chosen_tool="a", oracle_tool="a"), _row(request_id="r2", chosen_tool="a", oracle_tool="b")]
    assert POSSIBLE_ORACLE_LEAK not in {f.code for f in lint_logged_decisions(rows)}
