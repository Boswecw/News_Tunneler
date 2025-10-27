.PHONY: help install dev test lint format seed migrate up down clean

help:
	@echo "News Tunneler Backend - Available Commands"
	@echo ""
	@echo "  make install      Install dependencies"
	@echo "  make dev          Run development server"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linting"
	@echo "  make format       Format code"
	@echo "  make seed         Seed database with sample data"
	@echo "  make migrate      Run database migrations"
	@echo "  make clean        Clean up generated files"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v --tb=short

lint:
	ruff check app/ tests/
	black --check app/ tests/

format:
	black app/ tests/
	ruff check --fix app/ tests/

seed:
	python -m app.seeds.seed

migrate:
	alembic upgrade head

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist build *.egg-info

