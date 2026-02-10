.DEFAULT_GOAL := help

.PHONY: help dev run install clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: ## Run with auto-reload (development)
	uvicorn webapp.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir webapp --reload-dir execution

run: ## Run without reload (production)
	uvicorn webapp.main:app --host 0.0.0.0 --port 8000

install: ## Install all dependencies
	pip install -r requirements.txt
	pip install -r webapp/requirements.txt

clean: ## Remove temp files and caches
	rm -f .tmp/job_applications/*.json .tmp/job_applications/*.md .tmp/job_applications/*.txt
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
