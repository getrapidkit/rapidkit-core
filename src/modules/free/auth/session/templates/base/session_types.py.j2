"""Typed helpers for Session module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping


@dataclass(frozen=True)
class SessionHealthSnapshot:
    """Aggregated snapshot used by session health routers."""

    module: str
    session_ttl_seconds: int
    refresh_ttl_seconds: int
    storage_backend: str
    cookie_name: str
    cookie_domain: str | None
    cookie_secure: bool
    cookie_httponly: bool
    cookie_same_site: str
    supports_refresh_tokens: bool
    features: tuple[str, ...]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "SessionHealthSnapshot":
        cookie = data.get("cookie", {})
        if not isinstance(cookie, Mapping):
            cookie = {}
        features_raw = data.get("features", [])
        features = tuple(
            str(feature)
            for feature in features_raw
            if isinstance(feature, str) and feature
        )
        return cls(
            module=str(data.get("module", "session")),
            session_ttl_seconds=int(data.get("session_ttl_seconds", 0)),
            refresh_ttl_seconds=int(data.get("refresh_ttl_seconds", 0)),
            storage_backend=str(data.get("storage_backend", "unknown")),
            cookie_name=str(cookie.get("name", "rapidkit_session")),
            cookie_domain=(
                str(cookie["domain"]) if cookie.get("domain") is not None else None
            ),
            cookie_secure=bool(cookie.get("secure", True)),
            cookie_httponly=bool(cookie.get("httponly", True)),
            cookie_same_site=str(cookie.get("same_site", "lax")),
            supports_refresh_tokens=bool(data.get("supports_refresh_tokens", True)),
            features=features,
        )


def as_dict(snapshot: SessionHealthSnapshot) -> MutableMapping[str, Any]:
    """Render the snapshot into a JSON-serializable mapping."""

    return {
        "module": snapshot.module,
        "session_ttl_seconds": snapshot.session_ttl_seconds,
        "refresh_ttl_seconds": snapshot.refresh_ttl_seconds,
        "storage_backend": snapshot.storage_backend,
        "cookie": {
            "name": snapshot.cookie_name,
            "domain": snapshot.cookie_domain,
            "secure": snapshot.cookie_secure,
            "httponly": snapshot.cookie_httponly,
            "same_site": snapshot.cookie_same_site,
        },
        "supports_refresh_tokens": snapshot.supports_refresh_tokens,
        "features": list(snapshot.features),
    }


__all__ = ["SessionHealthSnapshot", "as_dict"]
