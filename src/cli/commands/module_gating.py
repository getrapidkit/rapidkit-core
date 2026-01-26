from pathlib import Path
from typing import Optional, Union

import yaml

from cli.utils.pathing import resolve_modules_path, resolve_src_root
from core.kit_utils import validate_license_auto
from core.services.module_path_resolver import resolve_module_directory

# from ..utils.pathing import resolve_modules_path, resolve_src_root

MODULES_PATH = resolve_modules_path()
SRC_ROOT = resolve_src_root()
KITS_PATH = SRC_ROOT / "kits"
ADDONS_PATH = SRC_ROOT / "addons"


def enforce_module_gating(
    module_name: str,
    licenses_dir: Optional[str] = None,
    modules_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Enforce license gating for a module using the new license system.
    Accepts optional licenses_dir and modules_path for testability.
    """
    modules_base = Path(modules_path) if modules_path is not None else MODULES_PATH
    module_dir = resolve_module_directory(modules_base, module_name)
    mf = module_dir / "module.yaml"
    if not mf.exists():
        raise FileNotFoundError(f"Module {module_name} not found.")
    with open(mf) as f:
        manifest = yaml.safe_load(f)
    required_tier = manifest.get("tier")
    required_features = manifest.get("features")

    # Skip license check for free tier modules
    if required_tier == "free":
        return

    try:
        validate_license_auto(
            item_type="modules",
            item_name=module_name,
            required_tier=required_tier,
            required_features=required_features,
            licenses_dir=licenses_dir,
        )
    except Exception as e:
        # Preserve original traceback using 'from e'
        raise RuntimeError(f"Module '{module_name}' is gated: {e}") from e


def enforce_kit_gating(
    kit_name: str,
    licenses_dir: Optional[str] = None,
    kits_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Enforce license gating for a kit using the new license system.
    Accepts optional licenses_dir and kits_path for testability.
    """
    kits_base = Path(kits_path) if kits_path is not None else KITS_PATH
    kit_dir = kits_base / kit_name
    manifest_path = kit_dir / "kit.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Kit {kit_name} not found.")
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)
    required_tier = manifest.get("tier")
    required_features = manifest.get("features")
    try:
        validate_license_auto(
            item_type="kits",
            item_name=kit_name,
            required_tier=required_tier,
            required_features=required_features,
            licenses_dir=licenses_dir,
        )
    except Exception as e:
        # Preserve original traceback using 'from e'
        raise RuntimeError(f"Kit '{kit_name}' is gated: {e}") from e


def enforce_addon_gating(
    addon_name: str,
    licenses_dir: Optional[str] = None,
    addons_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Enforce license gating for an addon using the new license system.
    Accepts optional licenses_dir and addons_path for testability.
    """
    addons_base = Path(addons_path) if addons_path is not None else ADDONS_PATH
    addon_dir = addons_base / addon_name
    manifest_path = addon_dir / "addon.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Addon {addon_name} not found.")
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)
    required_tier = manifest.get("tier")
    required_features = manifest.get("features")
    try:
        validate_license_auto(
            item_type="addons",
            item_name=addon_name,
            required_tier=required_tier,
            required_features=required_features,
            licenses_dir=licenses_dir,
        )
    except Exception as e:
        # Preserve original traceback using 'from e'
        raise RuntimeError(f"Addon '{addon_name}' is gated: {e}") from e
