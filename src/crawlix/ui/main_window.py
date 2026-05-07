"""Main application shell: sidebar, stacked pages, job dock, project switcher."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from PyQt6.QtCore import QSettings, QSize, Qt, QThreadPool, QTimer, QUrl
from PyQt6.QtGui import QAction, QCloseEvent, QDesktopServices, QIcon, QKeySequence, QPalette, QShowEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func, or_, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from crawlix.config import app_db_path, default_data_dir
from crawlix.db.bootstrap import upgrade_database
from crawlix.db.models import (
    CitationCheck,
    CitationSource,
    Job,
    Keyword,
    Location,
    Page,
    Project,
    Ranking,
    SerpResult,
)
from crawlix.db.session import make_engine
from crawlix.db.settings_store import get_value, set_value
from crawlix.services.analyzer.site_audit import (
    inbound_internal_counts,
    latest_completed_crawl_job_id,
    outbound_internal_counts,
)
from crawlix.services.citations.seed import seed_builtin_sources
from crawlix.services.crawler.crawl_overview import (
    effective_final_url,
    fetch_crawl_dashboard_stats,
    fetch_duplicate_final_sizes,
    format_internal_link_insights,
    normalization_hints,
    path_segment_lines_from_norms,
)
from crawlix.services.crawler.crawl_snapshots import diff_latest_two_snapshots, format_crawl_diff_for_ui
from crawlix.services.exporters import (
    export_builtin_citation_sources_csv,
    export_page_links_csv,
    export_pages_csv,
    export_seo_audits_csv,
    export_seo_audits_json,
)
from crawlix.services.integrations import list_integration_placeholders
from crawlix.services.keywords.templates import (
    COUNTRY_CHOICES,
    SITE_TYPE_CHOICES,
    context_from_merged,
    merge_context_from_project,
    suggest_phrases,
)
from crawlix.services.updater import github_releases
from crawlix.ui import onboarding
from crawlix.ui.components import (
    InspectorPanel,
    PageHeader,
    StatusPill,
)
from crawlix.ui.controllers_actions import DashboardActionRoute
from crawlix.ui.controllers_audit import (
    build_audit_row_meta,
    issue_count,
    query_audit_results_rows,
)
from crawlix.ui.controllers_citations import (
    build_citation_check_row_meta,
    clipped_error,
    clipped_url,
)
from crawlix.ui.controllers_context_menu import (
    ContextMenuActionDef,
    crawl_context_menu_actions,
    keywords_context_menu_actions,
    rank_context_menu_actions,
    serp_context_menu_actions,
)
from crawlix.ui.controllers_crawl import build_crawl_hints_text
from crawlix.ui.controllers_dashboard import (
    format_dashboard_summary_line,
    load_dashboard_action_hub,
    load_dashboard_summary,
)
from crawlix.ui.controllers_dashboard_routes import build_dashboard_post_nav_plan
from crawlix.ui.controllers_inspector import build_audit_inspector_text
from crawlix.ui.controllers_inspector_secondary import (
    build_citation_inspector_text,
    build_serp_inspector_text,
)
from crawlix.ui.controllers_jobs import build_job_rows, top_jobs_badge_text
from crawlix.ui.controllers_nav import NAV_GROUPS, NAV_SLUGS, localized_nav_labels
from crawlix.ui.controllers_progress_state import (
    citation_progress_state_from_summary,
    serp_progress_state_from_status,
)
from crawlix.ui.controllers_project import project_choices
from crawlix.ui.controllers_serp import build_serp_row_meta, serp_organic_count
from crawlix.ui.controllers_shortcuts import (
    SHORTCUT_SPECS,
    export_action_id_for_page,
    focus_target_id_for_page,
    no_action_message_key,
    primary_action_id_for_page,
    refresh_action_id_for_page,
    shortcuts_help_text,
)
from crawlix.ui.controllers_status import citation_status_variant, serp_status_variant
from crawlix.ui.dashboard_action_runner import decode_dashboard_list_item, resolve_route_from_decoded
from crawlix.ui.layout_helpers import wrap_page_content
from crawlix.ui.pages import (
    build_audit_page,
    build_citations_page,
    build_crawl_page,
    build_dashboard_page,
    build_integrations_page,
    build_keywords_page,
    build_local_page,
    build_reports_page,
    build_settings_page,
)
from crawlix.ui.project_dialog import NewProjectDialog
from crawlix.ui.saved_views import SavedView, SavedViewStore
from crawlix.ui.shell import JobCenter, NavRailColumn, PageHost, TopCommandStrip
from crawlix.ui.svg_icons import svg_icon_colored
from crawlix.ui.theme import apply_application_theme, sync_theme_to_qsettings
from crawlix.utils.slug import unique_project_slug
from crawlix.workers.audit_worker import AuditWorker
from crawlix.workers.citation_worker import CitationMatrixWorker
from crawlix.workers.crawl_worker import CrawlWorker
from crawlix.workers.job_bus import JobBus
from crawlix.workers.serp_worker import SerpWorker
from crawlix.workers.task_worker import SimpleTaskWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._ok = False
        self.setWindowTitle(self.tr("Crawlix"))
        self.resize(1200, 800)

        self._qs = QSettings("COWEBS", "Crawlix")
        self._saved_views = SavedViewStore(self._qs)
        self._data_dir = Path(
            self._qs.value("data_dir", str(default_data_dir()), str)  # type: ignore[arg-type]
        )
        self._engine = None
        self._Session = None
        self._current_project_id: int | None = None
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(4)
        self._bus = JobBus()
        self._bus.progress.connect(self._on_job_progress)
        self._bus.finished.connect(self._on_job_finished)
        self._bus.failed.connect(self._on_job_failed)
        self._bus.task_progress.connect(self._on_task_progress)
        self._bus.task_finished.connect(self._on_task_finished)
        self._bus.task_failed.connect(self._on_task_failed)

        self._crawl_active_job_id: int | None = None
        self._audit_active_job_id: int | None = None
        self._serp_active_job_id: int | None = None
        self._citation_active_job_id: int | None = None

        if not self._bootstrap_database():
            return

        self._build_ui()
        self._reload_styles()
        self._reload_projects_combo()
        self._refresh_job_table()
        self._ok = True

    def _session(self) -> Session:
        assert self._Session is not None
        return self._Session()

    def _bootstrap_database(self) -> bool:
        db_path = app_db_path(self._data_dir)
        if not db_path.exists():
            res = onboarding.run_first_run_wizard(self)
            if not res:
                return False
            self._data_dir = Path(res["data_dir"])
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._qs.setValue("data_dir", str(self._data_dir))
            db_path = app_db_path(self._data_dir)
            upgrade_database(db_path)
            self._engine = make_engine(db_path)
            self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)
            s = self._session()
            try:
                set_value(s, "master_password_hash", res["password_hash"])
                set_value(s, "politeness_preset", res["politeness_preset"])
                set_value(s, "automation_disclaimer", res["automation_disclaimer"])
                set_value(s, "wizard_completed", res["wizard_completed"])
                set_value(s, "data_dir", str(self._data_dir))
                set_value(s, "ollama_base_url", res.get("ollama_base_url") or "http://127.0.0.1:11434")
                set_value(s, "ollama_enabled", res.get("ollama_enabled", "0"))
                set_value(s, "ui_theme", "dark")
                s.commit()
                sync_theme_to_qsettings("dark")
                app = QApplication.instance()
                if app:
                    apply_application_theme(app, mode="dark")
                seed_builtin_sources(s)
                if (s.scalar(select(func.count()).select_from(Project)) or 0) == 0:
                    s.add(
                        Project(
                            name=self.tr("Demo project"),
                            slug="demo",
                            default_domain="example.com",
                        )
                    )
                    s.commit()
            finally:
                s.close()
        else:
            dlg = onboarding.UnlockDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return False
            upgrade_database(db_path)
            self._engine = make_engine(db_path)
            self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)
            s = self._session()
            try:
                h = get_value(s, "master_password_hash")
                if not h or not onboarding.verify_password(h, dlg.password()):
                    QMessageBox.critical(self, self.tr("Unlock failed"), self.tr("Invalid password."))
                    return False
                mode = get_value(s, "ui_theme", "dark") or "dark"
                sync_theme_to_qsettings(mode)
                app_inst = QApplication.instance()
                if app_inst:
                    apply_application_theme(app_inst, mode=mode)
                seed_builtin_sources(s)
            finally:
                s.close()
        return True

    def _build_ui(self) -> None:
        self._nav_collapsed = bool(self._qs.value("ui/nav_collapsed", False))
        self._job_dock_hidden = bool(self._qs.value("ui/job_dock_hidden", False))
        self._setup_menu()
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self._top_command_strip = TopCommandStrip()

        main_row = QWidget()
        m = QHBoxLayout(main_row)
        m.setContentsMargins(8, 8, 8, 0)

        self._nav = QListWidget()
        self._nav.setSpacing(2)
        self._nav.currentRowChanged.connect(self._on_nav)
        self._nav_slug_to_row: dict[str, int] = {}
        self._nav_row_to_page_index: dict[int, int] = {}
        nav_labels = localized_nav_labels(self.tr)
        for group_label, slugs in NAV_GROUPS:
            heading = QListWidgetItem(self.tr(group_label))
            heading.setFlags(Qt.ItemFlag.NoItemFlags)
            heading.setData(Qt.ItemDataRole.UserRole, self.tr(group_label))
            heading.setData(Qt.ItemDataRole.UserRole + 1, "")
            heading.setData(Qt.ItemDataRole.UserRole + 2, "heading")
            self._nav.addItem(heading)
            for slug in slugs:
                label = nav_labels[slug]
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, label)
                item.setData(Qt.ItemDataRole.UserRole + 1, slug)
                item.setToolTip(label)
                row = self._nav.count()
                self._nav.addItem(item)
                self._nav_slug_to_row[slug] = row
                self._nav_row_to_page_index[row] = NAV_SLUGS.index(slug)

        self._nav_toggle = QToolButton()
        self._nav_toggle.setAutoRaise(True)
        self._nav_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._nav_toggle.setIconSize(QSize(22, 22))
        self._nav_toggle.clicked.connect(self._toggle_nav_collapsed)
        self._refresh_nav_toggle_icon()

        self._nav_col = NavRailColumn(self._nav_toggle, self._nav)
        m.addWidget(self._nav_col)
        self._apply_nav_compact()

        self._stack = QStackedWidget()
        self._stack.addWidget(wrap_page_content(self._page_dashboard()))
        self._stack.addWidget(wrap_page_content(self._page_crawl()))
        self._stack.addWidget(wrap_page_content(self._page_audit()))
        self._stack.addWidget(wrap_page_content(self._page_keywords()))
        self._stack.addWidget(wrap_page_content(self._page_citations()))
        self._stack.addWidget(wrap_page_content(self._page_local()))
        self._stack.addWidget(wrap_page_content(self._page_integrations()))
        self._stack.addWidget(wrap_page_content(self._page_reports()))
        self._stack.addWidget(wrap_page_content(self._page_settings()))

        top = self._top_command_strip.layout()
        assert top is not None
        self._project_identity = QLabel(self.tr("No project"))
        self._project_identity.setProperty("role", "metadata")
        top.addWidget(self._project_identity)
        top.addWidget(QLabel(self.tr("Project:")))
        self._project_combo = QComboBox()
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        top.addWidget(self._project_combo, 1)
        self._global_search = QLineEdit()
        self._global_search.setPlaceholderText(self.tr("Global search (coming soon)"))
        self._global_search.setEnabled(False)
        top.addWidget(self._global_search, 2)
        self._top_jobs_badge = StatusPill(self.tr("Jobs: idle"), status="neutral")
        top.addWidget(self._top_jobs_badge)
        self._settings_shortcut_btn = QPushButton(self.tr("Settings"))
        self._settings_shortcut_btn.setProperty("variant", "secondary")
        self._settings_shortcut_btn.clicked.connect(lambda: self._set_current_nav_slug("settings"))
        top.addWidget(self._settings_shortcut_btn)

        self._page_host = PageHost(self._stack)
        m.addWidget(self._page_host, 1)

        self._dock_wrap = JobCenter()
        dw = self._dock_wrap.body_layout()
        dw.setContentsMargins(8, 4, 8, 8)
        dock_head = QWidget()
        dh = QHBoxLayout(dock_head)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.addWidget(QLabel(self.tr("Job dock")))
        dh.addStretch()
        self._dock_toggle_btn = QToolButton()
        self._dock_toggle_btn.setAutoRaise(True)
        self._dock_toggle_btn.clicked.connect(self._toggle_job_dock_hidden)
        dh.addWidget(self._dock_toggle_btn)
        self._cancel_job_btn = QPushButton(self.tr("Cancel selected job"))
        self._cancel_job_btn.clicked.connect(self._cancel_selected_job)
        dh.addWidget(self._cancel_job_btn)
        dw.addWidget(dock_head)
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        self._jobs_table = QTableWidget(0, 5)
        self._jobs_table.setHorizontalHeaderLabels(
            [self.tr("ID"), self.tr("Type"), self.tr("%"), self.tr("Status"), self.tr("Project")]
        )
        self._jobs_table.setMinimumHeight(96)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        tabs.addTab(self._jobs_table, self.tr("Jobs"))
        tabs.addTab(self._log, self.tr("Log"))
        dw.addWidget(tabs, 1)

        self._main_vertical_split = QSplitter(Qt.Orientation.Vertical)
        self._main_vertical_split.setChildrenCollapsible(True)
        self._main_vertical_split.setCollapsible(0, False)
        self._main_vertical_split.setCollapsible(1, True)
        self._main_vertical_split.addWidget(main_row)
        self._main_vertical_split.addWidget(self._dock_wrap)
        self._main_vertical_split.setStretchFactor(0, 1)
        self._main_vertical_split.setStretchFactor(1, 0)
        outer_layout.addWidget(self._top_command_strip)
        outer_layout.addWidget(self._main_vertical_split, 1)

        self.setCentralWidget(outer)
        self._set_current_nav_slug("dashboard")
        self._sync_job_dock_toggle_ui()

        sb = QStatusBar()
        preset = "conservative"
        s = self._session()
        try:
            preset = get_value(s, "politeness_preset", "conservative") or "conservative"
        finally:
            s.close()
        self._status_preset = QLabel(self.tr("Politeness: %1").replace("%1", preset))
        sb.addPermanentWidget(self._status_preset)
        self.setStatusBar(sb)

    def _refresh_nav_toggle_icon(self) -> None:
        btn = getattr(self, "_nav_toggle", None)
        if not btn:
            return
        c = self.palette().color(QPalette.ColorRole.ButtonText)
        btn.setIcon(svg_icon_colored("menu", 22, c))

    def _refresh_nav_list_icons(self) -> None:
        nav = getattr(self, "_nav", None)
        if not nav:
            return
        c = self.palette().color(QPalette.ColorRole.WindowText)
        px = max(18, nav.iconSize().width())
        for i in range(nav.count()):
            it = nav.item(i)
            slug = it.data(Qt.ItemDataRole.UserRole + 1)
            if isinstance(slug, str) and slug:
                it.setIcon(svg_icon_colored(slug, px, c))
            else:
                it.setIcon(QIcon())

    def _toggle_nav_collapsed(self) -> None:
        self._nav_collapsed = not self._nav_collapsed
        self._qs.setValue("ui/nav_collapsed", self._nav_collapsed)
        self._apply_nav_compact()

    def _apply_nav_compact(self) -> None:
        collapsed = self._nav_collapsed
        self._nav.setIconSize(QSize(26, 26) if collapsed else QSize(22, 22))
        self._refresh_nav_list_icons()
        side = 58 if collapsed else 212
        self._nav_col.setFixedWidth(side)
        hint_h = 46 if collapsed else 34
        row_w = max(40, side - 10)
        for i in range(self._nav.count()):
            it = self._nav.item(i)
            raw = it.data(Qt.ItemDataRole.UserRole)
            lab = str(raw) if raw is not None else it.text()
            is_heading = it.data(Qt.ItemDataRole.UserRole + 2) == "heading"
            if is_heading:
                it.setText("" if collapsed else lab.upper())
                it.setToolTip("")
                it.setSizeHint(QSize(row_w, 14 if collapsed else 22))
                continue
            it.setText("" if collapsed else lab)
            it.setToolTip(lab)
            it.setSizeHint(QSize(row_w, hint_h) if collapsed else QSize(200, hint_h))
        self._refresh_nav_toggle_icon()
        self._nav_toggle.setToolTip(
            self.tr("Expand sidebar (show labels)") if collapsed else self.tr("Collapse sidebar to icons only")
        )

    def _sync_job_dock_toggle_ui(self) -> None:
        hidden = self._job_dock_hidden
        self._dock_toggle_btn.setText(self.tr("Show") if hidden else self.tr("Hide"))
        self._dock_toggle_btn.setToolTip(
            self.tr("Show job dock") if hidden else self.tr("Hide job dock for more vertical space")
        )
        act = getattr(self, "_act_job_dock", None)
        if act:
            act.blockSignals(True)
            act.setChecked(not hidden)
            act.blockSignals(False)

    def _on_job_dock_menu_toggled(self, checked: bool) -> None:
        self._set_job_dock_hidden(not checked)

    def _set_job_dock_hidden(self, hidden: bool) -> None:
        self._job_dock_hidden = bool(hidden)
        self._qs.setValue("ui/job_dock_hidden", self._job_dock_hidden)
        sp = getattr(self, "_main_vertical_split", None)
        dock = getattr(self, "_dock_wrap", None)
        if not sp or not dock:
            self._sync_job_dock_toggle_ui()
            return
        h = max(120, sp.height())
        if self._job_dock_hidden:
            sizes = sp.sizes()
            if len(sizes) >= 2 and sizes[1] > 48:
                self._qs.setValue("ui/job_dock_last_height", sizes[1])
            sp.setSizes([max(200, h - 1), 0])
            dock.setVisible(False)
        else:
            dock.setVisible(True)
            dh = int(self._qs.value("ui/job_dock_last_height", 200))
            dh = int(min(max(dh, 120), h * 0.5))
            sp.setSizes([max(160, h - dh), dh])
        self._sync_job_dock_toggle_ui()

    def _toggle_job_dock_hidden(self) -> None:
        self._set_job_dock_hidden(not self._job_dock_hidden)

    def _restore_main_vertical_split(self) -> None:
        sp = getattr(self, "_main_vertical_split", None)
        dock = getattr(self, "_dock_wrap", None)
        if not sp or not dock:
            return
        h = sp.height()
        if h < 80:
            return
        if getattr(self, "_job_dock_hidden", False):
            dock.setVisible(False)
            sp.setSizes([max(200, h - 1), 0])
            self._sync_job_dock_toggle_ui()
            return
        dock.setVisible(True)
        raw = self._qs.value("ui/main_vertical_split", "")
        parts: list[int] = []
        if raw:
            for x in str(raw).split(","):
                x = x.strip()
                if x.isdigit():
                    parts.append(int(x))
        if len(parts) == 2 and parts[0] > 120 and parts[1] > 48:
            sp.setSizes(parts)
            return
        dock_h = min(220, max(112, int(h * 0.22)))
        sp.setSizes([max(200, h - dock_h), dock_h])

    def _persist_main_vertical_split(self) -> None:
        if getattr(self, "_job_dock_hidden", False):
            return
        sp = getattr(self, "_main_vertical_split", None)
        if not sp:
            return
        sizes = sp.sizes()
        if len(sizes) >= 2:
            self._qs.setValue("ui/main_vertical_split", f"{sizes[0]},{sizes[1]}")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not getattr(self, "_did_initial_split_restore", False) and getattr(
            self, "_main_vertical_split", None
        ):
            self._did_initial_split_restore = True
            QTimer.singleShot(100, self._restore_main_vertical_split)
        if not getattr(self, "_did_crawl_lr_restore", False) and getattr(self, "_crawl_lr_split", None):
            self._did_crawl_lr_restore = True
            QTimer.singleShot(140, self._restore_crawl_lr_split)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._persist_main_vertical_split()
        cbs = getattr(self, "_crawl_body_split", None)
        if cbs:
            csz = cbs.sizes()
            if len(csz) >= 2:
                self._qs.setValue("ui/crawl_body_split", f"{csz[0]},{csz[1]}")
        lr = getattr(self, "_crawl_lr_split", None)
        if lr:
            lsz = lr.sizes()
            if len(lsz) >= 2 and lsz[0] > 120 and lsz[1] > 120:
                self._qs.setValue("ui/crawl_lr_split", f"{lsz[0]},{lsz[1]}")
        super().closeEvent(event)

    def _setup_menu(self) -> None:
        m_file = self.menuBar().addMenu(self.tr("&File"))
        act_new = QAction(self.tr("New project…"), self)
        act_new.triggered.connect(self._new_project)
        m_file.addAction(act_new)
        act_folder = QAction(self.tr("Open data folder…"), self)
        act_folder.triggered.connect(self._open_data_folder)
        m_file.addAction(act_folder)
        m_file.addSeparator()
        act_quit = QAction(self.tr("E&xit"), self)
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)
        m_view = self.menuBar().addMenu(self.tr("&View"))
        self._act_job_dock = QAction(self.tr("Job dock"), self)
        self._act_job_dock.setCheckable(True)
        self._act_job_dock.setChecked(not self._job_dock_hidden)
        self._act_job_dock.toggled.connect(self._on_job_dock_menu_toggled)
        m_view.addAction(self._act_job_dock)
        m_help = self.menuBar().addMenu(self.tr("&Help"))
        act_shortcuts = QAction(self.tr("Keyboard &shortcuts"), self)
        act_shortcuts.setShortcut(QKeySequence(SHORTCUT_SPECS["help_shortcuts"].key))
        act_shortcuts.triggered.connect(self._show_shortcuts_help)
        m_help.addAction(act_shortcuts)
        act_updates = QAction(self.tr("&Check for updates…"), self)
        act_updates.triggered.connect(self._check_updates)
        m_help.addAction(act_updates)
        self._register_keyboard_shortcuts()

    def _register_keyboard_shortcuts(self) -> None:
        shortcut_callbacks: dict[str, callable] = {
            "focus_search": self._focus_current_page_search,
            "refresh_page": self._refresh_current_page,
            "toggle_jobs": self._toggle_job_dock_hidden,
            "focus_project": self._focus_project_switcher,
            "export_view": self._export_current_page,
            "run_primary": self._run_primary_current_page_action,
            "open_settings": lambda: self._set_current_nav_slug("settings"),
        }
        self._shortcut_actions: list[QAction] = []
        for key, callback in shortcut_callbacks.items():
            action = QAction(self)
            action.setShortcut(QKeySequence(SHORTCUT_SPECS[key].key))
            action.triggered.connect(callback)
            self.addAction(action)
            self._shortcut_actions.append(action)

    def _show_shortcuts_help(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Keyboard shortcuts"))
        dialog.resize(520, 360)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(shortcuts_help_text(self.tr))
        layout.addWidget(text)
        close_btn = QPushButton(self.tr("Close"))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def _focus_project_switcher(self) -> None:
        self._project_combo.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self._project_combo.showPopup()

    def _focus_current_page_search(self) -> None:
        slug = NAV_SLUGS[self._stack.currentIndex()]
        kw_idx = (
            int(self._kw_tabs.currentIndex()) if slug == "keywords" and getattr(self, "_kw_tabs", None) else None
        )
        cit_idx = (
            int(self._cit_tabs.currentIndex()) if slug == "citations" and getattr(self, "_cit_tabs", None) else None
        )
        focus_id = focus_target_id_for_page(slug, keywords_tab_index=kw_idx, citations_tab_index=cit_idx)
        focus_targets = self._shortcut_focus_targets()
        widget = focus_targets.get(focus_id)
        if widget is not None:
            widget.setFocus(Qt.FocusReason.ShortcutFocusReason)
            return
        self._project_combo.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _shortcut_focus_targets(self) -> dict[str, QWidget | None]:
        return {
            "keywords_input": getattr(self, "_kw_phrase", None),
            "serp_keyword_combo": getattr(self, "_serp_kw_combo", None),
            "rank_keyword_combo": getattr(self, "_rank_kw_combo", None),
            "citations_sources_table": getattr(self, "_cit_src_table", None),
            "citations_locations_table": getattr(self, "_cit_loc_table", None),
            "citations_checks_table": getattr(self, "_cit_chk_table", None),
            "crawl_search": getattr(self, "_crawl_search", None),
            "audit_search": getattr(self, "_audit_search", None),
            "dashboard_actions": getattr(self, "_dash_actions", None),
            "project_switcher": self._project_combo,
        }

    def _refresh_current_page(self) -> None:
        slug = NAV_SLUGS[self._stack.currentIndex()]
        action_id = refresh_action_id_for_page(slug)
        refresher = self._shortcut_refresh_actions().get(action_id or "")
        if refresher is None:
            self._show_shortcut_no_action_message("refresh", slug)
            return
        refresher()

    def _shortcut_refresh_actions(self) -> dict[str, Callable[[], None]]:
        return {
            "dashboard_refresh": self._refresh_dashboard_stats,
            "crawl_refresh_table": self._refresh_crawl_pages_table,
            "audit_refresh_results": self._refresh_audit_results_table,
            "keywords_refresh_lists": self._refresh_serp_tab_lists,
            "citations_refresh_all": self._refresh_citations_page,
        }

    def _export_current_page(self) -> None:
        slug = NAV_SLUGS[self._stack.currentIndex()]
        kw_idx = (
            int(self._kw_tabs.currentIndex()) if slug == "keywords" and getattr(self, "_kw_tabs", None) else None
        )
        cit_idx = (
            int(self._cit_tabs.currentIndex()) if slug == "citations" and getattr(self, "_cit_tabs", None) else None
        )
        action_id = export_action_id_for_page(slug, keywords_tab_index=kw_idx, citations_tab_index=cit_idx)
        exporters = self._shortcut_export_actions()
        exporter = exporters.get(action_id or "")
        if exporter is None:
            self._show_shortcut_no_action_message("export", slug)
            return
        exporter()

    def _shortcut_export_actions(self) -> dict[str, Callable[[], None]]:
        return {
            "keywords_export_csv": self._export_keywords_csv_dialog,
            "serp_export_csv": self._export_serp_snapshots_csv_dialog,
            "rank_export_csv": self._export_rank_history_csv_dialog,
            "citations_export_sources_csv": self._export_builtin_citations_csv,
            "crawl_export_pages_csv": self._export_pages_csv_dialog,
            "audit_export_csv": self._export_audits_csv_dialog,
            "reports_export_markdown": self._export_md,
        }

    def _run_primary_current_page_action(self) -> None:
        slug = NAV_SLUGS[self._stack.currentIndex()]
        kw_idx = (
            int(self._kw_tabs.currentIndex()) if slug == "keywords" and getattr(self, "_kw_tabs", None) else None
        )
        cit_idx = (
            int(self._cit_tabs.currentIndex()) if slug == "citations" and getattr(self, "_cit_tabs", None) else None
        )
        action_id = primary_action_id_for_page(slug, keywords_tab_index=kw_idx, citations_tab_index=cit_idx)
        actions = self._shortcut_primary_actions()
        action = actions.get(action_id or "")
        if action is None:
            self._show_shortcut_no_action_message("primary", slug)
            return
        action()

    def _show_shortcut_no_action_message(self, action_kind: str, slug: str) -> None:
        key = no_action_message_key(action_kind, slug)
        messages = {
            "no_export_keywords_tab": self.tr("No export action on this Keywords tab"),
            "no_export_citations_tab": self.tr("No export action on this Citations tab"),
            "no_export_page": self.tr("No export action on this page"),
            "no_refresh_page": self.tr("No refresh action on this page"),
            "no_primary_page": self.tr("No primary action on this page"),
            "no_action_generic": self.tr("No action available"),
        }
        self.statusBar().showMessage(messages.get(key, messages["no_action_generic"]), 1600)

    def _shortcut_primary_actions(self) -> dict[str, Callable[[], None]]:
        return {
            "keywords_add": self._add_keyword,
            "serp_run": self._run_serp,
            "rank_refresh": self._rebuild_rank_chart,
            "citations_refresh_sources": self._refresh_citations_builtin_table,
            "citations_refresh_locations": self._refresh_citations_locations_table,
            "citations_refresh_checks": self._refresh_citations_checks_table,
            "dashboard_run_selected": self._run_selected_dashboard_action,
            "crawl_start": self._start_crawl,
            "audit_start": self._start_audit,
        }

    def _reload_styles(self) -> None:
        s = self._session()
        try:
            mode = get_value(s, "ui_theme", "dark") or "dark"
        finally:
            s.close()
        app = QApplication.instance()
        if app:
            apply_application_theme(app, mode=mode)
            sync_theme_to_qsettings(mode)
        self._refresh_nav_list_icons()
        self._refresh_nav_toggle_icon()

    def _on_nav(self, row: int) -> None:
        if row < 0:
            return
        page_idx = self._nav_row_to_page_index.get(row)
        if page_idx is None:
            return
        self._stack.setCurrentIndex(page_idx)

    def _set_current_nav_slug(self, slug: str) -> None:
        row = self._nav_slug_to_row.get(slug)
        if row is not None:
            self._nav.setCurrentRow(row)

    def _on_project_changed(self) -> None:
        pid = self._project_combo.currentData()
        self._current_project_id = int(pid) if pid is not None else None
        self._project_identity.setText(
            self.tr("Current project: %1").replace("%1", self._project_combo.currentText() or self.tr("None"))
        )
        self._refresh_all_project_views()

    def _reload_projects_combo(self) -> None:
        self._project_combo.clear()
        s = self._session()
        try:
            for pid, name in project_choices(s):
                self._project_combo.addItem(name, pid)
        finally:
            s.close()
        if self._project_combo.count():
            self._current_project_id = int(self._project_combo.itemData(0))
            self._project_identity.setText(
                self.tr("Current project: %1").replace("%1", self._project_combo.itemText(0))
            )
        else:
            self._project_identity.setText(self.tr("Current project: none"))
        self._refresh_all_project_views()

    def _refresh_all_project_views(self) -> None:
        self._refresh_dashboard_stats()
        self._refresh_crawl_pages_table()
        self._refresh_audit_results_table()
        self._refresh_keywords_table()
        self._refresh_serp_tab_lists()
        self._refresh_citations_page()

    def _page_header(self, title: str, subtitle: str | None = None) -> QWidget:
        """Plain-text page title (avoid HTML auto-rich-text that breaks contrast)."""
        return PageHeader(title, subtitle)

    def _page_dashboard(self) -> QWidget:
        page, refs = build_dashboard_page(
            header=self._page_header(self.tr("Dashboard")),
            tr=self.tr,
            on_refresh_summary=self._refresh_dashboard_stats,
            on_run_selected_action=self._run_selected_dashboard_action,
        )
        self._dash_stats = refs.dash_stats
        self._dash_actions_panel = refs.dash_actions_panel
        self._dash_actions = refs.dash_actions
        self._dash_action_btn = refs.dash_action_btn
        self._dash_needs_panel = refs.dash_needs_panel
        self._dash_needs_attention = refs.dash_needs_attention
        self._dash_recent_panel = refs.dash_recent_panel
        self._dash_recent_outcomes = refs.dash_recent_outcomes
        return page

    def _run_selected_dashboard_action(self) -> None:
        row = self._dash_actions.currentRow() if getattr(self, "_dash_actions", None) else -1
        if row < 0:
            return
        decoded = decode_dashboard_list_item(self._dash_actions.item(row))
        if decoded is None:
            return
        route = resolve_route_from_decoded(decoded)
        if route.show_jobs:
            self._set_job_dock_hidden(False)
            return
        if route.nav_row is not None:
            if 0 <= route.nav_row < len(NAV_SLUGS):
                self._set_current_nav_slug(NAV_SLUGS[route.nav_row])
        sf = decoded.suggested_filter
        QTimer.singleShot(
            0,
            lambda r=route, f=sf: self._dashboard_post_nav_actions(r, f),
        )

    def _dashboard_post_nav_actions(
        self,
        route: DashboardActionRoute,
        suggested_filter: dict[str, object] | None,
    ) -> None:
        plan = build_dashboard_post_nav_plan(route, suggested_filter)
        if plan.focus_audit_page_id is not None:
            self._focus_audit_row_for_page_id(plan.focus_audit_page_id)
            return
        if plan.focus_crawl_seeds:
            if plan.apply_saved_crawl_view:
                self._apply_crawl_saved_view()
            elif plan.crawl_filter:
                self._apply_crawl_filter_partial(plan.crawl_filter)
            if getattr(self, "_crawl_seeds", None):
                self._crawl_seeds.setFocus(Qt.FocusReason.OtherFocusReason)
            return

    def _apply_crawl_filter_partial(self, data: dict[str, object]) -> None:
        if not getattr(self, "_crawl_search", None):
            return
        widgets = (
            self._crawl_search,
            self._crawl_http_filter,
            self._crawl_depth_filter,
            self._crawl_max_inbound,
            self._crawl_min_outbound,
            self._crawl_dup_only,
        )
        for w in widgets:
            w.blockSignals(True)
        try:
            if "search" in data:
                self._crawl_search.setText(str(data.get("search") or ""))
            if "http_filter" in data:
                idx = self._crawl_http_filter.findData(data.get("http_filter"))
                if idx >= 0:
                    self._crawl_http_filter.setCurrentIndex(idx)
            if "depth_filter" in data:
                idx2 = self._crawl_depth_filter.findData(data.get("depth_filter"))
                if idx2 >= 0:
                    self._crawl_depth_filter.setCurrentIndex(idx2)
            if "max_inbound" in data:
                self._crawl_max_inbound.setValue(int(data["max_inbound"]))
            if "min_outbound" in data:
                self._crawl_min_outbound.setValue(int(data["min_outbound"]))
            if "dup_only" in data:
                self._crawl_dup_only.setChecked(bool(data["dup_only"]))
        finally:
            for w in widgets:
                w.blockSignals(False)
        self._refresh_crawl_pages_table()

    def _select_audit_row_for_page_id(self, page_id: int) -> bool:
        tb = getattr(self, "_audit_results_table", None)
        if tb is None:
            return False
        for r in range(tb.rowCount()):
            it = tb.item(r, 1)
            if it is not None and it.text() == str(page_id):
                tb.selectRow(r)
                cell = tb.item(r, 0)
                if cell is not None:
                    tb.scrollToItem(cell, QAbstractItemView.ScrollHint.PositionAtCenter)
                self._on_audit_selection_changed()
                return True
        return False

    def _focus_audit_row_for_page_id(self, page_id: int) -> None:
        if self._select_audit_row_for_page_id(page_id):
            return
        self._refresh_audit_results_table(prioritize_page_id=page_id)
        self._select_audit_row_for_page_id(page_id)

    def _page_crawl(self) -> QWidget:
        return build_crawl_page(self)

    def _restore_crawl_body_split(self) -> None:
        sp = getattr(self, "_crawl_body_split", None)
        if not sp:
            return
        h = sp.height()
        if h < 100:
            return
        raw = self._qs.value("ui/crawl_body_split", "")
        parts: list[int] = []
        if raw:
            for x in str(raw).split(","):
                x = x.strip()
                if x.lstrip("-").isdigit():
                    parts.append(int(x))
        if len(parts) == 2 and parts[0] > 80 and parts[1] > 80:
            sp.setSizes(parts)
            return
        top_h = min(380, max(220, int(h * 0.38)))
        sp.setSizes([top_h, max(160, h - top_h)])

    def _restore_crawl_lr_split(self) -> None:
        sp = getattr(self, "_crawl_lr_split", None)
        if not sp:
            return
        w = sp.width()
        if w < 400:
            return
        raw = self._qs.value("ui/crawl_lr_split", "")
        parts: list[int] = []
        if raw:
            for x in str(raw).split(","):
                x = x.strip()
                if x.isdigit():
                    parts.append(int(x))
        if len(parts) == 2 and parts[0] > 200 and parts[1] >= 300:
            sp.setSizes(parts)
            return
        right = max(400, int(w * 0.46))
        left = max(220, w - right)
        sp.setSizes([left, right])

    def _save_crawl_saved_view(self) -> None:
        if not getattr(self, "_crawl_search", None):
            return
        sv = SavedView(
            search=self._crawl_search.text().strip(),
            http_filter=self._crawl_http_filter.currentData(),
            depth_filter=self._crawl_depth_filter.currentData(),
            max_inbound=int(self._crawl_max_inbound.value()),
            min_outbound=int(self._crawl_min_outbound.value()),
            dup_only=bool(self._crawl_dup_only.isChecked()),
        )
        self._saved_views.save("crawl", sv)
        self.statusBar().showMessage(self.tr("Saved crawl view"), 1800)

    def _apply_crawl_saved_view(self) -> None:
        if not getattr(self, "_crawl_search", None):
            return
        sv = self._saved_views.load("crawl")
        self._crawl_search.setText(sv.search)
        idx = self._crawl_http_filter.findData(sv.http_filter)
        if idx >= 0:
            self._crawl_http_filter.setCurrentIndex(idx)
        idx2 = self._crawl_depth_filter.findData(sv.depth_filter)
        if idx2 >= 0:
            self._crawl_depth_filter.setCurrentIndex(idx2)
        self._crawl_max_inbound.setValue(sv.max_inbound)
        self._crawl_min_outbound.setValue(sv.min_outbound)
        self._crawl_dup_only.setChecked(sv.dup_only)
        self._refresh_crawl_pages_table()

    def _start_crawl(self) -> None:
        if not self._current_project_id:
            QMessageBox.warning(self, self.tr("Project"), self.tr("Select a project first."))
            return
        seeds = [s.strip() for s in self._crawl_seeds.text().split(",") if s.strip()]
        if not seeds:
            return
        s = self._session()
        try:
            preset = get_value(s, "politeness_preset", "conservative") or "conservative"
            job = Job(
                project_id=self._current_project_id,
                type="crawl",
                status="queued",
                progress_pct=0,
                payload_json={
                    "seed_urls": seeds,
                    "max_depth": int(self._crawl_depth.value()),
                    "respect_robots": True,
                    "politeness_preset": preset,
                },
            )
            s.add(job)
            s.commit()
            jid = job.id
        finally:
            s.close()
        self._append_log(f"Queued crawl job {jid}")
        self._crawl_active_job_id = jid
        self._crawl_btn.setEnabled(False)
        self._crawl_progress.setRange(0, 100)
        self._crawl_progress.setValue(0)
        self._crawl_progress.setVisible(True)
        self._set_progress_status(self._crawl_status, self.tr("Queued…"), state="running")
        w = CrawlWorker(jid, self._engine, self._bus, job_key=f"crawl-{jid}")
        self._pool.start(w)
        self._refresh_job_table()

    def _page_audit(self) -> QWidget:
        page, refs = build_audit_page(
            header=self._page_header(
                self.tr("Audit"),
                self.tr("Scores, issues, crawl depth, and internal in/out link counts from the last crawl graph."),
            ),
            tr=self.tr,
            on_start_audit=self._start_audit,
            on_refresh_results=self._refresh_audit_results_table,
            on_export_audits_csv=self._export_audits_csv_dialog,
            on_export_audits_json=self._export_audits_json_dialog,
            on_selection_changed=self._on_audit_selection_changed,
        )
        self._audit_btn = refs.audit_btn
        self._audit_progress = refs.audit_progress
        self._audit_status = refs.audit_status
        self._audit_filter_bar = refs.audit_filter_bar
        self._audit_search = refs.audit_search
        self._audit_max_score = refs.audit_max_score
        self._audit_min_issues = refs.audit_min_issues
        self._audit_results_table = refs.audit_results_table
        self._audit_row_meta = refs.audit_row_meta
        self._audit_inspector_panel = refs.audit_inspector_panel
        self._audit_inspector = refs.audit_inspector
        return page

    def _start_audit(self) -> None:
        if not self._current_project_id:
            return
        s = self._session()
        try:
            pages = (
                s.execute(
                    select(Page.id)
                    .where(Page.project_id == self._current_project_id)
                    .order_by(Page.id.asc())
                    .limit(500)
                )
                .scalars()
                .all()
            )
            if not pages:
                QMessageBox.information(self, self.tr("Audit"), self.tr("No pages yet — run a crawl."))
                return
        finally:
            s.close()
        self._start_audit_pages(list(pages))

    def _start_audit_pages(self, page_ids: list[int]) -> None:
        if not self._current_project_id:
            QMessageBox.warning(self, self.tr("Project"), self.tr("Select a project first."))
            return
        ids = sorted({int(x) for x in page_ids if x})
        if not ids:
            QMessageBox.information(self, self.tr("Audit"), self.tr("No pages selected."))
            return
        if len(ids) > 500:
            ids = ids[:500]
            QMessageBox.information(
                self,
                self.tr("Audit"),
                self.tr("Only the first 500 page IDs will be audited."),
            )
        s = self._session()
        try:
            job = Job(
                project_id=self._current_project_id,
                type="audit",
                status="queued",
                progress_pct=0,
                payload_json={"page_ids": ids},
            )
            s.add(job)
            s.commit()
            jid = job.id
        finally:
            s.close()
        self._audit_active_job_id = jid
        self._audit_btn.setEnabled(False)
        self._audit_progress.setRange(0, 100)
        self._audit_progress.setValue(0)
        self._audit_progress.setVisible(True)
        self._set_progress_status(self._audit_status, self.tr("Queued…"), state="running")
        self._pool.start(AuditWorker(jid, self._engine, self._bus))
        self._refresh_job_table()

    def _page_keywords(self) -> QWidget:
        s_theme = self._session()
        try:
            chart_theme = get_value(s_theme, "ui_theme", "dark") or "dark"
        finally:
            s_theme.close()
        page, refs = build_keywords_page(
            header=self._page_header(self.tr("Keywords / SERP"), self.tr("Keywords, SERP snapshots, rank history.")),
            tr=self.tr,
            site_type_choices=list(SITE_TYPE_CHOICES),
            country_choices=list(COUNTRY_CHOICES),
            chart_theme=chart_theme,
            on_save_project_seo_context=self._save_project_seo_context,
            on_generate_keyword_templates=self._generate_keyword_templates,
            on_add_checked_template_keywords=self._add_checked_template_keywords,
            on_add_keyword=self._add_keyword,
            on_refresh_keywords_table=self._refresh_keywords_table,
            on_export_keywords_csv=self._export_keywords_csv_dialog,
            on_keywords_context_menu=self._on_keywords_table_context_menu,
            on_refresh_serp_tab_lists=self._refresh_serp_tab_lists,
            on_run_serp=self._run_serp,
            on_export_serp_snapshots_csv=self._export_serp_snapshots_csv_dialog,
            on_serp_context_menu=self._on_serp_table_context_menu,
            on_save_serp_saved_view=self._save_serp_saved_view,
            on_apply_serp_saved_view=self._apply_serp_saved_view,
            on_serp_selection_changed=self._on_serp_selection_changed,
            on_rebuild_rank_chart=self._rebuild_rank_chart,
            on_export_rank_history_csv=self._export_rank_history_csv_dialog,
            on_rank_context_menu=self._on_rank_chart_context_menu,
        )
        self._kw_tabs = refs.tabs
        self._kw_site_type = refs.kw_site_type
        self._kw_country = refs.kw_country
        self._kw_brand = refs.kw_brand
        self._kw_topic = refs.kw_topic
        self._kw_template_list = refs.kw_template_list
        self._kw_phrase = refs.kw_phrase
        self._kw_table = refs.kw_table
        self._serp_kw_combo = refs.serp_kw_combo
        self._serp_btn = refs.serp_btn
        self._serp_save_view_btn = refs.serp_save_view_btn
        self._serp_load_view_btn = refs.serp_load_view_btn
        self._serp_progress = refs.serp_progress
        self._serp_status = refs.serp_status
        self._serp_snapshots_table = refs.serp_snapshots_table
        self._serp_row_meta = refs.serp_row_meta
        self._serp_inspector_panel = refs.serp_inspector_panel
        self._serp_inspector = refs.serp_inspector
        self._rank_kw_combo = refs.rank_kw_combo
        self._rank_fig = refs.rank_fig
        self._rank_chart_theme = refs.rank_chart_theme
        self._rank_canvas = refs.rank_canvas
        self._refresh_serp_tab_lists()
        return page

    def _refresh_serp_tab_lists(self) -> None:
        self._refresh_serp_keyword_combo()
        self._refresh_serp_snapshots_table()
        self._rebuild_rank_chart()
        self._apply_serp_saved_view()

    def _save_serp_saved_view(self) -> None:
        kid = self._serp_kw_combo.currentData() if getattr(self, "_serp_kw_combo", None) else None
        rank_kid = self._rank_kw_combo.currentData() if getattr(self, "_rank_kw_combo", None) else None
        self._qs.setValue("ui/saved_view/serp/keyword_id", "" if kid is None else str(kid))
        self._qs.setValue("ui/saved_view/serp/rank_keyword_id", "" if rank_kid is None else str(rank_kid))
        self.statusBar().showMessage(self.tr("Saved SERP view"), 1800)

    def _apply_serp_saved_view(self) -> None:
        if not getattr(self, "_serp_kw_combo", None):
            return
        kid_raw = str(self._qs.value("ui/saved_view/serp/keyword_id", ""))
        rank_raw = str(self._qs.value("ui/saved_view/serp/rank_keyword_id", ""))
        if kid_raw.isdigit():
            i = self._serp_kw_combo.findData(int(kid_raw))
            if i >= 0:
                self._serp_kw_combo.setCurrentIndex(i)
        if rank_raw.isdigit():
            i2 = self._rank_kw_combo.findData(int(rank_raw))
            if i2 >= 0:
                self._rank_kw_combo.setCurrentIndex(i2)

    def _refresh_keywords_table(self) -> None:
        if not getattr(self, "_kw_table", None):
            return
        if not self._current_project_id:
            self._kw_table.setRowCount(0)
            self._load_keyword_project_context()
            return
        s = self._session()
        try:
            kws = (
                s.execute(
                    select(Keyword)
                    .where(Keyword.project_id == self._current_project_id)
                    .order_by(Keyword.phrase.asc())
                    .limit(500)
                )
                .scalars()
                .all()
            )
            self._kw_table.setRowCount(len(kws))
            for r, k in enumerate(kws):
                self._kw_table.setItem(r, 0, QTableWidgetItem(str(k.id)))
                self._kw_table.setItem(r, 1, QTableWidgetItem(k.phrase))
                self._kw_table.setItem(r, 2, QTableWidgetItem(k.locale or ""))
                self._kw_table.setItem(r, 3, QTableWidgetItem(k.device or ""))
                arch = self.tr("yes") if k.archived_at else ""
                self._kw_table.setItem(r, 4, QTableWidgetItem(arch))
        finally:
            s.close()
        self._load_keyword_project_context()

    def _refresh_serp_keyword_combo(self) -> None:
        combos: list[QComboBox] = []
        if getattr(self, "_serp_kw_combo", None):
            combos.append(self._serp_kw_combo)
        if getattr(self, "_rank_kw_combo", None):
            combos.append(self._rank_kw_combo)
        if not combos:
            return
        preserved = {id(c): c.currentData() for c in combos}
        for c in combos:
            c.blockSignals(True)
            c.clear()
        if not self._current_project_id:
            for c in combos:
                c.addItem(self.tr("(select a project)"), None)
            for c in combos:
                c.blockSignals(False)
            return
        s = self._session()
        try:
            kws = list(
                s.execute(
                    select(Keyword)
                    .where(
                        Keyword.project_id == self._current_project_id,
                        Keyword.archived_at.is_(None),
                    )
                    .order_by(Keyword.phrase.asc())
                )
                .scalars()
                .all()
            )
        finally:
            s.close()
        for c in combos:
            for k in kws:
                c.addItem(k.phrase[:120], k.id)
            if not kws:
                c.addItem(self.tr("(add a keyword first)"), None)
        for c in combos:
            c.blockSignals(False)
        for c in combos:
            prev = preserved.get(id(c))
            if prev is not None:
                idx = c.findData(prev)
                if idx >= 0:
                    c.blockSignals(True)
                    c.setCurrentIndex(idx)
                    c.blockSignals(False)

    def _refresh_serp_snapshots_table(self) -> None:
        if not getattr(self, "_serp_snapshots_table", None):
            return
        if not self._current_project_id:
            self._serp_snapshots_table.setRowCount(0)
            if getattr(self, "_serp_inspector", None):
                self._serp_inspector.clear()
            return
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(SerpResult, Keyword.phrase)
                    .join(Keyword, SerpResult.keyword_id == Keyword.id)
                    .where(Keyword.project_id == self._current_project_id)
                    .order_by(SerpResult.fetched_at.desc())
                    .limit(200)
                )
                .all()
            )
            self._serp_snapshots_table.setRowCount(len(rows))
            self._serp_row_meta = []
            for r, (sr, phrase) in enumerate(rows):
                n_org = serp_organic_count(sr.results_json)
                self._serp_row_meta.append(
                    build_serp_row_meta(
                        snapshot_id=sr.id,
                        phrase=phrase,
                        status=sr.status,
                        fetched=(sr.fetched_at.isoformat() if sr.fetched_at else ""),
                        organic_rows=n_org,
                        has_html=bool(sr.html_gzip),
                    )
                )
                self._serp_snapshots_table.setItem(r, 0, QTableWidgetItem(str(sr.id)))
                self._serp_snapshots_table.setItem(r, 1, QTableWidgetItem(phrase))
                fts = sr.fetched_at.isoformat() if sr.fetched_at else ""
                self._serp_snapshots_table.setItem(r, 2, QTableWidgetItem(fts))
                raw_status = (sr.status or "").strip()
                self._serp_snapshots_table.setItem(r, 3, QTableWidgetItem(raw_status))
                self._serp_snapshots_table.setCellWidget(
                    r,
                    3,
                    StatusPill(raw_status or self.tr("unknown"), status=serp_status_variant(raw_status)),
                )
                self._serp_snapshots_table.setItem(r, 4, QTableWidgetItem(str(n_org)))
        finally:
            s.close()
        self._on_serp_selection_changed()

    def _on_serp_selection_changed(self) -> None:
        if not getattr(self, "_serp_inspector", None):
            return
        rows = sorted({ix.row() for ix in self._serp_snapshots_table.selectedIndexes()})
        if len(rows) != 1:
            self._serp_inspector.setPlainText(self.tr("Select one SERP snapshot row to inspect."))
            return
        row = rows[0]
        if row < 0 or row >= len(getattr(self, "_serp_row_meta", [])):
            self._serp_inspector.setPlainText(self.tr("No snapshot metadata found for selection."))
            return
        m = self._serp_row_meta[row]
        self._serp_inspector.setPlainText(build_serp_inspector_text(m))

    def _rebuild_rank_chart(self) -> None:
        if not getattr(self, "_rank_fig", None) or not getattr(self, "_rank_canvas", None):
            return
        s_theme = self._session()
        try:
            chart_theme = get_value(s_theme, "ui_theme", "dark") or "dark"
        finally:
            s_theme.close()
        self._rank_chart_theme = chart_theme
        self._rank_fig.clear()
        ax = self._rank_fig.add_subplot(111)
        if chart_theme == "light":
            self._rank_fig.patch.set_facecolor("#f3f3f3")
            ax.set_facecolor("#ffffff")
            ax.tick_params(colors="#333333")
            ax.title.set_color("#1a1a1a")
            spine_c = "#888888"
            line_c = "#006cbd"
        else:
            self._rank_fig.patch.set_facecolor("#252526")
            ax.set_facecolor("#1e1e1e")
            ax.tick_params(colors="#e8e8e8")
            ax.title.set_color("#e8e8e8")
            spine_c = "#6a6a6a"
            line_c = "#4ec9b0"
        for spine in ax.spines.values():
            spine.set_color(spine_c)
        ax.set_title(self.tr("Rank position vs project domain (selected keyword)"))
        ax.set_xlabel(self.tr("Snapshot index (oldest → newest)"))
        ax.set_ylabel(self.tr("Rank (1 = best); gaps = not in top organic"))
        ax.grid(True, alpha=0.25, color=spine_c)
        if not self._current_project_id:
            ax.text(
                0.5,
                0.5,
                self.tr("Select a project."),
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=ax.title.get_color(),
            )
            self._rank_canvas.draw()
            return
        kid = self._rank_kw_combo.currentData() if getattr(self, "_rank_kw_combo", None) else None
        if kid is None:
            ax.text(
                0.5,
                0.5,
                self.tr("Select a keyword for the chart."),
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=ax.title.get_color(),
            )
            self._rank_canvas.draw()
            return
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(Ranking.position, Ranking.tracked_at, Ranking.degraded)
                    .where(Ranking.keyword_id == int(kid))
                    .order_by(Ranking.tracked_at.asc())
                    .limit(100)
                )
                .all()
            )
        finally:
            s.close()
        if not rows:
            ax.text(
                0.5,
                0.5,
                self.tr(
                    "No rank rows yet — run a SERP snapshot. "
                    "Rank matches the project default domain to organic URLs."
                ),
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=ax.title.get_color(),
            )
            self._rank_canvas.draw()
            return
        ys: list[float] = []
        for pos, _ta, _deg in rows:
            ys.append(float(pos) if pos is not None else math.nan)
        xs = list(range(1, len(ys) + 1))
        ax.plot(xs, ys, color=line_c, marker="o", markersize=3)
        ax.invert_yaxis()
        self._rank_canvas.draw()

    def _add_keyword(self) -> None:
        if not self._current_project_id:
            return
        phrase = self._kw_phrase.text().strip()
        if not phrase:
            return
        s = self._session()
        try:
            s.add(Keyword(project_id=self._current_project_id, phrase=phrase))
            s.commit()
        finally:
            s.close()
        self._kw_phrase.clear()
        self._refresh_keywords_table()
        self._refresh_serp_keyword_combo()

    def _load_keyword_project_context(self) -> None:
        if not getattr(self, "_kw_site_type", None):
            return
        if not self._current_project_id:
            self._kw_brand.clear()
            self._kw_topic.clear()
            self._kw_template_list.clear()
            self._kw_site_type.setCurrentIndex(0)
            self._kw_country.setCurrentIndex(0)
            return
        s = self._session()
        try:
            p = s.get(Project, self._current_project_id)
            if not p:
                return
            try:
                merged = merge_context_from_project(s, p)
            except OperationalError:
                s.rollback()
                merged = {
                    "site_type": "other",
                    "primary_country_code": "",
                    "brand_name": (p.name or "").strip(),
                    "primary_topic": "",
                }
        finally:
            s.close()
        st = str(merged.get("site_type") or "other")
        ix = self._kw_site_type.findData(st)
        self._kw_site_type.setCurrentIndex(ix if ix >= 0 else 0)
        cc = str(merged.get("primary_country_code") or "").upper()[:2]
        ix2 = self._kw_country.findData(cc)
        self._kw_country.setCurrentIndex(ix2 if ix2 >= 0 else 0)
        self._kw_brand.setText(str(merged.get("brand_name") or ""))
        self._kw_topic.setText(str(merged.get("primary_topic") or ""))

    def _save_project_seo_context(self) -> None:
        if not self._current_project_id:
            QMessageBox.warning(self, self.tr("Project"), self.tr("Select a project first."))
            return
        s = self._session()
        try:
            p = s.get(Project, self._current_project_id)
            if not p:
                return
            prev = dict(p.seo_context_json or {})
            prev.update(
                {
                    "site_type": str(self._kw_site_type.currentData() or "other"),
                    "primary_country_code": str(self._kw_country.currentData() or "").upper()[:2],
                    "brand_name": self._kw_brand.text().strip(),
                    "primary_topic": self._kw_topic.text().strip(),
                }
            )
            p.seo_context_json = prev
            s.commit()
        except OperationalError:
            s.rollback()
            QMessageBox.warning(
                self,
                self.tr("Database"),
                self.tr("Run database migration to enable project targeting (seo_context_json)."),
            )
            return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Keywords"), self.tr("Targeting saved for this project."))

    def _generate_keyword_templates(self) -> None:
        if not self._current_project_id:
            return
        s = self._session()
        phrases: list[str] = []
        try:
            p = s.get(Project, self._current_project_id)
            if not p:
                return
            merged = merge_context_from_project(s, p)
            merged["site_type"] = str(self._kw_site_type.currentData() or "other")
            merged["primary_country_code"] = str(self._kw_country.currentData() or "").upper()[:2]
            merged["brand_name"] = self._kw_brand.text().strip()
            merged["primary_topic"] = self._kw_topic.text().strip()
            ctx = context_from_merged(merged, p, s)
            rows = s.execute(
                select(Keyword.phrase).where(Keyword.project_id == self._current_project_id)
            ).all()
            existing = {str(row[0]).casefold() for row in rows}
            phrases = suggest_phrases(ctx, existing_lower=existing)
        except OperationalError:
            s.rollback()
            QMessageBox.warning(
                self,
                self.tr("Database"),
                self.tr("Run database migration to enable project targeting (seo_context_json)."),
            )
            return
        finally:
            s.close()
        self._kw_template_list.clear()
        for ph in phrases:
            it = QListWidgetItem(ph)
            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            it.setCheckState(Qt.CheckState.Checked)
            self._kw_template_list.addItem(it)
        if not phrases:
            QMessageBox.information(
                self,
                self.tr("Templates"),
                self.tr("No new suggestions (try another site type or fill brand/topic)."),
            )

    def _add_checked_template_keywords(self) -> None:
        if not self._current_project_id:
            return
        to_add: list[str] = []
        for i in range(self._kw_template_list.count()):
            it = self._kw_template_list.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                to_add.append(it.text().strip())
        if not to_add:
            QMessageBox.information(self, self.tr("Keywords"), self.tr("No rows checked."))
            return
        site_type = str(self._kw_site_type.currentData() or "other")
        s = self._session()
        try:
            for phrase in to_add:
                if not phrase:
                    continue
                s.add(
                    Keyword(
                        project_id=self._current_project_id,
                        phrase=phrase[:512],
                        tags_json={"source": "template", "site_type": site_type},
                    )
                )
            s.commit()
        except OperationalError:
            s.rollback()
            QMessageBox.warning(self, self.tr("Database"), self.tr("Migration may be required."))
            return
        finally:
            s.close()
        self._refresh_keywords_table()
        self._refresh_serp_keyword_combo()
        QMessageBox.information(
            self,
            self.tr("Keywords"),
            self.tr("Added %1 keyword(s).").replace("%1", str(len(to_add))),
        )

    def _run_serp(self) -> None:
        if not self._current_project_id:
            return
        kid = self._serp_kw_combo.currentData() if getattr(self, "_serp_kw_combo", None) else None
        if kid is None:
            QMessageBox.information(self, self.tr("SERP"), self.tr("Add or select a keyword first."))
            return
        s = self._session()
        try:
            kw = s.get(Keyword, int(kid))
            if not kw or kw.project_id != self._current_project_id or kw.archived_at is not None:
                QMessageBox.warning(self, self.tr("SERP"), self.tr("Invalid keyword for this project."))
                return
            job = Job(
                project_id=self._current_project_id,
                type="serp",
                status="queued",
                progress_pct=0,
                payload_json={"keyword_id": int(kid)},
            )
            s.add(job)
            s.commit()
            jid = job.id
        finally:
            s.close()
        self._append_log(f"Queued SERP job {jid}")
        self._serp_active_job_id = jid
        self._serp_btn.setEnabled(False)
        self._serp_progress.setRange(0, 100)
        self._serp_progress.setValue(0)
        self._serp_progress.setVisible(True)
        self._set_progress_status(self._serp_status, self.tr("Queued…"), state="running")
        self._pool.start(SerpWorker(jid, self._engine, self._bus))
        self._refresh_job_table()

    def _run_citation_matrix(self) -> None:
        if not self._current_project_id:
            QMessageBox.information(
                self,
                self.tr("Citations"),
                self.tr("Select a project first."),
            )
            return
        s = self._session()
        try:
            n_loc = (
                s.scalar(
                    select(func.count())
                    .select_from(Location)
                    .where(Location.project_id == self._current_project_id)
                )
                or 0
            )
            n_src = (
                s.scalar(
                    select(func.count())
                    .select_from(CitationSource)
                    .where(
                        CitationSource.is_builtin.is_(True),
                        CitationSource.project_id.is_(None),
                        CitationSource.enabled.is_(True),
                    )
                )
                or 0
            )
        finally:
            s.close()
        if n_loc == 0:
            QMessageBox.information(
                self,
                self.tr("Citations"),
                self.tr(
                    "This project has no locations yet. "
                    "Add one when creating a project or wait for a location editor."
                ),
            )
            return
        if n_src == 0:
            QMessageBox.information(
                self,
                self.tr("Citations"),
                self.tr("No enabled built-in citation sources in the database."),
            )
            return
        total = int(n_loc) * int(n_src)
        msg = (
            self.tr(
                "About to queue %1 checks (%2 locations × %3 built-in sources). "
                "HTTP requests will be sent to third-party sites—only continue if "
                "that is allowed for you and you accept rate-limit responsibility. Proceed?"
            )
            .replace("%1", str(total))
            .replace("%2", str(n_loc))
            .replace("%3", str(n_src))
        )
        if (
            QMessageBox.question(
                self,
                self.tr("Citation matrix"),
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        s = self._session()
        try:
            job = Job(
                project_id=self._current_project_id,
                type="citation",
                status="queued",
                progress_pct=0.0,
                payload_json={},
            )
            s.add(job)
            s.commit()
            jid = job.id
        finally:
            s.close()
        self._append_log(self.tr("Queued citation job %1").replace("%1", str(jid)))
        self._citation_active_job_id = jid
        self._cit_run_btn.setEnabled(False)
        self._cit_progress.setRange(0, 100)
        self._cit_progress.setValue(0)
        self._cit_progress.setVisible(True)
        self._set_progress_status(self._cit_status, self.tr("Queued…"), state="running")
        self._pool.start(CitationMatrixWorker(jid, self._engine, self._bus))
        self._refresh_job_table()

    def _export_builtin_citations_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export built-in citation sources"), "", self.tr("CSV (*.csv)")
        )
        if not path:
            return
        p = Path(path)
        s = self._session()
        try:
            try:
                n = export_builtin_citation_sources_csv(s, p)
            except OSError as e:
                self._warn_export_write_failed(p, e)
                return
        finally:
            s.close()
        QMessageBox.information(
            self,
            self.tr("Export"),
            self.tr("Wrote {0} row(s) to:\n{1}").format(n, str(p)),
        )

    def _refresh_citations_builtin_table(self) -> None:
        if not getattr(self, "_cit_src_table", None):
            return
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(CitationSource)
                    .where(CitationSource.is_builtin.is_(True), CitationSource.project_id.is_(None))
                    .order_by(CitationSource.sort_order, CitationSource.id)
                )
                .scalars()
                .all()
            )
            self._cit_src_table.setRowCount(len(rows))
            for r, src in enumerate(rows):
                tags = src.region_tags
                tags_s = json.dumps(tags, ensure_ascii=False) if isinstance(tags, list) else (tags or "")
                self._cit_src_table.setItem(r, 0, QTableWidgetItem(str(src.id)))
                self._cit_src_table.setItem(r, 1, QTableWidgetItem(src.name))
                url = src.template_url
                if len(url) > 96:
                    url = url[:93] + "…"
                self._cit_src_table.setItem(r, 2, QTableWidgetItem(url))
                self._cit_src_table.setItem(r, 3, QTableWidgetItem(tags_s))
                self._cit_src_table.setItem(
                    r, 4, QTableWidgetItem(self.tr("yes") if src.requires_playwright else "")
                )
                self._cit_src_table.setItem(r, 5, QTableWidgetItem(self.tr("yes") if src.enabled else ""))
                self._cit_src_table.setItem(r, 6, QTableWidgetItem(str(src.pack_version)))
        finally:
            s.close()

    def _refresh_citations_locations_table(self) -> None:
        if not getattr(self, "_cit_loc_table", None):
            return
        if not self._current_project_id:
            self._cit_loc_table.setRowCount(0)
            return
        s = self._session()
        try:
            locs = (
                s.execute(
                    select(Location)
                    .where(Location.project_id == self._current_project_id)
                    .order_by(Location.label.asc())
                    .limit(200)
                )
                .scalars()
                .all()
            )
            self._cit_loc_table.setRowCount(len(locs))
            for r, loc in enumerate(locs):
                self._cit_loc_table.setItem(r, 0, QTableWidgetItem(str(loc.id)))
                self._cit_loc_table.setItem(r, 1, QTableWidgetItem(loc.label))
                self._cit_loc_table.setItem(r, 2, QTableWidgetItem(loc.business_name))
                line1 = loc.address_line1 or ""
                city = loc.city or ""
                reg = loc.region or ""
                self._cit_loc_table.setItem(r, 3, QTableWidgetItem(line1))
                self._cit_loc_table.setItem(r, 4, QTableWidgetItem(city))
                self._cit_loc_table.setItem(r, 5, QTableWidgetItem(reg))
                self._cit_loc_table.setItem(r, 6, QTableWidgetItem(loc.primary_phone_e164 or ""))
        finally:
            s.close()

    def _refresh_citations_checks_table(self) -> None:
        if not getattr(self, "_cit_chk_table", None):
            return
        if not self._current_project_id:
            self._cit_chk_table.setRowCount(0)
            if getattr(self, "_cit_inspector", None):
                self._cit_inspector.clear()
            return
        s = self._session()
        try:
            q = (
                select(CitationCheck, Location.label, CitationSource.name)
                .join(Location, CitationCheck.location_id == Location.id)
                .join(CitationSource, CitationCheck.source_id == CitationSource.id)
                .where(Location.project_id == self._current_project_id)
                .order_by(CitationCheck.id.desc())
                .limit(500)
            )
            rows = s.execute(q).all()
            self._cit_chk_table.setRowCount(len(rows))
            self._cit_chk_row_meta = []
            for r, (chk, loc_label, src_name) in enumerate(rows):
                when = chk.fetched_at.isoformat() if chk.fetched_at else ""
                fu = chk.final_url or chk.requested_url or ""
                fu_short = clipped_url(fu, max_len=80)
                err = clipped_error(chk.error_text or "", max_len=120)
                self._cit_chk_row_meta.append(
                    build_citation_check_row_meta(
                        check_id=chk.id,
                        fetched=when,
                        location=loc_label,
                        source=src_name,
                        status=chk.status or "",
                        http_status=chk.http_status,
                        final_url=(chk.final_url or chk.requested_url or ""),
                        error=(chk.error_text or ""),
                    )
                )
                self._cit_chk_table.setItem(r, 0, QTableWidgetItem(str(chk.id)))
                self._cit_chk_table.setItem(r, 1, QTableWidgetItem(when))
                self._cit_chk_table.setItem(r, 2, QTableWidgetItem(loc_label))
                self._cit_chk_table.setItem(r, 3, QTableWidgetItem(src_name))
                raw_status = (chk.status or "").strip()
                self._cit_chk_table.setItem(r, 4, QTableWidgetItem(raw_status))
                self._cit_chk_table.setCellWidget(
                    r,
                    4,
                    StatusPill(raw_status or self.tr("unknown"), status=citation_status_variant(raw_status)),
                )
                self._cit_chk_table.setItem(
                    r, 5, QTableWidgetItem("" if chk.http_status is None else str(chk.http_status))
                )
                self._cit_chk_table.setItem(r, 6, QTableWidgetItem(fu_short))
                self._cit_chk_table.setItem(r, 7, QTableWidgetItem(err))
        finally:
            s.close()
        self._on_citations_check_selection_changed()

    def _on_citations_check_selection_changed(self) -> None:
        if not getattr(self, "_cit_inspector", None):
            return
        rows = sorted({ix.row() for ix in self._cit_chk_table.selectedIndexes()})
        if len(rows) != 1:
            self._cit_inspector.setPlainText(self.tr("Select one citation check row to inspect."))
            return
        row = rows[0]
        if row < 0 or row >= len(getattr(self, "_cit_chk_row_meta", [])):
            self._cit_inspector.setPlainText(self.tr("No citation details for selected row."))
            return
        m = self._cit_chk_row_meta[row]
        self._cit_inspector.setPlainText(build_citation_inspector_text(m))

    def _refresh_citations_page(self) -> None:
        self._refresh_citations_builtin_table()
        self._refresh_citations_locations_table()
        self._refresh_citations_checks_table()

    def _save_citations_saved_view(self) -> None:
        if not getattr(self, "_cit_tabs", None):
            return
        self._qs.setValue("ui/saved_view/citations/tab_index", int(self._cit_tabs.currentIndex()))
        self.statusBar().showMessage(self.tr("Saved citations view"), 1800)

    def _apply_citations_saved_view(self) -> None:
        if not getattr(self, "_cit_tabs", None):
            return
        raw = self._qs.value("ui/saved_view/citations/tab_index", 0)
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            idx = 0
        idx = max(0, min(idx, max(0, self._cit_tabs.count() - 1)))
        self._cit_tabs.setCurrentIndex(idx)

    def _page_citations(self) -> QWidget:
        page, refs = build_citations_page(
            header=self._page_header(
                self.tr("Citations"),
                self.tr(
                    "Built-in directory templates (YAML → DB), project NAP locations, and any stored citation checks."
                ),
            ),
            tr=self.tr,
            make_inspector_panel=lambda: InspectorPanel(
                self.tr("Inspector"),
                self.tr("Select one check row to inspect citation risks/actions."),
                min_width=340,
            ),
            on_run_citation_matrix=self._run_citation_matrix,
            on_refresh_citations_page=self._refresh_citations_page,
            on_save_citations_saved_view=self._save_citations_saved_view,
            on_apply_citations_saved_view=self._apply_citations_saved_view,
            on_refresh_citations_builtin_table=self._refresh_citations_builtin_table,
            on_export_builtin_citations_csv=self._export_builtin_citations_csv,
            on_refresh_citations_locations_table=self._refresh_citations_locations_table,
            on_refresh_citations_checks_table=self._refresh_citations_checks_table,
            on_citations_check_selection_changed=self._on_citations_check_selection_changed,
        )
        self._cit_run_btn = refs.cit_run_btn
        self._cit_progress = refs.cit_progress
        self._cit_save_view_btn = refs.cit_save_view_btn
        self._cit_load_view_btn = refs.cit_load_view_btn
        self._cit_status = refs.cit_status
        self._cit_src_table = refs.cit_src_table
        self._cit_loc_table = refs.cit_loc_table
        self._cit_chk_table = refs.cit_chk_table
        self._cit_chk_row_meta = refs.cit_chk_row_meta
        self._cit_inspector_panel = refs.cit_inspector_panel
        self._cit_inspector = refs.cit_inspector
        self._cit_tabs = refs.cit_tabs
        return page

    def _page_local(self) -> QWidget:
        return build_local_page(
            header=self._page_header(self.tr("Local")),
            tr=self.tr,
        )

    def _page_integrations(self) -> QWidget:
        return build_integrations_page(
            header=self._page_header(self.tr("Integrations")),
            tr=self.tr,
            placeholders=list_integration_placeholders(),
        )

    def _page_reports(self) -> QWidget:
        page, refs = build_reports_page(
            header=self._page_header(self.tr("Reports")),
            tr=self.tr,
            on_export_markdown=self._export_md,
        )
        self._export_btn = refs.export_btn
        self._reports_progress = refs.reports_progress
        self._reports_status = refs.reports_status
        return page

    def _export_md(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Save report"), "", "*.md")
        if not path:
            return

        def write_file() -> str:
            Path(path).write_text("# Crawlix export\n\n(J11 stub)\n", encoding="utf-8")
            return path

        self._export_btn.setEnabled(False)
        self._pool.start(
            SimpleTaskWorker(
                "export_md",
                self._bus,
                write_file,
                started_message=self.tr("Writing file…"),
            )
        )

    def _page_settings(self) -> QWidget:
        theme_mode = "dark"
        s = self._session()
        try:
            theme_mode = get_value(s, "ui_theme", "dark") or "dark"
        finally:
            s.close()
        ollama_url = "http://127.0.0.1:11434"
        ollama_enabled = False
        s_ol = self._session()
        try:
            ollama_url = get_value(s_ol, "ollama_base_url", "http://127.0.0.1:11434") or "http://127.0.0.1:11434"
            ollama_enabled = get_value(s_ol, "ollama_enabled", "0") == "1"
        finally:
            s_ol.close()
        page, refs = build_settings_page(
            header=self._page_header(self.tr("Settings")),
            tr=self.tr,
            theme_mode=theme_mode,
            ollama_base_url=ollama_url,
            ollama_enabled=ollama_enabled,
            on_save_theme=self._save_theme,
            on_save_ollama_settings=self._save_ollama_settings,
        )
        self._theme_combo = refs.theme_combo
        self._ollama_url = refs.ollama_url
        self._ollama_en = refs.ollama_en
        return page

    def _save_theme(self) -> None:
        mode = "light" if self._theme_combo.currentIndex() == 1 else "dark"
        s = self._session()
        try:
            set_value(s, "ui_theme", mode)
            s.commit()
        finally:
            s.close()
        self._reload_styles()
        self._rebuild_rank_chart()

    def _save_ollama_settings(self) -> None:
        s = self._session()
        try:
            set_value(s, "ollama_base_url", self._ollama_url.text().strip() or "http://127.0.0.1:11434")
            set_value(s, "ollama_enabled", "1" if self._ollama_en.isChecked() else "0")
            s.commit()
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Settings"), self.tr("Ollama settings saved."))

    def _new_project(self) -> None:
        dlg = NewProjectDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        s = self._session()
        try:
            slug = unique_project_slug(s, dlg.project_name())
            p = Project(
                name=dlg.project_name(),
                slug=slug,
                default_domain=dlg.default_domain(),
            )
            s.add(p)
            s.flush()
            loc = dlg.location_payload()
            if loc:
                s.add(
                    Location(
                        project_id=p.id,
                        label=loc["label"],
                        business_name=loc["business_name"],
                        city=loc.get("city"),
                        country_code=loc.get("country_code"),
                    )
                )
            s.commit()
            new_id = int(p.id)
        finally:
            s.close()
        self._reload_projects_combo()
        idx = self._project_combo.findData(new_id)
        if idx >= 0:
            self._project_combo.setCurrentIndex(idx)
        self._append_log(self.tr("Created project %1").replace("%1", str(new_id)))

    def _open_data_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._data_dir.resolve())))

    def _cancel_selected_job(self) -> None:
        row = self._jobs_table.currentRow()
        if row < 0:
            QMessageBox.information(self, self.tr("Jobs"), self.tr("Select a job row in the Jobs table first."))
            return
        item = self._jobs_table.item(row, 0)
        if not item:
            return
        try:
            jid = int(item.text())
        except ValueError:
            return
        s = self._session()
        try:
            j = s.get(Job, jid)
            if not j:
                return
            if j.status not in ("queued", "running"):
                QMessageBox.information(
                    self,
                    self.tr("Jobs"),
                    self.tr("Only queued or running jobs can be cancelled."),
                )
                return
            j.cancel_requested = True
            s.commit()
        finally:
            s.close()
        self._append_log(self.tr("Cancel requested for job %1").replace("%1", str(jid)))

    def _refresh_dashboard_stats(self) -> None:
        if not getattr(self, "_dash_stats", None):
            return
        if not self._current_project_id:
            self._dash_stats.setText(self.tr("Select a project from the list above."))
            if getattr(self, "_dash_actions", None):
                self._dash_actions.clear()
                self._dash_needs_attention.clear()
                self._dash_recent_outcomes.clear()
            return
        s = self._session()
        try:
            summary = load_dashboard_summary(s, self._current_project_id, never_label=self.tr("never"))
            self._dash_stats.setText(format_dashboard_summary_line(summary))
            if getattr(self, "_dash_actions", None):
                hub = load_dashboard_action_hub(s, self._current_project_id)
                self._dash_actions.clear()
                for a in hub.next_actions:
                    it = QListWidgetItem(f"{a.label}\n{a.reason}")
                    it.setData(Qt.ItemDataRole.UserRole, a.target)
                    it.setData(Qt.ItemDataRole.UserRole + 1, a.entity_id)
                    it.setData(Qt.ItemDataRole.UserRole + 2, a.entity_type)
                    if a.suggested_filter:
                        it.setData(
                            Qt.ItemDataRole.UserRole + 3,
                            json.dumps(a.suggested_filter, ensure_ascii=True),
                        )
                    else:
                        it.setData(Qt.ItemDataRole.UserRole + 3, None)
                    self._dash_actions.addItem(it)
                self._dash_needs_attention.clear()
                for line in hub.needs_attention:
                    self._dash_needs_attention.addItem(line)
                self._dash_recent_outcomes.clear()
                for line in hub.recent_outcomes:
                    self._dash_recent_outcomes.addItem(line)
        finally:
            s.close()

    def _refresh_crawl_pages_table(self) -> None:
        if not getattr(self, "_crawl_pages_table", None):
            return
        self._crawl_row_meta = []
        self._crawl_display_page_ids = []
        if not self._current_project_id:
            self._crawl_pages_table.setRowCount(0)
            if getattr(self, "_crawl_filter_bar", None):
                self._crawl_filter_bar.set_summary(self.tr("Active filters: none"))
            for v in getattr(self, "_crawl_stat_values", {}).values():
                v.setText("—")
            if getattr(self, "_crawl_link_insights", None):
                self._crawl_link_insights.clear()
            if getattr(self, "_crawl_diff_view", None):
                self._crawl_diff_view.clear()
            self._update_crawl_detail_panel(None)
            return
        s = self._session()
        try:
            stats = fetch_crawl_dashboard_stats(s, self._current_project_id)
            dup_sizes = fetch_duplicate_final_sizes(s, self._current_project_id)
            url_norms_seg = list(
                s.scalars(
                    select(Page.url_norm).where(Page.project_id == self._current_project_id).limit(5000)
                ).all()
            )
            seg_lines = path_segment_lines_from_norms(url_norms_seg)
            seg_text = "\n".join(f"{a}  {b}" for a, b in seg_lines[:40])
            self._crawl_detail_segments.setPlainText(
                (self.tr("First path segment (sample up to 5000 URLs):\n") + seg_text)
                if seg_text
                else self.tr("No URLs yet.")
            )
            sv = getattr(self, "_crawl_stat_values", None)
            if sv:
                sv["pages"].setText(str(stats["pages"]))
                sv["unique_final"].setText(str(stats["unique_final_urls"]))
                sv["dup_clusters"].setText(str(stats["duplicate_clusters"]))
                sv["max_depth"].setText(str(stats["max_depth"]))
                sv["avg_depth"].setText(str(stats["avg_depth"]))
                sv["http_err"].setText(str(stats["http_errors"]))
            insight_cap = 800
            lite_rows = list(
                s.execute(
                    select(Page.id, Page.url_norm, Page.crawl_depth)
                    .where(Page.project_id == self._current_project_id)
                    .order_by(Page.id.asc())
                    .limit(insight_cap)
                ).all()
            )
            pages_minimal = [(int(r[0]), str(r[1]), r[2]) for r in lite_rows]
            url_norms_all = [t[1] for t in pages_minimal]
            pages_by_id_all = {t[0]: t[1] for t in pages_minimal}
            in_all = inbound_internal_counts(s, self._current_project_id, url_norms_all)
            out_all = outbound_internal_counts(s, self._current_project_id, pages_by_id_all)
            insight_txt = format_internal_link_insights(pages_minimal, in_all, out_all)
            _lj = latest_completed_crawl_job_id(s, self._current_project_id)
            if _lj is not None:
                insight_txt += f"\n\nInternal link counts use crawl job #{_lj} (latest completed crawl)."
            if int(stats["pages"]) > len(pages_minimal):
                insight_txt += (
                    f"\n\nNote: link stats above use the first {len(pages_minimal)} pages by id "
                    f"(project total {int(stats['pages'])} pages; avoids oversized SQL IN lists)."
                )
            self._crawl_link_insights.setPlainText(insight_txt)
            try:
                diff = diff_latest_two_snapshots(s, self._current_project_id)
                self._crawl_diff_view.setPlainText(format_crawl_diff_for_ui(diff))
            except OperationalError:
                self._crawl_diff_view.setPlainText(
                    "Crawl diff needs database migration (crawl_snapshots tables). "
                    "Run alembic upgrade or restart after updating Crawlix."
                )
            stmt = select(Page).where(Page.project_id == self._current_project_id)
            q = self._crawl_search.text().strip()
            if q:
                esc = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                pat = f"%{esc}%"
                stmt = stmt.where(
                    or_(Page.url_norm.like(pat, escape="\\"), Page.title.like(pat, escape="\\"))
                )
            hf = self._crawl_http_filter.currentData()
            if hf == "2xx":
                stmt = stmt.where(
                    Page.status_code.isnot(None),
                    Page.status_code >= 200,
                    Page.status_code < 300,
                )
            elif hf == "3xx":
                stmt = stmt.where(
                    Page.status_code.isnot(None),
                    Page.status_code >= 300,
                    Page.status_code < 400,
                )
            elif hf == "4xx":
                stmt = stmt.where(
                    Page.status_code.isnot(None),
                    Page.status_code >= 400,
                    Page.status_code < 500,
                )
            elif hf == "5xx":
                stmt = stmt.where(
                    Page.status_code.isnot(None),
                    Page.status_code >= 500,
                    Page.status_code < 600,
                )
            elif hf == "err":
                stmt = stmt.where(Page.status_code.isnot(None), Page.status_code >= 400)
            elif hf == "none":
                stmt = stmt.where(Page.status_code.is_(None))
            dd = self._crawl_depth_filter.currentData()
            if isinstance(dd, int):
                stmt = stmt.where(Page.crawl_depth == dd)
            candidates = list(
                s.execute(stmt.order_by(Page.id.desc()).limit(3000)).scalars().all()
            )
            url_norms = [p.url_norm for p in candidates]
            pages_by_id = {p.id: p.url_norm for p in candidates}
            in_map = inbound_internal_counts(s, self._current_project_id, url_norms)
            out_map = outbound_internal_counts(s, self._current_project_id, pages_by_id)
            max_in = self._crawl_max_inbound.value()
            min_out = self._crawl_min_outbound.value()
            dup_only = self._crawl_dup_only.isChecked()
            active_filters: list[str] = []
            if q:
                active_filters.append(self.tr("Search"))
            if hf:
                active_filters.append(self.tr("HTTP"))
            if isinstance(dd, int):
                active_filters.append(self.tr("Depth"))
            if dup_only:
                active_filters.append(self.tr("Duplicate finals"))
            if max_in >= 0:
                active_filters.append(self.tr("Max inbound"))
            if min_out >= 0:
                active_filters.append(self.tr("Min outbound"))
            self._crawl_filter_bar.set_summary(
                self.tr("Active filters: none")
                if not active_filters
                else self.tr("Active filters: %1").replace("%1", ", ".join(active_filters))
            )
            rows_data: list[tuple[Page, int, int, int]] = []
            for p in candidates:
                eff = effective_final_url(p)
                dg = dup_sizes.get(eff, 1)
                if dup_only and dg <= 1:
                    continue
                nin = in_map.get(p.url_norm, 0)
                nout = out_map.get(p.id, 0)
                if max_in >= 0 and nin > max_in:
                    continue
                if min_out >= 0 and nout < min_out:
                    continue
                rows_data.append((p, nin, nout, dg))
            rows_data = rows_data[:500]
            self._crawl_pages_table.setRowCount(len(rows_data))
            for r, (p, nin, nout, dg) in enumerate(rows_data):
                dup_cell = "" if dg <= 1 else self.tr("%1 URLs").replace("%1", str(dg))
                meta = {
                    "id": p.id,
                    "url_norm": p.url_norm,
                    "url_final": p.url_final,
                    "title": p.title or "",
                    "status_code": p.status_code,
                    "crawl_depth": p.crawl_depth,
                    "last_crawled_at": p.last_crawled_at,
                    "nin": nin,
                    "nout": nout,
                    "dup_group_size": dg,
                }
                self._crawl_row_meta.append(meta)
                self._crawl_display_page_ids.append(int(p.id))
                self._crawl_pages_table.setItem(r, 0, QTableWidgetItem(str(p.id)))
                self._crawl_pages_table.setItem(r, 1, QTableWidgetItem(p.url_norm))
                self._crawl_pages_table.setItem(r, 2, QTableWidgetItem((p.title or "")[:120]))
                self._crawl_pages_table.setItem(
                    r, 3, QTableWidgetItem("" if p.status_code is None else str(p.status_code))
                )
                self._crawl_pages_table.setItem(
                    r, 4, QTableWidgetItem("" if p.crawl_depth is None else str(p.crawl_depth))
                )
                self._crawl_pages_table.setItem(r, 5, QTableWidgetItem(str(nin)))
                self._crawl_pages_table.setItem(r, 6, QTableWidgetItem(str(nout)))
                self._crawl_pages_table.setItem(r, 7, QTableWidgetItem(dup_cell))
                ts = p.last_crawled_at.isoformat() if p.last_crawled_at else ""
                self._crawl_pages_table.setItem(r, 8, QTableWidgetItem(ts))
        finally:
            s.close()
        self._on_crawl_selection_changed()

    def _crawl_selected_row_indices(self) -> list[int]:
        return sorted({ix.row() for ix in self._crawl_pages_table.selectedIndexes()})

    def _on_crawl_selection_changed(self) -> None:
        rows = self._crawl_selected_row_indices()
        if len(rows) != 1:
            self._update_crawl_detail_panel(None)
            return
        r = rows[0]
        if r < 0 or r >= len(self._crawl_row_meta):
            self._update_crawl_detail_panel(None)
            return
        self._update_crawl_detail_panel(self._crawl_row_meta[r])

    def _update_crawl_detail_panel(self, meta: dict[str, object] | None) -> None:
        if not meta:
            self._crawl_detail_orig.setText("—")
            self._crawl_detail_final.setText("—")
            self._crawl_detail_title.setText("—")
            self._crawl_detail_http.setText("—")
            self._crawl_detail_depth.setText("—")
            self._crawl_detail_inout.setText("—")
            self._crawl_detail_last.setText("—")
            self._crawl_detail_hints.setText("")
            return
        un = str(meta.get("url_norm") or "")
        raw_final = meta.get("url_final")
        ufn_s = raw_final.strip() if isinstance(raw_final, str) else ""
        display_final = ufn_s if ufn_s else self.tr("(same as original)")
        self._crawl_detail_orig.setText(self.tr("Original URL:\n%1").replace("%1", un))
        self._crawl_detail_final.setText(self.tr("Final URL:\n%1").replace("%1", display_final))
        self._crawl_detail_title.setText(self.tr("Title:\n%1").replace("%1", str(meta.get("title") or "")))
        sc = meta.get("status_code")
        self._crawl_detail_http.setText(
            self.tr("HTTP status: %1").replace("%1", "—" if sc is None else str(int(sc)))
        )
        d = meta.get("crawl_depth")
        self._crawl_detail_depth.setText(
            self.tr("Depth: %1").replace("%1", "—" if d is None else str(int(d)))
        )
        nin = int(meta.get("nin") or 0)
        nout = int(meta.get("nout") or 0)
        self._crawl_detail_inout.setText(
            self.tr("Internal inbound: %1\nInternal outbound: %2")
            .replace("%1", str(nin))
            .replace("%2", str(nout))
        )
        ts = meta.get("last_crawled_at")
        last_s = ts.isoformat() if ts else "—"
        self._crawl_detail_last.setText(self.tr("Last crawled: %1").replace("%1", last_s))
        dg = int(meta.get("dup_group_size") or 1)
        hints = normalization_hints(un, ufn_s or None, dup_group_size=dg)
        self._crawl_detail_hints.setText(
            build_crawl_hints_text(
                hints=hints,
                status_code=(None if sc is None else int(sc)),
                depth=(None if d is None else int(d)),
                inbound=nin,
                outbound=nout,
                fallback_no_hints=self.tr("No canonical/extension hints for this row."),
            )
        )

    def _on_crawl_table_context_menu(self, pos) -> None:
        self._show_context_menu(
            pos=pos,
            anchor=self._crawl_pages_table.viewport(),
            action_defs=crawl_context_menu_actions(),
            callbacks={"crawl_audit_selected": self._audit_crawl_selected_rows},
        )

    def _on_keywords_table_context_menu(self, pos) -> None:
        self._show_context_menu(
            pos=pos,
            anchor=self._kw_table.viewport(),
            action_defs=keywords_context_menu_actions(),
            callbacks={
                "keywords_refresh": self._refresh_keywords_table,
                "keywords_export_csv": self._export_keywords_csv_dialog,
            },
        )

    def _on_serp_table_context_menu(self, pos) -> None:
        self._show_context_menu(
            pos=pos,
            anchor=self._serp_snapshots_table.viewport(),
            action_defs=serp_context_menu_actions(),
            callbacks={
                "serp_refresh": self._refresh_serp_snapshots_table,
                "serp_run": self._run_serp,
                "serp_export_csv": self._export_serp_snapshots_csv_dialog,
            },
        )

    def _on_rank_chart_context_menu(self, pos) -> None:
        self._show_context_menu(
            pos=pos,
            anchor=self._rank_canvas,
            action_defs=rank_context_menu_actions(),
            callbacks={
                "rank_refresh": self._rebuild_rank_chart,
                "rank_export_csv": self._export_rank_history_csv_dialog,
            },
        )

    def _show_context_menu(
        self,
        *,
        pos,
        anchor: QWidget,
        action_defs: tuple[ContextMenuActionDef, ...],
        callbacks: dict[str, Callable[[], None]],
    ) -> None:
        menu = QMenu(self)
        for definition in action_defs:
            callback = callbacks.get(definition.action_id)
            if callback is None:
                continue
            action = QAction(self.tr(definition.label), self)
            action.triggered.connect(callback)
            menu.addAction(action)
        menu.exec(anchor.mapToGlobal(pos))

    def _audit_crawl_selected_rows(self) -> None:
        rows = self._crawl_selected_row_indices()
        if not rows:
            QMessageBox.information(self, self.tr("Audit"), self.tr("Select one or more rows first."))
            return
        ids = [self._crawl_row_meta[r]["id"] for r in rows if 0 <= r < len(self._crawl_row_meta)]
        self._start_audit_pages([int(x) for x in ids])

    def _audit_crawl_filtered_visible(self) -> None:
        if not self._crawl_display_page_ids:
            QMessageBox.information(
                self,
                self.tr("Audit"),
                self.tr("No visible rows — adjust filters or run a crawl."),
            )
            return
        self._start_audit_pages(list(self._crawl_display_page_ids))

    def _refresh_audit_results_table(self, *, prioritize_page_id: int | None = None) -> None:
        if not getattr(self, "_audit_results_table", None):
            return
        if not self._current_project_id:
            self._audit_results_table.setRowCount(0)
            if getattr(self, "_audit_filter_bar", None):
                self._audit_filter_bar.set_summary(self.tr("Active filters: none"))
            if getattr(self, "_audit_inspector", None):
                self._audit_inspector.clear()
            return
        s = self._session()
        try:
            rows = query_audit_results_rows(
                s,
                self._current_project_id,
                limit=200,
                prioritize_page_id=prioritize_page_id,
            )
            search = self._audit_search.text().strip().lower() if getattr(self, "_audit_search", None) else ""
            max_score = float(self._audit_max_score.value()) if getattr(self, "_audit_max_score", None) else -1.0
            min_issues = int(self._audit_min_issues.value()) if getattr(self, "_audit_min_issues", None) else 0
            filtered_rows: list[tuple[object, object]] = []
            for audit, page in rows:
                if search and search not in page.url_norm.lower():
                    continue
                n_issues = issue_count(audit.issues_json or [])
                if min_issues > 0 and n_issues < min_issues:
                    continue
                if max_score >= 0 and audit.overall_score is not None and float(audit.overall_score) > max_score:
                    continue
                filtered_rows.append((audit, page))
            active_filters: list[str] = []
            if search:
                active_filters.append(self.tr("Search"))
            if max_score >= 0:
                active_filters.append(self.tr("Max score"))
            if min_issues > 0:
                active_filters.append(self.tr("Min issues"))
            self._audit_filter_bar.set_summary(
                self.tr("Active filters: none")
                if not active_filters
                else self.tr("Active filters: %1").replace("%1", ", ".join(active_filters))
            )
            self._audit_results_table.setRowCount(len(filtered_rows))
            self._audit_row_meta = []
            url_norms_a = [page.url_norm for _audit, page in filtered_rows]
            pages_by_id_a = {page.id: page.url_norm for _audit, page in filtered_rows}
            in_map_a = inbound_internal_counts(s, self._current_project_id, url_norms_a)
            out_map_a = outbound_internal_counts(s, self._current_project_id, pages_by_id_a)
            for r, (audit, page) in enumerate(filtered_rows):
                issues = audit.issues_json or []
                n_issues = issue_count(issues)
                self._audit_results_table.setItem(r, 0, QTableWidgetItem(str(audit.id)))
                self._audit_results_table.setItem(r, 1, QTableWidgetItem(str(audit.page_id)))
                self._audit_results_table.setItem(r, 2, QTableWidgetItem(page.url_norm))
                self._audit_results_table.setItem(
                    r, 3, QTableWidgetItem("" if page.crawl_depth is None else str(page.crawl_depth))
                )
                nin = in_map_a.get(page.url_norm, 0)
                nout = out_map_a.get(page.id, 0)
                self._audit_row_meta.append(
                    build_audit_row_meta(
                        page_id=page.id,
                        url_norm=page.url_norm,
                        issues=issues,
                        inbound=nin,
                        outbound=nout,
                    )
                )
                self._audit_results_table.setItem(r, 4, QTableWidgetItem(str(nin)))
                self._audit_results_table.setItem(r, 5, QTableWidgetItem(str(nout)))
                sc = "" if audit.overall_score is None else f"{audit.overall_score:.1f}"
                self._audit_results_table.setItem(r, 6, QTableWidgetItem(sc))
                self._audit_results_table.setItem(r, 7, QTableWidgetItem(str(n_issues)))
        finally:
            s.close()
        self._on_audit_selection_changed()

    def _on_audit_selection_changed(self) -> None:
        if not getattr(self, "_audit_inspector", None):
            return
        rows = sorted({ix.row() for ix in self._audit_results_table.selectedIndexes()})
        if len(rows) != 1:
            self._audit_inspector.setPlainText(self.tr("Select one row to view contextual insights."))
            return
        row = rows[0]
        if row < 0 or row >= len(getattr(self, "_audit_row_meta", [])):
            self._audit_inspector.setPlainText(self.tr("No insight data for selection."))
            return
        meta = self._audit_row_meta[row]
        self._audit_inspector.setPlainText(build_audit_inspector_text(meta))

    def _warn_export_write_failed(self, path: Path, exc: Exception) -> None:
        QMessageBox.warning(
            self,
            self.tr("Export failed"),
            self.tr(
                "Could not write to:\n%1\n\n"
                "Common causes: the file is open in another program (for example Excel), "
                "OneDrive or sync software is locking the file, or the folder is read-only. "
                "Close the file, wait for sync to finish, or choose a different path.\n\n"
                "Details: %2"
            )
            .replace("%1", str(path))
            .replace("%2", str(exc)),
        )

    def _export_keywords_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export keywords"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(Keyword.id, Keyword.phrase, Keyword.locale, Keyword.device, Keyword.archived_at)
                    .where(Keyword.project_id == self._current_project_id)
                    .order_by(Keyword.phrase.asc())
                )
                .all()
            )
            try:
                with dest.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["keyword_id", "phrase", "locale", "device", "archived"])
                    for kid, phrase, locale, device, archived_at in rows:
                        writer.writerow(
                            [
                                int(kid),
                                str(phrase or ""),
                                str(locale or ""),
                                str(device or ""),
                                "" if archived_at is None else "yes",
                            ]
                        )
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(len(rows))))

    def _export_serp_snapshots_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export SERP snapshots"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(
                        SerpResult.id,
                        Keyword.phrase,
                        SerpResult.fetched_at,
                        SerpResult.status,
                        SerpResult.results_json,
                    )
                    .join(Keyword, SerpResult.keyword_id == Keyword.id)
                    .where(Keyword.project_id == self._current_project_id)
                    .order_by(SerpResult.fetched_at.desc())
                    .limit(500)
                )
                .all()
            )
            try:
                with dest.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["snapshot_id", "keyword", "fetched_at", "status", "organic_rows"])
                    for snapshot_id, phrase, fetched_at, status, results_json in rows:
                        writer.writerow(
                            [
                                int(snapshot_id),
                                str(phrase or ""),
                                "" if fetched_at is None else fetched_at.isoformat(),
                                str(status or ""),
                                int(serp_organic_count(results_json)),
                            ]
                        )
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(len(rows))))

    def _export_rank_history_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        kid = self._rank_kw_combo.currentData() if getattr(self, "_rank_kw_combo", None) else None
        if kid is None:
            QMessageBox.information(self, self.tr("Export"), self.tr("Select a keyword first."))
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export rank history"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            phrase = (
                s.execute(select(Keyword.phrase).where(Keyword.id == int(kid)).limit(1)).scalar_one_or_none() or ""
            )
            rows = (
                s.execute(
                    select(Ranking.tracked_at, Ranking.position, Ranking.degraded)
                    .where(Ranking.keyword_id == int(kid))
                    .order_by(Ranking.tracked_at.asc())
                    .limit(1000)
                )
                .all()
            )
            try:
                with dest.open("w", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow(["keyword_id", "keyword", "tracked_at", "position", "degraded"])
                    for tracked_at, position, degraded in rows:
                        writer.writerow(
                            [
                                int(kid),
                                str(phrase),
                                "" if tracked_at is None else tracked_at.isoformat(),
                                "" if position is None else int(position),
                                "yes" if degraded else "",
                            ]
                        )
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(len(rows))))

    def _export_pages_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export pages"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            try:
                n = export_pages_csv(s, self._current_project_id, dest)
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(n)))

    def _export_links_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export links"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            try:
                n = export_page_links_csv(s, self._current_project_id, dest)
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(n)))

    def _export_audits_csv_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export audits"), "", "*.csv")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            try:
                n = export_seo_audits_csv(s, self._current_project_id, dest)
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 rows.").replace("%1", str(n)))

    def _export_audits_json_dialog(self) -> None:
        if not self._current_project_id:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.tr("Export audits"), "", "*.json")
        if not path:
            return
        dest = Path(path)
        s = self._session()
        try:
            try:
                n = export_seo_audits_json(s, self._current_project_id, dest)
            except OSError as e:
                self._warn_export_write_failed(dest, e)
                return
        finally:
            s.close()
        QMessageBox.information(self, self.tr("Export"), self.tr("Exported %1 records.").replace("%1", str(n)))

    def _check_updates(self) -> None:
        self._pool.start(
            SimpleTaskWorker(
                "updates",
                self._bus,
                github_releases.fetch_latest_release,
                started_message=self.tr("Contacting GitHub…"),
            )
        )

    def _append_log(self, line: str) -> None:
        self._log.append(f"{datetime.now(UTC).isoformat()} {line}")

    def _set_progress_status(self, label: QLabel, text: str, *, state: str) -> None:
        label.setVisible(True)
        label.setText(text)
        label.setProperty("state", state)
        style = label.style()
        if style is not None:
            style.unpolish(label)
            style.polish(label)

    def _serp_finished_progress_state(self, summary: dict) -> tuple[str, str]:
        rid = summary.get("serp_result_id")
        if rid is None:
            return ("success", self.tr("Completed"))
        s = self._session()
        try:
            status = (
                s.execute(select(SerpResult.status).where(SerpResult.id == int(rid)).limit(1)).scalar_one_or_none()
                or ""
            )
        finally:
            s.close()
        return serp_progress_state_from_status(str(status), self.tr)

    def _citation_finished_progress_state(self, summary: dict) -> tuple[str, str]:
        return citation_progress_state_from_summary(summary, self.tr)

    def _on_job_progress(self, job_id: int, pct: float, msg: str) -> None:
        self._append_log(f"Job {job_id}: {pct:.0f}% {msg}")
        self._refresh_job_table()
        if job_id == self._crawl_active_job_id:
            self._crawl_progress.setVisible(True)
            self._crawl_progress.setRange(0, 100)
            self._crawl_progress.setValue(int(min(100, max(0, pct))))
            self._set_progress_status(self._crawl_status, msg, state="running")
        if job_id == self._audit_active_job_id:
            self._audit_progress.setVisible(True)
            self._audit_progress.setRange(0, 100)
            self._audit_progress.setValue(int(min(100, max(0, pct))))
            self._set_progress_status(self._audit_status, msg, state="running")
        if job_id == self._serp_active_job_id:
            self._serp_progress.setVisible(True)
            self._serp_progress.setRange(0, 100)
            self._serp_progress.setValue(int(min(100, max(0, pct))))
            self._set_progress_status(self._serp_status, msg, state="running")
        if job_id == self._citation_active_job_id:
            self._cit_progress.setVisible(True)
            self._cit_progress.setRange(0, 100)
            self._cit_progress.setValue(int(min(100, max(0, pct))))
            self._set_progress_status(self._cit_status, msg, state="running")

    def _on_job_finished(self, job_id: int, summary: dict) -> None:
        self._append_log(f"Job {job_id} finished: {json.dumps(summary)}")
        self._refresh_job_table()
        if job_id == self._crawl_active_job_id:
            self._crawl_active_job_id = None
            self._crawl_btn.setEnabled(True)
            self._set_progress_status(self._crawl_status, self.tr("Completed"), state="success")
            self._crawl_progress.setVisible(False)
            self._crawl_status.setVisible(False)
            self._refresh_crawl_pages_table()
            self._refresh_dashboard_stats()
            if summary.get("cancelled"):
                QMessageBox.information(self, self.tr("Crawl"), self.tr("Crawl cancelled."))
        if job_id == self._audit_active_job_id:
            self._audit_active_job_id = None
            self._audit_btn.setEnabled(True)
            self._set_progress_status(self._audit_status, self.tr("Completed"), state="success")
            self._audit_progress.setVisible(False)
            self._audit_status.setVisible(False)
            self._refresh_audit_results_table()
            self._refresh_dashboard_stats()
            if summary.get("cancelled"):
                QMessageBox.information(self, self.tr("Audit"), self.tr("Audit cancelled."))
        if job_id == self._serp_active_job_id and summary.get("type") == "serp":
            self._serp_active_job_id = None
            self._serp_btn.setEnabled(True)
            serp_state, serp_text = self._serp_finished_progress_state(summary)
            self._set_progress_status(self._serp_status, serp_text, state=serp_state)
            self._serp_progress.setVisible(False)
            self._serp_status.setVisible(serp_state == "degraded")
            self._refresh_serp_snapshots_table()
            self._rebuild_rank_chart()
            QMessageBox.information(self, self.tr("SERP"), self.tr("Snapshot stored (best-effort)."))
        if job_id == self._citation_active_job_id and summary.get("type") == "citation":
            self._citation_active_job_id = None
            if getattr(self, "_cit_run_btn", None):
                self._cit_run_btn.setEnabled(True)
            cit_state, cit_text = self._citation_finished_progress_state(summary)
            self._set_progress_status(self._cit_status, cit_text, state=cit_state)
            self._cit_progress.setVisible(False)
            self._cit_status.setVisible(cit_state == "degraded")
            self._refresh_citations_checks_table()
            self._refresh_dashboard_stats()
            if summary.get("cancelled"):
                QMessageBox.information(
                    self,
                    self.tr("Citations"),
                    self.tr("Citation matrix cancelled."),
                )
            else:
                ok = summary.get("http_ok", 0)
                err = summary.get("http_err", 0)
                sk = summary.get("skipped_playwright", 0)
                QMessageBox.information(
                    self,
                    self.tr("Citations"),
                    self.tr("Matrix finished: %1 OK HTTP, %2 errors, %3 skipped (Playwright).")
                    .replace("%1", str(ok))
                    .replace("%2", str(err))
                    .replace("%3", str(sk)),
                )

    def _on_job_failed(self, job_id: int, code: str, msg: str) -> None:
        self._append_log(f"Job {job_id} failed ({code}): {msg}")
        self._refresh_job_table()
        if job_id == self._crawl_active_job_id:
            self._crawl_active_job_id = None
            self._crawl_btn.setEnabled(True)
            self._set_progress_status(self._crawl_status, msg, state="failure")
            self._crawl_progress.setVisible(False)
            self._crawl_status.setVisible(False)
            self._refresh_crawl_pages_table()
            self._refresh_dashboard_stats()
            QMessageBox.warning(self, self.tr("Crawl"), f"{code}: {msg}")
        if job_id == self._audit_active_job_id:
            self._audit_active_job_id = None
            self._audit_btn.setEnabled(True)
            self._set_progress_status(self._audit_status, msg, state="failure")
            self._audit_progress.setVisible(False)
            self._audit_status.setVisible(False)
            self._refresh_audit_results_table()
            self._refresh_dashboard_stats()
            QMessageBox.warning(self, self.tr("Audit"), f"{code}: {msg}")
        if job_id == self._serp_active_job_id:
            self._serp_active_job_id = None
            self._serp_btn.setEnabled(True)
            self._set_progress_status(self._serp_status, msg, state="failure")
            self._serp_progress.setVisible(False)
            self._serp_status.setVisible(False)
            QMessageBox.warning(self, self.tr("SERP"), f"{code}: {msg}")
        if job_id == self._citation_active_job_id:
            self._citation_active_job_id = None
            if getattr(self, "_cit_run_btn", None):
                self._cit_run_btn.setEnabled(True)
            self._set_progress_status(self._cit_status, msg, state="failure")
            self._cit_progress.setVisible(False)
            self._cit_status.setVisible(False)
            QMessageBox.warning(self, self.tr("Citations"), f"{code}: {msg}")

    def _on_task_progress(self, task_id: str, pct: float, msg: str) -> None:
        if task_id == "updates":
            self.statusBar().showMessage(msg, 0)
        elif task_id == "export_md":
            self._reports_progress.setVisible(True)
            self._set_progress_status(self._reports_status, msg, state="running")
            if pct < 0:
                self._reports_progress.setRange(0, 0)
            else:
                self._reports_progress.setRange(0, 100)
                self._reports_progress.setValue(int(pct))

    def _on_task_finished(self, task_id: str, data: dict) -> None:
        if task_id == "updates":
            self.statusBar().clearMessage()
            rel = data.get("result") or {}
            tag = rel.get("tag_name", "?")
            QMessageBox.information(
                self,
                self.tr("Updates"),
                self.tr("Latest release: %1 (verify checksum before install).").replace("%1", str(tag)),
            )
        elif task_id == "export_md":
            self._export_btn.setEnabled(True)
            self._set_progress_status(self._reports_status, self.tr("Completed"), state="success")
            self._reports_progress.setVisible(False)
            self._reports_status.setVisible(False)
            self._reports_progress.setRange(0, 100)
            self._reports_progress.setValue(0)

    def _on_task_failed(self, task_id: str, code: str, msg: str) -> None:
        if task_id == "updates":
            self.statusBar().clearMessage()
            QMessageBox.warning(self, self.tr("Updates"), msg)
        elif task_id == "export_md":
            self._export_btn.setEnabled(True)
            self._set_progress_status(self._reports_status, msg, state="failure")
            self._reports_progress.setVisible(False)
            self._reports_status.setVisible(False)
            self._reports_progress.setRange(0, 100)
            self._reports_progress.setValue(0)
            QMessageBox.warning(self, self.tr("Export"), msg)

    def _refresh_job_table(self) -> None:
        s = self._session()
        try:
            jobs = s.execute(select(Job).order_by(Job.id.desc()).limit(50)).scalars().all()
            rows = build_job_rows(jobs)
            self._jobs_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                self._jobs_table.setItem(r, 0, QTableWidgetItem(row.job_id))
                self._jobs_table.setItem(r, 1, QTableWidgetItem(row.job_type))
                self._jobs_table.setItem(r, 2, QTableWidgetItem(row.progress_pct))
                self._jobs_table.setItem(r, 3, QTableWidgetItem(row.status_text))
                self._jobs_table.setCellWidget(
                    r,
                    3,
                    StatusPill(row.status_text or self.tr("unknown"), status=row.status_variant),
                )
                self._jobs_table.setItem(r, 4, QTableWidgetItem(row.project_id))
            running = sum(1 for j in jobs if j.status in {"queued", "running"})
            failed = sum(1 for j in jobs if j.status == "failed")
            text, variant = top_jobs_badge_text(running=running, failed=failed)
            self._top_jobs_badge.set_status(self.tr(text), status=variant)
        finally:
            s.close()
