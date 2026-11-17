import re

from PySide6.QtCore import QLocale
from PySide6.QtWebEngineCore import QWebEngineNotification
from PySide6.QtWebEngineQuick import QQuickWebEngineDownloadRequest, QQuickWebEngineProfile

from kondor.core.notifier import Notifier
from kondor.core.settings.settings import Settings
from kondor.downloads.downloadmanager import DownloadManager
from kondor.site.identity.profileidentity import ProfileIdentity

QT_WEB_ENGINE_TOKEN = re.compile("QtWebEngine/[^ ]+")
KONDOR_TOKEN = "Kondor/0.1"
NOTIFICATION_ICON = "preferences-desktop-notification"


def setting(name: str) -> object:
    return Settings.instance().property(name)


def string_list_setting(name: str) -> list[str]:
    value = setting(name)
    return [str(item) for item in value] if isinstance(value, list) else []


def apply_user_agent(profile: QQuickWebEngineProfile) -> None:
    user_agent = QT_WEB_ENGINE_TOKEN.sub(KONDOR_TOKEN, profile.httpUserAgent())
    profile.setHttpUserAgent(user_agent)


def route_downloads(profile: QQuickWebEngineProfile) -> None:
    def handle(download: QQuickWebEngineDownloadRequest) -> None:
        DownloadManager.instance().handle_request(download, profile.isOffTheRecord())

    profile.downloadRequested.connect(handle)


def show_notification(notification: QWebEngineNotification | None) -> None:
    if notification is None:
        return
    title, message = notification.title(), notification.message()
    Notifier.instance().notify(title, message, NOTIFICATION_ICON)
    notification.show()


def route_notifications(profile: QQuickWebEngineProfile) -> None:
    profile.presentNotification.connect(show_notification)


def apply_spell_check(profile: QQuickWebEngineProfile) -> None:
    profile.setSpellCheckLanguages(string_list_setting("spellCheckLanguages"))
    profile.setSpellCheckEnabled(bool(setting("spellCheckEnabled")))


def apply(profile: QQuickWebEngineProfile) -> None:
    apply_user_agent(profile)
    profile.setHttpAcceptLanguage(QLocale().bcp47Name())
    profile.setDownloadPath(str(setting("downloadDirectory")))
    apply_spell_check(profile)
    ProfileIdentity(profile).install()
    route_downloads(profile)
    route_notifications(profile)
