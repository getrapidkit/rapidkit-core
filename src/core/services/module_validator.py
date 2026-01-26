"""Enterprise-grade module schema & validation utilities.

Lightweight now (Pydantic models) but intentionally extensible:
 - Preserves unknown keys (future forward-compat) via `extra = "allow"`.
 - Normalizes optional sections to canonical empty dict/list so downstream code
   can rely on attributes existing.
 - Provides helper for brace expansion (future use for snippet targets).

This does NOT replace existing `ModuleManifest` (used for legacy minimal graph);
we layer on top for richer commands (summary/validate) without breaking add flow.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # Pydantic v2
    from pydantic import BaseModel, ConfigDict, Field

    _PYDANTIC_V2 = True
except ImportError:  # pragma: no cover - fallback for v1
    from pydantic import BaseModel, Field

    _PYDANTIC_V2 = False
import yaml


class ChangelogEntry(BaseModel):
    version: str
    date: Optional[date] = None
    # Changelog in module.yaml may be either a stub entry (notes-only) or a
    # structured list of change objects; full history usually lives in
    # docs/changelog.md.
    notes: Optional[str] = None
    changes: Optional[Any] = None

    if _PYDANTIC_V2:  # pragma: no branch
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover

        class Config:  # noqa: D401 - simple config container
            extra = "allow"


class SnippetSpec(BaseModel):
    target: Any  # string | list | brace expression; keep flexible
    anchor: Any
    template: str
    profiles: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    mode: Optional[str] = None  # append | replace | anchor (future)

    if _PYDANTIC_V2:  # pragma: no branch
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover - only executed under Pydantic v1

        class Config:  # noqa: D401 - simple config container
            extra = "allow"


class ModuleRichSpec(BaseModel):
    name: str
    display_name: Optional[str] = None
    version: str = "0.1.0"
    status: str = "active"  # active|experimental|placeholder|deprecated
    access: str = "free"  # free|commercial|internal
    maturity: str = "stable"  # alpha|beta|stable|legacy
    description: Optional[str] = None
    profiles: List[str] = Field(default_factory=list)
    license: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    profile_inherits: Dict[str, str] = Field(default_factory=dict)
    depends_on: Any = Field(default_factory=lambda: [])  # list or mapping (profile->deps)
    variables: Dict[str, Any] = Field(default_factory=dict)
    features: Dict[str, Any] = Field(default_factory=dict)  # feature -> profiles list OR metadata
    files: Dict[str, Any] = Field(default_factory=dict)
    snippets: List[SnippetSpec] = Field(default_factory=list)
    migrations: List[Dict[str, Any]] = Field(default_factory=list)
    docs: List[Dict[str, Any]] = Field(default_factory=list)
    changelog: List[ChangelogEntry] = Field(default_factory=list)
    ci_cd: Any = Field(default_factory=lambda: {})
    unit_tests: Dict[str, Any] = Field(default_factory=lambda: {})
    e2e_tests: Dict[str, Any] = Field(default_factory=lambda: {})
    security_tests: Dict[str, Any] = Field(default_factory=lambda: {})
    performance_tests: Dict[str, Any] = Field(default_factory=lambda: {})
    features_files: Dict[str, Any] = Field(default_factory=lambda: {})
    root_path: str = ""

    if _PYDANTIC_V2:  # pragma: no branch
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover

        class Config:  # noqa: D401 - simple config container
            extra = "allow"  # keep forward compatibility

    @property
    def effective_name(self) -> str:
        return self.display_name or self.name

    @property
    def feature_count(self) -> int:
        return len(self.features or {})

    @property
    def dependency_count(self) -> int:
        # supports list OR mapping style
        deps = getattr(self, "depends_on", None)
        if isinstance(deps, list):
            return len(deps)
        if isinstance(deps, dict):
            # flatten unique
            uniq = set()
            for v in deps.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            uniq.add(item)
                        elif isinstance(item, dict):
                            uniq.add(next(iter(item.keys()), "?"))
            return len(uniq)
        return 0


def load_rich_spec(path: Path) -> ModuleRichSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    spec = ModuleRichSpec(**data)
    return spec


def load_all_specs(modules_root: Path) -> Dict[str, ModuleRichSpec]:
    specs: Dict[str, ModuleRichSpec] = {}
    for module_dir in modules_root.iterdir():
        if not module_dir.is_dir():
            continue
        mf = module_dir / "module.yaml"
        if mf.exists():
            try:
                specs[module_dir.name] = load_rich_spec(mf)
            except (OSError, ValueError):
                # skip invalid; validation command will surface details when invoked
                continue
    return specs


def validate_spec(path: Path) -> List[str]:
    """Return list of validation error messages (empty if valid)."""
    try:
        spec = load_rich_spec(path)
        errors: List[str] = []
        # profile inheritance validation (detect unknown or cycles)
        graph = spec.profile_inherits or {}
        for child, parent in graph.items():
            if child not in spec.profiles:
                errors.append(f"profile_inherits: child '{child}' not in profiles list")
            if parent not in spec.profiles:
                errors.append(f"profile_inherits: parent '{parent}' not in profiles list")
        # cycle detection
        visiting = set()
        visited = set()

        def dfs(n: str) -> bool:
            if n in visited:
                return False
            if n in visiting:
                return True  # cycle
            visiting.add(n)
            p = graph.get(n)
            if p and dfs(p):
                return True
            visiting.remove(n)
            visited.add(n)
            return False

        for node in graph:
            if dfs(node):
                errors.append("profile_inherits: cycle detected")
                break
        if errors:
            return errors
        return []
    except (ValueError, TypeError) as e:  # pydantic ValidationError or other
        return [str(e)]
