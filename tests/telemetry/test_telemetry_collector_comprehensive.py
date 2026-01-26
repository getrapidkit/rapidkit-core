# tests/test_telemetry_collector_comprehensive.py
"""Comprehensive tests for telemetry collector from end-user perspective."""

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from core.telemetry.collector import SystemInfo, TelemetryCollector, TelemetryEvent

# Test constants
EXPECTED_EVENTS_COUNT = 2
COMMAND_EXECUTION_COUNT = 5


class TestTelemetryCollectorEndUser:
    """Test telemetry collector from end-user perspective."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.telemetry_dir = Path(self.temp_dir) / ".rapidkit" / "telemetry"
        config = MagicMock()
        config.telemetry_dir = self.telemetry_dir
        self.collector = TelemetryCollector(config=config)
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        # Clean up any created files
        if self.telemetry_dir.exists():
            for file in self.telemetry_dir.glob("*.json"):
                file.unlink()
            # Remove directory structure
            import shutil

            shutil.rmtree(self.temp_dir)

    def test_telemetry_collector_initialization_end_user(self) -> None:
        """Test collector initialization from end-user perspective."""
        # Test default initialization
        collector = TelemetryCollector()
        assert collector._is_enabled is True  # Should be enabled by default
        assert collector._session_id is not None
        assert collector._telemetry_dir.exists()

    def test_telemetry_disabled_via_environment_end_user(self) -> None:
        """Test disabling telemetry via environment variable."""
        with patch.dict(os.environ, {"RAPIDKIT_TELEMETRY": "false"}):
            collector = TelemetryCollector()
            assert collector._is_enabled is False

    def test_telemetry_enabled_via_environment_end_user(self) -> None:
        """Test enabling telemetry via environment variable."""
        with patch.dict(os.environ, {"RAPIDKIT_TELEMETRY": "true"}):
            collector = TelemetryCollector()
            assert collector._is_enabled is True

    def test_telemetry_disabled_via_config_end_user(self) -> None:
        """Test disabling telemetry via configuration."""
        config = MagicMock()
        config.telemetry_enabled = False
        collector = TelemetryCollector(config=config)
        assert collector._is_enabled is False

    def test_track_command_execution_success_end_user(self) -> None:
        """Test tracking successful command execution."""
        start_time = time.time()
        time.sleep(0.01)  # Small delay to ensure duration > 0

        self.collector.track_command(
            command="create",
            args={"project": "myapp", "template": "fastapi"},
            start_time=start_time,
            success=True,
            metadata={"user_id": "test_user"},
        )

        # Check that event was queued
        assert self.collector._event_queue.qsize() == 1

    def test_track_command_execution_failure_end_user(self) -> None:
        """Test tracking failed command execution."""
        start_time = time.time()
        time.sleep(0.01)

        self.collector.track_command(
            command="create",
            args={"project": "myapp"},
            start_time=start_time,
            success=False,
            error_message="Template not found",
            metadata={"error_code": "TEMPLATE_NOT_FOUND"},
        )

        assert self.collector._event_queue.qsize() == 1

    def test_track_feature_usage_end_user(self) -> None:
        """Test tracking feature usage."""
        self.collector.track_feature_usage(
            feature="enterprise_template",
            metadata={"template_type": "fastapi_enterprise"},
        )

        assert self.collector._event_queue.qsize() == 1

    def test_track_performance_metric_end_user(self) -> None:
        """Test tracking performance metrics."""
        self.collector.track_performance_metric(
            metric_name="command_duration",
            value=1500.5,
            metadata={"command": "create", "template": "fastapi"},
        )

        assert self.collector._event_queue.qsize() == 1

    def test_sanitize_args_removes_sensitive_data_end_user(self) -> None:
        """Test that sensitive arguments are sanitized."""
        args = {
            "password": "secret123",
            "token": "abc123def456",
            "normal_arg": "value",
            "api_key": "key123",
            "project_path": Path("/home/user/project"),
        }

        sanitized = self.collector._sanitize_args(args)

        # Sensitive data should be redacted
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"

        # Normal data should be preserved
        assert sanitized["normal_arg"] == "value"

        # Path should be hashed
        assert "Path(" in sanitized["project_path"]
        assert "[REDACTED]" not in sanitized["project_path"]

    def test_process_batch_creates_telemetry_file_end_user(self) -> None:
        """Test that processing batch creates telemetry files."""
        # Add some events to queue
        self.collector.track_command("create", {"project": "test"}, time.time())
        self.collector.track_feature_usage("template_used")

        # Process batch
        self.collector._process_batch()

        # Check that telemetry file was created
        telemetry_files = list(self.telemetry_dir.glob("telemetry_batch_*.json"))
        assert len(telemetry_files) == 1

        # Verify file contents
        with open(telemetry_files[0], "r") as f:
            batch = json.load(f)

        assert "schema_version" in batch
        assert "events" in batch
        assert len(batch["events"]) == EXPECTED_EVENTS_COUNT
        assert batch["events"][0]["event_type"] == "command_execution"
        assert batch["events"][1]["event_type"] == "feature_usage"

    def test_get_telemetry_status_end_user(self) -> None:
        """Test getting telemetry status information."""
        status = self.collector.get_telemetry_status()

        assert "enabled" in status
        assert "session_id" in status
        assert "queue_size" in status
        assert "telemetry_dir" in status
        assert "system_info" in status

        assert isinstance(status["enabled"], bool)
        assert isinstance(status["session_id"], str)
        assert isinstance(status["queue_size"], int)

    def test_flush_events_processes_all_pending_end_user(self) -> None:
        """Test that flush_events processes all pending events."""
        # Add multiple events
        for i in range(5):
            self.collector.track_command(f"command_{i}", {}, time.time())

        assert self.collector._event_queue.qsize() == COMMAND_EXECUTION_COUNT

        # Flush events
        self.collector.flush_events()

        # Check that files were created
        telemetry_files = list(self.telemetry_dir.glob("telemetry_batch_*.json"))
        assert len(telemetry_files) >= 1

    def test_telemetry_event_creation_end_user(self) -> None:
        """Test TelemetryEvent dataclass creation."""
        event = TelemetryEvent(
            event_type="test_event",
            command="test_command",
            args={"arg1": "value1"},
            success=True,
            metadata={"key": "value"},
        )

        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.event_type == "test_event"
        assert event.command == "test_command"
        assert event.args == {"arg1": "value1"}
        assert event.success is True
        assert event.metadata == {"key": "value"}

    def test_system_info_creation_end_user(self) -> None:
        """Test SystemInfo dataclass creation."""
        system_info = SystemInfo()

        assert system_info.platform is not None
        assert system_info.python_version is not None
        assert system_info.rapidkit_version == "0.1.0"

    def test_disabled_telemetry_does_not_track_end_user(self) -> None:
        """Test that disabled telemetry doesn't track events."""
        with patch.dict(os.environ, {"RAPIDKIT_TELEMETRY": "false"}):
            collector = TelemetryCollector()

            # Try to track events
            collector.track_command("test", {}, time.time())
            collector.track_feature_usage("test_feature")

            # Queue should be empty
            assert collector._event_queue.qsize() == 0

    def test_event_to_dict_conversion_end_user(self) -> None:
        """Test converting TelemetryEvent to dictionary."""
        event = TelemetryEvent(
            event_type="test",
            command="cmd",
            args={"a": "1"},
            success=False,
            error_message="error",
            metadata={"m": "1"},
        )

        event_dict = self.collector._event_to_dict(event)

        assert event_dict["event_type"] == "test"
        assert event_dict["command"] == "cmd"
        assert event_dict["args"] == {"a": "1"}
        assert event_dict["success"] is False
        assert event_dict["error_message"] == "error"
        assert event_dict["metadata"] == {"m": "1"}

    def test_persist_batch_handles_errors_gracefully_end_user(self) -> None:
        """Test that batch persistence handles errors gracefully."""
        batch = {"test": "data"}

        # Mock file operations to raise error
        with patch("builtins.open", side_effect=OSError("Disk full")):
            # Should not raise exception
            self.collector._persist_batch(batch)

    def test_background_worker_handles_errors_end_user(self) -> None:
        """Test that background worker handles errors gracefully."""
        # This is harder to test directly, but we can verify the worker setup
        # Use the existing collector from setup_method instead of creating a new one
        if self.collector._is_enabled:
            # Worker thread should exist
            worker_threads = [t for t in threading.enumerate() if t.name == "TelemetryWorker"]
            # There should be at least one worker thread
            assert len(worker_threads) >= 1
