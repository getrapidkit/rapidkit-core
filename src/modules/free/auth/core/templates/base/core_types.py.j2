"""Typed helpers for the Auth Core module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping


@dataclass(frozen=True)
class AuthCoreHealthSnapshot:
    """Serializable view of the Auth Core runtime configuration."""

    module: str
    issuer: str | None
    hash: str | None
    iterations: int
    token_ttl_seconds: int
    pepper_env: str | None
    pepper_configured: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AuthCoreHealthSnapshot":
        return cls(
            module=str(data.get("module", "auth_core")),
            issuer=data.get("issuer"),
            hash=data.get("hash"),
            iterations=int(data.get("iterations", 0)),
            token_ttl_seconds=int(data.get("token_ttl_seconds", 0)),
            pepper_env=data.get("pepper_env"),
            pepper_configured=bool(data.get("pepper_configured", False)),
        )


def as_dict(snapshot: AuthCoreHealthSnapshot) -> MutableMapping[str, Any]:
    """Render the snapshot as a plain mapping suitable for JSON responses."""

    return {
        "module": snapshot.module,
        "issuer": snapshot.issuer,
        "hash": snapshot.hash,
        "iterations": snapshot.iterations,
        "token_ttl_seconds": snapshot.token_ttl_seconds,
        "pepper_env": snapshot.pepper_env,
        "pepper_configured": snapshot.pepper_configured,
    }


__all__ = ["AuthCoreHealthSnapshot", "as_dict"]
