"""Application-wide theme: Fusion + QSS so dialogs/wizards match and stay readable."""

from __future__ import annotations

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from crawlix.ui.styles import load_stylesheet


def apply_application_palette(app: QApplication) -> None:
    """Fusion avoids Windows native dark/light quirks mixing with QSS."""
    app.setStyle("Fusion")


def apply_application_theme(app: QApplication, *, mode: str | None = None) -> None:
    """Set stylesheet on the QApplication so QWizard/QDialog inherit before MainWindow exists."""
    if mode is None:
        qs = QSettings("COWEBS", "Crawlix")
        mode = (qs.value("ui_theme", "dark", str) or "dark").lower()
    if mode not in ("dark", "light"):
        mode = "dark"
    app.setStyleSheet(load_stylesheet(mode))


def sync_theme_to_qsettings(mode: str) -> None:
    qs = QSettings("COWEBS", "Crawlix")
    qs.setValue("ui_theme", mode)
