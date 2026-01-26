# PostgreSQL Database Module API Reference

This document provides comprehensive API reference for the PostgreSQL database module.

## Core Classes

### DatabasePostgres

Main database module class that manages PostgreSQL connections and provides access to engines and
sessions.

#### Methods

##### `get_postgres_db() -> AsyncSession`

FastAPI dependency that provides an async database session.

**Returns:** `AsyncSession` - SQLAlchemy async session

**Usage:**

```python
from src.modules.free.database.db_postgres.postgres import get_postgres_db


@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    # Use db session here
    pass
```

##### `get_sync_db() -> Session`

FastAPI dependency that provides a synchronous database session.

**Returns:** `Session` - SQLAlchemy sync session

**Usage:**

```python
from src.modules.free.database.db_postgres.postgres import get_sync_db


@app.get("/legacy")
def get_legacy_data(db: Session = Depends(get_sync_db)):
    # Use sync db session here
    pass
```

##### `transactional_async(func) -> Callable`

Decorator for async functions that provides transaction management.

**Parameters:**

- `func` - Async function to wrap with transaction

**Returns:** Decorated function with automatic transaction handling

**Usage:**

```python
@transactional_async
async def create_user(user_data: dict):
    user = User(**user_data)
    db.add(user)
    await db.commit()
    return user
```

##### `transactional_sync(func) -> Callable`

Decorator for sync functions that provides transaction management.

**Parameters:**

- `func` - Sync function to wrap with transaction

**Returns:** Decorated function with automatic transaction handling

**Usage:**

```python
@transactional_sync
def create_user_sync(user_data: dict):
    user = User(**user_data)
    db.add(user)
    db.commit()
    return user
```

## Database Engines

### async_engine

SQLAlchemy async engine configured for PostgreSQL.

**Type:** `AsyncEngine`

**Configuration:**

- Uses asyncpg driver
- Connection pooling enabled
- SSL support
- Health monitoring

### sync_engine

SQLAlchemy sync engine configured for PostgreSQL.

**Type:** `Engine`

**Configuration:**

- Uses psycopg2 driver
- Connection pooling enabled
- SSL support
- Health monitoring

## Session Factories

### AsyncSessionLocal

SQLAlchemy async session factory.

**Type:** `async_sessionmaker[AsyncSession]`

### SessionLocal

SQLAlchemy sync session factory.

**Type:** `sessionmaker[Session]`

## Base Classes

### Base

SQLAlchemy declarative base for model definitions.

**Type:** `DeclarativeBase`

**Usage:**

```python
from src.modules.free.database.db_postgres.postgres import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255))
```

## Health Check Classes

### PostgresHealthCheck

Health check class for PostgreSQL database connectivity.

#### Health Check Methods

##### `check_connectivity() -> HealthStatus`

Checks basic database connectivity.

**Returns:** `HealthStatus` - Health check result

##### `check_pool_status() -> HealthStatus`

Checks connection pool status and metrics.

**Returns:** `HealthStatus` - Pool health status

##### `check_performance() -> HealthStatus`

Checks query performance and response times.

**Returns:** `HealthStatus` - Performance health status

## Configuration Classes

### DatabaseSettings

Pydantic settings class for database configuration.

#### Attributes

- `database_url: str` - PostgreSQL connection URL
- `pool_size: int` - Connection pool size (default: 20)
- `max_overflow: int` - Maximum overflow connections (default: 50)
- `pool_recycle: int` - Connection recycle time in seconds (default: 1800)
- `pool_pre_ping: bool` - Enable connection health checks (default: True)
- `echo: bool` - Enable SQL logging (default: False)

## Exception Classes

### DatabaseConnectionError

Raised when database connection fails.

**Inherits from:** `Exception`

### PoolExhaustedError

Raised when connection pool is exhausted.

**Inherits from:** `DatabaseConnectionError`

### TransactionError

Raised when transaction operations fail.

**Inherits from:** `Exception`

## Utility Functions

### create_database_url()

Creates database URL from individual components.

**Parameters:**

- `host: str` - Database host
- `port: int` - Database port
- `database: str` - Database name
- `username: str` - Database username
- `password: str` - Database password
- `ssl_mode: str` - SSL mode (default: "require")

**Returns:** `str` - Complete database URL

### get_engine_health(engine) -> dict

Gets health metrics for a database engine.

**Parameters:**

- `engine` - SQLAlchemy engine instance

**Returns:** `dict` - Health metrics dictionary

### validate_connection(url: str) -> bool

Validates database connection URL format.

**Parameters:**

- `url: str` - Database connection URL

**Returns:** `bool` - True if URL is valid

## FastAPI Integration

### Dependency Injection

The module provides FastAPI dependencies for seamless integration:

```python
from fastapi import APIRouter, Depends
from src.modules.free.database.db_postgres.postgres import get_postgres_db

router = APIRouter()


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_postgres_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

### Health Endpoints

Built-in health check endpoints:

```python
from src.health.postgres import router as health_router

app.include_router(health_router, prefix="/api/health")
```

Available endpoints:

- `GET /api/health/module/postgres` - Overall database health
- `GET /api/health/module/postgres/connectivity` - Connection check
- `GET /api/health/module/postgres/pool` - Pool status
- `GET /api/health/module/postgres/performance` - Performance metrics

## NestJS Integration

### DatabasePostgresService

NestJS service class for PostgreSQL operations.

#### Service Methods

##### `getConnection() -> Connection`

Gets a database connection from the pool.

##### `executeQuery(query: string, params?: any[]) -> Promise<any[]>`

Executes a raw SQL query.

##### `transaction<T>(callback: (connection: Connection) => Promise<T>) -> Promise<T>`

Executes operations within a transaction.

## Migration Tools

### Alembic Integration

The module provides Alembic configuration for migrations:

```python
# alembic/env.py
from src.modules.free.database.db_postgres.postgres import Base

target_metadata = Base.metadata
```

### Migration Commands

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Run migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring and Metrics

### Prometheus Metrics

The module exposes Prometheus-compatible metrics:

- `postgres_connections_active` - Active connections
- `postgres_connections_idle` - Idle connections
- `postgres_pool_size` - Pool size
- `postgres_query_duration_seconds` - Query execution time
- `postgres_transactions_total` - Transaction count

### Logging

Structured logging for database operations:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "module": "database.postgres",
  "operation": "query",
  "duration_ms": 150,
  "query": "SELECT * FROM users WHERE id = $1",
  "parameters": [123]
}
```

## Error Handling

### Connection Errors

```python
from src.modules.free.database.db_postgres.postgres import (
    DatabaseConnectionError,
)

try:
    # Database operation
    pass
except DatabaseConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    # Handle connection error
```

### Transaction Errors

```python
from src.modules.free.database.db_postgres.postgres import (
    TransactionError,
)

try:
    # Transaction operation
    pass
except TransactionError as e:
    logger.error(f"Transaction failed: {e}")
    # Handle transaction error
```

## Type Hints

The module provides comprehensive type hints:

```python
from typing import TYPE_CHECKING
from src.modules.free.database.db_postgres.postgres import (
    AsyncSession,
    Session,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as AsyncSessionType
    from sqlalchemy.orm import Session as SessionType
```

## Constants

### DEFAULT_POOL_SIZE = 20

Default connection pool size.

### DEFAULT_MAX_OVERFLOW = 50

Default maximum overflow connections.

### DEFAULT_POOL_RECYCLE = 1800

Default connection recycle time in seconds.

### POSTGRES_DRIVER_ASYNC = "asyncpg"

Async PostgreSQL driver name.

### POSTGRES_DRIVER_SYNC = "psycopg2"

Sync PostgreSQL driver name.
