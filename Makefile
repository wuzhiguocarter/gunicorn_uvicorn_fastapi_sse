.PHONY: help install dev-install test lint format type-check clean run run-dev run-gunicorn load-test ramp-up test-client check-all

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package dependencies
	uv pip install -e .

dev-install:  ## Install development dependencies
	uv pip install -e ".[dev]"

test:  ## Run tests
	uv run pytest

test-coverage:  ## Run tests with coverage
	uv run pytest --cov=src/app --cov-report=html --cov-report=term-missing

coverage-view:  ## View HTML coverage report
	uv run python view_coverage.py

coverage-json:  ## Generate JSON coverage report
	uv run pytest --cov=src/app --cov-report=json --cov-report=term-missing

coverage-full:  ## Generate complete coverage report (HTML + JSON + XML)
	uv run pytest --cov=src/app --cov-report=html --cov-report=term-missing --cov-report=xml

coverage-check:  ## Check if coverage meets threshold (95%)
	uv run pytest --cov=src/app --cov-report=term-missing --cov-fail-under=95

coverage-branch:  ## Run coverage with branch coverage
	uv run pytest --cov=src/app --cov-branch --cov-report=html --cov-report=term-missing

quick-coverage:  ## Quick view of coverage statistics
	uv run python view_coverage.py

lint:  ## Run linting checks
	uv run ruff check src/app src/load_test src/tests .

format:  ## Format code with ruff
	uv run ruff format src/app src/load_test src/tests .

format-check:  ## Check code formatting with ruff
	uv run ruff format --check src/app src/load_test src/tests .

type-check:  ## Run type checking
	uv run mypy --package src.app --package src.load_test --package src.tests --ignore-missing-imports --no-error-summary

check-all: format-check lint type-check test  ## Run all quality checks

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run:  ## Run the server
	uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000

run-dev:  ## Run the server in development mode
	uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

run-gunicorn:  ## Run the server with gunicorn
	./start.sh

load-test:  ## Run simple load test
	uv run python src/load_test/scripts/run_load_test.py --simple

load-test-full:  ## Run full load test
	uv run python src/load_test/scripts/run_load_test.py --requests 100 --concurrency 10

load-test-ramp:  ## Run ramp-up load test
	uv run python src/load_test/scripts/run_load_test.py --ramp-up 30 --duration 60 --concurrency 20

ramp-up:  ## Run comprehensive ramp-up test (non-interactive)
	uv run python src/load_test/ramp_up_test.py --no-prompt

ramp-up-interactive:  ## Run ramp-up test with interactive prompts
	uv run python src/load_test/ramp_up_test.py

test-client:  ## Test load client metrics accuracy
	uv run python test_client_metrics.py

setup-dev:  ## Set up development environment
	@if [ ! -d ".venv" ]; then \
		uv venv --python 3.12; \
	fi
	uv pip install -e ".[dev]"
	@git config --unset-all core.hooksPath 2>/dev/null || true
	uv run pre-commit install -f

pre-commit:  ## Run pre-commit hooks
	uv run pre-commit run --all-files

demo:  ## Run demo with sample data
	@echo "Starting ChatBot SSE Server demo..."
	@echo "Open http://localhost:8000 in your browser to test"
	@echo "Press Ctrl+C to stop"
	uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

# Development shortcuts
dev:  ## Quick development setup and run
	make setup-dev
	make run-dev

quick-test:  ## Run tests quickly without coverage
	uv run pytest -v

smoke-test:  ## Run basic smoke tests
	uv run pytest src/tests/test_main.py -v

load-test-quick:  ## Quick load test (20 requests, 5 concurrency)
	uv run python src/load_test/scripts/run_load_test.py --requests 20 --concurrency 5 --simple

profile-memory:  ## Profile memory usage during load test
	uv run python -m memory_profiler src/load_test/scripts/run_load_test.py --requests 50 --concurrency 10

# Container commands (if needed)
container-build:  ## Build Docker container
	docker build -t chatbot-sse-server .

container-run:  ## Run Docker container
	docker run -p 8000:8000 chatbot-sse-server

container-test:  ## Test Docker container
	@echo "Testing Docker container..."
	@sleep 3
	curl -f http://localhost:8000/health || exit 1
	@echo "Container test passed!"
