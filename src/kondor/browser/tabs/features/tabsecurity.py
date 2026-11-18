from dataclasses import dataclass, field

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.site.httpsonly.profilehttpsonly import ProfileHttpsOnly


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
    upgradeChanged = Signal()
    continueToHttpRequested = Signal(QUrl)
    leaveHttpsOnlyWarningRequested = Signal()

    def __init__(
        self, profile: QQuickWebEngineProfile | None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._profile = profile
        self._url = QUrl()
        self._state = "local"
        self._is_pending = False
        self._error = CertificateError()
        self._upgraded_from = QUrl()
        self._is_warning_pending = False

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

    upgradedFrom = Property(QUrl, lambda self: self._upgraded_from, notify=upgradeChanged)
    upgradedHost = Property(str, lambda self: self._upgraded_from.host(), notify=upgradeChanged)
    httpsOnlyWarningPending = Property(
        bool, lambda self: self._is_warning_pending, notify=upgradeChanged
    )

    def update_for(self, url: QUrl) -> None:
        self._url = url
        self._note_upgrade_of(url)
        self._refresh_state()

    def _refresh_state(self) -> None:
        assign_and_notify((self, "_state"), self._compute_state(), self.stateChanged)

    def _compute_state(self) -> str:
        scheme = self._url.scheme().lower()
        if self._is_pending:
            return "error"
        if self._is_warning_pending:
            return "insecure"
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

    def _https_only(self) -> ProfileHttpsOnly | None:
        return ProfileHttpsOnly.of(self._profile)

    def _note_upgrade_of(self, url: QUrl) -> None:
        state = self._https_only()
        original = QUrl() if state is None else state.original_of(url)
        if original.isEmpty():
            return
        self._set_upgrade(original, self._is_warning_pending)

    def _set_upgrade(self, original: QUrl, is_warning_pending: bool) -> None:
        if self._upgraded_from == original and self._is_warning_pending == is_warning_pending:
            return
        self._upgraded_from = original
        self._is_warning_pending = is_warning_pending
        self._refresh_state()
        self.upgradeChanged.emit()

    @Slot(QUrl, result=bool)
    def failUpgradeOf(self, url: QUrl) -> bool:
        state = self._https_only()
        original = QUrl() if state is None else state.original_of(url)
        if original.isEmpty():
            original = self._upgraded_from if self._is_upgraded_url(url) else QUrl()
        if original.isEmpty():
            return False
        self._set_upgrade(original, True)
        return True

    def _is_upgraded_url(self, url: QUrl) -> bool:
        return not self._upgraded_from.isEmpty() and url.host() == self._upgraded_from.host()

    @Slot()
    def finishUpgrade(self) -> None:
        state = self._https_only()
        if state is not None:
            state.forget(self._url)
        self._set_upgrade(QUrl(), False)

    @Slot()
    def dismissHttpsOnlyWarning(self) -> None:
        if self._is_warning_pending:
            self._set_upgrade(QUrl(), False)

    @Slot()
    def continueToHttp(self) -> None:
        state, original = self._https_only(), self._upgraded_from
        if not self._is_warning_pending or state is None:
            return
        state.allow(original.host())
        self._set_upgrade(QUrl(), False)
        self.continueToHttpRequested.emit(original)

    @Slot()
    def leaveHttpsOnlyWarning(self) -> None:
        if not self._is_warning_pending:
            return
        self._set_upgrade(QUrl(), False)
        self.leaveHttpsOnlyWarningRequested.emit()
