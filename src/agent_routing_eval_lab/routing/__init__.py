"""Subpackage.

Available routers:
- BaselineRouter: 基线路由器
- ContextWeaverRouter: 上下文感知路由器
- CostAwareRouter: 成本感知路由器
- StrictPolicyRouter: 严格策略路由器

Router metadata contract
------------------------
A router exposes ``route(query, intent, available_tools, metadata=None) -> str``
and must select from ``available_tools`` only. The ``metadata`` dict carries
**decision-time information only**. Allowed keys:

- ``approval_granted`` (bool): whether human approval has been granted for the
  request, for tools that require it.

The evaluator deliberately does **not** pass ``oracle_tool`` (the ground-truth
answer): a router that read it could score a perfect correct-tool rate and
invalidate every comparison. Treat any other key as absent and default it.
See docs/evaluation_methodology.md ("Decision-time information (leakage guard)").
"""

from .baseline_router import BaselineRouter
from .contextweaver_router import ContextWeaverRouter
from .cost_aware_router import CostAwareRouter
from .strict_policy_router import StrictPolicyRouter

__all__ = [
    "BaselineRouter",
    "ContextWeaverRouter",
    "CostAwareRouter",
    "StrictPolicyRouter",
]
