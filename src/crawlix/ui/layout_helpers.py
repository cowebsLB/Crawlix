"""Shared layout helpers for stacked pages (margins, spacing, scroll)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QScrollArea, QVBoxLayout, QWidget


def wrap_page_content(inner: QWidget, *, margins: tuple[int, int, int, int] = (16, 12, 16, 12)) -> QScrollArea:
    """Wrap page body in a scroll area so tall modules stay usable at any window size."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

    container = QWidget()
    v = QVBoxLayout(container)
    v.setContentsMargins(*margins)
    v.setSpacing(12)
    v.addWidget(inner, 0, Qt.AlignmentFlag.AlignTop)

    scroll.setWidget(container)
    return scroll
