PYTHON ?= python3
.RECIPEPREFIX := >

install:
>$(PYTHON) -m pip install --upgrade pip
>$(PYTHON) -m pip install -e .[dev]

test:
>pytest

generate-data:
>$(PYTHON) -m agent_routing_eval_lab.cli generate-data --output examples/logged_decisions.sample.csv --rows 300

evaluate:
>$(PYTHON) -m agent_routing_eval_lab.cli evaluate --input examples/logged_decisions.sample.csv

report:
>$(PYTHON) -m agent_routing_eval_lab.cli report --input examples/logged_decisions.sample.csv --output reports/example_report.md

demo:
>$(PYTHON) -m agent_routing_eval_lab.cli demo
