import asyncio

from src.modules.free.security.rate_limiting import RateLimiter, RateLimiterConfig


def test_rate_limiter_memory_backend_enforces_limits() -> None:
    config = RateLimiterConfig(default_limit=2, default_window=10)
    limiter = RateLimiter(config)

    async def _exercise() -> tuple[bool, bool, bool]:
        first = await limiter.consume(
            identity="tester",
            method="GET",
            path="/tests",
            raise_on_failure=False,
        )
        second = await limiter.consume(
            identity="tester",
            method="GET",
            path="/tests",
            raise_on_failure=False,
        )
        third = await limiter.consume(
            identity="tester",
            method="GET",
            path="/tests",
            raise_on_failure=False,
        )
        return first.allowed, second.allowed, third.allowed

    first_allowed, second_allowed, third_allowed = asyncio.run(_exercise())

    assert first_allowed is True
    assert second_allowed is True
    assert third_allowed is False
