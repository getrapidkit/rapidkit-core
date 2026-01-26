#!/usr/bin/env python3
"""
Advanced Pre-commit Hook Manager

Features:
- Parallel execution for faster runs
- Selective hook execution
- Performance monitoring
- Hook health checks
- Emergency bypass options

Usage:
    python scripts/pre_commit_manager.py --help
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class PreCommitManager:
    """Advanced pre-commit hook management."""

    def __init__(self) -> None:
        self.repo_root = Path(__file__).parent.parent
        self.hooks_config = self.repo_root / ".pre-commit-config.yaml"

    def run_hooks_parallel(self, hook_ids: Optional[List[str]] = None) -> bool:
        """Run hooks in parallel for better performance."""
        if hook_ids:
            # Run each hook individually for better control
            all_passed = True
            for hook in hook_ids:
                cmd = ["poetry", "run", "pre-commit", "run", hook, "--all-files"]
                result = subprocess.run(cmd, cwd=self.repo_root, check=False)
                if result.returncode != 0:
                    all_passed = False
            return all_passed
        else:
            cmd = ["poetry", "run", "pre-commit", "run", "--all-files", "--jobs", "4"]

        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.repo_root, check=False)

        elapsed = time.time() - start_time
        print(f"⚡ Completed in {elapsed:.2f}s")
        return result.returncode == 0

    def run_quick_check(self) -> bool:
        """Run only the fastest, most critical hooks."""
        critical_hooks = ["black", "ruff", "trailing-whitespace", "end-of-file-fixer"]

        print("🚀 Running quick quality check...")
        return self.run_hooks_parallel(critical_hooks)

    def run_full_audit(self) -> bool:
        """Run all hooks including security and performance checks."""
        print("🔍 Running full security and quality audit...")
        return self.run_hooks_parallel()

    def check_hook_health(self) -> None:
        """Check the health and performance of all hooks."""
        print("🏥 Checking hook health...")

        # Test each hook individually
        hooks_to_test = [
            ("black", "pre-commit"),
            ("ruff", "pre-commit"),
            ("mypy", "pre-commit"),
            ("pytest-with-coverage", "pre-commit"),
            ("bandit", "pre-commit"),
            ("trailing-whitespace", "pre-commit"),
            ("end-of-file-fixer", "pre-commit"),
            ("check-yaml", "pre-commit"),
            ("check-json", "pre-commit"),
            ("mdformat", "pre-commit"),
            ("hadolint-docker", "pre-commit"),
            ("shellcheck", "pre-commit"),
        ]

        for hook_name, stage in hooks_to_test:
            start_time = time.time()
            if stage == "commit-msg":
                # For commit-msg hooks, we need a temporary commit message file
                import tempfile

                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write("test: health check commit")
                    temp_file = f.name

                result = subprocess.run(
                    [
                        "poetry",
                        "run",
                        "pre-commit",
                        "run",
                        hook_name,
                        "--commit-msg-filename",
                        temp_file,
                    ],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=False,
                )
                os.unlink(temp_file)
            else:
                result = subprocess.run(
                    ["poetry", "run", "pre-commit", "run", hook_name, "--all-files"],
                    cwd=self.repo_root,
                    capture_output=True,
                    check=False,
                )
            elapsed = time.time() - start_time

            status = "✅" if result.returncode == 0 else "❌"
            print(f"{status} {hook_name}: {elapsed:.2f}s")

    def emergency_bypass(self, reason: str) -> None:
        """Emergency bypass for critical situations."""
        print(f"🚨 EMERGENCY BYPASS: {reason}")
        print("⚠️  This should only be used in critical situations!")

        # Create emergency commit
        subprocess.run(
            [
                "git",
                "commit",
                "--no-verify",  # Skip all hooks
                "-m",
                f"EMERGENCY: {reason}",
            ],
            cwd=self.repo_root,
            check=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Pre-commit Manager")
    parser.add_argument(
        "action",
        choices=["quick", "full", "health", "parallel", "emergency"],
        help="Action to perform",
    )
    parser.add_argument("--hooks", nargs="*", help="Specific hooks to run (for parallel mode)")
    parser.add_argument("--reason", help="Reason for emergency bypass")

    args = parser.parse_args()
    manager = PreCommitManager()

    success = False  # Initialize success variable

    if args.action == "quick":
        success = manager.run_quick_check()
    elif args.action == "full":
        success = manager.run_full_audit()
    elif args.action == "parallel":
        success = manager.run_hooks_parallel(args.hooks)
    elif args.action == "health":
        manager.check_hook_health()
        return
    elif args.action == "emergency":
        if not args.reason:
            print("❌ Emergency bypass requires --reason")
            sys.exit(1)
        manager.emergency_bypass(args.reason)
        return

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
