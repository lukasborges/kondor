from PySide6.QtCore import Property, QCoreApplication, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.address import addressresolver
from kondor.browser.profile import pagescripts, profilesetup
from kondor.browser.profile.certificateoverrides import CertificateOverrides
from kondor.browser.profile.profilecookies import (
    block_third_party_cookies_when_configured,
    clear_cookies_and_cache,
)
from kondor.core.settings.settings import Settings
from kondor.history.historymanager import HistoryManager

STORAGE_NAME = "kondor"
Policy = QQuickWebEngineProfile.PersistentPermissionsPolicy
Cookies = QQuickWebEngineProfile.PersistentCookiesPolicy


def setting(name: str) -> object:
    return Settings.instance().property(name)


def search_template() -> str:
    return str(Settings.instance().searchUrlTemplate())


class ProfileManager(QObject):
    homePageChanged = Signal()
    profileCreated = Signal(QQuickWebEngineProfile)
    _instance: "ProfileManager | None" = None

    def __init__(self) -> None:
        super().__init__()
        self._default_profile: QQuickWebEngineProfile | None = None
        self._private_profiles: list[QQuickWebEngineProfile] = []
        self._certificate_overrides = CertificateOverrides()
        self.connect_settings()
        QCoreApplication.instance().aboutToQuit.connect(self.clear_data_on_exit)

    @classmethod
    def instance(cls) -> "ProfileManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect_settings(self) -> None:
        settings = Settings.instance()
        settings.homePageChanged.connect(self.homePageChanged)
        settings.downloadDirectoryChanged.connect(self.apply_download_directory)
        settings.spellCheckEnabledChanged.connect(self.apply_spell_check)
        settings.spellCheckLanguagesChanged.connect(self.apply_spell_check)

    def home_page(self) -> str:
        return str(setting("homePage"))

    homePage = Property(str, home_page, notify=homePageChanged)

    @Slot(result=QQuickWebEngineProfile)
    def defaultProfile(self) -> QQuickWebEngineProfile:
        if self._default_profile is None:
            self._default_profile = self.create_persistent_profile()
        return self._default_profile

    @Slot(result=QQuickWebEngineProfile)
    def createPrivateProfile(self) -> QQuickWebEngineProfile:
        profile = QQuickWebEngineProfile(self)
        profile.setPersistentCookiesPolicy(Cookies.NoPersistentCookies)
        profile.setPersistentPermissionsPolicy(Policy.StoreInMemory)
        self._private_profiles.append(profile)
        profile.destroyed.connect(lambda: self._private_profiles.remove(profile))
        self.setup_profile(profile)
        return profile

    @Slot(str, result=QUrl)
    def resolveAddress(self, text: str) -> QUrl:
        home_page = QUrl(self.home_page())
        return addressresolver.resolve_address(text, home_page, search_template())

    @Slot(str, result=QUrl)
    def addressUrl(self, text: str) -> QUrl:
        return addressresolver.address_url(text)

    @Slot(str, result=QUrl)
    def searchUrl(self, text: str) -> QUrl:
        return addressresolver.search_url(text, search_template())

    @Slot()
    def clearCookiesAndCacheNow(self) -> None:
        clear_cookies_and_cache(self.defaultProfile())

    def mark_certificate_overridden(
        self, profile: QQuickWebEngineProfile | None, host: str
    ) -> None:
        self._certificate_overrides.mark(profile, host)

    def is_certificate_overridden(
        self, profile: QQuickWebEngineProfile | None, host: str
    ) -> bool:
        return self._certificate_overrides.is_overridden(profile, host)

    def profiles(self) -> list[QQuickWebEngineProfile]:
        default = [] if self._default_profile is None else [self._default_profile]
        return default + self._private_profiles

    def create_persistent_profile(self) -> QQuickWebEngineProfile:
        profile = QQuickWebEngineProfile(STORAGE_NAME, self)
        profile.setPersistentCookiesPolicy(Cookies.AllowPersistentCookies)
        profile.setPersistentPermissionsPolicy(Policy.StoreOnDisk)
        self.setup_profile(profile)
        block_third_party_cookies_when_configured(profile)
        return profile

    def setup_profile(self, profile: QQuickWebEngineProfile) -> None:
        pagescripts.install(profile)
        profilesetup.apply(profile)
        profile.destroyed.connect(lambda: self._certificate_overrides.forget(profile))
        self.profileCreated.emit(profile)

    def apply_download_directory(self) -> None:
        directory = str(setting("downloadDirectory"))
        for profile in self.profiles():
            profile.setDownloadPath(directory)

    def apply_spell_check(self) -> None:
        for profile in self.profiles():
            profilesetup.apply_spell_check(profile)

    def clear_data_on_exit(self) -> None:
        if not setting("clearDataOnExit"):
            return
        if self._default_profile is not None:
            clear_cookies_and_cache(self._default_profile)
        HistoryManager.instance().clearAll()
