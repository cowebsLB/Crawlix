"""First-run wizard (6 steps) and unlock dialog."""

from __future__ import annotations

from pathlib import Path

from argon2 import PasswordHasher
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from crawlix.config import default_data_dir

_ph = PasswordHasher()


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(hash_str: str, pw: str) -> bool:
    try:
        return _ph.verify(hash_str, pw)
    except Exception:
        return False


class UnlockDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Unlock Crawlix"))
        self.setMinimumWidth(440)
        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(self.tr("Enter your master password:")))
        lay.addWidget(self._pw)
        lay.addWidget(buttons)

    def password(self) -> str:
        return self._pw.text()


class WelcomePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Welcome"))
        self.setSubTitle(
            self.tr(
                "Crawlix is a local-first SEO workstation. "
                "It is not a ranking guarantee. Network jobs require your responsibility."
            )
        )
        l = QVBoxLayout(self)
        l.addWidget(QLabel(self.tr("Click Continue to configure data storage and security.")))


class DataDirPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Data folder"))
        self.setSubTitle(self.tr("Application database and caches are stored here."))
        self._path = QLineEdit(str(default_data_dir()))
        lay = QFormLayout(self)
        lay.addRow(self.tr("Data directory:"), self._path)

    def data_dir(self) -> Path:
        return Path(self._path.text().strip()).expanduser()


class MasterPasswordPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Master password"))
        self.setSubTitle(self.tr("Encrypts your local database at rest (SQLCipher path planned)."))
        self._a = QLineEdit()
        self._a.setEchoMode(QLineEdit.EchoMode.Password)
        self._b = QLineEdit()
        self._b.setEchoMode(QLineEdit.EchoMode.Password)
        lay = QFormLayout(self)
        lay.addRow(self.tr("Password:"), self._a)
        lay.addRow(self.tr("Confirm:"), self._b)

    def validatePage(self) -> bool:
        if len(self._a.text()) < 8:
            QMessageBox.warning(self, self.tr("Too short"), self.tr("Use at least 8 characters."))
            return False
        if self._a.text() != self._b.text():
            QMessageBox.warning(self, self.tr("Mismatch"), self.tr("Passwords do not match."))
            return False
        return True

    def password(self) -> str:
        return self._a.text()


class DisclaimerPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Automation disclaimer"))
        self.setSubTitle(self.tr("Third-party sites may prohibit automated access."))
        self._cb = QCheckBox(
            self.tr("I understand automated fetches may violate third-party terms and accept responsibility.")
        )
        lay = QVBoxLayout(self)
        lay.addWidget(self._cb)

    def validatePage(self) -> bool:
        if not self._cb.isChecked():
            QMessageBox.warning(self, self.tr("Required"), self.tr("You must accept to continue."))
            return False
        return True


class PolitenessPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Politeness preset"))
        self.setSubTitle(
            self.tr(
                "Default: same-host delay ~3–5s, 1 connection per host, 4 concurrent hosts. "
                "See README for numeric table."
            )
        )
        self._combo = QComboBox()
        for k in ("conservative", "normal", "aggressive"):
            self._combo.addItem(k.replace("_", " ").title(), k)
        self._agg_warn = QCheckBox(
            self.tr("I understand Aggressive increases block risk (extra confirmation).")
        )
        lay = QVBoxLayout(self)
        lay.addWidget(self._combo)
        lay.addWidget(self._agg_warn)

    def preset(self) -> str:
        return self._combo.currentData()

    def validatePage(self) -> bool:
        if self.preset() == "aggressive" and not self._agg_warn.isChecked():
            QMessageBox.warning(
                self,
                self.tr("Aggressive"),
                self.tr("Check the extra confirmation for Aggressive preset."),
            )
            return False
        return True


class OllamaPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle(self.tr("Ollama (optional)"))
        self.setSubTitle(self.tr("Local LLM at http://127.0.0.1:11434 — skip if not installed."))
        lay = QVBoxLayout(self)
        lay.addWidget(
            QLabel(
                self.tr(
                    "AI features work better with Ollama. You can enable it later in Settings."
                )
            )
        )

    def skipped(self) -> bool:
        return True


def run_first_run_wizard(parent=None) -> dict | None:
    wiz = QWizard(parent)
    wiz.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
    wiz.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)
    wiz.addPage(WelcomePage())
    wiz.addPage(DataDirPage())
    wiz.addPage(MasterPasswordPage())
    wiz.addPage(DisclaimerPage())
    wiz.addPage(PolitenessPage())
    wiz.addPage(OllamaPage())
    wiz.setWindowTitle(wiz.tr("Crawlix setup"))
    if wiz.exec() != QWizard.DialogCode.Accepted:
        return None
    data_page: DataDirPage = wiz.page(1)  # type: ignore[assignment]
    pw_page: MasterPasswordPage = wiz.page(2)  # type: ignore[assignment]
    pol_page: PolitenessPage = wiz.page(4)  # type: ignore[assignment]
    return {
        "data_dir": data_page.data_dir(),
        "password_hash": hash_password(pw_page.password()),
        "politeness_preset": pol_page.preset(),
        "automation_disclaimer": "1",
        "wizard_completed": "1",
    }
