# 灵台未央集成指南

本文档说明如何将灵台未央（灵）的路由系统集成到 agent-routing-eval-lab 中，用于离线评估灵的三轴分析路由策略。

## 概述

灵台未央是一个心理学×哲学×编码的三轴分析系统，其路由策略基于：
- **哲学轴**：存在主义、斯多葛、尼采等18学派
- **心理学轴**：精神分析、CBT、人本等18学派
- **综合轴**：三轴整合分析
- **编码轴**：CodeWhale 编程执行

通过集成到 agent-routing-eval-lab，我们可以：
1. 记录灵的路由决策
2. 离线评估路由策略效果
3. 比较不同路由策略
4. 优化意图识别和工具选择

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    灵台未央路由系统                          │
├─────────────────────────────────────────────────────────────┤
│  用户输入 → 意图识别 → 工具选择 → 执行 → 结果              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 agent-routing-eval-lab                       │
├─────────────────────────────────────────────────────────────┤
│  LingDecisionLogger: 记录路由决策                           │
│  LingEvalAdapter: 转换格式并计算指标                        │
│  LingTriageRouter: 灵的路由器实现                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    离线评估系统                              │
├─────────────────────────────────────────────────────────────┤
│  OfflineEvaluator: 评估路由策略                             │
│  PolicyMetrics: 计算指标                                    │
│  Report: 生成报告                                           │
└─────────────────────────────────────────────────────────────┘
```

## 组件说明

### 1. LingTriageRouter

灵的三轴分析路由器，实现基于规则的意图识别和工具选择。

**文件位置**: `src/agent_routing_eval_lab/routing/ling_triage_router.py`

**主要功能**:
- 意图识别：根据关键词和模式匹配识别用户意图
- 工具选择：根据意图选择合适的工具
- 替代方案：当首选工具不可用时提供替代方案

**使用示例**:
```python
from agent_routing_eval_lab.routing import LingTriageRouter

router = LingTriageRouter()

# 路由决策
tool = router.route(
    query="什么是存在主义？",
    available_tools=["marvis.ling_ask_philosophy", "direct.answer"],
)

# 获取意图分析
intent_info = router.get_intent_explanation("从心理学角度分析焦虑症")
```

### 2. LingDecisionLogger

决策日志收集器，记录灵的路由决策用于离线评估。

**文件位置**: `src/agent_routing_eval_lab/data/ling_decision_logger.py`

**主要功能**:
- 记录路由决策到 CSV 文件
- 按日期分文件存储
- 导出日志用于评估
- 计算统计信息

**使用示例**:
```python
from agent_routing_eval_lab.data import LingDecisionLogger

logger = LingDecisionLogger(log_dir="logs/ling_decisions")

# 记录决策
request_id = logger.log_decision(
    user_query="什么是存在主义？",
    intent="philosophy_analysis",
    available_tools=["marvis.ling_ask_philosophy", "direct.answer"],
    chosen_tool="marvis.ling_ask_philosophy",
    oracle_tool="marvis.ling_ask_philosophy",
    success=True,
    cost=0.15,
    latency_ms=2000,
    policy_version="ling_triage_v1",
)

# 获取统计信息
stats = logger.get_statistics()
print(f"成功率: {stats['success_rate']:.1%}")

# 导出日志
logger.export_for_evaluation("logs/export.csv")
```

### 3. LingEvalAdapter

评估适配器，将灵的决策格式转换为标准格式并计算灵特有的指标。

**文件位置**: `src/agent_routing_eval_lab/adapters/ling_eval_adapter.py`

**主要功能**:
- 加载灵的工具目录
- 转换决策格式
- 计算灵特有的指标（模块使用率、切换次数等）
- 生成灵的评估报告

**使用示例**:
```python
from agent_routing_eval_lab.adapters import LingEvalAdapter

adapter = LingEvalAdapter()

# 获取工具规格
spec = adapter.get_tool_spec("marvis.ling_ask_philosophy")
print(f"成本: ${spec.avg_cost}, 延迟: {spec.avg_latency_ms}ms")

# 计算灵的指标
metrics = adapter.calculate_ling_metrics(decisions)
print(f"哲学模块使用率: {metrics.philosophy_usage:.1%}")

# 生成报告
report = adapter.generate_ling_report(decisions)
```

## 工具目录

灵的工具目录定义在 `examples/ling_tool_catalog.yaml`，包含以下工具：

| 工具名称 | 模块 | 成本 | 延迟 | 说明 |
|----------|------|------|------|------|
| marvis.ling_ask_philosophy | ling-philosophy | $0.15 | 2000ms | 哲学分析 |
| marvis.ling_ask_psychology | ling-psychology | $0.15 | 2000ms | 心理学分析 |
| marvis.ling_ask_main | ling-main | $0.20 | 2500ms | 综合分析 |
| codewhale.exec | codewhale | $0.25 | 3000ms | 编码执行 |
| direct.answer | direct | $0.01 | 500ms | 直接回答 |
| memory.search | memory | $0.02 | 300ms | 记忆检索 |
| knowledge.search | knowledge | $0.02 | 300ms | 知识库检索 |
| web.search | web | $0.05 | 1500ms | Web 搜索 |
| file.read | file | $0.01 | 100ms | 文件读取 |
| file.write | file | $0.02 | 200ms | 文件写入 |
| shell.exec | shell | $0.10 | 1000ms | Shell 执行 |

## 策略配置

灵的路由策略配置在 `examples/policy_candidates/ling_triage_v1.yaml`，包含：

- **策略类型**: rule_based（基于规则）
- **置信度阈值**: 0.3
- **默认工具**: direct.answer
- **意图权重**: 各意图的优先级权重
- **工具映射**: 意图到工具的映射关系
- **替代工具**: 首选工具不可用时的替代方案
- **关键词**: 各意图的关键词列表
- **模式**: 各意图的正则模式

## 集成步骤

### 1. 安装依赖

```bash
cd agent-routing-eval-lab
pip install -e .
```

### 2. 运行演示

```bash
python examples/ling_integration_demo.py
```

### 3. 集成到灵的系统

在灵的路由系统中添加日志记录：

```python
from agent_routing_eval_lab.data import LingDecisionLogger
from agent_routing_eval_lab.adapters import LingEvalAdapter

# 初始化
logger = LingDecisionLogger(log_dir="logs/ling_decisions")
adapter = LingEvalAdapter()

# 在路由决策后记录
def route_and_log(query, available_tools):
    # 执行路由
    chosen_tool = router.route(query, available_tools=available_tools)
    
    # 记录决策
    logger.log_decision(
        user_query=query,
        intent=intent,
        available_tools=available_tools,
        chosen_tool=chosen_tool,
        cost=adapter.get_tool_spec(chosen_tool).avg_cost,
        latency_ms=adapter.get_tool_spec(chosen_tool).avg_latency_ms,
        policy_version="ling_triage_v1",
    )
    
    return chosen_tool
```

### 4. 定期评估

定期运行离线评估：

```python
from agent_routing_eval_lab.evaluation import OfflineEvaluator

# 加载日志
logged_rows = logger.get_logs()

# 创建评估器
evaluator = OfflineEvaluator(logged_rows)

# 评估策略
result = evaluator.evaluate_policy("ling_triage_v1", router)

# 输出结果
print(f"成功率: {result.metrics.success_rate:.1%}")
print(f"警告: {result.warnings}")
```

## 评估指标

### 标准指标

- **成功率 (success_rate)**: 路由决策正确的比例
- **正确工具率 (correct_tool_rate)**: 选择最优工具的比例
- **平均成本 (avg_cost)**: 每次决策的平均成本
- **平均延迟 (avg_latency_ms)**: 每次决策的平均延迟
- **不安全操作率 (unsafe_action_rate)**: 不安全操作的比例

### 灵特有指标

- **哲学模块使用率**: 使用哲学分析模块的比例
- **心理学模块使用率**: 使用心理学分析模块的比例
- **综合模块使用率**: 使用综合分析模块的比例
- **编码模块使用率**: 使用编码执行模块的比例
- **直接回答率**: 直接回答（无工具调用）的比例
- **模块切换次数**: 不同模块之间的切换次数

## 最佳实践

### 1. 日志记录

- 记录所有路由决策，包括成功和失败的
- 定期备份日志文件
- 使用版本化的策略名称

### 2. 意图识别

- 定期更新关键词和模式
- 收集误判案例用于改进
- 监控置信度分布

### 3. 工具选择

- 记录工具不可用的情况
- 监控替代工具的使用
- 优化工具映射关系

### 4. 持续改进

- 定期运行离线评估
- 比较不同策略版本
- 根据评估结果调整策略

## 扩展

### 添加新工具

1. 在 `examples/ling_tool_catalog.yaml` 中添加工具定义
2. 在 `examples/policy_candidates/ling_triage_v1.yaml` 中添加工具映射
3. 更新路由器中的工具选择逻辑

### 添加新意图

1. 在 `examples/policy_candidates/ling_triage_v1.yaml` 中添加关键词和模式
2. 在 `LingTriageRouter` 中添加意图模式
3. 更新工具映射和替代方案

### 自定义指标

1. 在 `LingEvalAdapter` 中添加新的指标计算
2. 更新报告生成逻辑
3. 在评估器中集成新指标

## 故障排除

### 问题：工具目录加载失败

**原因**: 工具目录文件路径错误或格式错误

**解决**:
1. 检查文件路径是否正确
2. 验证 YAML 格式
3. 确保所有必需字段都已填写

### 问题：意图识别不准确

**原因**: 关键词或模式配置不当

**解决**:
1. 检查关键词是否完整
2. 验证正则模式是否正确
3. 收集误判案例并更新配置

### 问题：日志文件损坏

**原因**: 写入过程中断或编码问题

**解决**:
1. 使用 UTF-8 编码
2. 确保写入过程完整
3. 定期备份日志文件

## 相关文档

- [架构说明](architecture.md)
- [评估方法论](evaluation_methodology.md)
- [术语表](glossary.md)
- [顾问手册](consultant_playbook.md)
