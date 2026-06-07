import shutil
from pathlib import Path

from modules.free.security.audit_policy import generate
from modules.shared.versioning import ensure_version_consistency


def _clone_module_root(source: Path, destination: Path) -> Path:
    ignore_names = {"__pycache__", ".pytest_cache"}

    def _ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignore_names}

    shutil.copytree(source, destination, ignore=_ignore)
    return destination


def test_audit_policy_version_consistency_no_bump(tmp_path: Path) -> None:
    module_root = Path(generate.__file__).resolve().parent
    isolated_root = _clone_module_root(module_root, tmp_path / "audit-policy-module")
    config = generate.load_module_config()

    updated_config, bumped = ensure_version_consistency(config, module_root=isolated_root)

    assert bumped is False
    assert updated_config["version"] == config["version"]
