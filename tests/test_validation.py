import csv

from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs
from agent_routing_eval_lab.evaluation.validation import validate_logged_decisions


def _write(path, rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_valid_file_has_no_errors(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    rows = [record.to_dict() for record in generate_synthetic_logs(rows=20, seed=1)]
    _write(path, rows)
    assert validate_logged_decisions(path) == []


def test_missing_columns_reported(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    path.write_text("request_id,user_query\nr1,q\n", encoding="utf-8")
    errors = validate_logged_decisions(path)
    assert len(errors) == 1
    assert "missing required column" in errors[0]


def test_collects_multiple_row_errors_with_context(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    rows = [record.to_dict() for record in generate_synthetic_logs(rows=3, seed=1)]
    rows[0]["success"] = "maybe"
    rows[1]["cost"] = "free"
    _write(path, rows)

    errors = validate_logged_decisions(path)
    assert len(errors) == 2
    assert any("invalid boolean value" in e and "line 2" in e for e in errors)
    assert any("invalid numeric value" in e and "line 3" in e for e in errors)


def test_max_errors_caps_output(tmp_path) -> None:
    path = tmp_path / "logs.csv"
    rows = [record.to_dict() for record in generate_synthetic_logs(rows=5, seed=1)]
    for row in rows:
        row["success"] = "maybe"
    _write(path, rows)

    assert len(validate_logged_decisions(path, max_errors=2)) == 2
