"""Local page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from crawlix.ui.components import EmptyState


def build_local_page(*, header: QWidget, tr: Callable[[str], str]) -> QWidget:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)
    description = tr(
        "GBP / local pack is a roadmap-preview module. Crawlix stays explicit about constraints: "
        "official APIs and user-supplied evidence, no implied unsupported scraping.\n\n"
        "Planned checklist direction:\n"
        "• NAP consistency across on-site and major listings (manual or API-backed).\n"
        "• GBP profile completeness (hours, categories, services) with official-tool links.\n"
        "• Local pack / map visibility only where SERP captures or third-party data support defensible reads.\n"
        "• Review and Q&A hygiene with policy-first guidance."
    )
    state = EmptyState(
        tr("Local module preview"),
        description,
        primary_label=tr("Open local roadmap"),
    )
    intro = QLabel(tr("See docs/local-pack-roadmap.md for product constraints and planned delivery."))
    intro.setWordWrap(True)
    intro.setProperty("role", "metadata")
    state.body_layout.addWidget(intro)
    assert state.primary_button is not None
    state.primary_button.clicked.connect(
        lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path("docs/local-pack-roadmap.md").resolve())))
    )
    lay.addWidget(state)
    lay.addStretch()
    return root
