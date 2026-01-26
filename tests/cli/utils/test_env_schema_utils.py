"""
Tests for environment schema utilities.
"""

import tempfile
from pathlib import Path

from cli.utils.env_schema_utils import collect_env_schemas


class TestCollectEnvSchemas:
    """Test collect_env_schemas function."""

    def test_collect_env_schemas_empty_directory(self) -> None:
        """Test collecting schemas from empty modules directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)
            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_no_config_directory(self) -> None:
        """Test collecting schemas when modules don't have config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create a module directory without config
            module_dir = modules_path / "test_module"
            module_dir.mkdir()

            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_no_env_schema_file(self) -> None:
        """Test collecting schemas when config directory exists but no env_schema.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create module with config directory but no env_schema.py
            module_dir = modules_path / "test_module"
            config_dir = module_dir / "config"
            config_dir.mkdir(parents=True)

            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_valid_env_schema(self) -> None:
        """Test collecting schemas from valid env_schema.py files."""
        env_schema_content = """
ENV_SCHEMA = {
    "DATABASE_URL": {
        "type": "string",
        "required": True,
        "description": "Database connection URL"
    },
    "DEBUG": {
        "type": "boolean",
        "default": False,
        "description": "Enable debug mode"
    }
}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create module with valid env_schema.py
            module_dir = modules_path / "test_module"
            config_dir = module_dir / "config"
            config_dir.mkdir(parents=True)

            env_schema_file = config_dir / "env_schema.py"
            env_schema_file.write_text(env_schema_content)

            result = collect_env_schemas(modules_path)

            expected = {
                "DATABASE_URL": {
                    "type": "string",
                    "required": True,
                    "description": "Database connection URL",
                },
                "DEBUG": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable debug mode",
                },
            }
            assert result == expected

    def test_collect_env_schemas_multiple_modules(self) -> None:
        """Test collecting schemas from multiple modules."""
        module1_schema = """
ENV_SCHEMA = {
    "DB_URL": {"type": "string", "required": True},
    "API_KEY": {"type": "string", "required": False}
}
"""

        module2_schema = """
ENV_SCHEMA = {
    "REDIS_URL": {"type": "string", "required": True},
    "CACHE_TTL": {"type": "integer", "default": 3600}
}
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create first module
            module1_dir = modules_path / "auth"
            module1_config = module1_dir / "config"
            module1_config.mkdir(parents=True)
            (module1_config / "env_schema.py").write_text(module1_schema)

            # Create second module
            module2_dir = modules_path / "cache"
            module2_config = module2_dir / "config"
            module2_config.mkdir(parents=True)
            (module2_config / "env_schema.py").write_text(module2_schema)

            result = collect_env_schemas(modules_path)

            expected = {
                "DB_URL": {"type": "string", "required": True},
                "API_KEY": {"type": "string", "required": False},
                "REDIS_URL": {"type": "string", "required": True},
                "CACHE_TTL": {"type": "integer", "default": 3600},
            }
            assert result == expected

    def test_collect_env_schemas_invalid_env_schema(self) -> None:
        """Test collecting schemas when env_schema.py has invalid content."""
        invalid_schema_content = """
# Invalid Python syntax
ENV_SCHEMA = {
    "INVALID": "missing closing brace"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create module with invalid env_schema.py
            module_dir = modules_path / "test_module"
            config_dir = module_dir / "config"
            config_dir.mkdir(parents=True)

            env_schema_file = config_dir / "env_schema.py"
            env_schema_file.write_text(invalid_schema_content)

            # Should not raise exception, should just skip invalid module
            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_no_env_schema_attribute(self) -> None:
        """Test collecting schemas when env_schema.py doesn't define ENV_SCHEMA."""
        no_schema_content = """
# Module without ENV_SCHEMA
def some_function():
    return "test"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create module with env_schema.py but no ENV_SCHEMA
            module_dir = modules_path / "test_module"
            config_dir = module_dir / "config"
            config_dir.mkdir(parents=True)

            env_schema_file = config_dir / "env_schema.py"
            env_schema_file.write_text(no_schema_content)

            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_non_dict_env_schema(self) -> None:
        """Test collecting schemas when ENV_SCHEMA is not a dictionary."""
        invalid_schema_content = """
ENV_SCHEMA = "this is not a dict"
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create module with non-dict ENV_SCHEMA
            module_dir = modules_path / "test_module"
            config_dir = module_dir / "config"
            config_dir.mkdir(parents=True)

            env_schema_file = config_dir / "env_schema.py"
            env_schema_file.write_text(invalid_schema_content)

            result = collect_env_schemas(modules_path)
            assert result == {}

    def test_collect_env_schemas_mixed_valid_invalid(self) -> None:
        """Test collecting schemas with mix of valid and invalid modules."""
        valid_schema = """
ENV_SCHEMA = {
    "VALID_VAR": {"type": "string", "required": True}
}
"""

        invalid_schema = """
# Invalid syntax
ENV_SCHEMA = {
    "INVALID_VAR": "missing closing
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            modules_path = Path(temp_dir)

            # Create valid module
            valid_dir = modules_path / "valid_module"
            valid_config = valid_dir / "config"
            valid_config.mkdir(parents=True)
            (valid_config / "env_schema.py").write_text(valid_schema)

            # Create invalid module
            invalid_dir = modules_path / "invalid_module"
            invalid_config = invalid_dir / "config"
            invalid_config.mkdir(parents=True)
            (invalid_config / "env_schema.py").write_text(invalid_schema)

            result = collect_env_schemas(modules_path)

            # Should only include valid module
            expected = {"VALID_VAR": {"type": "string", "required": True}}
            assert result == expected
