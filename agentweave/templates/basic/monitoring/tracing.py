"""
Tracing module for monitoring agent activities.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class Tracer:
    """
    Tracer for monitoring and debugging agent activities.
    This class provides functionality to log, trace, and visualize agent actions.
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        console_logging: bool = True,
        file_logging: bool = True,
    ):
        """
        Initialize the tracer.

        Args:
            log_dir: Directory to store trace logs
            console_logging: Whether to log to console
            file_logging: Whether to log to file
        """
        self.traces = []
        self.console_logging = console_logging
        self.file_logging = file_logging

        if log_dir:
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.log_dir = Path("logs")
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        if self.console_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

        # Create a new trace file for this session
        if self.file_logging:
            self.trace_file = self.log_dir / f"trace_{int(time.time())}.jsonl"

    def start_trace(
        self, trace_type: str, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new trace.

        Args:
            trace_type: Type of the trace (e.g., "agent_action", "tool_call")
            conversation_id: Optional ID of the conversation

        Returns:
            The trace object
        """
        trace = {
            "id": len(self.traces) + 1,
            "type": trace_type,
            "conversation_id": conversation_id,
            "start_time": time.time(),
            "end_time": None,
            "duration": None,
            "status": "running",
            "data": {},
        }

        self.traces.append(trace)
        return trace

    def update_trace(
        self, trace: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing trace with new data.

        Args:
            trace: The trace to update
            data: The data to update with

        Returns:
            The updated trace
        """
        trace["data"].update(data)
        return trace

    def end_trace(
        self,
        trace: Dict[str, Any],
        status: str = "success",
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        End a trace.

        Args:
            trace: The trace to end
            status: Status of the completed trace
            data: Additional data to add

        Returns:
            The completed trace
        """
        trace["end_time"] = time.time()
        trace["duration"] = trace["end_time"] - trace["start_time"]
        trace["status"] = status

        if data:
            trace["data"].update(data)

        self._log_trace(trace)
        return trace

    def _log_trace(self, trace: Dict[str, Any]) -> None:
        """
        Log a trace to the configured outputs.

        Args:
            trace: The trace to log
        """
        # Log to console if enabled
        if self.console_logging:
            logger.info(
                f"Trace: {trace['type']} - Status: {trace['status']} - Duration: {trace['duration']:.4f}s"
            )

        # Write to trace file if enabled
        if self.file_logging:
            with open(self.trace_file, "a") as f:
                f.write(json.dumps(trace) + "\n")

    def trace_function(self, func: Callable) -> Callable:
        """
        Decorator to trace function execution.

        Args:
            func: The function to trace

        Returns:
            The traced function
        """

        def wrapped(*args, **kwargs):
            trace = self.start_trace(
                trace_type=f"function_{func.__name__}",
                conversation_id=kwargs.get("conversation_id"),
            )

            try:
                result = func(*args, **kwargs)
                self.end_trace(
                    trace,
                    status="success",
                    data={"args": str(args), "kwargs": str(kwargs)},
                )
                return result
            except Exception as e:
                self.end_trace(
                    trace,
                    status="error",
                    data={"error": str(e), "args": str(args), "kwargs": str(kwargs)},
                )
                raise e

        return wrapped


# Singleton instance
tracer = Tracer()
