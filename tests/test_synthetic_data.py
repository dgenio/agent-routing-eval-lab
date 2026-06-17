import pytest

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs, write_csv


def test_generate_synthetic_logs_fields_and_modes() -> None:
    rows = generate_synthetic_logs(rows=250, seed=11)

    assert len(rows) == 250
    first = rows[0].to_dict()
    expected = {
        "request_id",
        "timestamp",
        "user_query",
        "intent",
        "available_tools",
        "chosen_tool",
        "oracle_tool",
        "tool_result",
        "success",
        "failure_type",
        "cost",
        "latency_ms",
        "requires_approval",
        "approval_granted",
        "unsafe_action",
        "human_rating",
        "policy_version",
    }
    assert expected.issubset(first.keys())

    failure_types = {row.failure_type for row in rows if row.failure_type}
    assert "wrong_tool_selected" in failure_types or "expensive_tool_selected" in failure_types
    assert "unsafe_action" in failure_types or any(row.unsafe_action for row in rows)


def test_write_csv_rejects_empty_records(tmp_path) -> None:
    with pytest.raises(ValueError, match="empty"):
        write_csv(tmp_path / "out.csv", [])


@pytest.mark.parametrize("rows", [0, -1])
def test_generate_synthetic_logs_rejects_non_positive_rows(rows: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        generate_synthetic_logs(rows=rows)
