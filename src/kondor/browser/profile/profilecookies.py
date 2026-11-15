from PySide6.QtWebEngineCore import QWebEngineCookieStore
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.core.settings.settings import Settings


def clear_cookies_and_cache(profile: QQuickWebEngineProfile) -> None:
    profile.clearHttpCache()
    store = profile.cookieStore()
    if store is not None:
        store.deleteAllCookies()


def accepts_cookie(request: QWebEngineCookieStore.FilterRequest) -> bool:
    blocks_third_party = bool(Settings.instance().property("blockThirdPartyCookies"))
    return not request.thirdParty or not blocks_third_party


def block_third_party_cookies_when_configured(profile: QQuickWebEngineProfile) -> None:
    store = profile.cookieStore()
    if store is not None:
        store.setCookieFilter(accepts_cookie)
