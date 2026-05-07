"""Reusable UI building blocks for the main shell pages."""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QPushButton, QTextEdit, QVBoxLayout, QWidget


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


class SectionCard(QWidget):
    """Semantic card container replacing ad hoc QGroupBox usage."""

    def __init__(self, title: str, subtitle: str | None = None) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame()
        self.frame.setObjectName("SectionCard")
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(8)
        self.title = QLabel(title)
        frame_layout.addWidget(self.title)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("role", "metadata")
            sub.setWordWrap(True)
            frame_layout.addWidget(sub)
        self.body_layout = frame_layout
        root.addWidget(self.frame)


class ActionListPanel(SectionCard):
    """Card-like panel with list + optional action button."""

    def __init__(self, title: str, *, button_label: str | None = None) -> None:
        super().__init__(title)
        layout = self.body_layout
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.button: QPushButton | None = None
        if button_label:
            self.button = QPushButton(button_label)
            layout.addWidget(self.button)


class PageHeader(QWidget):
    """Reusable page identity block (title + optional subtitle)."""

    def __init__(self, title: str, subtitle: str | None = None, *, eyebrow: str | None = None) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 6)
        if eyebrow:
            e = QLabel(eyebrow)
            e.setProperty("role", "metadata")
            root.addWidget(e)
        heading = QLabel(title)
        heading_font = QFont(heading.font())
        heading_font.setPointSize(15)
        heading_font.setBold(True)
        heading.setFont(heading_font)
        root.addWidget(heading)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setWordWrap(True)
            root.addWidget(sub)


class EmptyState(SectionCard):
    """Intentional empty-state surface with title/body and optional actions."""

    def __init__(
        self,
        title: str,
        description: str,
        *,
        primary_label: str | None = None,
        secondary_label: str | None = None,
    ) -> None:
        super().__init__(title)
        desc = QLabel(description)
        desc.setWordWrap(True)
        self.body_layout.addWidget(desc)
        self.primary_button: QPushButton | None = None
        self.secondary_button: QPushButton | None = None
        if primary_label:
            self.primary_button = QPushButton(primary_label)
            self.body_layout.addWidget(self.primary_button)
        if secondary_label:
            self.secondary_button = QPushButton(secondary_label)
            self.secondary_button.setProperty("variant", "secondary")
            self.body_layout.addWidget(self.secondary_button)


class FilterBar(SectionCard):
    """Shared filter surface with explicit active-filter summary label."""

    def __init__(self, title: str = "Filters", subtitle: str | None = None) -> None:
        super().__init__(title, subtitle)
        self.summary_label = QLabel("")
        self.summary_label.setProperty("role", "metadata")
        self.body_layout.addWidget(self.summary_label)

    def set_summary(self, text: str) -> None:
        self.summary_label.setText(text)


class DataGridToolbar(SectionCard):
    """Shared toolbar row for table/data-grid actions."""

    def __init__(self, title: str = "Table actions", subtitle: str | None = None) -> None:
        super().__init__(title, subtitle)
        self.actions_row = QHBoxLayout()
        self.actions_row.setSpacing(8)
        self.body_layout.addLayout(self.actions_row)

    def add_action(self, label: str, on_click: object, *, variant: str | None = None) -> QPushButton:
        btn = QPushButton(label)
        if variant:
            btn.setProperty("variant", variant)
        btn.clicked.connect(on_click)  # type: ignore[arg-type]
        self.actions_row.addWidget(btn)
        return btn

    def add_stretch(self) -> None:
        self.actions_row.addStretch()


class StatusPill(QLabel):
    """Compact semantic status label using QSS dynamic properties."""

    def __init__(self, text: str, *, status: str = "neutral") -> None:
        super().__init__(text)
        self.setObjectName("StatusPill")
        self.setProperty("status", status)
        self.setProperty("role", "metadata")

    def set_status(self, text: str, *, status: str) -> None:
        self.setText(text)
        self.setProperty("status", status)
        # Re-polish so QSS property selectors apply immediately.
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)


class MethodologyPanel(SectionCard):
    """Trust/limitations explainer block for SERP, citations, crawl, and AI modules."""

    def __init__(self, title: str, summary: str, points: list[str] | None = None) -> None:
        super().__init__(title)
        lead = QLabel(summary)
        lead.setWordWrap(True)
        self.body_layout.addWidget(lead)
        if points:
            bullets = "\n".join(f"• {p}" for p in points)
            details = QLabel(bullets)
            details.setWordWrap(True)
            details.setProperty("role", "metadata")
            self.body_layout.addWidget(details)
