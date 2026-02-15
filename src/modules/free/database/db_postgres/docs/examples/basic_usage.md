# Basic Usage Examples

This document provides basic usage examples for the PostgreSQL database module.

## Model Definition

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.modules.free.database.db_postgres.postgres import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    author = relationship("User", back_populates="posts")


# Add reverse relationship to User
User.posts = relationship("Post", back_populates="author")
```

## FastAPI CRUD Operations

### Create User

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.free.database.db_postgres.postgres import get_postgres_db
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    name: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime


@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_postgres_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    db_user = User(email=user.email, name=user.name)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        name=db_user.name,
        created_at=db_user.created_at,
    )
```

### Get Users with Pagination

```python
from typing import List, Optional
from fastapi import Query


@router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_postgres_db),
):
    query = select(User)

    if search:
        query = query.where(User.name.ilike(f"%{search}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    return [
        UserResponse(
            id=user.id, email=user.email, name=user.name, created_at=user.created_at
        )
        for user in users
    ]
```

### Get Single User with Posts

```python
from sqlalchemy.orm import selectinload


class UserDetailResponse(UserResponse):
    posts: List[PostResponse] = []


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(
        select(User).options(selectinload(User.posts)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        posts=[
            PostResponse(
                id=post.id,
                title=post.title,
                content=post.content,
                created_at=post.created_at,
            )
            for post in user.posts
        ],
    )
```

### Update User

```python
class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(get_postgres_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check email uniqueness if updating email
    if user_update.email and user_update.email != user.email:
        email_check = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already taken")

    # Update fields
    if user_update.email:
        user.email = user_update.email
    if user_update.name:
        user.name = user_update.name

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id, email=user.email, name=user.name, created_at=user.created_at
    )
```

### Delete User

```python
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}
```

## Raw SQL Queries

### Using text() for Raw Queries

```python
from sqlalchemy import text


@router.get("/stats")
async def get_user_stats(db: AsyncSession = Depends(get_postgres_db)):
    # Raw SQL query
    result = await db.execute(text("""
        SELECT
            COUNT(*) as total_users,
            COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as new_users_30d,
            AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))/86400) as avg_account_age_days
        FROM users
    """))

    row = result.first()
    return {
        "total_users": row.total_users,
        "new_users_last_30_days": row.new_users_30d,
        "avg_account_age_days": (
            round(row.avg_account_age_days, 2) if row.avg_account_age_days else 0
        ),
    }
```

## Sync Database Operations

### Using Sync Dependencies

```python
from src.modules.free.database.db_postgres.postgres import get_sync_db
from sqlalchemy.orm import Session


@app.get("/legacy-users")
def get_legacy_users(db: Session = Depends(get_sync_db)):
    """Legacy endpoint using sync database operations"""
    users = db.query(User).all()
    return [{"id": user.id, "name": user.name, "email": user.email} for user in users]
```

## Error Handling

### Comprehensive Error Handling

```python
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


@router.post("/users")
async def create_user_safe(
    user: UserCreate, db: AsyncSession = Depends(get_postgres_db)
):
    try:
        # Check for existing user
        result = await db.execute(select(User).where(User.email == user.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user
        db_user = User(email=user.email, name=user.name)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return {"id": db_user.id, "message": "User created successfully"}

    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=500, detail="Database integrity error")

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Configuration Examples

### Environment Variables

```bash
# .env file
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/myapp
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
DB_POOL_RECYCLE=1800
DB_ECHO=false
```

### Settings Class

```python
from pydantic import BaseSettings


class DatabaseSettings(BaseSettings):
    database_url: str
    pool_size: int = 20
    max_overflow: int = 50
    pool_recycle: int = 1800
    echo: bool = False

    class Config:
        env_file = ".env"


db_settings = DatabaseSettings()
```
