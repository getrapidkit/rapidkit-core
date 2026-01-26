from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CORSConfig(BaseModel):
    """Configuration for CORS middleware."""

    enabled: bool = True
    allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    allow_headers: List[str] = Field(default_factory=lambda: ["*"])
    expose_headers: Optional[List[str]] = None
    max_age: int = 600
    log_level: str = "INFO"
    metadata: Dict[str, Any] = Field(default_factory=dict)


def create_cors_middleware(config: CORSConfig) -> CORSMiddleware:
    """Create FastAPI CORS middleware with the given configuration."""

    return CORSMiddleware(
        allow_origins=config.allow_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
        expose_headers=config.expose_headers,
        max_age=config.max_age,
    )


def _capture_config(config: CORSConfig) -> dict:
    """Return a serializable representation of the CORS configuration."""

    if hasattr(config, "model_dump"):
        return config.model_dump()
    return config.dict()


def setup_cors(app: Any, config: Optional[CORSConfig] = None) -> None:
    """Setup CORS middleware on a FastAPI application.

    Args:
        app: FastAPI application instance
        config: CORS configuration. If None, uses default permissive config.
    """
    if config is None:
        config = CORSConfig()

    config_payload = _capture_config(config)

    state = getattr(app, "state", None)
    if state is None:  # pragma: no cover - FastAPI always provides state
        raise AttributeError("FastAPI application must expose a 'state' attribute")

    setattr(state, "cors_config", config)
    setattr(state, "cors_settings", config_payload)
    setattr(state, "cors_enabled", bool(config.enabled))
    setattr(state, "cors_log_level", config.log_level)
    setattr(state, "cors_metadata", dict(config.metadata))

    if not config.enabled:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allow_origins,
        allow_credentials=config.allow_credentials,
        allow_methods=config.allow_methods,
        allow_headers=config.allow_headers,
        expose_headers=config.expose_headers,
        max_age=config.max_age,
    )
