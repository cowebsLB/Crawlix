"""Qt signals for job progress (GUI thread only)."""

from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal


class JobBus(QObject):
    progress = pyqtSignal(int, float, str)
    finished = pyqtSignal(int, dict)
    failed = pyqtSignal(int, str, str)
    # Lightweight UI tasks without a Job row (e.g. export file, check updates).
    # pct < 0 means indeterminate progress bar.
    task_progress = pyqtSignal(str, float, str)
    task_finished = pyqtSignal(str, dict)
    task_failed = pyqtSignal(str, str, str)
