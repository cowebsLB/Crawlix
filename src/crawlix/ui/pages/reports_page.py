"""Reports page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from crawlix.ui.components import DataGridToolbar, EmptyState, ProgressStrip, SectionCard
from crawlix.ui.controllers_toolbar import reports_export_toolbar_actions


@dataclass
class ReportsPageRefs:
    export_btn: object
    reports_progress: QProgressBar
    reports_status: QLabel


def build_reports_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    on_export_markdown: Callable[[], None],
) -> tuple[QWidget, ReportsPageRefs]:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)
    state = EmptyState(
        tr("Report builder preview"),
        tr(
            "Use this module to assemble technical audit, crawl, citations, and keyword summaries. "
            "Structured templates and multi-format bundles are planned."
        ),
    )
    lay.addWidget(state)
    ex = SectionCard(tr("Export"))
    ev = ex.body_layout
    export_toolbar = DataGridToolbar(tr("Export actions"))
    export_btn = None
    export_callbacks = {"reports_export_markdown": on_export_markdown}
    for action in reports_export_toolbar_actions():
        callback = export_callbacks.get(action.action_id)
        if callback is None:
            continue
        created = export_toolbar.add_action(tr(action.label), callback, variant=action.variant)
        if action.action_id == "reports_export_markdown":
            export_btn = created
    export_toolbar.add_stretch()
    assert export_btn is not None
    ev.addWidget(export_toolbar)
    reports_progress_strip = ProgressStrip(tr("Export progress"))
    reports_progress = reports_progress_strip.progress_bar
    reports_status = reports_progress_strip.status_label
    reports_progress.setRange(0, 0)
    reports_progress.setTextVisible(False)
    ev.addWidget(reports_progress_strip)
    lay.addWidget(ex)
    lay.addStretch()
    refs = ReportsPageRefs(
        export_btn=export_btn,
        reports_progress=reports_progress,
        reports_status=reports_status,
    )
    return root, refs
