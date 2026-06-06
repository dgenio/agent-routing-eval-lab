"""灵台未央决策日志收集器

记录灵的路由决策，用于离线评估。

日志格式：
- request_id: 请求ID
- timestamp: 时间戳
- user_query: 用户输入
- intent: 意图
- available_tools: 可用工具（管道符分隔）
- chosen_tool: 选择的工具
- oracle_tool: 最优工具（人工标注或事后确定）
- tool_result: 工具执行结果
- success: 是否成功
- failure_type: 失败类型
- cost: 成本
- latency_ms: 延迟
- requires_approval: 是否需要审批
- approval_granted: 是否获得审批
- unsafe_action: 是否不安全
- human_rating: 人工评分
- policy_version: 策略版本
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


class LingDecisionLogger:
    """灵台未央决策日志收集器"""

    def __init__(self, log_dir: str | Path = "logs/ling_decisions") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_log_file = self._get_log_file()

    def _get_log_file(self) -> Path:
        """获取当前日志文件路径"""
        # 按日期分文件
        now = datetime.now(timezone(timedelta(hours=8)))
        date_str = now.strftime("%Y-%m-%d")
        return self.log_dir / f"ling_decisions_{date_str}.csv"

    def _ensure_log_file(self) -> None:
        """确保日志文件存在并有表头"""
        if not self.current_log_file.exists():
            with self.current_log_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "request_id",
                    "timestamp",
                    "user_query",
                    "intent",
                    "available_tools",
                    "chosen_tool",
                    "oracle_tool",
                    "tool_result",
                    "success",
                    "failure_type",
                    "cost",
                    "latency_ms",
                    "requires_approval",
                    "approval_granted",
                    "unsafe_action",
                    "human_rating",
                    "policy_version",
                ])

    def log_decision(
        self,
        user_query: str,
        intent: str,
        available_tools: list[str],
        chosen_tool: str,
        oracle_tool: str = "",
        tool_result: str = "",
        success: bool = True,
        failure_type: str = "",
        cost: float = 0.0,
        latency_ms: int = 0,
        requires_approval: bool = False,
        approval_granted: bool = True,
        unsafe_action: bool = False,
        human_rating: int = 0,
        policy_version: str = "v1.0",
    ) -> str:
        """记录路由决策

        Args:
            user_query: 用户输入
            intent: 意图
            available_tools: 可用工具列表
            chosen_tool: 选择的工具
            oracle_tool: 最优工具（可选）
            tool_result: 工具执行结果（可选）
            success: 是否成功
            failure_type: 失败类型
            cost: 成本
            latency_ms: 延迟（毫秒）
            requires_approval: 是否需要审批
            approval_granted: 是否获得审批
            unsafe_action: 是否不安全
            human_rating: 人工评分（1-5）
            policy_version: 策略版本

        Returns:
            str: 请求ID
        """
        self._ensure_log_file()

        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]

        # 获取时间戳
        now = datetime.now(timezone(timedelta(hours=8)))
        timestamp = now.isoformat()

        # 转换工具列表为管道符分隔的字符串
        available_tools_str = "|".join(available_tools)

        # 写入日志
        with self.current_log_file.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                request_id,
                timestamp,
                user_query,
                intent,
                available_tools_str,
                chosen_tool,
                oracle_tool,
                tool_result,
                success,
                failure_type,
                cost,
                latency_ms,
                requires_approval,
                approval_granted,
                unsafe_action,
                human_rating,
                policy_version,
            ])

        return request_id

    def log_from_dict(self, decision: dict[str, Any]) -> str:
        """从字典记录决策

        Args:
            decision: 决策字典

        Returns:
            str: 请求ID
        """
        return self.log_decision(
            user_query=decision.get("user_query", ""),
            intent=decision.get("intent", ""),
            available_tools=decision.get("available_tools", []),
            chosen_tool=decision.get("chosen_tool", ""),
            oracle_tool=decision.get("oracle_tool", ""),
            tool_result=decision.get("tool_result", ""),
            success=decision.get("success", True),
            failure_type=decision.get("failure_type", ""),
            cost=decision.get("cost", 0.0),
            latency_ms=decision.get("latency_ms", 0),
            requires_approval=decision.get("requires_approval", False),
            approval_granted=decision.get("approval_granted", True),
            unsafe_action=decision.get("unsafe_action", False),
            human_rating=decision.get("human_rating", 0),
            policy_version=decision.get("policy_version", "v1.0"),
        )

    def get_logs(self, date: str = "") -> list[dict[str, Any]]:
        """获取日志

        Args:
            date: 日期（格式：YYYY-MM-DD），默认为今天

        Returns:
            list: 日志列表
        """
        if date:
            log_file = self.log_dir / f"ling_decisions_{date}.csv"
        else:
            log_file = self.current_log_file

        if not log_file.exists():
            return []

        logs = []
        with log_file.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 转换类型
                row["success"] = row["success"].lower() in {"1", "true", "yes"}
                row["cost"] = float(row["cost"])
                row["latency_ms"] = int(float(row["latency_ms"]))
                row["requires_approval"] = row["requires_approval"].lower() in {"1", "true", "yes"}
                row["approval_granted"] = row["approval_granted"].lower() in {"1", "true", "yes"}
                row["unsafe_action"] = row["unsafe_action"].lower() in {"1", "true", "yes"}
                row["human_rating"] = int(row["human_rating"])
                logs.append(row)

        return logs

    def export_for_evaluation(self, output_path: str | Path, date: str = "") -> Path:
        """导出日志用于评估

        Args:
            output_path: 输出文件路径
            date: 日期（格式：YYYY-MM-DD），默认为今天

        Returns:
            Path: 输出文件路径
        """
        logs = self.get_logs(date)
        output_path = Path(output_path)

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入 CSV
        if logs:
            with output_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)

        return output_path

    def get_statistics(self, date: str = "") -> dict[str, Any]:
        """获取统计信息

        Args:
            date: 日期（格式：YYYY-MM-DD），默认为今天

        Returns:
            dict: 统计信息
        """
        logs = self.get_logs(date)

        if not logs:
            return {
                "total_decisions": 0,
                "success_rate": 0.0,
                "avg_cost": 0.0,
                "avg_latency_ms": 0,
                "tool_distribution": {},
                "intent_distribution": {},
            }

        total = len(logs)
        success_count = sum(1 for log in logs if log["success"])
        total_cost = sum(log["cost"] for log in logs)
        total_latency = sum(log["latency_ms"] for log in logs)

        # 工具分布
        tool_dist = {}
        for log in logs:
            tool = log["chosen_tool"]
            tool_dist[tool] = tool_dist.get(tool, 0) + 1

        # 意图分布
        intent_dist = {}
        for log in logs:
            intent = log["intent"]
            intent_dist[intent] = intent_dist.get(intent, 0) + 1

        return {
            "total_decisions": total,
            "success_rate": success_count / total if total > 0 else 0.0,
            "avg_cost": total_cost / total if total > 0 else 0.0,
            "avg_latency_ms": total_latency // total if total > 0 else 0,
            "tool_distribution": tool_dist,
            "intent_distribution": intent_dist,
        }
