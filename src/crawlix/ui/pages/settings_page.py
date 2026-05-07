"""Settings page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget

from crawlix.ui.components import MethodologyPanel, SectionCard


@dataclass
class SettingsPageRefs:
    theme_combo: QComboBox
    ollama_url: QLineEdit
    ollama_en: QCheckBox


def build_settings_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    theme_mode: str,
    ollama_base_url: str,
    ollama_enabled: bool,
    on_save_theme: Callable[[], None],
    on_save_ollama_settings: Callable[[], None],
) -> tuple[QWidget, SettingsPageRefs]:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)

    app_box = SectionCard(tr("Appearance"))
    av = app_box.body_layout
    theme_combo = QComboBox()
    theme_combo.addItems([tr("Dark"), tr("Light")])
    theme_combo.blockSignals(True)
    theme_combo.setCurrentIndex(1 if theme_mode == "light" else 0)
    theme_combo.blockSignals(False)
    theme_combo.currentIndexChanged.connect(on_save_theme)
    lf = QFormLayout()
    lf.addRow(tr("Theme:"), theme_combo)
    av.addLayout(lf)
    lay.addWidget(app_box)

    ol_box = SectionCard(tr("Ollama"))
    olv = ol_box.body_layout
    ollama_url_edit = QLineEdit()
    ollama_url_edit.setText(ollama_base_url or "http://127.0.0.1:11434")
    ollama_en = QCheckBox(tr("Enable Ollama for AI features"))
    ollama_en.setChecked(ollama_enabled)
    olf = QFormLayout()
    olf.addRow(tr("Base URL:"), ollama_url_edit)
    olf.addRow("", ollama_en)
    olv.addLayout(olf)
    save_btn = QPushButton(tr("Save Ollama settings"))
    save_btn.clicked.connect(on_save_ollama_settings)
    olv.addWidget(save_btn)
    lay.addWidget(ol_box)

    crawl_note = MethodologyPanel(
        tr("Crawler politeness"),
        tr("Default crawl behavior prioritizes safe pacing and predictable load."),
        points=[
            tr("Same-host delay uses ~3–5s jitter, with 1 connection per host."),
            tr("Default concurrency is 4 hosts in parallel; see README for current limits."),
        ],
    )
    lay.addWidget(crawl_note)
    lay.addStretch()

    refs = SettingsPageRefs(
        theme_combo=theme_combo,
        ollama_url=ollama_url_edit,
        ollama_en=ollama_en,
    )
    return root, refs
