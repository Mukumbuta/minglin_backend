# Django/Python targets
install:
	pipenv install

run:
	pipenv run python3 manage.py runserver

test:
	pipenv run python3 manage.py test

migrate:
	pipenv run python3 manage.py migrate

collectstatic:
	pipenv run python3 manage.py collectstatic --noinput

createsuperuser:
	pipenv run python3 manage.py createsuperuser

shell:
	pipenv run python3 manage.py shell

# Database management
clear-db:
	pipenv run python3 manage.py flush --noinput

# Docker targets
docker-build:
	docker build -t minglin-backend:1.0.0 .

docker-run:
	docker run -p 8000:8000 --env-file .env minglin-backend:1.0.0

docker-compose-up:
	docker compose up -d

docker-compose-down:
	docker compose down

docker-clean:
	docker system prune -f

# Production targets
.PHONY: prod-start prod-stop prod-restart prod-logs prod-clean

prod-start: check-tools
	@bash scripts/install-tools.sh
	@echo "🚀 Starting production environment..."
	@docker compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@until curl -f http://localhost:8000/api/v1/healthcheck/ >/dev/null 2>&1; do \
		echo "   Waiting for Django API..."; \
		sleep 5; \
	done
	@echo "✅ Production environment is ready!"
	@echo "🌐 API is running at: http://localhost:8000"
	@echo "📊 PostgreSQL is running at: localhost:5432"

prod-stop:
	@echo "🛑 Stopping production environment..."
	@docker compose down
	@echo "✅ Production environment stopped"

prod-restart: prod-stop prod-start

prod-logs:
	@echo "📋 Showing production logs..."
	@docker compose logs -f

prod-clean:
	@echo "🧹 Cleaning production environment..."
	@docker compose down -v
	@docker image rm minglin-backend:1.0.0 2>/dev/null || true
	@echo "✅ Production environment cleaned"

# Development targets with dependencies
.PHONY: dev-setup dev-start dev-stop dev-restart dev-logs dev-clean check-db check-migrations

# Check if required tools are installed
check-tools:
	@echo "🔍 Checking required tools..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is not installed. Run: bash scripts/install-tools.sh"; exit 1; }
	@command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose is not installed. Run: bash scripts/install-tools.sh"; exit 1; }
	@command -v make >/dev/null 2>&1 || { echo "❌ Make is not installed. Run: bash scripts/install-tools.sh"; exit 1; }
	@echo "✅ All required tools are available"

# Check if database is running
check-db:
	@echo "🔍 Checking if PostgreSQL is running..."
	@docker compose ps db | grep -q "Up" || { echo "❌ PostgreSQL is not running. Starting it..."; make start-db; }

# Check if migrations are applied
check-migrations:
	@echo "🔍 Checking if migrations are applied..."
	@docker compose exec -T web python manage.py migrate || { echo "❌ Migrations failed. Please check the logs."; exit 1; }
	@echo "✅ Migrations are up to date"

# Start database container
start-db:
	@echo "🚀 Starting PostgreSQL container..."
	@docker compose up -d db
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@until docker compose exec -T db pg_isready -U minglin >/dev/null 2>&1; do \
		echo "   Waiting for PostgreSQL..."; \
		sleep 2; \
	done
	@echo "✅ PostgreSQL is ready"

# Run database migrations
run-migrations:
	@echo "🔄 Running database migrations..."
	@docker compose exec -T web python manage.py migrate
	@echo "✅ Migrations completed"

# Build development Docker image
build-dev-image:
	@echo "🔨 Building development Docker image..."
	@docker compose build web
	@echo "✅ Development image built successfully"

# Start development environment (main target)
dev-start: check-tools start-db build-dev-image
	@echo "🚀 Starting development environment..."
	@docker compose up -d web
	@echo "⏳ Waiting for API to be ready..."
	@until curl -f http://localhost:8000/api/v1/healthcheck/ >/dev/null 2>&1; do \
		echo "   Waiting for API..."; \
		sleep 3; \
	done
	@echo "✅ Development environment is ready!"
	@echo "🌐 API is running at: http://localhost:8000"
	@echo "📊 PostgreSQL is running at: localhost:5432"
	@echo ""
	@echo "Useful commands:"
	@echo "  make dev-logs     # View logs"
	@echo "  make dev-stop     # Stop all services"
	@echo "  make dev-restart  # Restart all services"

# Stop development environment
dev-stop:
	@echo "🛑 Stopping development environment..."
	@docker compose down
	@echo "✅ Development environment stopped"

# Restart development environment
dev-restart: dev-stop dev-start

# View development logs
dev-logs:
	@echo "📋 Showing development logs..."
	@docker compose logs -f

# Clean development environment
dev-clean:
	@echo "🧹 Cleaning development environment..."
	@docker compose down -v
	@docker image rm minglin-backend-dev:latest 2>/dev/null || true
	@echo "✅ Development environment cleaned"

# One-click setup (installs tools and starts environment)
dev-setup:
	@echo "🚀 One-click development setup..."
	@echo "This will install required tools and start the development environment."
	@echo ""
	@read -p "Do you want to continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@bash scripts/install-tools.sh
	@make dev-start 