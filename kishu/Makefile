.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")

.PHONY: help
help:             ## Show the help.
	@echo "Usage: make <target>"
	@echo " "
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep


.PHONY: show
show:             ## Show the current environment.
	@echo "Current environment:"
	@if [ "$(USING_POETRY)" ]; then poetry env info && exit; fi
	@echo "Running using $(ENV_PREFIX)"
	@$(ENV_PREFIX)python -V
	@$(ENV_PREFIX)python -m site

.PHONY: install
install:          ## Install the project in dev mode.
	@if [ "$(USING_POETRY)" ]; then poetry install && exit; fi
	$(ENV_PREFIX)pip install -e .[dev]

.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)isort kishu/
	$(ENV_PREFIX)black -l 127 kishu/
	$(ENV_PREFIX)black -l 127 tests/

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 --extend-ignore=E203 --max-line-length 127 kishu/
	$(ENV_PREFIX)black -l 127 --check kishu/
	$(ENV_PREFIX)black -l 127 --check tests/
	$(ENV_PREFIX)mypy --ignore-missing-imports kishu/

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -vv --cov-config .coveragerc --cov=kishu -l --tb=short --maxfail=1 tests
	$(ENV_PREFIX)coverage xml
	$(ENV_PREFIX)coverage html

.PHONY: clean
clean:            ## Clean unused files.
	@find ./kishu -name '*.pyc' -exec rm -f {} \;
	@find ./kishu -d -name '__pycache__' -exec rm -rf {} \;
	@find ./kishu -name 'Thumbs.db' -exec rm -f {} \;
	@find ./kishu -name '*~' -exec rm -f {} \;
	@find ./tests -name '*.pyc' -exec rm -f {} \;
	@find ./tests -d -name '__pycache__' -exec rm -rf {} \;
	@find ./tests -name 'Thumbs.db' -exec rm -f {} \;
	@find ./tests -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build
