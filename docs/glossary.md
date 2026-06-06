# Glossary of Agent Routing, Tool-Selection, and Governance Concepts

> This glossary defines core terms used across the agent-routing-eval-lab codebase, docs, and reports. Definitions are concise (1–3 sentences) and match actual code behavior.

---

## Agent Routing

**Definition:** The process of selecting which tool, API, or action an AI agent should invoke in response to a user request. In this lab, routing is evaluated by replaying logged decisions through candidate policies and measuring outcomes.

**Related:** [Tool Selection](#tool-selection), [Candidate Policy](#candidate-policy)

---

## Tool Selection

**Definition:** The specific mechanism by which an agent chooses one tool from a set of available options. Tool selection is a subset of agent routing that focuses on the "which tool" decision rather than the broader "what to do" decision.

**Related:** [Agent Routing](#agent-routing), [MCP-Style Tools](#mcp-style-tools)

---

## Tool-Calling Agent

**Definition:** An AI agent that can invoke external tools (APIs, functions, services) as part of its reasoning process. Unlike pure text generators, tool-calling agents can interact with the real world through structured tool calls.

**Related:** [MCP-Style Tools](#mcp-style-tools)

---

## MCP-Style Tools

**Definition:** Tools that follow the Model Context Protocol pattern, where tools are defined with a name, description, and JSON schema for parameters. The agent receives a tool catalog and can invoke tools by name with structured arguments.

**Example:**
```json
{
  "name": "search_docs",
  "description": "Search documentation",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string"}
    }
  }
}
```

---

## Offline Evaluation

**Definition:** Testing agent routing policies against historical data without sending requests to live systems. Offline evaluation allows teams to compare policies safely before production rollout.

**Why it matters:** Production changes can improve one metric while quietly increasing cost, latency, unsafe actions, or unresolved requests. Offline evaluation catches these trade-offs early.

**Related:** [Logged Decision](#logged-decision)

---

## Logged Decision

**Definition:** A record of a past agent routing decision, including the user intent, available tools, chosen tool, outcome, and metadata. Logged decisions are the input data for offline evaluation.

**Example:**
```json
{
  "intent": "find_documentation",
  "available_tools": ["search_docs", "list_files", "ask_human"],
  "chosen_tool": "search_docs",
  "outcome": "success",
  "latency_ms": 150,
  "cost": 0.002
}
```

---

## Candidate Policy

**Definition:** A routing policy being evaluated for potential production use. Multiple candidate policies can be compared against the same set of logged decisions to identify the best performer.

**Example candidates:** `contextweaver_v1`, `strict_policy`, `cost_aware`, `baseline`

---

## Unsafe Baseline

**Definition:** A routing policy that prioritizes speed or cost over safety, used as a reference point to measure the safety improvements of governed policies. The unsafe baseline helps teams understand the safety cost of optimization.

**Related:** [Governed Path](#governed-path)

---

## Governed Path

**Definition:** A routing policy that includes safety guardrails, approval workflows, and coverage checks. Governed paths are slower but safer than ungoverned alternatives.

**Example:** A policy that requires human approval for high-risk actions like database writes or financial transactions.

**Related:** [Context Firewall](#context-firewall), [Bounded Choice Card](#bounded-choice-card)

---

## Context Firewall

**Definition:** A safety mechanism that limits the information available to the agent when making routing decisions. Context firewalls prevent the agent from accessing sensitive data that could lead to unsafe actions.

**Example:** When routing a support ticket, the context firewall might hide the user's payment information to prevent the agent from making unauthorized charges.

**Related:** [Governed Path](#governed-path)

---

## Bounded Choice Card

**Definition:** A pre-approved set of tools available to the agent in a specific context. Instead of exposing the full tool catalog, bounded choice cards restrict options to a safe, context-appropriate subset.

**Example:** For a "read-only support" context, the choice card might include `search_docs` and `list_tickets` but exclude `update_ticket` and `delete_record`.

**Related:** [Context Firewall](#context-firewall)

---

## Support/Coverage Warning

**Definition:** A warning emitted when the historical data contains too few examples of a specific `(intent, chosen_tool)` pair to make reliable statistical inferences. Low support means the evaluation results may be unreliable.

**Threshold:** In this lab, support warnings trigger when the count of historical matches falls below a configurable threshold (default: 10).

**Example:** If only 2 logged decisions match the pattern `(intent="refund_request", tool="manual_review")`, the support warning will flag this as statistically unreliable.

---

## Oracle Tool

**Definition:** A tool that provides perfect information about what the "correct" action should have been. In offline evaluation, oracle tools are used to measure regret by comparing the agent's choice against the ideal choice.

**Example:** If the logged decision shows the agent chose `search_docs` but the user ultimately needed `ask_human`, the oracle tool would identify `ask_human` as the correct choice.

**Related:** [Regret](#regret)

---

## Regret

**Definition:** The difference in outcome between the agent's chosen action and the optimal action. Regret measures the "cost of not knowing" — how much worse did the agent perform compared to the oracle?

**Calculation:**
```
regret = oracle_outcome - actual_outcome
```

**Example:** If the oracle action would have resolved the ticket in 1 step but the agent's action took 3 steps, the regret is 2 steps.

**Related:** [Oracle Tool](#oracle-tool)

---

## Approval-Required Action

**Definition:** An action that requires human approval before execution. Approval-required actions are used for high-risk operations where the cost of an incorrect action is high.

**Examples:**
- Database writes or deletions
- Financial transactions
- Access to sensitive data
- Changes to production systems

**Related:** [Governed Path](#governed-path)

---

## Cross-References

| Term | Related Terms |
|------|---------------|
| Agent Routing | Tool Selection, Candidate Policy |
| Tool Selection | Agent Routing, MCP-Style Tools |
| Tool-Calling Agent | MCP-Style Tools |
| Offline Evaluation | Logged Decision, Candidate Policy |
| Logged Decision | Offline Evaluation, Oracle Tool |
| Candidate Policy | Agent Routing, Unsafe Baseline |
| Unsafe Baseline | Governed Path, Regret |
| Governed Path | Context Firewall, Bounded Choice Card |
| Context Firewall | Governed Path, Bounded Choice Card |
| Bounded Choice Card | Context Firewall, Governed Path |
| Support/Coverage Warning | Logged Decision |
| Oracle Tool | Regret |
| Regret | Oracle Tool, Unsafe Baseline |
| Approval-Required Action | Governed Path |

---

*This glossary is maintained as part of the [agent-routing-eval-lab](https://github.com/dgenio/agent-routing-eval-lab) project. For corrections or additions, please open an issue or pull request.*
