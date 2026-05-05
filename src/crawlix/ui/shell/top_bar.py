"""Top command strip: project identity, future global search / job badges."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QWidget

from crawlix.ui.design_tokens import spacing_px


class TopCommandStrip(QWidget):
    """Dense top row above the workspace; callers add widgets to :meth:`stretch_content`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TopCommandStrip")
        self._root = QHBoxLayout(self)
        self._root.setContentsMargins(spacing_px("12"), spacing_px("8"), spacing_px("12"), spacing_px("8"))
        self._root.setSpacing(spacing_px("8"))
