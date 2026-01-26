"""Generator context integration tests for Db Postgres."""

from __future__ import annotations


def test_base_context_contains_expected_paths(
    db_postgres_generator, module_config: dict[str, object]
) -> None:
    context = db_postgres_generator.build_base_context(module_config)
    assert context["python_output_relative"] == "src/modules/free/database/db_postgres/postgres.py"
    assert (
        context["nest_output_relative"]
        == "src/modules/free/database/db_postgres/postgres.service.ts"
    )
    assert context["rapidkit_vendor_module"] == "db_postgres"
