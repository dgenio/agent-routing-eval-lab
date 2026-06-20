import json

import pytest

from agent_routing_eval_lab import __version__
from agent_routing_eval_lab.cli import EXIT_GATE_FAILED, EXIT_OK, EXIT_USAGE, main
from agent_routing_eval_lab.data.generate_synthetic_logs import generate_synthetic_logs, write_csv


@pytest.fixture()
def sample_csv(tmp_path):
    path = tmp_path / "logs.csv"
    write_csv(path, generate_synthetic_logs(rows=120, seed=3))
    return path


def test_version_prints_and_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_evaluate_text_is_default(capsys, sample_csv) -> None:
    assert main(["evaluate", "--input", str(sample_csv)]) == EXIT_OK
    assert "Winner:" in capsys.readouterr().out


def test_evaluate_json_emits_valid_json(capsys, sample_csv) -> None:
    assert main(["evaluate", "--input", str(sample_csv), "--format", "json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "1"
    assert payload["row_count"] == 120


def test_evaluate_dump_decisions_writes_one_file_per_policy(tmp_path, sample_csv) -> None:
    out = tmp_path / "dump"
    assert main(["evaluate", "--input", str(sample_csv), "--dump-decisions", str(out)]) == EXIT_OK
    files = sorted(p.name for p in out.glob("*_decisions.csv"))
    assert files == [
        "baseline_decisions.csv",
        "contextweaver_v1_decisions.csv",
        "cost_aware_decisions.csv",
        "strict_policy_decisions.csv",
    ]


def test_gate_passes_and_fails_with_documented_exit_codes(capsys, sample_csv) -> None:
    assert main(["gate", "--input", str(sample_csv), "--max-unsafe-rate", "1.0"]) == EXIT_OK
    capsys.readouterr()
    assert main(["gate", "--input", str(sample_csv), "--min-success-rate", "0.99"]) == EXIT_GATE_FAILED
    assert "Gate FAILED" in capsys.readouterr().out


def test_gate_without_thresholds_is_usage_error(capsys, sample_csv) -> None:
    assert main(["gate", "--input", str(sample_csv)]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "at least one threshold" in err


def test_gate_unknown_config_key_is_usage_error(capsys, tmp_path, sample_csv) -> None:
    config = tmp_path / "gate.json"
    config.write_text(json.dumps({"bogus": 1}), encoding="utf-8")
    assert main(["gate", "--input", str(sample_csv), "--config", str(config)]) == EXIT_USAGE
    assert "error:" in capsys.readouterr().err


def test_compare_unknown_policy_is_usage_error(capsys, sample_csv) -> None:
    assert main(["compare", "--input", str(sample_csv), "--policy-a", "baseline", "--policy-b", "nope"]) == EXIT_USAGE
    assert "unknown policy" in capsys.readouterr().err


def test_compare_json_reports_summary(capsys, sample_csv) -> None:
    code = main(
        ["compare", "--input", str(sample_csv), "--policy-a", "baseline", "--policy-b", "strict_policy", "--format", "json"]
    )
    assert code == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["policy_a"] == "baseline"
    assert set(payload["summary"]) == {"regressed", "improved", "neutral"}


def test_validate_ok_and_failure(capsys, tmp_path, sample_csv) -> None:
    assert main(["validate", "--input", str(sample_csv)]) == EXIT_OK
    bad = tmp_path / "bad.csv"
    bad.write_text("request_id,user_query\nr1,q\n", encoding="utf-8")
    assert main(["validate", "--input", str(bad)]) == EXIT_GATE_FAILED
    assert "missing required column" in capsys.readouterr().err


def test_missing_input_file_is_usage_error_without_traceback(capsys, tmp_path) -> None:
    missing = tmp_path / "nope.csv"
    assert main(["evaluate", "--input", str(missing)]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.err.startswith("error:")
    assert "Traceback" not in captured.err


def test_demo_output_dir_writes_artifacts(tmp_path, capsys) -> None:
    out = tmp_path / "run"
    assert main(["demo", "--output-dir", str(out)]) == EXIT_OK
    assert (out / "examples" / "logged_decisions.sample.csv").is_file()
    assert (out / "reports" / "example_report.md").is_file()
    assert str(out) in capsys.readouterr().out
