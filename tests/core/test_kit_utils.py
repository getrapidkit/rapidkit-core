# tests/core/test_kit_utils.py
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.kit_utils import (
    _git_bin,
    _safe_branch,
    clone_or_pull_repo,
)


class TestKitUtils:
    """Test cases for the kit utilities module."""

    def test_safe_branch_valid_branches(self) -> None:
        """Test that valid branch names are accepted."""
        valid_branches = [
            "main",
            "develop",
            "feature/new-feature",
            "bugfix/issue-123",
            "release/v1.0.0",
            "hotfix/critical-bug",
            "user/john-doe/feature",
            "test_branch",
            "branch.with.dots",
            "branch-with-dashes",
        ]

        for branch in valid_branches:
            result = _safe_branch(branch)
            assert result == branch

    def test_safe_branch_invalid_branches(self) -> None:
        """Test that invalid branch names are rejected."""
        invalid_branches = [
            "",
            "branch with spaces",
            "branch;rm -rf /",
            "branch&&echo hacked",
            "branch|cat /etc/passwd",
            "branch\nnewline",
            "branch\tab",
            "branch\x00null",
            "../../../etc/passwd",
            "branch`command`",
            "branch$(command)",
            "branch${VAR}",
        ]

        for branch in invalid_branches:
            with pytest.raises(ValueError, match="Invalid branch name"):
                _safe_branch(branch)

    def test_safe_branch_edge_cases(self) -> None:
        """Test edge cases for branch name validation."""
        # Empty string
        with pytest.raises(ValueError):
            _safe_branch("")

        # Only special characters
        with pytest.raises(ValueError):
            _safe_branch("!@#$%^&*()")

        # Branch name with only dots
        with pytest.raises(ValueError):
            _safe_branch("...")

        # Branch name with only slashes
        with pytest.raises(ValueError):
            _safe_branch("///")

    @patch("shutil.which")
    def test_git_bin_found(self, mock_which: Mock) -> None:
        """Test git binary detection when git is available."""
        mock_which.return_value = "/usr/bin/git"

        result = _git_bin()
        assert result == "/usr/bin/git"
        mock_which.assert_called_once_with("git")

    @patch("shutil.which")
    def test_git_bin_not_found(self, mock_which: Mock) -> None:
        """Test git binary detection when git is not available."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError, match="git not found in PATH"):
            _git_bin()

    @patch("shutil.which")
    def test_git_bin_empty_path(self, mock_which: Mock) -> None:
        """Test git binary detection when git path is empty."""
        mock_which.return_value = ""

        with pytest.raises(RuntimeError, match="git not found in PATH"):
            _git_bin()

    @patch("core.kit_utils._git_bin")
    @patch("subprocess.run")
    def test_clone_or_pull_repo_clone_new(
        self, mock_run: Mock, mock_git_bin: Mock, tmp_path: Path
    ) -> None:
        """Test cloning a new repository."""
        mock_git_bin.return_value = "/usr/bin/git"
        dest_path = tmp_path / "repo"
        repo_url = "https://github.com/user/repo.git"
        branch = "main"

        # Mock that dest_path doesn't exist initially
        assert not dest_path.exists()

        clone_or_pull_repo(repo_url, dest_path, branch)

        # Verify git clone was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "clone" in call_args[0][0]
        assert repo_url in call_args[0][0]
        assert str(dest_path) in call_args[0][0]
        assert "-b" in call_args[0][0]
        assert branch in call_args[0][0]

    @patch("core.kit_utils._git_bin")
    @patch("subprocess.run")
    def test_clone_or_pull_repo_pull_existing(
        self, mock_run: Mock, mock_git_bin: Mock, tmp_path: Path
    ) -> None:
        """Test pulling an existing repository."""
        mock_git_bin.return_value = "/usr/bin/git"
        dest_path = tmp_path / "repo"
        dest_path.mkdir()  # Create directory to simulate existing repo
        repo_url = "https://github.com/user/repo.git"
        branch = "develop"

        clone_or_pull_repo(repo_url, dest_path, branch)

        # Should call git pull instead of git clone
        EXPECTED_CALLS = 1
        assert mock_run.call_count == EXPECTED_CALLS  # One for pull

        # Check that pull was called
        pull_call = mock_run.call_args_list[0]
        assert "pull" in pull_call[0][0]
        assert branch in pull_call[0][0]

    @patch("core.kit_utils._git_bin")
    @patch("subprocess.run")
    def test_clone_or_pull_repo_with_subprocess_error(
        self, mock_run: Mock, mock_git_bin: Mock, tmp_path: Path
    ) -> None:
        """Test handling of subprocess errors during git operations."""
        mock_git_bin.return_value = "/usr/bin/git"
        dest_path = tmp_path / "repo"
        repo_url = "https://github.com/user/repo.git"
        branch = "main"

        # Mock subprocess.run to raise an exception
        mock_run.side_effect = Exception("Git command failed")

        with pytest.raises(Exception, match="Git command failed"):
            clone_or_pull_repo(repo_url, dest_path, branch)

    @patch("core.kit_utils._git_bin")
    @patch("subprocess.run")
    def test_clone_or_pull_repo_branch_checkout(
        self, mock_run: Mock, mock_git_bin: Mock, tmp_path: Path
    ) -> None:
        """Test that branch checkout is performed correctly."""
        mock_git_bin.return_value = "/usr/bin/git"
        dest_path = tmp_path / "repo"
        dest_path.mkdir()  # Existing repo
        repo_url = "https://github.com/user/repo.git"
        branch = "feature/awesome-feature"

        clone_or_pull_repo(repo_url, dest_path, branch)

        # Verify pull command was called with safe branch name
        pull_calls = [call for call in mock_run.call_args_list if "pull" in call[0][0]]
        assert len(pull_calls) == 1

        pull_args = pull_calls[0][0][0]
        assert branch in pull_args
        assert str(dest_path) in pull_args

    def test_clone_or_pull_repo_invalid_branch_name(self, tmp_path: Path) -> None:
        """Test that invalid branch names are rejected."""
        dest_path = tmp_path / "repo"
        repo_url = "https://github.com/user/repo.git"
        invalid_branch = "branch;rm -rf /"

        with pytest.raises(ValueError, match="Invalid branch name"):
            clone_or_pull_repo(repo_url, dest_path, invalid_branch)

    @patch("core.kit_utils._git_bin")
    @patch("subprocess.run")
    def test_clone_or_pull_repo_command_construction(
        self, mock_run: Mock, mock_git_bin: Mock, tmp_path: Path
    ) -> None:
        """Test that git commands are constructed correctly."""
        mock_git_bin.return_value = "/usr/bin/git"
        dest_path = tmp_path / "repo"
        repo_url = "https://github.com/user/repo.git"
        branch = "test-branch"

        clone_or_pull_repo(repo_url, dest_path, branch)

        # Get the actual command that was called
        call_args = mock_run.call_args
        command = call_args[0][0]

        # Verify command structure
        assert command[0] == "/usr/bin/git"
        assert "clone" in command
        assert repo_url in command
        assert str(dest_path) in command

        # Verify subprocess options
        call_kwargs = call_args[1]
        assert call_kwargs.get("check") is True
