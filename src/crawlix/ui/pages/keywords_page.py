"""Keywords/SERP page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from crawlix.ui.components import DataGridToolbar, InspectorPanel, MethodologyPanel, ProgressStrip, SectionCard
from crawlix.ui.controllers_toolbar import (
    keywords_toolbar_actions,
    rank_toolbar_actions,
    serp_toolbar_actions,
)
from crawlix.ui.page_sections import table_with_inspector_split


@dataclass
class KeywordsPageRefs:
    tabs: QTabWidget
    kw_site_type: QComboBox
    kw_country: QComboBox
    kw_brand: object
    kw_topic: object
    kw_template_list: QListWidget
    kw_phrase: object
    kw_table: QTableWidget
    serp_kw_combo: QComboBox
    serp_btn: object
    serp_save_view_btn: object
    serp_load_view_btn: object
    serp_progress: QProgressBar
    serp_status: QLabel
    serp_snapshots_table: QTableWidget
    serp_row_meta: list[dict[str, object]]
    serp_inspector_panel: InspectorPanel
    serp_inspector: object
    rank_kw_combo: QComboBox
    rank_fig: Figure
    rank_canvas: FigureCanvasQTAgg
    rank_chart_theme: str


def build_keywords_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    site_type_choices: list[tuple[str, str]],
    country_choices: list[tuple[str, str]],
    chart_theme: str,
    on_save_project_seo_context: Callable[[], None],
    on_generate_keyword_templates: Callable[[], None],
    on_add_checked_template_keywords: Callable[[], None],
    on_add_keyword: Callable[[], None],
    on_refresh_keywords_table: Callable[[], None],
    on_export_keywords_csv: Callable[[], None],
    on_keywords_context_menu: Callable[[object], None],
    on_refresh_serp_tab_lists: Callable[[], None],
    on_run_serp: Callable[[], None],
    on_export_serp_snapshots_csv: Callable[[], None],
    on_serp_context_menu: Callable[[object], None],
    on_save_serp_saved_view: Callable[[], None],
    on_apply_serp_saved_view: Callable[[], None],
    on_serp_selection_changed: Callable[[], None],
    on_rebuild_rank_chart: Callable[[], None],
    on_export_rank_history_csv: Callable[[], None],
    on_rank_context_menu: Callable[[object], None],
) -> tuple[QWidget, KeywordsPageRefs]:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)
    tabs = QTabWidget()
    tabs.setDocumentMode(True)

    kw_tab = QWidget()
    kvl = QVBoxLayout(kw_tab)
    kvl.setSpacing(10)
    tgt = SectionCard(tr("Project targeting (templates)"))
    tgf = QFormLayout()
    kw_site_type = QComboBox()
    for site_key, lab in site_type_choices:
        kw_site_type.addItem(lab, site_key)
    kw_country = QComboBox()
    for code, lab in country_choices:
        kw_country.addItem(lab, code)
    from PyQt6.QtWidgets import QLineEdit  # local to avoid large import churn

    kw_brand = QLineEdit()
    kw_topic = QLineEdit()
    kw_topic.setPlaceholderText(tr("e.g. web design, running shoes, CRM"))
    tgf.addRow(tr("Site type:"), kw_site_type)
    tgf.addRow(tr("Primary country:"), kw_country)
    tgf.addRow(tr("Brand / business name:"), kw_brand)
    tgf.addRow(tr("Primary topic or product:"), kw_topic)
    save_toolbar = DataGridToolbar(tr("Targeting actions"))
    save_toolbar.add_action(tr("Save targeting"), on_save_project_seo_context)
    save_toolbar.add_stretch()
    tgf.addRow("", save_toolbar)
    tgt.body_layout.addLayout(tgf)
    kvl.addWidget(tgt)

    tmpl = MethodologyPanel(
        tr("Template keyword ideas"),
        tr("Suggestions use site type, country, brand/topic context, and first location city when available."),
        points=[
            tr("Generate a shortlist, then tick rows you want to add as tracked keywords."),
            tr("Treat generated phrases as analyst prompts; review intent and geography before storing."),
        ],
    )
    tbtn = DataGridToolbar(tr("Suggestion actions"))
    tbtn.add_action(tr("Generate suggestions"), on_generate_keyword_templates)
    tbtn.add_action(tr("Add checked to project"), on_add_checked_template_keywords, variant="secondary")
    tbtn.add_stretch()
    tmpl.body_layout.addWidget(tbtn)
    kw_template_list = QListWidget()
    kw_template_list.setMinimumHeight(140)
    tmpl.body_layout.addWidget(kw_template_list)
    kvl.addWidget(tmpl)

    kw_box = SectionCard(tr("Keywords"))
    kw_inner = kw_box.body_layout
    kw_phrase = QLineEdit()
    kf = QFormLayout()
    kf.addRow(tr("New keyword:"), kw_phrase)
    kw_inner.addLayout(kf)
    kw_toolbar = DataGridToolbar(tr("Keyword actions"))
    kw_callbacks = {
        "keywords_add": on_add_keyword,
        "keywords_refresh": on_refresh_keywords_table,
        "keywords_export": on_export_keywords_csv,
    }
    for action in keywords_toolbar_actions():
        callback = kw_callbacks.get(action.action_id)
        if callback is not None:
            kw_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    kw_toolbar.add_stretch()
    kw_inner.addWidget(kw_toolbar)
    kvl.addWidget(kw_box)
    kw_table = QTableWidget(0, 5)
    kw_table.setHorizontalHeaderLabels([tr("ID"), tr("Phrase"), tr("Locale"), tr("Device"), tr("Archived")])
    kw_table.setColumnWidth(1, 360)
    kw_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    kw_table.customContextMenuRequested.connect(on_keywords_context_menu)
    kvl.addWidget(kw_table, 1)
    tabs.addTab(kw_tab, tr("Keywords"))

    serp_tab = QWidget()
    svl = QVBoxLayout(serp_tab)
    svl.setSpacing(10)
    serp_box = SectionCard(tr("SERP snapshot"))
    sg = serp_box.body_layout
    sk = QFormLayout()
    serp_kw_combo = QComboBox()
    sk.addRow(tr("Keyword:"), serp_kw_combo)
    sg.addLayout(sk)
    serp_toolbar = DataGridToolbar(tr("SERP actions"))
    serp_btn = None
    serp_save_view_btn = None
    serp_load_view_btn = None
    serp_callbacks = {
        "serp_refresh_lists": on_refresh_serp_tab_lists,
        "serp_run": on_run_serp,
        "serp_export": on_export_serp_snapshots_csv,
        "serp_save_view": on_save_serp_saved_view,
        "serp_load_view": on_apply_serp_saved_view,
    }
    for action in serp_toolbar_actions():
        callback = serp_callbacks.get(action.action_id)
        if callback is None:
            continue
        created = serp_toolbar.add_action(tr(action.label), callback, variant=action.variant)
        if action.action_id == "serp_run":
            serp_btn = created
        elif action.action_id == "serp_save_view":
            serp_save_view_btn = created
        elif action.action_id == "serp_load_view":
            serp_load_view_btn = created
    serp_toolbar.add_stretch()
    sg.addWidget(serp_toolbar)
    serp_progress_strip = ProgressStrip(tr("SERP progress"))
    sg.addWidget(serp_progress_strip)
    serp_progress = serp_progress_strip.progress_bar
    serp_status = serp_progress_strip.status_label
    sg.addWidget(
        MethodologyPanel(
            tr("Methodology"),
            tr("SERP snapshots are best-effort captures and may differ from live browser results."),
            points=[
                tr("Results can vary by datacenter IP, consent walls, localization, and anti-bot defenses."),
                tr("Parser quality can degrade on layout changes; use inspector/status for degraded evidence."),
            ],
        )
    )
    svl.addWidget(serp_box)
    serp_snapshots_table = QTableWidget(0, 5)
    serp_snapshots_table.setHorizontalHeaderLabels(
        [tr("Snapshot ID"), tr("Keyword"), tr("Fetched"), tr("Status"), tr("Organic rows")]
    )
    serp_snapshots_table.setColumnWidth(1, 220)
    serp_snapshots_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    serp_snapshots_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    serp_snapshots_table.customContextMenuRequested.connect(on_serp_context_menu)
    serp_snapshots_table.itemSelectionChanged.connect(on_serp_selection_changed)
    serp_row_meta: list[dict[str, object]] = []
    serp_inspector_panel = InspectorPanel(
        tr("Inspector"),
        tr("Select a snapshot to inspect ranking context and actions."),
        min_width=360,
    )
    serp_inspector = serp_inspector_panel.body
    serp_split = table_with_inspector_split(serp_snapshots_table, serp_inspector_panel)
    svl.addWidget(serp_split, 1)
    tabs.addTab(serp_tab, tr("SERP snapshots"))

    rank_tab = QWidget()
    rvl = QVBoxLayout(rank_tab)
    rvl.setSpacing(10)
    rank_box = SectionCard(tr("Rank history"))
    rg = rank_box.body_layout
    rank_kw_combo = QComboBox()
    rank_kw_combo.currentIndexChanged.connect(on_rebuild_rank_chart)
    rank_form = QFormLayout()
    rank_form.addRow(tr("Keyword:"), rank_kw_combo)
    rg.addLayout(rank_form)
    rank_toolbar = DataGridToolbar(tr("Rank actions"))
    rank_callbacks = {
        "rank_refresh": on_rebuild_rank_chart,
        "rank_export": on_export_rank_history_csv,
    }
    for action in rank_toolbar_actions():
        callback = rank_callbacks.get(action.action_id)
        if callback is not None:
            rank_toolbar.add_action(tr(action.label), callback, variant=action.variant)
    rank_toolbar.add_stretch()
    rg.addWidget(rank_toolbar)
    rank_fig = Figure(figsize=(6, 3.2))
    rank_canvas = FigureCanvasQTAgg(rank_fig)
    rank_canvas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    rank_canvas.customContextMenuRequested.connect(on_rank_context_menu)
    rg.addWidget(rank_canvas, 1)
    rvl.addWidget(rank_box, 1)
    tabs.addTab(rank_tab, tr("Rank history"))
    assert serp_btn is not None
    assert serp_save_view_btn is not None
    assert serp_load_view_btn is not None

    lay.addWidget(tabs, 1)
    refs = KeywordsPageRefs(
        tabs=tabs,
        kw_site_type=kw_site_type,
        kw_country=kw_country,
        kw_brand=kw_brand,
        kw_topic=kw_topic,
        kw_template_list=kw_template_list,
        kw_phrase=kw_phrase,
        kw_table=kw_table,
        serp_kw_combo=serp_kw_combo,
        serp_btn=serp_btn,
        serp_save_view_btn=serp_save_view_btn,
        serp_load_view_btn=serp_load_view_btn,
        serp_progress=serp_progress,
        serp_status=serp_status,
        serp_snapshots_table=serp_snapshots_table,
        serp_row_meta=serp_row_meta,
        serp_inspector_panel=serp_inspector_panel,
        serp_inspector=serp_inspector,
        rank_kw_combo=rank_kw_combo,
        rank_fig=rank_fig,
        rank_canvas=rank_canvas,
        rank_chart_theme=chart_theme,
    )
    return root, refs
