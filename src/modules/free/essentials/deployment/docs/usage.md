# Deployment Module Usage Guide

This guide explains how to integrate the RapidKit deployment module into an existing project.

## Prerequisites

- Python 3.10 or newer for FastAPI assets
- Node.js 20.x for NestJS assets
- RapidKit CLI installed in the project virtual environment

## Installation

```bash
rapidkit add module deployment
rapidkit modules lock --overwrite
```

The first command adds the module to the active project. The lock command refreshes vendor snapshots
so other environments receive identical artefacts.

## Generating Assets

Run the module generator to emit project-level files:

```bash
poetry run python -m src.modules.free.essentials.deployment.generate fastapi .
```

Replace `fastapi` with `nestjs` for Node projects.

Generation outputs three Compose overlays under `deploy/compose/`:

- `base.yml` – shared configuration (images, env files, volumes)
- `local.yml` – bind mounts, live reload, dev-only ports
- `production.yml` – production commands, restart policy, hardened defaults

## Customisation

- Toggle CI output by setting `include_ci` in `module.yaml` or via the `RAPIDKIT_DEPLOYMENT_SKIP_CI`
  environment variable.
- Add Postgres services by setting `include_postgres` in `module.yaml` or exporting
  `RAPIDKIT_DEPLOYMENT_INCLUDE_POSTGRES=1` before generation.
- Override Compose image metadata with `docker_image_name` and `docker_registry_url` variables.

## Introspection Endpoints

The generated frameworks expose the deployment plan metadata so tooling can discover available
assets at runtime:

- **FastAPI**: `GET /deployment/plan` returns module/version plus asset descriptions and metadata
  (Dockerfile, Compose, workflow paths).
- **NestJS**: `GET /deployment/plan` mirrors the FastAPI payload, while `GET /deployment/assets`
  lists the raw asset entries.
- **Health**: `/api/health/module/deployment` (FastAPI) and `/health/deployment` (NestJS) surface
  the plan summary, asset counts, runtime flags, and resolved hostname for observability dashboards.

## Next Steps

- Review the rendered Makefile, Docker assets, and workflow under the project root.
- Start the local stack with `make docker-up` (uses `base.yml` + `local.yml` and enables the `local`
  profile).
- Bring up a production-like stack with `make docker-up-prod` (uses `base.yml` + `production.yml` in
  detached mode). Provide secrets via `docker compose --env-file` or CI secrets injection.
- Commit the updated `.rapidkit/vendor` directory alongside project artefacts.
