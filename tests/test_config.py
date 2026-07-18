import pytest

from agent_routing_eval_lab.config import (
    default_catalog_path,
    load_policy_candidates,
    load_tool_catalog,
)
from agent_routing_eval_lab.data.schemas import TOOL_CATALOG
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter

_POLICY_DIR = default_catalog_path().parent / "policy_candidates"


def test_shipped_catalog_yaml_matches_in_code_catalog() -> None:
    # Drift guard (#4): the external YAML must exactly reproduce TOOL_CATALOG,
    # including access/risk_tier/resolves_without_success and every tool.
    loaded = load_tool_catalog(default_catalog_path())
    assert loaded == TOOL_CATALOG


def test_load_policy_candidates_includes_both_contextweaver_variants() -> None:
    policies = load_policy_candidates(_POLICY_DIR)
    assert {"baseline", "cost_aware", "strict_policy", "contextweaver_v1", "contextweaver_v2"} <= set(policies)
    # The two ContextWeaver variants differ by card budget.
    assert isinstance(policies["contextweaver_v1"], ContextWeaverRouter)
    assert policies["contextweaver_v1"].max_cards == 4
    assert policies["contextweaver_v2"].max_cards == 3


def test_load_tool_catalog_rejects_unknown_key(tmp_path) -> None:
    bad = tmp_path / "catalog.yaml"
    bad.write_text("tools:\n  - name: x.y\n    avg_cost: 0.1\n    avg_latency_ms: 10\n    bogus: 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown key"):
        load_tool_catalog(bad)


def test_load_policy_candidates_rejects_unknown_strategy(tmp_path) -> None:
    (tmp_path / "p.yaml").write_text("name: weird\nstrategy: does-not-exist\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown strategy"):
        load_policy_candidates(tmp_path)


def test_load_tool_catalog_rejects_non_mapping_entry(tmp_path) -> None:
    bad = tmp_path / "catalog.yaml"
    bad.write_text("tools:\n  - just_a_string\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a mapping"):
        load_tool_catalog(bad)


def test_load_tool_catalog_rejects_duplicate_tool_names(tmp_path) -> None:
    bad = tmp_path / "catalog.yaml"
    bad.write_text(
        "tools:\n"
        "  - name: x.y\n    avg_cost: 0.1\n    avg_latency_ms: 10\n"
        "  - name: x.y\n    avg_cost: 0.2\n    avg_latency_ms: 20\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate tool name"):
        load_tool_catalog(bad)
