.PHONY: help install run-api build-api build-crawler run-api-container run-crawler-yogya run-crawler-indomaret run-crawler-alfagift stop-api stop-crawler clean lint test s3-list s3-rotate s3-backup

# Variables
IMAGE_API = bibit-api
IMAGE_CRAWLER = bibit-crawler
CONTAINER_API = bibit-api-container
CONTAINER_CRAWLER = bibit-crawler-container
API_PORT = 8000
REGISTRY = ghcr.io/k1m0ch1

# Crawler platforms
PLATFORM ?= yogyaonline
STEINDB_URL ?=
STEINDB_USERNAME ?=
STEINDB_PASSWORD ?=

# Object Storage Settings
CRAWLER_BACKUP_PATH = s3://storage-infra/playground/k1m0ch1/indiemart/backup/crawling/
INDIEMART_BACKUP_PATH = s3://storage-infra/playground/k1m0ch1/indiemart/backup/db/
CRAWLER_PATH = s3://storage-infra/playground/k1m0ch1/indiemart/backup/crawler.db
INDIEMART_PATH = s3://storage-infra/playground/k1m0ch1/indiemart/backup/indiemart.db
LOCAL_BACKUP_DIR = ~/workspace/indiemart/backup-indiemart

help: ## Show this help message
	@echo Usage: make [target]
	@echo:
	@echo Available targets:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

run-api: ## Run API server locally using uv
	uv run python src/main.py web.api

run-crawler: ## Run crawler locally (use PLATFORM=yogyaonline|klikindomaret|alfagift)
	uv run python src/main.py --target $(PLATFORM) do.scrap

# Docker Image Build Targets
build-api: ## Build API Docker image
	docker build -f Dockerfile.API -t $(IMAGE_API):latest -t $(REGISTRY)/$(IMAGE_API):latest .

build-crawler: ## Build crawler Docker image
	docker build -f Dockerfile.crawler -t $(IMAGE_CRAWLER):latest -t $(REGISTRY)/$(IMAGE_CRAWLER):latest .

# Docker Container Run Targets
run-api-container: ## Run API container (port 8000)
	docker run -d \
		--name $(CONTAINER_API) \
		-p $(API_PORT):8000 \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		--restart unless-stopped \
		$(IMAGE_API):latest

run-crawler-yogya: ## Run crawler container for Yogya Online
	docker run -d \
		--name $(CONTAINER_CRAWLER)-yogya \
		-e PLATFORM=yogyaonline \
		-e STEINDB_URL=$(STEINDB_URL) \
		-e STEINDB_USERNAME=$(STEINDB_USERNAME) \
		-e STEINDB_PASSWORD=$(STEINDB_PASSWORD) \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		--restart unless-stopped \
		$(IMAGE_CRAWLER):latest

run-crawler-indomaret: ## Run crawler container for Klik Indomaret
	docker run -d \
		--name $(CONTAINER_CRAWLER)-indomaret \
		-e PLATFORM=klikindomaret \
		-e STEINDB_URL=$(STEINDB_URL) \
		-e STEINDB_USERNAME=$(STEINDB_USERNAME) \
		-e STEINDB_PASSWORD=$(STEINDB_PASSWORD) \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		--restart unless-stopped \
		$(IMAGE_CRAWLER):latest

run-crawler-alfagift: ## Run crawler container for Alfagift
	docker run -d \
		--name $(CONTAINER_CRAWLER)-alfagift \
		-e PLATFORM=alfagift \
		-e STEINDB_URL=$(STEINDB_URL) \
		-e STEINDB_USERNAME=$(STEINDB_USERNAME) \
		-e STEINDB_PASSWORD=$(STEINDB_PASSWORD) \
		-v $(PWD)/data:/app/data \
		-v $(PWD):/app \
		--restart unless-stopped \
		$(IMAGE_CRAWLER):latest

# Container Management
stop-api: ## Stop and remove API container
	docker stop $(CONTAINER_API) || true
	docker rm $(CONTAINER_API) || true

stop-crawler: ## Stop and remove all crawler containers
	docker stop $(CONTAINER_CRAWLER)-yogya || true
	docker rm $(CONTAINER_CRAWLER)-yogya || true
	docker stop $(CONTAINER_CRAWLER)-indomaret || true
	docker rm $(CONTAINER_CRAWLER)-indomaret || true
	docker stop $(CONTAINER_CRAWLER)-alfagift || true
	docker rm $(CONTAINER_CRAWLER)-alfagift || true

restart-api: stop-api run-api-container ## Restart API container

logs-api: ## Show API container logs
	docker logs -f $(CONTAINER_API)

logs-crawler-yogya: ## Show Yogya crawler logs
	docker logs -f $(CONTAINER_CRAWLER)-yogya

logs-crawler-indomaret: ## Show Indomaret crawler logs
	docker logs -f $(CONTAINER_CRAWLER)-indomaret

logs-crawler-alfagift: ## Show Alfagift crawler logs
	docker logs -f $(CONTAINER_CRAWLER)-alfagift

# Development
lint: ## Run flake8 linter
	uv run flake8 src/

test: ## Run tests
	uv run python -m unittest discover

# Cleanup
clean: ## Clean up Python cache and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf .pytest_cache || true
	rm -rf .ruff_cache || true

clean-docker: stop-api stop-crawler ## Stop all containers and remove images
	docker rmi $(IMAGE_API):latest || true
	docker rmi $(IMAGE_CRAWLER):latest || true

# S3 Backup Management
s3-list: ## Show S3 storage usage
	s3cmd du -H s3://storage-infra

s3-rotate: ## Delete backup files older than 31 days (format: *yyyymmdd.db)
	@echo "Checking for old backup files (>31 days)..."
	@for path in $(CRAWLER_BACKUP_PATH) $(INDIEMART_BACKUP_PATH); do \
		echo "Checking $$path"; \
		s3cmd ls $$path | grep -E '[0-9]{8}\.db$$' | while read -r line; do \
			file=$$(echo $$line | awk '{print $$4}'); \
			filename=$$(basename $$file); \
			datestr=$$(echo $$filename | grep -oE '[0-9]{8}'); \
			if [ -n "$$datestr" ]; then \
				filedate=$$(date -d "$$datestr" +%s 2>/dev/null || date -j -f "%Y%m%d" "$$datestr" +%s 2>/dev/null); \
				cutoff=$$(date -d "31 days ago" +%s 2>/dev/null || date -v-31d +%s 2>/dev/null); \
				if [ $$filedate -lt $$cutoff ]; then \
					echo "Deleting old file: $$file ($$datestr)"; \
					s3cmd del $$file; \
				fi; \
			fi; \
		done; \
	done
	@echo "Rotation complete!"

s3-backup: ## Upload today's newest backups to S3 and cleanup local files
	@echo "Starting backup upload process..."
	@TODAY=$$(date +%Y%m%d); \
	echo "Today's date: $$TODAY"; \
	\
	CRAWL_FILE=$$(ls -t $(LOCAL_BACKUP_DIR)/crawl.db.$$TODAY* 2>/dev/null | head -1); \
	INDIEMART_FILE=$$(ls -t $(LOCAL_BACKUP_DIR)/indiemart.db.$$TODAY* 2>/dev/null | head -1); \
	\
	if [ -n "$$CRAWL_FILE" ]; then \
		echo "Found newest crawl.db backup: $$CRAWL_FILE"; \
		S3_CRAWL_NAME="crawl.db_$$TODAY"; \
		echo "Uploading to $(CRAWLER_BACKUP_PATH)$$S3_CRAWL_NAME"; \
		s3cmd put "$$CRAWL_FILE" "$(CRAWLER_BACKUP_PATH)$$S3_CRAWL_NAME"; \
		if [ $$? -eq 0 ]; then \
			echo "Upload successful, deleting local files matching crawl.db.*$$TODAY*"; \
			rm -f $(LOCAL_BACKUP_DIR)/crawl.db.*$$TODAY*; \
		else \
			echo "Upload failed for crawl.db, keeping local files"; \
		fi; \
	else \
		echo "No crawl.db backup found for today ($$TODAY)"; \
	fi; \
	\
	if [ -n "$$INDIEMART_FILE" ]; then \
		echo "Found newest indiemart.db backup: $$INDIEMART_FILE"; \
		S3_INDIEMART_NAME="indiemart.db_$$TODAY"; \
		echo "Uploading to $(INDIEMART_BACKUP_PATH)$$S3_INDIEMART_NAME"; \
		s3cmd put "$$INDIEMART_FILE" "$(INDIEMART_BACKUP_PATH)$$S3_INDIEMART_NAME"; \
		if [ $$? -eq 0 ]; then \
			echo "Upload successful, deleting local files matching indiemart.db.*$$TODAY*"; \
			rm -f $(LOCAL_BACKUP_DIR)/indiemart.db.*$$TODAY*; \
		else \
			echo "Upload failed for indiemart.db, keeping local files"; \
		fi; \
	else \
		echo "No indiemart.db backup found for today ($$TODAY)"; \
	fi; \
	\
	echo "Backup upload complete!"

# Quick start commands
dev: install ## Setup development environment
	@echo "✅ Development environment ready!"
	@echo "Run 'make run-api' to start the API server"

all: build-api build-crawler ## Build all Docker images
	@echo "✅ All Docker images built successfully!"

up: run-api-container ## Start API container
	@echo "✅ API container started on http://localhost:$(API_PORT)"

down: stop-api stop-crawler ## Stop all containers
	@echo "✅ All containers stopped"
