"""Shared page layout helpers for consistent command/workspace/inspector structure."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QWidget


def table_with_inspector_split(
    table_widget: QWidget,
    inspector_widget: QWidget,
    *,
    left_stretch: int = 3,
    right_stretch: int = 2,
) -> QSplitter:
    split = QSplitter(Qt.Orientation.Horizontal)
    split.addWidget(table_widget)
    split.addWidget(inspector_widget)
    split.setStretchFactor(0, left_stretch)
    split.setStretchFactor(1, right_stretch)
    return split
