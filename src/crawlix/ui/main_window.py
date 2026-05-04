"""Main application shell: sidebar, stacked pages, job dock, project switcher."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import QSettings, QThreadPool, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func, select
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
    SeoAudit,
    SerpResult,
)
from crawlix.db.session import make_engine
from crawlix.db.settings_store import get_value, set_value
from crawlix.services.citations.seed import seed_builtin_sources
from crawlix.services.analyzer.site_audit import inbound_internal_counts, outbound_internal_counts
from crawlix.services.exporters import (
    export_builtin_citation_sources_csv,
    export_page_links_csv,
    export_pages_csv,
    export_seo_audits_csv,
    export_seo_audits_json,
)
from crawlix.services.integrations import list_integration_placeholders
from crawlix.services.updater import github_releases
from crawlix.ui import onboarding
from crawlix.ui.project_dialog import NewProjectDialog
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
        self._setup_menu()
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        main_row = QWidget()
        m = QHBoxLayout(main_row)
        m.setContentsMargins(8, 8, 8, 0)

        self._nav = QListWidget()
        for label in (
            self.tr("Dashboard"),
            self.tr("Crawl"),
            self.tr("Audit"),
            self.tr("Keywords && SERP"),
            self.tr("Citations"),
            self.tr("Local"),
            self.tr("Integrations"),
            self.tr("Reports"),
            self.tr("Settings"),
        ):
            QListWidgetItem(label, self._nav)
        self._nav.setFixedWidth(200)
        self._nav.currentRowChanged.connect(self._on_nav)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_dashboard())
        self._stack.addWidget(self._page_crawl())
        self._stack.addWidget(self._page_audit())
        self._stack.addWidget(self._page_keywords())
        self._stack.addWidget(self._page_citations())
        self._stack.addWidget(self._page_local())
        self._stack.addWidget(self._page_integrations())
        self._stack.addWidget(self._page_reports())
        self._stack.addWidget(self._page_settings())

        top = QHBoxLayout()
        top.addWidget(QLabel(self.tr("Project:")))
        self._project_combo = QComboBox()
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)
        top.addWidget(self._project_combo, 1)

        right = QVBoxLayout()
        right.addLayout(top)
        right.addWidget(self._stack, 1)

        m.addWidget(self._nav)
        m.addLayout(right, 1)
        outer_layout.addWidget(main_row, 1)

        dock_wrap = QWidget()
        dw = QVBoxLayout(dock_wrap)
        dw.setContentsMargins(8, 0, 8, 8)
        dock_head = QWidget()
        dh = QHBoxLayout(dock_head)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.addWidget(QLabel(self.tr("Job dock")))
        dh.addStretch()
        self._cancel_job_btn = QPushButton(self.tr("Cancel selected job"))
        self._cancel_job_btn.clicked.connect(self._cancel_selected_job)
        dh.addWidget(self._cancel_job_btn)
        dw.addWidget(dock_head)
        tabs = QTabWidget()
        self._jobs_table = QTableWidget(0, 5)
        self._jobs_table.setHorizontalHeaderLabels(
            [self.tr("ID"), self.tr("Type"), self.tr("%"), self.tr("Status"), self.tr("Project")]
        )
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        tabs.addTab(self._jobs_table, self.tr("Jobs"))
        tabs.addTab(self._log, self.tr("Log"))
        dw.addWidget(tabs)
        outer_layout.addWidget(dock_wrap)

        self.setCentralWidget(outer)
        self._nav.setCurrentRow(0)

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
        m_help = self.menuBar().addMenu(self.tr("&Help"))
        act_updates = QAction(self.tr("&Check for updates…"), self)
        act_updates.triggered.connect(self._check_updates)
        m_help.addAction(act_updates)

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

    def _on_nav(self, row: int) -> None:
        self._stack.setCurrentIndex(max(0, row))

    def _on_project_changed(self) -> None:
        pid = self._project_combo.currentData()
        self._current_project_id = int(pid) if pid is not None else None
        self._refresh_dashboard_stats()
        self._refresh_crawl_pages_table()
        self._refresh_audit_results_table()
        self._refresh_keywords_table()
        self._refresh_serp_tab_lists()
        self._rebuild_rank_chart()
        self._refresh_citations_page()

    def _reload_projects_combo(self) -> None:
        self._project_combo.clear()
        s = self._session()
        try:
            for p in s.execute(select(Project).order_by(Project.name)).scalars():
                self._project_combo.addItem(p.name, p.id)
        finally:
            s.close()
        if self._project_combo.count():
            self._current_project_id = int(self._project_combo.itemData(0))
        self._refresh_dashboard_stats()
        self._refresh_crawl_pages_table()
        self._refresh_audit_results_table()
        self._refresh_keywords_table()
        self._refresh_serp_tab_lists()
        self._rebuild_rank_chart()
        self._refresh_citations_page()

    def _page_header(self, title: str, subtitle: str | None = None) -> QWidget:
        """Plain-text page title (avoid HTML auto-rich-text that breaks contrast)."""
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 10)
        t = QLabel(title)
        tf = QFont(t.font())
        tf.setPointSize(15)
        tf.setBold(True)
        t.setFont(tf)
        v.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setWordWrap(True)
            v.addWidget(s)
        return box

    def _page_dashboard(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(self._page_header(self.tr("Dashboard")))
        l.addWidget(
            QLabel(
                self.tr("Overview for this project — run Crawl, Audit, or Keywords from the sidebar.")
            )
        )
        self._dash_stats = QLabel("")
        self._dash_stats.setWordWrap(True)
        l.addWidget(self._dash_stats)
        db = QPushButton(self.tr("Refresh summary"))
        db.clicked.connect(self._refresh_dashboard_stats)
        l.addWidget(db)
        l.addStretch()
        return w

    def _page_crawl(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            self._page_header(
                self.tr("Crawl"),
                self.tr("Map pages and links; depth and internal in/out counts reflect the crawl graph."),
            )
        )
        self._crawl_seeds = QLineEdit("https://example.com/")
        self._crawl_depth = QSpinBox()
        self._crawl_depth.setRange(0, 5)
        self._crawl_depth.setValue(1)
        form = QFormLayout()
        form.addRow(self.tr("Seed URLs (comma-separated):"), self._crawl_seeds)
        form.addRow(self.tr("Max depth:"), self._crawl_depth)
        l.addLayout(form)
        self._crawl_btn = QPushButton(self.tr("Start crawl"))
        self._crawl_btn.clicked.connect(self._start_crawl)
        l.addWidget(self._crawl_btn)
        self._crawl_progress = QProgressBar()
        self._crawl_progress.setRange(0, 100)
        self._crawl_progress.setTextVisible(True)
        self._crawl_progress.setVisible(False)
        self._crawl_status = QLabel("")
        self._crawl_status.setWordWrap(True)
        self._crawl_status.setVisible(False)
        l.addWidget(self._crawl_progress)
        l.addWidget(self._crawl_status)
        crawl_btns = QHBoxLayout()
        rb = QPushButton(self.tr("Refresh pages list"))
        rb.clicked.connect(self._refresh_crawl_pages_table)
        crawl_btns.addWidget(rb)
        ep = QPushButton(self.tr("Export pages CSV…"))
        ep.clicked.connect(self._export_pages_csv_dialog)
        crawl_btns.addWidget(ep)
        el = QPushButton(self.tr("Export links CSV…"))
        el.clicked.connect(self._export_links_csv_dialog)
        crawl_btns.addWidget(el)
        crawl_btns.addStretch()
        l.addLayout(crawl_btns)
        self._crawl_pages_table = QTableWidget(0, 8)
        self._crawl_pages_table.setHorizontalHeaderLabels(
            [
                self.tr("ID"),
                self.tr("URL"),
                self.tr("Title"),
                self.tr("HTTP"),
                self.tr("Depth"),
                self.tr("In"),
                self.tr("Out"),
                self.tr("Last crawled"),
            ]
        )
        self._crawl_pages_table.setColumnWidth(1, 320)
        l.addWidget(self._crawl_pages_table, 1)
        return w

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
        self._crawl_status.setText(self.tr("Queued…"))
        self._crawl_status.setVisible(True)
        w = CrawlWorker(jid, self._engine, self._bus, job_key=f"crawl-{jid}")
        self._pool.start(w)
        self._refresh_job_table()

    def _page_audit(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            self._page_header(
                self.tr("Audit"),
                self.tr("Scores, issues, crawl depth, and internal in/out link counts from the last crawl graph."),
            )
        )
        self._audit_btn = QPushButton(self.tr("Run audit on crawled pages"))
        self._audit_btn.clicked.connect(self._start_audit)
        l.addWidget(self._audit_btn)
        self._audit_progress = QProgressBar()
        self._audit_progress.setRange(0, 100)
        self._audit_progress.setTextVisible(True)
        self._audit_progress.setVisible(False)
        self._audit_status = QLabel("")
        self._audit_status.setWordWrap(True)
        self._audit_status.setVisible(False)
        l.addWidget(self._audit_progress)
        l.addWidget(self._audit_status)
        aud_btns = QHBoxLayout()
        ar = QPushButton(self.tr("Refresh audit results"))
        ar.clicked.connect(self._refresh_audit_results_table)
        aud_btns.addWidget(ar)
        ea = QPushButton(self.tr("Export audits CSV…"))
        ea.clicked.connect(self._export_audits_csv_dialog)
        aud_btns.addWidget(ea)
        ej = QPushButton(self.tr("Export audits JSON…"))
        ej.clicked.connect(self._export_audits_json_dialog)
        aud_btns.addWidget(ej)
        aud_btns.addStretch()
        l.addLayout(aud_btns)
        self._audit_results_table = QTableWidget(0, 8)
        self._audit_results_table.setHorizontalHeaderLabels(
            [
                self.tr("Audit ID"),
                self.tr("Page ID"),
                self.tr("URL"),
                self.tr("Depth"),
                self.tr("In"),
                self.tr("Out"),
                self.tr("Score"),
                self.tr("Issues"),
            ]
        )
        self._audit_results_table.setColumnWidth(2, 280)
        l.addWidget(self._audit_results_table, 1)
        return w

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
            job = Job(
                project_id=self._current_project_id,
                type="audit",
                status="queued",
                progress_pct=0,
                payload_json={"page_ids": list(pages)},
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
        self._audit_status.setText(self.tr("Queued…"))
        self._audit_status.setVisible(True)
        self._pool.start(AuditWorker(jid, self._engine, self._bus))
        self._refresh_job_table()

    def _page_keywords(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            self._page_header(
                self.tr("Keywords && SERP"),
                self.tr("Keywords, SERP snapshots, rank history."),
            )
        )
        tabs = QTabWidget()
        kw_tab = QWidget()
        kvl = QVBoxLayout(kw_tab)
        self._kw_phrase = QLineEdit()
        kf = QFormLayout()
        kf.addRow(self.tr("New keyword:"), self._kw_phrase)
        krow = QHBoxLayout()
        kb = QPushButton(self.tr("Add keyword"))
        kb.clicked.connect(self._add_keyword)
        krow.addWidget(kb)
        kr = QPushButton(self.tr("Refresh keywords"))
        kr.clicked.connect(self._refresh_keywords_table)
        krow.addWidget(kr)
        krow.addStretch()
        kvl.addLayout(kf)
        kvl.addLayout(krow)
        self._kw_table = QTableWidget(0, 5)
        self._kw_table.setHorizontalHeaderLabels(
            [self.tr("ID"), self.tr("Phrase"), self.tr("Locale"), self.tr("Device"), self.tr("Archived")]
        )
        self._kw_table.setColumnWidth(1, 360)
        kvl.addWidget(self._kw_table, 1)
        tabs.addTab(kw_tab, self.tr("Keywords"))

        serp_tab = QWidget()
        svl = QVBoxLayout(serp_tab)
        sk = QHBoxLayout()
        sk.addWidget(QLabel(self.tr("Keyword for snapshot:")))
        self._serp_kw_combo = QComboBox()
        sk.addWidget(self._serp_kw_combo, 1)
        skr = QPushButton(self.tr("Refresh lists"))
        skr.clicked.connect(self._refresh_serp_tab_lists)
        sk.addWidget(skr)
        svl.addLayout(sk)
        self._serp_btn = QPushButton(self.tr("Run SERP snapshot (demo parser)"))
        self._serp_btn.clicked.connect(self._run_serp)
        svl.addWidget(self._serp_btn)
        self._serp_progress = QProgressBar()
        self._serp_progress.setRange(0, 100)
        self._serp_progress.setTextVisible(True)
        self._serp_progress.setVisible(False)
        self._serp_status = QLabel("")
        self._serp_status.setWordWrap(True)
        self._serp_status.setVisible(False)
        svl.addWidget(self._serp_progress)
        svl.addWidget(self._serp_status)
        self._serp_snapshots_table = QTableWidget(0, 5)
        self._serp_snapshots_table.setHorizontalHeaderLabels(
            [
                self.tr("Snapshot ID"),
                self.tr("Keyword"),
                self.tr("Fetched"),
                self.tr("Status"),
                self.tr("Organic rows"),
            ]
        )
        self._serp_snapshots_table.setColumnWidth(1, 220)
        svl.addWidget(self._serp_snapshots_table, 1)
        tabs.addTab(serp_tab, self.tr("SERP snapshots"))

        rank_tab = QWidget()
        rvl = QVBoxLayout(rank_tab)
        rr = QHBoxLayout()
        rrb = QPushButton(self.tr("Refresh chart"))
        rrb.clicked.connect(self._rebuild_rank_chart)
        rr.addWidget(rrb)
        rr.addStretch()
        rvl.addLayout(rr)
        s_theme = self._session()
        try:
            chart_theme = get_value(s_theme, "ui_theme", "dark") or "dark"
        finally:
            s_theme.close()
        self._rank_fig = Figure(figsize=(6, 3.2))
        self._rank_chart_theme = chart_theme
        self._rank_canvas = FigureCanvasQTAgg(self._rank_fig)
        rvl.addWidget(self._rank_canvas, 1)
        tabs.addTab(rank_tab, self.tr("Rank history"))
        self._rebuild_rank_chart()

        l.addWidget(tabs)
        return w

    def _refresh_serp_tab_lists(self) -> None:
        self._refresh_serp_keyword_combo()
        self._refresh_serp_snapshots_table()

    def _refresh_keywords_table(self) -> None:
        if not getattr(self, "_kw_table", None):
            return
        if not self._current_project_id:
            self._kw_table.setRowCount(0)
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

    def _refresh_serp_keyword_combo(self) -> None:
        if not getattr(self, "_serp_kw_combo", None):
            return
        self._serp_kw_combo.blockSignals(True)
        self._serp_kw_combo.clear()
        if not self._current_project_id:
            self._serp_kw_combo.addItem(self.tr("(select a project)"), None)
            self._serp_kw_combo.blockSignals(False)
            return
        s = self._session()
        try:
            kws = (
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
            for k in kws:
                self._serp_kw_combo.addItem(k.phrase[:120], k.id)
            if not kws:
                self._serp_kw_combo.addItem(self.tr("(add a keyword first)"), None)
        finally:
            s.close()
        self._serp_kw_combo.blockSignals(False)

    def _refresh_serp_snapshots_table(self) -> None:
        if not getattr(self, "_serp_snapshots_table", None):
            return
        if not self._current_project_id:
            self._serp_snapshots_table.setRowCount(0)
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
            for r, (sr, phrase) in enumerate(rows):
                organic = (sr.results_json or {}).get("organic") or []
                n_org = len(organic) if isinstance(organic, list) else 0
                self._serp_snapshots_table.setItem(r, 0, QTableWidgetItem(str(sr.id)))
                self._serp_snapshots_table.setItem(r, 1, QTableWidgetItem(phrase))
                fts = sr.fetched_at.isoformat() if sr.fetched_at else ""
                self._serp_snapshots_table.setItem(r, 2, QTableWidgetItem(fts))
                self._serp_snapshots_table.setItem(r, 3, QTableWidgetItem(sr.status))
                self._serp_snapshots_table.setItem(r, 4, QTableWidgetItem(str(n_org)))
        finally:
            s.close()

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
        ax.set_title(self.tr("SERP organic row count over snapshots (project)"))
        ax.set_xlabel(self.tr("Snapshot index (oldest → newest)"))
        ax.set_ylabel(self.tr("Organic URLs parsed"))
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
        s = self._session()
        try:
            pts = (
                s.execute(
                    select(SerpResult.fetched_at, SerpResult.results_json)
                    .join(Keyword, SerpResult.keyword_id == Keyword.id)
                    .where(Keyword.project_id == self._current_project_id)
                    .order_by(SerpResult.fetched_at.asc())
                    .limit(100)
                )
                .all()
            )
        finally:
            s.close()
        if not pts:
            ax.text(
                0.5,
                0.5,
                self.tr("No SERP snapshots yet — run a snapshot from the SERP tab."),
                transform=ax.transAxes,
                ha="center",
                va="center",
                color=ax.title.get_color(),
            )
            self._rank_canvas.draw()
            return
        ys: list[int] = []
        for _ft, rj in pts:
            organic = (rj or {}).get("organic") or []
            ys.append(len(organic) if isinstance(organic, list) else 0)
        xs = list(range(1, len(ys) + 1))
        ax.plot(xs, ys, color=line_c, marker="o", markersize=3)
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
        self._serp_status.setText(self.tr("Queued…"))
        self._serp_status.setVisible(True)
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
                self.tr("This project has no locations yet. Add one when creating a project or wait for a location editor."),
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
                "HTTP requests will be sent to third-party sites—only continue if that is allowed for you and you accept rate-limit responsibility. Proceed?"
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
        self._cit_status.setText(self.tr("Queued…"))
        self._cit_status.setVisible(True)
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
            for r, (chk, loc_label, src_name) in enumerate(rows):
                when = chk.fetched_at.isoformat() if chk.fetched_at else ""
                fu = chk.final_url or chk.requested_url or ""
                if len(fu) > 80:
                    fu = fu[:77] + "…"
                err = (chk.error_text or "")[:120]
                self._cit_chk_table.setItem(r, 0, QTableWidgetItem(str(chk.id)))
                self._cit_chk_table.setItem(r, 1, QTableWidgetItem(when))
                self._cit_chk_table.setItem(r, 2, QTableWidgetItem(loc_label))
                self._cit_chk_table.setItem(r, 3, QTableWidgetItem(src_name))
                self._cit_chk_table.setItem(r, 4, QTableWidgetItem(chk.status or ""))
                self._cit_chk_table.setItem(
                    r, 5, QTableWidgetItem("" if chk.http_status is None else str(chk.http_status))
                )
                self._cit_chk_table.setItem(r, 6, QTableWidgetItem(fu))
                self._cit_chk_table.setItem(r, 7, QTableWidgetItem(err))
        finally:
            s.close()

    def _refresh_citations_page(self) -> None:
        self._refresh_citations_builtin_table()
        self._refresh_citations_locations_table()
        self._refresh_citations_checks_table()

    def _page_citations(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            self._page_header(
                self.tr("Citations"),
                self.tr(
                    "Built-in directory templates (YAML → DB), project NAP locations, and any stored citation checks."
                ),
            )
        )
        l.addWidget(
            QLabel(
                self.tr(
                    "Run a citation matrix job to record one row per (location × built-in source): "
                    "HTTP GET for templates that do not require Playwright; Playwright-only sources are recorded as skipped."
                )
            )
        )
        mrow = QHBoxLayout()
        self._cit_run_btn = QPushButton(self.tr("Run citation matrix (HTTP)…"))
        self._cit_run_btn.clicked.connect(self._run_citation_matrix)
        mrow.addWidget(self._cit_run_btn)
        self._cit_progress = QProgressBar()
        self._cit_progress.setRange(0, 100)
        self._cit_progress.setTextVisible(True)
        self._cit_progress.setVisible(False)
        mrow.addWidget(self._cit_progress, 1)
        l.addLayout(mrow)
        self._cit_status = QLabel("")
        self._cit_status.setWordWrap(True)
        self._cit_status.setVisible(False)
        l.addWidget(self._cit_status)
        tabs = QTabWidget()
        src_tab = QWidget()
        sv = QVBoxLayout(src_tab)
        srow = QHBoxLayout()
        sref = QPushButton(self.tr("Refresh built-in list"))
        sref.clicked.connect(self._refresh_citations_builtin_table)
        srow.addWidget(sref)
        sex = QPushButton(self.tr("Export built-in sources CSV…"))
        sex.clicked.connect(self._export_builtin_citations_csv)
        srow.addWidget(sex)
        srow.addStretch()
        sv.addLayout(srow)
        self._cit_src_table = QTableWidget(0, 7)
        self._cit_src_table.setHorizontalHeaderLabels(
            [
                self.tr("ID"),
                self.tr("Name"),
                self.tr("Template URL"),
                self.tr("Regions"),
                self.tr("Playwright"),
                self.tr("Enabled"),
                self.tr("Pack"),
            ]
        )
        self._cit_src_table.setColumnWidth(2, 420)
        sv.addWidget(self._cit_src_table, 1)
        tabs.addTab(src_tab, self.tr("Built-in sources"))

        loc_tab = QWidget()
        lv = QVBoxLayout(loc_tab)
        lv.addWidget(
            QLabel(
                self.tr(
                    "Locations belong to the current project (optional NAP at project creation in J3; dedicated editor later)."
                )
            )
        )
        lref = QPushButton(self.tr("Refresh locations"))
        lref.clicked.connect(self._refresh_citations_locations_table)
        lv.addWidget(lref)
        self._cit_loc_table = QTableWidget(0, 7)
        self._cit_loc_table.setHorizontalHeaderLabels(
            [
                self.tr("ID"),
                self.tr("Label"),
                self.tr("Business name"),
                self.tr("Address"),
                self.tr("City"),
                self.tr("Region"),
                self.tr("Phone"),
            ]
        )
        self._cit_loc_table.setColumnWidth(2, 220)
        lv.addWidget(self._cit_loc_table, 1)
        tabs.addTab(loc_tab, self.tr("Locations (NAP)"))

        chk_tab = QWidget()
        cv = QVBoxLayout(chk_tab)
        cv.addWidget(
            QLabel(self.tr("Latest citation check rows for this project’s locations (newest first, up to 500)."))
        )
        cref = QPushButton(self.tr("Refresh check history"))
        cref.clicked.connect(self._refresh_citations_checks_table)
        cv.addWidget(cref)
        self._cit_chk_table = QTableWidget(0, 8)
        self._cit_chk_table.setHorizontalHeaderLabels(
            [
                self.tr("Check ID"),
                self.tr("Fetched"),
                self.tr("Location"),
                self.tr("Source"),
                self.tr("Status"),
                self.tr("HTTP"),
                self.tr("Final URL"),
                self.tr("Error"),
            ]
        )
        self._cit_chk_table.setColumnWidth(6, 320)
        cv.addWidget(self._cit_chk_table, 1)
        tabs.addTab(chk_tab, self.tr("Check history"))

        l.addWidget(tabs, 1)
        all_ref = QPushButton(self.tr("Refresh all citations tabs"))
        all_ref.clicked.connect(self._refresh_citations_page)
        l.addWidget(all_ref)
        return w

    def _page_local(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(self._page_header(self.tr("Local")))
        l.addWidget(
            QLabel(
                self.tr(
                    "GBP / local pack — placeholder UI. Honest scope: official APIs and user-supplied evidence; "
                    "no implied unsupported scraping."
                )
            )
        )
        l.addWidget(
            QLabel(
                self.tr(
                    "Planned checklist direction:\n"
                    "• NAP consistency across on-site and major listings (manual or API-backed).\n"
                    "• GBP profile completeness (hours, categories, services) — link to official tools.\n"
                    "• Local pack / map visibility only where SERP captures or third-party data allow defensible reads.\n"
                    "• Review and Q&A hygiene — policy-first guidance.\n\n"
                    "See docs/local-pack-roadmap.md for product constraints."
                )
            )
        )
        return w

    def _page_integrations(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(self._page_header(self.tr("Integrations")))
        for st in list_integration_placeholders():
            l.addWidget(QLabel(f"{st.provider.upper()} — {self.tr('Not connected')}"))
        return w

    def _page_reports(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(self._page_header(self.tr("Reports")))
        self._export_btn = QPushButton(self.tr("Export sample Markdown"))
        self._export_btn.clicked.connect(self._export_md)
        l.addWidget(self._export_btn)
        self._reports_progress = QProgressBar()
        self._reports_progress.setRange(0, 0)
        self._reports_progress.setTextVisible(False)
        self._reports_progress.setVisible(False)
        self._reports_status = QLabel("")
        self._reports_status.setVisible(False)
        l.addWidget(self._reports_progress)
        l.addWidget(self._reports_status)
        return w

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
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(self._page_header(self.tr("Settings")))
        self._theme_combo = QComboBox()
        self._theme_combo.addItems([self.tr("Dark"), self.tr("Light")])
        s = self._session()
        try:
            cur = get_value(s, "ui_theme", "dark") or "dark"
        finally:
            s.close()
        self._theme_combo.blockSignals(True)
        self._theme_combo.setCurrentIndex(1 if cur == "light" else 0)
        self._theme_combo.blockSignals(False)
        self._theme_combo.currentIndexChanged.connect(self._save_theme)
        lf = QFormLayout()
        lf.addRow(self.tr("Theme:"), self._theme_combo)
        l.addLayout(lf)
        self._ollama_url = QLineEdit()
        self._ollama_en = QCheckBox(self.tr("Enable Ollama for AI features"))
        s_ol = self._session()
        try:
            self._ollama_url.setText(
                get_value(s_ol, "ollama_base_url", "http://127.0.0.1:11434") or "http://127.0.0.1:11434"
            )
            self._ollama_en.setChecked(get_value(s_ol, "ollama_enabled", "0") == "1")
        finally:
            s_ol.close()
        olf = QFormLayout()
        olf.addRow(self.tr("Ollama base URL:"), self._ollama_url)
        olf.addRow("", self._ollama_en)
        l.addLayout(olf)
        ob = QPushButton(self.tr("Save Ollama settings"))
        ob.clicked.connect(self._save_ollama_settings)
        l.addWidget(ob)
        l.addWidget(
            QLabel(
                self.tr(
                    "Politeness defaults: same-host ~3–5s jitter, 1 conn/host, 4 concurrent hosts — README."
                )
            )
        )
        return w

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
            return
        s = self._session()
        try:
            n_pages = (
                s.scalar(select(func.count()).select_from(Page).where(Page.project_id == self._current_project_id))
                or 0
            )
            n_jobs = (
                s.scalar(select(func.count()).select_from(Job).where(Job.project_id == self._current_project_id))
                or 0
            )
            n_audits = s.scalar(
                select(func.count())
                .select_from(SeoAudit)
                .join(Page, SeoAudit.page_id == Page.id)
                .where(Page.project_id == self._current_project_id)
            ) or 0
            last_c = s.scalar(
                select(func.max(Page.last_crawled_at)).where(Page.project_id == self._current_project_id)
            )
            last_s = last_c.isoformat() if last_c else self.tr("never")
            self._dash_stats.setText(
                self.tr("Pages: %1 — Jobs (all types): %2 — Audits: %3 — Last page crawl: %4")
                .replace("%1", str(n_pages))
                .replace("%2", str(n_jobs))
                .replace("%3", str(n_audits))
                .replace("%4", last_s)
            )
        finally:
            s.close()

    def _refresh_crawl_pages_table(self) -> None:
        if not getattr(self, "_crawl_pages_table", None):
            return
        if not self._current_project_id:
            self._crawl_pages_table.setRowCount(0)
            return
        s = self._session()
        try:
            pages = (
                s.execute(
                    select(Page)
                    .where(Page.project_id == self._current_project_id)
                    .order_by(Page.id.desc())
                    .limit(500)
                )
                .scalars()
                .all()
            )
            self._crawl_pages_table.setRowCount(len(pages))
            url_norms = [p.url_norm for p in pages]
            pages_by_id = {p.id: p.url_norm for p in pages}
            in_map = inbound_internal_counts(s, self._current_project_id, url_norms)
            out_map = outbound_internal_counts(s, self._current_project_id, pages_by_id)
            for r, p in enumerate(pages):
                self._crawl_pages_table.setItem(r, 0, QTableWidgetItem(str(p.id)))
                self._crawl_pages_table.setItem(r, 1, QTableWidgetItem(p.url_norm))
                self._crawl_pages_table.setItem(r, 2, QTableWidgetItem((p.title or "")[:120]))
                self._crawl_pages_table.setItem(
                    r, 3, QTableWidgetItem("" if p.status_code is None else str(p.status_code))
                )
                self._crawl_pages_table.setItem(
                    r, 4, QTableWidgetItem("" if p.crawl_depth is None else str(p.crawl_depth))
                )
                nin = in_map.get(p.url_norm, 0)
                nout = out_map.get(p.id, 0)
                self._crawl_pages_table.setItem(r, 5, QTableWidgetItem(str(nin)))
                self._crawl_pages_table.setItem(r, 6, QTableWidgetItem(str(nout)))
                ts = p.last_crawled_at.isoformat() if p.last_crawled_at else ""
                self._crawl_pages_table.setItem(r, 7, QTableWidgetItem(ts))
        finally:
            s.close()

    def _refresh_audit_results_table(self) -> None:
        if not getattr(self, "_audit_results_table", None):
            return
        if not self._current_project_id:
            self._audit_results_table.setRowCount(0)
            return
        s = self._session()
        try:
            rows = (
                s.execute(
                    select(SeoAudit, Page)
                    .join(Page, SeoAudit.page_id == Page.id)
                    .where(Page.project_id == self._current_project_id)
                    .order_by(SeoAudit.audited_at.desc())
                    .limit(200)
                )
                .all()
            )
            self._audit_results_table.setRowCount(len(rows))
            url_norms_a = [page.url_norm for _audit, page in rows]
            pages_by_id_a = {page.id: page.url_norm for _audit, page in rows}
            in_map_a = inbound_internal_counts(s, self._current_project_id, url_norms_a)
            out_map_a = outbound_internal_counts(s, self._current_project_id, pages_by_id_a)
            for r, (audit, page) in enumerate(rows):
                issues = audit.issues_json or []
                n_issues = len(issues) if isinstance(issues, list) else 0
                self._audit_results_table.setItem(r, 0, QTableWidgetItem(str(audit.id)))
                self._audit_results_table.setItem(r, 1, QTableWidgetItem(str(audit.page_id)))
                self._audit_results_table.setItem(r, 2, QTableWidgetItem(page.url_norm))
                self._audit_results_table.setItem(
                    r, 3, QTableWidgetItem("" if page.crawl_depth is None else str(page.crawl_depth))
                )
                nin = in_map_a.get(page.url_norm, 0)
                nout = out_map_a.get(page.id, 0)
                self._audit_results_table.setItem(r, 4, QTableWidgetItem(str(nin)))
                self._audit_results_table.setItem(r, 5, QTableWidgetItem(str(nout)))
                sc = "" if audit.overall_score is None else f"{audit.overall_score:.1f}"
                self._audit_results_table.setItem(r, 6, QTableWidgetItem(sc))
                self._audit_results_table.setItem(r, 7, QTableWidgetItem(str(n_issues)))
        finally:
            s.close()

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

    def _on_job_progress(self, job_id: int, pct: float, msg: str) -> None:
        self._append_log(f"Job {job_id}: {pct:.0f}% {msg}")
        self._refresh_job_table()
        if job_id == self._crawl_active_job_id:
            self._crawl_progress.setVisible(True)
            self._crawl_progress.setRange(0, 100)
            self._crawl_progress.setValue(int(min(100, max(0, pct))))
            self._crawl_status.setVisible(True)
            self._crawl_status.setText(msg)
        if job_id == self._audit_active_job_id:
            self._audit_progress.setVisible(True)
            self._audit_progress.setRange(0, 100)
            self._audit_progress.setValue(int(min(100, max(0, pct))))
            self._audit_status.setVisible(True)
            self._audit_status.setText(msg)
        if job_id == self._serp_active_job_id:
            self._serp_progress.setVisible(True)
            self._serp_progress.setRange(0, 100)
            self._serp_progress.setValue(int(min(100, max(0, pct))))
            self._serp_status.setVisible(True)
            self._serp_status.setText(msg)
        if job_id == self._citation_active_job_id:
            self._cit_progress.setVisible(True)
            self._cit_progress.setRange(0, 100)
            self._cit_progress.setValue(int(min(100, max(0, pct))))
            self._cit_status.setVisible(True)
            self._cit_status.setText(msg)

    def _on_job_finished(self, job_id: int, summary: dict) -> None:
        self._append_log(f"Job {job_id} finished: {json.dumps(summary)}")
        self._refresh_job_table()
        if job_id == self._crawl_active_job_id:
            self._crawl_active_job_id = None
            self._crawl_btn.setEnabled(True)
            self._crawl_progress.setVisible(False)
            self._crawl_status.setVisible(False)
            self._refresh_crawl_pages_table()
            self._refresh_dashboard_stats()
            if summary.get("cancelled"):
                QMessageBox.information(self, self.tr("Crawl"), self.tr("Crawl cancelled."))
        if job_id == self._audit_active_job_id:
            self._audit_active_job_id = None
            self._audit_btn.setEnabled(True)
            self._audit_progress.setVisible(False)
            self._audit_status.setVisible(False)
            self._refresh_audit_results_table()
            self._refresh_dashboard_stats()
            if summary.get("cancelled"):
                QMessageBox.information(self, self.tr("Audit"), self.tr("Audit cancelled."))
        if job_id == self._serp_active_job_id and summary.get("type") == "serp":
            self._serp_active_job_id = None
            self._serp_btn.setEnabled(True)
            self._serp_progress.setVisible(False)
            self._serp_status.setVisible(False)
            self._refresh_serp_snapshots_table()
            self._rebuild_rank_chart()
            QMessageBox.information(self, self.tr("SERP"), self.tr("Snapshot stored (best-effort)."))
        if job_id == self._citation_active_job_id and summary.get("type") == "citation":
            self._citation_active_job_id = None
            if getattr(self, "_cit_run_btn", None):
                self._cit_run_btn.setEnabled(True)
            self._cit_progress.setVisible(False)
            self._cit_status.setVisible(False)
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
            self._crawl_progress.setVisible(False)
            self._crawl_status.setVisible(False)
            self._refresh_crawl_pages_table()
            self._refresh_dashboard_stats()
            QMessageBox.warning(self, self.tr("Crawl"), f"{code}: {msg}")
        if job_id == self._audit_active_job_id:
            self._audit_active_job_id = None
            self._audit_btn.setEnabled(True)
            self._audit_progress.setVisible(False)
            self._audit_status.setVisible(False)
            self._refresh_audit_results_table()
            self._refresh_dashboard_stats()
            QMessageBox.warning(self, self.tr("Audit"), f"{code}: {msg}")
        if job_id == self._serp_active_job_id:
            self._serp_active_job_id = None
            self._serp_btn.setEnabled(True)
            self._serp_progress.setVisible(False)
            self._serp_status.setVisible(False)
            QMessageBox.warning(self, self.tr("SERP"), f"{code}: {msg}")
        if job_id == self._citation_active_job_id:
            self._citation_active_job_id = None
            if getattr(self, "_cit_run_btn", None):
                self._cit_run_btn.setEnabled(True)
            self._cit_progress.setVisible(False)
            self._cit_status.setVisible(False)
            QMessageBox.warning(self, self.tr("Citations"), f"{code}: {msg}")

    def _on_task_progress(self, task_id: str, pct: float, msg: str) -> None:
        if task_id == "updates":
            self.statusBar().showMessage(msg, 0)
        elif task_id == "export_md":
            self._reports_progress.setVisible(True)
            self._reports_status.setVisible(True)
            self._reports_status.setText(msg)
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
            self._reports_progress.setVisible(False)
            self._reports_status.setVisible(False)
            self._reports_progress.setRange(0, 100)
            self._reports_progress.setValue(0)
            QMessageBox.warning(self, self.tr("Export"), msg)

    def _refresh_job_table(self) -> None:
        s = self._session()
        try:
            jobs = s.execute(select(Job).order_by(Job.id.desc()).limit(50)).scalars().all()
            self._jobs_table.setRowCount(len(jobs))
            for r, j in enumerate(jobs):
                self._jobs_table.setItem(r, 0, QTableWidgetItem(str(j.id)))
                self._jobs_table.setItem(r, 1, QTableWidgetItem(j.type))
                self._jobs_table.setItem(r, 2, QTableWidgetItem(f"{j.progress_pct:.0f}"))
                self._jobs_table.setItem(r, 3, QTableWidgetItem(j.status))
                self._jobs_table.setItem(r, 4, QTableWidgetItem(str(j.project_id)))
        finally:
            s.close()
