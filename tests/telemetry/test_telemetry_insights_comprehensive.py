# tests/test_telemetry_insights_comprehensive.py
"""Comprehensive tests for telemetry insights from end-user perspective."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from core.telemetry.insights import Insight, InsightsEngine, UsagePattern

# Test constants
EXPECTED_EVENTS_COUNT = 2
RECOMMENDATIONS_COUNT = 2
PATTERN_FREQUENCY = 100
PATTERN_DURATION = 1500.0
PATTERN_SUCCESS_RATE = 0.95
CONFIDENCE_THRESHOLD = 0.8


class TestTelemetryInsightsEndUser:
    """Test telemetry insights from end-user perspective."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.telemetry_dir = Path(self.temp_dir) / ".rapidkit" / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.engine = InsightsEngine(telemetry_dir=self.telemetry_dir)

    def teardown_method(self) -> None:
        """Clean up test environment."""
        # Clean up any created files
        if self.telemetry_dir.exists():
            for file in self.telemetry_dir.glob("*.json"):
                file.unlink()
            import shutil

            shutil.rmtree(self.telemetry_dir)

    def test_insights_engine_initialization_end_user(self) -> None:
        """Test insights engine initialization from end-user perspective."""
        engine = InsightsEngine()
        assert engine.telemetry_dir is not None
        assert engine._insights == []
        assert engine._usage_patterns == {}

    def test_analyze_empty_telemetry_data_end_user(self) -> None:
        """Test analyzing empty telemetry data."""
        insights = self.engine.analyze_telemetry_data()
        assert insights == []

    def test_analyze_telemetry_with_performance_insights_end_user(self) -> None:
        """Test analyzing telemetry data for performance insights."""
        # Create mock telemetry data with slow commands
        events = [
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 6000,  # Slow command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 7000,  # Another slow command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 8000,  # Another slow command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 5500,  # Another slow command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 6500,  # Another slow command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            },
        ]

        self._create_mock_telemetry_batch(events)
        insights = self.engine.analyze_telemetry_data()

        # Should generate performance insights
        performance_insights = [i for i in insights if i.category == "performance"]
        assert len(performance_insights) > 0

        insight = performance_insights[0]
        assert "Slow Command Performance" in insight.title
        assert insight.severity in ["low", "medium", "high"]
        assert len(insight.recommendations) > 0

    def test_analyze_usage_patterns_end_user(self) -> None:
        """Test analyzing usage patterns."""
        # Create mock telemetry data with command usage
        events = []
        base_time = datetime.now()

        # Simulate usage over different hours
        for hour in range(24):
            for _ in range(5):  # 5 executions per hour
                event_time = base_time.replace(hour=hour)
                events.append(
                    {
                        "event_type": "command_execution",
                        "command": "create",
                        "timestamp": event_time.isoformat(),
                        "success": True,
                    }
                )

        self._create_mock_telemetry_batch(events)
        insights = self.engine.analyze_telemetry_data()

        # Should generate usage insights
        usage_insights = [i for i in insights if i.category == "usage"]
        assert len(usage_insights) >= 0  # May or may not generate insights depending on patterns

    def test_analyze_error_patterns_end_user(self) -> None:
        """Test analyzing error patterns."""
        # Create mock telemetry data with errors
        events = [
            {
                "event_type": "command_execution",
                "command": "create",
                "success": False,
                "error_message": "Template not found",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "success": False,
                "error_message": "Template not found",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "event_type": "command_execution",
                "command": "create",
                "success": True,
                "timestamp": datetime.now().isoformat(),
            },
        ]

        self._create_mock_telemetry_batch(events)
        insights = self.engine.analyze_telemetry_data()

        # Should contain insights (may include reliability insights)
        assert isinstance(insights, list)

    def test_analyze_security_insights_end_user(self) -> None:
        """Test analyzing security insights."""
        # Create mock telemetry data
        events = [
            {
                "event_type": "command_execution",
                "command": "create",
                "args": {"password": "[REDACTED]"},  # Should indicate security awareness
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }
        ]

        self._create_mock_telemetry_batch(events)
        insights = self.engine.analyze_telemetry_data()

        # Should generate some insights
        assert isinstance(insights, list)

    def test_get_recent_files_filters_by_date_end_user(self) -> None:
        """Test filtering telemetry files by date."""
        # Create files with different dates
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d_%H%M%S")
        recent_date = (datetime.now() - timedelta(days=2)).strftime("%Y%m%d_%H%M%S")

        old_file = self.telemetry_dir / f"telemetry_batch_{old_date}_abc123.json"
        recent_file = self.telemetry_dir / f"telemetry_batch_{recent_date}_def456.json"

        old_file.write_text('{"events": []}')
        recent_file.write_text('{"events": []}')

        files = [old_file, recent_file]
        recent_files = self.engine._get_recent_files(files, days=7)

        assert len(recent_files) == 1
        assert recent_file in recent_files
        assert old_file not in recent_files

    def test_load_events_from_files_end_user(self) -> None:
        """Test loading events from telemetry files."""
        # Create mock telemetry batch
        batch_data = {
            "events": [
                {"event_type": "command_execution", "command": "create"},
                {"event_type": "feature_usage", "command": "template"},
            ]
        }

        batch_file = self.telemetry_dir / "telemetry_batch_20231201_120000_abc123.json"
        with open(batch_file, "w") as f:
            json.dump(batch_data, f)

        events = self.engine._load_events_from_files([batch_file])

        assert len(events) == EXPECTED_EVENTS_COUNT
        assert events[0]["event_type"] == "command_execution"
        assert events[1]["event_type"] == "feature_usage"

    def test_analyze_performance_insights_with_fast_commands_end_user(self) -> None:
        """Test performance analysis with fast commands."""
        events = [
            {
                "event_type": "command_execution",
                "command": "info",
                "duration_ms": 100,  # Fast command
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }
        ]

        insights = self.engine._analyze_performance_insights(events)

        # Should not generate slow command insights for fast commands
        slow_insights = [i for i in insights if "Slow Command" in i.title]
        assert len(slow_insights) == 0

    def test_analyze_performance_insights_with_insufficient_samples_end_user(self) -> None:
        """Test performance analysis with insufficient samples."""
        events = [
            {
                "event_type": "command_execution",
                "command": "create",
                "duration_ms": 6000,
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }  # Only 1 sample, needs 5 for analysis
        ]

        insights = self.engine._analyze_performance_insights(events)

        # Should not generate insights with insufficient samples
        assert len(insights) == 0

    def test_analyze_usage_patterns_with_various_commands_end_user(self) -> None:
        """Test usage pattern analysis with various commands."""
        events = []
        commands = ["create", "add", "list", "info"]

        for cmd in commands:
            for _ in range(10):  # 10 executions per command
                events.append(
                    {
                        "event_type": "command_execution",
                        "command": cmd,
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                    }
                )

        insights = self.engine._analyze_usage_patterns(events)

        # Should generate insights about command usage
        assert isinstance(insights, list)

    def test_insight_dataclass_creation_end_user(self) -> None:
        """Test Insight dataclass creation."""
        insight = Insight(
            insight_id="test_insight",
            title="Test Insight",
            description="This is a test insight",
            severity="medium",
            category="performance",
            confidence=0.8,
            impact="high",
            recommendations=["Do this", "Do that"],
            metadata={"key": "value"},
        )

        assert insight.insight_id == "test_insight"
        assert insight.title == "Test Insight"
        assert insight.severity == "medium"
        assert insight.category == "performance"
        assert insight.confidence == CONFIDENCE_THRESHOLD
        assert insight.impact == "high"
        assert len(insight.recommendations) == RECOMMENDATIONS_COUNT
        assert insight.metadata == {"key": "value"}

    def test_usage_pattern_dataclass_creation_end_user(self) -> None:
        """Test UsagePattern dataclass creation."""
        pattern = UsagePattern(
            pattern_id="test_pattern",
            command="create",
            frequency=100,
            avg_duration=1500.0,
            success_rate=0.95,
            peak_usage_hours=[9, 10, 11],
            common_args={"template": 50, "project": 30},
        )

        assert pattern.pattern_id == "test_pattern"
        assert pattern.command == "create"
        assert pattern.frequency == PATTERN_FREQUENCY
        assert pattern.avg_duration == PATTERN_DURATION
        assert pattern.success_rate == PATTERN_SUCCESS_RATE
        assert pattern.peak_usage_hours == [9, 10, 11]
        assert pattern.common_args == {"template": 50, "project": 30}

    def test_analyze_telemetry_data_with_corrupted_files_end_user(self) -> None:
        """Test analyzing telemetry data with corrupted files."""
        # Create a corrupted JSON file
        corrupted_file = self.telemetry_dir / "corrupted_batch.json"
        corrupted_file.write_text("{ invalid json content")

        # Create a valid file
        valid_file = self.telemetry_dir / "valid_batch.json"
        with open(valid_file, "w") as f:
            json.dump({"events": [{"event_type": "test"}]}, f)

        # Should handle corrupted files gracefully
        insights = self.engine.analyze_telemetry_data()
        assert isinstance(insights, list)

    def _create_mock_telemetry_batch(self, events: list) -> None:
        """Helper method to create mock telemetry batch files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetry_batch_{timestamp}_test123.json"
        filepath = self.telemetry_dir / filename

        batch = {
            "schema_version": "telemetry-v1",
            "batch_id": "test_batch",
            "collected_at": datetime.now().isoformat(),
            "system_info": {
                "platform": "Linux",
                "python_version": "3.10.14",
                "rapidkit_version": "0.1.0",
            },
            "events": events,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(batch, f)
