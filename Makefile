PYTHON ?= python3

# This Makefile uses `>` instead of tabs for recipe lines so the file stays
# visibly consistent across editors; do not reindent recipes with tabs.
.RECIPEPREFIX := >

.PHONY: install test generate-data evaluate report demo help

help: ## Show available developer commands
>@printf '%s\n' 'Available targets:'
>@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the project with development dependencies
>$(PYTHON) -m pip install --upgrade pip
>$(PYTHON) -m pip install -e .[dev]

test: ## Run the pytest suite
>pytest

generate-data: ## Write the sample logged-decisions CSV
>$(PYTHON) -m agent_routing_eval_lab.cli generate-data --output examples/logged_decisions.sample.csv --rows 300

evaluate: ## Evaluate candidate policies on the sample CSV
>$(PYTHON) -m agent_routing_eval_lab.cli evaluate --input examples/logged_decisions.sample.csv

report: ## Write the example markdown report
>$(PYTHON) -m agent_routing_eval_lab.cli report --input examples/logged_decisions.sample.csv --output reports/example_report.md

demo: ## Run the end-to-end deterministic demo flow
>$(PYTHON) -m agent_routing_eval_lab.cli demo
