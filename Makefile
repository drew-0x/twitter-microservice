# Makefile for Twitter Microservices Project

.PHONY: help test test-users test-tweets test-feed test-search test-all
.PHONY: test-verbose test-coverage install-all clean format lint

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)Twitter Microservices - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test-all        - Run all tests for all services"
	@echo "  make test-users      - Run users service tests"
	@echo "  make test-tweets     - Run tweets service tests"
	@echo "  make test-feed       - Run feed service tests"
	@echo "  make test-search     - Run search service tests"
	@echo "  make test-verbose    - Run all tests with verbose output"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make install-all     - Install dependencies for all services"
	@echo "  make format          - Format code with black"
	@echo "  make lint            - Lint code with ruff"
	@echo "  make clean           - Clean up cache and temp files"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make up              - Start all services with docker-compose"
	@echo "  make down            - Stop all services"
	@echo "  make logs            - Show docker logs"

# ===== Testing =====

# Test environment variables
export TEST_ENV := \
	DB_USERNAME=test_user \
	DB_PASSWORD=test_pass \
	DB_HOST=localhost \
	DB_PORT=5432 \
	DB_DATABASE=test_db \
	JWT_SECRET=test_secret_key_for_testing_only \
	JAEGER=localhost:4317 \
	RABBITMQ_URL=amqp://test:test@localhost:5672 \
	REDIS_HOST=localhost \
	REDIS_PORT=6379 \
	ELASTICSEARCH_URL=http://localhost:9200 \
	USER_SERVICE_GRPC_TARGET=localhost:50051 \
	TWEET_SERVICE_GRPC_TARGET=localhost:50052

test-users:
	@echo "$(BLUE)Running users service tests...$(NC)"
	@cd users && $(TEST_ENV) uv run python -m pytest tests/ -v

test-tweets:
	@echo "$(BLUE)Running tweets service tests...$(NC)"
	@cd tweets && $(TEST_ENV) uv run python -m pytest tests/ -v

test-feed:
	@echo "$(BLUE)Running feed service tests...$(NC)"
	@cd feed && $(TEST_ENV) uv run python -m pytest tests/ -v

test-search:
	@echo "$(BLUE)Running search service tests...$(NC)"
	@cd search && $(TEST_ENV) uv run python -m pytest tests/ -v

test-all: test-users test-tweets test-feed test-search
	@echo "$(GREEN)All tests completed!$(NC)"

test-verbose:
	@echo "$(BLUE)Running all tests with verbose output...$(NC)"
	@cd users && uv run python -m pytest tests/ -vv -s
	@cd tweets && uv run python -m pytest tests/ -vv -s
	@cd feed && uv run python -m pytest tests/ -vv -s
	@cd search && uv run python -m pytest tests/ -vv -s

test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@cd users && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@cd tweets && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@cd feed && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@cd search && uv run python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage reports generated in each service's htmlcov/ directory$(NC)"

# ===== Development =====

install-all:
	@echo "$(BLUE)Installing dependencies for all services...$(NC)"
	@cd users && uv sync
	@cd tweets && uv sync
	@cd feed && uv sync
	@cd search && uv sync
	@echo "$(GREEN)All dependencies installed!$(NC)"

format:
	@echo "$(BLUE)Formatting code with black...$(NC)"
	@cd users && uv run black src/ tests/
	@cd tweets && uv run black src/ tests/
	@cd feed && uv run black src/ tests/
	@cd search && uv run black src/ tests/
	@echo "$(GREEN)Code formatted!$(NC)"

lint:
	@echo "$(BLUE)Linting code with ruff...$(NC)"
	@cd users && uv run ruff check src/ tests/
	@cd tweets && uv run ruff check src/ tests/
	@cd feed && uv run ruff check src/ tests/
	@cd search && uv run ruff check src/ tests/
	@echo "$(GREEN)Linting complete!$(NC)"

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -f {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# ===== Docker =====

up:
	@echo "$(BLUE)Starting services with docker-compose...$(NC)"
	docker-compose up --build -d

down:
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down

logs:
	docker-compose logs -f

# ===== Quick Test Shortcuts =====

test: test-all

t: test-all

tu: test-users

tt: test-tweets

tf: test-feed

ts: test-search
