# src/core/telemetry/metrics.py
"""Enterprise metrics tracker for performance monitoring and analytics."""

import importlib
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Optional

# Optional runtime import for psutil
psutil_runtime: Optional[Any] = None
try:
    _psutil_module = importlib.import_module("psutil")
except ImportError:  # pragma: no cover - optional dependency
    psutil_runtime = None
    HAS_PSUTIL = False
else:
    psutil_runtime = _psutil_module
    HAS_PSUTIL = True


@dataclass
class MetricData:
    """Represents a single metric measurement."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric statistics."""

    name: str
    count: int = 0
    sum: float = 0.0
    min: float = float("inf")
    max: float = float("-inf")
    avg: float = 0.0
    median: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    values: deque[float] = field(default_factory=lambda: deque(maxlen=1000))


class MetricsTracker:
    """Enterprise-grade metrics tracker for performance monitoring."""

    def __init__(self, max_history: int = 1000):
        self._metrics: Dict[str, AggregatedMetric] = {}
        self._max_history = max_history
        self._lock = threading.Lock()
        self._system_metrics_enabled = self._check_system_metrics_available()

    def _check_system_metrics_available(self) -> bool:
        """Check if system metrics collection is available."""
        if not HAS_PSUTIL:
            return False
        try:  # light probe
            if psutil_runtime is not None:
                psutil_runtime.cpu_percent(interval=0.0)
            return True
        except (RuntimeError, OSError, AttributeError):  # pragma: no cover - defensive
            return False

    def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a metric measurement."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = AggregatedMetric(name=name)
                # Set the maxlen of the deque to match the tracker's max_history
                self._metrics[name].values = deque(
                    self._metrics[name].values, maxlen=self._max_history
                )

            metric = self._metrics[name]
            metric.count += 1
            metric.sum += value
            metric.min = min(metric.min, value)
            metric.max = max(metric.max, value)
            metric.values.append(value)

            # Update statistics
            if metric.values:
                sorted_values = sorted(metric.values)
                metric.avg = mean(metric.values)
                metric.median = median(sorted_values)

                # Calculate percentiles
                n = len(sorted_values)
                if n > 0:
                    p95_idx = int(0.95 * (n - 1))
                    p99_idx = int(0.99 * (n - 1))
                    metric.p95 = sorted_values[min(p95_idx, n - 1)]
                    metric.p99 = sorted_values[min(p99_idx, n - 1)]

    def get_metric(self, name: str) -> Optional[AggregatedMetric]:
        """Get aggregated metric data."""
        with self._lock:
            return self._metrics.get(name)

    def get_all_metrics(self) -> Dict[str, AggregatedMetric]:
        """Get all metrics."""
        with self._lock:
            return self._metrics.copy()

    def record_timing(
        self, name: str, start_time: float, tags: Optional[Dict[str, str]] = None
    ) -> float:
        """Record timing metric."""
        duration = time.time() - start_time
        self.record_metric(f"{name}_duration", duration * 1000, tags, {"unit": "ms"})
        return duration

    def record_counter(
        self, name: str, increment: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record counter metric."""
        self.record_metric(f"{name}_count", increment, tags)

    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        self.record_metric(f"{name}_gauge", value, tags)

    def collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        if not self._system_metrics_enabled:
            return

        if not HAS_PSUTIL or psutil_runtime is None:  # runtime guard
            return
        try:
            cpu_percent = psutil_runtime.cpu_percent(interval=0.1)
            self.record_gauge("system.cpu_percent", cpu_percent)
        except (RuntimeError, OSError, AttributeError):
            return
        try:
            memory = psutil_runtime.virtual_memory()
            self.record_gauge("system.memory_percent", memory.percent)
            self.record_gauge("system.memory_used_mb", memory.used / 1024 / 1024)
        except (RuntimeError, OSError, AttributeError):
            return
        try:
            disk = psutil_runtime.disk_usage("/")
            self.record_gauge("system.disk_percent", disk.percent)
        except (RuntimeError, OSError, AttributeError):
            return
        try:
            net = psutil_runtime.net_io_counters()
            if net:
                self.record_counter("system.net_bytes_sent", net.bytes_sent)
                self.record_counter("system.net_bytes_recv", net.bytes_recv)
        except (RuntimeError, OSError, AttributeError):
            return

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        with self._lock:
            summary: Dict[str, Any] = {
                "total_metrics": len(self._metrics),
                "system_metrics_enabled": self._system_metrics_enabled,
                "metrics": {},
            }

            for name, metric in self._metrics.items():
                if metric.count > 0:
                    summary["metrics"][name] = {
                        "count": metric.count,
                        "avg": round(metric.avg, 2),
                        "min": round(metric.min, 2),
                        "max": round(metric.max, 2),
                        "p95": round(metric.p95, 2),
                        "p99": round(metric.p99, 2),
                    }

            return summary

    def reset_metric(self, name: str) -> bool:
        """Reset a specific metric."""
        with self._lock:
            if name in self._metrics:
                self._metrics[name] = AggregatedMetric(name=name)
                return True
            return False

    def reset_all_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()

    def export_metrics(self, filepath: Path) -> None:
        """Export metrics to JSON file."""
        summary = self.get_performance_summary()
        try:
            import json

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except (OSError, IOError) as e:
            print(f"Failed to export metrics: {e}", file=__import__("sys").stderr)
