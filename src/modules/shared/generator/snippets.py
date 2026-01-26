# pyright: reportMissingImports=false

"""Cross-module snippet injection infrastructure."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import yaml

from . import TemplateRenderer

logger = logging.getLogger(__name__)


def _normalize_target_path(value: str) -> str:
    cleaned = value.strip().lstrip("./")
    cleaned = cleaned.replace("\\", "/")
    while cleaned.startswith("//"):
        cleaned = cleaned[1:]
    return cleaned


def _derive_aliases(value: str) -> List[str]:
    """Return helpful aliases for backwards compatibility."""
    aliases = {_normalize_target_path(value)}
    if value.startswith("src/"):
        aliases.add(_normalize_target_path(value[4:]))
    else:
        aliases.add(_normalize_target_path(f"src/{value}"))
    return sorted(alias for alias in aliases if alias)


@dataclass
class SnippetDefinition:
    """Loaded snippet definition from module metadata."""

    identifier: str
    source_module: str
    template_path: Path
    anchor: str
    targets: Sequence[str]
    variants: Sequence[str]
    priority: int
    features: Sequence[str]
    extra_context: Mapping[str, object] = field(default_factory=dict)

    _renderer: Optional[TemplateRenderer] = field(default=None, init=False, repr=False)

    def matches_target(self, target: str) -> bool:
        target_norm = _normalize_target_path(target)
        return any(target_norm == candidate for candidate in self.targets)

    def supports_variant(self, variant: Optional[str]) -> bool:
        if not self.variants:
            return True
        if variant is None:
            return False
        return variant in self.variants

    def render(self, context: Mapping[str, object]) -> str:
        if self._renderer is None:
            self._renderer = TemplateRenderer(self.template_path.parent)
        merged_context: Dict[str, object] = dict(context)
        merged_context.setdefault("snippet_module", self.source_module)
        for key, value in self.extra_context.items():
            merged_context.setdefault(key, value)
        return self._renderer.render(self.template_path, merged_context)


@dataclass
class RenderedSnippet:
    anchor: str
    content: str
    priority: int
    provider: str


class SnippetRegistry:
    """Discover snippet definitions and render contributions on demand."""

    def __init__(self) -> None:
        self._definitions: List[SnippetDefinition] = []
        self._loaded_root: Optional[Path] = None

    def ensure_loaded(self, project_root: Path) -> None:
        project_root = project_root.resolve()
        if self._loaded_root == project_root:
            return
        self._definitions = self._load_definitions(project_root)
        self._loaded_root = project_root

    def _load_definitions(self, project_root: Path) -> List[SnippetDefinition]:
        modules_root = project_root / "src" / "modules"
        if not modules_root.exists():
            logger.debug("Modules root %s not found; skipping snippet discovery", modules_root)
            return []

        definitions: List[SnippetDefinition] = []
        for config_path in modules_root.glob("**/config/snippets.yaml"):
            try:
                data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:  # pragma: no cover - defensive guard
                logger.warning("Failed to parse snippet config %s: %s", config_path, exc)
                continue

            snippets = data.get("snippets")
            if not isinstance(snippets, list):
                continue

            module_root = config_path.parent.parent
            module_name = module_root.relative_to(project_root).as_posix()

            for entry in snippets:
                if not isinstance(entry, dict):
                    continue
                identifier = str(entry.get("id") or entry.get("template") or config_path.stem)
                anchor = str(entry.get("anchor", "")).strip()
                template_name = entry.get("template")
                if not anchor or not template_name:
                    continue
                template_path = module_root / "templates" / "snippets" / template_name
                if not template_path.exists():
                    logger.debug("Skipping missing snippet template %s", template_path)
                    continue

                raw_targets = entry.get("target", "")
                targets: List[str] = []
                for target_value in str(raw_targets).split(","):
                    if not target_value.strip():
                        continue
                    targets.extend(_derive_aliases(target_value))
                if not targets:
                    continue

                profiles = entry.get("profiles") or []
                variants: List[str] = []
                for profile in profiles:
                    if not isinstance(profile, str):
                        continue
                    variant = profile.split("/", 1)[0].strip()
                    if variant:
                        variants.append(variant)
                priority = int(entry.get("priority", 0))
                features = tuple(entry.get("features") or ())
                extra_context = entry.get("context") or {}
                if not isinstance(extra_context, Mapping):
                    extra_context = {}

                definitions.append(
                    SnippetDefinition(
                        identifier=identifier,
                        source_module=module_name,
                        template_path=template_path,
                        anchor=anchor,
                        targets=tuple(dict.fromkeys(targets)),
                        variants=tuple(dict.fromkeys(variants)),
                        priority=priority,
                        features=tuple(features),
                        extra_context=dict(extra_context),
                    )
                )
        return definitions

    def render_for_target(
        self,
        *,
        project_root: Path,
        target: str,
        variant: Optional[str],
        context: Mapping[str, object],
        enabled_features: Optional[Iterable[str]] = None,
    ) -> Dict[str, List[RenderedSnippet]]:
        self.ensure_loaded(project_root)
        feature_set = set(enabled_features) if enabled_features is not None else None
        contributions: Dict[str, List[RenderedSnippet]] = {}

        for definition in self._definitions:
            if not definition.matches_target(target):
                continue
            if not definition.supports_variant(variant):
                continue
            if feature_set is not None and definition.features:
                if not set(definition.features).issubset(feature_set):
                    continue
            rendered = definition.render(context)
            if not rendered.strip():
                continue
            contributions.setdefault(definition.anchor, []).append(
                RenderedSnippet(
                    anchor=definition.anchor,
                    content=rendered.rstrip(),
                    priority=definition.priority,
                    provider=definition.identifier,
                )
            )

        for _anchor, snippets in contributions.items():
            snippets.sort(key=lambda item: item.priority, reverse=True)
        return contributions


_PATTERN_CACHE: Dict[str, re.Pattern[str]] = {}


def _anchor_pattern(anchor: str) -> re.Pattern[str]:
    cached = _PATTERN_CACHE.get(anchor)
    if cached is not None:
        return cached
    pattern = re.compile(rf"^(?P<indent>[ \t]*){re.escape(anchor)}\s*$", re.MULTILINE)
    _PATTERN_CACHE[anchor] = pattern
    return pattern


def apply_snippets(content: str, rendered: Mapping[str, Sequence[RenderedSnippet]]) -> str:
    result = content
    for anchor, snippets in rendered.items():
        if not snippets:
            continue
        pattern = _anchor_pattern(anchor)
        match = pattern.search(result)
        if not match:
            logger.debug("Anchor '%s' not found; skipping %d snippets", anchor, len(snippets))
            continue
        indent = match.group("indent").replace("\t", "    ")
        block_lines: List[str] = []
        for snippet in snippets:
            snippet_lines = snippet.content.strip("\n").splitlines()
            block_lines.extend(indent + line if line.strip() else indent for line in snippet_lines)
            block_lines.append("")
        while block_lines and not block_lines[-1].strip():
            block_lines.pop()
        replacement = match.group(0) + "\n" + "\n".join(block_lines)
        result = pattern.sub(replacement, result, count=1)
    return result


_global_registry = SnippetRegistry()


def get_snippet_registry() -> SnippetRegistry:
    return _global_registry
