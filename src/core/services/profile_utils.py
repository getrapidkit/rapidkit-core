from typing import Any, Dict, List


def profile_aliases(profile: str) -> List[str]:
    """Return canonical alias forms for a profile identifier."""

    aliases: List[str] = []

    def _add(candidate: str) -> None:
        if candidate and candidate not in aliases:
            aliases.append(candidate)

    _add(profile)
    if "/" in profile:
        _add(profile.replace("/", "."))
    if "." in profile:
        _add(profile.replace(".", "/"))

    return aliases


def resolve_profile_chain(profile: str, profiles_config: Dict[str, Any]) -> List[str]:
    """Resolve inheritance chain for a given profile, supporting dict and list metadata."""

    visited = set()
    chain: List[str] = []
    current = profile

    while current:
        current_clean = current.split(":")[0].strip()
        if not current_clean:
            break

        profiles_section = profiles_config.get("profiles")
        inherited_profile: str | None = None
        resolved_key = current_clean

        if isinstance(profiles_section, dict):
            entry = None
            for alias in profile_aliases(current_clean):
                candidate = profiles_section.get(alias)
                if isinstance(candidate, dict):
                    entry = candidate
                    resolved_key = alias
                    break
            if isinstance(entry, dict):
                maybe_inherits = entry.get("inherits")
                if isinstance(maybe_inherits, str) and maybe_inherits:
                    inherited_profile = maybe_inherits.strip()
        elif isinstance(profiles_section, list):
            for raw_profile in profiles_section:
                if not isinstance(raw_profile, str):
                    continue
                segment = raw_profile.split(":", 1)
                name = segment[0].strip()
                for alias in profile_aliases(current_clean):
                    if name == alias:
                        resolved_key = name
                        if "inherits" in raw_profile:
                            inherited_profile = raw_profile.split("inherits", 1)[-1].strip()
                        break
                if resolved_key == name:
                    break

        if resolved_key in visited:
            break

        visited.add(resolved_key)
        chain.insert(0, resolved_key)

        if inherited_profile:
            current = inherited_profile
            continue

        break

    return chain
