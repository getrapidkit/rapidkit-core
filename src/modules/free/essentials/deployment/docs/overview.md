# Deployment Toolkit Module Overview

The Deployment module provides portable Docker, Compose, Makefile, and CI assets for rapid
deployment of RapidKit applications across local, staging, and production environments.

## Key Capabilities

- **Multi-environment Compose** – Layered Docker Compose overlays for local development, staging,
  and production with shared base configuration.
- **Makefile automation** – Common tasks (build, up, down, logs, exec, migrations) wrapped in simple
  `make` commands.
- **CI/CD workflows** – Pre-configured GitHub Actions, GitLab CI, and Jenkins pipelines for
  automated testing and deployment.
- **Container optimization** – Multi-stage Dockerfile with build cache layers, security hardening,
  and minimal production images.
- **Health orchestration** – Docker Compose health checks integrated with application health
  endpoints.
- **Database migrations** – Alembic integration with migration tasks in Compose and CI workflows.
- **Framework agnostic** – Works with FastAPI, NestJS, and custom applications with minimal
  configuration.

## Module Components

- **Docker Assets**: Multi-stage Dockerfile with development and production targets
- **Compose Overlays**: Base, local, and production Compose configurations
- **Makefile**: Automated commands for common deployment tasks
- **CI Workflows**: GitHub Actions, GitLab CI, and Jenkins pipelines
- **Health Checks**: Container health monitoring and orchestration
- **Migration Tools**: Database migration automation with Compose

## Architecture

```
┌──────────────────────────────────┐
│  Deployment Toolkit              │
├──────────────┬───────────────────┤
│  Dockerfile  │  Compose Overlays │
│  - dev       │  - base.yml       │
│  - prod      │  - local.yml      │
│              │  - production.yml │
├──────────────┼───────────────────┤
│  Makefile    │  CI Workflows     │
│  - build     │  - test           │
│  - up/down   │  - deploy         │
│  - logs      │  - migrations     │
└──────────────┴───────────────────┘
```

## Quick Start

### Local Development

```bash
# Build and start local stack
make docker-build
make docker-up

# View logs
make docker-logs

# Run migrations
make docker-migrate

# Execute commands in container
make docker-exec cmd="python manage.py shell"

# Stop and clean up
make docker-down
```

### Production Deployment

```bash
# Build production image
make docker-build-prod

# Start production stack
make docker-up-prod

# Health check
curl http://localhost:8000/health
```

## Generated Files

### Docker Assets

- `Dockerfile` - Multi-stage build with dev and production targets
- `.dockerignore` - Exclude unnecessary files from image

### Compose Files

- `deploy/compose/base.yml` - Shared configuration (images, volumes, networks)
- `deploy/compose/local.yml` - Development overrides (bind mounts, live reload)
- `deploy/compose/production.yml` - Production settings (restart policies, resource limits)

### CI/CD

- `.github/workflows/deploy.yml` - GitHub Actions workflow
- `.gitlab-ci.yml` - GitLab CI pipeline
- `Jenkinsfile` - Jenkins pipeline configuration

### Automation

- `Makefile` - Deployment commands and shortcuts

## Configuration

Environment-specific settings:

```yaml
# base.yml - Shared configuration
services:
  app:
    image: ${DOCKER_IMAGE}:${VERSION}
    env_file: .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3

# local.yml - Development overrides
services:
  app:
    build:
      target: development
    volumes:
      - ./src:/app/src:ro
    ports:
      - "8000:8000"
      - "5678:5678"  # debugpy

# production.yml - Production overrides
services:
  app:
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Multi-Stage Dockerfile

```dockerfile
# Development stage
FROM python:3.10-slim as development
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]

# Production stage
FROM python:3.10-slim as production
WORKDIR /app
COPY --from=development /app .
RUN pip install --no-cache-dir -r requirements.txt
USER nobody
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker"]
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Deploy
on: [push]
jobs:
    deploy:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Build and test
              run: |
                  make docker-build
                  make docker-test
            - name: Deploy to production
              run: make docker-deploy
```

## Health Checks

Container health monitoring:

```yaml
healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 3s
    retries: 3
    start_period: 40s
```

## Database Migrations

Automated migration workflow:

```bash
# Run migrations in container
make docker-migrate

# Create new migration
make docker-exec cmd="alembic revision -m 'add users table'"

# Rollback migration
make docker-exec cmd="alembic downgrade -1"
```

## Customization Options

Override defaults via environment variables:

```bash
# Docker image settings
DOCKER_IMAGE_NAME=myapp
DOCKER_REGISTRY_URL=registry.example.com

# Feature toggles
RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES=1
RAPIDKIT_DEPLOYMENT_SKIP_CI=0
RAPIDKIT_DEPLOYMENT_INCLUDE_REDIS=1
```

## Supported Environments

- **Local**: Docker Compose with hot reload and debugging
- **Staging**: Production-like setup with test data
- **Production**: Optimized images with health checks and auto-restart
- **CI/CD**: Automated testing and deployment pipelines

## Security Features

- **Non-root user**: Containers run as `nobody` user
- **Secret management**: Environment file injection
- **Image scanning**: Trivy integration in CI
- **Network isolation**: Internal networks for services

## Getting Help

- **Usage Guide**: Detailed deployment instructions
- **Advanced Guide**: Custom Docker configurations
- **Troubleshooting**: Common deployment issues
- **Migration Guide**: Upgrading deployment assets

For issues and questions, visit our
[GitHub repository](https://github.com/getrapidkit/rapidkit-core).
