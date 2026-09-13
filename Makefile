# Terra Virtualis (demo-paragraphica)

.DEFAULT_GOAL := help

.PHONY: help install lock lint format test coverage ci env-check run dry-run history gallery serve service-install service-uninstall clean

help: ## Show this help
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} \
	  /^# === .* ===$$/  { sub(/^# === /, ""); sub(/ ===$$/, ""); printf "\n\033[33m%s\033[0m\n", $$0 } \
	  /^[a-zA-Z0-9_-]+:.*?## / { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)
	@echo ""

# === Setup ===

install: ## Create .venv (Python from .python-version) and install everything from uv.lock
	uv sync --locked --all-groups --all-extras

lock: ## Re-resolve dependencies and rewrite uv.lock
	uv lock

# === Check ===

lint: ## ruff check + format --check
	uv run ruff check .
	uv run ruff format --check .

format: ## ruff format + fix
	uv run ruff format .
	uv run ruff check --fix .

test: ## Run the test suite (offline; uses recorded fixtures in tests/)
	uv run pytest

coverage: ## Test suite with coverage report
	uv run pytest --cov=src/paragraphica --cov-report=term-missing

ci: lint test ## Full local gate

# === Run ===
# API keys come from 1Password at run time via the references in op.env
# (`op run` injects them into the child process only). OP= to bypass, e.g.
# when the variables are already exported: make run OP=

LOCATION ?= Schiphol-Rijk
STYLE ?= photo
BACKEND ?= gemini
OP ?= op run --env-file=op.env --

env-check: ## Show which 1Password items in op.env resolve (prints no values)
	tools/op-env.sh --check

run: ## Generate one image into the history store (output/): make run LOCATION="Amsterdam" STYLE="film noir"
	$(OP) uv run terra generate --location "$(LOCATION)" --style "$(STYLE)" --backend "$(BACKEND)"

dry-run: ## Description + prompt only, no image call
	$(OP) uv run terra generate --location "$(LOCATION)" --style "$(STYLE)" --backend "$(BACKEND)" --dry-run

history: ## Recent generations from output/history.jsonl
	uv run terra history

gallery: ## Rebuild output/index.html and open it
	uv run terra gallery --open

serve: ## Run the HTTP service on :8471 (gallery at /, API for the Pi client)
	$(OP) uv run --extra service terra serve

PLIST = io.lab271.terra.plist
service-install: ## Install + start the launchd agent on this Mac (Mac Mini)
	sed -e "s|__REPO__|$(CURDIR)|g" -e "s|__HOME__|$(HOME)|g" deploy/launchd/$(PLIST) > $(HOME)/Library/LaunchAgents/$(PLIST)
	launchctl bootout gui/$$(id -u)/io.lab271.terra 2>/dev/null || true
	launchctl bootstrap gui/$$(id -u) $(HOME)/Library/LaunchAgents/$(PLIST)
	@echo "started; logs: $(HOME)/Library/Logs/terra.log  health: curl localhost:8471/healthz"

service-uninstall: ## Stop + remove the launchd agent
	launchctl bootout gui/$$(id -u)/io.lab271.terra 2>/dev/null || true
	rm -f $(HOME)/Library/LaunchAgents/$(PLIST)


# === Housekeeping ===

clean: ## Remove venv, caches and build output
	rm -rf .venv .pytest_cache .ruff_cache .coverage build dist *.egg-info
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
