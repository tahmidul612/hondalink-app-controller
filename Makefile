.PHONY: help build up down restart logs shell test lint format clean health

help:
	@echo "HondaLink Controller - Docker Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make build          Build Docker image"
	@echo "  make up             Start services in background"
	@echo ""
	@echo "Management:"
	@echo "  make down           Stop and remove containers"
	@echo "  make restart        Restart services"
	@echo "  make logs           View container logs"
	@echo "  make shell          Open shell in container"
	@echo ""
	@echo "Monitoring:"
	@echo "  make health         Check service health"
	@echo "  make stats          Show resource usage"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make lint           Check code style"
	@echo "  make format         Format code"
	@echo "  make clean          Remove containers and images"

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for service to be healthy..."
	@sleep 5
	@docker compose ps

down:
	docker compose down

restart:
	docker compose restart
	@docker compose ps

logs:
	docker compose logs -f

shell:
	docker compose exec hondalink-controller /bin/bash

health:
	@docker compose ps
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:8000/health | jq . || echo "Service not responding"

stats:
	docker stats hondalink-controller --no-stream

test:
	docker compose exec hondalink-controller pytest

lint:
	docker compose exec hondalink-controller ruff check src/ tests/

format:
	docker compose exec hondalink-controller ruff format src/ tests/

clean:
	docker compose down -v
	docker rmi hondalink-controller:latest || true
	@echo "Cleaned up containers and images"
