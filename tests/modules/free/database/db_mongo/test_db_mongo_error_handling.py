"""Error handling tests for Db Mongo runtime."""

from __future__ import annotations

import pytest


def test_missing_motor_dependency_raises(generated_db_mongo_modules) -> None:
    base_module = generated_db_mongo_modules.base
    original_client = getattr(base_module, "AsyncIOMotorClient", None)
    base_module.AsyncIOMotorClient = None  # Simulate motor not installed

    runtime = base_module.DbMongo()
    with pytest.raises(base_module.DbMongoDependencyError):
        _ = runtime.client

    base_module.AsyncIOMotorClient = original_client
