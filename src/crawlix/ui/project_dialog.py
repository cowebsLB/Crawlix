"""New project dialog — J3 (name, domain, optional primary location)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class NewProjectDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("New project"))
        self.setMinimumWidth(480)
        self._name = QLineEdit()
        self._domain = QLineEdit()
        self._loc_enable = QCheckBox(self.tr("Add primary location (NAP seed)"))
        self._loc_label = QLineEdit(self.tr("Main"))
        self._biz = QLineEdit()
        self._city = QLineEdit()
        self._country = QLineEdit()
        self._country.setMaxLength(2)
        self._country.setPlaceholderText("LB")

        form = QFormLayout()
        form.addRow(self.tr("Project name:"), self._name)
        form.addRow(self.tr("Default domain (e.g. example.com):"), self._domain)

        loc = QGroupBox(self.tr("Optional location"))
        lf = QFormLayout(loc)
        lf.addRow(self._loc_enable)
        lf.addRow(self.tr("Location label:"), self._loc_label)
        lf.addRow(self.tr("Business name:"), self._biz)
        lf.addRow(self.tr("City:"), self._city)
        lf.addRow(self.tr("Country code (ISO-3166 alpha-2):"), self._country)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(loc)
        root.addWidget(buttons)

    def _try_accept(self) -> None:
        name = self._name.text().strip()
        if len(name) < 2:
            QMessageBox.warning(self, self.tr("Name"), self.tr("Enter a project name (at least 2 characters)."))
            return
        dom = self._domain.text().strip().lower()
        if len(dom) < 3 or "." not in dom:
            QMessageBox.warning(
                self,
                self.tr("Domain"),
                self.tr("Enter a plausible default domain (e.g. example.com)."),
            )
            return
        if self._loc_enable.isChecked():
            biz = self._biz.text().strip()
            if len(biz) < 2:
                QMessageBox.warning(self, self.tr("Location"), self.tr("Business name is required for a location."))
                return
            cc = self._country.text().strip().upper()
            if cc and len(cc) != 2:
                QMessageBox.warning(self, self.tr("Location"), self.tr("Country code must be two letters or empty."))
                return
        self.accept()

    def project_name(self) -> str:
        return self._name.text().strip()

    def default_domain(self) -> str:
        return self._domain.text().strip().lower()

    def location_payload(self) -> dict | None:
        if not self._loc_enable.isChecked():
            return None
        cc = self._country.text().strip().upper() or None
        return {
            "label": self._loc_label.text().strip() or self.tr("Main"),
            "business_name": self._biz.text().strip(),
            "city": self._city.text().strip() or None,
            "country_code": cc,
        }
