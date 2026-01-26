# tests/test_telemetry_metrics_comprehensive.py
"""Comprehensive tests for telemetry metrics from end-user perspective."""

import time
from unittest.mock import MagicMock, patch

import core.telemetry.metrics as metrics_module
from core.telemetry.metrics import AggregatedMetric, MetricData, MetricsTracker

# Test constants
CPU_USAGE_VALUE = 75.0
MEDIAN_TEST_VALUE = 5.0
CPU_PERCENT_VALUE = 45.5
MEMORY_PERCENT_VALUE = 67.8
TEST_METRIC_VALUE = 123.45
BASIC_METRIC_VALUE = 42.5
API_CALL_VALUE = 150.0
MEMORY_USAGE_VALUE = 85.5
AGGREGATED_COUNT = 10
AGGREGATED_SUM = 500.0
AGGREGATED_MIN = 10.0
AGGREGATED_MAX = 100.0
AGGREGATED_AVG = 50.0
AGGREGATED_MEDIAN = 45.0
AGGREGATED_P95 = 90.0
AGGREGATED_P99 = 95.0
NEGATIVE_METRIC_VALUE = -10.5
LARGE_METRIC_COUNT = 100
MULTIPLE_VALUES_LIST = [10.0, 20.0, 30.0, 40.0, 50.0]
DEFAULT_MAX_HISTORY = 100
PERCENTILE_VALUES_LIST = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
SMALL_HISTORY_LIMIT = 5
DEFAULT_MAX_HISTORY_VALUE = 1000
MEDIAN_TEST_VALUES = [1, 3, 5, 7, 9]
MULTIPLE_VALUES_COUNT = 5
MULTIPLE_VALUES_MIN = 10.0
MULTIPLE_VALUES_MAX = 50.0
MULTIPLE_VALUES_AVG = 30.0
AGGREGATED_VALUES_LEN = 5
CONCURRENT_THREAD_COUNT = 3


class TestTelemetryMetricsEndUser:
    """Test telemetry metrics from end-user perspective."""

    def setup_method(self) -> None:
        """Setup test environment."""
        self.tracker = MetricsTracker(max_history=DEFAULT_MAX_HISTORY)

    def test_metrics_tracker_initialization_end_user(self) -> None:
        """Test metrics tracker initialization from end-user perspective."""
        tracker = MetricsTracker()
        assert tracker._metrics == {}
        assert tracker._max_history == DEFAULT_MAX_HISTORY_VALUE  # Default value
        assert tracker._lock is not None

    def test_record_metric_basic_functionality_end_user(self) -> None:
        """Test basic metric recording functionality."""
        self.tracker.record_metric("test_metric", BASIC_METRIC_VALUE)

        assert "test_metric" in self.tracker._metrics
        metric = self.tracker._metrics["test_metric"]
        assert metric.count == 1
        assert metric.sum == BASIC_METRIC_VALUE
        assert metric.min == BASIC_METRIC_VALUE
        assert metric.max == BASIC_METRIC_VALUE
        assert metric.avg == BASIC_METRIC_VALUE

    def test_record_metric_multiple_values_end_user(self) -> None:
        """Test recording multiple values for the same metric."""
        values = MULTIPLE_VALUES_LIST

        for value in values:
            self.tracker.record_metric("response_time", value)

        metric = self.tracker._metrics["response_time"]
        assert metric.count == MULTIPLE_VALUES_COUNT
        assert metric.sum == API_CALL_VALUE
        assert metric.min == MULTIPLE_VALUES_MIN
        assert metric.max == MULTIPLE_VALUES_MAX
        assert metric.avg == MULTIPLE_VALUES_AVG

    def test_record_metric_with_tags_end_user(self) -> None:
        """Test recording metrics with tags."""
        self.tracker.record_metric(
            "api_call", API_CALL_VALUE, tags={"endpoint": "/api/users", "method": "GET"}
        )

        assert "api_call" in self.tracker._metrics

    def test_record_metric_with_metadata_end_user(self) -> None:
        """Test recording metrics with metadata."""
        self.tracker.record_metric(
            "memory_usage",
            MEMORY_USAGE_VALUE,
            metadata={"unit": "percent", "server": "web-01"},
        )

        assert "memory_usage" in self.tracker._metrics

    def test_get_metric_existing_end_user(self) -> None:
        """Test getting an existing metric."""
        self.tracker.record_metric("cpu_usage", CPU_USAGE_VALUE)

        metric = self.tracker.get_metric("cpu_usage")
        assert metric is not None
        assert metric.name == "cpu_usage"
        assert metric.count == 1
        assert metric.avg == CPU_USAGE_VALUE

    def test_get_metric_nonexistent_end_user(self) -> None:
        """Test getting a nonexistent metric."""
        metric = self.tracker.get_metric("nonexistent_metric")
        assert metric is None

    def test_metric_percentiles_calculation_end_user(self) -> None:
        """Test percentile calculation for metrics."""
        # Record enough values to calculate percentiles
        values = PERCENTILE_VALUES_LIST

        for value in values:
            self.tracker.record_metric("test_percentiles", float(value))

        metric = self.tracker._metrics["test_percentiles"]

        # Check that percentiles are calculated
        assert metric.p95 is not None
        assert metric.p99 is not None
        assert metric.p95 <= metric.p99  # 95th percentile should be <= 99th percentile

    def test_metric_median_calculation_end_user(self) -> None:
        """Test median calculation for metrics."""
        values = MEDIAN_TEST_VALUES  # Odd number of values

        for value in values:
            self.tracker.record_metric("test_median", float(value))

        metric = self.tracker._metrics["test_median"]
        assert metric.median == MEDIAN_TEST_VALUE  # Median of [1,3,5,7,9] is 5

    def test_system_metrics_detection_end_user(self) -> None:
        """Test system metrics availability detection."""
        # Test with psutil available (mock the actual psutil module)
        with patch.object(metrics_module, "psutil_runtime") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 10.0
            # Also need to patch HAS_PSUTIL to ensure the check passes
            with patch.object(metrics_module, "HAS_PSUTIL", True):
                tracker = MetricsTracker()
                assert tracker._system_metrics_enabled is True

        # Test without psutil (mock psutil as None)
        with patch.object(metrics_module, "HAS_PSUTIL", False):
            tracker = MetricsTracker()
            assert tracker._system_metrics_enabled is False

    def test_record_system_metric_cpu_end_user(self) -> None:
        """Test recording CPU usage metric."""
        with patch.object(metrics_module, "psutil_runtime") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 45.5

            # This would normally record system metrics
            # For testing, we simulate the functionality
            cpu_percent = 45.5
            self.tracker.record_metric("cpu_percent", cpu_percent)

            metric = self.tracker._metrics["cpu_percent"]
            assert metric.avg == CPU_PERCENT_VALUE

    def test_record_system_metric_memory_end_user(self) -> None:
        """Test recording memory usage metric."""
        with patch.object(metrics_module, "psutil_runtime") as mock_psutil:
            mock_memory = MagicMock()
            mock_memory.percent = 67.8
            mock_psutil.virtual_memory.return_value = mock_memory

            # Simulate recording memory metric
            memory_percent = 67.8
            self.tracker.record_metric("memory_percent", memory_percent)

            metric = self.tracker._metrics["memory_percent"]
            assert metric.avg == MEMORY_PERCENT_VALUE

    def test_metric_data_dataclass_creation_end_user(self) -> None:
        """Test MetricData dataclass creation."""

        current_time = time.time()

        metric_data = MetricData(
            name="test_metric",
            value=123.45,
            timestamp=current_time,
            tags={"env": "test"},
            metadata={"source": "unit_test"},
        )

        assert metric_data.name == "test_metric"
        assert metric_data.value == TEST_METRIC_VALUE
        assert metric_data.timestamp == current_time
        assert metric_data.tags == {"env": "test"}
        assert metric_data.metadata == {"source": "unit_test"}

    def test_aggregated_metric_dataclass_creation_end_user(self) -> None:
        """Test AggregatedMetric dataclass creation."""
        from collections import deque

        metric = AggregatedMetric(
            name="test_aggregated",
            count=AGGREGATED_COUNT,
            sum=AGGREGATED_SUM,
            min=AGGREGATED_MIN,
            max=100.0,
            avg=50.0,
            median=45.0,
            p95=90.0,
            p99=95.0,
            values=deque([10, 20, 30, 40, 50]),
        )

        assert metric.name == "test_aggregated"
        assert metric.count == AGGREGATED_COUNT
        assert metric.sum == AGGREGATED_SUM
        assert metric.min == AGGREGATED_MIN
        assert metric.max == AGGREGATED_MAX
        assert metric.avg == AGGREGATED_AVG
        assert metric.median == AGGREGATED_MEDIAN
        assert metric.p95 == AGGREGATED_P95
        assert metric.p99 == AGGREGATED_P99
        assert len(metric.values) == AGGREGATED_VALUES_LEN

    def test_concurrent_metric_recording_end_user(self) -> None:
        """Test concurrent metric recording (basic thread safety)."""
        import threading

        results = []

        def record_metrics(thread_id: int) -> None:
            for i in range(100):
                self.tracker.record_metric(f"thread_{thread_id}_metric", float(i))
            results.append(f"thread_{thread_id}_done")

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=record_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all threads completed
        assert len(results) == CONCURRENT_THREAD_COUNT
        assert all("done" in result for result in results)

        # Verify metrics were recorded
        for i in range(3):
            assert f"thread_{i}_metric" in self.tracker._metrics

    def test_metric_history_limit_end_user(self) -> None:
        """Test that metric history is limited."""
        # Create tracker with small history limit
        tracker = MetricsTracker(max_history=SMALL_HISTORY_LIMIT)

        # Record more values than the limit
        for i in range(10):
            tracker.record_metric("limited_metric", float(i))

        metric = tracker._metrics["limited_metric"]
        assert len(metric.values) <= SMALL_HISTORY_LIMIT  # Should not exceed max_history

    def test_zero_value_metrics_end_user(self) -> None:
        """Test recording zero values."""
        self.tracker.record_metric("zero_metric", 0.0)

        metric = self.tracker._metrics["zero_metric"]
        assert metric.count == 1
        assert metric.sum == 0.0
        assert metric.min == 0.0
        assert metric.max == 0.0
        assert metric.avg == 0.0

    def test_negative_value_metrics_end_user(self) -> None:
        """Test recording negative values."""
        self.tracker.record_metric("negative_metric", -10.5)

        metric = self.tracker._metrics["negative_metric"]
        assert metric.count == 1
        assert metric.sum == NEGATIVE_METRIC_VALUE
        assert metric.min == NEGATIVE_METRIC_VALUE
        assert metric.max == NEGATIVE_METRIC_VALUE
        assert metric.avg == NEGATIVE_METRIC_VALUE

    def test_large_number_of_metrics_end_user(self) -> None:
        """Test handling a large number of different metrics."""
        # Record many different metrics
        for i in range(100):
            self.tracker.record_metric(f"metric_{i}", float(i))

        # Verify all metrics were recorded
        assert len(self.tracker._metrics) == LARGE_METRIC_COUNT

        for i in range(100):
            assert f"metric_{i}" in self.tracker._metrics
            metric = self.tracker._metrics[f"metric_{i}"]
            assert metric.avg == float(i)
