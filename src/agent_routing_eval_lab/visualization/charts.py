from __future__ import annotations

from agent_routing_eval_lab.evaluation.evaluator import PolicyEvaluationResult, rank_results


def ascii_score_chart(results: list[PolicyEvaluationResult]) -> str:
    ranked = rank_results(results)
    lines = ["Policy score chart"]
    for result in ranked:
        width = max(1, int(result.metrics.score / 2))
        lines.append(f"- {result.policy_name:16} {'█' * width} {result.metrics.score:.2f}")
    return "\n".join(lines)
