#!/usr/bin/env python3
"""灵台未央集成示例

演示如何使用灵的路由评估系统：
1. 初始化路由器和日志收集器
2. 模拟路由决策
3. 记录决策日志
4. 生成评估报告
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from agent_routing_eval_lab.routing import LingTriageRouter
from agent_routing_eval_lab.data import LingDecisionLogger
from agent_routing_eval_lab.adapters import LingEvalAdapter


def main():
    """主函数"""
    print("=" * 60)
    print("灵台未央路由评估系统 - 集成演示")
    print("=" * 60)
    print()

    # 1. 初始化组件
    print("1. 初始化组件...")
    router = LingTriageRouter()
    logger = LingDecisionLogger(log_dir="demo_logs/ling_decisions")
    adapter = LingEvalAdapter()
    print("   [OK] 路由器初始化完成")
    print("   [OK] 日志收集器初始化完成")
    print("   [OK] 评估适配器初始化完成")
    print()

    # 2. 模拟用户输入
    test_queries = [
        {
            "query": "什么是存在主义？",
            "expected_intent": "philosophy_analysis",
            "expected_tool": "marvis.ling_ask_philosophy",
        },
        {
            "query": "从心理学角度分析焦虑症的治疗方法",
            "expected_intent": "psychology_analysis",
            "expected_tool": "marvis.ling_ask_psychology",
        },
        {
            "query": "综合分析这个案例的哲学和心理学意义",
            "expected_intent": "integrated_analysis",
            "expected_tool": "marvis.ling_ask_main",
        },
        {
            "query": "写一个 Python 函数来计算斐波那契数列",
            "expected_intent": "coding_task",
            "expected_tool": "codewhale.exec",
        },
        {
            "query": "什么是量子计算？",
            "expected_intent": "knowledge_search",
            "expected_tool": "knowledge.search",
        },
        {
            "query": "今天天气怎么样？",
            "expected_intent": "direct_answer",
            "expected_tool": "direct.answer",
        },
    ]

    # 3. 可用工具列表
    available_tools = [
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

    # 4. 执行路由决策
    print("2. 执行路由决策...")
    print()
    decisions = []

    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected_tool = test_case["expected_tool"]

        # 获取意图分析
        intent_info = router.get_intent_explanation(query)
        intent = intent_info["intent"]
        confidence = intent_info["confidence"]

        # 执行路由
        chosen_tool = router.route(
            query=query,
            available_tools=available_tools,
        )

        # 判断是否正确
        correct = chosen_tool == expected_tool
        status = "[OK]" if correct else "[FAIL]"

        print(f"   测试 {i}: {query}")
        print(f"      意图: {intent} (置信度: {confidence:.2f})")
        print(f"      预期: {expected_tool}")
        print(f"      实际: {chosen_tool} {status}")
        print()

        # 记录决策
        request_id = logger.log_decision(
            user_query=query,
            intent=intent,
            available_tools=available_tools,
            chosen_tool=chosen_tool,
            oracle_tool=expected_tool,
            success=correct,
            cost=adapter.get_tool_spec(chosen_tool).avg_cost if adapter.get_tool_spec(chosen_tool) else 0.0,
            latency_ms=adapter.get_tool_spec(chosen_tool).avg_latency_ms if adapter.get_tool_spec(chosen_tool) else 0,
            policy_version="ling_triage_v1",
        )

        decisions.append({
            "request_id": request_id,
            "user_query": query,
            "intent": intent,
            "available_tools": available_tools,
            "chosen_tool": chosen_tool,
            "oracle_tool": expected_tool,
            "success": correct,
            "cost": adapter.get_tool_spec(chosen_tool).avg_cost if adapter.get_tool_spec(chosen_tool) else 0.0,
            "latency_ms": adapter.get_tool_spec(chosen_tool).avg_latency_ms if adapter.get_tool_spec(chosen_tool) else 0,
            "policy_version": "ling_triage_v1",
        })

    # 5. 获取统计信息
    print("3. 统计信息...")
    stats = logger.get_statistics()
    print(f"   总决策数: {stats['total_decisions']}")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   平均成本: ${stats['avg_cost']:.3f}")
    print(f"   平均延迟: {stats['avg_latency_ms']}ms")
    print()

    # 6. 计算灵的指标
    print("4. 灵的指标...")
    ling_metrics = adapter.calculate_ling_metrics(decisions)
    print(f"   哲学模块使用率: {ling_metrics.philosophy_usage:.1%}")
    print(f"   心理学模块使用率: {ling_metrics.psychology_usage:.1%}")
    print(f"   综合模块使用率: {ling_metrics.integrated_usage:.1%}")
    print(f"   编码模块使用率: {ling_metrics.coding_usage:.1%}")
    print(f"   直接回答率: {ling_metrics.direct_usage:.1%}")
    print(f"   模块切换次数: {ling_metrics.module_switches}")
    print()

    # 7. 生成报告
    print("5. 生成评估报告...")
    report = adapter.generate_ling_report(decisions)

    # 保存报告
    report_path = project_root / "reports" / "ling_evaluation_demo.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)

    print(f"   [OK] 报告已保存到: {report_path}")
    print()

    # 8. 导出日志
    print("6. 导出日志...")
    export_path = project_root / "logs" / "ling_decisions_export.csv"
    logger.export_for_evaluation(export_path)
    print(f"   [OK] 日志已导出到: {export_path}")
    print()

    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 查看生成的报告: reports/ling_evaluation_demo.md")
    print("2. 查看导出的日志: logs/ling_decisions_export.csv")
    print("3. 使用离线评估器比较不同策略")
    print("4. 集成到灵的路由系统中")


if __name__ == "__main__":
    main()
