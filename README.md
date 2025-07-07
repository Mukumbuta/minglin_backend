# minglin Backend (Django/DRF/PostGIS Edition)

## Overview
This is the new backend for minglin, rebuilt with Django, Django REST Framework (DRF), and PostgreSQL/PostGIS for geospatial support. It is designed with modern SRE (Site Reliability Engineering) best practices, including:
- **Prometheus** metrics for monitoring
- **Sentry** for error tracking
- **Healthcheck** endpoints
- **Structured logging**
- **Dockerized deployment**
- **OpenAPI/Swagger docs** (drf-spectacular)
- **Heavily documented code and configuration**

## Project Philosophy
- **Transparency:** Every major component and configuration is documented inline and in this README.
- **Reliability:** SRE features are first-class citizens (metrics, health, error reporting, etc).
- **Developer Experience:** Easy onboarding, clear API structure (`/api/v1/...`), and robust local dev setup.

## Stack
- Python 3.12, Django 5.x, DRF, PostgreSQL + PostGIS
- Prometheus, Sentry, Docker, Gunicorn, CORS, drf-spectacular, django-prometheus, django-environ

## Setup Instructions

### 1. Install System Dependencies
- Python 3.12+
- PostgreSQL with PostGIS extension
- [pipenv](https://pipenv.pypa.io/en/latest/)
- Docker & Docker Compose (for containerized dev/prod)

### 2. Clone the Repository
```sh
git clone <your-github-repo-url>
cd minglin_backend
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root (see below for variables):
```
SECRET_KEY=replace-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=minglin
POSTGRES_USER=minglin
POSTGRES_PASSWORD=minglin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SENTRY_DSN=
```

### 4. Install Python Dependencies
```sh
pipenv install --dev
pipenv shell
```

### 5. Run Migrations
```sh
python manage.py migrate
```

### 6. Run the Development Server
```sh
python manage.py runserver
```

### 7. API Documentation
- Swagger/OpenAPI: `/api/schema/` and `/api/docs/`
- Prometheus metrics: `/metrics`
- Healthcheck: `/api/v1/healthcheck/`

## SRE Features
- **Prometheus:** Metrics at `/metrics` (enabled by django-prometheus)
- **Sentry:** Error tracking (set `SENTRY_DSN` in `.env`)
- **Healthcheck:** `/api/v1/healthcheck/` endpoint
- **Structured Logging:** Configurable in `settings.py`
- **Docker:** Production-ready Dockerfile and Compose
- **PostGIS:** Geospatial queries and fields

## API Structure
- All endpoints are under `/api/v1/`
- JWT authentication (to be configured)
- Models: User, Business, Deal (see `api/models.py`)

## Documentation
- Inline comments in all major files
- This README is your main onboarding guide
- See `settings.py` for configuration documentation

---

# minglin_backend

A RESTful API for managing authentication, users, businesses, and deals. Built with Node.js, Express, and MongoDB.

## Features
- API versioning (`/api/v1/`)
- Healthcheck endpoint
- Proper HTTP verbs for REST
- Logging with morgan and winston
- Environment-based configuration
- Database migrations
- Unit tests
- Postman collection for API testing

## Setup Instructions

### 1. Clone the repository
```sh
git clone <your-github-repo-url>
cd minglin_backend
```

### 2. Install dependencies
```sh
make install
```

### 3. Configure environment variables
Create a `.env` file in the root directory:
```
MONGO_URI=mongodb://localhost:27017/minglin
PORT=5000
```

### 4. Run database migrations
```sh
make migrate
```

### 5. Start the server
```sh
make run
```

### 6. Run tests
```sh
make test
```

### 7. Import Postman collection
Import `postman_collection.json` into Postman to test the API endpoints.

## 🚀 One-Click Development Setup

### Prerequisites
The following tools must be installed on your system:
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container orchestration
- **Make** - Build automation tool

If you don't have these tools installed, our setup script will install them for you automatically.

### Quick Start (One-Click Setup)
```sh
# This will install required tools and start the development environment
make dev-setup
```

### Manual Setup

#### Step 1: Install Required Tools
```sh
# Run the automated tool installation script
bash scripts/install-tools.sh
```

#### Step 2: Start Development Environment
```sh
# Start the API and database with hot reloading
make dev-start
```

### Development Workflow

#### Available Make Targets

| Target | Description | Dependencies |
|--------|-------------|--------------|
| `make dev-setup` | One-click setup (installs tools + starts environment) | None |
| `make dev-start` | Start development environment | check-tools, start-db, build-dev-image |
| `make dev-stop` | Stop all development services | None |
| `make dev-restart` | Restart all development services | dev-stop, dev-start |
| `make dev-logs` | View real-time logs | None |
| `make dev-clean` | Clean up all development resources | None |

#### Individual Targets

| Target | Description |
|--------|-------------|
| `make check-tools` | Verify Docker, Docker Compose, and Make are installed |
| `make start-db` | Start MongoDB container and wait for it to be ready |
| `make run-migrations` | Run database migrations |
| `make build-dev-image` | Build the development Docker image |

### Environment Variables
Create a `.env` file in the root directory:
```
MONGO_URI=mongodb://mongo-dev:27017/minglin_dev
PORT=5000
NODE_ENV=development
```

### Development Features
- **Hot Reloading**: Code changes automatically restart the server
- **Volume Mounting**: Source code is mounted for live development
- **Health Checks**: Automatic health monitoring for all services
- **Dependency Management**: Automatic tool installation and verification

### Production Docker Setup

#### Build Production Image
```sh
make docker-build
```

#### Run Production Container
```sh
# Using Docker directly
make docker-run

# Or using Docker Compose (includes MongoDB)
make docker-compose-up
```

### Docker Commands
- `make docker-build` - Build the production Docker image with semver tag
- `make docker-run` - Run the production container with environment variables
- `make docker-compose-up` - Start API and MongoDB with Docker Compose
- `make docker-compose-down` - Stop all containers
- `make docker-clean` - Clean up unused Docker resources

## API Endpoints
- `GET /api/v1/healthcheck` - Health check
- `POST /api/v1/auth/...` - Auth endpoints
- `GET /api/v1/users/...` - User endpoints
- `GET /api/v1/businesses/...` - Business endpoints
- `GET /api/v1/deals/...` - Deal endpoints

## License
MIT