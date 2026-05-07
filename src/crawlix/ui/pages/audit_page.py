"""Audit page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import QLabel, QProgressBar, QTableWidget, QVBoxLayout, QWidget

from crawlix.ui.components import DataGridToolbar, FilterBar, InspectorPanel, ProgressStrip, SectionCard
from crawlix.ui.controllers_filters import audit_filter_field_labels
from crawlix.ui.controllers_toolbar import audit_results_toolbar_actions, audit_run_toolbar_actions
from crawlix.ui.page_sections import table_with_inspector_split


@dataclass
class AuditPageRefs:
    audit_btn: object
    audit_progress: QProgressBar
    audit_status: QLabel
    audit_filter_bar: FilterBar
    audit_search: object
    audit_max_score: object
    audit_min_issues: object
    audit_results_table: QTableWidget
    audit_row_meta: list[dict[str, object]]
    audit_inspector_panel: InspectorPanel
    audit_inspector: object


def build_audit_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    on_start_audit: Callable[[], None],
    on_refresh_results: Callable[[], None],
    on_export_audits_csv: Callable[[], None],
    on_export_audits_json: Callable[[], None],
    on_selection_changed: Callable[[], None],
) -> tuple[QWidget, AuditPageRefs]:
    from PyQt6.QtWidgets import QDoubleSpinBox, QLineEdit, QSpinBox

    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(12)
    lay.addWidget(header)

    run_box = SectionCard(tr("Run"))
    rv = run_box.body_layout
    run_toolbar = DataGridToolbar(tr("Audit actions"))
    audit_btn = None
    run_callbacks = {"audit_run_crawled_pages": on_start_audit}
    for action in audit_run_toolbar_actions():
        callback = run_callbacks.get(action.action_id)
        if callback is None:
            continue
        created = run_toolbar.add_action(tr(action.label), callback, variant=action.variant)
        if action.action_id == "audit_run_crawled_pages":
            audit_btn = created
    run_toolbar.add_stretch()
    assert audit_btn is not None
    rv.addWidget(run_toolbar)
    audit_progress_strip = ProgressStrip(tr("Audit progress"))
    rv.addWidget(audit_progress_strip)
    audit_progress = audit_progress_strip.progress_bar
    audit_status = audit_progress_strip.status_label
    lay.addWidget(run_box)

    audit_toolbar = DataGridToolbar(tr("Results actions"))
    results_callbacks = {
        "audit_refresh_results": on_refresh_results,
        "audit_export_csv": on_export_audits_csv,
        "audit_export_json": on_export_audits_json,
    }
    for action in audit_results_toolbar_actions():
        callback = results_callbacks.get(action.action_id)
        if callback is not None:
            audit_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    audit_toolbar.add_stretch()
    lay.addWidget(audit_toolbar)

    audit_filter_bar = FilterBar(
        tr("Result filters"),
        tr("Focus audit rows by URL match, score threshold, and issue volume."),
    )
    audit_filter_bar.set_summary(tr("Active filters: none"))
    af = audit_filter_bar.body_layout
    controls = DataGridToolbar(tr("Filter controls"))
    search_label, max_score_label, min_issues_label = audit_filter_field_labels()
    controls.actions_row.addWidget(QLabel(tr(search_label)))
    audit_search = QLineEdit()
    audit_search.setPlaceholderText(tr("Substring match…"))
    audit_search.textChanged.connect(on_refresh_results)
    controls.actions_row.addWidget(audit_search, 1)
    controls.actions_row.addWidget(QLabel(tr(max_score_label)))
    audit_max_score = QDoubleSpinBox()
    audit_max_score.setRange(-1.0, 100.0)
    audit_max_score.setSingleStep(5.0)
    audit_max_score.setValue(-1.0)
    audit_max_score.setSpecialValueText(tr("Any"))
    audit_max_score.valueChanged.connect(on_refresh_results)
    controls.actions_row.addWidget(audit_max_score)
    controls.actions_row.addWidget(QLabel(tr(min_issues_label)))
    audit_min_issues = QSpinBox()
    audit_min_issues.setRange(0, 99)
    audit_min_issues.setValue(0)
    audit_min_issues.valueChanged.connect(on_refresh_results)
    controls.actions_row.addWidget(audit_min_issues)
    controls.add_stretch()
    af.addWidget(controls)
    lay.addWidget(audit_filter_bar)

    results_card = SectionCard(tr("Audit results"))
    audit_results_table = QTableWidget(0, 8)
    audit_results_table.setHorizontalHeaderLabels(
        [
            tr("Audit ID"),
            tr("Page ID"),
            tr("URL"),
            tr("Depth"),
            tr("In"),
            tr("Out"),
            tr("Score"),
            tr("Issues"),
        ]
    )
    audit_results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    audit_results_table.itemSelectionChanged.connect(on_selection_changed)
    audit_results_table.setColumnWidth(2, 280)
    audit_row_meta: list[dict[str, object]] = []
    audit_inspector_panel = InspectorPanel(
        tr("Inspector"),
        tr("Select an audit row to inspect prioritized insights."),
        min_width=360,
    )
    audit_inspector = audit_inspector_panel.body
    split = table_with_inspector_split(audit_results_table, audit_inspector_panel)
    results_card.body_layout.addWidget(split)
    lay.addWidget(results_card, 1)

    refs = AuditPageRefs(
        audit_btn=audit_btn,
        audit_progress=audit_progress,
        audit_status=audit_status,
        audit_filter_bar=audit_filter_bar,
        audit_search=audit_search,
        audit_max_score=audit_max_score,
        audit_min_issues=audit_min_issues,
        audit_results_table=audit_results_table,
        audit_row_meta=audit_row_meta,
        audit_inspector_panel=audit_inspector_panel,
        audit_inspector=audit_inspector,
    )
    return root, refs
