# PostgreSQL Database Troubleshooting Guide

This guide helps you resolve common PostgreSQL database issues in your FastAPI applications using
the RapidKit PostgreSQL module.

## Connection Issues

### 1. Connection Refused

**Error**: `Connection refused` or `Can't connect to PostgreSQL server`

**Solutions**:

#### Check Database Server Status

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Or check process
ps aux | grep postgres

# Start PostgreSQL if stopped
sudo systemctl start postgresql
```

#### Verify Connection Parameters

```bash
# Check your DATABASE_URL format
DATABASE_URL=postgresql://user:password@localhost:5432/database_name

# Common mistakes:
# ❌ Wrong protocol: postgres:// (should be postgresql://)
# ❌ Missing port: postgresql://user:pass@localhost/db (should include :5432)
# ❌ Wrong host: postgresql://user:pass@wronghost:5432/db
```

#### Test Connection Manually

```bash
# Test with psql
psql -h localhost -p 5432 -U username -d database_name

# Test with python
python3 -c "
import asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://user:pass@localhost:5432/db')
    await conn.close()
    print('Connection successful')
import asyncio
asyncio.run(test())
"
```

### 2. Authentication Failed

**Error**: `FATAL: password authentication failed for user`

**Solutions**:

#### Check Password

```bash
# Reset password in psql
sudo -u postgres psql
ALTER USER username PASSWORD 'new_password';
```

#### Verify pg_hba.conf

```bash
# Check authentication configuration
sudo cat /etc/postgresql/12/main/pg_hba.conf

# Ensure you have appropriate authentication method
# local   all             username                                md5
# host    all             username        127.0.0.1/32            md5
```

#### Environment Variable Issues

```python
# Ensure DATABASE_URL is set correctly
import os

print(os.getenv("DATABASE_URL"))  # Should show your connection string

# Check for special characters in password (URL encode them)
# @ becomes %40, etc.
```

### 3. Database Does Not Exist

**Error**: `FATAL: database "database_name" does not exist`

**Solutions**:

#### Create Database

```bash
# Create database
sudo -u postgres createdb database_name

# Or in psql
sudo -u postgres psql
CREATE DATABASE database_name OWNER username;
```

#### Check Database Name in URL

```bash
# Ensure DATABASE_URL points to correct database
DATABASE_URL=postgresql://user:pass@localhost:5432/correct_db_name
```

## Pool Configuration Issues

### 1. Connection Pool Exhausted

**Error**: `TimeoutError: QueuePool limit of size 10 overflow 20 reached`

**Solutions**:

#### Increase Pool Size

```bash
# Environment variables
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
```

#### Monitor Pool Usage

```python
from modules.free.database.db_postgres.postgres import get_pool_status


@app.get("/debug/pool")
async def debug_pool():
    status = await get_pool_status()
    return status


# Check pool status regularly
# pool_size: 20
# checked_out: 18  # High usage
# overflow: 5      # Using overflow connections
```

#### Optimize Query Performance

```python
# ✅ Good: Use async queries
result = await db.execute(select(User).where(User.active == True))

# ❌ Bad: Blocking operations in async context
import time

time.sleep(1)  # Blocks event loop
```

### 2. Connection Timeout

**Error**: `TimeoutError: QueuePool timeout`

**Solutions**:

#### Increase Timeout

```bash
DB_POOL_TIMEOUT=60  # Increase from default 30 seconds
```

#### Check Database Performance

```sql
-- Check for slow queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Check locks
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query,
       blocking_activity.query AS blocking_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

## Transaction Issues

### 1. Transaction Deadlock

**Error**: `TransactionRollbackError: deadlock detected`

**Solutions**:

#### Handle Deadlocks Gracefully

```python
from sqlalchemy.exc import OperationalError
from asyncpg.exceptions import DeadlockDetectedError


async def safe_operation():
    async with transactional_async() as session:
        try:
            # Your operation
            await session.execute(...)
            await session.commit()
        except (OperationalError, DeadlockDetectedError) as e:
            if "deadlock" in str(e).lower():
                logger.warning("Deadlock detected, retrying...")
                raise  # Let transaction context manager handle rollback
            else:
                raise
```

#### Avoid Lock Contention

```python
# ✅ Good: Consistent ordering
users = await session.execute(
    select(User).where(User.id.in_([1, 2, 3])).order_by(User.id)
)

# ❌ Bad: Random ordering can cause deadlocks
users = await session.execute(
    select(User).where(User.id.in_([3, 1, 2]))  # Different order
)
```

### 2. Transaction Not Committing

**Error**: Changes not persisted to database

**Solutions**:

#### Check Transaction Scope

```python
# ✅ Correct: Changes committed
async with transactional_async() as session:
    user = User(name="John")
    session.add(user)
    # Transaction commits automatically

# ❌ Wrong: Session not flushed/committed
async for db in get_postgres_db():
    user = User(name="John")
    db.add(user)
    # No commit - changes lost when session closes
    break
```

#### Verify Autocommit Settings

```python
# Check session configuration
print(f"Autocommit: {session.autocommit}")
print(f"Autoflush: {session.autoflush}")
```

## Query Performance Issues

### 1. Slow Queries

**Symptoms**: Requests taking too long, timeouts

**Solutions**:

#### Add Database Indexes

```sql
-- Check slow queries
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
```

#### Optimize Queries

```python
# ✅ Good: Selective loading
result = await db.execute(select(User.id, User.name).where(User.active == True))

# ✅ Good: Use relationships efficiently
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(User).options(selectinload(User.posts)).where(User.id == user_id)
)

# ❌ Bad: Loading unnecessary data
result = await db.execute(select(User))  # Loads all columns
users = result.scalars().all()
for user in users:
    print(user.posts)  # N+1 query problem
```

### 2. Memory Issues

**Error**: `MemoryError` or high memory usage

**Solutions**:

#### Use Streaming for Large Result Sets

```python
# For large datasets, use server-side cursors
result = await db.stream(select(User))
async for user in result:
    process_user(user)  # Process one at a time
```

#### Limit Result Sets

```python
# Always limit results
result = await db.execute(select(User).limit(100).offset(page * 100))
```

## Health Check Issues

### 1. Health Check Failing

**Error**: Health endpoint returns 503

**Solutions**:

#### Debug Health Check

```python
# Test health check manually
from src.modules.free.database.db_postgres.postgres import (
    check_postgres_connection,
)

try:
    await check_postgres_connection()
    print("Health check passed")
except Exception as e:
    print(f"Health check failed: {e}")
```

#### Check Network Connectivity

```bash
# Test basic connectivity
telnet localhost 5432

# Test with pg_isready
pg_isready -h localhost -p 5432 -U username -d database_name
```

### 2. Pool Status Unavailable

**Error**: Pool status endpoint returns errors

**Solutions**:

#### Check Engine Initialization

```python
from src.modules.free.database.db_postgres.postgres import async_engine

print(f"Engine pool: {async_engine.pool}")
print(f"Pool size: {async_engine.pool.size()}")
```

## Migration Issues

### 1. Data Type Incompatibilities

**Problem**: Column types don't match between old and new database

**Solutions**:

#### Check Column Types

```sql
-- Compare schemas
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

#### Use Compatible Types

```python
# SQLAlchemy type mapping
from sqlalchemy import String, Integer, DateTime, Boolean


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # VARCHAR(100)
    email = Column(String(255), unique=True)  # VARCHAR(255)
    active = Column(Boolean, default=True)  # BOOLEAN
    created_at = Column(DateTime, default=datetime.utcnow)  # TIMESTAMP
```

### 2. Foreign Key Constraint Violations

**Error**: `Foreign key constraint violation`

**Solutions**:

#### Check Foreign Key Relationships

```sql
-- Find foreign key violations
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f';

-- Check for orphaned records
SELECT * FROM child_table
WHERE parent_id NOT IN (SELECT id FROM parent_table);
```

#### Handle Constraint Violations

```python
try:
    async with transactional_async() as session:
        # Your operation
        session.add(new_record)
        await session.commit()
except IntegrityError as e:
    if "foreign key" in str(e).lower():
        raise HTTPException(400, "Invalid reference")
    raise
```

## Testing Issues

### 1. Test Database Not Isolated

**Problem**: Tests affecting each other

**Solutions**:

#### Use Separate Test Database

```bash
# Set test database URL
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/myapp_test
```

#### Clean Between Tests

```python
@pytest.fixture(autouse=True)
async def clean_database():
    """Clean database between tests."""
    async with transactional_async() as session:
        # Delete test data
        await session.execute(text("DELETE FROM test_table"))
        await session.commit()
```

### 2. Async Test Issues

**Problem**: Async tests hanging or failing

**Solutions**:

#### Use Correct Test Markers

```python
@pytest.mark.asyncio
async def test_async_operation():
    async with get_postgres_db() as db:
        result = await db.execute(select(User))
        assert len(result.scalars().all()) >= 0
```

#### Handle Event Loop

```python
# For pytest-asyncio
@pytest.fixture
async def db_session():
    async for session in get_postgres_db():
        yield session
        break  # Only get one session
```

## Performance Monitoring

### Enable Query Logging

```python
# Enable SQL logging for debugging
DB_ECHO = true

# Or enable programmatically
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### Monitor Connection Usage

```python
# Add middleware to monitor database usage
@app.middleware("http")
async def db_monitor(request, call_next):
    start_time = time.time()

    # Count database operations (simplified)
    db_operations = 0

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"Request: {request.url} | DB ops: {db_operations} | Duration: {duration:.2f}s"
    )

    return response
```

## Getting Help

If you're still having issues:

1. Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-12-main.log`
1. Use `EXPLAIN ANALYZE` for query performance analysis
1. Monitor connection pool status regularly
1. Consider using a connection pool monitor like pg_stat_statements
1. Review the [usage guide](usage.md) for best practices

## Related Documentation

- [Usage Guide](usage.md) - Basic setup and configuration
- [Advanced Guide](advanced.md) - Complex scenarios and optimization
- [Migration Guide](migration.md) - Upgrading from other database solutions
