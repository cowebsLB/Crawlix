"""Block mouse wheel from changing numeric steppers and combo boxes (scroll parent instead)."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtWidgets import QAbstractSpinBox, QApplication, QComboBox, QScrollBar

_guard: QObject | None = None


class _AppWheelStepBlocker(QObject):
    """Application-wide: swallow wheel on spin boxes and combo boxes (not scroll bars)."""

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)

    def eventFilter(self, _watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.Wheel:
            return False
        if isinstance(_watched, QScrollBar):
            return False
        if isinstance(_watched, (QAbstractSpinBox, QComboBox)):
            return True
        return False


def install_app_wheel_step_blocker(app: QApplication) -> None:
    """Install once per process. Safe to call multiple times."""
    global _guard
    if _guard is not None:
        return
    _guard = _AppWheelStepBlocker(app)  # parent = app for lifetime
    app.installEventFilter(_guard)
