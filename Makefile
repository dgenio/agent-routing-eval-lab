PYTHON ?= python3

# Fixed generation timestamp so `make report`/`make demo` produce byte-stable
# reports and committed artifacts don't drift on every run (issue #75). Override
# to use a different stamp; unset entirely to fall back to the wall clock.
SOURCE_DATE_EPOCH ?= 1767225600
export SOURCE_DATE_EPOCH

# This Makefile uses `>` instead of tabs for recipe lines so the file stays
# visibly consistent across editors; do not reindent recipes with tabs.
.RECIPEPREFIX := >

.PHONY: install test generate-data evaluate report demo unsafe-demo governed-demo validate gate help

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

unsafe-demo: ## Run the ungoverned unsafe baseline agent and show what breaks
>$(PYTHON) -m agent_routing_eval_lab.cli unsafe-demo

governed-demo: ## Run the governed agent and show the before/after vs the unsafe baseline
>$(PYTHON) -m agent_routing_eval_lab.cli governed-demo

validate: ## Validate the sample logged-decisions CSV against the schema
>$(PYTHON) -m agent_routing_eval_lab.cli validate --input examples/logged_decisions.sample.csv

gate: ## Run the CI gate against the sample CSV
>$(PYTHON) -m agent_routing_eval_lab.cli gate --input examples/logged_decisions.sample.csv --max-unsafe-rate 0.05 --min-success-rate 0.5
