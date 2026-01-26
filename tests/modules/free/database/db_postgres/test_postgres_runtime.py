from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from importlib.machinery import ModuleSpec
from types import ModuleType, SimpleNamespace
from typing import Any, Generator, Iterable, List

import pytest

fastapi = pytest.importorskip("fastapi")
HTTPException = fastapi.HTTPException


class _StubLoader:
    def create_module(self, _spec):  # pragma: no cover - importlib shim
        return None

    def exec_module(self, _module):  # pragma: no cover - importlib shim
        return None


try:  # SQLAlchemy is optional in the test environment
    from sqlalchemy.exc import SQLAlchemyError  # type: ignore[import]
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments

    class SQLAlchemyError(Exception):
        """Lightweight stand-in when SQLAlchemy is unavailable."""


def _install_settings_stub(inserted_modules: list[str]) -> None:
    if "core.settings" in sys.modules:
        return

    settings_module = ModuleType("core.settings")
    settings_ns = SimpleNamespace(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db",
        DB_ECHO=False,
        DB_POOL_SIZE=1,
        DB_MAX_OVERFLOW=1,
        DB_POOL_RECYCLE=300,
        DB_POOL_TIMEOUT=30,
        TEST_DATABASE_URL=None,
    )
    settings_module.settings = settings_ns  # type: ignore[attr-defined]
    settings_module.__spec__ = ModuleSpec("core.settings", _StubLoader())  # type: ignore[attr-defined]
    settings_module.__path__ = []  # type: ignore[attr-defined]

    sys.modules["core.settings"] = settings_module
    inserted_modules.append("core.settings")


def _install_sqlalchemy_stub(inserted_modules: list[str]) -> None:
    if "sqlalchemy" in sys.modules:
        return

    def _text(sql: str) -> str:
        return sql

    class _AsyncEngineStub:
        def __init__(self) -> None:
            self.pool = SimpleNamespace(
                size=lambda: 0,
                checkedin=lambda: 0,
                checkedout=lambda: 0,
                overflow=lambda: 0,
            )
            self.url = "postgresql+asyncpg://stub"

        def begin(self):
            class _Begin:
                async def __aenter__(self):
                    return SimpleNamespace(execute=lambda _: [])

                async def __aexit__(self, exc_type, exc, tb) -> None:
                    return None

            return _Begin()

        async def dispose(self) -> None:
            return None

    class _SyncEngineStub:
        def __init__(self) -> None:
            self.url = "postgresql+psycopg://stub"

        def connect(self):
            class _Connect:
                def __enter__(self):
                    return SimpleNamespace(execute=lambda _: [])

                def __exit__(self, exc_type, exc, tb) -> None:
                    return None

            return _Connect()

        def dispose(self) -> None:
            return None

    def _create_async_engine(*_args, **_kwargs):
        return _AsyncEngineStub()

    def _create_engine(*_args, **_kwargs):
        return _SyncEngineStub()

    def _async_sessionmaker(*_args, **_kwargs):
        async def _factory(*_f_args, **_f_kwargs):  # pragma: no cover - stub fallback
            raise RuntimeError("async_sessionmaker stub invoked")

        return _factory

    def _sessionmaker(*_args, **_kwargs):
        def _factory(*_f_args, **_f_kwargs):  # pragma: no cover - stub fallback
            raise RuntimeError("sessionmaker stub invoked")

        return _factory

    def _declarative_base():
        return SimpleNamespace()

    sqlalchemy_module = ModuleType("sqlalchemy")
    sqlalchemy_module.create_engine = _create_engine  # type: ignore[attr-defined]
    sqlalchemy_module.text = _text  # type: ignore[attr-defined]

    sqlalchemy_exc = ModuleType("sqlalchemy.exc")
    sqlalchemy_exc.SQLAlchemyError = SQLAlchemyError  # type: ignore[attr-defined]

    sqlalchemy_ext = ModuleType("sqlalchemy.ext")
    sqlalchemy_ext_asyncio = ModuleType("sqlalchemy.ext.asyncio")
    sqlalchemy_ext_asyncio.AsyncSession = type("AsyncSession", (), {})  # type: ignore[attr-defined]
    sqlalchemy_ext_asyncio.async_sessionmaker = _async_sessionmaker  # type: ignore[attr-defined]
    sqlalchemy_ext_asyncio.create_async_engine = _create_async_engine  # type: ignore[attr-defined]

    sqlalchemy_orm = ModuleType("sqlalchemy.orm")
    sqlalchemy_orm.Session = type("Session", (), {})  # type: ignore[attr-defined]
    sqlalchemy_orm.declarative_base = _declarative_base  # type: ignore[attr-defined]
    sqlalchemy_orm.sessionmaker = _sessionmaker  # type: ignore[attr-defined]

    sqlalchemy_spec = ModuleSpec("sqlalchemy", _StubLoader())
    sqlalchemy_spec.submodule_search_locations = []  # type: ignore[attr-defined]
    sqlalchemy_module.__spec__ = sqlalchemy_spec  # type: ignore[attr-defined]
    sqlalchemy_module.__path__ = []  # type: ignore[attr-defined]

    sqlalchemy_exc.__spec__ = ModuleSpec("sqlalchemy.exc", _StubLoader())  # type: ignore[attr-defined]

    sqlalchemy_ext_spec = ModuleSpec("sqlalchemy.ext", _StubLoader())
    sqlalchemy_ext_spec.submodule_search_locations = []  # type: ignore[attr-defined]
    sqlalchemy_ext.__spec__ = sqlalchemy_ext_spec  # type: ignore[attr-defined]
    sqlalchemy_ext.__path__ = []  # type: ignore[attr-defined]

    sqlalchemy_ext_asyncio.__spec__ = ModuleSpec("sqlalchemy.ext.asyncio", _StubLoader())  # type: ignore[attr-defined]
    sqlalchemy_orm.__spec__ = ModuleSpec("sqlalchemy.orm", _StubLoader())  # type: ignore[attr-defined]

    sqlalchemy_module.exc = sqlalchemy_exc  # type: ignore[attr-defined]
    sqlalchemy_module.ext = sqlalchemy_ext  # type: ignore[attr-defined]
    sqlalchemy_module.orm = sqlalchemy_orm  # type: ignore[attr-defined]
    sqlalchemy_ext.asyncio = sqlalchemy_ext_asyncio  # type: ignore[attr-defined]

    sys.modules["sqlalchemy"] = sqlalchemy_module
    sys.modules["sqlalchemy.exc"] = sqlalchemy_exc
    sys.modules["sqlalchemy.ext"] = sqlalchemy_ext
    sys.modules["sqlalchemy.ext.asyncio"] = sqlalchemy_ext_asyncio
    sys.modules["sqlalchemy.orm"] = sqlalchemy_orm
    inserted_modules.extend(
        [
            "sqlalchemy",
            "sqlalchemy.exc",
            "sqlalchemy.ext",
            "sqlalchemy.ext.asyncio",
            "sqlalchemy.orm",
        ]
    )


def _cleanup_modules(module_names: list[str]) -> None:
    for name in reversed(module_names):
        sys.modules.pop(name, None)


@contextmanager
def _import_postgres_with_settings(**overrides) -> Generator[ModuleType, None, None]:
    inserted_modules: list[str] = []
    _install_settings_stub(inserted_modules)
    settings_module = sys.modules["core.settings"].settings  # type: ignore[attr-defined]
    for key, value in overrides.items():
        setattr(settings_module, key, value)
    _install_sqlalchemy_stub(inserted_modules)

    original_postgres_runtime = sys.modules.pop("runtime.core.database.postgres", None)

    module = importlib.import_module("runtime.core.database.postgres")
    sys.modules.setdefault("core.database.postgres", module)

    try:
        yield module
    finally:
        sys.modules.pop("runtime.core.database.postgres", None)
        sys.modules.pop("core.database.postgres", None)
        if original_postgres_runtime is not None:
            sys.modules["runtime.core.database.postgres"] = original_postgres_runtime
        if "core.database.postgres" not in sys.modules:
            sys.modules["core.database.postgres"] = sys.modules.get(
                "runtime.core.database.postgres"
            )
        _cleanup_modules(inserted_modules)


HTTP_INTERNAL_ERROR = 500


@pytest.fixture(scope="module")
def postgres_module() -> Generator[ModuleType, None, None]:
    inserted_modules: list[str] = []
    _install_settings_stub(inserted_modules)
    _install_sqlalchemy_stub(inserted_modules)

    original_postgres_runtime = sys.modules.pop("runtime.core.database.postgres", None)

    module = importlib.import_module("runtime.core.database.postgres")
    sys.modules.setdefault("core.database.postgres", module)

    try:
        yield module
    finally:
        sys.modules.pop("runtime.core.database.postgres", None)
        sys.modules.pop("core.database.postgres", None)
        if original_postgres_runtime is not None:
            sys.modules["runtime.core.database.postgres"] = original_postgres_runtime
        if "core.database.postgres" not in sys.modules:
            sys.modules["core.database.postgres"] = sys.modules.get(
                "runtime.core.database.postgres"
            )
        _cleanup_modules(inserted_modules)


@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"


class AsyncSessionStub:
    def __init__(self, rows: Iterable[Any] | None = None) -> None:
        self.closed = False
        self.rollback_called = False
        self.begin_entries = 0
        self.executed_sql: List[str] = []
        self.close_calls = 0
        self._rows = list(rows or [("row",)])

    async def __aenter__(self) -> AsyncSessionStub:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.closed = True

    def begin(self):
        session = self

        class _Transaction:
            async def __aenter__(self):
                session.begin_entries += 1
                return session

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return

        return _Transaction()

    async def close(self) -> None:
        self.closed = True
        self.close_calls += 1

    async def rollback(self) -> None:
        self.rollback_called = True

    async def execute(self, statement) -> Any:
        self.executed_sql.append(str(statement))

        class _Result:
            def __init__(self, rows: Iterable[Any]) -> None:
                self._rows = list(rows)

            def fetchall(self) -> List[Any]:
                return list(self._rows)

        return _Result(self._rows)


class SyncSessionStub:
    def __init__(self) -> None:
        self.closed = False
        self.rollback_called = False
        self.begin_entries = 0

    def begin(self):
        session = self

        class _Transaction:
            def __enter__(self):
                session.begin_entries += 1
                return session

            def __exit__(self, exc_type, exc, tb) -> None:
                return

        return _Transaction()

    def close(self) -> None:
        self.closed = True

    def rollback(self) -> None:
        self.rollback_called = True


class AsyncConnectionStub:
    def __init__(self) -> None:
        self.executed: List[str] = []

    async def execute(self, statement) -> None:
        self.executed.append(str(statement))


class AsyncEngineStub:
    def __init__(self) -> None:
        self.connection = AsyncConnectionStub()
        self.pool: Any = DummyPool()
        self.disposed = False

    def begin(self):
        connection = self.connection

        class _Begin:
            async def __aenter__(self):
                return connection

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return

        return _Begin()

    async def dispose(self) -> None:
        self.disposed = True


class FailingAsyncEngineStub(AsyncEngineStub):
    def begin(self):
        class _Begin:
            async def __aenter__(self):
                raise SQLAlchemyError("async failure")

            async def __aexit__(self, exc_type, exc, tb) -> None:
                return

        return _Begin()


class SyncConnectionStub:
    def __init__(self) -> None:
        self.executed: List[str] = []

    def execute(self, statement) -> List[str]:
        self.executed.append(str(statement))
        return []


class SyncEngineStub:
    def __init__(self) -> None:
        self.connection = SyncConnectionStub()
        self.disposed = False

    def connect(self):
        connection = self.connection

        class _Connect:
            def __enter__(self):
                return connection

            def __exit__(self, exc_type, exc, tb) -> None:
                return

        return _Connect()

    def dispose(self) -> None:
        self.disposed = True


class FailingSyncEngineStub(SyncEngineStub):
    def connect(self):
        class _Connect:
            def __enter__(self):
                raise SQLAlchemyError("sync failure")

            def __exit__(self, exc_type, exc, tb) -> None:
                return

        return _Connect()


class DummyPool:
    def __init__(
        self, size: int = 5, checked_in: int = 3, checked_out: int = 2, overflow: int = 1
    ) -> None:
        self._size = size
        self._checked_in = checked_in
        self._checked_out = checked_out
        self._overflow = overflow

    def size(self) -> int:
        return self._size

    def checkedin(self) -> int:
        return self._checked_in

    def checkedout(self) -> int:
        return self._checked_out

    def overflow(self) -> int:
        return self._overflow


class LoggerStub:
    def __init__(self) -> None:
        self.info_messages: List[str] = []
        self.error_messages: List[str] = []

    def info(self, message: str) -> None:
        self.info_messages.append(message)

    def error(self, message: str) -> None:
        self.error_messages.append(message)


@pytest.mark.anyio
async def test_get_postgres_db_yields_session_and_closes(monkeypatch, postgres_module):
    session = AsyncSessionStub()
    monkeypatch.setattr(postgres_module, "AsyncSessionLocal", lambda: session)

    generator = postgres_module.get_postgres_db()
    yielded = await generator.__anext__()

    assert yielded is session
    await generator.aclose()
    assert session.close_calls == 1


@pytest.mark.anyio
async def test_transactional_async_rolls_back_on_error(monkeypatch, postgres_module):
    created: List[AsyncSessionStub] = []

    def factory() -> AsyncSessionStub:
        session = AsyncSessionStub()
        created.append(session)
        return session

    monkeypatch.setattr(postgres_module, "AsyncSessionLocal", factory)

    with pytest.raises(RuntimeError):
        async with postgres_module.transactional_async():
            raise RuntimeError("trigger rollback")

    session = created[-1]
    assert session.rollback_called is True
    assert session.begin_entries == 1
    assert session.closed is True


def test_transactional_sync_rolls_back_on_error(monkeypatch, postgres_module):
    created: List[SyncSessionStub] = []

    def factory() -> SyncSessionStub:
        session = SyncSessionStub()
        created.append(session)
        return session

    monkeypatch.setattr(postgres_module, "SyncSessionLocal", factory)

    with pytest.raises(RuntimeError), postgres_module.transactional_sync():
        raise RuntimeError("trigger rollback")

    session = created[-1]
    assert session.rollback_called is True
    assert session.begin_entries == 1
    assert session.closed is True


@pytest.mark.anyio
async def test_check_postgres_connection_runs_select(monkeypatch, postgres_module):
    engine = AsyncEngineStub()
    logger = LoggerStub()
    monkeypatch.setattr(postgres_module, "async_engine", engine)
    monkeypatch.setattr(postgres_module, "logger", logger)

    await postgres_module.check_postgres_connection()

    assert engine.connection.executed == ["SELECT 1"]
    assert logger.info_messages


@pytest.mark.anyio
async def test_check_postgres_connection_failure(monkeypatch, postgres_module):
    engine = FailingAsyncEngineStub()
    logger = LoggerStub()
    monkeypatch.setattr(postgres_module, "async_engine", engine)
    monkeypatch.setattr(postgres_module, "logger", logger)

    with pytest.raises(HTTPException) as exc:
        await postgres_module.check_postgres_connection()

    assert exc.value.status_code == HTTP_INTERNAL_ERROR
    assert logger.error_messages


def test_check_postgres_connection_sync_success(monkeypatch, postgres_module):
    engine = SyncEngineStub()
    logger = LoggerStub()
    monkeypatch.setattr(postgres_module, "sync_engine", engine)
    monkeypatch.setattr(postgres_module, "logger", logger)

    postgres_module.check_postgres_connection_sync()

    assert engine.connection.executed == ["SELECT 1"]
    assert logger.info_messages


def test_check_postgres_connection_sync_failure(monkeypatch, postgres_module):
    engine = FailingSyncEngineStub()
    logger = LoggerStub()
    monkeypatch.setattr(postgres_module, "sync_engine", engine)
    monkeypatch.setattr(postgres_module, "logger", logger)

    with pytest.raises(HTTPException) as exc:
        postgres_module.check_postgres_connection_sync()

    assert exc.value.status_code == HTTP_INTERNAL_ERROR
    assert logger.error_messages


@pytest.mark.anyio
async def test_get_pool_status_reports_counts(monkeypatch, postgres_module):
    engine = AsyncEngineStub()
    engine.pool = DummyPool(size=8, checked_in=5, checked_out=2, overflow=1)
    monkeypatch.setattr(postgres_module, "async_engine", engine)

    result = await postgres_module.get_pool_status()

    assert result == {
        "pool_size": 8,
        "checked_in": 5,
        "checked_out": 2,
        "overflow": 1,
        "total_connections": 9,
    }


@pytest.mark.anyio
async def test_execute_raw_sql_returns_rows(monkeypatch, postgres_module):
    created: List[AsyncSessionStub] = []

    def factory() -> AsyncSessionStub:
        session = AsyncSessionStub(rows=[("value",)])
        created.append(session)
        return session

    monkeypatch.setattr(postgres_module, "AsyncSessionLocal", factory)

    result = await postgres_module.execute_raw_sql("SELECT 42")

    session = created[-1]
    assert result == [("value",)]
    assert session.executed_sql == ["SELECT 42"]
    assert session.closed is True


@pytest.mark.anyio
async def test_close_async_engine_disposes(monkeypatch, postgres_module):
    engine = AsyncEngineStub()
    monkeypatch.setattr(postgres_module, "async_engine", engine)

    await postgres_module.close_async_engine()

    assert engine.disposed is True


@pytest.mark.anyio
async def test_initialize_database_runs_create_all(monkeypatch, postgres_module):
    create_calls: List[Any] = []

    def fake_create_all(bind: Any) -> None:
        create_calls.append(bind)

    metadata = SimpleNamespace(create_all=fake_create_all)
    base_stub = SimpleNamespace(metadata=metadata)
    monkeypatch.setattr(postgres_module, "Base", base_stub)

    class _Connection:
        async def run_sync(self, func):
            func("sync-connection")

    class _BeginContext:
        async def __aenter__(self):
            return _Connection()

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    class _Engine:
        def begin(self):
            return _BeginContext()

    engine = _Engine()
    logger = LoggerStub()

    monkeypatch.setattr(postgres_module, "async_engine", engine)
    monkeypatch.setattr(postgres_module, "logger", logger)

    await postgres_module.initialize_database()

    assert create_calls == ["sync-connection"]
    assert logger.info_messages


def test_close_sync_engine_disposes(monkeypatch, postgres_module):
    engine = SyncEngineStub()
    monkeypatch.setattr(postgres_module, "sync_engine", engine)

    postgres_module.close_sync_engine()

    assert engine.disposed is True


def test_get_database_url_masks_password(monkeypatch, postgres_module):
    settings = SimpleNamespace(DATABASE_URL="postgresql://user:secret@localhost/db")
    monkeypatch.setattr(postgres_module, "settings", settings)

    masked = postgres_module.get_database_url()

    assert masked == "postgresql://user:***@localhost/db"


def test_get_database_url_can_expose_password(monkeypatch, postgres_module):
    settings = SimpleNamespace(DATABASE_URL="postgresql://user:secret@localhost/db")
    monkeypatch.setattr(postgres_module, "settings", settings)

    exposed = postgres_module.get_database_url(hide_password=False)

    assert exposed == "postgresql://user:secret@localhost/db"


def test_test_engines_initialize_when_test_database_url_present():
    test_url = "postgresql://tester:secret@localhost/test_db"

    with _import_postgres_with_settings(
        TEST_DATABASE_URL=test_url, test_database_url=test_url
    ) as module:
        assert module.test_async_engine is not None
        assert module.test_sync_engine is not None
        assert module.TestAsyncSessionLocal is not None
        assert module.TestSyncSessionLocal is not None
