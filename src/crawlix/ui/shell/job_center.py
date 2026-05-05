"""Global job dock / activity panel shell."""

from __future__ import annotations

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from crawlix.ui.design_tokens import spacing_px


class JobCenter(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("JobCenter")
        self._body = QVBoxLayout(self)
        self._body.setContentsMargins(spacing_px("8"), spacing_px("8"), spacing_px("8"), spacing_px("8"))
        self._body.setSpacing(spacing_px("4"))

    def body_layout(self) -> QVBoxLayout:
        return self._body
