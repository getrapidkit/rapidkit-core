"""Tests for Storage override functionality."""

import yaml

from modules.free.business.storage.overrides import StorageOverrideManager


def test_preserve_user_overrides_merges_python_definitions(tmp_path):
    module_root = tmp_path
    python_path = module_root / "src" / "modules" / "free" / "business" / "storage"
    python_path.mkdir(parents=True)
    override_file = python_path / "storage.py"
    override_file.write_text(
        "class GeneratedStorage:\n    pass\n\n"
        "class CustomStorage:\n    pass\n\n"
        "def helper_function():\n    return 'user'\n",
        encoding="utf-8",
    )

    manager = StorageOverrideManager(module_root)
    preserved = manager.preserve_user_overrides(
        {"src/modules/free/business/storage/storage.py": "class GeneratedStorage:\n    pass"}
    )

    merged_content = preserved["src/modules/free/business/storage/storage.py"]
    assert "class GeneratedStorage" in merged_content
    assert "class CustomStorage" in merged_content
    assert "def helper_function" in merged_content


def test_preserve_user_overrides_merges_yaml(tmp_path):
    module_root = tmp_path
    config_path = module_root / "config"
    config_path.mkdir()
    override_file = config_path / "storage_custom.yaml"
    override_file.write_text(
        "bucket: user-bucket\nnested:\n  override: true\n",
        encoding="utf-8",
    )

    manager = StorageOverrideManager(module_root)
    preserved = manager.preserve_user_overrides(
        {"config/storage_custom.yaml": ("bucket: generated\nnested:\n  default: true\n")}
    )

    merged = yaml.safe_load(preserved["config/storage_custom.yaml"])
    assert merged["bucket"] == "user-bucket"
    assert merged["nested"]["default"] is True
    assert merged["nested"]["override"] is True


def test_validate_overrides_reports_errors_and_warnings(tmp_path):
    module_root = tmp_path
    python_path = module_root / "src" / "modules" / "free" / "business" / "storage"
    python_path.mkdir(parents=True)
    (python_path / "storage.py").write_text("def broken(:\n    pass\n", encoding="utf-8")

    ts_path = python_path
    (ts_path / "storage.service.ts").write_text("const value = 1;\n", encoding="utf-8")

    manager = StorageOverrideManager(module_root)
    results = manager.validate_overrides()

    assert any(result.startswith("Invalid Python") for result in results["errors"])
    assert any(result.startswith("Possible TypeScript") for result in results["warnings"])


def test_get_override_and_backup_collect_user_files(tmp_path):
    module_root = tmp_path
    ts_path = module_root / "src" / "modules" / "free" / "business" / "storage"
    ts_path.mkdir(parents=True)
    controller_path = ts_path / "storage.controller.ts"
    controller_content = "export class StorageController {}\n"
    controller_path.write_text(controller_content, encoding="utf-8")

    manager = StorageOverrideManager(module_root)

    retrieved = manager.get_override("src/modules/free/business/storage/storage.controller.ts")
    assert retrieved == controller_content

    backups = manager.backup_user_files()
    assert backups["src/modules/free/business/storage/storage.controller.ts"] == controller_content
