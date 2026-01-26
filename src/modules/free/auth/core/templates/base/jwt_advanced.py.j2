"""Advanced JWT utilities for enterprise authentication scenarios."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union

from .core import AuthCoreRuntime, _base64url, _base64url_decode

logger = logging.getLogger("src.modules.free.auth.core.auth.jwt_advanced")


@dataclass(frozen=True)
class JWTClaims:
    """Standard and custom JWT claims structure."""

    # Standard claims (RFC 7519)
    iss: Optional[str] = None  # Issuer
    sub: Optional[str] = None  # Subject
    aud: Optional[Union[str, List[str]]] = None  # Audience
    exp: Optional[int] = None  # Expiration Time
    nbf: Optional[int] = None  # Not Before
    iat: Optional[int] = None  # Issued At
    jti: Optional[str] = None  # JWT ID

    # Custom claims
    scopes: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert claims to dictionary for JWT payload."""
        result = {}

        # Standard claims
        if self.iss is not None:
            result["iss"] = self.iss
        if self.sub is not None:
            result["sub"] = self.sub
        if self.aud is not None:
            result["aud"] = self.aud
        if self.exp is not None:
            result["exp"] = self.exp
        if self.nbf is not None:
            result["nbf"] = self.nbf
        if self.iat is not None:
            result["iat"] = self.iat
        if self.jti is not None:
            result["jti"] = self.jti

        # Custom claims
        if self.scopes:
            result["scopes"] = self.scopes
        if self.roles:
            result["roles"] = self.roles
        if self.permissions:
            result["permissions"] = self.permissions
        if self.tenant_id:
            result["tenant_id"] = self.tenant_id
        if self.device_id:
            result["device_id"] = self.device_id
        if self.session_id:
            result["session_id"] = self.session_id

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTClaims":
        """Create claims from dictionary."""
        return cls(
            iss=data.get("iss"),
            sub=data.get("sub"),
            aud=data.get("aud"),
            exp=data.get("exp"),
            nbf=data.get("nbf"),
            iat=data.get("iat"),
            jti=data.get("jti"),
            scopes=data.get("scopes"),
            roles=data.get("roles"),
            permissions=data.get("permissions"),
            tenant_id=data.get("tenant_id"),
            device_id=data.get("device_id"),
            session_id=data.get("session_id"),
        )


class JWTAdvancedRuntime:
    """Advanced JWT operations extending core functionality."""

    def __init__(self, core_runtime: AuthCoreRuntime) -> None:
        self.core = core_runtime
        self._revoked_tokens: Set[str] = set()

    def issue_access_token(
        self,
        subject: str,
        *,
        audience: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        device_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """Issue an access token with standard and custom claims."""
        now = int(time.time())
        exp = now + (ttl_seconds or self.core.settings.token_ttl_seconds)

        claims = JWTClaims(
            iss=self.core.settings.issuer,
            sub=subject,
            aud=audience,
            exp=exp,
            iat=now,
            jti=self._generate_jti(),
            scopes=scopes,
            roles=roles,
            permissions=permissions,
            tenant_id=tenant_id,
            device_id=device_id,
            session_id=session_id,
        )

        return self._encode_jwt(claims)

    def issue_refresh_token(
        self,
        subject: str,
        *,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        ttl_seconds: int = 86400 * 30,  # 30 days default
    ) -> str:
        """Issue a refresh token with minimal claims."""
        now = int(time.time())
        exp = now + ttl_seconds

        claims = JWTClaims(
            iss=self.core.settings.issuer,
            sub=subject,
            aud="refresh",
            exp=exp,
            iat=now,
            jti=self._generate_jti(),
            session_id=session_id,
            device_id=device_id,
        )

        return self._encode_jwt(claims)

    def verify_access_token(
        self,
        token: str,
        *,
        required_scopes: Optional[List[str]] = None,
        required_roles: Optional[List[str]] = None,
        required_audience: Optional[str] = None,
    ) -> JWTClaims:
        """Verify access token with additional validation."""
        payload = self.core.verify_token(token)
        claims = JWTClaims.from_dict(payload)

        # Check if token is revoked
        jti = claims.jti or self._extract_jti_from_token(token)
        if jti and jti in self._revoked_tokens:
            raise ValueError("Token has been revoked")

        # Validate audience
        if required_audience and claims.aud != required_audience:
            raise ValueError(f"Token audience mismatch: expected {required_audience}")

        # Validate scopes
        if required_scopes:
            token_scopes = set(claims.scopes or [])
            required_scopes_set = set(required_scopes)
            if not required_scopes_set.issubset(token_scopes):
                missing = required_scopes_set - token_scopes
                raise ValueError(f"Token missing required scopes: {missing}")

        # Validate roles
        if required_roles:
            token_roles = set(claims.roles or [])
            required_roles_set = set(required_roles)
            if not required_roles_set.intersection(token_roles):
                raise ValueError(f"Token missing required roles: {required_roles}")

        return claims

    def revoke_token(self, token: str) -> None:
        """Add token to revocation list."""
        jti = self._extract_jti_from_token(token)
        if jti:
            self._revoked_tokens.add(jti)

    def revoke_all_user_tokens(self, subject: str) -> None:
        """Revoke all tokens for a specific user (requires external session store)."""
        # This would typically integrate with Redis or database
        # For now, we'll log the action
        logger.info(f"Revocation requested for all tokens of subject: {subject}")

    def _encode_jwt(self, claims: JWTClaims) -> str:
        """Encode JWT with claims."""
        payload = claims.to_dict()

        header = {"alg": "HS256", "typ": "JWT"}
        header_segment = _base64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_segment = _base64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        signature = _base64url(self.core._sign(signing_input))

        return f"{header_segment}.{payload_segment}.{signature}"

    def _extract_jti_from_token(self, token: str) -> Optional[str]:
        """Extract JTI from token without full verification."""
        try:
            _, payload_b64, _ = token.split(".")
            payload_json = _base64url_decode(payload_b64)
            payload = json.loads(payload_json)
            return payload.get("jti")
        except Exception:
            return None

    def _generate_jti(self) -> str:
        """Generate a unique token identifier."""
        return uuid.uuid4().hex


__all__ = [
    "JWTClaims",
    "JWTAdvancedRuntime",
]
