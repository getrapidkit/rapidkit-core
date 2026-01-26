"""Module manifest loading & validation.

Phase 1: lightweight Pydantic parsing for module metadata (versioning, status, profiles).
Designed so richer schema (dependencies graph, hooks) can be layered later without
breaking existing call sites.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from core.services.module_path_resolver import resolve_module_directory

try:  # Pydantic v2
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    _PYDANTIC_V2 = True
except ImportError:  # pragma: no cover
    from pydantic import BaseModel, Field, ValidationError

    _PYDANTIC_V2 = False
import yaml

ManifestStatus = Literal[
    "active",
    "stable",
    "beta",
    "draft",
    "experimental",
    "planned",
    "legacy",
    "placeholder",
    "deprecated",
]


class ModuleManifest(BaseModel):
    # Canonical identifier for dependency graphs (e.g. "free/database/db_postgres").
    # Derived from the manifest path; not required in module.yaml.
    slug: str = ""
    name: str
    version: str = "0.1.0"
    status: ManifestStatus = "active"
    description: Optional[str] = None
    display_name: Optional[str] = None
    profiles: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(
        default_factory=list, description="Module names this module depends on"
    )
    raw: Dict[str, Any] = Field(default_factory=dict, description="Unknown / passthrough sections")

    if _PYDANTIC_V2:  # pragma: no branch
        # Allow unknown keys routed into raw via manual extraction; base model should forbid extras implicitly
        model_config = ConfigDict(extra="forbid")
    else:  # pragma: no cover - v1 path

        class Config:
            pass
            extra = "forbid"

    @property
    def effective_name(self) -> str:
        return self.display_name or self.name

    @classmethod
    def load(cls, path: Path) -> "ModuleManifest":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        # Extract known keys; everything else -> raw
        known = {}
        raw: Dict[str, Any] = {}
        for k, v in data.items():
            if k in {
                "name",
                "version",
                "status",
                "description",
                "display_name",
                "profiles",
                "depends_on",
            }:
                known[k] = v
            else:
                raw[k] = v
        try:
            manifest = cls(**known, raw=raw)
        except ValidationError as e:
            raise RuntimeError(f"Invalid module manifest '{path}': {e}") from e
        return manifest


def find_manifest(modules_root: Path, module_name: str) -> Optional[Path]:
    module_dir = resolve_module_directory(modules_root, module_name)
    candidate = module_dir / "module.yaml"
    return candidate if candidate.exists() else None


def load_manifest_or_none(modules_root: Path, module_name: str) -> Optional[ModuleManifest]:
    p = find_manifest(modules_root, module_name)
    if not p:
        return None
    manifest = ModuleManifest.load(p)
    slug = _slug_from_manifest_path(modules_root, p)
    return _with_slug(manifest, slug)


class DependencyCycleError(RuntimeError):
    pass


class DependencyResolutionError(RuntimeError):
    pass


def _with_slug(manifest: ModuleManifest, slug: str) -> ModuleManifest:
    if not slug:
        return manifest
    if _PYDANTIC_V2:
        return manifest.model_copy(update={"slug": slug})
    return manifest.copy(update={"slug": slug})


def _slug_from_manifest_path(modules_root: Path, manifest_path: Path) -> str:
    """Compute canonical module slug from a module.yaml path."""

    try:
        rel = manifest_path.parent.resolve().relative_to(modules_root.resolve())
    except (OSError, ValueError):
        try:
            rel = manifest_path.parent.relative_to(modules_root)
        except ValueError:
            return ""
    return rel.as_posix().strip("/")


def load_all_manifests(modules_root: Path) -> Dict[str, ModuleManifest]:
    manifests: Dict[str, ModuleManifest] = {}
    for manifest_path in modules_root.rglob("module.yaml"):
        if not manifest_path.is_file():
            continue
        try:
            m = ModuleManifest.load(manifest_path)
            slug = _slug_from_manifest_path(modules_root, manifest_path)
            if not slug:
                continue
            manifests[slug] = _with_slug(m, slug)
        except (OSError, RuntimeError, ValueError):
            continue
    return manifests


def topo_sort_modules(manifests: Dict[str, ModuleManifest]) -> List[ModuleManifest]:
    # Kahn's algorithm
    incoming: Dict[str, Set[str]] = {}
    outgoing: Dict[str, Set[str]] = {}
    for name, m in manifests.items():
        deps = set(m.depends_on or [])
        incoming[name] = deps.copy()
        for d in deps:
            outgoing.setdefault(d, set()).add(name)
        outgoing.setdefault(name, set())
    ready = [n for n, deps in incoming.items() if not deps]
    ordered: List[str] = []
    while ready:
        n = ready.pop()
        ordered.append(n)
        for succ in outgoing.get(n, set()):
            inc = incoming[succ]
            if n in inc:
                inc.remove(n)
                if not inc:
                    ready.append(succ)
    if len(ordered) != len(incoming):
        # cycle detection: nodes with remaining deps
        cyclic = [n for n, deps in incoming.items() if deps]
        raise DependencyCycleError(f"Dependency cycle detected: {' -> '.join(cyclic)}")
    return [manifests[n] for n in ordered]


def compute_install_order(
    targets: List[str], manifests: Dict[str, ModuleManifest]
) -> List[ModuleManifest]:
    # restrict graph to closure of targets
    needed: Set[str] = set()

    def dfs(n: str) -> None:
        if n in needed:
            return
        if n not in manifests:
            raise DependencyResolutionError(
                f"Unknown module slug '{n}' in dependency graph (missing module.yaml)"
            )
        needed.add(n)
        m = manifests[n]
        for dep in m.depends_on:
            if dep not in manifests:
                raise DependencyResolutionError(
                    f"Unknown dependency slug '{dep}' required by '{n}' (missing module.yaml)"
                )
            dfs(dep)

    for t in targets:
        dfs(t)
    sub = {k: v for k, v in manifests.items() if k in needed}
    ordered = topo_sort_modules(sub)
    # keep only those whose slug in needed and order precedence respected
    return [m for m in ordered if m.slug in needed]
