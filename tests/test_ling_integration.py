"""灵台未央集成测试

测试灵的路由器、日志收集器和评估适配器。
"""

import pytest
import tempfile
from pathlib import Path

from agent_routing_eval_lab.routing import LingTriageRouter
from agent_routing_eval_lab.data import LingDecisionLogger
from agent_routing_eval_lab.adapters import LingEvalAdapter


class TestLingTriageRouter:
    """测试灵的三轴分析路由器"""

    def setup_method(self):
        """测试前初始化"""
        self.router = LingTriageRouter()
        self.available_tools = [
            "marvis.ling_ask_philosophy",
            "marvis.ling_ask_psychology",
            "marvis.ling_ask_main",
            "codewhale.exec",
            "memory.search",
            "knowledge.search",
            "web.search",
            "file.read",
            "file.write",
            "shell.exec",
            "direct.answer",
        ]

    def test_philosophy_intent(self):
        """测试哲学意图识别"""
        query = "什么是存在主义？"
        intent_info = self.router.get_intent_explanation(query)
        assert intent_info["intent"] == "philosophy_analysis"
        assert intent_info["tool"] == "marvis.ling_ask_philosophy"

    def test_psychology_intent(self):
        """测试心理学意图识别"""
        query = "从心理学角度分析焦虑症"
        intent_info = self.router.get_intent_explanation(query)
        assert intent_info["intent"] == "psychology_analysis"
        assert intent_info["tool"] == "marvis.ling_ask_psychology"

    def test_integrated_intent(self):
        """测试综合分析意图识别"""
        query = "综合分析这个案例的哲学和心理学意义"
        intent_info = self.router.get_intent_explanation(query)
        assert intent_info["intent"] == "integrated_analysis"
        assert intent_info["tool"] == "marvis.ling_ask_main"

    def test_coding_intent(self):
        """测试编码意图识别"""
        query = "写一个 Python 函数来计算斐波那契数列"
        intent_info = self.router.get_intent_explanation(query)
        assert intent_info["intent"] == "coding_task"
        assert intent_info["tool"] == "codewhale.exec"

    def test_direct_answer(self):
        """测试直接回答"""
        query = "今天天气怎么样？"
        intent_info = self.router.get_intent_explanation(query)
        assert intent_info["intent"] == "direct_answer"
        assert intent_info["tool"] == "direct.answer"

    def test_routing_with_available_tools(self):
        """测试路由决策（指定可用工具）"""
        query = "什么是存在主义？"
        tool = self.router.route(
            query=query,
            available_tools=self.available_tools,
        )
        assert tool == "marvis.ling_ask_philosophy"

    def test_routing_with_fallback(self):
        """测试路由决策（首选工具不可用时的回退）"""
        query = "什么是存在主义？"
        available_tools = ["marvis.ling_ask_main", "direct.answer"]
        tool = self.router.route(
            query=query,
            available_tools=available_tools,
        )
        assert tool == "marvis.ling_ask_main"

    def test_routing_with_empty_tools(self):
        """测试路由决策（无可用工具）"""
        query = "什么是存在主义？"
        tool = self.router.route(
            query=query,
            available_tools=[],
        )
        assert tool == "direct.answer"


class TestLingDecisionLogger:
    """测试灵的决策日志收集器"""

    def setup_method(self):
        """测试前初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = LingDecisionLogger(log_dir=self.temp_dir)

    def test_log_decision(self):
        """测试记录决策"""
        request_id = self.logger.log_decision(
            user_query="什么是存在主义？",
            intent="philosophy_analysis",
            available_tools=["marvis.ling_ask_philosophy", "direct.answer"],
            chosen_tool="marvis.ling_ask_philosophy",
            success=True,
            cost=0.15,
            latency_ms=2000,
            policy_version="ling_triage_v1",
        )
        assert request_id is not None
        assert len(request_id) == 8

    def test_get_logs(self):
        """测试获取日志"""
        # 记录多个决策
        for i in range(3):
            self.logger.log_decision(
                user_query=f"测试查询 {i}",
                intent="test_intent",
                available_tools=["direct.answer"],
                chosen_tool="direct.answer",
                success=True,
            )

        logs = self.logger.get_logs()
        assert len(logs) == 3

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 记录成功和失败的决策
        self.logger.log_decision(
            user_query="成功查询",
            intent="test_intent",
            available_tools=["direct.answer"],
            chosen_tool="direct.answer",
            success=True,
        )
        self.logger.log_decision(
            user_query="失败查询",
            intent="test_intent",
            available_tools=["direct.answer"],
            chosen_tool="direct.answer",
            success=False,
        )

        stats = self.logger.get_statistics()
        assert stats["total_decisions"] == 2
        assert stats["success_rate"] == 0.5

    def test_export_for_evaluation(self):
        """测试导出日志"""
        # 记录决策
        self.logger.log_decision(
            user_query="测试查询",
            intent="test_intent",
            available_tools=["direct.answer"],
            chosen_tool="direct.answer",
            success=True,
        )

        # 导出日志
        export_path = Path(self.temp_dir) / "export.csv"
        self.logger.export_for_evaluation(export_path)
        assert export_path.exists()


class TestLingEvalAdapter:
    """测试灵的评估适配器"""

    def setup_method(self):
        """测试前初始化"""
        self.adapter = LingEvalAdapter()

    def test_get_tool_spec(self):
        """测试获取工具规格"""
        spec = self.adapter.get_tool_spec("marvis.ling_ask_philosophy")
        assert spec is not None
        assert spec.name == "marvis.ling_ask_philosophy"
        assert spec.avg_cost == 0.15
        assert spec.avg_latency_ms == 2000

    def test_get_module_for_tool(self):
        """测试获取工具模块"""
        module = self.adapter.get_module_for_tool("marvis.ling_ask_philosophy")
        assert module == "ling-philosophy"

    def test_convert_to_standard_format(self):
        """测试转换为标准格式"""
        ling_decision = {
            "request_id": "test123",
            "timestamp": "2026-06-06T14:44:00+08:00",
            "user_query": "什么是存在主义？",
            "intent": "philosophy_analysis",
            "available_tools": ["marvis.ling_ask_philosophy", "direct.answer"],
            "chosen_tool": "marvis.ling_ask_philosophy",
            "success": True,
        }

        standard = self.adapter.convert_to_standard_format(ling_decision)
        assert standard["request_id"] == "test123"
        assert standard["cost"] == 0.15
        assert standard["latency_ms"] == 2000

    def test_calculate_ling_metrics(self):
        """测试计算灵的指标"""
        decisions = [
            {"chosen_tool": "marvis.ling_ask_philosophy"},
            {"chosen_tool": "marvis.ling_ask_psychology"},
            {"chosen_tool": "marvis.ling_ask_main"},
            {"chosen_tool": "codewhale.exec"},
            {"chosen_tool": "direct.answer"},
        ]

        metrics = self.adapter.calculate_ling_metrics(decisions)
        assert metrics.philosophy_usage == 0.2
        assert metrics.psychology_usage == 0.2
        assert metrics.integrated_usage == 0.2
        assert metrics.coding_usage == 0.2
        assert metrics.direct_usage == 0.2

    def test_generate_ling_report(self):
        """测试生成灵的报告"""
        decisions = [
            {
                "chosen_tool": "marvis.ling_ask_philosophy",
                "intent": "philosophy_analysis",
            },
            {
                "chosen_tool": "marvis.ling_ask_psychology",
                "intent": "psychology_analysis",
            },
        ]

        report = self.adapter.generate_ling_report(decisions)
        assert "灵台未央路由评估报告" in report
        assert "哲学模块使用率" in report
        assert "心理学模块使用率" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
