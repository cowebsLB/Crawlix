"""UI page modules extracted from MainWindow."""

from crawlix.ui.pages.audit_page import AuditPageRefs, build_audit_page
from crawlix.ui.pages.citations_page import CitationsPageRefs, build_citations_page
from crawlix.ui.pages.crawl_page import build_crawl_page
from crawlix.ui.pages.dashboard_page import DashboardPageRefs, build_dashboard_page
from crawlix.ui.pages.integrations_page import build_integrations_page
from crawlix.ui.pages.keywords_page import KeywordsPageRefs, build_keywords_page
from crawlix.ui.pages.local_page import build_local_page
from crawlix.ui.pages.reports_page import ReportsPageRefs, build_reports_page
from crawlix.ui.pages.settings_page import SettingsPageRefs, build_settings_page

__all__ = (
    "AuditPageRefs",
    "CitationsPageRefs",
    "DashboardPageRefs",
    "KeywordsPageRefs",
    "ReportsPageRefs",
    "SettingsPageRefs",
    "build_audit_page",
    "build_citations_page",
    "build_crawl_page",
    "build_dashboard_page",
    "build_integrations_page",
    "build_keywords_page",
    "build_local_page",
    "build_reports_page",
    "build_settings_page",
)
