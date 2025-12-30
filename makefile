BLUE      := $(shell tput -Txterm setaf 4)
GREEN     := $(shell tput -Txterm setaf 2)
TURQUOISE := $(shell tput -Txterm setaf 6)
WHITE     := $(shell tput -Txterm setaf 7)
YELLOW    := $(shell tput -Txterm setaf 3)
GREY      := $(shell tput -Txterm setaf 1)
RESET     := $(shell tput -Txterm sgr0)

HELP_FUN = \
	%help; \
	use Data::Dumper; \
	while(<>) { \
		if (/^([_a-zA-Z0-9\-%]+)\s*:.*\#\#(?:@([a-zA-Z0-9\-_\s]+))?\t(.*)$$/ \
			|| /^([_a-zA-Z0-9\-%]+)\s*:.*\#\#(?:@([a-zA-Z0-9\-]+))?\s(.*)$$/) { \
			$$c = $$2; $$t = $$1; $$d = $$3; \
			push @{$$help{$$c}}, [$$t, $$d, $$ARGV] unless grep { grep { grep /^$$t$$/, $$_->[0] } @{$$help{$$_}} } keys %help; \
		} \
	}; \
	for (sort keys %help) { \
		printf("${WHITE}%24s:${RESET}\n\n", $$_); \
		for (@{$$help{$$_}}) { \
			printf("%s%25s${RESET}%s  %s${RESET}\n", \
				( $$_->[2] eq "makefile" || $$_->[0] eq "help" ? "${YELLOW}" : "${GREY}"), \
				$$_->[0], \
				( $$_->[2] eq "makefile" || $$_->[0] eq "help" ? "${GREEN}" : "${GREY}"), \
				$$_->[1] \
			); \
		} \
		print "\n"; \
	}

.DEFAULT_GOAL := help

.PHONY: help
help:: ##@Usage Show this help.
	@echo ""
	@printf "%30s " "${YELLOW}TARGETS"
	@echo "${RESET}"
	@echo ""
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

.PHONY: build-mcp test lint type format format-check manual-test clean

build-mcp:	##@Docker Build clockodo-mcp:latest image
	docker build -t clockodo-mcp:latest .

test:	##@Testing Run pytest with coverage in container
	docker compose -f docker-compose.test.yml run --rm test

lint:	##@Code-Quality Run pylint in container
	docker compose -f docker-compose.test.yml run --rm lint

type:	##@Code-Quality Run mypy type checking in container
	docker compose -f docker-compose.test.yml run --rm type

format:	##@Code-Quality Format code with black in container
	docker compose -f docker-compose.test.yml run --rm -v .:/app -w /app style-check sh -c "black /app/src/clockodo_mcp /app/tests"

format-check:	##@Code-Quality Check code formatting in container
	docker compose -f docker-compose.test.yml run --rm style-check

manual-test:	##@Manual Start Jupyter notebook for manual testing
	docker compose -f docker-compose.test.yml up jupyter

clean:	##@Cleanup Remove build artifacts and cache
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache tests/.coverage.xml tests/.junit.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
