import asyncio
from types import SimpleNamespace

import pytest

from runtime.security import rate_limiting
from runtime.security.rate_limiting import (
    MemoryRateLimitBackend,
    RateLimiter,
    RateLimiterConfig,
    RateLimitHeaders,
    RateLimitResult,
    RateLimitRule,
    configure_rate_limiter,
    create_backend,
    get_rate_limiter_metadata,
)

MEMORY_BLOCK_SECONDS = 30.0
REDIS_BLOCK_SECONDS = 5.0


def test_rate_limiter_headers_surface_metadata() -> None:
    config = RateLimiterConfig(default_limit=1, default_window=30)
    limiter = configure_rate_limiter(config)

    async def _exercise():
        allowed = await limiter.consume(
            identity="integration",
            method="GET",
            path="/integration",
            raise_on_failure=False,
        )
        blocked = await limiter.consume(
            identity="integration",
            method="GET",
            path="/integration",
            raise_on_failure=False,
        )
        return allowed, blocked

    allowed, blocked = asyncio.run(_exercise())

    assert allowed.allowed is True
    assert blocked.allowed is False

    headers = blocked.to_headers(config.headers)
    assert config.headers.limit in headers
    assert config.headers.remaining in headers
    assert headers[config.headers.limit] == str(config.default_limit)
    assert headers[config.headers.rule] == config.build_default_rule().name

    metadata = get_rate_limiter_metadata()
    assert metadata["default_rule"]["limit"] == config.default_limit


def test_rate_limiter_disabled_allows_requests() -> None:
    config = RateLimiterConfig(enabled=False, default_limit=3, default_window=15)
    limiter = RateLimiter(config)

    result = asyncio.run(
        limiter.consume(
            identity=None,
            method="POST",
            path="/disabled",
            raise_on_failure=True,
        )
    )

    assert result.allowed is True
    assert result.remaining == config.default_limit
    assert result.bucket == f"{config.default_rule_name}:anonymous"


def test_rate_limiter_route_rule_has_priority() -> None:
    route_rule = RateLimitRule(
        name="route",
        limit=5,
        window_seconds=60,
        scope="route-identity",
        priority=10,
        methods=("GET",),
        routes=("/api",),
    )
    config = RateLimiterConfig(default_limit=100, default_window=60, rules=(route_rule,))
    limiter = RateLimiter(config)

    result = asyncio.run(
        limiter.consume(
            identity="bob",
            method="GET",
            path="/api/users",
            raise_on_failure=False,
        )
    )

    assert result.rule.name == "route"
    assert result.bucket == "route::api:users:bob"


def test_memory_backend_honours_block_seconds() -> None:
    config = RateLimiterConfig(
        default_limit=1, default_window=3, default_block_seconds=int(MEMORY_BLOCK_SECONDS)
    )
    limiter = RateLimiter(config)

    first = asyncio.run(
        limiter.consume(identity="client", method="GET", path="/block", raise_on_failure=True)
    )
    second = asyncio.run(
        limiter.consume(
            identity="client",
            method="GET",
            path="/block",
            raise_on_failure=False,
        )
    )
    third = asyncio.run(
        limiter.consume(
            identity="client",
            method="GET",
            path="/block",
            raise_on_failure=False,
        )
    )

    assert first.allowed is True
    assert second.allowed is False
    assert second.blocked is True
    assert second.retry_after == pytest.approx(MEMORY_BLOCK_SECONDS, rel=0.01)
    assert third.allowed is False
    assert third.blocked is True
    assert third.retry_after == pytest.approx(MEMORY_BLOCK_SECONDS, rel=0.01)


def test_rate_limit_result_skips_headers_when_disabled() -> None:
    rule = RateLimitRule(
        name="custom",
        limit=10,
        window_seconds=10,
        include_headers=False,
    )
    result = RateLimitResult(
        rule=rule,
        allowed=False,
        remaining=0,
        reset_after=5.0,
        reset_at=123.0,
        limit=10,
        identity="user",
        bucket="custom:user",
    )

    assert result.to_headers(RateLimitHeaders()) == {}


def test_rate_limiter_metadata_masks_redis_url() -> None:
    config = RateLimiterConfig(
        backend="redis", redis_url="redis://sensitive", default_limit=2, default_window=10
    )
    limiter = RateLimiter(config, backend=MemoryRateLimitBackend())

    metadata = limiter.get_metadata()

    assert metadata["backend"] == "redis"
    assert metadata["redis_url"] == "***"


def test_create_backend_requires_redis_url() -> None:
    config = RateLimiterConfig(backend="redis", redis_url=None)
    with pytest.raises(RuntimeError):
        create_backend(config)


class _FakeRedisPipeline:
    def __init__(self, client: "_FakeRedisClient") -> None:
        self._client = client
        self._ops: list[tuple[str, str, int]] = []

    def incrby(self, key: str, value: int) -> "_FakeRedisPipeline":
        self._ops.append(("incrby", key, value))
        return self

    def pttl(self, key: str) -> "_FakeRedisPipeline":
        self._ops.append(("pttl", key, 0))
        return self

    async def execute(self) -> tuple[int, int]:
        count = 0
        ttl = -1
        for op, key, value in self._ops:
            if op == "incrby":
                count = self._client._incrby(key, value)
            elif op == "pttl":
                ttl = self._client._pttl(key)
        self._ops.clear()
        return count, ttl


class _FakeRedisClient:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.ttls: dict[str, int] = {}
        self.block_ttls: dict[str, int] = {}

    @classmethod
    def from_url(
        cls, _url: str, *, decode_responses: bool = False
    ) -> "_FakeRedisClient":  # noqa: ARG003
        return cls()

    def pipeline(self) -> _FakeRedisPipeline:
        return _FakeRedisPipeline(self)

    def _incrby(self, key: str, value: int) -> int:
        self.counters[key] = self.counters.get(key, 0) + value
        return self.counters[key]

    def _pttl(self, key: str) -> int:
        return self.ttls.get(key, -1)

    async def pexpire(self, key: str, ttl: int) -> bool:
        self.ttls[key] = ttl
        return True

    async def set(self, key: str, value: bytes, *, ex: int | None = None) -> bool:  # noqa: ARG002
        if ex is not None:
            self.block_ttls[key] = int(ex * 1000)
        return True

    async def pttl(self, key: str) -> int:
        return self.block_ttls.get(key, -2)


def test_redis_backend_enforces_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = SimpleNamespace(Redis=_FakeRedisClient)
    monkeypatch.setattr(rate_limiting, "redis_async", fake_module)

    config = RateLimiterConfig(
        backend="redis",
        redis_url="redis://local",
        default_limit=2,
        default_window=10,
    )
    backend = create_backend(config)
    limiter = RateLimiter(config, backend=backend)

    first = asyncio.run(
        limiter.consume(
            identity="redis-user",
            method="GET",
            path="/resource",
            raise_on_failure=True,
        )
    )
    second = asyncio.run(
        limiter.consume(
            identity="redis-user",
            method="GET",
            path="/resource",
            raise_on_failure=True,
        )
    )
    third = asyncio.run(
        limiter.consume(
            identity="redis-user",
            method="GET",
            path="/resource",
            raise_on_failure=False,
        )
    )

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.remaining == 0

    redis_client: _FakeRedisClient = backend._redis  # type: ignore[attr-defined]
    key = backend._format_key(first.bucket)  # type: ignore[attr-defined]
    assert redis_client.counters[key] >= config.default_limit
    assert redis_client.ttls[key] == config.default_window * 1000


def test_redis_backend_honours_block_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = SimpleNamespace(Redis=_FakeRedisClient)
    monkeypatch.setattr(rate_limiting, "redis_async", fake_module)

    config = RateLimiterConfig(
        backend="redis",
        redis_url="redis://local",
        default_limit=1,
        default_window=1,
        default_block_seconds=int(REDIS_BLOCK_SECONDS),
    )
    backend = create_backend(config)
    limiter = RateLimiter(config, backend=backend)

    first = asyncio.run(
        limiter.consume(
            identity="redis-lock",
            method="GET",
            path="/resource",
            raise_on_failure=True,
        )
    )
    second = asyncio.run(
        limiter.consume(
            identity="redis-lock",
            method="GET",
            path="/resource",
            raise_on_failure=False,
        )
    )
    third = asyncio.run(
        limiter.consume(
            identity="redis-lock",
            method="GET",
            path="/resource",
            raise_on_failure=False,
        )
    )

    assert first.allowed is True
    assert second.allowed is False
    assert second.blocked is True
    assert second.retry_after == pytest.approx(REDIS_BLOCK_SECONDS, rel=0.01)
    assert third.blocked is True

    redis_client: _FakeRedisClient = backend._redis  # type: ignore[attr-defined]
    block_key = backend._format_block_key(second.bucket)  # type: ignore[attr-defined]
    assert redis_client.block_ttls[block_key] == config.default_block_seconds * 1000
