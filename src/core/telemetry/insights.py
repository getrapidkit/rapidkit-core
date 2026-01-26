# src/core/telemetry/insights.py
"""Enterprise insights engine for advanced analytics and recommendations."""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Constants for analysis thresholds
MIN_SAMPLES_FOR_PERFORMANCE = 5
SLOW_COMMAND_THRESHOLD_MS = 5000
CRITICAL_SLOW_THRESHOLD_MS = 10000
SIGNIFICANT_USAGE_THRESHOLD = 10
MIN_EXECUTIONS_FOR_ERROR_ANALYSIS = 5
HIGH_ERROR_RATE_THRESHOLD = 0.3
CRITICAL_ERROR_RATE_THRESHOLD = 0.5


@dataclass
class Insight:
    """Represents a single insight or recommendation."""

    insight_id: str
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str  # 'performance', 'usage', 'security', 'reliability'
    confidence: float  # 0.0 to 1.0
    impact: str  # 'low', 'medium', 'high'
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UsagePattern:
    """Represents a usage pattern analysis."""

    pattern_id: str
    command: str
    frequency: int
    avg_duration: float
    success_rate: float
    peak_usage_hours: List[int]
    common_args: Dict[str, int]


class InsightsEngine:
    """Enterprise-grade insights engine for telemetry analytics."""

    def __init__(self, telemetry_dir: Optional[Path] = None) -> None:
        self.telemetry_dir = telemetry_dir or Path.home() / ".rapidkit" / "telemetry"
        self._insights: List[Insight] = []
        self._usage_patterns: Dict[str, UsagePattern] = {}

    def analyze_telemetry_data(self) -> List[Insight]:
        """Analyze telemetry data and generate insights."""
        if not self.telemetry_dir.exists():
            return []

        insights: List[Insight] = []

        # Load and analyze telemetry batches
        telemetry_files = list(self.telemetry_dir.glob("telemetry_batch_*.json"))
        if not telemetry_files:
            return insights

        # Analyze recent data (last 7 days)
        recent_files = self._get_recent_files(telemetry_files, days=7)
        events = self._load_events_from_files(recent_files)

        if not events:
            return insights

        # Generate various insights
        insights.extend(self._analyze_performance_insights(events))
        insights.extend(self._analyze_usage_patterns(events))
        insights.extend(self._analyze_error_patterns(events))
        insights.extend(self._analyze_security_insights(events))

        self._insights = insights
        return insights

    def _get_recent_files(self, files: List[Path], days: int) -> List[Path]:
        """Get telemetry files from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_files = []

        for file in files:
            try:
                # Extract timestamp from filename
                match = re.search(r"telemetry_batch_(\d{8})_(\d{6})", file.name)
                if match:
                    date_str = match.group(1)
                    time_str = match.group(2)
                    file_date = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    if file_date > cutoff_date:
                        recent_files.append(file)
            except (ValueError, AttributeError):
                continue

        return recent_files

    def _load_events_from_files(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Load events from telemetry batch files."""
        events = []

        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    batch = json.load(f)
                    events.extend(batch.get("events", []))
            except (OSError, json.JSONDecodeError):
                continue

        return events

    def _analyze_performance_insights(self, events: List[Dict[str, Any]]) -> List[Insight]:
        """Analyze performance-related insights."""
        insights = []

        # Analyze command execution times
        command_times = defaultdict(list)
        for event in events:
            if event.get("event_type") == "command_execution" and event.get("duration_ms"):
                command = event.get("command", "unknown")
                command_times[command].append(event["duration_ms"])

        # Find slow commands
        for command, times in command_times.items():
            if len(times) >= MIN_SAMPLES_FOR_PERFORMANCE:
                avg_time = sum(times) / len(times)
                max_time = max(times)

                if avg_time > SLOW_COMMAND_THRESHOLD_MS:
                    insights.append(
                        Insight(
                            insight_id=f"perf_slow_command_{command}",
                            title=f"Slow Command Performance: {command}",
                            description=f"Command '{command}' has an average execution time of {avg_time:.1f}ms",
                            severity=("medium" if avg_time > CRITICAL_SLOW_THRESHOLD_MS else "low"),
                            category="performance",
                            confidence=min(0.9, len(times) / 20),
                            impact="medium",
                            recommendations=[
                                f"Consider optimizing the {command} command implementation",
                                "Review command arguments for potential inefficiencies",
                                "Monitor system resources during command execution",
                            ],
                            metadata={
                                "command": command,
                                "avg_time_ms": avg_time,
                                "max_time_ms": max_time,
                                "sample_count": len(times),
                            },
                        )
                    )

        return insights

    def _analyze_usage_patterns(self, events: List[Dict[str, Any]]) -> List[Insight]:
        """Analyze usage patterns and generate insights."""
        insights: List[Insight] = []

        # Count command usage
        command_counts: Dict[str, int] = defaultdict(int)
        hourly_usage: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

        for event in events:
            if event.get("event_type") == "command_execution":
                command = event.get("command", "unknown")
                command_counts[command] += 1

                # Parse timestamp for hourly analysis
                try:
                    timestamp = datetime.fromisoformat(
                        event.get("timestamp", "").replace("Z", "+00:00")
                    )
                    hour = timestamp.hour
                    hourly_usage[command][hour] += 1
                except (ValueError, AttributeError):
                    continue

        # Find most/least used commands
        if command_counts:
            most_used = max(command_counts.items(), key=lambda x: x[1])

            if most_used[1] > SIGNIFICANT_USAGE_THRESHOLD:
                insights.append(
                    Insight(
                        insight_id="usage_most_popular",
                        title=f"Most Popular Command: {most_used[0]}",
                        description=f"Command '{most_used[0]}' is used {most_used[1]} times",
                        severity="low",
                        category="usage",
                        confidence=0.8,
                        impact="low",
                        recommendations=[
                            f"Consider prioritizing improvements to {most_used[0]}",
                            "This command might benefit from additional features",
                        ],
                        metadata={"command": most_used[0], "usage_count": most_used[1]},
                    )
                )

        return insights

    def _analyze_error_patterns(self, events: List[Dict[str, Any]]) -> List[Insight]:
        """Analyze error patterns and generate insights."""
        insights: List[Insight] = []

        # Count errors by command
        error_counts: Dict[str, int] = defaultdict(int)
        total_executions: Dict[str, int] = defaultdict(int)

        for event in events:
            if event.get("event_type") == "command_execution":
                command = event.get("command", "unknown")
                total_executions[command] += 1

                if not event.get("success", True):
                    error_counts[command] += 1

        # Find commands with high error rates
        for command, errors in error_counts.items():
            total = total_executions.get(command, 0)
            if total >= MIN_EXECUTIONS_FOR_ERROR_ANALYSIS:
                error_rate = errors / total
                if error_rate > HIGH_ERROR_RATE_THRESHOLD:
                    insights.append(
                        Insight(
                            insight_id=f"error_high_rate_{command}",
                            title=f"High Error Rate: {command}",
                            description=f"Command '{command}' has a {error_rate:.1%} error rate ({errors}/{total} executions)",
                            severity=(
                                "high" if error_rate > CRITICAL_ERROR_RATE_THRESHOLD else "medium"
                            ),
                            category="reliability",
                            confidence=min(0.9, total / 20),
                            impact="high",
                            recommendations=[
                                f"Investigate and fix the root cause of errors in {command}",
                                "Add better error handling and validation",
                                "Consider adding retry logic for transient failures",
                            ],
                            metadata={
                                "command": command,
                                "error_rate": error_rate,
                                "error_count": errors,
                                "total_executions": total,
                            },
                        )
                    )

        return insights

    def _analyze_security_insights(self, events: List[Dict[str, Any]]) -> List[Insight]:
        """Analyze security-related insights."""
        insights: List[Insight] = []

        # Check for sensitive data in arguments
        sensitive_patterns = [
            r"password",
            r"token",
            r"secret",
            r"key",
            r"auth",
            r"credential",
        ]

        sensitive_usage: Dict[str, int] = defaultdict(int)

        for event in events:
            args = event.get("args", {})
            for arg_key, arg_value in args.items():
                if isinstance(arg_value, str):
                    for pattern in sensitive_patterns:
                        if re.search(pattern, arg_key, re.IGNORECASE):
                            sensitive_usage[pattern] += 1
                            break

        # Generate security insights
        if sensitive_usage:
            total_sensitive = sum(sensitive_usage.values())
            insights.append(
                Insight(
                    insight_id="security_sensitive_data",
                    title="Sensitive Data Handling",
                    description=f"Detected {total_sensitive} instances of sensitive data in command arguments",
                    severity="medium",
                    category="security",
                    confidence=0.7,
                    impact="high",
                    recommendations=[
                        "Ensure sensitive data is properly sanitized before logging",
                        "Consider using secure input methods for sensitive parameters",
                        "Review telemetry data handling for privacy compliance",
                    ],
                    metadata={"sensitive_instances": dict(sensitive_usage)},
                )
            )

        return insights

    def get_insights_by_category(self, category: str) -> List[Insight]:
        """Get insights filtered by category."""
        return [insight for insight in self._insights if insight.category == category]

    def get_insights_by_severity(self, severity: str) -> List[Insight]:
        """Get insights filtered by severity."""
        return [insight for insight in self._insights if insight.severity == severity]

    def get_top_insights(self, limit: int = 10) -> List[Insight]:
        """Get top insights sorted by severity and confidence."""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        def sort_key(insight: Insight) -> Tuple[int, float]:
            return (severity_order.get(insight.severity, 0), insight.confidence)

        return sorted(self._insights, key=sort_key, reverse=True)[:limit]

    def export_insights(self, filepath: Path) -> None:
        """Export insights to JSON file."""
        try:
            insights_data = {
                "export_timestamp": datetime.now().isoformat(),
                "total_insights": len(self._insights),
                "insights": [
                    {
                        "insight_id": insight.insight_id,
                        "title": insight.title,
                        "description": insight.description,
                        "severity": insight.severity,
                        "category": insight.category,
                        "confidence": insight.confidence,
                        "impact": insight.impact,
                        "recommendations": insight.recommendations,
                        "metadata": insight.metadata,
                        "timestamp": insight.timestamp,
                    }
                    for insight in self._insights
                ],
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(insights_data, f, indent=2, ensure_ascii=False)

        except (OSError, IOError) as e:
            print(f"Failed to export insights: {e}", file=__import__("sys").stderr)
