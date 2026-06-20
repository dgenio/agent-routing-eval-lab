import csv

import pytest

from agent_routing_eval_lab.io_utils import atomic_write_csv, atomic_write_text


def test_atomic_write_text_creates_file_and_parents(tmp_path) -> None:
    target = tmp_path / "nested" / "out.txt"
    atomic_write_text(target, "hello\nworld\n")

    assert target.read_text(encoding="utf-8") == "hello\nworld\n"
    # No temp files left behind on success.
    assert list(target.parent.glob(".*tmp")) == []


def test_atomic_write_text_leaves_no_partial_file_on_failure(tmp_path, monkeypatch) -> None:
    target = tmp_path / "out.txt"
    target.write_text("original", encoding="utf-8")

    def boom(*args, **kwargs):
        raise RuntimeError("interrupted")

    monkeypatch.setattr("agent_routing_eval_lab.io_utils.os.replace", boom)
    with pytest.raises(RuntimeError, match="interrupted"):
        atomic_write_text(target, "new content")

    # The original file is untouched and no temp file is orphaned.
    assert target.read_text(encoding="utf-8") == "original"
    assert [p.name for p in tmp_path.iterdir()] == ["out.txt"]


def test_atomic_write_csv_round_trip(tmp_path) -> None:
    target = tmp_path / "rows.csv"
    rows = [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]
    atomic_write_csv(target, ["a", "b"], rows)

    with target.open(newline="", encoding="utf-8") as file:
        loaded = list(csv.DictReader(file))
    assert loaded == rows
