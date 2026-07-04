include targets/help.mk

.PHONY: test
test: ## Run the full test suite. //testing
	uv run pytest . -q

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report in terminal. //testing
	uv run pytest --cov=core --cov=fetcher --cov=tagger --cov-report=term-missing . -q

.PHONY: coverage-html
coverage-html: ## Generate HTML coverage report (htmlcov/). //testing
	uv run pytest --cov=core --cov=fetcher --cov=tagger --cov-report=html . -q

.PHONY: lint
lint: ## Check lint, format, and import order (read-only). //lint
	uv run ruff check .
	uv run black --check --diff .
	uv run isort --profile black --check-only .

.PHONY: lint-fix
lint-fix: ## Apply ruff, black, and isort auto-fixes. //lint
	uv run ruff check --fix .
	uv run black .
	uv run isort --profile black .

.PHONY: type-check
type-check: ## Run mypy on all packages (strict). //lint
	uv run mypy -p core -p fetcher -p tagger
