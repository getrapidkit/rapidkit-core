# Connection Pooling Examples

This document demonstrates connection pooling patterns and optimization techniques with the
PostgreSQL module.

## Basic Pool Configuration

```bash
# Environment variables for pool configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myapp
DB_POOL_SIZE=20          # Base pool size
DB_MAX_OVERFLOW=50       # Additional connections when pool is full
DB_POOL_RECYCLE=1800     # Recycle connections after 30 minutes
DB_POOL_PRE_PING=true    # Health check connections before use
DB_ECHO=false           # Disable SQL logging in production
```

## Pool Size Optimization

### Calculating Optimal Pool Size

```python
import math


def calculate_pool_size():
    """
    Calculate optimal pool size based on server resources
    Rule of thumb: pool_size = (cores * 2) + disk_count
    """

    # Server specifications
    cpu_cores = 8
    disk_count = 2

    # Base calculation
    base_pool_size = (cpu_cores * 2) + disk_count  # 18

    # Adjust for application type
    # Web applications: higher pool size
    # Batch processing: lower pool size
    application_multiplier = 1.5  # For web apps

    optimal_pool_size = math.ceil(base_pool_size * application_multiplier)

    return optimal_pool_size


# Example configuration
POOL_SIZE = calculate_pool_size()  # 27
MAX_OVERFLOW = POOL_SIZE * 2  # 54 for burst traffic
```

## Connection Pool Monitoring

### Real-time Pool Statistics

```python
import logging

from modules.free.database.db_postgres.postgres import async_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def log_pool_stats():
    """Log current connection pool statistics"""

    # Get pool statistics
    pool = async_engine.pool

    stats = {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }

    logger.info(f"Pool stats: {stats}")

    # Log PostgreSQL connection count
    async with async_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT
                count(*) as total_connections,
                count(*) filter (where state = 'active') as active_connections,
                count(*) filter (where state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))

        pg_stats = result.first()
        logger.info(f"PostgreSQL connections: {dict(pg_stats)}")


# Usage in health check
@app.get("/health/pool")
async def pool_health():
    await log_pool_stats()

    pool = async_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "utilization_percent": (pool.checkedout() / pool.size()) * 100,
    }
```

## Connection Health Checks

### Pre-ping Configuration

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# Enable pre-ping to test connections before use
async_engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connection health on checkout
    pool_recycle=1800,  # Recycle connections every 30 minutes
    echo=False,
)

sync_engine = create_engine(
    DATABASE_URL.replace("+asyncpg", "+psycopg2"),
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)
```

### Custom Health Check Function

```python
import asyncio
from sqlalchemy.exc import DisconnectionError


async def check_connection_health(conn) -> bool:
    """Custom connection health check"""

    try:
        # Simple query to test connection
        await conn.execute(text("SELECT 1"))

        # More thorough check
        result = await conn.execute(text("SELECT pg_is_in_recovery()"))
        is_replica = result.scalar()

        if is_replica:
            logger.warning("Connected to read-only replica")

        return True

    except DisconnectionError:
        logger.error("Connection health check failed")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in health check: {e}")
        return False


# Usage with connection event listeners
from sqlalchemy import event


@event.listens_for(async_engine, "connect")
def connect(dbapi_connection, connection_record):
    """Handle new connections"""
    logger.info("New database connection established")


@event.listens_for(async_engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    """Handle connection checkout from pool"""
    logger.debug("Connection checked out from pool")


@event.listens_for(async_engine, "checkin")
def checkin(dbapi_connection, connection_record):
    """Handle connection checkin to pool"""
    logger.debug("Connection returned to pool")
```

## Pool Overflow Handling

### Graceful Degradation

```python
from sqlalchemy.exc import TimeoutError as SATimeoutError
from fastapi import HTTPException


class PoolExhaustionError(Exception):
    pass


async def execute_with_pool_protection(db_operation, timeout: float = 5.0):
    """
    Execute operation with pool exhaustion protection
    """

    try:
        # Set statement timeout to prevent long-running queries
        await db.execute(text(f"SET statement_timeout = {int(timeout * 1000)}"))

        return await asyncio.wait_for(db_operation(), timeout=timeout)

    except asyncio.TimeoutError:
        logger.error("Query timeout - possible pool exhaustion")
        raise PoolExhaustionError("Database operation timeout")

    except SATimeoutError:
        logger.error("Connection pool timeout")
        raise PoolExhaustionError("Connection pool exhausted")


# Usage in endpoint
@app.get("/protected-data")
async def get_protected_data(db: AsyncSession = Depends(get_postgres_db)):
    try:

        async def fetch_data():
            result = await db.execute(select(User).limit(100))
            return result.scalars().all()

        users = await execute_with_pool_protection(fetch_data, timeout=3.0)
        return {"users": users}

    except PoolExhaustionError:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable - database pool exhausted",
        )
```

## Connection Pool Tuning

### Production Configuration

```python
# production_settings.py
from pydantic import BaseSettings, validator


class DatabasePoolSettings(BaseSettings):
    database_url: str

    # Pool sizing
    pool_size: int = 20
    max_overflow: int = 50
    pool_timeout: float = 30.0  # Seconds to wait for connection

    # Connection lifecycle
    pool_recycle: int = 1800  # 30 minutes
    pool_pre_ping: bool = True

    # Connection validation
    connect_args: dict = {}

    @validator("connect_args", pre=True, always=True)
    def set_connect_args(cls, v):
        # Set connection validation parameters
        return {
            **v,
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }

    class Config:
        env_file = ".env"


# Create engines with optimized settings
db_settings = DatabasePoolSettings()

async_engine = create_async_engine(
    db_settings.database_url,
    pool_size=db_settings.pool_size,
    max_overflow=db_settings.max_overflow,
    pool_timeout=db_settings.pool_timeout,
    pool_recycle=db_settings.pool_recycle,
    pool_pre_ping=db_settings.pool_pre_ping,
    connect_args=db_settings.connect_args,
    echo=False,
)
```

## Read/Write Splitting

### Connection Pool for Read Replicas

```python
from typing import Literal


class DatabaseManager:
    def __init__(self):
        # Write connection (master)
        self.write_engine = create_async_engine(
            "postgresql+asyncpg://user:pass@master:5432/db",
            pool_size=10,
            max_overflow=20,
        )

        # Read connections (replicas)
        self.read_engines = [
            create_async_engine(
                "postgresql+asyncpg://user:pass@replica1:5432/db",
                pool_size=15,
                max_overflow=30,
            ),
            create_async_engine(
                "postgresql+asyncpg://user:pass@replica2:5432/db",
                pool_size=15,
                max_overflow=30,
            ),
        ]

    def get_engine(self, operation: Literal["read", "write"]):
        """Get appropriate engine for operation type"""

        if operation == "write":
            return self.write_engine

        # Round-robin load balancing for reads
        import random

        return random.choice(self.read_engines)


# Usage in dependencies
async def get_write_db():
    """Dependency for write operations"""
    async for session in get_session(db_manager.get_engine("write")):
        yield session


async def get_read_db():
    """Dependency for read operations"""
    async for session in get_session(db_manager.get_engine("read")):
        yield session


# FastAPI routes
@app.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_write_db)):
    # Write operation
    db_user = User(**user.dict())
    db.add(db_user)
    await db.commit()
    return db_user


@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_read_db)):
    # Read operation
    result = await db.execute(select(User))
    return result.scalars().all()
```

## Connection Pool Metrics

### Prometheus Metrics Collection

```python
from prometheus_client import Gauge, Counter, Histogram
import time

# Pool metrics
pool_size_gauge = Gauge("db_pool_size", "Current pool size")
pool_checked_out_gauge = Gauge(
    "db_pool_checked_out", "Connections currently checked out"
)
pool_overflow_gauge = Gauge("db_pool_overflow", "Current overflow connections")

# Connection metrics
connection_created_counter = Counter(
    "db_connections_created_total", "Total connections created"
)
connection_closed_counter = Counter(
    "db_connections_closed_total", "Total connections closed"
)

# Query metrics
query_duration_histogram = Histogram(
    "db_query_duration_seconds",
    "Query execution time",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)


# Update metrics function
def update_pool_metrics():
    """Update Prometheus metrics with current pool state"""

    pool = async_engine.pool

    pool_size_gauge.set(pool.size())
    pool_checked_out_gauge.set(pool.checkedout())
    pool_overflow_gauge.set(pool.overflow())


# Usage in background task
async def metrics_updater():
    """Background task to update metrics"""

    while True:
        update_pool_metrics()
        await asyncio.sleep(10)  # Update every 10 seconds


# Middleware for query metrics
@app.middleware("http")
async def db_metrics_middleware(request, call_next):
    if request.url.path.startswith("/api/"):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        query_duration_histogram.observe(duration)

        return response

    return await call_next(request)
```

## Connection Pool Testing

### Load Testing Pool Behavior

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor


async def load_test_pool(concurrent_requests: int = 100):
    """Load test connection pool under concurrent load"""

    async def make_request(session_id: int):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "http://localhost:8000/api/users",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    return response.status
            except Exception as e:
                logger.error(f"Request {session_id} failed: {e}")
                return None

    # Execute concurrent requests
    tasks = [make_request(i) for i in range(concurrent_requests)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analyze results
    successful = sum(1 for r in results if r == 200)
    failed = sum(1 for r in results if r is None or isinstance(r, Exception))

    logger.info(f"Load test results: {successful} successful, {failed} failed")

    # Check pool state after load
    await log_pool_stats()


# Usage
@app.post("/load-test")
async def run_load_test():
    await load_test_pool(200)  # Test with 200 concurrent requests
    return {"message": "Load test completed"}
```

## Best Practices

### 1. Right-size Your Pool

```python
# Calculate based on your application needs
def optimal_pool_config(requests_per_second: int, avg_query_time: float):
    """
    Calculate pool size based on expected load

    Args:
        requests_per_second: Expected RPS
        avg_query_time: Average query time in seconds
    """

    # Connections needed = RPS * avg_query_time
    concurrent_connections = requests_per_second * avg_query_time

    # Add buffer for variability
    pool_size = math.ceil(concurrent_connections * 1.2)

    # Cap at reasonable limits
    pool_size = min(pool_size, 100)  # Max 100 connections
    pool_size = max(pool_size, 5)  # Min 5 connections

    return {"pool_size": pool_size, "max_overflow": pool_size * 2, "pool_timeout": 30.0}
```

### 2. Monitor Pool Health

```python
async def pool_health_check():
    """Comprehensive pool health check"""

    pool = async_engine.pool
    issues = []

    # Check pool utilization
    utilization = pool.checkedout() / pool.size()
    if utilization > 0.8:
        issues.append(f"High pool utilization: {utilization:.1%}")

    # Check overflow
    if pool.overflow() > pool.size() * 0.5:
        issues.append(f"High overflow: {pool.overflow()} connections")

    # Check PostgreSQL connection count
    async with async_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT count(*) as connection_count
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))

        pg_connections = result.scalar()
        if pg_connections > pool.size() * 2:
            issues.append(f"Too many PostgreSQL connections: {pg_connections}")

    return {
        "healthy": len(issues) == 0,
        "issues": issues,
        "pool_stats": {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        },
    }
```

### 3. Handle Pool Exhaustion Gracefully

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class PoolProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware to protect against pool exhaustion"""

    def __init__(self, app, max_concurrent_requests: int = 1000):
        super().__init__(app)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    async def dispatch(self, request: Request, call_next):
        # Limit concurrent requests
        async with self.semaphore:
            # Check pool state
            pool = async_engine.pool
            utilization = pool.checkedout() / pool.size()

            if utilization > 0.95:
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service temporarily unavailable"},
                )

            response = await call_next(request)
            return response
```

### 4. Implement Circuit Breaker

```python
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class DatabaseCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = CircuitState.CLOSED

    async def call(self, db_operation):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise PoolExhaustionError("Circuit breaker is OPEN")

        try:
            result = await db_operation()
            self.on_success()
            return result

        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


# Usage
circuit_breaker = DatabaseCircuitBreaker()


async def safe_db_operation():
    async def operation():
        async with get_postgres_db() as db:
            result = await db.execute(select(User).limit(10))
            return result.scalars().all()

    return await circuit_breaker.call(operation)
```
