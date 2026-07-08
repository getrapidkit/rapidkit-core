#!/usr/bin/env python3
"""Opinionated end-to-end module stabilization orchestrator.

This runner executes the core checklist described in
`dev-engine/playbooks/modules/AI_AGENT_MODULE_STABILIZATION_PROMPT_*.md` so an
agent (or CI job) can stabilize a module with minimal manual intervention. It
shells out to the existing RapidKit tooling so we keep behaviour aligned with
the official CLI.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zlib
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from core.services.module_manifest import (  # noqa: E402
    DependencyCycleError,
    DependencyResolutionError,
    compute_install_order,
    load_all_manifests,
)

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from _module_slug import expand_module_slug, normalize_module_slugs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULES_ROOT = REPO_ROOT / "src" / "modules"
DEFAULT_KITS = ["fastapi.standard", "fastapi.ddd", "nestjs.standard"]
AUDIT_HISTORY_ROOT = REPO_ROOT / "dev-engine" / "audit-history"
DEFAULT_KIT_ROOT = AUDIT_HISTORY_ROOT / "_kit-runs"
IN_PROGRESS_MARKER = ".in_progress"
IN_PROGRESS_STALE_S = 6 * 60 * 60
PY310_REQ_PATTERN = re.compile(r"python\s*=\s*['\"](?:\^|>=)?3\.10")
DEFAULT_PRODUCT_SCORE_THRESHOLD = 70.0
DEFAULT_CORE_TEST_TIMEOUT_S = int(os.environ.get("RAPIDKIT_CORE_TEST_TIMEOUT_S", "120"))
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 299
MIN_MODULE_SLUG_PARTS_FOR_LEGACY_LAYOUT = 3
TWO_PART_MODULE_SLUG_LENGTH = 2
MIN_OWNER_SLUG_PARTS = 3
MAX_SNIPPET_REGISTRY_KEYS_SHOWN = 50

# Release-grade expectations (override via environment variables).
EXPECTED_PYTHON_VERSION = os.environ.get("RAPIDKIT_EXPECT_PYTHON_VERSION", "3.10.19")
EXPECTED_NODE_VERSION = os.environ.get("RAPIDKIT_EXPECT_NODE_VERSION", "20.20.0")

# Optional explicit tool overrides (useful when shells don't load nvm/rbenv/etc).
NODE_BIN_OVERRIDE = os.environ.get("RAPIDKIT_NODE_BIN")
NPM_BIN_OVERRIDE = os.environ.get("RAPIDKIT_NPM_BIN")

# Tool pins used by stabilization (avoid non-deterministic @latest fetches).
PINNED_ESLINT_VERSION = os.environ.get("RAPIDKIT_PIN_ESLINT_VERSION", "8.57.0")
PINNED_ESLINT_SECURITY_PLUGIN_VERSION = os.environ.get(
    "RAPIDKIT_PIN_ESLINT_SECURITY_PLUGIN_VERSION", "1.4.0"
)
PINNED_PIP_AUDIT_VERSION = os.environ.get("RAPIDKIT_PIN_PIP_AUDIT_VERSION", "2.10.0")

# Production-readiness tuning knobs (used by --pro-gates)
PRO_MAX_HEALTH_LATENCY_MS = float(os.environ.get("RAPIDKIT_PRO_MAX_HEALTH_LATENCY_MS", "2000"))
PRO_DOCKER_HEALTH_TIMEOUT_S = float(os.environ.get("RAPIDKIT_PRO_DOCKER_HEALTH_TIMEOUT_S", "45"))
PRO_LICENSE_DENYLIST = os.environ.get(
    "RAPIDKIT_PRO_LICENSE_DENYLIST",
    "AGPL;GPL;LGPL",
)
PRO_FAIL_ON_UNKNOWN_LICENSE = os.environ.get("RAPIDKIT_PRO_FAIL_ON_UNKNOWN_LICENSE", "0") in (
    "1",
    "true",
    "TRUE",
    "yes",
    "YES",
)
PRO_TRIVY_DB_REPOSITORY = os.environ.get(
    "RAPIDKIT_PRO_TRIVY_DB_REPOSITORY",
    "ghcr.io/aquasecurity/trivy-db:2",
)
PRO_TRIVY_ALLOWLIST = os.environ.get("RAPIDKIT_PRO_TRIVY_ALLOWLIST")


def _colors_enabled() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    isatty = getattr(sys.stdout, "isatty", None)
    return bool(isatty and isatty())


def _ansi(code: str) -> str:
    return f"\x1b[{code}m"


def _paint(text: str, *, code: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{_ansi(code)}{text}{_ansi('0')}"


def _kit_color_code(kit: str) -> str:
    palette = ["94", "96", "95", "93", "97"]
    idx = zlib.crc32(kit.encode("utf-8")) % len(palette)
    return palette[idx]


@dataclass
class StepResult:
    name: str
    command: Sequence[str]
    status: str
    duration_s: float
    log_path: str
    summary: str
    raw_output: str = ""
    metadata: dict[str, Any] | None = None

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload.pop("raw_output", None)
        if not self.metadata:
            payload.pop("metadata", None)
        return payload


@dataclass
class KitRunResult:
    kit: str
    project_dir: str
    status: str
    steps: List[StepResult]
    notes: str = ""
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    total_duration_s: Optional[float] = None
    shipped_tests: Optional[dict[str, Any]] = None

    def as_dict(self) -> dict:
        payload: dict[str, Any] = {
            "kit": self.kit,
            "project_dir": self.project_dir,
            "status": self.status,
            "steps": [s.as_dict() for s in self.steps],
            "notes": self.notes,
        }
        if self.started_at is not None:
            payload["started_at"] = self.started_at
        if self.ended_at is not None:
            payload["ended_at"] = self.ended_at
        if self.total_duration_s is not None:
            payload["total_duration_s"] = self.total_duration_s
        if self.shipped_tests:
            payload["shipped_tests"] = self.shipped_tests
        return payload


class StabilizationRunner:
    def __init__(
        self,
        module_slug: str,
        kits: Iterable[str],
        dry_run: bool,
        keep_workdirs: bool,
        skip_kits: bool,
        skip_snippet_verification: bool,
        skip_module_tests: bool,
        modules_doctor_profile: str,
        sync_verify: bool,
        kit_root: Path,
        keep_last: int,
        product_score_threshold: float,
        strict_health: bool = True,
        fail_on_ebadengine: bool = True,
        deterministic_deps: bool = True,
        strict_dev_audit_high: bool = False,
        pro_gates: bool = False,
        use_kit_cache: bool = False,
        rebuild_kit_cache: bool = False,
        static_analysis_cmd: Optional[Sequence[str]] = None,
        user_scenarios: Optional[Path] = None,
        trivy_allowlist: Optional[Path] = None,
        stabilization_fingerprint: str = "",
        stabilization_fingerprint_payload: Optional[Path] = None,
    ) -> None:
        self.original_slug = module_slug
        self.modules_root = MODULES_ROOT.resolve()
        normalized, missing = normalize_module_slugs([module_slug], self.modules_root)
        if missing or not normalized:
            missing_display = ", ".join(sorted(set(missing))) or module_slug
            raise ValueError(f"Module slug '{missing_display}' not found under {self.modules_root}")
        self.module_slug = normalized[0]
        self.kits = list(kits)
        self.dry_run = dry_run
        self.keep_workdirs = keep_workdirs
        self.skip_kits = skip_kits
        self.skip_snippet_verification = bool(skip_snippet_verification)
        self.skip_module_tests = bool(skip_module_tests)
        self.modules_doctor_profile = modules_doctor_profile
        self.sync_verify = bool(sync_verify)
        self.kit_root = kit_root
        self.keep_last = keep_last
        self.product_score_threshold = product_score_threshold
        self.strict_health = bool(strict_health)
        self.fail_on_ebadengine = bool(fail_on_ebadengine)
        self.deterministic_deps = bool(deterministic_deps)
        self.strict_dev_audit_high = bool(strict_dev_audit_high)
        self.pro_gates = bool(pro_gates)
        self.use_kit_cache = bool(use_kit_cache)
        self.rebuild_kit_cache = bool(rebuild_kit_cache)
        self.kit_cache_root = self.kit_root / "_kit-cache"
        self.timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")
        self.safe_slug = self.module_slug.replace("/", "-")
        slug_tail = self.module_slug.split("/")[-1]
        self.health_slug = slug_tail.replace("_", "-")
        self.audit_dir = AUDIT_HISTORY_ROOT / self.safe_slug / self.timestamp
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        (self.audit_dir / IN_PROGRESS_MARKER).write_text(
            f"pid={os.getpid()}\nstarted_utc={self.timestamp}\n", encoding="utf-8"
        )
        self.kit_root.mkdir(parents=True, exist_ok=True)
        self.records: List[StepResult] = []
        self.kit_runs: List[KitRunResult] = []
        self.static_analysis_cmd: Optional[List[str]] = (
            list(static_analysis_cmd) if static_analysis_cmd else None
        )
        self.stabilization_fingerprint = stabilization_fingerprint.strip()
        self.stabilization_fingerprint_payload_path = stabilization_fingerprint_payload
        self.stabilization_fingerprint_payload = self._load_json_file(
            stabilization_fingerprint_payload
        )
        self.user_scenarios_path = user_scenarios
        self.user_scenarios: List[dict[str, Any]] = self._load_user_scenarios(user_scenarios)

        resolved_trivy_allowlist: Optional[Path] = trivy_allowlist
        if resolved_trivy_allowlist is None and PRO_TRIVY_ALLOWLIST:
            resolved_trivy_allowlist = Path(PRO_TRIVY_ALLOWLIST)
        if resolved_trivy_allowlist is None:
            default_allowlist = REPO_ROOT / "dev-engine" / "runbooks" / "trivy-allowlist.yml"
            if default_allowlist.exists():
                resolved_trivy_allowlist = default_allowlist
        if resolved_trivy_allowlist is not None and not resolved_trivy_allowlist.exists():
            raise ValueError(f"Trivy allowlist not found: {resolved_trivy_allowlist}")
        self.trivy_allowlist_path = resolved_trivy_allowlist
        self.trivy_allowlist_ids = self._load_trivy_allowlist(resolved_trivy_allowlist)

        # Base environment used for all subprocess execution.
        # This keeps runs deterministic even when invoked from non-interactive shells (like make).
        self.base_env: dict[str, str] = dict(os.environ)
        if NODE_BIN_OVERRIDE:
            node_path = Path(NODE_BIN_OVERRIDE)
            if node_path.is_file():
                node_dir = str(node_path.parent)
                existing_path = self.base_env.get("PATH", "")
                self.base_env["PATH"] = (
                    f"{node_dir}{os.pathsep}{existing_path}" if existing_path else node_dir
                )

    # Public -----------------------------------------------------------------

    def run(self) -> Path:
        self._log(f"Starting stabilization for {self.module_slug} at {self.timestamp}")
        if self.original_slug != self.module_slug:
            self._log(f"Normalized module slug '{self.original_slug}' -> '{self.module_slug}'")

        success = False
        summary_path: Path | None = None
        try:
            preflight_step = self._preflight()
            self.records.append(preflight_step)
            if preflight_step.status != "pass":
                summary_path = self._write_summary(None, None)
                self._log(f"Summary written to {summary_path}")
                self._prune_audit_history()
                success = True
                return summary_path

            yaml_standard_log = self.audit_dir / "module_yaml_standard.log"
            yaml_standard_cmd = [
                "poetry",
                "run",
                "python",
                "scripts/validate_module_structure.py",
                "--ensure",
                self.module_slug,
                "--strict-module-yaml",
                "--strict-module-yaml-schema",
                "--only-module-yaml",
            ]
            self._log("Running strict module.yaml standard validation …")
            self.records.append(
                self._run_command(
                    name="module.yaml standard",
                    cmd=yaml_standard_cmd,
                    log_path=yaml_standard_log,
                )
            )
            self._log("module.yaml standard validation finished")

            self._log("Running snippet contract validation …")
            self.records.append(self._verify_module_snippet_contract())
            self._log("Snippet contract validation finished")

            doctor_log = self.audit_dir / "modules_doctor.log"
            doctor_args = [
                "poetry",
                "run",
                "python",
                "scripts/modules_doctor.py",
                self.modules_doctor_profile,
                "--modules",
                self.module_slug,
                "--with-product-score",
                "--product-score-threshold",
                f"{self.product_score_threshold}",
                "--json-report",
                str(self.audit_dir / "modules_doctor.json"),
            ]
            if self.sync_verify:
                doctor_args.insert(-2, "--sync-verify")
            self._log("Running modules_doctor …")
            self.records.append(
                self._run_command(
                    name=f"modules_doctor ({self.modules_doctor_profile})",
                    cmd=doctor_args,
                    log_path=doctor_log,
                )
            )
            self._log("modules_doctor step finished")

            self._log("Running module-scoped core tests …")
            self.records.append(self._run_core_module_tests())
            self._log("Module-scoped core tests finished")

            parity_log = self.audit_dir / "parity.log"
            parity_cmd = [
                sys.executable,
                "scripts/audit_module_parity.py",
                "--module",
                self.module_slug,
                "--json",
            ]
            self._log("Running parity audit …")
            parity_step = self._run_command("parity", parity_cmd, parity_log)
            self.records.append(parity_step)
            parity_payload = self._extract_json(parity_step.raw_output)
            if parity_payload:
                (self.audit_dir / "parity.json").write_text(
                    json.dumps(parity_payload, indent=2), encoding="utf-8"
                )
            self._log("Parity audit finished")

            product_score_log = self.audit_dir / "product_score.log"
            product_cmd = [
                sys.executable,
                "scripts/product_score.py",
                "--module",
                self.module_slug,
                "--min-score",
                f"{self.product_score_threshold}",
            ]
            self._log("Computing Product Score …")
            product_step = self._run_command("product_score", product_cmd, product_score_log)
            self.records.append(product_step)
            product_payload = self._extract_json(product_step.raw_output)
            if product_payload:
                (self.audit_dir / "product_score.json").write_text(
                    json.dumps(product_payload, indent=2), encoding="utf-8"
                )
            self._log("Product Score finished")

            static_log = self.audit_dir / "static_analysis.log"
            if self.static_analysis_cmd:
                self._log("Running static analysis …")
                static_step = self._run_command(
                    name="static_analysis",
                    cmd=self.static_analysis_cmd,
                    log_path=static_log,
                )
                self._log("Static analysis step finished")
            else:
                static_log.write_text(
                    "Static analysis skipped — no command configured via --static-analysis-cmd.\n",
                    encoding="utf-8",
                )
                static_step = StepResult(
                    name="static_analysis",
                    command=[],
                    status="skipped",
                    duration_s=0.0,
                    log_path=self._rel_path(static_log),
                    summary="No static analysis command configured",
                )
            self.records.append(static_step)

            if not self.skip_kits:
                for kit in self.kits:
                    self._log(f"Starting kit install: {kit}")
                    self.kit_runs.append(self._run_kit_install(kit))
                    self._log(f"Kit {kit} finished with status {self.kit_runs[-1].status}")

            summary_path = self._write_summary(parity_payload, product_payload)
            self._log(f"Summary written to {summary_path}")
            self._prune_audit_history()
            success = True
            return summary_path
        finally:
            if success:
                marker = self.audit_dir / IN_PROGRESS_MARKER
                try:
                    marker.unlink(missing_ok=True)
                except Exception:
                    pass

    def _normalize_to_list(self, val: object) -> list[str]:
        if val is None:
            return []
        if isinstance(val, list):
            items = val
        elif isinstance(val, str):
            v = val.strip()
            if v.startswith("{") and v.endswith("}"):
                v = v[1:-1]
            items = [s.strip() for s in v.split(",")] if v else []
        else:
            items = [str(val).strip()]
        return [s for s in items if isinstance(s, str) and s.strip()]

    def _infer_owner_slug_from_target(self, target: str) -> str | None:
        """Infer module slug from a target path under src/modules/<tier>/<category>/<module>/..."""

        try:
            parts = Path(target).parts
        except (TypeError, ValueError):
            return None

        # Normalise separators + ignore leading ./
        parts = tuple(p for p in parts if p not in (".", ""))
        try:
            idx = parts.index("modules")
        except ValueError:
            return None
        # Require preceding "src" for safety.
        if idx == 0 or parts[idx - 1] != "src":
            return None
        rest = parts[idx + 1 :]
        if len(rest) < MIN_OWNER_SLUG_PARTS:
            return None
        tier, category, module = rest[0], rest[1], rest[2]
        if not (tier and category and module):
            return None
        return f"{tier}/{category}/{module}"

    def _verify_module_snippet_contract(self) -> StepResult:
        """Validate module snippet configuration against templates and dependency contract.

        Checks:
        - config/snippets.yaml is parseable when present
        - injection-style entries reference existing templates/snippets/*
        - cross-module targets under src/modules/... require the owner module to be installed
          via depends_on (direct or transitive)
        """

        log_path = self.audit_dir / "snippet_contract.log"
        slug_parts = [p for p in self.module_slug.split("/") if p]
        module_dir = self.modules_root / Path(*slug_parts)
        snippet_cfg_path = module_dir / "config" / "snippets.yaml"
        templates_dir = module_dir / "templates" / "snippets"

        # Also run the repo-wide static validator (source-of-truth checks + semantic checks).
        # This includes policy gates like explicit profile coverage when inheritance exists.
        static_validator_log = self.audit_dir / "validate_module_snippet_configs.log"

        lines: list[str] = [f"Module: {self.module_slug}", f"Module dir: {module_dir}"]
        if not snippet_cfg_path.exists():
            lines.append("No config/snippets.yaml present; skipping snippet contract checks.")
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            # Still run the static validator so other snippet-related policies (if any)
            # are enforced consistently across all modules.
            validator_step = self._run_command(
                name="validate module snippet configs",
                cmd=[
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "validate_module_snippet_configs.py"),
                    "--module",
                    self.module_slug,
                    "--skip-template-placeholders",
                ],
                log_path=static_validator_log,
                cwd=REPO_ROOT,
            )
            if validator_step.status == "fail":
                return StepResult(
                    name="snippet contract",
                    command=[],
                    status="fail",
                    duration_s=0.0,
                    log_path=self._rel_path(static_validator_log),
                    summary="Static snippet validation failed",
                )
            return StepResult(
                name="snippet contract",
                command=[],
                status="pass",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="No snippets.yaml present",
            )

        errors: list[str] = []
        try:
            loaded = yaml.safe_load(snippet_cfg_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"failed to parse {snippet_cfg_path}: {exc}")
            loaded = {}
        if not isinstance(loaded, Mapping):
            errors.append(f"invalid YAML structure in {snippet_cfg_path} (expected mapping)")
            loaded = {}

        raw_snippets = loaded.get("snippets") if isinstance(loaded, Mapping) else None
        if raw_snippets is None:
            snippets: list[object] = []
        elif isinstance(raw_snippets, list):
            snippets = raw_snippets
        else:
            errors.append("snippets must be a list in config/snippets.yaml")
            snippets = []

        dep_slugs = set(
            self._resolve_dependency_install_order(self.module_slug) + [self.module_slug]
        )
        lines.append(f"Dependency closure size: {len(dep_slugs)}")

        injection_count = 0
        for entry in snippets:
            if not isinstance(entry, Mapping):
                continue

            injection_keys = {
                "id",
                "anchor",
                "target",
                "profiles",
                "priority",
                "schema",
                "conflict_resolution",
                "version",
                "features",
            }
            is_injection_style = any(key in entry for key in injection_keys) and any(
                key in entry for key in ("anchor", "target")
            )
            if not is_injection_style:
                continue
            injection_count += 1

            snippet_id = str(entry.get("id") or "").strip()
            template = str(entry.get("template") or "").strip()
            anchor = entry.get("anchor")
            targets = self._normalize_to_list(entry.get("target"))

            if not snippet_id:
                errors.append("snippet entry missing required id")
                continue
            if not template or not anchor or not targets:
                errors.append(f"snippet {snippet_id}: missing target/anchor/template")
                continue
            if "/" in template or "\\" in template:
                errors.append(
                    f"snippet {snippet_id}: template must be a filename under templates/snippets/ (got '{template}')"
                )
                continue
            template_path = templates_dir / template
            if not template_path.exists():
                errors.append(f"snippet {snippet_id}: template not found: {template_path}")

            for target in targets:
                owner = self._infer_owner_slug_from_target(target)
                if owner and owner != self.module_slug and owner not in dep_slugs:
                    errors.append(
                        f"snippet {snippet_id}: target '{target}' belongs to '{owner}' but it's not in depends_on closure"
                    )

        lines.append(f"Injection-style snippets found: {injection_count}")
        if errors:
            lines.append("Errors:")
            lines.extend(f"- {e}" for e in errors)
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return StepResult(
                name="snippet contract",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary=f"Snippet contract violations ({len(errors)})",
            )

        # Enforce the full static validator (semantic checks + policy gates).
        validator_step = self._run_command(
            name="validate module snippet configs",
            cmd=[
                sys.executable,
                str(REPO_ROOT / "scripts" / "validate_module_snippet_configs.py"),
                "--module",
                self.module_slug,
                "--skip-template-placeholders",
            ],
            log_path=static_validator_log,
            cwd=REPO_ROOT,
        )
        if validator_step.status == "fail":
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return StepResult(
                name="snippet contract",
                command=list(validator_step.command),
                status="fail",
                duration_s=validator_step.duration_s,
                log_path=self._rel_path(static_validator_log),
                summary="Static snippet validation failed",
            )

        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return StepResult(
            name="snippet contract",
            command=[],
            status="pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary="Snippet contract ok",
        )

    def _run_core_module_tests(self) -> StepResult:
        log_path = self.audit_dir / "core_module_tests.log"
        if self.skip_module_tests:
            log_path.write_text(
                "Skipped module-scoped core tests (requested via --skip-module-tests).\n",
                encoding="utf-8",
            )
            return StepResult(
                name="core module tests",
                command=[],
                status="skipped",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="Skipped",
            )

        slug_parts = [p for p in self.module_slug.split("/") if p]
        test_dir = REPO_ROOT / "tests" / "modules" / Path(*slug_parts)
        if not test_dir.exists():
            log_path.write_text(
                f"No module-scoped core tests directory found at: {test_dir}\n",
                encoding="utf-8",
            )
            return StepResult(
                name="core module tests",
                command=[],
                status="skipped",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="No tests directory",
            )

        return self._run_command(
            name="core module tests",
            cmd=[
                "poetry",
                "run",
                "pytest",
                "-q",
                "--maxfail=1",
                str(test_dir),
            ],
            log_path=log_path,
            cwd=REPO_ROOT,
            timeout_s=DEFAULT_CORE_TEST_TIMEOUT_S,
        )

    # Internal helpers -------------------------------------------------------

    def _run_command(
        self,
        name: str,
        cmd: Sequence[str],
        log_path: Path,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout_s: int | None = None,
    ) -> StepResult:
        cwd = cwd or REPO_ROOT
        log_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()
        if self.dry_run:
            rendered = " ".join(cmd)
            log_path.write_text(f"DRY RUN — skipped executing: {rendered}\n", encoding="utf-8")
            return StepResult(
                name=name,
                command=list(cmd),
                status="skipped",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="dry-run",
                raw_output="",
            )

        if env is None:
            run_env = dict(self.base_env)
        else:
            run_env = dict(env)
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                env=run_env,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.time() - start
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            combined = stdout + stderr
            timeout_note = f"\nCommand timed out after {timeout_s}s.\n"
            combined = f"{combined}{timeout_note}"
            log_path.write_text(combined, encoding="utf-8")
            return StepResult(
                name=name,
                command=list(cmd),
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"Timed out after {timeout_s}s",
                raw_output=combined,
            )
        duration = time.time() - start
        combined = (proc.stdout or "") + (proc.stderr or "")
        log_path.write_text(combined, encoding="utf-8")
        summary = self._summarize(combined)
        status = "pass" if proc.returncode == 0 else "fail"
        return StepResult(
            name=name,
            command=list(cmd),
            status=status,
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=summary,
            raw_output=combined,
        )

    def _preflight(self) -> StepResult:
        """Fail-fast toolchain checks for release-grade stabilization."""

        log_path = self.audit_dir / "preflight.log"
        lines: list[str] = []
        errors: list[str] = []

        expected_python = EXPECTED_PYTHON_VERSION
        expected_node = EXPECTED_NODE_VERSION
        lines.append(f"expected_python={expected_python}")
        lines.append(f"expected_node={expected_node}")

        actual_python = (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        )
        lines.append(f"python={actual_python}")
        if actual_python != expected_python:
            errors.append(
                f"Python mismatch: running {actual_python} but expected {expected_python}"
            )

        if self.skip_kits:
            lines.append("skip_kits=true (toolchain checks limited to Python)")
        else:
            if self.pro_gates:
                docker_bin = shutil.which("docker")
                if not docker_bin:
                    errors.append("Missing 'docker' executable (required for --pro-gates)")
                else:
                    proc = subprocess.run(
                        [docker_bin, "--version"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    docker_raw = (proc.stdout or proc.stderr or "").strip()
                    lines.append(f"docker_raw={docker_raw}")
                    if proc.returncode != 0:
                        errors.append(
                            f"Unable to determine docker version (exit {proc.returncode})"
                        )

                    info_proc = subprocess.run(
                        [docker_bin, "info"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    lines.append(f"docker_info_exit={info_proc.returncode}")
                    if info_proc.returncode != 0:
                        errors.append("Docker daemon not reachable (docker info failed)")

                trivy_bin = shutil.which("trivy")
                if not trivy_bin:
                    errors.append(
                        "Missing 'trivy' executable (required for --pro-gates container scan)"
                    )
                else:
                    proc = subprocess.run(
                        [trivy_bin, "--version"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    trivy_raw = (proc.stdout or proc.stderr or "").strip()
                    lines.append(f"trivy_raw={trivy_raw}")
                    if proc.returncode != 0:
                        errors.append(f"Unable to determine trivy version (exit {proc.returncode})")

                    lines.append(f"trivy_db_repository={PRO_TRIVY_DB_REPOSITORY}")
                    if self.trivy_allowlist_path is not None:
                        lines.append(
                            f"trivy_allowlist_path={self._rel_path(self.trivy_allowlist_path.resolve())}"
                        )
                        lines.append(f"trivy_allowlist_ids={len(self.trivy_allowlist_ids)}")
                    else:
                        lines.append("trivy_allowlist_path=")

                    db_proc = subprocess.run(
                        [
                            trivy_bin,
                            "image",
                            "--download-db-only",
                            "--no-progress",
                            "--db-repository",
                            PRO_TRIVY_DB_REPOSITORY,
                            "alpine:3.19",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    lines.append(f"trivy_db_download_exit={db_proc.returncode}")
                    if db_proc.returncode != 0:
                        raw = ((db_proc.stdout or "") + (db_proc.stderr or "")).strip()
                        errors.append(
                            "Trivy vulnerability DB download failed (required for --pro-gates). "
                            f"db_repository={PRO_TRIVY_DB_REPOSITORY} details={self._summarize(raw)}"
                        )

                if self.user_scenarios_path is None:
                    errors.append(
                        "Missing --user-scenarios (required when --pro-gates is enabled). "
                        "Example: --user-scenarios dev-engine/runbooks/pro-gates-user-scenarios.example.yml"
                    )

            if any(k.startswith("fastapi") for k in self.kits):
                require_export = os.environ.get("RAPIDKIT_REQUIRE_POETRY_EXPORT", "0") in (
                    "1",
                    "true",
                    "TRUE",
                    "yes",
                    "YES",
                )
                if not shutil.which("poetry"):
                    errors.append("Missing 'poetry' executable (required for fastapi kits)")
                else:
                    poetry_bin = shutil.which("poetry")
                    if poetry_bin:
                        proc = subprocess.run(
                            [poetry_bin, "export", "--help"],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        raw = ((proc.stdout or "") + (proc.stderr or "")).strip()
                        lines.append(f"poetry_export_check_exit={proc.returncode}")
                        if proc.returncode != 0 and "command export does not exist" in raw:
                            if require_export:
                                errors.append(
                                    "Missing Poetry export support (install 'poetry-plugin-export' via: poetry self add poetry-plugin-export)"
                                )
                            else:
                                lines.append("poetry_export_warning=missing")

                try:
                    from importlib import metadata as _importlib_metadata

                    pip_audit_version = _importlib_metadata.version("pip-audit")
                    lines.append(f"pip_audit={pip_audit_version}")
                    if pip_audit_version != PINNED_PIP_AUDIT_VERSION:
                        errors.append(
                            f"pip-audit mismatch: running {pip_audit_version} but expected {PINNED_PIP_AUDIT_VERSION}"
                        )
                except Exception as exc:  # pragma: no cover
                    errors.append(f"Missing pip-audit in stabilization environment: {exc}")

                if self.pro_gates:
                    # SBOM generation relies on pip-audit's CycloneDX output format.
                    proc = subprocess.run(
                        [sys.executable, "-m", "pip_audit", "--help"],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    help_raw = ((proc.stdout or "") + (proc.stderr or "")).lower()
                    if proc.returncode != 0 or "cyclonedx" not in help_raw:
                        errors.append(
                            "pip-audit missing CycloneDX output support (required for --pro-gates SBOM)"
                        )

                    # Bandit is our deterministic Python SAST gate.
                    poetry_bin = shutil.which("poetry")
                    if poetry_bin:
                        bandit_proc = subprocess.run(
                            [poetry_bin, "run", "bandit", "--version"],
                            check=False,
                            capture_output=True,
                            text=True,
                            cwd=str(REPO_ROOT),
                        )
                        bandit_raw = (bandit_proc.stdout or bandit_proc.stderr or "").strip()
                        lines.append(f"bandit_raw={bandit_raw}")
                        if bandit_proc.returncode != 0:
                            errors.append(
                                "Bandit not available via 'poetry run bandit' (required for --pro-gates SAST)"
                            )

            if any(k.startswith("nestjs") for k in self.kits):
                node_bin = NODE_BIN_OVERRIDE or shutil.which("node")
                npm_bin = NPM_BIN_OVERRIDE or shutil.which("npm")
                lines.append(f"node_bin={node_bin or ''}")
                lines.append(f"npm_bin={npm_bin or ''}")
                if not node_bin:
                    errors.append("Missing 'node' executable (required for nestjs kits)")
                if not npm_bin:
                    errors.append("Missing 'npm' executable (required for nestjs kits)")

                if node_bin:
                    proc = subprocess.run(
                        [node_bin, "--version"],
                        check=False,
                        capture_output=True,
                        text=True,
                        env=dict(self.base_env),
                    )
                    raw = (proc.stdout or proc.stderr or "").strip()
                    lines.append(f"node_raw={raw}")
                    version = raw.lstrip("v")
                    if proc.returncode != 0 or not version:
                        errors.append(f"Unable to determine node version (exit {proc.returncode})")
                    elif version != expected_node:
                        errors.append(
                            f"Node mismatch: running {version} but expected {expected_node}. "
                            f"If you use nvm, run 'nvm use {expected_node}' before running make, "
                            "or set RAPIDKIT_NODE_BIN to an absolute node path."
                        )

        rendered = "\n".join(lines + (["Errors:"] if errors else []) + [f"- {e}" for e in errors])
        log_path.write_text(rendered + "\n", encoding="utf-8")

        if errors:
            return StepResult(
                name="preflight",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary=f"Preflight failed ({len(errors)})",
            )
        return StepResult(
            name="preflight",
            command=[],
            status="pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary="Preflight ok",
        )

    def _load_user_scenarios(self, scenario_path: Optional[Path]) -> List[dict[str, Any]]:
        if scenario_path is None:
            return []
        try:
            raw = scenario_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self._log(f"User scenario file {scenario_path} not found; skipping custom scenarios")
            return []
        except OSError as exc:
            self._log(f"Unable to read user scenarios from {scenario_path}: {exc}")
            return []
        try:
            data = yaml.safe_load(raw) or []
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            self._log(f"Failed to parse user scenarios from {scenario_path}: {exc}")
            return []
        if not isinstance(data, list):
            self._log("User scenarios file must contain a list of scenario entries; ignoring")
            return []

        scenarios: List[dict[str, Any]] = []
        for index, entry in enumerate(data, start=1):
            if not isinstance(entry, dict):
                self._log(f"Scenario #{index} is not a mapping; skipping")
                continue
            command = entry.get("command")
            parsed_cmd: List[str]
            if isinstance(command, str):
                parsed_cmd = shlex.split(command)
            elif isinstance(command, list) and all(isinstance(item, str) for item in command):
                parsed_cmd = list(command)
            else:
                self._log(
                    f"Scenario '{entry.get('name') or index}' is missing a valid command; skipping"
                )
                continue

            kits_field = entry.get("kits")
            kit_targets: Optional[set[str]] = None
            if isinstance(kits_field, str):
                kit_targets = {kits_field}
            elif isinstance(kits_field, list) and kits_field:
                kit_targets = {str(item) for item in kits_field}

            env_field = entry.get("env")
            env_vars = (
                {str(k): str(v) for k, v in env_field.items()}
                if isinstance(env_field, dict)
                else {}
            )

            scenarios.append(
                {
                    "name": str(entry.get("name") or f"scenario-{index}"),
                    "command": parsed_cmd,
                    "kits": kit_targets,
                    "workdir": entry.get("workdir"),
                    "env": env_vars,
                }
            )

        if scenarios:
            self._log(
                f"Loaded {len(scenarios)} user scenario(s) from {self._rel_path(scenario_path.resolve())}"
            )
        return scenarios

    def _load_trivy_allowlist(self, allowlist_path: Optional[Path]) -> set[str]:
        if allowlist_path is None:
            return set()
        try:
            raw = allowlist_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Unable to read Trivy allowlist from {allowlist_path}: {exc}")
        try:
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:  # type: ignore[attr-defined]
            raise ValueError(f"Failed to parse Trivy allowlist from {allowlist_path}: {exc}")

        ids: Iterable[object]
        if isinstance(data, list):
            ids = data
        elif isinstance(data, dict):
            ids = data.get("ignore_vulnerability_ids") or []
        else:
            raise ValueError(
                "Trivy allowlist must be a list or a mapping containing 'ignore_vulnerability_ids'"
            )

        parsed: set[str] = set()
        for item in ids:
            if not item:
                continue
            parsed.add(str(item).strip())
        return {v for v in parsed if v}

    def _run_user_scenarios(self, kit: str, project_dir: Path, kit_dir: Path) -> List[StepResult]:
        scenario_dir = kit_dir / "scenarios"
        scenario_dir.mkdir(parents=True, exist_ok=True)
        steps: List[StepResult] = []
        if not self.user_scenarios:
            log_path = scenario_dir / "scenarios.log"
            message = "User scenarios skipped — no file provided via --user-scenarios.\n"
            status = "skipped"
            summary = "No user scenarios configured"
            if self.pro_gates:
                message = (
                    "User scenarios missing — --pro-gates requires at least one scenario entry.\n"
                )
                status = "fail"
                summary = "Missing user scenarios"
            log_path.write_text(message, encoding="utf-8")
            return [
                StepResult(
                    name="user_scenarios",
                    command=[],
                    status=status,
                    duration_s=0.0,
                    log_path=self._rel_path(log_path),
                    summary=summary,
                )
            ]

        executed = False
        for index, scenario in enumerate(self.user_scenarios, start=1):
            kits = scenario.get("kits")
            if kits and kit not in kits and "*" not in kits:
                continue
            executed = True
            cmd = self._render_scenario_command(scenario["command"], project_dir, kit)
            env = self._build_scenario_env(scenario.get("env") or {}, project_dir, kit)
            workdir = self._resolve_scenario_workdir(scenario.get("workdir"), project_dir)
            log_stub = self._slugify(f"{index:02d}-{scenario['name']}") or f"scenario-{index:02d}"
            log_path = scenario_dir / f"{log_stub}.log"
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name=f"scenario: {scenario['name']}",
                    cmd=cmd,
                    log_path=log_path,
                    cwd=workdir,
                    env=env,
                )
            )
        if not executed:
            log_path = scenario_dir / "scenarios.log"
            message = f"User scenarios skipped — no entries targeted kit '{kit}'.\n"
            status = "skipped"
            summary = "No user scenarios matched kit"
            if self.pro_gates:
                message = f"User scenarios missing for kit '{kit}' — --pro-gates requires at least one matching scenario.\n"
                status = "fail"
                summary = "No user scenarios matched kit"
            log_path.write_text(message, encoding="utf-8")
            steps.append(
                StepResult(
                    name="user_scenarios",
                    command=[],
                    status=status,
                    duration_s=0.0,
                    log_path=self._rel_path(log_path),
                    summary=summary,
                )
            )
        return steps

    def _render_scenario_command(
        self, command: Sequence[str], project_dir: Path, kit: str
    ) -> List[str]:
        rendered: List[str] = []
        for part in command:
            rendered.append(
                part.replace("{project_dir}", str(project_dir))
                .replace("{kit}", kit)
                .replace("{module}", self.module_slug)
            )
        return rendered

    def _build_scenario_env(
        self,
        env_vars: Mapping[str, str],
        project_dir: Path,
        kit: str,
    ) -> Mapping[str, str]:
        env = os.environ.copy()
        for key, value in env_vars.items():
            env[key] = (
                value.replace("{project_dir}", str(project_dir))
                .replace("{kit}", kit)
                .replace("{module}", self.module_slug)
            )
        return env

    def _resolve_scenario_workdir(self, raw_workdir: Any, project_dir: Path) -> Path:
        if isinstance(raw_workdir, str) and raw_workdir.strip():
            candidate = Path(raw_workdir)
            if not candidate.is_absolute():
                candidate = project_dir / candidate
            return candidate
        return project_dir

    def _slugify(self, value: str, *, fallback: str = "scenario") -> str:
        sanitized = re.sub(r"[^a-zA-Z0-9-_]+", "-", value).strip("-")
        return sanitized or fallback

    def _format_timestamp(self, value: datetime) -> str:
        return value.replace(microsecond=0).isoformat() + "Z"

    def _log_kit(self, kit: str, message: str) -> None:
        self._log(f"[kit:{kit}] {message}")

    def _attach_test_metrics(self, step: StepResult, kind: str) -> None:
        metrics = self._parse_test_metrics(step.raw_output, kind)
        if not metrics:
            return
        step.metadata = step.metadata or {}
        step.metadata["tests"] = metrics

    def _parse_test_metrics(self, raw: str, kind: str) -> dict[str, Any] | None:
        if not raw:
            return None

        def _first_int(pattern: str) -> int:
            match = re.search(pattern, raw, re.IGNORECASE | re.MULTILINE)
            return int(match.group(1)) if match else 0

        passed = _first_int(r"(\d+)\s+passed")
        failed = _first_int(r"(\d+)\s+failed")
        skipped = _first_int(r"(\d+)\s+skipped")
        todo = _first_int(r"(\d+)\s+todo")
        total = _first_int(r"(\d+)\s+total")
        if total == 0:
            computed = passed + failed + skipped + todo
            total = computed if computed > 0 else 0

        duration_match = re.search(r"in\s+([0-9]+\.?[0-9]*)s", raw)
        duration = float(duration_match.group(1)) if duration_match else None

        if all(value == 0 for value in (passed, failed, skipped, todo, total)):
            return None

        metrics: dict[str, Any] = {
            "tool": kind,
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "todo": todo,
        }
        if duration is not None:
            metrics["duration_s"] = duration
        return metrics

    def _parse_pip_audit(self, raw: str) -> Tuple[int, int, List[dict[str, Any]], bool]:
        """Parse pip-audit JSON output.

        pip-audit may emit a JSON value followed by human text like
        "No known vulnerabilities found". We extract the first JSON value and
        support both legacy list payloads and modern object payloads.
        """

        def _extract_first_json_value(text: str) -> object | None:
            decoder = json.JSONDecoder()
            for idx, ch in enumerate(text):
                if ch not in ("{", "["):
                    continue
                try:
                    value, _ = decoder.raw_decode(text[idx:])
                except json.JSONDecodeError:
                    continue
                return value
            return None

        payload = _extract_first_json_value(raw or "")
        if payload is None:
            return 0, 0, [], False

        high = 0
        critical = 0
        vulnerabilities: List[dict[str, Any]] = []

        def _register_vuln(
            *,
            dependency: str | None,
            version: str | None,
            vuln: Mapping[str, Any],
        ) -> None:
            nonlocal high, critical
            severity_raw = vuln.get("severity")
            severity = str(severity_raw or "").upper().strip()
            if not severity:
                severity = "HIGH"  # fail-closed-ish: treat unknown severity as high
            record = {
                "id": vuln.get("id"),
                "aliases": vuln.get("aliases"),
                "severity": severity,
                "fix_versions": vuln.get("fix_versions"),
                "dependency": dependency,
                "version": version,
            }
            vulnerabilities.append(record)
            if severity == "CRITICAL":
                critical += 1
            elif severity == "HIGH":
                high += 1

        if isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                dep_name = entry.get("name")
                dep_version = entry.get("version")
                vulns = entry.get("vulnerabilities")
                if not isinstance(vulns, list):
                    continue
                for vuln in vulns:
                    if not isinstance(vuln, dict):
                        continue
                    _register_vuln(dependency=dep_name, version=dep_version, vuln=vuln)
            return high, critical, vulnerabilities, True

        if isinstance(payload, dict):
            deps = payload.get("dependencies")
            if not isinstance(deps, list):
                return 0, 0, [], False
            for dep in deps:
                if not isinstance(dep, dict):
                    continue
                dep_name = dep.get("name")
                dep_version = dep.get("version")
                vulns = dep.get("vulns")
                if not isinstance(vulns, list):
                    continue
                for vuln in vulns:
                    if not isinstance(vuln, dict):
                        continue
                    _register_vuln(dependency=dep_name, version=dep_version, vuln=vuln)
            return high, critical, vulnerabilities, True

        return 0, 0, [], False

    def _parse_npm_audit(self, raw: str) -> Tuple[int, int, bool]:
        """Parse npm/yarn audit JSON output.

        Returns (high, critical, parsed_ok).

        npm/yarn sometimes emit multiple JSON payloads; we attempt a best-effort
        parse but fail closed when we cannot extract vulnerability metadata.
        """

        def _extract_first_json_object(text: str) -> str | None:
            start = text.find("{")
            if start == -1:
                return None
            depth = 0
            in_string = False
            escape = False
            for idx in range(start, len(text)):
                ch = text[idx]
                if in_string:
                    if escape:
                        escape = False
                        continue
                    if ch == "\\":
                        escape = True
                        continue
                    if ch == '"':
                        in_string = False
                    continue
                if ch == '"':
                    in_string = True
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : idx + 1]
            return None

        payload: object
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
            extracted = _extract_first_json_object(raw)
            if extracted is not None:
                try:
                    payload = json.loads(extracted)
                except json.JSONDecodeError:
                    payload = None

            if payload is None:
                # Fallback: scan for single-line JSON objects.
                for line in raw.splitlines():
                    candidate = line.strip()
                    if candidate.startswith("{") and candidate.endswith("}"):
                        try:
                            payload = json.loads(candidate)
                            break
                        except json.JSONDecodeError:
                            continue
            if payload is None:
                return 0, 0, False

        metadata = payload.get("metadata") if isinstance(payload, dict) else None
        vulnerabilities = metadata.get("vulnerabilities") if isinstance(metadata, dict) else None
        if not isinstance(vulnerabilities, dict):
            return 0, 0, False

        high = int(vulnerabilities.get("high", 0) or 0)
        critical = int(vulnerabilities.get("critical", 0) or 0)
        return high, critical, True

    def _module_has_applicable_snippets(self, *, kit: str) -> Tuple[bool, int]:
        """Return (has_applicable, applicable_count) for this module and kit.

        This is a conservative gate used to avoid PASS-with-zero-expectations:
        - If the module declares snippets (config/snippets.yaml) that target this kit
          (or have no explicit profiles), then we expect the snippet registry to
          record at least one applied snippet after reconcile.
        - If no snippets are declared for this kit, we do not enforce registry presence.
        """

        slug_parts = [p for p in self.module_slug.split("/") if p]
        module_dir = self.modules_root / Path(*slug_parts)
        snippet_cfg_path = module_dir / "config" / "snippets.yaml"
        if not snippet_cfg_path.exists():
            return False, 0
        try:
            loaded = yaml.safe_load(snippet_cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            # Parsing errors are handled by the snippet contract gate.
            return False, 0
        if not isinstance(loaded, Mapping):
            return False, 0
        raw_snippets = loaded.get("snippets")
        if not isinstance(raw_snippets, list) or not raw_snippets:
            return False, 0

        applicable = 0
        for entry in raw_snippets:
            if not isinstance(entry, Mapping):
                continue
            profiles = entry.get("profiles")
            if profiles is None:
                applicable += 1
                continue
            if isinstance(profiles, str):
                if profiles.strip() == kit:
                    applicable += 1
                continue
            if isinstance(profiles, list):
                normalized = [str(item).strip() for item in profiles if str(item).strip()]
                if kit in normalized:
                    applicable += 1
                continue
        return (applicable > 0), applicable

    def _run_kit_step(
        self,
        kit: str,
        *,
        step_name: str,
        cmd: Sequence[str],
        log_path: Path,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> StepResult:
        self._log_kit(kit, f"{step_name} …")
        result = self._run_command(step_name, cmd, log_path, cwd=cwd, env=env)
        self._log_kit(
            kit,
            f"{step_name} {result.status.upper()} (log: {result.log_path}, duration={result.duration_s:.1f}s)",
        )
        return result

    def _aggregate_shipped_tests(self, steps: List[StepResult]) -> Optional[dict[str, Any]]:
        aggregate: dict[str, Any] = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "todo": 0,
            "steps": [],
        }
        step_entries: List[dict[str, Any]] = aggregate["steps"]
        for step in steps:
            tests = (step.metadata or {}).get("tests") if step.metadata else None
            if not tests:
                continue
            step_entries.append({"step": step.name, **tests})
            for key in ("total", "passed", "failed", "skipped", "todo"):
                aggregate[key] += int(tests.get(key, 0) or 0)
        return aggregate if step_entries else None

    def _aggregate_all_shipped_tests(self) -> Optional[dict[str, Any]]:
        aggregate: dict[str, Any] = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "todo": 0,
            "kits": [],
        }
        kit_entries: List[dict[str, Any]] = aggregate["kits"]
        for run in self.kit_runs:
            kit_tests = run.shipped_tests if isinstance(run.shipped_tests, dict) else None
            if not kit_tests:
                continue
            kit_entries.append({"kit": run.kit, **kit_tests})
            for key in ("total", "passed", "failed", "skipped", "todo"):
                aggregate[key] += int(kit_tests.get(key, 0) or 0)
        return aggregate if kit_entries else None

    def _finalize_kit_result(
        self,
        *,
        kit: str,
        project_dir: Path,
        steps: List[StepResult],
        notes: str,
        status: str,
        started_at: datetime,
        started_monotonic: float,
    ) -> KitRunResult:
        ended_at = datetime.utcnow()
        duration = time.time() - started_monotonic
        shipped_tests = self._aggregate_shipped_tests(steps)
        return KitRunResult(
            kit=kit,
            project_dir=self._rel_path(project_dir),
            status=status,
            steps=steps,
            notes=notes,
            started_at=self._format_timestamp(started_at),
            ended_at=self._format_timestamp(ended_at),
            total_duration_s=round(duration, 2),
            shipped_tests=shipped_tests,
        )

    def _run_kit_install(self, kit: str) -> KitRunResult:
        kit_dir = self.kit_root / self.safe_slug / self.timestamp / kit.replace(".", "-")
        compact_slug = self.safe_slug[:16]
        compact_time = self.timestamp.replace("-", "")[:8]
        project_name = f"audit-{compact_slug}-{kit.replace('.', '-')}-{compact_time}"
        project_dir = kit_dir / project_name
        if kit_dir.exists() and not self.keep_workdirs:
            shutil.rmtree(kit_dir)
        kit_dir.mkdir(parents=True, exist_ok=True)
        kit_started_at = datetime.utcnow()
        kit_start_monotonic = time.time()
        steps: List[StepResult] = []

        rapidkit_cmd = self._rapidkit_cmd()
        if self.use_kit_cache:
            steps.append(
                self._hydrate_kit_project_from_cache(
                    kit=kit,
                    project_name=project_name,
                    kit_dir=kit_dir,
                    project_dir=project_dir,
                    rapidkit_cmd=rapidkit_cmd,
                )
            )
        else:
            create_cmd = [
                *rapidkit_cmd,
                "create",
                "project",
                kit,
                project_name,
                "--skip-essentials",
                "--output",
                str(kit_dir),
                "--force",
            ]
            if kit.startswith("nestjs"):
                create_cmd.extend(["--variable", "package_manager=npm"])
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name=f"create {kit}",
                    cmd=create_cmd,
                    log_path=kit_dir / "create.log",
                )
            )
        if steps[-1].status != "pass":
            if self.dry_run and steps[-1].status == "skipped":
                notes = "Dry-run completed; kit commands were planned but not executed."
                return self._finalize_kit_result(
                    kit=kit,
                    project_dir=project_dir,
                    steps=steps,
                    notes=notes,
                    status="pass",
                    started_at=kit_started_at,
                    started_monotonic=kit_start_monotonic,
                )
            return self._finalize_kit_result(
                kit=kit,
                project_dir=project_dir,
                steps=steps,
                notes="Project creation failed; inspect create.log",
                status="fail",
                started_at=kit_started_at,
                started_monotonic=kit_start_monotonic,
            )

        dependency_slugs = self._resolve_dependency_install_order(self.module_slug)
        for dep_slug in dependency_slugs:
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name=f"install dependency {dep_slug} ({kit})",
                    cmd=[*rapidkit_cmd, "add", "module", dep_slug, "--profile", kit],
                    log_path=kit_dir / f"install-dep-{dep_slug.replace('/', '-')}.log",
                    cwd=project_dir,
                )
            )
            if steps[-1].status != "pass":
                return self._finalize_kit_result(
                    kit=kit,
                    project_dir=project_dir,
                    steps=steps,
                    notes=f"Dependency install failed ({dep_slug}); inspect install-dep-{dep_slug.replace('/', '-')}.log",
                    status="fail",
                    started_at=kit_started_at,
                    started_monotonic=kit_start_monotonic,
                )

        install_cmd = [*rapidkit_cmd, "add", "module", self.module_slug, "--profile", kit]
        steps.append(
            self._run_kit_step(
                kit,
                step_name=f"install {kit}",
                cmd=install_cmd,
                log_path=kit_dir / "install.log",
                cwd=project_dir,
            )
        )
        if steps[-1].status != "pass":
            return self._finalize_kit_result(
                kit=kit,
                project_dir=project_dir,
                steps=steps,
                notes="Module install failed; inspect install.log",
                status="fail",
                started_at=kit_started_at,
                started_monotonic=kit_start_monotonic,
            )

        layout_check = self._verify_install_layout(
            kit=kit, project_dir=project_dir, kit_dir=kit_dir
        )
        steps.append(layout_check)

        if not self.skip_snippet_verification:
            steps.append(
                self._verify_snippet_injection(
                    kit=kit,
                    project_dir=project_dir,
                    kit_dir=kit_dir,
                )
            )

            steps.append(
                self._run_kit_step(
                    kit,
                    step_name="reconcile snippets",
                    cmd=[*rapidkit_cmd, "reconcile", "--verbose"],
                    log_path=kit_dir / "snippets-reconcile.log",
                    cwd=project_dir,
                )
            )

            steps.append(
                self._verify_snippet_registry_state(
                    kit=kit,
                    project_dir=project_dir,
                    kit_dir=kit_dir,
                )
            )

        steps.append(
            self._score_product_for_kit(
                kit=kit,
                project_dir=project_dir,
                kit_dir=kit_dir,
            )
        )

        if kit.startswith("fastapi"):
            steps.extend(self._run_python_project_checks(kit, project_dir))
        elif kit.startswith("nestjs"):
            steps.extend(self._run_node_project_checks(kit, project_dir))
        else:
            skip_log = kit_dir / "tests-skipped.log"
            skip_log.parent.mkdir(parents=True, exist_ok=True)
            skip_log.write_text(
                f"No automated workflow configured for kit '{kit}'. Please run manual verification and update the audit log.\n",
                encoding="utf-8",
            )
            steps.append(
                StepResult(
                    name=f"skip tests {kit}",
                    command=[],
                    status="skipped",
                    duration_s=0.0,
                    log_path=self._rel_path(skip_log),
                    summary="Unknown kit profile; manual verification required",
                )
            )

        steps.extend(self._run_user_scenarios(kit, project_dir, kit_dir))

        status = (
            "pass"
            if all(step.status == "pass" for step in steps if step.status != "skipped")
            else "fail"
        )
        notes = "See logs under dev-engine/audit-history for detailed evidence."
        return self._finalize_kit_result(
            kit=kit,
            project_dir=project_dir,
            steps=steps,
            notes=notes,
            status=status,
            started_at=kit_started_at,
            started_monotonic=kit_start_monotonic,
        )

    def _kit_cache_project_dir(self, kit: str) -> Path:
        return self.kit_cache_root / kit.replace(".", "-") / "base-project"

    def _kit_cache_ready(self, project_dir: Path) -> bool:
        if not project_dir.exists():
            return False
        if not (project_dir / ".rapidkit").exists():
            return False
        return (project_dir / "pyproject.toml").exists() or (project_dir / "package.json").exists()

    def _hydrate_kit_project_from_cache(
        self,
        *,
        kit: str,
        project_name: str,
        kit_dir: Path,
        project_dir: Path,
        rapidkit_cmd: Sequence[str],
    ) -> StepResult:
        cache_project_dir = self._kit_cache_project_dir(kit)
        cache_parent = cache_project_dir.parent
        log_path = kit_dir / "create.log"
        if self.rebuild_kit_cache and cache_parent.exists():
            shutil.rmtree(cache_parent)

        if not self._kit_cache_ready(cache_project_dir):
            cache_parent.mkdir(parents=True, exist_ok=True)
            if cache_project_dir.exists():
                shutil.rmtree(cache_project_dir)
            create_cmd = [
                *rapidkit_cmd,
                "create",
                "project",
                kit,
                cache_project_dir.name,
                "--skip-essentials",
                "--output",
                str(cache_parent),
                "--force",
            ]
            if kit.startswith("nestjs"):
                create_cmd.extend(["--variable", "package_manager=npm"])
            cache_result = self._run_kit_step(
                kit,
                step_name=f"create cached {kit}",
                cmd=create_cmd,
                log_path=log_path,
            )
            if cache_result.status != "pass":
                return cache_result

        if project_dir.exists():
            shutil.rmtree(project_dir)
        shutil.copytree(
            cache_project_dir,
            project_dir,
            ignore=shutil.ignore_patterns(
                ".venv",
                "node_modules",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "dist",
                "build",
                ".next",
                ".turbo",
                "__pycache__",
            ),
        )
        self._normalize_cached_project_identity(project_dir=project_dir, project_name=project_name)
        log_path.write_text(
            (
                f"Hydrated project from cached kit base.\n"
                f"kit={kit}\n"
                f"cache={cache_project_dir}\n"
                f"target={project_dir}\n"
            ),
            encoding="utf-8",
        )
        return StepResult(
            name=f"hydrate cached {kit}",
            command=["copytree", str(cache_project_dir), str(project_dir)],
            status="pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary="Hydrated isolated project from cached kit base",
        )

    def _normalize_cached_project_identity(self, *, project_dir: Path, project_name: str) -> None:
        replacements = {"base-project": project_name, "audit-base-project": project_name}
        for relative_path in (
            "pyproject.toml",
            "package.json",
            ".rapidkit/project.json",
            ".rapidkit/rapidkit.json",
        ):
            path = project_dir / relative_path
            if not path.exists() or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            updated = text
            for old, new in replacements.items():
                updated = updated.replace(old, new)
            if updated != text:
                path.write_text(updated, encoding="utf-8")
        marker = project_dir / ".rapidkit" / "cache-hydration.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            json.dumps(
                {
                    "hydratedAt": self._format_timestamp(datetime.utcnow()),
                    "runId": uuid.uuid4().hex,
                    "module": self.module_slug,
                    "projectName": project_name,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def _resolve_dependency_install_order(self, module_slug: str) -> list[str]:
        """Return a topologically ordered list of dependency slugs (excluding module_slug).

        Source-of-truth is `module.yaml` (manifest `depends_on` using canonical slugs).
        """

        resolved_target = expand_module_slug(module_slug, self.modules_root) or module_slug.strip(
            "/"
        )
        manifests = load_all_manifests(self.modules_root)
        if resolved_target not in manifests:
            raise ValueError(
                f"Unable to resolve manifest for '{module_slug}' under {self.modules_root} (missing module.yaml)"
            )

        try:
            ordered = compute_install_order([resolved_target], manifests)
        except (DependencyResolutionError, DependencyCycleError) as exc:
            raise ValueError(str(exc)) from exc

        # ordered includes the target as last; return only deps.
        dep_slugs = [m.slug for m in ordered if m.slug and m.slug != resolved_target]
        return dep_slugs

    def _verify_snippet_injection(
        self, *, kit: str, project_dir: Path, kit_dir: Path
    ) -> StepResult:
        """Ensure snippet injection ran in the installed kit project.

        This checks the *generated project output* for injection markers produced by
        core.services.snippet_injector.inject_snippet_enterprise.
        """

        log_path = kit_dir / "snippets-verify.log"
        cmd = [
            "poetry",
            "run",
            "python",
            "scripts/validate_installed_module_snippets.py",
            "--project-root",
            str(project_dir),
            "--module",
            self.module_slug,
            "--kit",
            kit,
            "--ignore-missing-registry",
        ]
        return self._run_kit_step(
            kit,
            step_name="verify snippets",
            cmd=cmd,
            log_path=log_path,
            cwd=REPO_ROOT,
        )

    def _verify_snippet_registry_state(
        self, *, kit: str, project_dir: Path, kit_dir: Path
    ) -> StepResult:
        log_path = kit_dir / "snippet-registry-health.log"
        registry_path = project_dir / ".rapidkit" / "snippet_registry.json"
        legacy_registry_path = project_dir / "snippet_registry.json"

        lines: list[str] = [
            f"Kit: {kit}",
            f"Project: {project_dir}",
            f"Registry: {registry_path}",
            f"Legacy registry: {legacy_registry_path}",
        ]
        has_snippets, snippet_count = self._module_has_applicable_snippets(kit=kit)
        lines.append(f"Module snippets applicable to kit: {has_snippets} (count={snippet_count})")
        if not registry_path.exists() and not legacy_registry_path.exists():
            lines.append(
                "No snippet_registry.json found; assuming no snippet injections were registered."
            )
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return StepResult(
                name="snippet registry health",
                command=[],
                status="pass",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary=(
                    "No snippet registry present"
                    if not has_snippets
                    else "No snippet registry present (snippets are best-effort)"
                ),
            )

        path_to_read = registry_path if registry_path.exists() else legacy_registry_path

        try:
            payload = json.loads(path_to_read.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            log_path.write_text(
                "\n".join(lines + [f"Failed to read registry: {exc}"]) + "\n", encoding="utf-8"
            )
            return StepResult(
                name="snippet registry health",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="Unreadable snippet registry",
            )

        entries = None
        if isinstance(payload, dict):
            entries = payload.get("snippets")
            if not isinstance(entries, dict):
                entries = payload.get("entries")

        if not isinstance(entries, dict):
            log_path.write_text(
                "\n".join(
                    lines
                    + [
                        "Invalid registry structure: expected mapping at 'snippets' (preferred) or 'entries' (legacy)'"
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            return StepResult(
                name="snippet registry health",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="Invalid snippet registry schema",
            )

        counts: dict[str, int] = {
            "pending": 0,
            "applied": 0,
            "failed": 0,
            "conflicted": 0,
            "unknown": 0,
        }
        problematic: list[str] = []
        for key, entry in entries.items():
            if not isinstance(key, str) or not isinstance(entry, dict):
                continue
            status = entry.get("status")
            status_norm = str(status).strip().lower() if status is not None else "unknown"
            if status_norm not in counts:
                status_norm = "unknown"
            counts[status_norm] += 1
            if status_norm in {"pending", "failed", "conflicted"}:
                problematic.append(key)
        problematic.sort()

        lines.append(f"Total entries: {sum(counts.values())}")
        lines.append(f"Counts: {counts}")
        if problematic:
            lines.append("Problematic keys:")
            lines.extend(f"- {k}" for k in problematic[:MAX_SNIPPET_REGISTRY_KEYS_SHOWN])
            if len(problematic) > MAX_SNIPPET_REGISTRY_KEYS_SHOWN:
                lines.append(f"... ({len(problematic) - MAX_SNIPPET_REGISTRY_KEYS_SHOWN} more)")

        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if problematic:
            return StepResult(
                name="snippet registry health",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary=f"Snippet registry has pending/failed/conflicted ({len(problematic)})",
            )
        if has_snippets and counts.get("applied", 0) <= 0:
            return StepResult(
                name="snippet registry health",
                command=[],
                status="fail",
                duration_s=0.0,
                log_path=self._rel_path(log_path),
                summary="No applied snippets recorded for module with declared snippets",
            )
        return StepResult(
            name="snippet registry health",
            command=[],
            status="pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary="Snippet registry clean",
        )

    def _score_product_for_kit(self, *, kit: str, project_dir: Path, kit_dir: Path) -> StepResult:
        """Compute product_score with kit context (enables snippet injection scoring)."""

        log_path = kit_dir / "product_score-kit.log"
        cmd = [
            sys.executable,
            "scripts/product_score.py",
            "--module",
            self.module_slug,
            "--min-score",
            "0",
            "--installed-project",
            str(project_dir),
            "--kit",
            kit,
            "--output",
            str(kit_dir / "product_score.json"),
        ]
        return self._run_kit_step(
            kit,
            step_name="product_score (kit)",
            cmd=cmd,
            log_path=log_path,
            cwd=REPO_ROOT,
        )

    def _declared_runtime_paths(
        self, *, kit: str, project_dir: Path
    ) -> Tuple[List[Path], List[Path]]:
        """Return materialized and declared runtime outputs for this module/kit pair."""

        manifest_path = self.modules_root / self.module_slug / "module.yaml"
        if not manifest_path.exists():
            return [], []

        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return [], []

        if not isinstance(manifest, Mapping):
            return [], []

        generation = manifest.get("generation")
        if not isinstance(generation, Mapping):
            return [], []

        variants = generation.get("variants")
        if not isinstance(variants, Mapping):
            return [], []

        profile_inherits = manifest.get("profile_inherits")
        variant_keys = [kit]
        if isinstance(profile_inherits, Mapping):
            inherited = profile_inherits.get(kit)
            if isinstance(inherited, str):
                variant_keys.append(inherited)
        if "." in kit:
            variant_keys.append(kit.split(".", 1)[0])

        variant: Any = None
        for key in variant_keys:
            candidate = variants.get(key)
            if isinstance(candidate, Mapping):
                variant = candidate
                break
        if not isinstance(variant, Mapping):
            return [], []

        files = variant.get("files")
        if not isinstance(files, list):
            return [], []

        declared: List[Path] = []
        hits: List[Path] = []
        for entry in files:
            if not isinstance(entry, Mapping):
                continue
            output = entry.get("output")
            if not isinstance(output, str) or not output.strip():
                continue
            output_path = project_dir / output
            declared.append(output_path)
            if output_path.exists():
                hits.append(output_path)

        return hits, declared

    def _verify_install_layout(self, *, kit: str, project_dir: Path, kit_dir: Path) -> StepResult:
        slug_parts = [part for part in self.module_slug.split("/") if part]
        expected_base = project_dir / "src" / "modules" / Path(*slug_parts)
        leaf = slug_parts[-1] if slug_parts else self.module_slug
        vendor_base = project_dir / ".rapidkit" / "vendor" / leaf
        log_path = kit_dir / "layout-check.log"
        declared_runtime_hits, declared_runtime_paths = self._declared_runtime_paths(
            kit=kit, project_dir=project_dir
        )

        legacy_candidates: List[Path] = []
        if len(slug_parts) >= MIN_MODULE_SLUG_PARTS_FOR_LEGACY_LAYOUT:
            legacy_candidates.append(project_dir / "src" / slug_parts[1] / f"{slug_parts[2]}.py")
            legacy_candidates.append(project_dir / "src" / "routers" / f"{slug_parts[2]}.py")
            legacy_candidates.append(project_dir / "src" / slug_parts[2])

        exists = expected_base.exists()
        vendor_exists = vendor_base.exists()
        file_count = sum(1 for path in expected_base.rglob("*") if path.is_file()) if exists else 0
        vendor_file_count = (
            sum(1 for path in vendor_base.rglob("*") if path.is_file()) if vendor_exists else 0
        )
        legacy_hits = [path for path in legacy_candidates if path.exists()]

        nested_duplicate = None
        forbidden_health = None
        if exists and expected_base.is_dir() and slug_parts:
            leaf = slug_parts[-1]
            candidate = expected_base / leaf
            if candidate.exists() and candidate.is_dir():
                nested_duplicate = candidate
            # Canonical health policy: health artefacts must live under `src/health/**`.
            # A module-local `src/modules/<slug>/health/**` folder is always forbidden.
            candidate_health = expected_base / "health"
            if candidate_health.exists() and candidate_health.is_dir():
                forbidden_health = candidate_health

        log_lines = [
            f"Module: {self.module_slug}",
            f"Kit: {kit}",
            f"Expected base: {expected_base}",
            f"Exists: {exists}",
            f"Files under expected base: {file_count}",
            f"Vendor base: {vendor_base}",
            f"Vendor exists: {vendor_exists}",
            f"Files under vendor base: {vendor_file_count}",
        ]
        if declared_runtime_paths:
            log_lines.append("Declared runtime outputs:")
            log_lines.extend(str(path) for path in declared_runtime_paths)
        if declared_runtime_hits:
            log_lines.append("Materialized declared runtime outputs:")
            log_lines.extend(str(path) for path in declared_runtime_hits)
        if nested_duplicate is not None:
            log_lines.append(f"Nested duplicate module folder detected: {nested_duplicate}")
        if forbidden_health is not None:
            log_lines.append(
                "Forbidden health folder under module base (canonical health expects src/health): "
                f"{forbidden_health}"
            )
        allow_vendor_runtime_paths = vendor_exists and not exists
        if legacy_hits and allow_vendor_runtime_paths:
            log_lines.append("Category-level runtime paths present for vendor-backed module:")
            log_lines.extend(str(hit) for hit in legacy_hits)
        elif legacy_hits:
            log_lines.append("Legacy paths present (should be absent):")
            log_lines.extend(str(hit) for hit in legacy_hits)
        else:
            log_lines.append("No legacy paths detected.")

        log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

        if not exists and not vendor_exists:
            summary = "Expected module base missing under src/modules and vendor snapshot missing"
            status = "fail"
        elif exists and file_count == 0:
            summary = "Expected module base is empty"
            status = "fail"
        elif vendor_exists and vendor_file_count == 0:
            summary = "Vendor snapshot exists but is empty"
            status = "fail"
        elif allow_vendor_runtime_paths and not legacy_hits and not declared_runtime_hits:
            summary = "Vendor snapshot exists but no declared runtime path was materialized"
            status = "fail"
        elif nested_duplicate is not None:
            summary = "Nested duplicate module folder present"
            status = "fail"
        elif forbidden_health is not None:
            summary = "Forbidden health folder present under module base"
            status = "fail"
        elif legacy_hits and not allow_vendor_runtime_paths:
            summary = "Legacy module paths still present"
            status = "fail"
        else:
            summary = (
                "Module installed under src/modules path"
                if exists
                else "Module materialized as vendor-backed snapshot with declared runtime paths"
            )
            status = "pass"

        return StepResult(
            name="check module layout",
            command=[],
            status=status,
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary=summary,
        )

    def _run_python_project_checks(self, kit: str, project_dir: Path) -> List[StepResult]:
        steps: List[StepResult] = []
        poetry_cmd = self._poetry_command_for_project(project_dir)
        # Always run Poetry in a sanitized environment.
        # In particular, disable secretstorage-backed keyrings so Poetry doesn't try
        # to talk to DBus on headless agents.
        poetry_env = self._kit_python_env()

        lock_path = project_dir / "poetry.lock"
        if self.deterministic_deps and lock_path.exists():
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name="poetry check --lock",
                    cmd=poetry_cmd + ["check", "--lock"],
                    log_path=project_dir / "poetry-check-lock.log",
                    cwd=project_dir,
                    env=poetry_env,
                )
            )
        else:
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name="poetry lock",
                    cmd=poetry_cmd + ["lock"],
                    log_path=project_dir / "poetry-lock.log",
                    cwd=project_dir,
                    env=poetry_env,
                )
            )

        install_cmd = poetry_cmd + ["install", "--no-root"]
        if self.deterministic_deps and lock_path.exists():
            install_cmd.append("--sync")
        steps.append(
            self._run_kit_step(
                kit,
                step_name="poetry install",
                cmd=install_cmd,
                log_path=project_dir / "poetry-install.log",
                cwd=project_dir,
                env=poetry_env,
            )
        )
        pytest_step = self._run_kit_step(
            kit,
            step_name="pytest",
            cmd=poetry_cmd + ["run", "pytest", "-q"],
            log_path=project_dir / "pytest.log",
            cwd=project_dir,
            env=poetry_env,
        )
        self._attach_test_metrics(pytest_step, "pytest")
        steps.append(pytest_step)
        steps.extend(
            self._run_security_scan_python(
                kit=kit,
                project_dir=project_dir,
                poetry_cmd=poetry_cmd,
                env=poetry_env,
            )
        )
        steps.append(
            self._run_fastapi_health_probe(
                kit=kit,
                project_dir=project_dir,
                poetry_cmd=poetry_cmd,
                env=poetry_env,
            )
        )
        if self.pro_gates:
            steps.append(self._run_bandit_sast(kit=kit, project_dir=project_dir))
            steps.append(self._run_secret_scan(kit=kit, project_dir=project_dir))
            steps.append(
                self._run_license_audit_python(
                    kit=kit,
                    project_dir=project_dir,
                    poetry_cmd=poetry_cmd,
                    env=poetry_env,
                )
            )
            steps.append(self._run_ci_parity_check(kit=kit, project_dir=project_dir))
            steps.append(self._run_docker_smoke(kit=kit, project_dir=project_dir))
        return steps

    def _rapidkit_cmd(self) -> List[str]:
        """Return a stable RapidKit CLI command.

        Prefer the repository's Poetry virtualenv entrypoint so we don't
        accidentally invoke a globally-installed `rapidkit` (e.g. an npm CLI).
        """

        venv_bin = REPO_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
        for exe_name in ("rapidkit.exe", "rapidkit"):
            candidate = venv_bin / exe_name
            if candidate.exists():
                return [str(candidate)]

        # Fallbacks: best-effort PATH resolution.
        if shutil.which("poetry"):
            return ["poetry", "run", "rapidkit"]
        return ["rapidkit"]

    def _poetry_command_for_project(self, project_dir: Path) -> List[str]:
        """Return the Poetry command to use for a generated kit project.

        Important: using `python -m poetry` is brittle because Poetry is often installed as
        a standalone executable (pipx/system) and not importable from the active interpreter.
        For stabilization runs we prefer the `poetry` executable whenever available.
        """

        if shutil.which("poetry"):
            return ["poetry"]

        # Best-effort fallback: keep the previous behaviour if Poetry is importable.
        pyproject = project_dir / "pyproject.toml"
        if not pyproject.exists():
            return ["poetry"]
        try:
            content = pyproject.read_text(encoding="utf-8")
        except OSError:
            return ["poetry"]
        if not PY310_REQ_PATTERN.search(content):
            return ["poetry"]
        python_exe = shutil.which("python3.10")
        if not python_exe:
            return ["poetry"]
        return [python_exe, "-m", "poetry"]

    def _kit_python_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        env.pop("POETRY_ACTIVE", None)
        env.setdefault("POETRY_NO_INTERACTION", "1")
        env.setdefault("POETRY_VIRTUALENVS_IN_PROJECT", "1")
        env.setdefault("POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON", "1")
        # Disable secretstorage-backed keyrings so Poetry doesn't try to talk to DBus
        # on headless CI agents where no session bus exists.
        env.setdefault("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")
        return env

    def _run_node_project_checks(self, kit: str, project_dir: Path) -> List[StepResult]:
        steps: List[StepResult] = []
        runner = ["yarn"] if (project_dir / "yarn.lock").exists() else ["npm"]
        pm = runner[0]

        install_cmd: List[str]
        if pm == "yarn":
            install_cmd = ["yarn", "install"]
            if self.deterministic_deps and (project_dir / "yarn.lock").exists():
                if (project_dir / ".yarnrc.yml").exists():
                    install_cmd.append("--immutable")
                else:
                    install_cmd.append("--frozen-lockfile")
        elif self.deterministic_deps and (project_dir / "package-lock.json").exists():
            install_cmd = ["npm", "ci"]
        else:
            install_cmd = ["npm", "install"]

        install_step = self._run_kit_step(
            kit,
            step_name=f"{pm} install",
            cmd=install_cmd,
            log_path=project_dir / f"{pm}-install.log",
            cwd=project_dir,
        )
        steps.append(self._enforce_engine_policy(install_step))
        if pm == "yarn":
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name="yarn lint",
                    cmd=["yarn", "lint"],
                    log_path=project_dir / "yarn-lint.log",
                    cwd=project_dir,
                )
            )
            yarn_test = self._run_kit_step(
                kit,
                step_name="yarn test",
                cmd=["yarn", "test", "--runInBand"],
                log_path=project_dir / "yarn-test.log",
                cwd=project_dir,
            )
            self._attach_test_metrics(yarn_test, "jest")
            steps.append(yarn_test)
        else:
            steps.append(
                self._run_kit_step(
                    kit,
                    step_name="npm lint",
                    cmd=["npm", "run", "lint", "--if-present"],
                    log_path=project_dir / "npm-lint.log",
                    cwd=project_dir,
                )
            )
            npm_test = self._run_kit_step(
                kit,
                step_name="npm test",
                cmd=["npm", "test", "--", "--runInBand"],
                log_path=project_dir / "npm-test.log",
                cwd=project_dir,
            )
            self._attach_test_metrics(npm_test, "jest")
            steps.append(npm_test)
        steps.append(
            self._run_security_lint_node(
                kit=kit,
                project_dir=project_dir,
            )
        )
        steps.extend(
            self._run_security_scan_node(
                kit=kit,
                project_dir=project_dir,
                runner=runner,
            )
        )
        steps.append(
            self._run_kit_step(
                kit,
                step_name=f"{pm} build",
                cmd=runner + ["run", "build"],
                log_path=project_dir / f"{pm}-build.log",
                cwd=project_dir,
            )
        )
        steps.append(self._run_nestjs_health_probe(kit=kit, project_dir=project_dir, runner=runner))
        if self.pro_gates:
            steps.append(self._run_secret_scan(kit=kit, project_dir=project_dir))
            steps.append(self._run_license_audit_node(kit=kit, project_dir=project_dir))
            steps.append(self._run_ci_parity_check(kit=kit, project_dir=project_dir))
            steps.append(self._run_docker_smoke(kit=kit, project_dir=project_dir))
        return steps

    def _run_bandit_sast(self, *, kit: str, project_dir: Path) -> StepResult:
        """Run Bandit against the generated Python project's source tree."""

        log_path = project_dir / "bandit.log"
        cmd = [
            "poetry",
            "run",
            "bandit",
            "-q",
            "-r",
            str(project_dir / "src"),
        ]
        return self._run_kit_step(
            kit,
            step_name="sast (bandit)",
            cmd=cmd,
            log_path=log_path,
            cwd=REPO_ROOT,
        )

    def _iter_scan_files(self, root: Path) -> Iterable[Path]:
        skip_dirs = {
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".tox",
        }
        for base, dirs, files in os.walk(root):
            base_path = Path(base)
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            for name in files:
                if name.startswith("."):
                    continue
                path = base_path / name
                suffix = path.suffix.lower()
                if suffix in {
                    ".py",
                    ".pyi",
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".json",
                    ".yml",
                    ".yaml",
                    ".toml",
                    ".env",
                    ".md",
                    ".txt",
                    ".ini",
                    ".cfg",
                } or path.name in {"Dockerfile", "docker-compose.yml"}:
                    yield path

    def _run_secret_scan(self, *, kit: str, project_dir: Path) -> StepResult:
        """Deterministic secret scan (high-confidence patterns only)."""

        log_path = project_dir / "secret-scan.log"
        findings: list[str] = []

        patterns: list[tuple[str, re.Pattern[str]]] = [
            (
                "private_key_block",
                re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----"),
            ),
            ("aws_access_key_id", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
            ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
        ]

        for path in self._iter_scan_files(project_dir):
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for label, pattern in patterns:
                if pattern.search(raw):
                    findings.append(f"{label}: {self._rel_path(path)}")

        lines = [f"Project: {project_dir}"]
        if findings:
            lines.append("Findings:")
            lines.extend(f"- {item}" for item in findings)
        else:
            lines.append("No high-confidence secrets detected.")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return StepResult(
            name="secret scan",
            command=[],
            status="fail" if findings else "pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary=f"findings={len(findings)}" if findings else "clean",
        )

    def _run_license_audit_python(
        self,
        *,
        kit: str,
        project_dir: Path,
        poetry_cmd: List[str],
        env: Mapping[str, str] | None,
    ) -> StepResult:
        """Collect dependency license info and enforce a denylist."""

        log_path = project_dir / "license-audit-python.log"
        start = time.time()

        deny_tokens = [
            t.strip().upper() for t in re.split(r"[;,]", PRO_LICENSE_DENYLIST) if t.strip()
        ]

        script = (
            "import json\n"
            "from importlib import metadata\n"
            "items=[]\n"
            "for dist in metadata.distributions():\n"
            "  name = dist.metadata.get('Name') or ''\n"
            "  version = dist.version\n"
            "  license_text = (dist.metadata.get('License') or '').strip()\n"
            "  classifiers = dist.metadata.get_all('Classifier') or []\n"
            "  if not license_text:\n"
            "    for c in classifiers:\n"
            "      if isinstance(c,str) and c.startswith('License ::'):\n"
            "        license_text = c\n"
            "        break\n"
            "  items.append({'name':name,'version':version,'license':license_text})\n"
            "print(json.dumps(items))\n"
        )

        proc = subprocess.run(
            poetry_cmd + ["run", "python", "-c", script],
            check=False,
            cwd=str(project_dir),
            env=dict(env) if env is not None else None,
            capture_output=True,
            text=True,
        )
        raw = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        duration = time.time() - start

        denied: list[str] = []
        unknown = 0
        parsed_ok = False
        try:
            payload = json.loads(raw) if raw else []
            parsed_ok = isinstance(payload, list)
        except json.JSONDecodeError:
            payload = []

        if parsed_ok:
            for item in payload:
                if not isinstance(item, dict):
                    continue
                lic = str(item.get("license") or "").strip()
                if not lic:
                    unknown += 1
                    continue
                lic_upper = lic.upper()
                if any(tok and tok in lic_upper for tok in deny_tokens):
                    denied.append(f"{item.get('name')}@{item.get('version')}: {lic}")

        lines: list[str] = [
            f"denylist={deny_tokens}",
            f"unknown={unknown}",
            f"denied={len(denied)}",
        ]
        if denied:
            lines.append("Denied licenses:")
            lines.extend(f"- {d}" for d in denied[:200])
        if stderr:
            lines.append("stderr:")
            lines.append(stderr)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        if proc.returncode != 0 or not parsed_ok:
            return StepResult(
                name="license audit (python)",
                command=poetry_cmd + ["run", "python", "-c", "<license-script>"],
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary="license audit failed",
            )
        if denied:
            return StepResult(
                name="license audit (python)",
                command=poetry_cmd + ["run", "python", "-c", "<license-script>"],
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"denied={len(denied)}",
            )
        if PRO_FAIL_ON_UNKNOWN_LICENSE and unknown:
            return StepResult(
                name="license audit (python)",
                command=poetry_cmd + ["run", "python", "-c", "<license-script>"],
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"unknown={unknown}",
            )
        return StepResult(
            name="license audit (python)",
            command=poetry_cmd + ["run", "python", "-c", "<license-script>"],
            status="pass",
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=f"unknown={unknown}, denied=0",
        )

    def _run_license_audit_node(self, *, kit: str, project_dir: Path) -> StepResult:
        """Minimal license sanity checks for Node projects."""

        log_path = project_dir / "license-audit-node.log"
        pkg_path = project_dir / "package.json"
        license_file = project_dir / "LICENSE"
        errors: list[str] = []
        declared = ""
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
            declared = str(pkg.get("license") or "").strip()
        except Exception as exc:
            errors.append(f"failed to read package.json: {exc}")

        if not declared:
            errors.append("package.json missing license field")
        if not license_file.exists():
            errors.append("LICENSE file missing")

        deny_tokens = [
            t.strip().upper() for t in re.split(r"[;,]", PRO_LICENSE_DENYLIST) if t.strip()
        ]
        if declared and any(tok and tok in declared.upper() for tok in deny_tokens):
            errors.append(f"declared license denied: {declared}")

        lines = [f"declared={declared or '<missing>'}", f"denylist={deny_tokens}"]
        if errors:
            lines.append("Errors:")
            lines.extend(f"- {e}" for e in errors)
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return StepResult(
            name="license audit (node)",
            command=[],
            status="fail" if errors else "pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary=f"errors={len(errors)}" if errors else "ok",
        )

    def _run_ci_parity_check(self, *, kit: str, project_dir: Path) -> StepResult:
        """Ensure generated CI workflow pins toolchains (CI parity gate)."""

        log_path = project_dir / "ci-parity.log"
        workflow_path = project_dir / ".github" / "workflows" / "ci.yml"
        errors: list[str] = []
        content = ""
        if not workflow_path.exists():
            errors.append("Missing .github/workflows/ci.yml")
        else:
            try:
                content = workflow_path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"Unable to read ci.yml: {exc}")

        if content:
            if kit.startswith("fastapi") and EXPECTED_PYTHON_VERSION not in content:
                errors.append(f"CI does not pin Python {EXPECTED_PYTHON_VERSION}")
            if kit.startswith("nestjs") and EXPECTED_NODE_VERSION not in content:
                errors.append(f"CI does not pin Node {EXPECTED_NODE_VERSION}")
            if self.deterministic_deps:
                if (
                    kit.startswith("nestjs")
                    and "npm ci" not in content
                    and "--frozen-lockfile" not in content
                ):
                    errors.append(
                        "CI does not appear to use deterministic Node install (npm ci / frozen lockfile)"
                    )
                if (
                    kit.startswith("fastapi")
                    and "poetry check" not in content
                    and "poetry lock" not in content
                ):
                    # CI parity: accept deterministic install commands as sufficient evidence.
                    # We do not require `poetry lock` regeneration in CI, but we do want a
                    # lock-respecting install (sync/frozen semantics).
                    if (
                        "poetry install" in content
                        and "--sync" in content
                        or "poetry sync" in content
                    ):
                        pass
                    else:
                        errors.append(
                            "CI does not appear to validate Poetry lock determinism (expected poetry sync or poetry install --sync)"
                        )

        lines = [f"workflow={workflow_path}"]
        if errors:
            lines.append("Errors:")
            lines.extend(f"- {e}" for e in errors)
        else:
            lines.append("CI parity ok")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return StepResult(
            name="ci parity",
            command=[],
            status="fail" if errors else "pass",
            duration_s=0.0,
            log_path=self._rel_path(log_path),
            summary=f"errors={len(errors)}" if errors else "ok",
        )

    def _run_security_scan_python(
        self,
        *,
        kit: str,
        project_dir: Path,
        poetry_cmd: List[str],
        env: Mapping[str, str] | None,
    ) -> List[StepResult]:
        """Run security lint (ruff) and Python SCA (pip-audit)."""

        steps: List[StepResult] = []
        cmd = poetry_cmd + ["run", "ruff", "check", "src", "--select", "S"]
        log_path = project_dir / "security-ruff.log"
        steps.append(
            self._run_kit_step(
                kit,
                step_name="security lint (ruff)",
                cmd=cmd,
                log_path=log_path,
                cwd=project_dir,
                env=env,
            )
        )
        steps.append(
            self._run_python_sca(
                kit=kit,
                project_dir=project_dir,
                poetry_cmd=poetry_cmd,
                env=env,
            )
        )
        return steps

    def _run_python_sca(
        self,
        *,
        kit: str,
        project_dir: Path,
        poetry_cmd: List[str],
        env: Mapping[str, str] | None,
    ) -> StepResult:
        """Run pip-audit against exported requirements with severity awareness."""

        self._log_kit(kit, "pip-audit …")

        log_path = project_dir / "pip-audit.log"
        req_path = project_dir / "pip-audit-requirements.txt"
        start = time.time()

        export_cmd = poetry_cmd + [
            "export",
            "--format",
            "requirements.txt",
            "--without-hashes",
            "--output",
            str(req_path),
        ]
        logs: list[str] = []

        def _run_export() -> subprocess.CompletedProcess[str]:
            proc = subprocess.run(
                export_cmd,
                check=False,
                cwd=str(project_dir),
                env=dict(env) if env is not None else None,
                capture_output=True,
                text=True,
            )
            logs.append("$ " + " ".join(export_cmd))
            logs.append(proc.stdout or "")
            logs.append(proc.stderr or "")
            return proc

        export_proc = _run_export()
        if export_proc.returncode != 0:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            stderr = export_proc.stderr or ""
            hint = (
                " (missing poetry-plugin-export)"
                if "command export does not exist" in stderr
                else ""
            )
            summary = f"pip-audit export failed (exit {export_proc.returncode}){hint}"
            duration = time.time() - start
            return StepResult(
                name="pip-audit",
                command=export_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=summary,
            )

        audit_cmd = [
            sys.executable,
            "-m",
            "pip_audit",
            "--requirement",
            str(req_path),
            "--format",
            "json",
            "--timeout",
            "60",
            "--progress-spinner",
            "off",
        ]

        audit_proc = subprocess.run(
            audit_cmd,
            check=False,
            cwd=str(project_dir),
            env=dict(env) if env is not None else None,
            capture_output=True,
            text=True,
        )

        logs.append("$ " + " ".join(audit_cmd))
        logs.append(audit_proc.stdout or "")
        logs.append(audit_proc.stderr or "")

        def _should_skip_pip_audit(proc: subprocess.CompletedProcess[str]) -> bool:
            if self.pro_gates:
                return False
            if proc.returncode in (0, 1):
                return False
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            haystack = combined.lower()
            retryable_markers = (
                "connection reset",
                "connection aborted",
                "connectionerror",
                "network is unreachable",
                "temporary failure",
                "name resolution",
                "failed to establish a new connection",
                "timed out",
                "certificate verify failed",
                "ssl",
                "proxyerror",
                "failed to upgrade `pip`",
                "failed to upgrade 'pip'",
                'failed to upgrade "pip"',
            )
            return any(marker in haystack for marker in retryable_markers)

        sbom_path = project_dir / "sbom.cyclonedx.json"
        if self.pro_gates:
            sbom_cmd = [
                sys.executable,
                "-m",
                "pip_audit",
                "--requirement",
                str(req_path),
                "--format",
                "cyclonedx-json",
                "--timeout",
                "60",
                "--progress-spinner",
                "off",
            ]
            sbom_proc = subprocess.run(
                sbom_cmd,
                check=False,
                cwd=str(project_dir),
                env=dict(env) if env is not None else None,
                capture_output=True,
                text=True,
            )
            logs.append("$ " + " ".join(sbom_cmd))
            logs.append(sbom_proc.stdout or "")
            logs.append(sbom_proc.stderr or "")

            def _extract_first_json_value(text: str) -> object | None:
                decoder = json.JSONDecoder()
                for idx, ch in enumerate(text):
                    if ch not in ("{", "["):
                        continue
                    try:
                        value, _ = decoder.raw_decode(text[idx:])
                    except json.JSONDecodeError:
                        continue
                    return value
                return None

            sbom_payload = _extract_first_json_value(sbom_proc.stdout or "")
            if sbom_proc.returncode != 0 or sbom_payload is None:
                # Fail closed: pro gate requires an actual SBOM payload.
                log_path.write_text("\n".join(logs), encoding="utf-8")
                duration = time.time() - start
                return StepResult(
                    name="pip-audit",
                    command=audit_cmd,
                    status="fail",
                    duration_s=duration,
                    log_path=self._rel_path(log_path),
                    summary=(
                        f"high=0, critical=0, sbom generation failed (exit {sbom_proc.returncode})"
                    ),
                    metadata={
                        "sca": {
                            "tool": "pip-audit",
                            "high": 0,
                            "critical": 0,
                            "vulnerabilities": [],
                        }
                    },
                )

            try:
                # Pretty print for deterministic diffs.
                sbom_path.write_text(
                    json.dumps(sbom_payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                log_path.write_text("\n".join(logs), encoding="utf-8")
                duration = time.time() - start
                return StepResult(
                    name="pip-audit",
                    command=audit_cmd,
                    status="fail",
                    duration_s=duration,
                    log_path=self._rel_path(log_path),
                    summary="high=0, critical=0, sbom write failed",
                )
        log_path.write_text("\n".join(logs), encoding="utf-8")

        if _should_skip_pip_audit(audit_proc):
            duration = time.time() - start
            return StepResult(
                name="pip-audit",
                command=audit_cmd,
                status="skipped",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary="high=0, critical=0, pip-audit skipped (transient environment/network error)",
                metadata={
                    "sca": {
                        "tool": "pip-audit",
                        "high": 0,
                        "critical": 0,
                        "vulnerabilities": [],
                    }
                },
            )

        high_count, critical_count, vulnerabilities, parsed_ok = self._parse_pip_audit(
            audit_proc.stdout or ""
        )
        status = "fail" if critical_count > 0 else "pass"
        summary_parts = [f"high={high_count}", f"critical={critical_count}"]
        if high_count > 0 and critical_count == 0:
            summary_parts.append("warnings: high severity present")
        if not parsed_ok:
            status = "fail"
            summary_parts.append("unparseable JSON output")
        if audit_proc.returncode not in (0, 1):
            status = "fail"
            summary_parts.append(f"audit error (exit {audit_proc.returncode})")
        summary = ", ".join(summary_parts)

        duration = time.time() - start
        metadata: dict[str, Any] = {
            "sca": {
                "tool": "pip-audit",
                "high": high_count,
                "critical": critical_count,
                "vulnerabilities": vulnerabilities,
            }
        }
        if self.pro_gates:
            metadata["sbom"] = {
                "format": "cyclonedx-json",
                "path": self._rel_path(sbom_path),
            }

        return StepResult(
            name="pip-audit",
            command=audit_cmd,
            status=status,
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=summary,
            metadata=metadata,
        )

    def _run_security_scan_node(
        self,
        *,
        kit: str,
        project_dir: Path,
        runner: List[str],
    ) -> List[StepResult]:
        """Run npm/yarn audit checks for prod and dev dependencies."""

        pm = runner[0]
        steps: List[StepResult] = []
        if pm == "yarn":
            prod_cmd = [pm, "audit", "--level", "high", "--environment", "production", "--json"]
            dev_cmd = [pm, "audit", "--level", "critical", "--json"]
        else:
            prod_cmd = [pm, "audit", "--production", "--audit-level", "high", "--json"]
            dev_cmd = [pm, "audit", "--audit-level", "critical", "--json"]
        steps.append(
            self._run_node_audit(
                kit=kit,
                project_dir=project_dir,
                pm=pm,
                cmd=prod_cmd,
                step_name=f"{pm} audit (prod high)",
                warn_on_high=False,
            )
        )
        steps.append(
            self._run_node_audit(
                kit=kit,
                project_dir=project_dir,
                pm=pm,
                cmd=dev_cmd,
                step_name=f"{pm} audit (dev critical)",
                warn_on_high=True,
            )
        )
        return steps

    def _run_node_audit(
        self,
        *,
        kit: str,
        project_dir: Path,
        pm: str,
        cmd: Sequence[str],
        step_name: str,
        warn_on_high: bool,
    ) -> StepResult:
        self._log_kit(kit, f"{step_name} …")
        log_path = project_dir / f"{pm}-audit-{self._slugify(step_name, fallback='audit')}.log"
        start = time.time()
        proc = subprocess.run(
            cmd,
            check=False,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        log_path.write_text(combined, encoding="utf-8")

        high_count, critical_count, parsed_ok = self._parse_npm_audit(combined)
        summary = f"high={high_count}, critical={critical_count}"

        # Fail-closed when audit output cannot be parsed.
        if not parsed_ok:
            status = "fail"
            summary = f"Unparseable audit output (exit {proc.returncode})"
        # npm/yarn return codes can be non-zero when vulnerabilities exist.
        # Treat exit codes outside the expected range as execution errors.
        elif proc.returncode not in (0, 1):
            status = "fail"
            summary += f" (audit error: exit {proc.returncode})"
        else:
            status = "pass"
            if critical_count > 0:
                status = "fail"
            elif warn_on_high:
                if high_count > 0 and self.strict_dev_audit_high:
                    status = "fail"
                    summary += " (high severity in dev deps)"
                elif high_count > 0:
                    status = "pass"
                    summary += " (warnings: high severity in dev deps)"
            elif high_count > 0:
                status = "fail"

        duration = time.time() - start
        metadata = {
            "sca": {
                "tool": f"{pm} audit",
                "high": high_count,
                "critical": critical_count,
            }
        }
        return StepResult(
            name=step_name,
            command=list(cmd),
            status=status,
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=summary,
            metadata=metadata,
        )

    def _run_security_lint_node(self, *, kit: str, project_dir: Path) -> StepResult:
        """Run eslint with eslint-plugin-security on NestJS/Node kits."""

        config = self._node_eslint_config(project_dir)
        targets = [path for path in ("src", "apps", "libs") if (project_dir / path).exists()] or [
            "src"
        ]
        install_cmd = [
            "npm",
            "install",
            "--no-save",
            "--no-package-lock",
            f"eslint@{PINNED_ESLINT_VERSION}",
            f"eslint-plugin-security@{PINNED_ESLINT_SECURITY_PLUGIN_VERSION}",
        ]
        install_log = project_dir / "eslint-security-install.log"
        install_step = self._run_kit_step(
            kit,
            step_name="install eslint-plugin-security",
            cmd=install_cmd,
            log_path=install_log,
            cwd=project_dir,
        )
        install_step = self._enforce_engine_policy(install_step)
        if install_step.status != "pass":
            return install_step
        cmd = [
            "npx",
            "--yes",
            "--package",
            f"eslint@{PINNED_ESLINT_VERSION}",
            "--package",
            f"eslint-plugin-security@{PINNED_ESLINT_SECURITY_PLUGIN_VERSION}",
            "eslint",
            "--no-error-on-unmatched-pattern",
            "--plugin",
            "security",
            "--rule",
            "security/detect-object-injection:error",
            "--rule",
            "security/detect-non-literal-fs-filename:error",
        ]
        if config:
            cmd.extend(["--config", config])
        else:
            cmd.append("--no-eslintrc")
        cmd.extend(targets)
        log_path = project_dir / "eslint-security.log"
        return self._run_kit_step(
            kit,
            step_name="security lint (eslint)",
            cmd=cmd,
            log_path=log_path,
            cwd=project_dir,
        )

    def _node_eslint_config(self, project_dir: Path) -> str | None:
        for candidate in (
            project_dir / "eslint.config.js",
            project_dir / ".eslintrc.js",
            project_dir / ".eslintrc.cjs",
            project_dir / ".eslintrc.json",
            project_dir / ".eslintrc",
        ):
            if candidate.exists():
                return str(candidate)
        return None

    def _run_fastapi_health_probe(
        self,
        kit: str,
        project_dir: Path,
        poetry_cmd: List[str],
        env: Mapping[str, str] | None,
    ) -> StepResult:
        port = self._reserve_port()
        host = "127.0.0.1"
        self._log_kit(kit, f"Starting FastAPI health probe on {host}:{port}")
        cmd = poetry_cmd + [
            "run",
            "uvicorn",
            "src.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ]
        log_path = project_dir / "fastapi-health.log"
        result = self._run_health_probe(
            name="fastapi health probe",
            cmd=cmd,
            cwd=project_dir,
            env=dict(env) if env is not None else None,
            log_path=log_path,
            host=host,
            port=port,
            urls=self._health_url_candidates(host, port),
        )
        self._log_kit(kit, f"FastAPI health probe {result.status.upper()} (log: {result.log_path})")
        return result

    def _run_nestjs_health_probe(
        self, kit: str, project_dir: Path, runner: List[str]
    ) -> StepResult:
        port = self._reserve_port()
        host = "127.0.0.1"
        cmd = ["yarn", "start"] if runner[0] == "yarn" else ["npm", "run", "start"]
        self._log_kit(kit, f"Starting NestJS health probe using {cmd[0]} on {host}:{port}")
        env = os.environ.copy()
        env.setdefault("HOST", host)
        env.setdefault("PORT", str(port))
        log_path = project_dir / f"{runner[0]}-health.log"
        result = self._run_health_probe(
            name="nestjs health probe",
            cmd=cmd,
            cwd=project_dir,
            env=env,
            log_path=log_path,
            host=host,
            port=port,
            urls=self._health_url_candidates(host, port),
            startup_timeout=60.0,
        )
        self._log_kit(kit, f"NestJS health probe {result.status.upper()} (log: {result.log_path})")
        return result

    def _run_health_probe(
        self,
        name: str,
        cmd: Sequence[str],
        cwd: Path,
        env: Mapping[str, str] | None,
        log_path: Path,
        host: str,
        port: int,
        urls: Sequence[str],
        startup_timeout: float = 30.0,
    ) -> StepResult:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()
        with log_path.open("w", encoding="utf-8") as stream:
            health_metadata: dict[str, Any] = {}
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                env=dict(env) if env is not None else None,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                self._wait_for_port(host, port, timeout=startup_timeout, proc=proc)
                url, status_code, body = self._probe_health_urls(urls)
                snippet = body.strip().splitlines()
                preview = snippet[0][:200] if snippet else ""
                health_metadata["url"] = url
                health_metadata["status_code"] = status_code
                analyzed, missing = self._analyze_health_payload(body)
                health_metadata.update(analyzed)
                if missing:
                    health_metadata["issues"] = missing
                if self.strict_health and missing:
                    raise ValueError("; ".join(missing))
                summary = f"{status_code} {url} {preview}".strip()
                status = "pass"
            except (TimeoutError, RuntimeError, OSError, urllib.error.URLError, ValueError) as exc:
                summary = f"Health probe failed: {exc}"
                status = "fail"
            finally:
                self._terminate_process(proc)
        duration = time.time() - start
        return StepResult(
            name=name,
            command=list(cmd),
            status=status,
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=summary,
            metadata={"health": health_metadata} if status == "pass" else None,
        )

    def _reserve_port(self) -> int:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    def _wait_for_port(
        self,
        host: str,
        port: int,
        *,
        timeout: float,
        proc: subprocess.Popen[bytes] | subprocess.Popen[str] | None = None,
    ) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if proc is not None and proc.poll() is not None:
                raise RuntimeError(f"server exited with code {proc.returncode}")
            with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                sock.settimeout(1.0)
                try:
                    sock.connect((host, port))
                    return
                except OSError:
                    time.sleep(0.3)
        raise TimeoutError(f"Timed out waiting for {host}:{port} to accept connections")

    def _terminate_process(self, proc: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
        if proc.poll() is not None:
            return
        with contextlib.suppress(ProcessLookupError):
            proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()

    def _probe_health_urls(self, urls: Sequence[str]) -> Tuple[str, int, str]:
        errors: List[str] = []
        for url in urls:
            try:
                status, body = self._http_get(url)
            except (TimeoutError, OSError, urllib.error.URLError, ValueError) as exc:
                errors.append(f"{url}: {exc}")
                continue
            if HTTP_SUCCESS_MIN <= status <= HTTP_SUCCESS_MAX:
                return url, status, body
            errors.append(f"{url}: status {status}")
        raise RuntimeError("; ".join(errors) or "No responsive health endpoints")

    def overall_status(self) -> str:
        return self._overall_status()

    def _http_get(self, url: str, timeout: float = 15.0) -> Tuple[int, str]:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "rapidkit-stabilization-runner/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read().decode("utf-8", errors="ignore")
                return response.getcode(), data
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            return exc.code, body

    def _health_url_candidates(self, host: str, port: int) -> List[str]:
        slug = self.health_slug
        nested = slug.replace("-", "/")
        paths = [
            f"/api/health/module/{slug}",
            "/api/health",
            "/health",
            f"/{slug}",
            f"/{slug}/health",
            f"/{nested}",
            f"/{nested}/health",
        ]
        urls: List[str] = []
        seen: set[str] = set()
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            urls.append(f"http://{host}:{port}{path}")
        return urls

    def _run_docker_smoke(self, *, kit: str, project_dir: Path) -> StepResult:
        """Build and run the generated project container, then probe health.

        This is an opt-in pro gate (enable via --pro-gates) because it requires
        Docker to be installed and the daemon to be available.
        """

        log_path = project_dir / "docker-smoke.log"
        start = time.time()

        docker_bin = shutil.which("docker") or "docker"
        # Docker tags must be lowercase and avoid slashes.
        image_tag = (
            f"rapidkit-audit-{self.safe_slug}-{kit.replace('.', '-')}-{self.timestamp}".lower()
        )
        container_name = (
            f"rapidkit-audit-{self.safe_slug}-{kit.replace('.', '-')}-{self.timestamp}".lower()
        )
        # Keep name reasonably short for Docker.
        container_name = re.sub(r"[^a-z0-9_.-]", "-", container_name)[:63]

        host = "127.0.0.1"
        host_port = self._reserve_port()
        logs: list[str] = []

        build_cmd = [docker_bin, "build", "-t", image_tag, "."]
        build_proc = subprocess.run(
            build_cmd,
            check=False,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        logs.append("$ " + " ".join(build_cmd))
        logs.append(build_proc.stdout or "")
        logs.append(build_proc.stderr or "")
        if build_proc.returncode != 0:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            duration = time.time() - start
            return StepResult(
                name="docker smoke",
                command=build_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"docker build failed (exit {build_proc.returncode})",
            )

        trivy_bin = shutil.which("trivy") or "trivy"
        trivy_report = project_dir / "trivy-image.json"
        trivy_cmd = [
            trivy_bin,
            "image",
            "--no-progress",
            "--scanners",
            "vuln",
            "--pkg-types",
            "os",
            "--format",
            "json",
            "--output",
            str(trivy_report),
            "--severity",
            "HIGH,CRITICAL",
            "--exit-code",
            "0",
            "--db-repository",
            PRO_TRIVY_DB_REPOSITORY,
            image_tag,
        ]
        trivy_proc = subprocess.run(
            trivy_cmd,
            check=False,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        logs.append("$ " + " ".join(trivy_cmd))
        logs.append(trivy_proc.stdout or "")
        logs.append(trivy_proc.stderr or "")

        trivy_json_raw: str = ""
        try:
            trivy_json_raw = trivy_report.read_text(encoding="utf-8")
        except OSError:
            trivy_json_raw = ""

        trivy_json: Optional[object]
        if trivy_json_raw.strip():
            try:
                trivy_json = json.loads(trivy_json_raw)
            except Exception:
                trivy_json = None
        else:
            trivy_json = None

        if trivy_proc.returncode != 0 and trivy_json is None:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            duration = time.time() - start
            return StepResult(
                name="docker smoke",
                command=build_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"trivy scan error (exit {trivy_proc.returncode})",
            )
        if trivy_json is None:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            duration = time.time() - start
            details = self._summarize((trivy_proc.stderr or trivy_proc.stdout or "").strip())
            return StepResult(
                name="docker smoke",
                command=build_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"trivy scan failed (no JSON report). details={details}",
            )

        allowlisted = set(self.trivy_allowlist_ids)
        remaining_ids: set[str] = set()
        allowlisted_hits: set[str] = set()
        remaining_count = 0
        allowlisted_count = 0
        try:
            results = trivy_json.get("Results") if isinstance(trivy_json, dict) else None
            if isinstance(results, list):
                for entry in results:
                    if not isinstance(entry, dict):
                        continue
                    vulns = entry.get("Vulnerabilities") or []
                    if not isinstance(vulns, list):
                        continue
                    for vuln in vulns:
                        if not isinstance(vuln, dict):
                            continue
                        vuln_id = (vuln.get("VulnerabilityID") or "").strip()
                        if not vuln_id:
                            continue
                        if vuln_id in allowlisted:
                            allowlisted_hits.add(vuln_id)
                            allowlisted_count += 1
                        else:
                            remaining_ids.add(vuln_id)
                            remaining_count += 1
        except Exception:
            remaining_count = 1
            remaining_ids = {"<unparsed>"}

        if remaining_count > 0:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            duration = time.time() - start
            sample = ",".join(sorted(remaining_ids)[:6])
            return StepResult(
                name="docker smoke",
                command=build_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=(
                    f"trivy found HIGH/CRITICAL vulnerabilities: {remaining_count} "
                    f"(allowlisted {allowlisted_count}). ids={sample}"
                ),
                metadata={
                    "trivy": {
                        "report": self._rel_path(trivy_report),
                        "db_repository": PRO_TRIVY_DB_REPOSITORY,
                        "allowlist_path": (
                            self._rel_path(self.trivy_allowlist_path)
                            if self.trivy_allowlist_path
                            else ""
                        ),
                        "allowlisted_ids": sorted(allowlisted_hits),
                        "remaining_ids": sorted(remaining_ids),
                    }
                },
            )

        run_cmd = [
            docker_bin,
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{host}:{host_port}:8000",
            image_tag,
        ]
        run_proc = subprocess.run(
            run_cmd,
            check=False,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
        )
        container_id = (run_proc.stdout or "").strip()
        logs.append("$ " + " ".join(run_cmd))
        logs.append(run_proc.stdout or "")
        logs.append(run_proc.stderr or "")
        if run_proc.returncode != 0 or not container_id:
            log_path.write_text("\n".join(logs), encoding="utf-8")
            duration = time.time() - start
            return StepResult(
                name="docker smoke",
                command=run_cmd,
                status="fail",
                duration_s=duration,
                log_path=self._rel_path(log_path),
                summary=f"docker run failed (exit {run_proc.returncode})",
            )

        status = "fail"
        summary = ""
        metadata: dict[str, Any] | None = None
        try:
            logs.append(
                f"[health] Waiting for TCP port {host}:{host_port} (timeout {PRO_DOCKER_HEALTH_TIMEOUT_S:.0f}s)"
            )
            self._wait_for_port(host, host_port, timeout=PRO_DOCKER_HEALTH_TIMEOUT_S)

            candidates = self._health_url_candidates(host, host_port)
            logs.append(f"[health] URL candidates ({len(candidates)}): {', '.join(candidates)}")

            url = ""
            status_code = 0
            body = ""
            last_error: Optional[Exception] = None
            deadline = time.time() + PRO_DOCKER_HEALTH_TIMEOUT_S
            while True:
                try:
                    t0 = time.perf_counter()
                    url, status_code, body = self._probe_health_urls(candidates)
                    break
                except Exception as exc:
                    last_error = exc
                    if time.time() >= deadline:
                        raise
                    time.sleep(0.5)

            if last_error is not None:
                logs.append(f"[health] First probe error (recovered): {last_error}")
            latency_ms = (time.perf_counter() - t0) * 1000.0
            snippet = body.strip().splitlines()
            preview = snippet[0][:200] if snippet else ""
            analyzed, missing = self._analyze_health_payload(body)
            if self.strict_health and missing:
                raise ValueError("; ".join(missing))
            if latency_ms > PRO_MAX_HEALTH_LATENCY_MS:
                raise ValueError(
                    f"health latency {latency_ms:.0f}ms exceeded {PRO_MAX_HEALTH_LATENCY_MS:.0f}ms"
                )
            status = "pass"
            summary = f"{status_code} {url} {preview}".strip()
            metadata = {
                "docker": {
                    "image": image_tag,
                    "container": container_id,
                    "host_port": host_port,
                    "trivy_report": self._rel_path(trivy_report),
                },
                "health": {
                    "url": url,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    **analyzed,
                },
            }
        except Exception as exc:
            logs.append(f"[health] Probe failed: {exc}")
            summary = f"docker smoke failed: {exc}"
            status = "fail"
        finally:
            inspect_cmd = [docker_bin, "inspect", container_name, "--format", "{{json .State}}"]
            inspect_proc = subprocess.run(
                inspect_cmd,
                check=False,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
            )
            logs.append("$ " + " ".join(inspect_cmd))
            logs.append(inspect_proc.stdout or "")
            logs.append(inspect_proc.stderr or "")

            logs_cmd = [docker_bin, "logs", container_name]
            logs_proc = subprocess.run(
                logs_cmd,
                check=False,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
            )
            logs.append("$ " + " ".join(logs_cmd))
            logs.append(logs_proc.stdout or "")
            logs.append(logs_proc.stderr or "")

            rm_cmd = [docker_bin, "rm", "-f", container_name]
            rm_proc = subprocess.run(
                rm_cmd,
                check=False,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
            )
            logs.append("$ " + " ".join(rm_cmd))
            logs.append(rm_proc.stdout or "")
            logs.append(rm_proc.stderr or "")
            log_path.write_text("\n".join(logs), encoding="utf-8")

        duration = time.time() - start
        return StepResult(
            name="docker smoke",
            command=build_cmd,
            status=status,
            duration_s=duration,
            log_path=self._rel_path(log_path),
            summary=summary,
            metadata=metadata if status == "pass" else None,
        )

    def _analyze_health_payload(self, body: str) -> Tuple[dict[str, Any], List[str]]:
        missing: List[str] = []
        metadata: dict[str, Any] = {}
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return {"parsed": False, "raw_preview": body.strip()[:200]}, ["non-json response"]

        for key in (
            "version",
            "uptime",
            "module",
            "status",
            "service",
            "name",
            "checked_at",
            "checkedAt",
        ):
            if key in payload:
                metadata[key] = payload.get(key)

        if not any(key in payload for key in ("module", "service", "name")):
            missing.append("module/service/name")
        if "status" not in payload:
            missing.append("status")

        return metadata, missing

    def _enforce_engine_policy(self, step: StepResult) -> StepResult:
        if not self.fail_on_ebadengine:
            return step
        if step.status != "pass":
            return step
        output = step.raw_output or ""
        if not re.search(r"\bEBADENGINE\b|unsupported engine", output, flags=re.IGNORECASE):
            return step
        step.status = "fail"
        suffix = "EBADENGINE detected (unsupported engine)"
        step.summary = f"{step.summary} ({suffix})" if step.summary else suffix
        return step

    def _prune_audit_history(self) -> None:
        if self.keep_last <= 0:
            return
        module_history = AUDIT_HISTORY_ROOT / self.safe_slug
        if not module_history.exists():
            return
        candidates: list[Path] = []
        now = time.time()
        for path in module_history.iterdir():
            if not path.is_dir():
                continue
            marker = path / IN_PROGRESS_MARKER
            if marker.exists():
                try:
                    age_s = now - marker.stat().st_mtime
                except OSError:
                    age_s = 0.0
                if age_s < IN_PROGRESS_STALE_S:
                    continue
            candidates.append(path)
        if len(candidates) <= self.keep_last:
            return
        candidates.sort(key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
        to_remove = candidates[self.keep_last :]
        for path in to_remove:
            shutil.rmtree(path, ignore_errors=True)
        if to_remove:
            self._log(
                f"Pruned {len(to_remove)} old audit runs under {self._rel_path(module_history)} (keep_last={self.keep_last})"
            )

    def _write_summary(self, parity_payload: object | None, product_payload: object | None) -> Path:
        summary = {
            "module": self.module_slug,
            "timestamp": self.timestamp,
            "artifact_dir": self._rel_path(self.audit_dir),
            "status": self._overall_status(),
            "steps": [record.as_dict() for record in self.records],
            "kit_runs": [run.as_dict() for run in self.kit_runs],
            "parity": parity_payload,
            "product_score": product_payload,
        }
        if self.stabilization_fingerprint:
            summary["stabilization_cache"] = {
                "schema_version": 1,
                "status": self._overall_status(),
                "fingerprint": self.stabilization_fingerprint,
                "fingerprint_payload": self.stabilization_fingerprint_payload,
            }
        shipped_tests = self._aggregate_all_shipped_tests()
        if shipped_tests:
            summary["shipped_tests"] = shipped_tests
        summary_path = self.audit_dir / "stabilization-run.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary_path

    def _overall_status(self) -> str:
        record_pass = all(rec.status == "pass" for rec in self.records if rec.status != "skipped")
        kit_pass = all(run.status == "pass" for run in self.kit_runs) if self.kit_runs else True
        return "pass" if record_pass and kit_pass else "fail"

    def _summarize(self, output: str, max_lines: int = 20) -> str:
        lines = [line for line in output.splitlines() if line.strip()]
        if len(lines) > max_lines:
            head = lines[: max_lines // 2]
            tail = lines[-max_lines // 2 :]
            lines = head + ["..."] + tail
        return "\n".join(lines)

    def _extract_json(self, raw: str) -> object | None:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _load_json_file(self, path: Path | None) -> object | None:
        if path is None:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _rel_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(REPO_ROOT))
        except ValueError:
            return str(path)

    def _log(self, message: str) -> None:
        colors = _colors_enabled()
        prefix = _paint("[stabilization-runner]", code="90", enabled=colors)

        kit_match = re.match(r"^\[kit:(?P<kit>[^\]]+)\]\s*(?P<body>.*)$", message)
        if kit_match:
            kit = kit_match.group("kit")
            body = kit_match.group("body")
            kit_label = _paint(f"[kit:{kit}]", code=_kit_color_code(kit), enabled=colors)
            rendered = f"{prefix} {kit_label} {body}".rstrip()
        else:
            rendered_message = message
            start_match = re.match(r"^(Starting kit install:\s+)(?P<kit>.+)$", message)
            if start_match:
                kit = start_match.group("kit")
                rendered_message = f"{start_match.group(1)}{_paint(kit, code=_kit_color_code(kit), enabled=colors)}"
            finished_match = re.match(
                r"^(Kit\s+)(?P<kit>.+?)(\s+finished\s+with\s+status\s+)(?P<status>\w+)$",
                message,
            )
            if finished_match:
                kit = finished_match.group("kit")
                rendered_message = (
                    f"{finished_match.group(1)}"
                    f"{_paint(kit, code=_kit_color_code(kit), enabled=colors)}"
                    f"{finished_match.group(3)}"
                    f"{finished_match.group('status')}"
                )
            rendered = f"{prefix} {rendered_message}".rstrip()

        # Highlight status tokens for quick scanning.
        if colors:
            rendered = re.sub(r"\bPASS\b", _paint("PASS", code="32;1", enabled=True), rendered)
            rendered = re.sub(r"\bFAIL\b", _paint("FAIL", code="31;1", enabled=True), rendered)
            rendered = re.sub(r"\bpass\b", _paint("pass", code="32", enabled=True), rendered)
            rendered = re.sub(r"\bfail\b", _paint("fail", code="31", enabled=True), rendered)
            rendered = re.sub(r"\bskipped\b", _paint("skipped", code="90", enabled=True), rendered)

        print(rendered)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RapidKit module stabilization orchestrator")
    parser.add_argument("--module", required=True, help="Module slug, e.g. free/cache/redis")
    parser.add_argument(
        "--kits",
        nargs="*",
        default=DEFAULT_KITS,
        help="Kits to install (default: fastapi.standard, fastapi.ddd, nestjs.standard)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print commands instead of executing them"
    )
    parser.add_argument(
        "--keep-workdirs", action="store_true", help="Skip deleting kit workspaces before running"
    )
    parser.add_argument(
        "--use-kit-cache",
        action="store_true",
        help=(
            "Create each kit base project once and hydrate isolated per-module projects from it. "
            "This preserves module isolation while avoiding repeated kit bootstrap cost."
        ),
    )
    parser.add_argument(
        "--rebuild-kit-cache",
        action="store_true",
        help="Recreate cached kit base projects before hydrating module workspaces.",
    )
    parser.add_argument(
        "--skip-kits", action="store_true", help="Only run engine checks (no kit installs)"
    )
    parser.add_argument(
        "--no-strict-health",
        action="store_true",
        help=(
            "Treat health probes as 2xx-only (do not require JSON payload keys). "
            "Default is strict: require a JSON response containing version/uptime/module keys."
        ),
    )
    parser.add_argument(
        "--no-fail-on-ebadengine",
        action="store_true",
        help=(
            "Do not fail Node steps when npm/yarn emits EBADENGINE/Unsupported engine warnings. "
            "Default is fail-closed."
        ),
    )
    parser.add_argument(
        "--no-deterministic-deps",
        action="store_true",
        help=(
            "Allow non-deterministic dependency resolution (e.g. npm install instead of npm ci when lockfiles exist). "
            "Default is deterministic."
        ),
    )
    parser.add_argument(
        "--strict-dev-audit-high",
        action="store_true",
        help=(
            "Fail when Node dev dependency audits contain high severity issues (not only critical). "
            "Default is warn-only for high severity in dev deps."
        ),
    )
    parser.add_argument(
        "--pro-gates",
        action="store_true",
        help=(
            "Enable additional production-readiness gates (SBOM, SAST, secret scan, license, CI parity, container scan + smoke, perf budget). "
            "Requires Docker daemon + Trivy, and --user-scenarios. Default is off."
        ),
    )
    parser.add_argument(
        "--skip-snippet-verification",
        action="store_true",
        help=(
            "Skip verifying that module snippets were injected into generated kit projects. "
            "By default the runner validates snippet injection after `rapidkit add module`."
        ),
    )
    parser.add_argument(
        "--skip-module-tests",
        action="store_true",
        help=(
            "Skip running module-scoped core tests under tests/modules/<tier>/<category>/<module>. "
            "Default is to run them so stabilization catches push-time test failures earlier."
        ),
    )
    parser.add_argument(
        "--keep-last",
        type=int,
        default=0,
        help="After writing the report, keep only the N most recent audit-history folders for this module",
    )
    parser.add_argument(
        "--modules-doctor-profile",
        default="push",
        choices=["fast", "push", "ci"],
        help="Profile to pass to modules_doctor.py (default: push)",
    )
    parser.add_argument(
        "--no-sync-verify",
        action="store_true",
        help=(
            "Do not sync module.verify.json entries during modules_doctor. "
            "Useful for diagnostic/batch runs where you want reports without mutating manifests."
        ),
    )
    parser.add_argument(
        "--kit-root",
        type=Path,
        default=DEFAULT_KIT_ROOT,
        help="Where to scaffold kit projects (default: dev-engine/audit-history/_kit-runs)",
    )
    parser.add_argument(
        "--product-score-threshold",
        type=float,
        default=DEFAULT_PRODUCT_SCORE_THRESHOLD,
        help="Minimum acceptable product score (default: 70)",
    )
    parser.add_argument(
        "--static-analysis-cmd",
        help=(
            "Optional command to run for static analysis (quote the entire command). "
            "Example: --static-analysis-cmd 'poetry run ruff check src'"
        ),
    )
    parser.add_argument(
        "--user-scenarios",
        type=Path,
        help="Path to YAML file describing end-user scenarios to run inside generated kit projects",
    )
    parser.add_argument(
        "--trivy-allowlist",
        type=Path,
        help=(
            "Optional YAML allowlist for Trivy HIGH/CRITICAL vulnerability IDs. "
            "When provided (or when dev-engine/runbooks/trivy-allowlist.yml exists), "
            "only non-allowlisted findings fail the --pro-gates container scan."
        ),
    )
    parser.add_argument(
        "--stabilization-fingerprint",
        default="",
        help="Cache fingerprint supplied by stabilize_all_modules.py for summary evidence.",
    )
    parser.add_argument(
        "--stabilization-fingerprint-payload",
        type=Path,
        help="Path to the fingerprint payload JSON supplied by stabilize_all_modules.py.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    static_cmd = shlex.split(args.static_analysis_cmd) if args.static_analysis_cmd else None
    try:
        runner = StabilizationRunner(
            module_slug=args.module,
            kits=args.kits,
            dry_run=args.dry_run,
            keep_workdirs=args.keep_workdirs,
            skip_kits=args.skip_kits,
            skip_snippet_verification=args.skip_snippet_verification,
            skip_module_tests=bool(args.skip_module_tests),
            modules_doctor_profile=args.modules_doctor_profile,
            sync_verify=not args.no_sync_verify,
            kit_root=args.kit_root,
            keep_last=args.keep_last,
            product_score_threshold=args.product_score_threshold,
            strict_health=not args.no_strict_health,
            fail_on_ebadengine=not args.no_fail_on_ebadengine,
            deterministic_deps=not args.no_deterministic_deps,
            strict_dev_audit_high=bool(args.strict_dev_audit_high),
            pro_gates=bool(args.pro_gates),
            use_kit_cache=bool(args.use_kit_cache),
            rebuild_kit_cache=bool(args.rebuild_kit_cache),
            static_analysis_cmd=static_cmd,
            user_scenarios=args.user_scenarios,
            trivy_allowlist=args.trivy_allowlist,
            stabilization_fingerprint=args.stabilization_fingerprint,
            stabilization_fingerprint_payload=args.stabilization_fingerprint_payload,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    try:
        runner.run()
    except KeyboardInterrupt:
        print("Interrupted")
        return 130
    return 0 if runner.overall_status() == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
