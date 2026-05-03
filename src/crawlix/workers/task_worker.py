"""Run a simple callable on the thread pool with JobBus task_* signals."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QRunnable

from crawlix.workers.job_bus import JobBus


class SimpleTaskWorker(QRunnable):
    """Emits task_progress (pct=-1 for indeterminate), then task_finished or task_failed."""

    def __init__(
        self,
        task_id: str,
        bus: JobBus,
        fn: Callable[[], Any],
        *,
        started_message: str = "…",
    ) -> None:
        super().__init__()
        self.task_id = task_id
        self.bus = bus
        self.fn = fn
        self.started_message = started_message

    def run(self) -> None:
        self.bus.task_progress.emit(self.task_id, -1.0, self.started_message)
        try:
            result = self.fn()
            self.bus.task_finished.emit(self.task_id, {"result": result})
        except Exception as e:
            self.bus.task_failed.emit(self.task_id, type(e).__name__, str(e))
