from typing import Any, Dict, List


def build_minimal_config_summary(cfg: Dict[str, Any], profile: str) -> str:
    """Return a compact, plain-text merged config summary (no color/boxes)."""
    name_ = cfg.get("name", "-")
    disp = cfg.get("display_name", "-")
    ver = cfg.get("version", "-")
    root = cfg.get("root_path", "-")

    # Active features for the selected profile
    feats_cfg = cfg.get("features", {}) or {}
    active_features: List[str] = []
    if isinstance(feats_cfg, dict):
        for feature_name, meta in feats_cfg.items():
            if meta is True:
                active_features.append(str(feature_name))
                continue
            if meta is False or meta is None:
                continue
            if isinstance(meta, dict) and profile in (meta.get("profiles") or []):
                active_features.append(str(feature_name))

    # Files from active features
    main_files: List[str] = []
    features_files = cfg.get("features_files", {}) or {}
    for feat in active_features:
        for entry in features_files.get(feat, []) or []:
            path = entry.get("path") if isinstance(entry, dict) else str(entry)
            if path:
                main_files.append(path)

    # Dependencies for the selected profile
    depends_on = cfg.get("depends_on", {}) or {}
    dep_names_raw = [
        d.get("name")
        for d in depends_on.get(profile, []) or []
        if isinstance(d, dict) and d.get("name")
    ]
    dep_names: List[str] = [str(n) for n in dep_names_raw if n is not None]

    # Compact, single-screen output
    lines = []
    lines.append(f"Merged Module Config — {name_} ({disp}) v{ver}")
    lines.append(f"Root: {root}")
    lines.append("Features: " + (", ".join(active_features) if active_features else "-"))
    if main_files:
        max_show = 6
        extra = len(main_files) - max_show
        shown = main_files[:max_show]
        files_line = ", ".join(shown) + (f", +{extra} more" if extra > 0 else "")
    else:
        files_line = "-"
    lines.append("Files: " + files_line)
    lines.append("Deps: " + (", ".join(dep_names) if dep_names else "-"))
    return "\n".join(lines)
