.DEFAULT_GOAL := help
PYTHON := .venv/bin/python
PROMPTEVAL ?= /opt/workspace/supervisor/scripts/prompteval

.PHONY: help check test lint typecheck build eval deploy-check

help: ## Show the stable repository commands.
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check: lint typecheck test eval build deploy-check ## Run every merge gate without mutating epistemic state.

test: ## Run deterministic Python, canon, and site-copy tests.
	PYTHONPATH=. $(PYTHON) -m unittest discover -s . -p 'test_*.py'
	PYTHONPATH=. $(PYTHON) scripts/test_subscription_cli_launcher.py
	PYTHONPATH=. $(PYTHON) lab/canon/test_conformance.py
	PYTHONPATH=. $(PYTHON) reasoning/check_programmes.py --self-test
	PYTHONPATH=. $(PYTHON) -m lab.canon.guard

lint: ## Run the fatal-error Python lint profile.
	$(PYTHON) -m ruff check .

typecheck: ## Type-check the maintained publication and configuration boundary.
	PYTHONPATH=. $(PYTHON) -m mypy knowledge scripts synaplex_paths.py

eval: ## Validate prompt inventory and accepted baseline contracts (no model calls).
	PYTHONPATH=. PROMPTEVAL=$(PROMPTEVAL) $(PYTHON) scripts/check_prompt_baselines.py

build: ## Regenerate the authoritative projection and build the public site.
	PYTHONPATH=. $(PYTHON) -m knowledge.generate
	PYTHONPATH=. $(PYTHON) scripts/prepare_site_projection.py
	cd site && npm run build --ignore-scripts

deploy-check: ## Validate deployment units and Pages configuration sources.
	PYTHONPATH=. $(PYTHON) scripts/check_deploy_contract.py
