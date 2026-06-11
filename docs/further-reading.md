# Further Reading

These references provide background for agent routing, tool use, offline evaluation, context design, and governance. They are included as field context, not as claims that this repository implements or validates every technique described.

## Agent Tool Use

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) introduces a common pattern for combining reasoning traces with tool-using actions.
- [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761) explores how language models can learn when and how to call external tools.
- [Gorilla: Large Language Model Connected with Massive APIs](https://arxiv.org/abs/2305.15334) studies API/tool selection and invocation accuracy across large tool surfaces.

## Model Context Protocol and Tool Interfaces

- [Model Context Protocol documentation](https://modelcontextprotocol.io/docs) describes an open protocol for connecting AI applications to tools and contextual data sources.
- [MCP specification](https://spec.modelcontextprotocol.io/) provides the protocol-level reference for MCP clients, servers, tools, resources, and prompts.

## Offline and Off-Policy Evaluation

- [A Survey of Off-policy Evaluation in Reinforcement Learning](https://arxiv.org/abs/2003.06478) gives background on estimating policy quality from data collected by another policy.
- [Doubly Robust Policy Evaluation and Learning](https://arxiv.org/abs/1103.4601) is a foundational reference for counterfactual policy evaluation methods.

## Context Engineering

- [OpenAI prompt engineering guide](https://platform.openai.com/docs/guides/prompt-engineering) covers practical context and instruction design patterns for language-model applications.
- [Anthropic prompt engineering overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) covers task framing, context placement, examples, and evaluation-oriented prompting.

## AI Governance

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) provides a governance frame for mapping, measuring, managing, and governing AI risks.
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) summarizes common security and safety risks for LLM-backed systems.
