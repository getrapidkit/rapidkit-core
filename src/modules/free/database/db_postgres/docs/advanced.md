# PostgreSQL Database Advanced Configuration

This guide covers advanced PostgreSQL database scenarios, performance optimization, monitoring, and
complex integration patterns.

## Advanced Connection Management

### Custom Connection Factories

Create custom connection factories for specialized use cases:

```python
from sqlalchemy.pool import QueuePool
from src.modules.free.database.db_postgres.postgres import async_engine


class CustomPool(QueuePool):
    """Custom connection pool with enhanced monitoring."""

    def _do_get(self):
        """Override to add custom connection setup."""
        connection = super()._do_get()

        # Set custom connection parameters
        connection.execute("SET timezone = 'UTC'")
        connection.execute("SET work_mem = '64MB'")

        return connection

    def _do_return_conn(self, conn):
        """Override to add cleanup logic."""
        # Reset connection state
        try:
            conn.execute("RESET ALL")
        except Exception:
            pass  # Ignore cleanup errors

        super()._do_return_conn(conn)


# Apply custom pool class
async_engine.pool._pool = CustomPool(
    creator=async_engine.pool._creator, pool_size=10, max_overflow=20, recycle=3600
)
```

### Read/Write Connection Splitting

Implement read/write splitting for high-traffic applications:

```python
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseRouter:
    """Route database operations to appropriate connections."""

    def __init__(self, read_urls: list[str], write_url: str):
        self.read_engines = [
            create_async_engine(url.replace("postgresql://", "postgresql+asyncpg://"))
            for url in read_urls
        ]
        self.write_engine = create_async_engine(
            write_url.replace("postgresql://", "postgresql+asyncpg://")
        )

        self.read_sessions = [
            async_sessionmaker(bind=engine, expire_on_commit=False)
            for engine in self.read_engines
        ]
        self.write_session = async_sessionmaker(
            bind=self.write_engine, expire_on_commit=False
        )

    def get_read_session(self) -> AsyncSession:
        """Get a read-only session (round-robin)."""
        import random

        session_maker = random.choice(self.read_sessions)
        return session_maker()

    def get_write_session(self) -> AsyncSession:
        """Get a write session."""
        return self.write_session()

    def get_session(self, read_only: bool = False) -> AsyncSession:
        """Get appropriate session based on operation type."""
        if read_only:
            return self.get_read_session()
        return self.get_write_session()


# Usage in dependencies
router = DatabaseRouter(
    read_urls=["postgresql://read1:pass@host1/db", "postgresql://read2:pass@host2/db"],
    write_url="postgresql://write:pass@host3/db",
)


async def get_db(read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
    """Smart database dependency that routes based on operation."""
    session = router.get_session(read_only)
    try:
        yield session
    finally:
        await session.close()
```

## Advanced Transaction Patterns

### Saga Pattern Implementation

Implement complex distributed transactions using the Saga pattern:

```python
from typing import Callable, Any
from dataclasses import dataclass
from enum import Enum


class SagaStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"


@dataclass
class SagaStep:
    """A step in a saga transaction."""

    name: str
    execute: Callable[[AsyncSession], Any]
    compensate: Callable[[AsyncSession], Any]


class SagaOrchestrator:
    """Orchestrate saga transactions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.steps: list[SagaStep] = []
        self.completed_steps: list[SagaStep] = []

    def add_step(self, step: SagaStep):
        """Add a step to the saga."""
        self.steps.append(step)

    async def execute(self) -> bool:
        """Execute the saga, compensating on failure."""
        try:
            for step in self.steps:
                await step.execute(self.session)
                self.completed_steps.append(step)

            await self.session.commit()
            return True

        except Exception as e:
            # Compensate completed steps in reverse order
            for step in reversed(self.completed_steps):
                try:
                    await step.compensate(self.session)
                except Exception as comp_error:
                    logger.error(f"Compensation failed for {step.name}: {comp_error}")

            await self.session.rollback()
            return False


# Usage example
async def create_user_saga(user_data: dict):
    """Create user with email notification using saga pattern."""

    async with transactional_async() as session:
        saga = SagaOrchestrator(session)

        # Step 1: Create user
        async def create_user_step(sess):
            user = User(**user_data)
            sess.add(user)
            await sess.flush()
            return user.id

        async def compensate_user_step(sess):
            # Delete created user
            await sess.execute(delete(User).where(User.id == user_id))

        saga.add_step(SagaStep("create_user", create_user_step, compensate_user_step))

        # Step 2: Send welcome email
        async def send_email_step(sess):
            # Send email logic
            email_service.send_welcome_email(user_data["email"])

        async def compensate_email_step(sess):
            # Email compensation (maybe send cancellation email)
            pass

        saga.add_step(SagaStep("send_email", send_email_step, compensate_email_step))

        success = await saga.execute()
        return {"success": success}
```

### Optimistic Concurrency Control

Implement optimistic locking for concurrent data modifications:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.ext.asyncio import AsyncSession


class VersionedModel(Base):
    """Base model with version field for optimistic locking."""

    __abstract__ = True

    version = Column(Integer, default=1, nullable=False)


class Product(VersionedModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)
    version = Column(Integer, default=1)


async def update_product_price_optimistic(
    product_id: int, new_price: int, expected_version: int
):
    """Update product price with optimistic locking."""

    async with transactional_async() as session:
        # Fetch with current version
        result = await session.execute(
            select(Product)
            .where(Product.id == product_id, Product.version == expected_version)
            .with_for_update()
        )

        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(409, "Product was modified by another user")

        # Update with version increment
        product.price = new_price
        product.version += 1

        await session.commit()
        return product


# Usage with retry logic
async def update_price_with_retry(
    product_id: int, new_price: int, max_retries: int = 3
):
    """Update price with automatic retry on version conflicts."""

    for attempt in range(max_retries):
        try:
            # Get current version
            async with get_postgres_db() as db:
                result = await db.execute(
                    select(Product.version).where(Product.id == product_id)
                )
                current_version = result.scalar_one()

            # Attempt update
            return await update_product_price_optimistic(
                product_id, new_price, current_version
            )

        except HTTPException as e:
            if e.status_code == 409 and attempt < max_retries - 1:
                continue  # Retry
            raise
```

## Performance Optimization

### Query Result Streaming

Handle large result sets efficiently:

```python
from sqlalchemy import text
import asyncio


async def stream_large_dataset(query: str, batch_size: int = 1000):
    """Stream large query results in batches."""

    async with async_engine.connect() as conn:
        # Use server-side cursor for large datasets
        async with conn.execution_options(stream_results=True).execute(
            text(query)
        ) as result:

            batch = []
            async for row in result:
                batch.append(row)

                if len(batch) >= batch_size:
                    yield batch
                    batch = []
                    await asyncio.sleep(0)  # Allow other coroutines to run

            if batch:
                yield batch


# Usage
async def process_large_dataset():
    """Process large dataset without loading everything into memory."""

    query = "SELECT * FROM large_table WHERE created_at > '2023-01-01'"

    async for batch in stream_large_dataset(query, batch_size=500):
        # Process batch
        for row in batch:
            await process_row(row)

        # Optional: Add delay between batches to prevent overwhelming
        await asyncio.sleep(0.1)
```

### Connection Pool Monitoring

Advanced pool monitoring and alerting:

```python
import time
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PoolMetrics:
    """Connection pool metrics."""

    timestamp: float
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    recycle_count: int


class PoolMonitor:
    """Monitor connection pool health and performance."""

    def __init__(self, alert_threshold: float = 0.8):
        self.metrics: List[PoolMetrics] = []
        self.alert_threshold = alert_threshold
        self.last_alert_time = 0
        self.alert_cooldown = 300  # 5 minutes

    async def collect_metrics(self):
        """Collect current pool metrics."""
        status = await get_pool_status()

        metrics = PoolMetrics(
            timestamp=time.time(),
            pool_size=status["pool_size"],
            checked_in=status["checked_in"],
            checked_out=status["checked_out"],
            overflow=status["overflow"],
            invalid=0,  # Would need additional tracking
            recycle_count=0,  # Would need additional tracking
        )

        self.metrics.append(metrics)

        # Keep only last 1000 metrics
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]

        # Check for alerts
        await self.check_alerts(metrics)

    async def check_alerts(self, metrics: PoolMetrics):
        """Check if pool usage exceeds thresholds."""
        total_connections = metrics.checked_out + metrics.overflow
        utilization = total_connections / (metrics.pool_size + metrics.overflow)

        if utilization > self.alert_threshold:
            current_time = time.time()
            if current_time - self.last_alert_time > self.alert_cooldown:
                logger.warning(
                    f"High connection pool utilization: {utilization:.2%} "
                    f"({total_connections}/{metrics.pool_size + metrics.overflow})"
                )
                self.last_alert_time = current_time

    def get_metrics_summary(self) -> Dict:
        """Get summary of recent pool metrics."""
        if not self.metrics:
            return {}

        recent = self.metrics[-10:]  # Last 10 measurements

        return {
            "avg_utilization": sum(
                (m.checked_out + m.overflow) / (m.pool_size + m.overflow)
                for m in recent
            )
            / len(recent),
            "max_utilization": max(
                (m.checked_out + m.overflow) / (m.pool_size + m.overflow)
                for m in recent
            ),
            "current": self.metrics[-1].__dict__ if self.metrics else None,
        }


# Global monitor instance
pool_monitor = PoolMonitor()


# Add to health check
@app.get("/health/pool")
async def pool_health():
    """Extended health check with pool metrics."""
    await pool_monitor.collect_metrics()
    summary = pool_monitor.get_metrics_summary()

    if summary.get("avg_utilization", 0) > 0.9:
        return JSONResponse(
            status_code=503, content={"status": "degraded", "pool": summary}
        )

    return {"status": "healthy", "pool": summary}
```

## Advanced Health Checks

### Deep Health Validation

Comprehensive health checks beyond basic connectivity:

```python
from sqlalchemy import text
import time


async def comprehensive_health_check() -> Dict:
    """Perform comprehensive database health checks."""

    results = {"timestamp": time.time(), "checks": {}, "overall_status": "unknown"}

    async with async_engine.connect() as conn:
        try:
            # Basic connectivity
            start_time = time.time()
            await conn.execute(text("SELECT 1"))
            results["checks"]["connectivity"] = {
                "status": "pass",
                "duration_ms": (time.time() - start_time) * 1000,
            }

            # Connection pool status
            pool_status = await get_pool_status()
            pool_utilization = (
                pool_status["checked_out"] + pool_status["overflow"]
            ) / pool_status["pool_size"]

            results["checks"]["pool_health"] = {
                "status": "pass" if pool_utilization < 0.9 else "warn",
                "utilization": pool_utilization,
                "details": pool_status,
            }

            # Database size check
            db_size_result = await conn.execute(
                text(
                    """
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """
                )
            )
            db_size = db_size_result.scalar()
            results["checks"]["database_size"] = {"status": "info", "size": db_size}

            # Long-running queries check
            long_queries_result = await conn.execute(
                text(
                    """
                SELECT count(*) as long_queries
                FROM pg_stat_activity
                WHERE state = 'active'
                AND now() - query_start > interval '30 seconds'
            """
                )
            )
            long_queries = long_queries_result.scalar()

            results["checks"]["long_queries"] = {
                "status": "pass" if long_queries == 0 else "warn",
                "count": long_queries,
            }

            # Replication lag check (if replica)
            try:
                lag_result = await conn.execute(
                    text(
                        """
                    SELECT extract(epoch from now() - pg_last_xact_replay_timestamp()) as lag_seconds
                """
                    )
                )
                lag_seconds = lag_result.scalar()

                results["checks"]["replication_lag"] = {
                    "status": "pass" if lag_seconds < 60 else "warn",
                    "lag_seconds": lag_seconds,
                }
            except Exception:
                # Not a replica or no permissions
                results["checks"]["replication_lag"] = {
                    "status": "skip",
                    "reason": "not applicable",
                }

            # Overall status
            failed_checks = [
                k for k, v in results["checks"].items() if v.get("status") == "fail"
            ]
            warn_checks = [
                k for k, v in results["checks"].items() if v.get("status") == "warn"
            ]

            if failed_checks:
                results["overall_status"] = "fail"
            elif warn_checks:
                results["overall_status"] = "warn"
            else:
                results["overall_status"] = "pass"

        except Exception as e:
            results["checks"]["connectivity"] = {"status": "fail", "error": str(e)}
            results["overall_status"] = "fail"

    return results


# Enhanced health endpoint
@app.get("/health/comprehensive")
async def comprehensive_health():
    """Comprehensive database health check."""
    health = await comprehensive_health_check()

    status_code = {
        "pass": 200,
        "warn": 200,  # Still OK, but with warnings
        "fail": 503,
    }.get(health["overall_status"], 503)

    return JSONResponse(status_code=status_code, content=health)
```

## Database Migration Strategies

### Zero-Downtime Migrations

Implement zero-downtime database migrations:

```python
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import asyncio


class ZeroDowntimeMigrator:
    """Handle database migrations with zero downtime."""

    def __init__(self, alembic_config_path: str):
        self.config = Config(alembic_config_path)

    async def migrate_with_fallback(self, migration_script: str):
        """Perform migration with automatic rollback on failure."""

        # Create savepoint for rollback
        async with async_engine.connect() as conn:
            await conn.execute(text("SAVEPOINT migration_start"))

            try:
                # Run migration
                await self.run_migration_script(conn, migration_script)

                # Validate migration
                await self.validate_migration(conn)

                # Release savepoint (commit migration)
                await conn.execute(text("RELEASE SAVEPOINT migration_start"))

            except Exception as e:
                # Rollback to savepoint
                await conn.execute(text("ROLLBACK TO SAVEPOINT migration_start"))
                logger.error(f"Migration failed, rolled back: {e}")
                raise

    async def run_migration_script(self, conn, script: str):
        """Execute migration SQL script."""
        # Split script into individual statements
        statements = [s.strip() for s in script.split(";") if s.strip()]

        for statement in statements:
            if statement:
                await conn.execute(text(statement))

    async def validate_migration(self, conn):
        """Validate that migration was successful."""
        # Run validation queries
        validation_queries = [
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'new_table'",
            "SELECT COUNT(*) FROM new_table",  # Check if data is accessible
        ]

        for query in validation_queries:
            result = await conn.execute(text(query))
            count = result.scalar()
            if count is None:
                raise ValueError(f"Validation failed for query: {query}")


# Usage
migrator = ZeroDowntimeMigrator("alembic.ini")

migration_sql = """
ALTER TABLE users ADD COLUMN new_field VARCHAR(100) DEFAULT 'default_value';
CREATE INDEX CONCURRENTLY idx_users_new_field ON users(new_field);
"""

# Run with automatic rollback on failure
await migrator.migrate_with_fallback(migration_sql)
```

## Monitoring and Observability

### Custom Metrics Collection

Implement comprehensive database metrics:

```python
from prometheus_client import Counter, Histogram, Gauge
import psutil
import time

# Prometheus metrics
db_connections_active = Gauge(
    "db_connections_active", "Number of active database connections"
)
db_query_duration = Histogram(
    "db_query_duration_seconds", "Database query duration", ["query_type"]
)
db_errors_total = Counter("db_errors_total", "Total database errors", ["error_type"])


class DatabaseMetricsCollector:
    """Collect and expose database metrics."""

    def __init__(self):
        self.query_patterns = {
            "SELECT": "read",
            "INSERT": "write",
            "UPDATE": "write",
            "DELETE": "write",
        }

    async def collect_periodic_metrics(self):
        """Collect metrics periodically."""
        while True:
            try:
                # Connection pool metrics
                pool_status = await get_pool_status()
                db_connections_active.set(pool_status["checked_out"])

                # Database size metric (would need additional implementation)
                # db_size_gauge.set(get_database_size())

            except Exception as e:
                logger.error(f"Failed to collect metrics: {e}")

            await asyncio.sleep(60)  # Collect every minute

    def instrument_query(self, query: str):
        """Instrument a database query for metrics."""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = await func(*args, **kwargs)

                    # Record query duration
                    duration = time.time() - start_time
                    query_type = self._classify_query(query)
                    db_query_duration.labels(query_type=query_type).observe(duration)

                    return result

                except Exception as e:
                    # Record error
                    error_type = type(e).__name__
                    db_errors_total.labels(error_type=error_type).inc()
                    raise

            return wrapper

        return decorator

    def _classify_query(self, query: str) -> str:
        """Classify query type for metrics."""
        query_upper = query.upper().strip()
        for keyword, query_type in self.query_patterns.items():
            if query_upper.startswith(keyword):
                return query_type
        return "other"


# Usage
metrics_collector = MetricsCollector()


# Instrument specific queries
@metrics_collector.instrument_query("SELECT * FROM users")
async def get_all_users():
    async with get_postgres_db() as db:
        result = await db.execute(select(User))
        return result.scalars().all()


# Start metrics collection
asyncio.create_task(metrics_collector.collect_periodic_metrics())
```

## Security Hardening

### Query Parameterization

Ensure all queries use proper parameterization:

```python
# ✅ Secure: Use parameterized queries
async def get_user_by_id(user_id: int):
    async with get_postgres_db() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


# ❌ Insecure: String interpolation
async def get_user_bad(user_id: str):
    async with get_postgres_db() as db:
        # NEVER DO THIS - SQL injection vulnerability
        result = await db.execute(text(f"SELECT * FROM users WHERE id = {user_id}"))
        return result.fetchone()
```

### Connection Encryption

Ensure connections use SSL/TLS:

```python
# Force SSL connections
ssl_config = {
    "ssl": True,
    "ssl_ca_certs": "/path/to/ca-cert.pem",
    "ssl_cert_reqs": ssl.CERT_REQUIRED,
}

async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    connect_args=ssl_config,
)

sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://"),
    connect_args=ssl_config,
)
```

## Related Documentation

- [Usage Guide](usage.md) - Basic setup and configuration
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Migration Guide](migration.md) - Upgrading from other database solutions
