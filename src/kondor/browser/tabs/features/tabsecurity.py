from dataclasses import dataclass, field

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.assignandnotify import assign_and_notify


@dataclass(frozen=True)
class CertificateError:
    url: QUrl = field(default_factory=QUrl)
    description: str = ""
    overridable: bool = False


class TabSecurity(QObject):
    stateChanged = Signal()
    certificateErrorChanged = Signal()
    acceptCertificateErrorRequested = Signal()
    rejectCertificateErrorRequested = Signal()

    def __init__(
        self, profile: QQuickWebEngineProfile | None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._profile = profile
        self._url = QUrl()
        self._state = "local"
        self._is_pending = False
        self._error = CertificateError()

    state = Property(str, lambda self: self._state, notify=stateChanged)
    certificateErrorPending = Property(
        bool, lambda self: self._is_pending, notify=certificateErrorChanged
    )
    certificateErrorUrl = Property(
        QUrl, lambda self: self._error.url, notify=certificateErrorChanged
    )
    certificateErrorDescription = Property(
        str, lambda self: self._error.description, notify=certificateErrorChanged
    )
    certificateErrorOverridable = Property(
        bool, lambda self: self._error.overridable, notify=certificateErrorChanged
    )

    def update_for(self, url: QUrl) -> None:
        self._url = url
        self._refresh_state()

    def _refresh_state(self) -> None:
        assign_and_notify((self, "_state"), self._compute_state(), self.stateChanged)

    def _compute_state(self) -> str:
        scheme = self._url.scheme().lower()
        if self._is_pending:
            return "error"
        if scheme == "https":
            return "error" if self._has_certificate_override() else "secure"
        return "insecure" if scheme == "http" else "local"

    def _has_certificate_override(self) -> bool:
        manager = ProfileManager.instance()
        return manager.is_certificate_overridden(self._profile, self._url.host())

    @Slot(QUrl, str, bool)
    def setPendingCertificateError(self, url: QUrl, description: str, overridable: bool) -> None:
        error = CertificateError(url, description, overridable)
        if self._is_pending and self._error == error:
            return
        self._is_pending = True
        self._error = error
        self._refresh_state()
        self.certificateErrorChanged.emit()

    def clear_pending_certificate_error(self) -> None:
        if not self._is_pending:
            return
        self._is_pending = False
        self._error = CertificateError()
        self._refresh_state()
        self.certificateErrorChanged.emit()

    def _mark_certificate_overridden(self) -> None:
        error_host = self._error.url.host()
        host = error_host or self._url.host()
        ProfileManager.instance().mark_certificate_overridden(self._profile, host)

    @Slot()
    def acceptCertificateError(self) -> None:
        if not self._is_pending:
            return
        self._mark_certificate_overridden()
        self.clear_pending_certificate_error()
        self.acceptCertificateErrorRequested.emit()

    @Slot()
    def rejectCertificateError(self) -> None:
        if not self._is_pending:
            return
        self.clear_pending_certificate_error()
        self.rejectCertificateErrorRequested.emit()
