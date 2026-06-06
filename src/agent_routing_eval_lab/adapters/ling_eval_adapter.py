"""灵台未央评估适配器

将灵的路由决策转换为标准评估格式。

功能：
1. 加载灵的工具目录
2. 转换灵的决策日志为标准格式
3. 计算灵特有的指标
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_routing_eval_lab.data.schemas import ToolSpec, TOOL_CATALOG


@dataclass
class LingToolSpec:
    """灵的工具规格"""
    name: str
    avg_cost: float
    avg_latency_ms: int
    sensitive: bool
    requires_approval: bool
    description: str
    module: str


@dataclass
class LingMetrics:
    """灵特有的指标"""
    philosophy_usage: float  # 哲学模块使用率
    psychology_usage: float  # 心理学模块使用率
    integrated_usage: float  # 综合模块使用率
    coding_usage: float      # 编码模块使用率
    direct_usage: float      # 直接回答率
    module_switches: int     # 模块切换次数
    avg_confidence: float    # 平均置信度


class LingEvalAdapter:
    """灵台未央评估适配器"""

    def __init__(self, tool_catalog_path: str | Path | None = None) -> None:
        """初始化适配器

        Args:
            tool_catalog_path: 灵的工具目录路径，默认为 examples/ling_tool_catalog.yaml
        """
        if tool_catalog_path is None:
            tool_catalog_path = Path(__file__).parent.parent.parent.parent / "examples" / "ling_tool_catalog.yaml"
        
        self.tool_catalog_path = Path(tool_catalog_path)
        self.ling_tools: dict[str, LingToolSpec] = {}
        self._load_tool_catalog()

    def _load_tool_catalog(self) -> None:
        """加载灵的工具目录"""
        if not self.tool_catalog_path.exists():
            raise FileNotFoundError(f"Tool catalog not found: {self.tool_catalog_path}")

        with self.tool_catalog_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for tool_data in data.get("tools", []):
            tool = LingToolSpec(
                name=tool_data["name"],
                avg_cost=tool_data["avg_cost"],
                avg_latency_ms=tool_data["avg_latency_ms"],
                sensitive=tool_data.get("sensitive", False),
                requires_approval=tool_data.get("requires_approval", False),
                description=tool_data.get("description", ""),
                module=tool_data.get("module", "unknown"),
            )
            self.ling_tools[tool.name] = tool

    def get_tool_spec(self, tool_name: str) -> LingToolSpec | None:
        """获取工具规格

        Args:
            tool_name: 工具名称

        Returns:
            LingToolSpec: 工具规格，如果不存在返回 None
        """
        return self.ling_tools.get(tool_name)

    def get_module_for_tool(self, tool_name: str) -> str:
        """获取工具所属模块

        Args:
            tool_name: 工具名称

        Returns:
            str: 模块名称
        """
        tool = self.ling_tools.get(tool_name)
        return tool.module if tool else "unknown"

    def convert_to_standard_format(self, ling_decision: dict[str, Any]) -> dict[str, Any]:
        """将灵的决策转换为标准格式

        Args:
            ling_decision: 灵的决策记录

        Returns:
            dict: 标准格式的决策记录
        """
        chosen_tool = ling_decision.get("chosen_tool", "")
        tool_spec = self.ling_tools.get(chosen_tool)

        # 计算成本和延迟
        cost = ling_decision.get("cost", 0.0)
        latency_ms = ling_decision.get("latency_ms", 0)

        if tool_spec and cost == 0.0:
            cost = tool_spec.avg_cost
        if tool_spec and latency_ms == 0:
            latency_ms = tool_spec.avg_latency_ms

        # 判断是否需要审批
        requires_approval = ling_decision.get("requires_approval", False)
        if tool_spec:
            requires_approval = tool_spec.requires_approval

        # 判断是否不安全
        unsafe_action = ling_decision.get("unsafe_action", False)
        if tool_spec and tool_spec.sensitive and not ling_decision.get("approval_granted", True):
            unsafe_action = True

        return {
            "request_id": ling_decision.get("request_id", ""),
            "timestamp": ling_decision.get("timestamp", ""),
            "user_query": ling_decision.get("user_query", ""),
            "intent": ling_decision.get("intent", ""),
            "available_tools": ling_decision.get("available_tools", []),
            "chosen_tool": chosen_tool,
            "oracle_tool": ling_decision.get("oracle_tool", ""),
            "tool_result": ling_decision.get("tool_result", ""),
            "success": ling_decision.get("success", True),
            "failure_type": ling_decision.get("failure_type", ""),
            "cost": cost,
            "latency_ms": latency_ms,
            "requires_approval": requires_approval,
            "approval_granted": ling_decision.get("approval_granted", True),
            "unsafe_action": unsafe_action,
            "human_rating": ling_decision.get("human_rating", 0),
            "policy_version": ling_decision.get("policy_version", "v1.0"),
        }

    def calculate_ling_metrics(self, decisions: list[dict[str, Any]]) -> LingMetrics:
        """计算灵特有的指标

        Args:
            decisions: 决策列表

        Returns:
            LingMetrics: 灵的指标
        """
        if not decisions:
            return LingMetrics(
                philosophy_usage=0.0,
                psychology_usage=0.0,
                integrated_usage=0.0,
                coding_usage=0.0,
                direct_usage=0.0,
                module_switches=0,
                avg_confidence=0.0,
            )

        total = len(decisions)
        module_counts = {
            "ling-philosophy": 0,
            "ling-psychology": 0,
            "ling-main": 0,
            "codewhale": 0,
            "direct": 0,
        }

        prev_module = None
        switches = 0

        for decision in decisions:
            chosen_tool = decision.get("chosen_tool", "")
            module = self.get_module_for_tool(chosen_tool)

            if module in module_counts:
                module_counts[module] += 1

            # 统计模块切换
            if prev_module and module != prev_module:
                switches += 1
            prev_module = module

        return LingMetrics(
            philosophy_usage=module_counts["ling-philosophy"] / total,
            psychology_usage=module_counts["ling-psychology"] / total,
            integrated_usage=module_counts["ling-main"] / total,
            coding_usage=module_counts["codewhale"] / total,
            direct_usage=module_counts["direct"] / total,
            module_switches=switches,
            avg_confidence=0.0,  # 需要从决策中提取
        )

    def generate_ling_report(self, decisions: list[dict[str, Any]]) -> str:
        """生成灵的评估报告

        Args:
            decisions: 决策列表

        Returns:
            str: Markdown 格式的报告
        """
        metrics = self.calculate_ling_metrics(decisions)

        report = f"""# 灵台未央路由评估报告

## 概览

- **总决策数**: {len(decisions)}
- **哲学模块使用率**: {metrics.philosophy_usage:.1%}
- **心理学模块使用率**: {metrics.psychology_usage:.1%}
- **综合模块使用率**: {metrics.integrated_usage:.1%}
- **编码模块使用率**: {metrics.coding_usage:.1%}
- **直接回答率**: {metrics.direct_usage:.1%}
- **模块切换次数**: {metrics.module_switches}

## 模块分布

| 模块 | 使用率 | 说明 |
|------|--------|------|
| 哲学模块 | {metrics.philosophy_usage:.1%} | 存在主义、斯多葛、尼采等18学派 |
| 心理学模块 | {metrics.psychology_usage:.1%} | 精神分析、CBT、人本等18学派 |
| 综合模块 | {metrics.integrated_usage:.1%} | 三轴整合分析 |
| 编码模块 | {metrics.coding_usage:.1%} | CodeWhale 编程执行 |
| 直接回答 | {metrics.direct_usage:.1%} | 简单问题直接回答 |

## 路由策略分析

### 三轴分析效果

"""
        # 添加意图分布分析
        intent_dist = {}
        for decision in decisions:
            intent = decision.get("intent", "unknown")
            intent_dist[intent] = intent_dist.get(intent, 0) + 1

        if intent_dist:
            report += "### 意图分布\n\n"
            report += "| 意图 | 数量 | 比例 |\n"
            report += "|------|------|------|\n"
            for intent, count in sorted(intent_dist.items(), key=lambda x: -x[1]):
                report += f"| {intent} | {count} | {count/len(decisions):.1%} |\n"

        report += """
## 建议

1. **模块平衡**: 确保各模块使用率合理，避免过度依赖某一模块
2. **切换优化**: 减少不必要的模块切换，提高用户体验
3. **置信度**: 提高意图识别的置信度，减少误判
4. **成本控制**: 监控各模块成本，优化高成本模块的使用

"""

        return report
