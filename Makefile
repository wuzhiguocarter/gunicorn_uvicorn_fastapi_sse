.PHONY: help install dev-install test lint format type-check clean run run-dev run-gunicorn load-test

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package dependencies
	python -m pip install -e .

dev-install:  ## Install development dependencies
	python -m pip install -e ".[dev]"

test:  ## Run tests
	python -m pytest src/tests/ -v

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
	ruff check src/app src/load_test src/tests

format:  ## Format code
	black src/app src/load_test src/tests
	isort src/app src/load_test src/tests

format-check:  ## Check code formatting
	black --check src/app src/load_test src/tests
	isort --check-only src/app src/load_test src/tests

type-check:  ## Run type checking
	mypy src/app src/load_test src/tests

check-all: format-check lint type-check test  ## Run all checks

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
	python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000

run-dev:  ## Run the server in development mode
	python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

run-gunicorn:  ## Run the server with gunicorn
	./start.sh

load-test:  ## Run simple load test
	python src/load_test/scripts/run_load_test.py --simple

load-test-full:  ## Run full load test
	python src/load_test/scripts/run_load_test.py --requests 100 --concurrency 10

load-test-ramp:  ## Run ramp-up load test
	python src/load_test/scripts/run_load_test.py --ramp-up 30 --duration 60 --concurrency 20

setup-dev:  ## Set up development environment
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"
	pre-commit install

pre-commit:  ## Run pre-commit hooks
	pre-commit run --all-files

demo:  ## Run demo with sample data
	@echo "Starting ChatBot SSE Server demo..."
	@echo "Open http://localhost:8000 in your browser to test"
	@echo "Press Ctrl+C to stop"
	python -m uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload