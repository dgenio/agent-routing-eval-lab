from pathlib import Path

import pytest

from agent_routing_eval_lab.cli import get_cli_surface

_CLI_DOC = Path(__file__).resolve().parent.parent / "docs" / "cli.md"


def _doc_text() -> str:
    return _CLI_DOC.read_text(encoding="utf-8")


def test_every_subcommand_is_documented() -> None:
    text = _doc_text()
    for subcommand in get_cli_surface():
        assert f"`{subcommand}`" in text, f"subcommand '{subcommand}' is missing from docs/cli.md"


@pytest.mark.parametrize("subcommand,options", sorted(get_cli_surface().items()))
def test_every_flag_is_documented(subcommand: str, options: list[str]) -> None:
    text = _doc_text()
    for option in options:
        assert option in text, f"flag '{option}' of '{subcommand}' is missing from docs/cli.md"
