"""Crawl page builder extracted from MainWindow."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from crawlix.ui.components import DataGridToolbar, FilterBar, ProgressStrip, SectionCard
from crawlix.ui.controllers_filters import crawl_depth_filter_options, crawl_http_filter_options
from crawlix.ui.controllers_toolbar import crawl_table_toolbar_actions


def build_crawl_page(window: Any) -> QWidget:
    w = QWidget()
    l = QVBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 0)
    l.setSpacing(0)

    chrome = QWidget()
    cv = QVBoxLayout(chrome)
    cv.setContentsMargins(0, 0, 0, 0)
    cv.setSpacing(10)
    cv.addWidget(
        window._page_header(
            window.tr("Crawl"),
            window.tr("Map pages and links; depth and internal in/out counts reflect the crawl graph."),
        )
    )

    run_box = SectionCard(window.tr("Run crawl"))
    run_row = QHBoxLayout()
    run_row.setSpacing(10)
    run_row.addWidget(QLabel(window.tr("Seeds (comma-separated):")))
    window._crawl_seeds = QLineEdit("https://example.com/")
    run_row.addWidget(window._crawl_seeds, 1)
    run_row.addWidget(QLabel(window.tr("Max depth:")))
    window._crawl_depth = QSpinBox()
    window._crawl_depth.setRange(0, 5)
    window._crawl_depth.setValue(1)
    run_row.addWidget(window._crawl_depth)
    window._crawl_btn = QPushButton(window.tr("Start crawl"))
    window._crawl_btn.setDefault(True)
    window._crawl_btn.clicked.connect(window._start_crawl)
    run_row.addWidget(window._crawl_btn)
    run_box.body_layout.addLayout(run_row)
    cv.addWidget(run_box)

    window._crawl_progress_strip = ProgressStrip(window.tr("Crawl progress"))
    cv.addWidget(window._crawl_progress_strip)
    # Compatibility wiring so existing MainWindow orchestration remains unchanged.
    window._crawl_progress = window._crawl_progress_strip.progress_bar
    window._crawl_status = window._crawl_progress_strip.status_label

    crawl_toolbar = DataGridToolbar(window.tr("Table actions"))
    crawl_callbacks = {
        "crawl_refresh_table": window._refresh_crawl_pages_table,
        "crawl_export_pages_csv": window._export_pages_csv_dialog,
        "crawl_export_links_csv": window._export_links_csv_dialog,
    }
    for action in crawl_table_toolbar_actions():
        callback = crawl_callbacks.get(action.action_id)
        if callback is not None:
            crawl_toolbar.add_action(window.tr(action.label), callback, variant=action.variant)
    crawl_toolbar.add_stretch()
    cv.addWidget(crawl_toolbar)

    stats_row = QWidget()
    sh = QHBoxLayout(stats_row)
    sh.setSpacing(20)
    window._crawl_stat_values: dict[str, QLabel] = {}

    def _stat_pair(key: str, caption: str) -> None:
        col = QVBoxLayout()
        col.setSpacing(2)
        cap = QLabel(caption)
        cap.setStyleSheet("color: palette(mid);")
        val = QLabel("—")
        vf = QFont(val.font())
        vf.setPointSize(13)
        vf.setBold(True)
        val.setFont(vf)
        col.addWidget(cap)
        col.addWidget(val)
        sh.addLayout(col)
        window._crawl_stat_values[key] = val

    _stat_pair("pages", window.tr("Pages"))
    _stat_pair("unique_final", window.tr("Unique finals"))
    _stat_pair("dup_clusters", window.tr("Dup clusters"))
    _stat_pair("max_depth", window.tr("Max depth"))
    _stat_pair("avg_depth", window.tr("Avg depth"))
    _stat_pair("http_err", window.tr("HTTP errors"))
    sh.addStretch()
    cv.addWidget(stats_row)

    intel_card = SectionCard(window.tr("Crawl intelligence"))
    intel_tabs = QTabWidget()
    intel_tabs.setDocumentMode(True)
    window._crawl_link_insights = QTextEdit()
    window._crawl_link_insights.setReadOnly(True)
    window._crawl_link_insights.setPlaceholderText(window.tr("Internal link insights appear after refresh."))
    intel_tabs.addTab(window._crawl_link_insights, window.tr("Link intelligence"))
    window._crawl_diff_view = QTextEdit()
    window._crawl_diff_view.setReadOnly(True)
    window._crawl_diff_view.setPlaceholderText(window.tr("Crawl diff vs previous snapshot after two completed crawls."))
    intel_tabs.addTab(window._crawl_diff_view, window.tr("Crawl diff"))
    intel_tabs.setMaximumHeight(200)
    intel_card.body_layout.addWidget(intel_tabs)
    cv.addWidget(intel_card)

    window._crawl_filter_bar = FilterBar(
        window.tr("Table filters"),
        window.tr("Refine visible crawl rows by URL, status, depth, link counts, and duplicate grouping."),
    )
    window._crawl_filter_bar.set_summary(window.tr("Active filters: none"))
    fv = window._crawl_filter_bar.body_layout
    fv.setSpacing(8)
    filt1 = QHBoxLayout()
    filt1.addWidget(QLabel(window.tr("Search URL/title:")))
    window._crawl_search = QLineEdit()
    window._crawl_search.setPlaceholderText(window.tr("Substring match…"))
    window._crawl_search.textChanged.connect(window._refresh_crawl_pages_table)
    filt1.addWidget(window._crawl_search, 1)
    filt1.addWidget(QLabel(window.tr("HTTP:")))
    window._crawl_http_filter = QComboBox()
    for option in crawl_http_filter_options():
        window._crawl_http_filter.addItem(window.tr(option.label), option.value)
    window._crawl_http_filter.currentIndexChanged.connect(window._refresh_crawl_pages_table)
    filt1.addWidget(window._crawl_http_filter)
    filt1.addWidget(QLabel(window.tr("Depth:")))
    window._crawl_depth_filter = QComboBox()
    for option in crawl_depth_filter_options(max_depth=10):
        window._crawl_depth_filter.addItem(window.tr(option.label), option.value)
    window._crawl_depth_filter.currentIndexChanged.connect(window._refresh_crawl_pages_table)
    filt1.addWidget(window._crawl_depth_filter)
    fv.addLayout(filt1)
    filt2 = QHBoxLayout()
    window._crawl_dup_only = QCheckBox(window.tr("Duplicate final URLs only"))
    window._crawl_dup_only.toggled.connect(window._refresh_crawl_pages_table)
    filt2.addWidget(window._crawl_dup_only)
    filt2.addWidget(QLabel(window.tr("Max inbound (≤):")))
    window._crawl_max_inbound = QSpinBox()
    window._crawl_max_inbound.setRange(-1, 500)
    window._crawl_max_inbound.setValue(-1)
    window._crawl_max_inbound.setSpecialValueText(window.tr("Any"))
    window._crawl_max_inbound.valueChanged.connect(window._refresh_crawl_pages_table)
    filt2.addWidget(window._crawl_max_inbound)
    filt2.addWidget(QLabel(window.tr("Min outbound (≥):")))
    window._crawl_min_outbound = QSpinBox()
    window._crawl_min_outbound.setRange(-1, 500)
    window._crawl_min_outbound.setValue(-1)
    window._crawl_min_outbound.setSpecialValueText(window.tr("Any"))
    window._crawl_min_outbound.valueChanged.connect(window._refresh_crawl_pages_table)
    filt2.addWidget(window._crawl_min_outbound)
    window._crawl_save_view_btn = QPushButton(window.tr("Save view"))
    window._crawl_save_view_btn.clicked.connect(window._save_crawl_saved_view)
    filt2.addWidget(window._crawl_save_view_btn)
    window._crawl_apply_view_btn = QPushButton(window.tr("Load view"))
    window._crawl_apply_view_btn.clicked.connect(window._apply_crawl_saved_view)
    filt2.addWidget(window._crawl_apply_view_btn)
    window._crawl_audit_filtered_btn = QPushButton(window.tr("Audit visible rows"))
    window._crawl_audit_filtered_btn.clicked.connect(window._audit_crawl_filtered_visible)
    filt2.addWidget(window._crawl_audit_filtered_btn)
    filt2.addStretch()
    fv.addLayout(filt2)
    cv.addWidget(window._crawl_filter_bar)

    bottom = QWidget()
    bv = QVBoxLayout(bottom)
    bv.setContentsMargins(0, 0, 0, 0)
    bv.setSpacing(0)
    window._crawl_pages_table = QTableWidget(0, 9)
    window._crawl_pages_table.setHorizontalHeaderLabels(
        [
            window.tr("ID"),
            window.tr("URL"),
            window.tr("Title"),
            window.tr("HTTP"),
            window.tr("Depth"),
            window.tr("In"),
            window.tr("Out"),
            window.tr("Dup group"),
            window.tr("Last crawled"),
        ]
    )
    window._crawl_pages_table.setColumnWidth(1, 280)
    window._crawl_pages_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    window._crawl_pages_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    window._crawl_pages_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window._crawl_pages_table.customContextMenuRequested.connect(window._on_crawl_table_context_menu)
    window._crawl_pages_table.itemSelectionChanged.connect(window._on_crawl_selection_changed)
    window._crawl_row_meta = []
    window._crawl_display_page_ids = []
    crawl_split = QSplitter(Qt.Orientation.Horizontal)
    left_wrap = QWidget()
    ll = QVBoxLayout(left_wrap)
    ll.setContentsMargins(0, 0, 0, 0)
    ll.addWidget(window._crawl_pages_table)
    crawl_split.addWidget(left_wrap)
    detail = QWidget()
    detail.setMinimumWidth(400)
    dv = QVBoxLayout(detail)
    dv.setSpacing(6)
    det_title = QLabel(window.tr("Page details"))
    dtf = QFont(det_title.font())
    dtf.setBold(True)
    det_title.setFont(dtf)
    dv.addWidget(det_title)
    window._crawl_detail_orig = QLabel("—")
    window._crawl_detail_orig.setWordWrap(True)
    dv.addWidget(window._crawl_detail_orig)
    window._crawl_detail_final = QLabel("—")
    window._crawl_detail_final.setWordWrap(True)
    dv.addWidget(window._crawl_detail_final)
    window._crawl_detail_title = QLabel("—")
    window._crawl_detail_title.setWordWrap(True)
    dv.addWidget(window._crawl_detail_title)
    window._crawl_detail_http = QLabel("—")
    dv.addWidget(window._crawl_detail_http)
    window._crawl_detail_depth = QLabel("—")
    dv.addWidget(window._crawl_detail_depth)
    window._crawl_detail_inout = QLabel("—")
    window._crawl_detail_inout.setWordWrap(True)
    dv.addWidget(window._crawl_detail_inout)
    window._crawl_detail_last = QLabel("—")
    dv.addWidget(window._crawl_detail_last)
    window._crawl_detail_hints = QLabel("")
    window._crawl_detail_hints.setWordWrap(True)
    dv.addWidget(window._crawl_detail_hints)
    dv.addWidget(QLabel(window.tr("Path segments (project)")))
    window._crawl_detail_segments = QTextEdit()
    window._crawl_detail_segments.setReadOnly(True)
    window._crawl_detail_segments.setMaximumHeight(200)
    dv.addWidget(window._crawl_detail_segments)
    dv.addStretch()
    crawl_split.addWidget(detail)
    crawl_split.setStretchFactor(0, 2)
    crawl_split.setStretchFactor(1, 2)
    window._crawl_lr_split = crawl_split
    bv.addWidget(crawl_split, 1)

    window._crawl_body_split = QSplitter(Qt.Orientation.Vertical)
    window._crawl_body_split.setChildrenCollapsible(False)
    window._crawl_body_split.addWidget(chrome)
    window._crawl_body_split.addWidget(bottom)
    window._crawl_body_split.setStretchFactor(0, 0)
    window._crawl_body_split.setStretchFactor(1, 1)
    window._crawl_body_split.setSizes([320, 420])
    l.addWidget(window._crawl_body_split, 1)
    QTimer.singleShot(0, window._restore_crawl_body_split)
    QTimer.singleShot(0, window._apply_crawl_saved_view)
    return w
