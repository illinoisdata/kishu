.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
SOURCE_DIRS=kishu/ tests/ coverage/
MAX_LINE_LENGTH=127

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
	$(ENV_PREFIX)isort ${SOURCE_DIRS}
	$(ENV_PREFIX)black -l ${MAX_LINE_LENGTH} ${SOURCE_DIRS}

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 --select=E9,F63,F7,F82 --show-source ${SOURCE_DIRS} \
		&& $(ENV_PREFIX)flake8 --max-complexity=100 --max-line-length=${MAX_LINE_LENGTH} --extend-ignore=W503,E203,E701 ${SOURCE_DIRS} \
		&& $(ENV_PREFIX)black -l ${MAX_LINE_LENGTH} --check ${SOURCE_DIRS} \
		&& $(ENV_PREFIX)mypy --ignore-missing-imports ${SOURCE_DIRS}

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)pytest -vv --cov-config .coveragerc --cov=kishu -l --tb=short --maxfail=1 tests \
		&& $(ENV_PREFIX)coverage xml \
		&& $(ENV_PREFIX)coverage html

.PHONY: clean
clean:            ## Clean unused files.
	@find ${SOURCE_DIRS} -name '*.pyc' -exec rm -f {} \;
	@find ${SOURCE_DIRS} -d -name '__pycache__' -exec rm -rf {} \;
	@find ${SOURCE_DIRS} -name 'Thumbs.db' -exec rm -f {} \;
	@find ${SOURCE_DIRS} -name '*~' -exec rm -f {} \;
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov
	@rm -rf .tox/
	@rm -rf docs/_build

.PHONY: release
release:          ## Build and upload to PyPI.
	$(ENV_PREFIX)python -m build
	$(ENV_PREFIX)twine upload dist/*
