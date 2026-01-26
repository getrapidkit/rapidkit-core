"""Small validators used by env_validator (for tests and examples)

Provide examples of custom validator callables that modules can reference via
`custom_validator: "core.services.validators.is_semver"` in schema.
"""

import re
from typing import Tuple


def is_semver(v: str) -> Tuple[bool, str]:
    pat = re.compile(r"^\d+\.\d+\.\d+$")
    ok = bool(pat.match(v))
    return ok, v if ok else v


def always_upper(v: str) -> str:
    return v.upper()
