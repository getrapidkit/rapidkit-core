# Application Settings Module Overview

The Application Settings module provides centralized, type-safe configuration management for
RapidKit projects. It delivers environment-aware settings loading, hot reload capabilities, and
multi-source configuration with validation built on Pydantic.

## Key Capabilities

- **Multi-source configuration** – Load settings from environment variables, .env files, AWS Secrets
  Manager, HashiCorp Vault, and custom YAML sources with priority-based merging.
- **Type-safe validation** – Pydantic models ensure configuration correctness at startup with clear
  error messages for missing or invalid values.
- **Hot reload** – File watcher automatically reloads configuration during development without
  application restart.
- **Health monitoring** – `/api/health/module/settings` endpoint exposes configuration metadata,
  loaded sources, and validation status.
- **Framework adapters** – FastAPI dependency injection and NestJS configuration factories provide
  seamless integration.
- **Custom sources** – Extensible plugin architecture supports bridging external secrets management
  systems.

## Module Components

- **Settings Runtime**: Core configuration loader with Pydantic validation
- **Custom Sources**: Bridges for Vault, AWS Secrets, and YAML configuration
- **Hot Reload**: Development-mode file watcher for instant config updates
- **Health Checks**: Configuration status and source diagnostics
- **Framework Integration**: FastAPI dependencies and NestJS services

## Architecture

```
┌──────────────────┐
│  Application     │
│  Configuration   │
└──────────────────┘
         │
    ┌────────────────┐
    │   Settings     │ ← Type-safe config
    │   Runtime      │
    └────────────────┘
         │
    ┌────────────────────────────────┐
    │  Configuration Sources         │
    ├────────────────┬───────────────┤
    │  .env files    │  Environment  │
    │  Vault/AWS     │  YAML files   │
    └────────────────┴───────────────┘
```

## Quick Start

```python
from fastapi import FastAPI, Depends
from src.modules.free.essentials.settings.settings import Settings, get_settings

app = FastAPI()


@app.get("/config")
async def get_config(settings: Settings = Depends(get_settings)):
    return {
        "environment": settings.ENVIRONMENT,
        "app_name": settings.APP_NAME,
        "debug": settings.DEBUG,
    }
```

## Configuration

Environment variables or `.env` file:

```bash
ENVIRONMENT=production
APP_NAME=MyApp
DEBUG=false
DATABASE_URL=postgresql://localhost/mydb
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

## Supported Frameworks

- **FastAPI**: Full dependency injection with singleton settings instance
- **NestJS**: ConfigService with TypeScript type definitions
- **Custom**: Direct settings access for other frameworks

## Hot Reload

Enable automatic configuration reload during development:

```python
from src.modules.free.essentials.settings.hot_reload import enable_hot_reload

if settings.ENVIRONMENT == "development":
    enable_hot_reload(app, settings)
```

## Custom Configuration Sources

Extend with custom sources:

```python
from src.modules.free.essentials.settings.custom_sources import (
    register_vault_source,
    register_aws_secrets_source,
)

# Load from HashiCorp Vault
settings = register_vault_source(
    vault_url="https://vault.example.com",
    vault_token="s.xxx",
    secret_path="secret/data/myapp",
)

# Load from AWS Secrets Manager
settings = register_aws_secrets_source(
    secret_name="myapp/production", region_name="us-east-1"
)
```

## Health & Monitoring

Built-in health endpoint monitors:

- Configuration load status
- Active configuration sources
- Environment detection
- Validation errors and warnings

Access health status at `/api/health/module/settings`.

## Security Features

- **Secret redaction**: Automatic masking of sensitive values in logs
- **Validation**: Type checking prevents misconfiguration
- **Source priority**: Explicit precedence rules for conflicting values
- **Immutable settings**: Settings instance is frozen after initialization

## Getting Help

- **Usage Guide**: Setup instructions and integration patterns
- **Advanced Guide**: Custom sources and hot reload configuration
- **Troubleshooting**: Common configuration issues and solutions
- **Migration Guide**: Upgrading from previous versions

For issues and questions, visit our [GitHub repository](https://github.com/getrapidkit/core).
