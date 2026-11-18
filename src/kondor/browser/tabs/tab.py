from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.agent.agenttabs import AgentTabs
from kondor.browser.agent.tabagent import TabAgent
from kondor.browser.tabs.assignandnotify import assign_and_notify
from kondor.browser.tabs.features.tabaudio import TabAudio
from kondor.browser.tabs.features.tabextensionitems import TabExtensionItems
from kondor.browser.tabs.features.tabmedia import TabMedia
from kondor.browser.tabs.features.tabpasswords import TabPasswords
from kondor.browser.tabs.features.tabpermissions import TabPermissions
from kondor.browser.tabs.features.tabpopups import TabPopups
from kondor.browser.tabs.features.tabsecurity import TabSecurity
from kondor.browser.tabs.features.tabsitereload import TabSiteReload
from kondor.browser.tabs.features.tabsleep import TabSleep
from kondor.browser.tabs.tabviewstate import TabViewState
from kondor.site.identity.tabidentity import TabIdentity

BLANK_PAGE = QUrl("about:blank")


def is_same_origin(first: QUrl, second: QUrl) -> bool:
    if first.isEmpty() or second.isEmpty():
        return False
    return bool(
        first.scheme().lower() == second.scheme().lower()
        and first.host().lower() == second.host().lower()
        and first.port() == second.port()
    )


def is_real_page(url: QUrl) -> bool:
    return not url.isEmpty() and url != BLANK_PAGE


class Tab(TabViewState):
    urlChanged = Signal()
    newTabPageChanged = Signal()

    def __init__(self, profile: QQuickWebEngineProfile | None, parent: QObject | None = None):
        super().__init__(parent)
        self._init_load_state()
        self._init_view_state()
        self._profile = profile
        self._is_private = profile is not None and profile.isOffTheRecord()
        self._url = QUrl()
        self._new_tab_page = True
        self._pending_request: QObject | None = None
        self._create_feature_groups(profile)
        self._create_agent_group()

    def _create_feature_groups(self, profile: QQuickWebEngineProfile | None) -> None:
        self._security = TabSecurity(profile, self)
        self._permissions = TabPermissions(self)
        self._passwords = TabPasswords(self._is_private, self)
        self._site_reload = TabSiteReload(self)
        self._extension_items = TabExtensionItems(self)
        self._sleep = TabSleep(self)
        self._media = TabMedia(self)
        self._audio = TabAudio(self)
        self._popups = TabPopups(self._is_private, self)
        self._identity = TabIdentity(profile, self._is_private, self)

    def _create_agent_group(self) -> None:
        self._agent = TabAgent(self._is_private, self)
        AgentTabs.instance().watch(self._agent)

    url = Property(QUrl, lambda self: self._url, notify=urlChanged)
    newTabPage = Property(bool, lambda self: self._new_tab_page, notify=newTabPageChanged)
    profile = Property(QObject, lambda self: self._profile, constant=True)
    isPrivate = Property(bool, lambda self: self._is_private, constant=True)
    security = Property(TabSecurity, lambda self: self._security, constant=True)
    permissions = Property(TabPermissions, lambda self: self._permissions, constant=True)
    passwords = Property(TabPasswords, lambda self: self._passwords, constant=True)
    siteReload = Property(TabSiteReload, lambda self: self._site_reload, constant=True)
    media = Property(TabMedia, lambda self: self._media, constant=True)
    audio = Property(TabAudio, lambda self: self._audio, constant=True)
    popups = Property(TabPopups, lambda self: self._popups, constant=True)
    identity = Property(TabIdentity, lambda self: self._identity, constant=True)
    agent = Property(TabAgent, lambda self: self._agent, constant=True)
    sleep = Property(TabSleep, lambda self: self._sleep, constant=True)
    extensionItems = Property(TabExtensionItems, lambda self: self._extension_items, constant=True)

    pendingRequest = Property(QObject, lambda self: self._pending_request, constant=False)

    @Slot()
    def clearPendingRequest(self) -> None:
        self._pending_request = None

    @Slot(QUrl)
    def setUrl(self, url: QUrl) -> None:
        self._leave_previous_page_for(url)
        if self._url == url:
            return
        self._url = url
        self._security.update_for(url)
        self._popups.update_for(url)
        self._identity.update_for(url)
        self._passwords.update_usernames_for(url)
        self.urlChanged.emit()

    def _leave_previous_page_for(self, url: QUrl) -> None:
        if is_real_page(url):
            self._set_new_tab_page(False)
        if not is_same_origin(self._url, url):
            self._permissions.deny_all()

    def adopt_request(self, request: QObject | None) -> None:
        if request is None:
            return
        self._pending_request = request
        self._agent.inherit_for(request)
        self._set_new_tab_page(False)

    @Slot(bool)
    def setLoading(self, loading: bool) -> None:
        if loading:
            self._site_reload.dismiss()
            self._identity.dismiss()
        super().setLoading(loading)

    def _set_new_tab_page(self, new_tab_page: bool) -> None:
        assign_and_notify((self, "_new_tab_page"), new_tab_page, self.newTabPageChanged)

    @Slot(QUrl)
    def navigateTo(self, url: QUrl) -> None:
        if url.isEmpty():
            return
        self._security.clear_pending_certificate_error()
        self._set_new_tab_page(False)
        self.navigationRequested.emit(url)

    @Slot()
    def showNewTabPage(self) -> None:
        if self._new_tab_page:
            return
        self._security.clear_pending_certificate_error()
        self._set_new_tab_page(True)
        self.newTabPageRequested.emit()

    @Slot()
    def exitFullScreen(self) -> None:
        if self._is_full_screen:
            self.exitFullScreenRequested.emit()

    @Slot()
    def toggleReaderMode(self) -> None:
        if self._reader_available or self._reader_active:
            self.toggleReaderModeRequested.emit()
