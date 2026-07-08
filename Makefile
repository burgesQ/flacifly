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

# Container engine: prefer docker, fall back to podman (override with OCI=...).
OCI ?= $(shell command -v docker >/dev/null 2>&1 && echo docker || echo podman)
IMAGE ?= flacifly:latest

.PHONY: docker-build
docker-build: ## Build the OCI image locally (OCI=docker|podman, IMAGE=...). //container
	$(OCI) build -t $(IMAGE) .

.PHONY: docker-buildx
docker-buildx: ## Build the multi-arch image (amd64+arm64) via docker buildx. //container
	docker buildx build --platform linux/amd64,linux/arm64 -t $(IMAGE) .
