from __future__ import annotations

import json
from pathlib import Path

from core.services.snippet_injector import (
    inject_snippet_enterprise,
    reconcile_pending_snippets,
    reconcile_pending_snippets_scoped,
)


def test_settings_fields_missing_file_records_pending(tmp_path: Path):
    # Simulate a module trying to inject settings-fields before the Settings module exists.
    target = tmp_path / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    assert not target.exists()

    snippet_template = tmp_path / "settings_fields.snippet.j2"
    snippet_template.write_text("MY_SETTING: str = 'x'\n", encoding="utf-8")

    res = inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "db_postgres_settings_fields",
            "version": "1.0.0",
            "priority": 5,
            "template": "settings_fields.snippet.j2",
            "module_slug": "free/database/db_postgres",
            "context": {"database_url": "postgresql://..."},
            "conflict_resolution": "merge",
        },
        project_root=tmp_path,
        lenient=False,
    )

    assert res["injected"] is False
    assert res["blocked"] is True

    reg_path = tmp_path / ".rapidkit" / "snippet_registry.json"
    assert reg_path.exists()
    payload = json.loads(reg_path.read_text(encoding="utf-8"))
    entry = payload["snippets"]["db_postgres_settings_fields::settings.py"]
    assert entry["status"] == "pending"
    assert entry["module_slug"] == "free/database/db_postgres"
    assert entry["template"] == "settings_fields.snippet.j2"
    assert entry["file"].endswith("src/modules/free/essentials/settings/settings.py")


def test_audit_log_written_on_snippet_registry_update(tmp_path: Path):
    target = tmp_path / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    snippet_template = tmp_path / "settings_fields.snippet.j2"
    snippet_template.write_text("MY_SETTING: str = 'x'\n", encoding="utf-8")

    inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "db_postgres_settings_fields",
            "version": "1.0.0",
            "priority": 5,
            "template": "settings_fields.snippet.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "merge",
        },
        project_root=tmp_path,
        lenient=False,
    )

    audit_path = tmp_path / ".rapidkit" / "audit" / "snippet_injections.jsonl"
    assert audit_path.exists()
    lines = [ln for ln in audit_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1
    events = [json.loads(ln) for ln in lines]
    assert any(
        e.get("event") == "snippet_injection_state"
        and e.get("key") == "db_postgres_settings_fields::settings.py"
        and e.get("status") == "pending"
        for e in events
    )


def test_reconcile_applies_pending_once_target_exists(tmp_path: Path):
    # Arrange: create pending entry by injecting before Settings exists.
    target = tmp_path / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    snippet_template = tmp_path / "settings_fields.snippet.j2"
    snippet_template.write_text("DB_URL: str = 'postgresql://...'\n", encoding="utf-8")

    inject_snippet_enterprise(
        destination_path=target,
        template_path=snippet_template,
        anchor="# <<<inject:settings-fields>>>",
        variables={},
        snippet_metadata={
            "id": "db_postgres_settings_fields",
            "version": "1.0.0",
            "priority": 5,
            "template": "settings_fields.snippet.j2",
            "module_slug": "free/database/db_postgres",
            "context": {},
            "conflict_resolution": "merge",
        },
        project_root=tmp_path,
        lenient=False,
    )

    # Now simulate Settings being installed later (file + anchor exist).
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# header\n# <<<inject:settings-fields>>>\n", encoding="utf-8")

    # Provide a fake modules tree so reconcile can locate the template by module_slug.
    modules_root = tmp_path / "modules"
    tpl = (
        modules_root
        / "free"
        / "database"
        / "db_postgres"
        / "templates"
        / "snippets"
        / "settings_fields.snippet.j2"
    )
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text("DB_URL: str = 'postgresql://reconciled'\n", encoding="utf-8")

    stats = reconcile_pending_snippets(tmp_path, modules_root=modules_root, lenient=False)
    assert stats["pending_before"] == 1
    assert stats["applied"] == 1
    assert stats["pending_after"] == 0

    out = target.read_text(encoding="utf-8")
    assert "<<<inject:settings-fields:db_postgres_settings_fields:start>>>" in out
    assert "postgresql://reconciled" in out

    payload = json.loads(
        (tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8")
    )
    entry = payload["snippets"]["db_postgres_settings_fields::settings.py"]
    assert entry["status"] == "applied"


def test_reconcile_preserves_conflicted_status_on_malformed_block(tmp_path: Path):
    # Arrange: a pending snippet whose target file already contains a malformed
    # marker block (start without end). This should be marked as `conflicted`,
    # not overwritten back to `pending`.
    target = tmp_path / "app.py"
    target.write_text(
        "# <<<inject:settings-fields>>>\n" "# <<<inject:settings-fields:x:start>>>\n" "X = 0\n",
        encoding="utf-8",
    )

    (tmp_path / ".rapidkit").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".rapidkit" / "snippet_registry.json").write_text(
        json.dumps(
            {
                "snippets": {
                    "x::app.py": {
                        "status": "pending",
                        "file": "app.py",
                        "anchor": "# <<<inject:settings-fields>>>",
                        "version": "1.0.0",
                        "priority": 1,
                        "template": "t.j2",
                        "module_slug": "free/some/module",
                        "context": {},
                        "schema": {},
                        "conflict_resolution": "override",
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (tmp_path / "registry.json").write_text(
        json.dumps({"installed_modules": [{"slug": "free/some/module"}]}, indent=2),
        encoding="utf-8",
    )

    modules_root = tmp_path / "modules"
    tpl = modules_root / "free" / "some" / "module" / "templates" / "snippets" / "t.j2"
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text("X = 1\n", encoding="utf-8")

    stats = reconcile_pending_snippets(tmp_path, modules_root=modules_root)
    assert stats["pending_before"] == 1
    assert stats["applied"] == 0
    assert stats["pending_after"] == 0
    assert stats["failed"] == 0

    payload = json.loads(
        (tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8")
    )
    assert payload["snippets"]["x::app.py"]["status"] == "conflicted"


def test_reconcile_skips_when_producer_module_not_installed(tmp_path: Path):
    # Pending entry exists, but registry.json says producer module isn't installed.
    target = tmp_path / "app.py"
    target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    # Create a pending entry (not using the injector to avoid auto-applied state).
    (tmp_path / ".rapidkit").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".rapidkit" / "snippet_registry.json").write_text(
        json.dumps(
            {
                "snippets": {
                    "x::app.py": {
                        "status": "pending",
                        "file": "app.py",
                        "anchor": "# <<<inject:settings-fields>>>",
                        "version": "1.0.0",
                        "priority": 1,
                        "template": "t.j2",
                        "module_slug": "free/some/module",
                        "context": {},
                        "schema": {},
                        "conflict_resolution": "override",
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    # registry.json does not include the producer module
    (tmp_path / "registry.json").write_text(
        json.dumps({"installed_modules": [{"slug": "free/other/module"}]}, indent=2),
        encoding="utf-8",
    )

    stats = reconcile_pending_snippets(tmp_path, modules_root=tmp_path / "modules")
    assert stats["pending_before"] == 1
    assert stats["applied"] == 0
    assert stats["pending_after"] == 1
    assert stats["skipped"] == 1


def test_reconcile_keeps_settings_fields_pending_until_settings_installed(tmp_path: Path):
    # Target exists and is inject-able, but the *owner module* isn't installed => keep pending.
    settings_target = (
        tmp_path / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    )
    settings_target.parent.mkdir(parents=True, exist_ok=True)
    settings_target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    (tmp_path / ".rapidkit").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".rapidkit" / "snippet_registry.json").write_text(
        json.dumps(
            {
                "snippets": {
                    "db_postgres_settings_fields::settings.py": {
                        "status": "pending",
                        "file": "src/modules/free/essentials/settings/settings.py",
                        "anchor": "# <<<inject:settings-fields>>>",
                        "version": "1.0.0",
                        "priority": 5,
                        "template": "settings_fields.snippet.j2",
                        "module_slug": "free/database/db_postgres",
                        "context": {},
                        "schema": {},
                        "conflict_resolution": "merge",
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Producer installed, owner (Settings) NOT installed
    (tmp_path / "registry.json").write_text(
        json.dumps({"installed_modules": [{"slug": "free/database/db_postgres"}]}, indent=2),
        encoding="utf-8",
    )

    modules_root = tmp_path / "modules"
    tpl = (
        modules_root
        / "free"
        / "database"
        / "db_postgres"
        / "templates"
        / "snippets"
        / "settings_fields.snippet.j2"
    )
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text("DB_URL: str = 'postgresql://should-not-apply'\n", encoding="utf-8")

    stats = reconcile_pending_snippets(tmp_path, modules_root=modules_root)
    assert stats["pending_before"] == 1
    assert stats["applied"] == 0
    assert stats["pending_after"] == 1
    assert stats["skipped"] == 1

    out = settings_target.read_text(encoding="utf-8")
    assert "should-not-apply" not in out


def test_reconcile_scoped_only_touches_related_pending(tmp_path: Path):
    # Two pending snippets, only one is related to scope.
    (tmp_path / "registry.json").write_text(
        json.dumps(
            {
                "installed_modules": [
                    {"slug": "free/database/db_postgres"},
                    {"slug": "free/essentials/settings"},
                ]
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # Owner file for settings module
    settings_target = (
        tmp_path / "src" / "modules" / "free" / "essentials" / "settings" / "settings.py"
    )
    settings_target.parent.mkdir(parents=True, exist_ok=True)
    settings_target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    # Another unrelated module-owned file (owner = free/cache/redis)
    redis_target = tmp_path / "src" / "modules" / "free" / "cache" / "redis" / "redis.py"
    redis_target.parent.mkdir(parents=True, exist_ok=True)
    redis_target.write_text("# <<<inject:settings-fields>>>\n", encoding="utf-8")

    (tmp_path / ".rapidkit").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".rapidkit" / "snippet_registry.json").write_text(
        json.dumps(
            {
                "snippets": {
                    # Related by owner=settings and producer=db_postgres
                    "db_postgres_settings_fields::settings.py": {
                        "status": "pending",
                        "file": "src/modules/free/essentials/settings/settings.py",
                        "anchor": "# <<<inject:settings-fields>>>",
                        "version": "1.0.0",
                        "priority": 5,
                        "template": "settings_fields.snippet.j2",
                        "module_slug": "free/database/db_postgres",
                        "context": {},
                        "schema": {},
                        "conflict_resolution": "merge",
                    },
                    # Unrelated: producer=free/cache/redis, owner=free/cache/redis
                    "redis_settings_fields::redis.py": {
                        "status": "pending",
                        "file": "src/modules/free/cache/redis/redis.py",
                        "anchor": "# <<<inject:settings-fields>>>",
                        "version": "1.0.0",
                        "priority": 5,
                        "template": "settings_fields.snippet.j2",
                        "module_slug": "free/cache/redis",
                        "context": {},
                        "schema": {},
                        "conflict_resolution": "merge",
                    },
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    modules_root = tmp_path / "modules"
    tpl = (
        modules_root
        / "free"
        / "database"
        / "db_postgres"
        / "templates"
        / "snippets"
        / "settings_fields.snippet.j2"
    )
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text("DB_URL: str = 'postgresql://scoped'\n", encoding="utf-8")

    stats = reconcile_pending_snippets_scoped(
        tmp_path,
        scope_slugs={"free/essentials/settings"},
        modules_root=modules_root,
    )
    assert stats["pending_before"] == 1
    assert stats["applied"] == 1

    # settings applied
    assert "postgresql://scoped" in settings_target.read_text(encoding="utf-8")
    # redis untouched (still pending)
    payload = json.loads(
        (tmp_path / ".rapidkit" / "snippet_registry.json").read_text(encoding="utf-8")
    )
    assert payload["snippets"]["redis_settings_fields::redis.py"]["status"] == "pending"
