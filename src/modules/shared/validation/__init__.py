"""Shared validation utilities for modules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

from modules.shared.exceptions import ModuleValidationError


class ValidationRule:
    """Base class for validation rules."""

    def __init__(self, name: str, message: str) -> None:
        self.name = name
        self.message = message

    def validate(self, value: Any) -> bool:
        """Validate a value according to this rule."""
        raise NotImplementedError

    def get_error_message(self, value: Any) -> str:
        """Get formatted error message for failed validation."""
        return f"{self.message}. Got: {value}"


class RequiredFieldRule(ValidationRule):
    """Validation rule for required fields."""

    def __init__(self, field_name: str) -> None:
        super().__init__(name=f"required_{field_name}", message=f"Field '{field_name}' is required")
        self.field_name = field_name

    def validate(self, value: Any) -> bool:
        """Check if value is not None and not empty."""
        if value is None:
            return False
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False
        return True


class TypeRule(ValidationRule):
    """Validation rule for type checking."""

    def __init__(self, field_name: str, expected_type: type) -> None:
        super().__init__(
            name=f"type_{field_name}",
            message=f"Field '{field_name}' must be of type {expected_type.__name__}",
        )
        self.field_name = field_name
        self.expected_type = expected_type

    def validate(self, value: Any) -> bool:
        """Check if value is of expected type."""
        return isinstance(value, self.expected_type)


class PatternRule(ValidationRule):
    """Validation rule for regex pattern matching."""

    def __init__(self, field_name: str, pattern: Union[str, Pattern[str]]) -> None:
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        super().__init__(
            name=f"pattern_{field_name}",
            message=f"Field '{field_name}' must match pattern: {self.pattern.pattern}",
        )
        self.field_name = field_name

    def validate(self, value: Any) -> bool:
        """Check if value matches the pattern."""
        if not isinstance(value, str):
            return False
        return bool(self.pattern.match(value))


class RangeRule(ValidationRule):
    """Validation rule for numeric ranges."""

    def __init__(
        self,
        field_name: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> None:
        constraints = []
        if min_value is not None:
            constraints.append(f"min: {min_value}")
        if max_value is not None:
            constraints.append(f"max: {max_value}")

        super().__init__(
            name=f"range_{field_name}",
            message=f"Field '{field_name}' must be within range ({', '.join(constraints)})",
        )
        self.field_name = field_name
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any) -> bool:
        """Check if value is within the specified range."""
        if not isinstance(value, (int, float)):
            return False

        if self.min_value is not None and value < self.min_value:
            return False

        if self.max_value is not None and value > self.max_value:
            return False

        return True


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class Validator:
    """Main validator class for applying validation rules."""

    def __init__(self) -> None:
        self.rules: List[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)

    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """Validate a single field against applicable rules."""
        result = ValidationResult()

        for rule in self.rules:
            # Only apply rules that match this field
            if hasattr(rule, "field_name") and getattr(rule, "field_name", None) == field_name:
                if not rule.validate(value):
                    result.add_error(rule.get_error_message(value))

        return result

    def validate_dict(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate a dictionary against all rules."""
        result = ValidationResult()

        for field_name, value in data.items():
            field_result = self.validate_field(field_name, value)
            result.merge(field_result)

        # Check for missing required fields
        for rule in self.rules:
            if (
                isinstance(rule, RequiredFieldRule)
                and hasattr(rule, "field_name")
                and getattr(rule, "field_name", None) not in data
            ):
                field_name = getattr(rule, "field_name", "unknown")
                result.add_error(f"Required field '{field_name}' is missing")

        return result


def validate_file_exists(file_path: Path, *, context: str = "file") -> None:
    """Validate that a file exists."""
    if not file_path.exists():
        raise ModuleValidationError(
            f"Required {context} not found: {file_path}",
            context={
                "file_path": str(file_path),
                "context": context,
                "parent_exists": file_path.parent.exists(),
            },
        )


def validate_directory_exists(dir_path: Path, *, context: str = "directory") -> None:
    """Validate that a directory exists."""
    if not dir_path.exists():
        raise ModuleValidationError(
            f"Required {context} not found: {dir_path}",
            context={
                "directory_path": str(dir_path),
                "context": context,
                "parent_exists": dir_path.parent.exists(),
            },
        )

    if not dir_path.is_dir():
        raise ModuleValidationError(
            f"Path exists but is not a {context}: {dir_path}",
            context={
                "directory_path": str(dir_path),
                "context": context,
                "is_file": dir_path.is_file(),
            },
        )


def create_module_validator() -> Validator:
    """Create a validator with common module validation rules."""
    validator = Validator()

    # Common module fields
    validator.add_rule(RequiredFieldRule("name"))
    validator.add_rule(TypeRule("name", str))
    validator.add_rule(PatternRule("name", r"^[a-zA-Z_][a-zA-Z0-9_-]*$"))

    validator.add_rule(RequiredFieldRule("version"))
    validator.add_rule(TypeRule("version", str))
    validator.add_rule(PatternRule("version", r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"))

    validator.add_rule(TypeRule("description", str))
    validator.add_rule(TypeRule("author", str))
    validator.add_rule(TypeRule("license", str))
    validator.add_rule(TypeRule("dependencies", dict))
    validator.add_rule(TypeRule("tags", list))

    return validator
