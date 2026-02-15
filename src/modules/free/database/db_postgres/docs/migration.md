# PostgreSQL Database Migration Guide

This guide helps you migrate from other database solutions or older PostgreSQL setups to the
RapidKit PostgreSQL module.

## Migrating from Raw SQLAlchemy

### Before: Manual SQLAlchemy Setup

```python
# Old manual setup (in multiple files)
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Database configuration scattered across files
DATABASE_URL = "postgresql://user:pass@localhost/db"

# Engines created manually
engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)

# Session factories
SessionLocal = sessionmaker(bind=engine)
AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession)


# Dependencies defined manually
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async_db = AsyncSessionLocal()
    try:
        yield async_db
    finally:
        await async_db.close()


# Base model
Base = declarative_base()
```

### After: RapidKit PostgreSQL Module

```python
# New setup with RapidKit module
from src.modules.free.database.db_postgres.postgres import (
    get_postgres_db,  # Async dependency
    get_sync_db,  # Sync dependency
    Base,  # SQLAlchemy base
    transactional_async,
    transactional_sync,
)

# All configuration centralized in settings
# DATABASE_URL configured via environment variables


# Usage in routes (same dependency injection pattern)
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


@app.get("/legacy")
def get_legacy_data(db: Session = Depends(get_sync_db)):
    return db.execute(text("SELECT * FROM legacy_table")).all()
```

### Key Changes

| Aspect                 | Before                          | After                 |
| ---------------------- | ------------------------------- | --------------------- |
| Engine Creation        | Manual in multiple places       | Centralized in module |
| Session Management     | Manual session creation/cleanup | Dependency injection  |
| Configuration          | Scattered environment variables | Centralized settings  |
| Health Checks          | Manual implementation           | Built-in endpoints    |
| Transaction Management | Manual try/finally blocks       | Context managers      |

## Migrating from Tortoise ORM

### Tortoise ORM Setup

```python
# Tortoise ORM configuration
from tortoise import Tortoise, fields
from tortoise.models import Model


# Model definition
class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)

    class Meta:
        table = "users"


# Initialization
await Tortoise.init(
    db_url="postgres://user:pass@localhost/db", modules={"models": ["myapp.models"]}
)

# Usage
users = await User.all()
user = await User.create(name="John", email="john@example.com")
```

### Migrated RapidKit Setup

```python
# SQLAlchemy models (generated or manual)
from sqlalchemy import Column, Integer, String
from src.modules.free.database.db_postgres.postgres import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True)


# Usage with RapidKit
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@app.post("/users")
async def create_user(user_data: dict):
    async with transactional_async() as session:
        user = User(**user_data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
```

### Tortoise to SQLAlchemy Mapping

| Tortoise ORM                          | SQLAlchemy                                  | Notes                   |
| ------------------------------------- | ------------------------------------------- | ----------------------- |
| `fields.IntField(pk=True)`            | `Column(Integer, primary_key=True)`         | Same functionality      |
| `fields.CharField(max_length=100)`    | `Column(String(100))`                       | Same functionality      |
| `fields.DatetimeField(auto_now=True)` | `Column(DateTime, default=datetime.utcnow)` | Use SQLAlchemy defaults |
| `User.all()`                          | `select(User)`                              | Use SQLAlchemy select   |
| `User.filter(name="John")`            | `select(User).where(User.name == "John")`   | Use where clauses       |
| `User.create(**data)`                 | `session.add(Model(**data))`                | Add to session          |
| `await user.save()`                   | `await session.commit()`                    | Commit transaction      |

## Migrating from Django ORM

### Django Model Setup

```python
# Django models.py
from django.db import models


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "myapp"


# Django settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "myapp",
        "USER": "user",
        "PASSWORD": "pass",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# Usage in views
def user_list(request):
    users = User.objects.all()
    return render(request, "users.html", {"users": users})
```

### Migrated Django Setup

```python
# SQLAlchemy models
from sqlalchemy import Column, Integer, String, DateTime
from src.modules.free.database.db_postgres.postgres import Base
import datetime


class User(Base):
    __tablename__ = "myapp_user"  # Django table naming

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# FastAPI view
@app.get("/users")
async def user_list(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"users": users}
```

### Django to SQLAlchemy Mapping

| Django ORM                                | SQLAlchemy                                  | Notes                      |
| ----------------------------------------- | ------------------------------------------- | -------------------------- |
| `models.CharField(max_length=100)`        | `Column(String(100))`                       | Same functionality         |
| `models.EmailField()`                     | `Column(String(255))`                       | Use string with validation |
| `models.DateTimeField(auto_now_add=True)` | `Column(DateTime, default=datetime.utcnow)` | Use default                |
| `models.ForeignKey(Model)`                | `Column(Integer, ForeignKey('model.id'))`   | Explicit foreign keys      |
| `User.objects.all()`                      | `select(User)`                              | Use select                 |
| `User.objects.filter(name="John")`        | `select(User).where(User.name == "John")`   | Use where                  |
| `User.objects.create(**data)`             | `session.add(User(**data))`                 | Add to session             |

## Migrating from Peewee ORM

### Peewee Setup

```python
# Peewee models
from peewee import Model, CharField, PostgresqlDatabase

db = PostgresqlDatabase("myapp", user="user", password="pass", host="localhost")


class User(Model):
    name = CharField()
    email = CharField(unique=True)

    class Meta:
        database = db


# Usage
db.connect()
users = User.select()
user = User.create(name="John", email="john@example.com")
```

### Migrated Peewee Setup

```python
# SQLAlchemy models
from sqlalchemy import Column, String
from src.modules.free.database.db_postgres.postgres import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(255), unique=True)


# Usage
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
```

## Migrating from Raw psycopg2

### Raw psycopg2 Usage

```python
import psycopg2

# Manual connection management
conn = psycopg2.connect(
    host="localhost", database="myapp", user="user", password="pass"
)

# Manual cursor management
cur = conn.cursor()
cur.execute("SELECT * FROM users")
users = cur.fetchall()
cur.close()
conn.close()
```

### Equivalent RapidKit Setup

```python
# SQLAlchemy with connection pooling
from src.modules.free.database.db_postgres.postgres import get_postgres_db


@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(text("SELECT * FROM users"))
    users = result.fetchall()
    return {"users": users}


# Or with ORM
result = await db.execute(select(User))
users = result.scalars().all()
```

### Key Improvements

| Raw psycopg2        | RapidKit PostgreSQL | Benefits           |
| ------------------- | ------------------- | ------------------ |
| Manual connections  | Connection pooling  | Better performance |
| Manual cursors      | Session management  | Automatic cleanup  |
| Manual transactions | Context managers    | Safer transactions |
| Raw SQL only        | ORM + Raw SQL       | Flexibility        |
| No async support    | Full async support  | Better concurrency |

## Migrating from Other Database Systems

### From MySQL

```python
# MySQL SQLAlchemy setup
from sqlalchemy import create_engine

engine = create_engine("mysql+pymysql://user:pass@localhost/db")

# PostgreSQL equivalent
from src.modules.free.database.db_postgres.postgres import async_engine

# Use PostgreSQL-specific features
async with async_engine.connect() as conn:
    # PostgreSQL JSON operations
    await conn.execute(text("SELECT data->>'key' FROM json_table"))

    # PostgreSQL arrays
    await conn.execute(text("SELECT * FROM table WHERE id = ANY($1)"), [[1, 2, 3]])
```

### From SQLite

```python
# SQLite setup (development)
engine = create_engine("sqlite:///dev.db")

# PostgreSQL setup (production)
# Use environment variables to switch
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")

# RapidKit handles both seamlessly
# Just change the DATABASE_URL environment variable
```

## Database Schema Migration

### Using Alembic with RapidKit

```python
# alembic/env.py
from src.modules.free.database.db_postgres.postgres import Base
from my_app.models import User, Post  # Your models

# Import all models for autogeneration
target_metadata = Base.metadata

# Use RapidKit engine for migrations
from src.modules.free.database.db_postgres.postgres import async_engine

config.set_main_option("sqlalchemy.url", str(async_engine.url).replace("+asyncpg", ""))
```

### Migration Workflow

1. **Generate migration**:

   ```bash
   alembic revision --autogenerate -m "Add new table"
   ```

1. **Review and edit** the generated migration file

1. **Run migration**:

   ```bash
   alembic upgrade head
   ```

1. **Verify** with health checks:

   ```bash
   curl http://localhost:8000/api/health/module/postgres
   ```

## Testing Migration

### Update Test Configuration

```python
# Before: Direct database setup in tests
@pytest.fixture
def db_session():
    engine = create_engine("postgresql://test:test@localhost/test_db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# After: Use RapidKit test database
from src.modules.free.database.db_postgres.postgres import get_postgres_db


@pytest.fixture
async def db_session():
    async for session in get_postgres_db():
        yield session
        break  # Only get one session from the pool
```

### Migration Testing

```python
# Test data migration scripts
async def test_data_migration():
    """Test that data migrates correctly."""

    # Setup old schema
    async with async_engine.connect() as conn:
        await conn.execute(text("""
            CREATE TABLE old_users (
                id SERIAL PRIMARY KEY,
                fullname VARCHAR(200)
            )
        """))
        await conn.commit()

    # Insert test data
    await conn.execute(text("""
        INSERT INTO old_users (fullname) VALUES ('John Doe'), ('Jane Smith')
    """))

    # Run migration
    await run_migration_script("migrate_users.sql")

    # Verify new schema
    result = await conn.execute(select(User).where(User.name.like("% %")))
    migrated_users = result.scalars().all()

    assert len(migrated_users) == 2
    assert migrated_users[0].name in ["John Doe", "Jane Smith"]
```

## Performance Considerations

### Connection Pool Tuning

```python
# MySQL typical settings
# pool_size=10, max_overflow=20

# PostgreSQL optimized settings
DB_POOL_SIZE = 20  # PostgreSQL can handle more connections
DB_MAX_OVERFLOW = 50  # Higher overflow for burst traffic
DB_POOL_RECYCLE = 1800  # Shorter recycle time
```

### Query Optimization

```pycon
# MySQL style LIMIT
# SELECT * FROM users LIMIT 10 OFFSET 20

# PostgreSQL optimized (same syntax works)
result = await db.execute(select(User).limit(10).offset(20))

# Use PostgreSQL-specific features
# JSON queries
await db.execute(select(User).where(User.metadata["role"].as_string() == "admin"))

# Array operations
await db.execute(select(User).where(User.tags.contains(["python", "sql"])))
```

## Common Migration Issues

### Data Type Differences

```sql
# MySQL: TINYINT(1) → BOOLEAN
# PostgreSQL: BOOLEAN

# Migration script
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
UPDATE users SET is_active = CASE WHEN active = 1 THEN TRUE ELSE FALSE END;
ALTER TABLE users DROP COLUMN active;
```

### Case Sensitivity

```sql
# MySQL: Case-insensitive by default
# PostgreSQL: Case-sensitive

# Fix: Use citext extension or explicit case conversion
CREATE EXTENSION IF NOT EXISTS citext;

ALTER TABLE users ALTER COLUMN email TYPE citext;
```

### Auto-Increment Differences

```sql
# MySQL: AUTO_INCREMENT
# PostgreSQL: SERIAL or IDENTITY

# Migration
ALTER TABLE users ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY;
```

## Rollback Strategies

### Database-Level Rollback

```pycon
# Create restore point before migration
async with async_engine.connect() as conn:
    await conn.execute(text("CREATE RESTORE POINT pre_migration"))

# If migration fails
await conn.execute(text("ROLLBACK TO RESTORE POINT pre_migration"))
```

### Application-Level Rollback

```pycon
# Implement feature flags
USE_NEW_SCHEMA = os.getenv("USE_NEW_SCHEMA", "false").lower() == "true"

if USE_NEW_SCHEMA:
    # Use new schema
    result = await db.execute(select(NewUser))
else:
    # Use old schema
    result = await db.execute(select(OldUser))
```

## Getting Help

If you encounter issues during migration:

1. **Check the troubleshooting guide** for common database issues
1. **Review PostgreSQL documentation** for syntax differences
1. **Use the health check endpoints** to verify database connectivity
1. **Test migrations on a copy** of your database first
1. **Consider professional migration services** for complex databases

## Summary

Migrating to RapidKit PostgreSQL module:

1. **Replace manual database setup** with dependency injection
1. **Update model definitions** to SQLAlchemy syntax
1. **Migrate queries** to use SQLAlchemy ORM or text
1. **Configure environment variables** for database connection
1. **Update tests** to use the new database fixtures
1. **Run health checks** to verify everything works

The module provides better performance, reliability, and maintainability compared to manual database
setups.
