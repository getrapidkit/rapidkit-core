"""Typed helpers for OAuth module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, MutableMapping


@dataclass(frozen=True)
class OAuthProviderSnapshot:
    """Serializable view of an OAuth provider configuration."""

    name: str
    authorize_url: str
    token_url: str
    scopes: tuple[str, ...]
    userinfo_url: str | None
    redirect_uri: str | None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OAuthProviderSnapshot":
        return cls(
            name=str(data.get("name", "")),
            authorize_url=str(data.get("authorize_url", "")),
            token_url=str(data.get("token_url", "")),
            scopes=tuple(str(scope) for scope in data.get("scopes", []) if scope),
            userinfo_url=data.get("userinfo_url"),
            redirect_uri=data.get("redirect_uri"),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "authorize_url": self.authorize_url,
            "token_url": self.token_url,
            "scopes": list(self.scopes),
            "userinfo_url": self.userinfo_url,
            "redirect_uri": self.redirect_uri,
        }


@dataclass(frozen=True)
class OAuthHealthSnapshot:
    """Aggregated OAuth module metadata consumed by health endpoints."""

    module: str
    redirect_base_url: str
    state_ttl_seconds: int
    state_cleanup_interval: int
    provider_count: int
    features: tuple[str, ...]
    providers: Mapping[str, OAuthProviderSnapshot]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "OAuthHealthSnapshot":
        providers_raw = data.get("providers", {})
        providers: Dict[str, OAuthProviderSnapshot] = {}
        if isinstance(providers_raw, Mapping):
            for key, value in providers_raw.items():
                if isinstance(value, Mapping):
                    providers[str(key)] = OAuthProviderSnapshot.from_mapping(value)

        features = tuple(str(feature) for feature in data.get("features", []) if feature)

        return cls(
            module=str(data.get("module", "oauth")),
            redirect_base_url=str(data.get("redirect_base_url", "/oauth")),
            state_ttl_seconds=int(data.get("state_ttl_seconds", 0)),
            state_cleanup_interval=int(data.get("state_cleanup_interval", 0)),
            provider_count=int(data.get("provider_count", len(providers))),
            features=features,
            providers=providers,
        )


def as_dict(snapshot: OAuthHealthSnapshot) -> MutableMapping[str, Any]:
    """Render the snapshot to a JSON-serializable mapping."""

    return {
        "module": snapshot.module,
        "redirect_base_url": snapshot.redirect_base_url,
        "state_ttl_seconds": snapshot.state_ttl_seconds,
        "state_cleanup_interval": snapshot.state_cleanup_interval,
        "provider_count": snapshot.provider_count,
        "features": list(snapshot.features),
        "providers": {
            key: provider.as_dict() for key, provider in snapshot.providers.items()
        },
    }


__all__ = ["OAuthHealthSnapshot", "OAuthProviderSnapshot", "as_dict"]
