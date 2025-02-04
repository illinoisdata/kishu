.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")
USING_POETRY=$(shell grep "tool.poetry" pyproject.toml && echo "yes")
SOURCE_DIRS=jupyterlab_kishu/handlers.py

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
	$(ENV_PREFIX)jupyter labextension develop . --overwrite
	$(ENV_PREFIX)jlpm build

.PHONY: rebuild
rebuild:          ## Rebuild on existing installation
	$(ENV_PREFIX)jlpm build

.PHONY: fmt
fmt:              ## Format code using black & isort.
	$(ENV_PREFIX)isort ${SOURCE_DIRS}
	$(ENV_PREFIX)black -l 127 ${SOURCE_DIRS}
	$(ENV_PREFIX)black -l 127 ui-tests/

.PHONY: lint
lint:             ## Run pep8, black, mypy linters.
	$(ENV_PREFIX)flake8 --extend-ignore=E203 --max-line-length 127 ${SOURCE_DIRS} \
		&& $(ENV_PREFIX)black -l 127 --check ${SOURCE_DIRS} \
		&& $(ENV_PREFIX)black -l 127 --check ui-tests/ \
		&& $(ENV_PREFIX)mypy --ignore-missing-imports ${SOURCE_DIRS}

.PHONY: test
test: lint        ## Run tests and generate coverage report.
	$(ENV_PREFIX)jlpm test

.PHONY: clean
clean:            ## Clean unused files.
	@find ./jupyterlab_kishu -name '*.pyc' -exec rm -f {} \;
	@find ./jupyterlab_kishu -d -name '__pycache__' -exec rm -rf {} \;
	@find ./jupyterlab_kishu -name 'Thumbs.db' -exec rm -f {} \;
	@find ./jupyterlab_kishu -name '*~' -exec rm -f {} \;
	@find ./ui-tests -name '*.pyc' -exec rm -f {} \;
	@find ./ui-tests -d -name '__pycache__' -exec rm -rf {} \;
	@find ./ui-tests -name 'Thumbs.db' -exec rm -f {} \;
	@find ./ui-tests -name '*~' -exec rm -f {} \;
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
	$(ENV_PREFIX)jlpm build
	$(ENV_PREFIX)python -m build
	$(ENV_PREFIX)twine upload dist/*
