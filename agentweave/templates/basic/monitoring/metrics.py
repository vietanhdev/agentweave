"""
Metrics module for collecting performance metrics of agent activities.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Metrics collector for tracking agent performance.
    """

    def __init__(self, metrics_dir: Optional[str] = None, flush_interval: int = 60):
        """
        Initialize the metrics collector.

        Args:
            metrics_dir: Directory to store metrics
            flush_interval: Interval in seconds to flush metrics to disk
        """
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "tool_usage": {},
            "errors": {},
        }

        self.last_flush_time = time.time()
        self.flush_interval = flush_interval

        if metrics_dir:
            self.metrics_dir = Path(metrics_dir)
            self.metrics_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.metrics_dir = Path("metrics")
            self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def record_request(
        self,
        success: bool,
        response_time: float,
        query: str,
        conversation_id: Optional[str] = None,
    ) -> None:
        """
        Record metrics for an agent request.

        Args:
            success: Whether the request was successful
            response_time: Time taken to respond in seconds
            query: The query that was processed
            conversation_id: Optional conversation ID
        """
        self.metrics["total_requests"] += 1

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        self.metrics["response_times"].append(response_time)

        # Check if we should flush metrics
        if time.time() - self.last_flush_time > self.flush_interval:
            self.flush_metrics()

    def record_tool_usage(
        self, tool_name: str, success: bool, execution_time: float
    ) -> None:
        """
        Record metrics for a tool usage.

        Args:
            tool_name: Name of the tool
            success: Whether the tool execution was successful
            execution_time: Time taken to execute the tool in seconds
        """
        if tool_name not in self.metrics["tool_usage"]:
            self.metrics["tool_usage"][tool_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "execution_times": [],
            }

        tool_metrics = self.metrics["tool_usage"][tool_name]
        tool_metrics["total_calls"] += 1

        if success:
            tool_metrics["successful_calls"] += 1
        else:
            tool_metrics["failed_calls"] += 1

        tool_metrics["execution_times"].append(execution_time)

    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an error.

        Args:
            error_type: Type of the error
            error_message: Error message
            context: Additional context for the error
        """
        if error_type not in self.metrics["errors"]:
            self.metrics["errors"][error_type] = {
                "count": 0,
                "examples": [],
            }

        error_metrics = self.metrics["errors"][error_type]
        error_metrics["count"] += 1

        # Store the error with context but limit the number of examples
        if len(error_metrics["examples"]) < 10:
            error_metrics["examples"].append(
                {
                    "message": error_message,
                    "context": context or {},
                    "timestamp": time.time(),
                }
            )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the metrics.

        Returns:
            A dictionary with summarized metrics
        """
        # Calculate summary statistics
        total_requests = self.metrics["total_requests"]
        if total_requests > 0:
            success_rate = self.metrics["successful_requests"] / total_requests * 100
        else:
            success_rate = 0

        response_times = self.metrics["response_times"]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
            min_response_time = 0

        # Summarize tool usage
        tool_usage_summary = {}
        for tool_name, tool_metrics in self.metrics["tool_usage"].items():
            total_calls = tool_metrics["total_calls"]
            if total_calls > 0:
                success_rate_tool = tool_metrics["successful_calls"] / total_calls * 100
                avg_execution_time = sum(tool_metrics["execution_times"]) / len(
                    tool_metrics["execution_times"]
                )
            else:
                success_rate_tool = 0
                avg_execution_time = 0

            tool_usage_summary[tool_name] = {
                "total_calls": total_calls,
                "success_rate": success_rate_tool,
                "avg_execution_time": avg_execution_time,
            }

        # Create the summary
        summary = {
            "total_requests": total_requests,
            "success_rate": success_rate,
            "response_time": {
                "avg": avg_response_time,
                "max": max_response_time,
                "min": min_response_time,
            },
            "tool_usage": tool_usage_summary,
            "error_count": sum(
                error["count"] for error in self.metrics["errors"].values()
            ),
            "most_common_errors": sorted(
                [
                    {"type": err_type, "count": err_data["count"]}
                    for err_type, err_data in self.metrics["errors"].items()
                ],
                key=lambda x: x["count"],
                reverse=True,
            )[:5],
        }

        return summary

    def flush_metrics(self) -> None:
        """
        Flush metrics to disk.
        """
        timestamp = int(time.time())
        metrics_file = self.metrics_dir / f"metrics_{timestamp}.json"

        with open(metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

        # Reset certain metrics after flushing
        self.metrics["response_times"] = []

        # Reset the flush timer
        self.last_flush_time = time.time()

        logger.info(f"Metrics flushed to {metrics_file}")

    def timing_decorator(self, func: Callable) -> Callable:
        """
        Decorator to time function execution and record metrics.

        Args:
            func: The function to time

        Returns:
            The timed function
        """

        def wrapped(*args, **kwargs):
            start_time = time.time()
            is_tool = kwargs.get("is_tool", False)
            tool_name = kwargs.get("tool_name", func.__name__)

            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time

                if is_tool:
                    self.record_tool_usage(tool_name, True, execution_time)

                return result
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time

                if is_tool:
                    self.record_tool_usage(tool_name, False, execution_time)

                self.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={"function": func.__name__},
                )
                raise e

        return wrapped


# Singleton instance
metrics = MetricsCollector()
