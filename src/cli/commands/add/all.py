import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import typer

from core.services.config_loader import load_module_config

from ...ui.printer import print_error, print_info, print_success, print_warning

# from ....core.services.config_loader import load_module_config
# from ...ui.printer import print_error, print_info, print_success, print_warning
from .module import add_module as invoke_add_module

try:  # optional dependency
    import yaml
except (ImportError, OSError):  # pragma: no cover - optional dependency
    yaml = None  # type: ignore[assignment]

all_app = typer.Typer()


def _module_priority(name: str, config: Dict[str, Any]) -> int:
    # Allow explicit priority in module config
    if "priority" in config:
        p = config["priority"]
        if isinstance(p, int):
            return p
    elif "meta" in config and "priority" in config["meta"]:
        p = config["meta"]["priority"]
        if isinstance(p, int):
            return p

    # heuristic priorities
    n = name.lower()
    if "settings" in n:
        return 0
    if "postgres" in n or "postgresql" in n or n == "db":
        return 10
    if "redis" in n:
        return 20
    return 50


@all_app.command("module")
def add_all(
    profile: str = typer.Option("fastapi/standard", help="Target profile"),
    project: str = typer.Option(None, help="Project name inside boilerplates"),
    final: bool = typer.Option(False, "--final", help="Remove inject anchors for production"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompts"),
    report: str = typer.Option("add_all_report.json", help="Report filename"),
) -> None:
    """Install all modules that apply to a given profile in priority order.

    Usage: rapidkit add all module --profile fastapi/enterprise --project xxx
    """
    # Resolve repo root robustly (4 levels above this file)
    repo_root = Path(__file__).resolve().parents[4]
    modules_path = repo_root / "src" / "modules"
    project_root = repo_root / "boilerplates" / (project or "test")
    if not project_root.exists():
        print_error(f"❌ Project root not found: {project_root}")
        raise typer.Exit(1)

    print_info(f"🔍 Locating modules for profile {profile}")
    candidates = []

    # 1) Prefer a modules index (JSON/YAML) if present to honor curated sets and order
    index_candidates = [
        repo_root / "modules_index.json",
        repo_root / "kit_modules.json",
        repo_root / "config" / "kit_modules.yaml",
        repo_root / "config" / "kit_modules.yml",
    ]
    index_path = next((p for p in index_candidates if p.exists()), None)

    ordered_names: List[str] = []
    if index_path:
        print_info(f"🔍 Loading modules index: {index_path}")
        try:
            if index_path.suffix in (".yaml", ".yml"):
                data = (
                    yaml.safe_load(index_path.read_text(encoding="utf-8")) if yaml else {}
                ) or {}
            else:
                data = json.loads(index_path.read_text(encoding="utf-8")) or {}
        except (OSError, json.JSONDecodeError, AttributeError) as e:
            print_warning(f"⚠️ Failed to read/parse modules index: {e}")
            data = {}

        # Support both legacy flat mapping and new schema with 'kits'
        kits = (data or {}).get("kits") or {}
        kit_spec = kits.get(profile)
        if not kit_spec:
            # try by kit name (e.g., fastapi) or other fallbacks
            kit_name = profile.split("/")[0]
            kit_spec = kits.get(kit_name)

        if kit_spec:
            # Build ordered list: recommended_install_order then remaining modules
            reco = kit_spec.get("recommended_install_order") or []
            listed = kit_spec.get("modules") or []
            # normalize to list[str]
            reco = [x for x in reco if isinstance(x, str)]
            listed = [x for x in listed if isinstance(x, str)]
            ordered_names = reco + [m for m in listed if m not in reco]
        else:
            # legacy: top-level mapping { profile: [modules...] }
            legacy_list = (data or {}).get(profile)
            if not legacy_list:
                kit_name = profile.split("/")[0]
                legacy_list = (data or {}).get(kit_name) or (data or {}).get("default")
            if isinstance(legacy_list, list):
                ordered_names = [x if isinstance(x, str) else x.get("name") for x in legacy_list]
                ordered_names = [x for x in ordered_names if x]

    # 2) If we have an ordered list from index, try to load those; otherwise scan filesystem
    if ordered_names:
        print_info(
            f"🧭 Using curated module list for {profile} from index ({len(ordered_names)} items)"
        )
        for name in ordered_names:
            try:
                cfg = load_module_config(name, profile)
                candidates.append((name, cfg))
            except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
                print_warning(f"⚠️ Skipping module {name} from index: could not load config ({e})")
                continue
    else:
        if not modules_path.exists():
            print_error(
                f"❌ No curated index available and modules directory not found: {modules_path}"
            )
            raise typer.Exit(1)
        print_info(f"🔍 Scanning modules in {modules_path} for profile {profile}")
        for d in modules_path.iterdir():
            if not d.is_dir():
                continue
            name = d.name
            try:
                cfg = load_module_config(name, profile)
            except (FileNotFoundError, OSError, json.JSONDecodeError) as e:
                print_warning(f"⚠️ Skipping module {name}: could not load config ({e})")
                continue
            # determine if module supports profile by explicit profiles key or features
            supports = False
            profiles_map = cfg.get("profiles", {}) or {}
            if profile in profiles_map:
                supports = True
            else:
                # check features entries for profile membership
                for feat in cfg.get("features", {}).values():
                    if isinstance(feat, dict) and profile in feat.get("profiles", []):
                        supports = True
                        break

            if supports:
                candidates.append((name, cfg))

    if not candidates:
        print_warning("⚠️ No modules found for this profile")
        raise typer.Exit(0)

    # sort by priority: if we used index order, keep it; otherwise use heuristic
    if ordered_names:
        order_index = {name: i for i, name in enumerate(ordered_names)}
        candidates.sort(key=lambda it: order_index.get(it[0], 10_000))
    else:
        candidates.sort(key=lambda it: _module_priority(it[0], it[1]))

    print_info(f"⚙️ Will attempt to install {len(candidates)} modules in order")
    for idx, (n, _) in enumerate(candidates, start=1):
        print_info(f"  {idx}. {n}")

    if not yes:
        if not typer.confirm("Proceed to install these modules? (y/N)"):
            print_info("Aborted by user")
            raise typer.Exit(0)

    report_entries = []
    for name, _cfg in candidates:  # _cfg unused; kept tuple structure
        entry = {"module": name, "status": "pending", "error": None}
        try:
            # call the add module function programmatically
            invoke_add_module(
                name,
                profile=profile,
                project=project,
                final=final,
                with_deps=True,
            )
            entry["status"] = "installed"
            print_success(f"✅ Installed module: {name}")
        except (OSError, RuntimeError) as e:
            entry["status"] = "failed"
            entry["error"] = str(e)
            print_warning(f"❌ Failed to install {name}: {e}")
        report_entries.append(entry)

    # Build report data without shadowing the filename option 'report'
    report_data = {
        "profile": profile,
        "project": project or "test",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": report_entries,
    }

    # Defensive: user might have passed something weird or internal shadowing occurred earlier
    report_filename = str(report)

    report_path = project_root / report_filename
    try:
        report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print_success(f"📄 Report written: {report_path}")
    except OSError as e:
        print_warning(f"⚠️ Could not write report file: {e}")
