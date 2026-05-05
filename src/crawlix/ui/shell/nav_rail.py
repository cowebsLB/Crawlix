"""Collapsible workflow rail (navigation list + toggle affordance)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from crawlix.ui.design_tokens import spacing_px


class NavRailColumn(QWidget):
    def __init__(
        self,
        nav_toggle: QToolButton,
        nav_list: QListWidget,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("NavRailColumn")
        self._toggle = nav_toggle
        self._nav = nav_list
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(spacing_px("4"))
        th = QHBoxLayout()
        th.setContentsMargins(0, 0, 0, 0)
        th.addStretch()
        th.addWidget(self._toggle)
        vl.addLayout(th)
        vl.addWidget(self._nav, 1)
