# Transaction Examples

This document demonstrates various transaction patterns and best practices with the PostgreSQL
module.

## Basic Transaction Context Manager

```python
from src.modules.free.database.db_postgres.postgres import (
    transactional_async,
)
from sqlalchemy import select, update


@transactional_async
async def transfer_credits(from_user_id: int, to_user_id: int, amount: int):
    """Transfer credits between users with automatic transaction management"""

    # Check sender balance
    result = await db.execute(select(User.credits).where(User.id == from_user_id))
    sender_balance = result.scalar_one()

    if sender_balance < amount:
        raise ValueError("Insufficient credits")

    # Perform transfer
    await db.execute(
        update(User)
        .where(User.id == from_user_id)
        .values(credits=User.credits - amount)
    )

    await db.execute(
        update(User).where(User.id == to_user_id).values(credits=User.credits + amount)
    )

    # Transaction automatically committed on success
    # Transaction automatically rolled back on exception
```

## Manual Transaction Management

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.free.database.db_postgres.postgres import get_postgres_db


async def manual_transaction_example(db: AsyncSession = Depends(get_postgres_db)):
    """Manual transaction control for complex operations"""

    async with db.begin():
        try:
            # Multiple operations in one transaction
            await db.execute(
                update(User).where(User.id == 1).values(status="processing")
            )

            # Simulate some work
            await asyncio.sleep(0.1)

            await db.execute(
                update(User).where(User.id == 1).values(status="completed")
            )

            # Explicit commit
            await db.commit()

        except Exception as e:
            # Explicit rollback on error
            await db.rollback()
            raise
```

## Nested Transactions (Savepoints)

```python
async def nested_transaction_example(db: AsyncSession = Depends(get_postgres_db)):
    """Using savepoints for nested transaction control"""

    async with db.begin():
        # Create user
        user = User(name="John Doe", email="john@example.com")
        db.add(user)
        await db.flush()  # Get user ID without committing

        try:
            # Nested operation with savepoint
            async with db.begin_nested():
                # Create profile
                profile = UserProfile(user_id=user.id, bio="Software developer")
                db.add(profile)

                # Simulate error
                if profile.bio == "Software developer":
                    raise ValueError("Invalid bio")

                # This won't execute due to exception

        except ValueError:
            # Savepoint rolled back, but outer transaction continues
            # Create profile with corrected data
            profile = UserProfile(user_id=user.id, bio="Senior Software Developer")
            db.add(profile)

        # Outer transaction commits both user and corrected profile
        await db.commit()
```

## Transaction Decorator Patterns

### Async Transaction Decorator

```python
from src.modules.free.database.db_postgres.postgres import (
    transactional_async,
)
from typing import List


@transactional_async
async def bulk_create_users(user_data: List[dict]) -> List[int]:
    """Create multiple users in a single transaction"""

    user_ids = []

    for data in user_data:
        user = User(**data)
        db.add(user)
        await db.flush()  # Get ID without committing
        user_ids.append(user.id)

    return user_ids


# Usage
@app.post("/bulk-users")
async def create_bulk_users(users: List[UserCreate]):
    user_ids = await bulk_create_users([user.dict() for user in users])
    return {"created_user_ids": user_ids}
```

### Sync Transaction Decorator

```python
from src.modules.free.database.db_postgres.postgres import (
    transactional_sync,
)


@transactional_sync
def sync_bulk_update(user_updates: List[dict]):
    """Synchronous bulk update operation"""

    for update_data in user_updates:
        db.query(User).filter(User.id == update_data["id"]).update(update_data)

    return {"updated_count": len(user_updates)}
```

## Complex Business Transactions

### Order Processing with Inventory Management

```python
@dataclass
class OrderItem:
    product_id: int
    quantity: int
    unit_price: float


@transactional_async
async def process_order(user_id: int, items: List[OrderItem]) -> dict:
    """Process order with inventory validation and payment"""

    # Calculate total
    total_amount = sum(item.quantity * item.unit_price for item in items)

    # Check user balance
    result = await db.execute(select(User.balance).where(User.id == user_id))
    user_balance = result.scalar_one()

    if user_balance < total_amount:
        raise ValueError("Insufficient balance")

    # Check inventory for all items
    for item in items:
        result = await db.execute(
            select(Product.stock).where(Product.id == item.product_id)
        )
        stock = result.scalar_one()

        if stock < item.quantity:
            raise ValueError(f"Insufficient stock for product {item.product_id}")

    # Create order
    order = Order(user_id=user_id, total_amount=total_amount, status="processing")
    db.add(order)
    await db.flush()

    # Create order items and update inventory
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        db.add(order_item)

        # Update inventory
        await db.execute(
            update(Product)
            .where(Product.id == item.product_id)
            .values(stock=Product.stock - item.quantity)
        )

    # Deduct payment
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(balance=User.balance - total_amount)
    )

    # Update order status
    order.status = "completed"

    return {"order_id": order.id, "total_amount": total_amount, "status": "completed"}
```

## Saga Pattern Implementation

### Basic Saga for Distributed Transactions

```python
class SagaStep:
    def __init__(self, name: str, execute_func, compensate_func):
        self.name = name
        self.execute = execute_func
        self.compensate = compensate_func


async def execute_saga(db: AsyncSession, steps: List[SagaStep]) -> dict:
    """Execute saga pattern with compensation on failure"""

    executed_steps = []

    try:
        for step in steps:
            await step.execute(db)
            executed_steps.append(step)

        await db.commit()
        return {"status": "success", "steps_completed": len(steps)}

    except Exception as e:
        # Compensate in reverse order
        for step in reversed(executed_steps):
            try:
                await step.compensate(db)
            except Exception as comp_error:
                logger.error(f"Compensation failed for {step.name}: {comp_error}")

        await db.rollback()
        raise ValueError(f"Saga failed at step {len(executed_steps) + 1}: {e}")


# Usage example
async def create_user_with_profile(user_data: dict, profile_data: dict):
    async def create_user(db):
        user = User(**user_data)
        db.add(user)
        await db.flush()
        return user.id

    async def compensate_user(db):
        # This would need user_id from context
        pass

    async def create_profile(db):
        profile = UserProfile(user_id=user_id, **profile_data)
        db.add(profile)

    async def compensate_profile(db):
        # Delete created profile
        pass

    steps = [
        SagaStep("create_user", create_user, compensate_user),
        SagaStep("create_profile", create_profile, compensate_profile),
    ]

    return await execute_saga(db, steps)
```

## Transaction Isolation Levels

### Setting Custom Isolation Levels

```python
from sqlalchemy import text


async def sensitive_operation(db: AsyncSession = Depends(get_postgres_db)):
    """Operation requiring serializable isolation"""

    # Set isolation level for this transaction
    await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))

    async with db.begin():
        # Read current balance
        result = await db.execute(select(Account.balance).where(Account.id == 1))
        balance = result.scalar_one()

        # Perform calculation
        new_balance = balance + 100

        # Update with check
        result = await db.execute(
            update(Account)
            .where(Account.id == 1)
            .where(Account.balance == balance)  # Optimistic locking
            .values(balance=new_balance)
        )

        if result.rowcount == 0:
            raise ValueError("Concurrent modification detected")
```

## Deadlock Handling

### Automatic Retry on Deadlock

```python
import asyncio
from sqlalchemy.exc import OperationalError


async def execute_with_retry(db_operation, max_retries: int = 3, delay: float = 0.1):
    """Execute operation with automatic retry on deadlock"""

    for attempt in range(max_retries):
        try:
            return await db_operation()

        except OperationalError as e:
            if "deadlock detected" in str(e).lower() and attempt < max_retries - 1:
                await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
                continue
            raise


@transactional_async
async def transfer_with_retry(from_id: int, to_id: int, amount: int):
    """Transfer with deadlock retry"""

    async def do_transfer():
        # Check balance
        result = await db.execute(select(Account.balance).where(Account.id == from_id))
        balance = result.scalar_one()

        if balance < amount:
            raise ValueError("Insufficient funds")

        # Perform transfer
        await db.execute(
            update(Account)
            .where(Account.id == from_id)
            .values(balance=Account.balance - amount)
        )

        await db.execute(
            update(Account)
            .where(Account.id == to_id)
            .values(balance=Account.balance + amount)
        )

    return await execute_with_retry(do_transfer)
```

## Long-Running Transaction Monitoring

### Transaction Timeout Handling

```python
import signal
from contextlib import asynccontextmanager


@asynccontextmanager
async def transaction_timeout(db: AsyncSession, timeout_seconds: int = 30):
    """Context manager for transaction timeouts"""

    def timeout_handler(signum, frame):
        raise TimeoutError("Transaction timeout")

    # Set signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        async with db.begin():
            yield db
    finally:
        # Restore signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


async def long_operation_with_timeout(db: AsyncSession = Depends(get_postgres_db)):
    """Operation with timeout protection"""

    async with transaction_timeout(db, timeout_seconds=60):
        # Perform long-running operations
        await db.execute(text("SELECT pg_sleep(30)"))  # Simulate long operation

        # More operations...
        result = await db.execute(select(User))
        users = result.scalars().all()

        return {"processed_users": len(users)}
```

## Best Practices

### 1. Keep Transactions Short

```python
# Good: Short transaction
@transactional_async
async def quick_update(user_id: int, new_name: str):
    await db.execute(update(User).where(User.id == user_id).values(name=new_name))


# Bad: Long transaction with external calls
@transactional_async
async def bad_update(user_id: int, new_name: str):
    # External API call inside transaction
    response = await httpx.get(f"https://api.example.com/validate/{new_name}")
    response.raise_for_status()

    await db.execute(update(User).where(User.id == user_id).values(name=new_name))
```

### 2. Use Appropriate Isolation Levels

```python
# Read-only operations can use lower isolation
async def read_operation(db: AsyncSession = Depends(get_postgres_db)):
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED"))
        result = await db.execute(select(User))
        return result.scalars().all()


# Critical operations use higher isolation
async def critical_operation(db: AsyncSession = Depends(get_postgres_db)):
    async with db.begin():
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
        # Critical business logic here
```

### 3. Handle Connection Errors Gracefully

```python
from sqlalchemy.exc import DisconnectionError


@transactional_async
async def robust_operation():
    try:
        # Database operations
        await db.execute(select(User))
    except DisconnectionError:
        # Connection lost, operation will be retried by decorator
        logger.warning("Connection lost, transaction will be retried")
        raise  # Re-raise to trigger retry
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
```
