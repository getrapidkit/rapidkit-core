"""
Module manifest schema and helpers for tiered licensing and signature.
"""

import json
from typing import Any, Dict, List, Optional


class ModuleManifest:
    def __init__(
        self,
        name: str,
        version: str,
        tier: str = "free",
        capabilities: Optional[List[str]] = None,
        signature: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.version = version
        self.tier = tier  # free | pro | enterprise
        self.capabilities = capabilities or []
        self.signature = signature
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "tier": self.tier,
            "capabilities": self.capabilities,
            "signature": self.signature,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModuleManifest":
        return cls(
            name=d["name"],
            version=d["version"],
            tier=d.get("tier", "free"),
            capabilities=d.get("capabilities", []),
            signature=d.get("signature"),
            extra={
                k: v
                for k, v in d.items()
                if k not in {"name", "version", "tier", "capabilities", "signature"}
            },
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, s: str) -> "ModuleManifest":
        return cls.from_dict(json.loads(s))
