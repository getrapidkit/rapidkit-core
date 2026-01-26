"""Typed helpers for Email module metadata serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping


@dataclass(frozen=True)
class EmailHealthSnapshot:
    """Normalized snapshot consumed by email health endpoints."""

    module: str
    enabled: bool
    provider: str
    from_email: str
    from_name: str | None
    reply_to: str | None
    supports_templates: bool
    template_directory: str | None
    template_auto_reload: bool
    template_strict: bool
    supports_smtp: bool
    smtp_host: str | None
    smtp_port: int | None
    smtp_timeout_seconds: float | None
    features: tuple[str, ...]
    metadata: Mapping[str, Any]
    default_headers: Mapping[str, str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "EmailHealthSnapshot":
        smtp = data.get("smtp", {}) if isinstance(data.get("smtp"), Mapping) else {}
        features_raw = data.get("features", [])
        metadata_raw = data.get("metadata", {})
        headers_raw = data.get("default_headers", {})
        return cls(
            module=str(data.get("module", "email")),
            enabled=bool(data.get("enabled", True)),
            provider=str(data.get("provider", "")),
            from_email=str(data.get("from_email", "")),
            from_name=str(data.get("from_name")) if data.get("from_name") is not None else None,
            reply_to=str(data.get("reply_to")) if data.get("reply_to") is not None else None,
            supports_templates=bool(data.get("supports_templates", False)),
            template_directory=str(data.get("template_directory")) if data.get("template_directory") else None,
            template_auto_reload=bool(data.get("template_auto_reload", False)),
            template_strict=bool(data.get("template_strict", False)),
            supports_smtp=bool(data.get("supports_smtp", False)),
            smtp_host=str(smtp.get("host")) if smtp.get("host") is not None else None,
            smtp_port=int(smtp.get("port")) if smtp.get("port") is not None else None,
            smtp_timeout_seconds=float(smtp.get("timeout_seconds")) if smtp.get("timeout_seconds") is not None else None,
            features=tuple(
                str(feature)
                for feature in features_raw
                if isinstance(feature, str) and feature
            ),
            metadata=dict(metadata_raw if isinstance(metadata_raw, Mapping) else {}),
            default_headers=dict(headers_raw if isinstance(headers_raw, Mapping) else {}),
        )


def as_dict(snapshot: EmailHealthSnapshot) -> MutableMapping[str, Any]:
    """Render the snapshot into a JSON-serializable mapping."""

    return {
        "module": snapshot.module,
        "enabled": snapshot.enabled,
        "provider": snapshot.provider,
        "from_email": snapshot.from_email,
        "from_name": snapshot.from_name,
        "reply_to": snapshot.reply_to,
        "supports_templates": snapshot.supports_templates,
        "template_directory": snapshot.template_directory,
        "template_auto_reload": snapshot.template_auto_reload,
        "template_strict": snapshot.template_strict,
        "supports_smtp": snapshot.supports_smtp,
        "smtp": {
            "host": snapshot.smtp_host,
            "port": snapshot.smtp_port,
            "timeout_seconds": snapshot.smtp_timeout_seconds,
        },
        "features": list(snapshot.features),
        "metadata": dict(snapshot.metadata),
        "default_headers": dict(snapshot.default_headers),
    }


__all__ = ["EmailHealthSnapshot", "as_dict"]
