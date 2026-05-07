"""Citations page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QLabel,
    QProgressBar,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from crawlix.ui.components import DataGridToolbar, MethodologyPanel, ProgressStrip, SectionCard
from crawlix.ui.controllers_toolbar import (
    citations_history_toolbar_actions,
    citations_location_toolbar_actions,
    citations_matrix_toolbar_actions,
    citations_source_toolbar_actions,
)
from crawlix.ui.page_sections import table_with_inspector_split


@dataclass
class CitationsPageRefs:
    cit_run_btn: object
    cit_progress: QProgressBar
    cit_save_view_btn: object
    cit_load_view_btn: object
    cit_status: QLabel
    cit_src_table: QTableWidget
    cit_loc_table: QTableWidget
    cit_chk_table: QTableWidget
    cit_chk_row_meta: list[dict[str, object]]
    cit_inspector_panel: QWidget
    cit_inspector: object
    cit_tabs: QTabWidget


def build_citations_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    make_inspector_panel: Callable[[], QWidget],
    on_run_citation_matrix: Callable[[], None],
    on_refresh_citations_page: Callable[[], None],
    on_save_citations_saved_view: Callable[[], None],
    on_apply_citations_saved_view: Callable[[], None],
    on_refresh_citations_builtin_table: Callable[[], None],
    on_export_builtin_citations_csv: Callable[[], None],
    on_refresh_citations_locations_table: Callable[[], None],
    on_refresh_citations_checks_table: Callable[[], None],
    on_citations_check_selection_changed: Callable[[], None],
) -> tuple[QWidget, CitationsPageRefs]:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)
    lay.addWidget(
        MethodologyPanel(
            tr("How citation checks work"),
            tr(
                "Run a citation matrix job to record one row per (location × built-in source). "
                "HTTP templates run directly; Playwright-only templates are marked skipped."
            ),
            points=[
                tr("A failed row does not always mean listing absence; it can indicate blocking or timeout."),
                tr("Use final URL, HTTP, and error columns to decide whether re-checking is needed."),
            ],
        )
    )

    run_box = SectionCard(tr("Matrix job"))
    rv = run_box.body_layout
    matrix_toolbar = DataGridToolbar(tr("Matrix actions"))
    cit_run_btn = None
    cit_save_view_btn = None
    cit_load_view_btn = None
    matrix_callbacks = {
        "citations_run_matrix": on_run_citation_matrix,
        "citations_refresh_all": on_refresh_citations_page,
        "citations_save_view": on_save_citations_saved_view,
        "citations_load_view": on_apply_citations_saved_view,
    }
    for action in citations_matrix_toolbar_actions():
        callback = matrix_callbacks.get(action.action_id)
        if callback is None:
            continue
        created = matrix_toolbar.add_action(tr(action.label), callback, variant=action.variant)
        if action.action_id == "citations_run_matrix":
            cit_run_btn = created
        elif action.action_id == "citations_save_view":
            cit_save_view_btn = created
        elif action.action_id == "citations_load_view":
            cit_load_view_btn = created
    matrix_toolbar.add_stretch()
    rv.addWidget(matrix_toolbar)
    cit_progress_strip = ProgressStrip(tr("Citation matrix progress"))
    rv.addWidget(cit_progress_strip)
    cit_progress = cit_progress_strip.progress_bar
    cit_status = cit_progress_strip.status_label
    lay.addWidget(run_box)

    tabs = QTabWidget()
    tabs.setDocumentMode(True)

    src_tab = QWidget()
    sv = QVBoxLayout(src_tab)
    sv.setSpacing(10)
    src_box = SectionCard(tr("Built-in sources"))
    sbi = src_box.body_layout
    src_toolbar = DataGridToolbar(tr("Source actions"))
    src_callbacks = {
        "citations_sources_refresh": on_refresh_citations_builtin_table,
        "citations_sources_export_csv": on_export_builtin_citations_csv,
    }
    for action in citations_source_toolbar_actions():
        callback = src_callbacks.get(action.action_id)
        if callback is not None:
            src_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    src_toolbar.add_stretch()
    sbi.addWidget(src_toolbar)
    sv.addWidget(src_box)
    cit_src_table = QTableWidget(0, 7)
    cit_src_table.setHorizontalHeaderLabels(
        [
            tr("ID"),
            tr("Name"),
            tr("Template URL"),
            tr("Regions"),
            tr("Playwright"),
            tr("Enabled"),
            tr("Pack"),
        ]
    )
    cit_src_table.setColumnWidth(2, 420)
    sv.addWidget(cit_src_table, 1)
    tabs.addTab(src_tab, tr("Built-in sources"))

    loc_tab = QWidget()
    lv = QVBoxLayout(loc_tab)
    lv.setSpacing(10)
    loc_box = SectionCard(tr("Locations (NAP)"))
    lbi = loc_box.body_layout
    lbi.addWidget(
        QLabel(
            tr(
                "Locations belong to the current project "
                "(optional NAP at project creation; dedicated editor later)."
            )
        )
    )
    loc_toolbar = DataGridToolbar(tr("Location actions"))
    loc_callbacks = {"citations_locations_refresh": on_refresh_citations_locations_table}
    for action in citations_location_toolbar_actions():
        callback = loc_callbacks.get(action.action_id)
        if callback is not None:
            loc_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    loc_toolbar.add_stretch()
    lbi.addWidget(loc_toolbar)
    lv.addWidget(loc_box)
    cit_loc_table = QTableWidget(0, 7)
    cit_loc_table.setHorizontalHeaderLabels(
        [
            tr("ID"),
            tr("Label"),
            tr("Business name"),
            tr("Address"),
            tr("City"),
            tr("Region"),
            tr("Phone"),
        ]
    )
    cit_loc_table.setColumnWidth(2, 220)
    lv.addWidget(cit_loc_table, 1)
    tabs.addTab(loc_tab, tr("Locations"))

    chk_tab = QWidget()
    cv = QVBoxLayout(chk_tab)
    cv.setSpacing(10)
    chk_box = SectionCard(tr("Check history"))
    cbi = chk_box.body_layout
    cbi.addWidget(QLabel(tr("Latest rows for this project’s locations (newest first, up to 500).")))
    chk_toolbar = DataGridToolbar(tr("History actions"))
    history_callbacks = {"citations_history_refresh": on_refresh_citations_checks_table}
    for action in citations_history_toolbar_actions():
        callback = history_callbacks.get(action.action_id)
        if callback is not None:
            chk_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    chk_toolbar.add_stretch()
    cbi.addWidget(chk_toolbar)
    cv.addWidget(chk_box)
    cit_chk_table = QTableWidget(0, 8)
    cit_chk_table.setHorizontalHeaderLabels(
        [
            tr("Check ID"),
            tr("Fetched"),
            tr("Location"),
            tr("Source"),
            tr("Status"),
            tr("HTTP"),
            tr("Final URL"),
            tr("Error"),
        ]
    )
    cit_chk_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    cit_chk_table.itemSelectionChanged.connect(on_citations_check_selection_changed)
    cit_chk_row_meta: list[dict[str, object]] = []
    cit_chk_table.setColumnWidth(6, 320)
    cit_inspector_panel = make_inspector_panel()
    cit_inspector = getattr(cit_inspector_panel, "body", None)
    chk_split = table_with_inspector_split(cit_chk_table, cit_inspector_panel)
    cv.addWidget(chk_split, 1)
    tabs.addTab(chk_tab, tr("Check history"))

    lay.addWidget(tabs, 1)
    QTimer.singleShot(0, on_apply_citations_saved_view)
    assert cit_run_btn is not None
    assert cit_save_view_btn is not None
    assert cit_load_view_btn is not None

    refs = CitationsPageRefs(
        cit_run_btn=cit_run_btn,
        cit_progress=cit_progress,
        cit_save_view_btn=cit_save_view_btn,
        cit_load_view_btn=cit_load_view_btn,
        cit_status=cit_status,
        cit_src_table=cit_src_table,
        cit_loc_table=cit_loc_table,
        cit_chk_table=cit_chk_table,
        cit_chk_row_meta=cit_chk_row_meta,
        cit_inspector_panel=cit_inspector_panel,
        cit_inspector=cit_inspector,
        cit_tabs=tabs,
    )
    return root, refs
