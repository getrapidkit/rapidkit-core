# cli/utils/validators.py
import re
from pathlib import Path

from core.exceptions import ValidationError

_MIN_NAME_LEN = 2
_MAX_NAME_LEN = 50


def validate_project_name(name: str) -> None:
    """Validate project name"""
    if not name:
        raise ValidationError("Project name cannot be empty")

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise ValidationError(
            "Project name must start with a letter and contain only "
            "letters, numbers, hyphens, and underscores"
        )

    if len(name) < _MIN_NAME_LEN:
        raise ValidationError(f"Project name must be at least {_MIN_NAME_LEN} characters long")
    if len(name) > _MAX_NAME_LEN:
        raise ValidationError(f"Project name must be less than {_MAX_NAME_LEN} characters")


def validate_output_path(path: str) -> Path:
    """Validate and normalize output path"""
    output_path = Path(path).resolve()

    # Check if parent directory exists and is writable
    if not output_path.parent.exists():
        raise ValidationError(f"Parent directory does not exist: {output_path.parent}")

    if not output_path.parent.is_dir():
        raise ValidationError(f"Parent path is not a directory: {output_path.parent}")

    try:
        # Test write permission by creating a temporary file
        test_file = output_path.parent / ".rapidkit_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError as err:
        raise ValidationError(f"No write permission in directory: {output_path.parent}") from err

    return output_path
