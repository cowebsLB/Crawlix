"""Dashboard page builder extracted from MainWindow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from crawlix.ui.components import ActionListPanel, SectionCard


@dataclass
class DashboardPageRefs:
    dash_stats: QLabel
    dash_actions_panel: ActionListPanel
    dash_actions: QListWidget
    dash_action_btn: QPushButton
    dash_needs_panel: ActionListPanel
    dash_needs_attention: QListWidget
    dash_recent_panel: ActionListPanel
    dash_recent_outcomes: QListWidget


def build_dashboard_page(
    *,
    header: QWidget,
    tr: Callable[[str], str],
    on_refresh_summary: Callable[[], None],
    on_run_selected_action: Callable[[], None],
) -> tuple[QWidget, DashboardPageRefs]:
    root = QWidget()
    lay = QVBoxLayout(root)
    lay.setSpacing(10)
    lay.addWidget(header)

    summary_card = SectionCard(tr("Project summary"))
    sv = summary_card.body_layout
    sv.addWidget(QLabel(tr("Action hub for this project. Prioritize next steps, not passive stats.")))
    dash_stats = QLabel("")
    dash_stats.setWordWrap(True)
    sv.addWidget(dash_stats)
    dh = QHBoxLayout()
    refresh_btn = QPushButton(tr("Refresh summary"))
    refresh_btn.clicked.connect(on_refresh_summary)
    dh.addWidget(refresh_btn)
    dh.addStretch()
    sv.addLayout(dh)
    lay.addWidget(summary_card)

    dash_actions_panel = ActionListPanel(
        tr("Next best actions"),
        button_label=tr("Run selected action"),
    )
    dash_actions = dash_actions_panel.list
    dash_actions.setMinimumHeight(130)
    dash_action_btn = dash_actions_panel.button
    assert dash_action_btn is not None
    dash_action_btn.clicked.connect(on_run_selected_action)
    lay.addWidget(dash_actions_panel)

    split = QSplitter(Qt.Orientation.Horizontal)
    dash_needs_panel = ActionListPanel(tr("Needs attention now"))
    dash_needs_attention = dash_needs_panel.list
    split.addWidget(dash_needs_panel)
    dash_recent_panel = ActionListPanel(tr("Recent outcomes"))
    dash_recent_outcomes = dash_recent_panel.list
    split.addWidget(dash_recent_panel)
    split.setStretchFactor(0, 1)
    split.setStretchFactor(1, 1)
    lay.addWidget(split, 1)
    lay.addStretch()

    refs = DashboardPageRefs(
        dash_stats=dash_stats,
        dash_actions_panel=dash_actions_panel,
        dash_actions=dash_actions,
        dash_action_btn=dash_action_btn,
        dash_needs_panel=dash_needs_panel,
        dash_needs_attention=dash_needs_attention,
        dash_recent_panel=dash_recent_panel,
        dash_recent_outcomes=dash_recent_outcomes,
    )
    return root, refs
