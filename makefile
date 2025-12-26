.PHONY: help lint format format-check test install clean build-mcp unittests manual-test
.DEFAULT_GOAL := help

help:  ##@Usage Show this help.
	@printf "\n%27s\n\n" "TARGETS"
	@awk 'BEGIN {FS = ":.*?##@"}; \
		/^[a-zA-Z_-]+:.*?##@/ { \
			if ($$2 != last) { \
				if (last != "") printf "\n"; \
				match($$2, /^[^ ]+/); \
				category = substr($$2, RSTART, RLENGTH); \
				printf "%20s:\n\n", category; \
				last = category; \
			} \
			description = substr($$2, RLENGTH + 2); \
			printf "%20s  %s\n", $$1, description; \
		}' $(MAKEFILE_LIST)
	@printf "\n"

build-mcp:  ##@Docker Build clockodo-mcp:latest image
	docker build -t clockodo-mcp:latest .

unittests:  ##@Docker Build docker
	docker compose -f docker-compose.test.yml up test

manual-test:  ##@Manual Start Jupyter notebook for manual testing
	docker compose -f docker-compose.test.yml up jupyter

lint:  ##@Code-Quality Run linters (ruff, mypy, pylint)
	ruff check src tests
	mypy src
	pylint src

format:  ##@Code-Quality Format code with black and isort
	black src tests
	isort src tests
	ruff check --fix src tests

format-check:  ##@Code-Quality Check code formatting without modifying
	black --check src tests
	isort --check-only src tests
	ruff check src tests

test:  ##@Code-Quality Run pytest with coverage
	pytest --cov=clockodo_mcp --cov-report=term-missing

install:  ##@Code-Quality Install package with dev dependencies
	pip install -e ".[dev]"

clean:  ##@Code-Quality Remove build artifacts and cache
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
