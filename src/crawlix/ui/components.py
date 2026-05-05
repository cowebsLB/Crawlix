"""Reusable UI building blocks for the main shell pages."""

from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox, QLabel, QListWidget, QPushButton, QTextEdit, QVBoxLayout, QWidget


class InspectorPanel(QWidget):
    """Lightweight persistent inspector container with title + read-only body."""

    def __init__(self, title: str, placeholder: str, *, min_width: int = 340) -> None:
        super().__init__()
        self._layout = QVBoxLayout(self)
        self._title = QLabel(title)
        self._layout.addWidget(self._title)
        self.body = QTextEdit()
        self.body.setReadOnly(True)
        self.body.setMinimumWidth(min_width)
        self.body.setPlaceholderText(placeholder)
        self._layout.addWidget(self.body, 1)

    def set_text(self, text: str) -> None:
        self.body.setPlainText(text)

    def clear(self) -> None:
        self.body.clear()


class ActionListPanel(QGroupBox):
    """Card-like group with list + optional action button."""

    def __init__(self, title: str, *, button_label: str | None = None) -> None:
        super().__init__(title)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.button: QPushButton | None = None
        if button_label:
            self.button = QPushButton(button_label)
            layout.addWidget(self.button)
