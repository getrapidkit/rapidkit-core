"""Override contracts for File Storage Module.

This module provides extension points for customizing storage behavior
while preserving user modifications across module updates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class StorageOverrideManager:
    """Manages user customizations for the Storage module.

    Handles preservation of user-defined adapters, validators,
    processors, and handlers across module updates.
    """

    # Patterns of files that preserve user overrides
    OVERRIDE_PATTERNS = [
        "src/modules/free/business/storage/storage.py",
        "src/modules/free/business/storage/storage_adapters.py",
        "src/modules/free/business/storage/storage_validators.py",
        "src/modules/free/business/storage/storage_processors.py",
        "src/health/storage.py",
        "src/modules/free/business/storage/routers/storage.py",  # FastAPI routes
        "src/modules/free/business/storage/storage.service.ts",  # NestJS service
        "src/modules/free/business/storage/storage.controller.ts",  # NestJS controller
        "src/modules/free/business/storage/storage.health.ts",
        "src/modules/free/business/storage/storage.routes.ts",
        "src/modules/free/business/storage/storage.configuration.ts",
        "tests/modules/integration/business/storage/test_storage_integration.py",
        "tests/modules/integration/business/storage/storage.integration.spec.ts",
        "config/storage.yaml",
        "config/storage_custom.yaml",
    ]

    def __init__(self, module_root: Path):
        """Initialize the override manager.

        Args:
            module_root: Root path of the storage module
        """
        self.module_root = Path(module_root)

    def preserve_user_overrides(self, generated_files: Dict[str, str]) -> Dict[str, str]:
        """Preserve user customizations in generated files.

        Args:
            generated_files: Dictionary mapping file paths to their content

        Returns:
            Files with user customizations preserved
        """
        preserved_files = dict(generated_files)

        for pattern in self.OVERRIDE_PATTERNS:
            override_path = self.module_root / pattern

            if override_path.exists():
                user_content = override_path.read_text(encoding="utf-8")
                # Merge with generated content if needed
                preserved_files[pattern] = self._merge_content(
                    generated_content=generated_files.get(pattern, ""),
                    user_content=user_content,
                    pattern=pattern,
                )

        return preserved_files

    def _merge_content(self, generated_content: str, user_content: str, pattern: str) -> str:
        """Merge generated and user content intelligently.

        Args:
            generated_content: Generated module content
            user_content: User-customized content
            pattern: File pattern for context-aware merging

        Returns:
            Merged content
        """
        # For Python files with custom classes/functions, preserve user code
        if pattern.endswith(".py"):
            return self._merge_python_content(generated_content, user_content)

        # For TypeScript files with custom services
        if pattern.endswith(".ts"):
            return self._merge_typescript_content(generated_content, user_content)

        # For YAML config, merge configurations
        if pattern.endswith(".yaml") or pattern.endswith(".yml"):
            return self._merge_yaml_content(generated_content, user_content)

        # Default: prefer user content
        return user_content

    def _merge_python_content(self, generated: str, user: str) -> str:
        """Merge Python content preserving user classes and functions."""
        # Extract user-defined classes and functions
        user_classes = self._extract_python_definitions(user, "class")
        user_functions = self._extract_python_definitions(user, "def")

        merged = generated

        # Append user definitions if not already present
        for class_def in user_classes:
            if class_def not in merged:
                merged += f"\n\n{class_def}"

        for func_def in user_functions:
            if func_def not in merged:
                merged += f"\n\n{func_def}"

        return merged

    def _merge_typescript_content(self, generated: str, user: str) -> str:
        """Merge TypeScript content preserving user methods."""
        # Similar to Python merging but for TypeScript
        # This is a simplified version - full implementation would parse AST
        return user if user.strip() else generated

    def _merge_yaml_content(self, generated: str, user: str) -> str:
        """Merge YAML configurations."""
        import yaml

        try:
            generated_config = yaml.safe_load(generated) or {}
            user_config = yaml.safe_load(user) or {}

            # Deep merge user config into generated
            merged = self._deep_merge_dicts(generated_config, user_config)

            return yaml.dump(merged, default_flow_style=False, sort_keys=False)
        except (yaml.YAMLError, TypeError, AttributeError, ValueError):
            # If merge fails, preserve user content
            return user

    def _extract_python_definitions(self, content: str, def_type: str) -> List[str]:
        """Extract Python class or function definitions."""
        import re

        if def_type == "class":
            pattern = r"^class\s+\w+.*?(?=\nclass\s|\ndef\s|$)"
        else:  # def
            pattern = r"^def\s+\w+.*?(?=\nclass\s|\ndef\s|$)"

        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        return [m.strip() for m in matches if m.strip()]

    def _deep_merge_dicts(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge override dict into base dict."""
        result = dict(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def get_override(self, pattern: str) -> Optional[str]:
        """Get user override content for a specific pattern.

        Args:
            pattern: File pattern to retrieve override for

        Returns:
            Override content if exists, None otherwise
        """
        override_path = self.module_root / pattern

        if override_path.exists():
            return override_path.read_text(encoding="utf-8")

        return None

    def backup_user_files(self) -> Dict[str, str]:
        """Create backup of all user-customized files.

        Returns:
            Dictionary mapping file patterns to their content
        """
        backups = {}

        for pattern in self.OVERRIDE_PATTERNS:
            override_path = self.module_root / pattern

            if override_path.exists():
                backups[pattern] = override_path.read_text(encoding="utf-8")

        return backups

    def validate_overrides(self) -> Dict[str, List[str]]:
        """Validate that overrides are syntactically correct.

        Returns:
            Dictionary of validation results (errors, warnings)
        """
        results: Dict[str, List[str]] = {"errors": [], "warnings": []}

        for pattern in self.OVERRIDE_PATTERNS:
            override_path = self.module_root / pattern

            if not override_path.exists():
                continue

            content = override_path.read_text(encoding="utf-8")

            if pattern.endswith(".py"):
                if not self._validate_python(content):
                    results["errors"].append(f"Invalid Python in {pattern}")

            elif pattern.endswith(".ts"):
                if not self._validate_typescript(content):
                    results["warnings"].append(f"Possible TypeScript syntax issue in {pattern}")

        return results

    def _validate_python(self, content: str) -> bool:
        """Validate Python syntax."""
        try:
            compile(content, "<string>", "exec")
            return True
        except SyntaxError:
            return False

    def _validate_typescript(self, content: str) -> bool:
        """Basic TypeScript validation (simplified)."""
        # Simplified check - real implementation would use TypeScript parser
        return "class" in content or "interface" in content or "function" in content
