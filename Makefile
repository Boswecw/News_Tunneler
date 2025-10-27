.PHONY: help install dev build test clean docker-build docker-up docker-down docker-logs seed

help:
	@echo "News Tunneler - Make Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install all dependencies"
	@echo "  make dev           - Start development servers (backend + frontend)"
	@echo "  make dev-backend   - Start backend dev server only"
	@echo "  make dev-frontend  - Start frontend dev server only"
	@echo ""
	@echo "Building:"
	@echo "  make build         - Build both backend and frontend"
	@echo "  make build-backend - Build backend only"
	@echo "  make build-frontend - Build frontend only"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-backend  - Run backend tests"
	@echo ""
	@echo "Database:"
	@echo "  make seed          - Seed database with sample data"
	@echo "  make migrate       - Run database migrations"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Clean all build artifacts"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && bun install

dev:
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@(cd backend && python -m uvicorn app.main:app --reload) & \
	(cd frontend && bun run dev) & \
	wait

dev-backend:
	cd backend && python -m uvicorn app.main:app --reload

dev-frontend:
	cd frontend && bun run dev

build: build-backend build-frontend

build-backend:
	cd backend && python -m py_compile app/

build-frontend:
	cd frontend && bun run build

test: test-backend

test-backend:
	cd backend && python -m pytest tests/ -v

seed:
	cd backend && python -c "from app.seeds.seed import seed_sources, seed_articles, seed_settings; seed_sources(); seed_articles(); seed_settings(); print('Database seeded successfully!')"

migrate:
	cd backend && alembic upgrade head

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	rm -rf backend/.pytest_cache backend/__pycache__ backend/app/__pycache__
	rm -rf frontend/dist frontend/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

