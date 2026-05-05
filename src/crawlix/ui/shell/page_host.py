"""Dedicated container for stacked page bodies (future page header docks here)."""

from __future__ import annotations

from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget


class PageHost(QWidget):
    def __init__(self, stack: QStackedWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PageHost")
        self._stack = stack
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._stack, 1)

    def stack(self) -> QStackedWidget:
        return self._stack
