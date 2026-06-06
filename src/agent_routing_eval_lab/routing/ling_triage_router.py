"""灵台未央三轴分析路由器

实现灵的三轴分析路由策略：
- 哲学轴：存在主义、斯多葛、尼采等18学派
- 心理学轴：精神分析、CBT、人本等18学派
- 综合轴：三轴整合分析
- 编码轴：编程任务
- 直接回答：简单问题

路由逻辑：
1. 分析用户输入的意图
2. 根据意图选择合适的工具
3. 考虑上下文和历史
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class IntentPattern:
    """意图模式定义"""
    name: str
    keywords: list[str]
    patterns: list[str]
    tool: str
    priority: int = 0
    description: str = ""


class LingTriageRouter:
    """灵台未央三轴分析路由器"""

    def __init__(self) -> None:
        self.intent_patterns = self._build_intent_patterns()

    def _build_intent_patterns(self) -> list[IntentPattern]:
        """构建意图模式列表"""
        return [
            # 哲学分析意图
            IntentPattern(
                name="philosophy_analysis",
                keywords=["哲学", "存在主义", "斯多葛", "尼采", "维特根斯坦", "伦理", "道德",
                         "意义", "荒谬", "自由", "责任", "正义", "真理", "认识论", "本体论",
                         "形而上学", "逻辑", "美学", "宗教哲学", "政治哲学"],
                patterns=[
                    r"什么是.*的意义",
                    r"从哲学角度.*分析",
                    r".*的哲学.*是什么",
                    r"如何理解.*的.*本质",
                    r".*伦理.*问题",
                    r"什么是.*(存在主义|斯多葛|尼采|维特根斯坦|伦理|道德|意义|荒谬|自由|责任|正义|真理|认识论|本体论|形而上学|逻辑|美学)",
                ],
                tool="marvis.ling_ask_philosophy",
                priority=10,
                description="纯哲学分析：存在主义、斯多葛、尼采、维特根斯坦等18学派",
            ),

            # 心理学分析意图
            IntentPattern(
                name="psychology_analysis",
                keywords=["心理", "精神分析", "弗洛伊德", "荣格", "认知", "行为", "CBT",
                         "人本", "马斯洛", "罗杰斯", "依恋", "创伤", "抑郁", "焦虑",
                         "人格", "发展", "社会心理", "临床", "治疗", "咨询"],
                patterns=[
                    r"从心理学角度.*分析",
                    r".*心理.*问题",
                    r"如何.*治疗.*",
                    r".*的.*心理.*机制",
                    r".*是什么.*心理.*障碍",
                ],
                tool="marvis.ling_ask_psychology",
                priority=10,
                description="纯心理学分析：精神分析、CBT、人本等18学派",
            ),

            # 综合分析意图（需要三轴整合）
            IntentPattern(
                name="integrated_analysis",
                keywords=["综合分析", "三轴", "整合", "全面分析", "深度分析", "系统性", "分析", "哲学", "心理", "意义"],
                patterns=[
                    r"从.*多个.*角度.*分析",
                    r"综合.*哲学.*心理.*分析",
                    r"全面.*分析.*问题",
                    r"深度.*分析.*",
                    r"综合.*分析.*",
                ],
                tool="marvis.ling_ask_main",
                priority=15,
                description="三轴整合：哲学追问→心理学诊断→综合方案",
            ),

            # 编码任务意图
            IntentPattern(
                name="coding_task",
                keywords=["代码", "编程", "函数", "类", "模块", "API", "数据库", "算法",
                         "bug", "调试", "重构", "测试", "部署", "Git", "脚本", "程序", "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust"],
                patterns=[
                    r"写.*代码",
                    r"实现.*函数",
                    r"修复.*bug",
                    r"创建.*脚本",
                    r".*怎么.*编程",
                    r"用.*代码.*实现",
                    r"写.*函数",
                    r".*Python.*函数",
                    r".*Java.*函数",
                    r".*JavaScript.*函数",
                ],
                tool="codewhale.exec",
                priority=8,
                description="复杂编程任务：文件读写、Shell、Git",
            ),

            # 记忆检索意图
            IntentPattern(
                name="memory_recall",
                keywords=["记得", "之前", "历史", "记录", "笔记", "上次", "以前"],
                patterns=[
                    r"之前.*说过",
                    r"记得.*吗",
                    r"历史.*记录",
                    r"查找.*笔记",
                ],
                tool="memory.search",
                priority=5,
                description="语义搜索记忆库",
            ),

            # 知识库检索意图
            IntentPattern(
                name="knowledge_search",
                keywords=["知识", "资料", "文献", "理论", "概念", "定义", "原理"],
                patterns=[
                    r"什么是.*",
                    r"解释.*概念",
                    r".*的定义.*是什么",
                    r"查找.*资料",
                ],
                tool="knowledge.search",
                priority=4,
                description="语义搜索知识库",
            ),

            # Web 搜索意图
            IntentPattern(
                name="web_search",
                keywords=["搜索", "查询", "最新", "新闻", "实时", "今天", "现在"],
                patterns=[
                    r"搜索.*",
                    r"查询.*最新.*",
                    r"今天.*新闻",
                    r"现在.*怎么样",
                ],
                tool="web.search",
                priority=3,
                description="搜索互联网获取实时信息",
            ),

            # 文件操作意图
            IntentPattern(
                name="file_operation",
                keywords=["文件", "读取", "写入", "保存", "打开", "编辑"],
                patterns=[
                    r"读取.*文件",
                    r"写入.*文件",
                    r"保存.*到.*",
                    r"打开.*文件",
                ],
                tool="file.read",
                priority=2,
                description="读取文件内容",
            ),

            # Shell 执行意图
            IntentPattern(
                name="shell_execution",
                keywords=["执行", "运行", "命令", "终端", "shell", "powershell"],
                patterns=[
                    r"执行.*命令",
                    r"运行.*脚本",
                    r"在.*终端.*执行",
                ],
                tool="shell.exec",
                priority=1,
                description="执行 Shell 命令",
            ),
        ]

    def _extract_intent(self, query: str) -> tuple[str, float]:
        """提取用户意图

        Args:
            query: 用户输入

        Returns:
            tuple: (意图名称, 置信度)
        """
        query_lower = query.lower()
        best_match = None
        best_score = 0.0

        for pattern in self.intent_patterns:
            score = 0.0

            # 关键词匹配
            keyword_matches = sum(1 for kw in pattern.keywords if kw in query_lower)
            if keyword_matches > 0:
                score += keyword_matches * 0.3

            # 正则模式匹配
            for regex in pattern.patterns:
                if re.search(regex, query, re.IGNORECASE):
                    score += 0.5

            # 优先级加权
            score += pattern.priority * 0.05

            if score > best_score:
                best_score = score
                best_match = pattern.name

        # 默认为直接回答
        # 如果没有关键词或模式匹配，直接返回直接回答
        if best_match is None or best_score < 0.3:
            return "direct_answer", 0.5

        # 如果只有优先级加权（没有关键词或模式匹配），也返回直接回答
        # 检查是否有实际的关键词或模式匹配
        has_keyword_match = False
        has_pattern_match = False
        for pattern in self.intent_patterns:
            if pattern.name == best_match:
                keyword_matches = sum(1 for kw in pattern.keywords if kw in query_lower)
                if keyword_matches > 0:
                    has_keyword_match = True
                for regex in pattern.patterns:
                    if re.search(regex, query, re.IGNORECASE):
                        has_pattern_match = True
                break

        if not has_keyword_match and not has_pattern_match:
            return "direct_answer", 0.5

        return best_match, min(best_score, 1.0)

    def _get_tool_for_intent(self, intent: str, available_tools: list[str]) -> str:
        """根据意图获取工具

        Args:
            intent: 意图名称
            available_tools: 可用工具列表

        Returns:
            str: 选择的工具名称
        """
        # 查找意图对应的工具
        for pattern in self.intent_patterns:
            if pattern.name == intent:
                if pattern.tool in available_tools:
                    return pattern.tool

        # 如果首选工具不可用，选择替代工具
        alternatives = {
            "philosophy_analysis": ["marvis.ling_ask_main", "direct.answer"],
            "psychology_analysis": ["marvis.ling_ask_main", "direct.answer"],
            "integrated_analysis": ["marvis.ling_ask_philosophy", "marvis.ling_ask_psychology", "direct.answer"],
            "coding_task": ["direct.answer"],
            "memory_recall": ["knowledge.search", "direct.answer"],
            "knowledge_search": ["memory.search", "direct.answer"],
            "web_search": ["direct.answer"],
            "file_operation": ["direct.answer"],
            "shell_execution": ["direct.answer"],
        }

        if intent in alternatives:
            for alt in alternatives[intent]:
                if alt in available_tools:
                    return alt

        # 默认返回直接回答
        return "direct.answer" if "direct.answer" in available_tools else available_tools[0]

    def route(
        self,
        query: str,
        intent: str = "",
        available_tools: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """路由决策

        Args:
            query: 用户输入
            intent: 意图（可选，如果不提供则自动提取）
            available_tools: 可用工具列表
            metadata: 元数据

        Returns:
            str: 选择的工具名称
        """
        if available_tools is None:
            available_tools = []

        # 如果没有可用工具，返回直接回答
        if not available_tools:
            return "direct.answer"

        # 提取意图
        if not intent:
            intent, confidence = self._extract_intent(query)
        else:
            confidence = 1.0

        # 获取工具
        tool = self._get_tool_for_intent(intent, available_tools)

        return tool

    def get_intent_explanation(self, query: str) -> dict[str, Any]:
        """获取意图分析解释

        Args:
            query: 用户输入

        Returns:
            dict: 意图分析结果
        """
        intent, confidence = self._extract_intent(query)

        # 找到匹配的模式
        matched_pattern = None
        for pattern in self.intent_patterns:
            if pattern.name == intent:
                matched_pattern = pattern
                break

        return {
            "query": query,
            "intent": intent,
            "confidence": confidence,
            "tool": matched_pattern.tool if matched_pattern else "direct.answer",
            "description": matched_pattern.description if matched_pattern else "直接回答简单问题",
            "keywords_matched": [kw for kw in (matched_pattern.keywords if matched_pattern else []) if kw in query.lower()],
        }
