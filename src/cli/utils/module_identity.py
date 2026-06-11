from __future__ import annotations

from typing import Optional


def module_identity_matches(recorded: Optional[str], requested: Optional[str]) -> bool:
    """Match hash-registry module labels against CLI module slugs.

    Hash registries may store short names (``agent_runtime``) while the CLI accepts
    fully-qualified slugs (``free/ai/agent_runtime``).
    """

    if not recorded or not requested:
        return False

    rec = str(recorded).strip().strip("/")
    req = str(requested).strip().strip("/")
    if not rec or not req:
        return False

    if rec == req:
        return True
    if rec.endswith(f"/{req}") or req.endswith(f"/{rec}"):
        return True

    return rec.split("/")[-1] == req.split("/")[-1]
