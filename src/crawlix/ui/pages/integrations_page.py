"""Integrations page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from crawlix.services.integrations import IntegrationStatus
from crawlix.ui.components import SectionCard


def build_integrations_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    placeholders: Iterable[IntegrationStatus],
) -> QWidget:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)
    box = SectionCard(tr("Provider connection center"))
    iv = box.body_layout
    iv.addWidget(
        QLabel(
            tr(
                "Integration status is shown provider-by-provider. Live OAuth/data sync surfaces "
                "are planned in a later milestone."
            )
        )
    )
    for st in placeholders:
        card = SectionCard(st.provider.upper())
        status = QLabel(f"{tr('Status')}: {tr('Not connected')}")
        status.setProperty("role", "metadata")
        card.body_layout.addWidget(status)
        card.body_layout.addWidget(QLabel(tr("Data sync and permissions UI: planned")))
        iv.addWidget(card)
    iv.addStretch()
    lay.addWidget(box)
    lay.addStretch()
    return root
