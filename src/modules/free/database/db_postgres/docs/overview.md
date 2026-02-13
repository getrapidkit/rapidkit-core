# PostgreSQL Database Module Overview

The PostgreSQL module provides production-ready database integration for RapidKit applications,
featuring async/sync SQLAlchemy engines, connection pooling, transaction management, and
comprehensive health monitoring.

## Key Features

- **Dual Engine Support**: Both async (asyncpg) and sync (psycopg2) database engines
- **Connection Pooling**: Configurable connection pools with health monitoring
- **Transaction Management**: Context managers for safe transaction handling
- **FastAPI Integration**: Dependency injection patterns for seamless API development
- **Health Checks**: Built-in database connectivity and performance monitoring
- **Migration Support**: Alembic integration for schema versioning
- **Type Safety**: Full SQLAlchemy 2.0 ORM support with type hints

## Architecture

The module follows a layered architecture:

```
┌─────────────────┐
│   FastAPI App   │
│  Dependencies   │
└─────────────────┘
         │
    ┌────────────┐
    │  Sessions  │ ← Dependency injection
    └────────────┘
         │
    ┌────────────┐
    │   Engines  │ ← Connection pooling
    └────────────┘
         │
    ┌────────────┐
    │ PostgreSQL │ ← Database server
    └────────────┘
```

## Quick Start

```
python
from fastapi import FastAPI, Depends
from src.modules.free.database.db_postgres.postgres import get_postgres_db, Base
from sqlalchemy import select

app = FastAPI()

# Define models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Use in routes
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

## Module Components

- **Database Engines**: Async and sync SQLAlchemy engines with connection pooling
- **Session Management**: Dependency injection for database sessions
- **Transaction Context**: Safe transaction handling with automatic rollback
- **Health Monitoring**: Database connectivity and performance checks
- **Migration Tools**: Schema versioning and database migrations

## Supported Frameworks

- **FastAPI**: Full dependency injection and health check integration
- **NestJS**: Service-based architecture with TypeScript support
- **Custom**: Direct engine/session access for other frameworks

## Configuration

The module is configured via environment variables:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
DB_POOL_RECYCLE=1800
```

## Health Checks

Built-in health endpoints monitor:

- Database connectivity
- Connection pool status
- Query performance
- Transaction health

Access health status at `/api/health/module/postgres`.

## Performance Features

- **Connection Pooling**: Efficient connection reuse
- **Async Operations**: Non-blocking database operations
- **Query Optimization**: Built-in query performance monitoring
- **Transaction Batching**: Efficient bulk operations

## Security

- **Connection Encryption**: SSL/TLS support
- **Credential Management**: Secure credential handling
- **Query Sanitization**: Safe query building with SQLAlchemy
- **Access Control**: Configurable database permissions

## Monitoring & Observability

- **Metrics Collection**: Prometheus-compatible metrics
- **Logging**: Structured logging for database operations
- **Tracing**: Request tracing through database calls
- **Alerting**: Configurable alerts for database issues

## Migration & Compatibility

The module supports migration from:

- Raw SQLAlchemy setups
- Tortoise ORM
- Django ORM
- Peewee ORM
- Raw psycopg2
- Other database systems

See the migration guide for detailed migration instructions.

## Getting Help

- **Usage Guide**: Basic setup and common patterns
- **Troubleshooting**: Common issues and solutions
- **Advanced Guide**: Complex patterns and optimization
- **Migration Guide**: Migrating from other database solutions

For issues and questions, visit our
[GitHub repository](https://github.com/getrapidkit/rapidkit-core).
