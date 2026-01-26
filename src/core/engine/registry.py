# src / core / engine / registry.py
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Type

import yaml

from core.config.kit_config import KitConfig
from core.engine.generator import BaseKitGenerator
from core.exceptions import InvalidKitError, KitNotFoundError


class KitRegistry:
    """Central registry for managing all available kits"""

    def __init__(self) -> None:
        self._kits: Dict[str, KitConfig] = {}
        self._generators: Dict[str, Type[BaseKitGenerator]] = {}
        self._shared_variables: Dict[str, Dict[str, Any]] = self._load_shared_variables()
        self._load_kits()

    def _load_kits(self) -> None:
        """Load all kits from the kits directory recursively"""
        kits_dir = Path(__file__).parent.parent.parent / "kits"

        for kit_yaml in kits_dir.rglob("kit.yaml"):
            try:
                kit_dir = kit_yaml.parent
                self._load_kit(kit_dir)
            except (OSError, ImportError, RuntimeError) as e:
                print(f"Warning: Failed to load kit at {kit_yaml}: {e}")

    def _load_kit(self, kit_dir: Path) -> None:
        kit_yaml = kit_dir / "kit.yaml"
        generator_py = kit_dir / "generator.py"

        if not kit_yaml.exists():
            raise InvalidKitError(f"kit.yaml not found in {kit_dir}")

        if not generator_py.exists():
            raise InvalidKitError(f"generator.py not found in {kit_dir}")

        with open(kit_yaml, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        if not isinstance(config_data, dict):
            raise InvalidKitError(f"Invalid kit.yaml structure in {kit_dir}")

        kit_variables = config_data.get("variables", {}) or {}
        merged_variables = self._merge_variables(kit_variables)
        config_data["variables"] = merged_variables

        config = KitConfig.from_dict(config_data)
        config.path = kit_dir

        # Load generator class
        spec = importlib.util.spec_from_file_location(f"{kit_dir.name}.generator", generator_py)
        if not spec or not spec.loader:  # defensive guard for mypy/runtime
            raise ImportError(f"Failed to load spec for generator in {kit_dir}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        generator_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseKitGenerator)
                and attr != BaseKitGenerator
            ):
                generator_class = attr
                break

        if not generator_class:
            raise InvalidKitError(f"No generator class found in {kit_dir}/generator.py")

        main_name = config.name.lower()
        if main_name in self._kits:
            return
        self._kits[main_name] = config
        self._generators[main_name] = generator_class

        for alias in config_data.get("aliases", []):
            alias_key = alias.lower().replace(" ", ".")
            if alias_key in self._kits:
                continue
            self._kits[alias_key] = config
            self._generators[alias_key] = generator_class

    def _load_shared_variables(self) -> Dict[str, Dict[str, Any]]:
        shared_path = Path(__file__).parent.parent.parent / "kits" / "shared" / "variables.yaml"
        if not shared_path.exists():
            return {}
        try:
            raw = yaml.safe_load(shared_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return {}
        if not isinstance(raw, dict):
            return {}
        normalized: Dict[str, Dict[str, Any]] = {}
        for key, value in raw.items():
            if isinstance(key, str) and isinstance(value, dict):
                normalized[key] = dict(value)
        return normalized

    def _merge_variables(self, kit_specific: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {name: dict(meta) for name, meta in self._shared_variables.items()}
        for name, meta in kit_specific.items():
            if name in merged and isinstance(merged[name], dict) and isinstance(meta, dict):
                merged[name].update(meta)
            else:
                merged[name] = meta
        return merged

    def get_kit(self, kit_name: str) -> KitConfig:
        """Get kit configuration by name"""
        if kit_name not in self._kits:
            raise KitNotFoundError(f"Kit '{kit_name}' not found")
        return self._kits[kit_name]

    def get_generator(self, kit_name: str) -> BaseKitGenerator:
        """Get generator instance for a kit"""
        if kit_name not in self._generators:
            raise KitNotFoundError(f"Generator for kit '{kit_name}' not found")

        config = self.get_kit(kit_name)
        if config.path is None:
            raise KitNotFoundError(f"Kit '{kit_name}' loaded without path; invalid configuration")
        generator_cls = self._generators[kit_name]
        return generator_cls(config.path, config)

    def list_kits(self) -> List[KitConfig]:
        """List all available kits"""
        return list(self._kits.values())

    def kit_exists(self, kit_name: str) -> bool:
        """Check if a kit exists"""
        return kit_name in self._kits

    def list_kits_names(self) -> List[str]:
        return list(self._kits.keys())
