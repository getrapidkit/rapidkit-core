from typing import Optional

_STATUS_MISSING = "missing"
_STATUS_NEW_TEMPLATE = "new_template"
_STATUS_UNKNOWN = "unknown"
_STATUS_UNTRACKED = "untracked_existing"
_STATUS_CLEAN = "clean"
_STATUS_TEMPLATE_UPDATED = "template_updated"
_STATUS_LOCALLY_MODIFIED = "locally_modified"
_STATUS_MANUALLY_UPDATED = "manually_updated"
_STATUS_DIVERGED = "diverged"


def classify_file_status(
    dst_exists: bool,
    registry_hash: Optional[str],
    current_hash: Optional[str],
    regenerated_hash: Optional[str],
) -> str:
    """Classify file status comparing registry, current, and regenerated template hashes.

    Returns one of predefined status constants.
    """
    status = _STATUS_UNKNOWN
    if not dst_exists:
        if registry_hash:
            status = _STATUS_MISSING
        else:
            status = _STATUS_NEW_TEMPLATE if regenerated_hash else _STATUS_UNKNOWN
    elif not registry_hash:
        # Legacy/initial projects may not have a registry yet. If the file exists
        # and there's no registry entry we treat it as untracked by default.
        # If we can regenerate a template and compare to the current file, we
        # only mark it as locally modified when different; when equal we still
        # consider it an untracked existing file (registry absent).
        if dst_exists and regenerated_hash and current_hash:
            status = (
                _STATUS_UNTRACKED if regenerated_hash == current_hash else _STATUS_LOCALLY_MODIFIED
            )
        else:
            status = _STATUS_UNTRACKED
    else:
        hashes_equal = current_hash == registry_hash
        if not regenerated_hash:
            status = _STATUS_CLEAN if hashes_equal else _STATUS_LOCALLY_MODIFIED
        else:
            template_equal_registry = regenerated_hash == registry_hash
            template_equal_current = regenerated_hash == current_hash
            if hashes_equal:
                status = _STATUS_CLEAN if template_equal_registry else _STATUS_TEMPLATE_UPDATED
            elif template_equal_registry:
                status = _STATUS_LOCALLY_MODIFIED
            elif template_equal_current:
                status = _STATUS_MANUALLY_UPDATED
            else:
                status = _STATUS_DIVERGED
    return status
