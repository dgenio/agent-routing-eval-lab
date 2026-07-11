"""Load the tool catalog and policy candidates from the ``examples/`` YAML files.

The deterministic core deliberately keeps zero runtime dependencies, so YAML is an
**optional** surface: these loaders import PyYAML lazily and raise a clear, actionable
error when it is missing, rather than being imported at module load. The in-code
``TOOL_CATALOG`` and :func:`agent_routing_eval_lab.cli._policies` remain the
config-free defaults; a drift-guard test asserts the shipped YAML matches them.

Install the optional extra to use these:

    pip install -e .[config]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_routing_eval_lab.data.schemas import ToolSpec
from agent_routing_eval_lab.routing.baseline_router import BaselineRouter
from agent_routing_eval_lab.routing.contextweaver_router import ContextWeaverRouter
from agent_routing_eval_lab.routing.cost_aware_router import CostAwareRouter
from agent_routing_eval_lab.routing.strict_policy_router import StrictPolicyRouter


def _require_yaml():
    """Import PyYAML or raise a clear, actionable error (never a silent fallback).

    Raises ``ValueError`` (not a bare import error) so the CLI reports it as a
    usage error with exit code 2 instead of a traceback.
    """
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise ValueError(
            "Loading YAML config requires PyYAML, which is not installed. "
            "Install the optional extra: pip install -e .[config]"
        ) from exc
    return yaml


def load_tool_catalog(path: Path) -> dict[str, ToolSpec]:
    """Build a ``{name: ToolSpec}`` catalog from a ``tool_catalog.yaml`` file.

    The YAML is the external, human-editable mirror of the in-code ``TOOL_CATALOG``;
    unknown keys raise so a typo cannot silently drop metadata.
    """
    yaml = _require_yaml()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "tools" not in raw:
        raise ValueError(f"{path} must be a mapping with a top-level 'tools' list")

    allowed = {
        "name",
        "avg_cost",
        "avg_latency_ms",
        "sensitive",
        "requires_approval",
        "resolves_without_success",
        "access",
        "risk_tier",
    }
    if not isinstance(raw["tools"], list):
        raise ValueError(f"{path}: 'tools' must be a list, got {type(raw['tools']).__name__}")
    catalog: dict[str, ToolSpec] = {}
    for index, entry in enumerate(raw["tools"]):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: tools[{index}] must be a mapping, got {type(entry).__name__}")
        unknown = set(entry) - allowed
        if unknown:
            name = entry.get("name", "?")
            raise ValueError(f"{path}: tool '{name}' has unknown key(s): {', '.join(sorted(unknown))}")
        if entry["name"] in catalog:
            raise ValueError(f"{path}: duplicate tool name '{entry['name']}'")
        spec = ToolSpec(
            name=entry["name"],
            avg_cost=float(entry["avg_cost"]),
            avg_latency_ms=int(entry["avg_latency_ms"]),
            sensitive=bool(entry.get("sensitive", False)),
            requires_approval=bool(entry.get("requires_approval", False)),
            resolves_without_success=bool(entry.get("resolves_without_success", False)),
            access=entry.get("access", "read"),
            risk_tier=entry.get("risk_tier", "safe"),
        )
        catalog[spec.name] = spec
    return catalog


# Maps a policy-candidate ``strategy`` to a factory taking the parsed YAML entry.
_STRATEGY_FACTORIES = {
    "naive-keyword-router": lambda entry: BaselineRouter(),
    "minimize-cost-under-safety-constraints": lambda entry: CostAwareRouter(),
    "safety-first-with-approval-gating": lambda entry: StrictPolicyRouter(),
    "bounded-tool-cards": lambda entry: ContextWeaverRouter(max_cards=int(entry.get("max_cards", 4))),
}


def _load_policy_entry(entry: dict[str, Any], source: Path) -> tuple[str, object]:
    name = entry.get("name")
    strategy = entry.get("strategy")
    if not name or not strategy:
        raise ValueError(f"{source}: policy candidate must have 'name' and 'strategy'")
    factory = _STRATEGY_FACTORIES.get(strategy)
    if factory is None:
        known = ", ".join(sorted(_STRATEGY_FACTORIES))
        raise ValueError(f"{source}: unknown strategy '{strategy}'. Known strategies: {known}")
    return name, factory(entry)


def load_policy_candidates(directory: Path) -> dict[str, object]:
    """Build ``{name: router}`` from every ``*.yaml`` in ``directory``.

    Loaded in sorted filename order for deterministic registry ordering.
    """
    yaml = _require_yaml()
    files = sorted(directory.glob("*.yaml"))
    if not files:
        raise ValueError(f"no policy-candidate YAML files found in {directory}")
    policies: dict[str, object] = {}
    for file in files:
        entry = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(entry, dict):
            raise ValueError(f"{file} must contain a single YAML mapping")
        name, router = _load_policy_entry(entry, file)
        policies[name] = router
    return policies


def default_catalog_path() -> Path:
    """Path to the shipped ``examples/tool_catalog.yaml`` (repo-relative)."""
    return Path(__file__).resolve().parents[2] / "examples" / "tool_catalog.yaml"
