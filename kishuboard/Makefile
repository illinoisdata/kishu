.ONESHELL:

NODE_INSTALLED=$(shell node -v > /dev/null 2>&1 && echo "yes")
KISHU_INSTALLED=$(shell pip list | grep -w "^kishu" && echo "yes")
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")

.PHONY: install_kishu
install_kishu: ## Install Kishu core and dependencies
	@if [ "$(KISHU_INSTALLED)" != "yes" ]; then \
		echo "Installing Kishu from source..."; \
		(cd ../kishu && make install) \
	fi

.PHONY: check_node
check_node:      ## Check if NodeJS is installed
	@if [ "$(NODE_INSTALLED)" != "yes" ]; then \
		echo "Node.js is not installed. Please install it from https://nodejs.org/"; \
		exit 1; \
	fi

.PHONY: install_frontend
install_frontend: check_node ## Install the NodeJS frontend
	@if [ ! -f package.json ]; then \
		echo "Initializing npm project..."; \
		npm init -y; \
	fi
	@npm install
	@npm run build

.PHONY: install_backend
install_backend: install_kishu ## Install the Kishu board
	@$(ENV_PREFIX)pip install -e .

.PHONY: install
install: install_frontend install_backend ## Install the frontend, backend, and Kishu board
	@echo "Installation completed successfully."
