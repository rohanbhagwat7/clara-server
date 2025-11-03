"""Performance metrics collection and monitoring.

Tracks key metrics to validate Phase 1 success criteria:
- Response time for all function tools (<5 second target)
- Factory specification lookup performance
- Data capture completion rates
- Service usage statistics

Supports both local logging and future integration with monitoring systems
(Prometheus, Grafana, Datadog, etc.)
"""

import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


logger = logging.getLogger("metrics")


@dataclass
class FunctionCallMetric:
    """Metrics for a single function tool call."""
    function_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/export."""
        return {
            "function_name": self.function_name,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class PerformanceMonitor:
    """Lightweight performance monitoring for function tools."""

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: List[FunctionCallMetric] = []
        self.function_call_counts = defaultdict(int)
        self.function_total_duration = defaultdict(float)
        self.function_error_counts = defaultdict(int)
        self.slow_calls_threshold_ms = 5000  # 5 second target
        logger.info("Initialized performance monitor")

    def record_function_call(
        self,
        function_name: str,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Record a function tool call.

        Args:
            function_name: Name of function tool
            duration_ms: Duration in milliseconds
            success: Whether call succeeded
            error_message: Error message if failed
            metadata: Additional context (model number, etc.)
        """
        end_time = time.time()
        start_time = end_time - (duration_ms / 1000.0)

        metric = FunctionCallMetric(
            function_name=function_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata or {},
        )

        self.metrics.append(metric)
        self.function_call_counts[function_name] += 1
        self.function_total_duration[function_name] += duration_ms

        if not success:
            self.function_error_counts[function_name] += 1

        # Log slow calls
        if duration_ms > self.slow_calls_threshold_ms:
            logger.warning(
                f"Slow function call: {function_name} took {duration_ms:.0f}ms (>{self.slow_calls_threshold_ms}ms threshold)"
            )

        # Log errors
        if not success:
            logger.error(f"Function call failed: {function_name} - {error_message}")

    def get_function_stats(self, function_name: str) -> Dict:
        """Get statistics for a specific function.

        Args:
            function_name: Name of function tool

        Returns:
            Dictionary with call count, avg duration, error rate, etc.
        """
        call_count = self.function_call_counts[function_name]
        if call_count == 0:
            return {
                "function_name": function_name,
                "call_count": 0,
                "avg_duration_ms": 0,
                "error_count": 0,
                "error_rate": 0.0,
            }

        total_duration = self.function_total_duration[function_name]
        error_count = self.function_error_counts[function_name]

        return {
            "function_name": function_name,
            "call_count": call_count,
            "avg_duration_ms": total_duration / call_count,
            "total_duration_ms": total_duration,
            "error_count": error_count,
            "error_rate": error_count / call_count,
        }

    def get_all_stats(self) -> Dict:
        """Get statistics for all functions.

        Returns:
            Dictionary with stats for each function
        """
        stats = {}
        for function_name in self.function_call_counts.keys():
            stats[function_name] = self.get_function_stats(function_name)
        return stats

    def get_slow_calls(self, threshold_ms: Optional[float] = None) -> List[FunctionCallMetric]:
        """Get all calls that exceeded the threshold.

        Args:
            threshold_ms: Optional custom threshold (default: 5000ms)

        Returns:
            List of slow function call metrics
        """
        threshold = threshold_ms or self.slow_calls_threshold_ms
        return [m for m in self.metrics if m.duration_ms > threshold]

    def get_failed_calls(self) -> List[FunctionCallMetric]:
        """Get all failed function calls.

        Returns:
            List of failed function call metrics
        """
        return [m for m in self.metrics if not m.success]

    def generate_report(self) -> str:
        """Generate a human-readable performance report.

        Returns:
            Formatted report string
        """
        lines = ["**Performance Report**\n"]

        # Overall stats
        total_calls = sum(self.function_call_counts.values())
        total_duration = sum(self.function_total_duration.values())
        total_errors = sum(self.function_error_counts.values())

        lines.append(f"**Overall Statistics:**")
        lines.append(f"  • Total function calls: {total_calls}")
        lines.append(f"  • Total duration: {total_duration:.0f}ms")
        lines.append(f"  • Average duration: {total_duration / total_calls:.0f}ms" if total_calls > 0 else "  • Average duration: N/A")
        lines.append(f"  • Total errors: {total_errors}")
        lines.append(f"  • Error rate: {total_errors / total_calls * 100:.1f}%" if total_calls > 0 else "  • Error rate: 0%")

        # Per-function stats
        lines.append("\n**Per-Function Statistics:**")
        all_stats = self.get_all_stats()
        for function_name, stats in sorted(all_stats.items(), key=lambda x: x[1]['call_count'], reverse=True):
            lines.append(f"\n  **{function_name}:**")
            lines.append(f"    - Calls: {stats['call_count']}")
            lines.append(f"    - Avg Duration: {stats['avg_duration_ms']:.0f}ms")
            lines.append(f"    - Errors: {stats['error_count']} ({stats['error_rate'] * 100:.1f}%)")

            # Flag if slow
            if stats['avg_duration_ms'] > self.slow_calls_threshold_ms:
                lines.append(f"    - ⚠️ SLOW: Exceeds {self.slow_calls_threshold_ms}ms target")

        # Slow calls
        slow_calls = self.get_slow_calls()
        if slow_calls:
            lines.append(f"\n**Slow Calls (>{self.slow_calls_threshold_ms}ms):** {len(slow_calls)}")
            for call in slow_calls[:5]:  # Show top 5
                lines.append(f"  • {call.function_name}: {call.duration_ms:.0f}ms")

        # Failed calls
        failed_calls = self.get_failed_calls()
        if failed_calls:
            lines.append(f"\n**Failed Calls:** {len(failed_calls)}")
            for call in failed_calls[:5]:  # Show top 5
                lines.append(f"  • {call.function_name}: {call.error_message}")

        return "\n".join(lines)

    def export_metrics_json(self) -> str:
        """Export all metrics as JSON.

        Returns:
            JSON string with all metrics
        """
        return json.dumps([m.to_dict() for m in self.metrics], indent=2)

    def clear_metrics(self):
        """Clear all collected metrics (for testing or periodic reset)."""
        self.metrics.clear()
        self.function_call_counts.clear()
        self.function_total_duration.clear()
        self.function_error_counts.clear()
        logger.info("Cleared all metrics")


# Global singleton instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get singleton instance of performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


class PerformanceTimer:
    """Context manager for timing function calls.

    Usage:
        with PerformanceTimer("get_factory_specifications", {"model": "ABC123"}):
            # Do work
            pass
    """

    def __init__(self, function_name: str, metadata: Optional[Dict] = None):
        """Initialize performance timer.

        Args:
            function_name: Name of function being timed
            metadata: Optional metadata to attach to metric
        """
        self.function_name = function_name
        self.metadata = metadata or {}
        self.start_time = None
        self.monitor = get_performance_monitor()

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record metric."""
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000

        success = exc_type is None
        error_message = str(exc_val) if exc_val else None

        self.monitor.record_function_call(
            function_name=self.function_name,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=self.metadata,
        )

        # Don't suppress exceptions
        return False
