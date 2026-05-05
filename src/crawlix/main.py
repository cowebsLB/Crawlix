"""Application entry — PyQt6."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from crawlix.ui.main_window import MainWindow
from crawlix.ui.theme import apply_application_palette, apply_application_theme
from crawlix.ui.wheel_guard import install_app_wheel_step_blocker


def main() -> int:
    app = QApplication(sys.argv)
    install_app_wheel_step_blocker(app)
    apply_application_palette(app)
    apply_application_theme(app)
    win = MainWindow()
    if not win._ok:  # noqa: SLF001
        return 0
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
