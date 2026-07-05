"""Runnable unsafe baseline agent.

A deliberately ungoverned tool-using agent that demonstrates — rather than merely
asserts — the failure modes this lab warns about: full-catalog distraction,
prompt-only "safety", raw tool output trusted as instruction, and unapproved
sensitive writes. It runs offline on a fixed synthetic scenario set and emits
evaluator-ready decision logs.
"""
