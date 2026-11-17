import pytest
from PySide6.QtCore import QUrl

from kondor.site.identity import useragents
from kondor.site.sitesettings import SiteSettings
from tests.site.identity.conftest import Browser

pytestmark = pytest.mark.usefixtures("window", "site_settings")


def hint_names(headers: dict[str, str]) -> set[str]:
    return {name for name in headers if name.startswith("sec-ch-ua")}


def test_site_without_identity_keeps_the_profile_user_agent(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    assert "Kondor/" in browser.last_header("user-agent")
    assert tab.title.startswith(browser.last_header("user-agent"))


def test_firefox_identity_reaches_the_header_and_the_page(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    tab.identity.choose(useragents.FIREFOX)
    assert tab.identity.isReloadPending
    browser.reload(tab)
    assert browser.last_header("user-agent") == useragents.FIREFOX_AGENT
    assert tab.title == f"{useragents.FIREFOX_AGENT}|nohints"


def test_firefox_identity_clears_only_client_hints_the_request_had(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    kondor_hints = hint_names(browser.server.page_headers[-1])
    tab.identity.choose(useragents.FIREFOX)
    browser.reload(tab)
    firefox_headers = browser.server.page_headers[-1]
    assert hint_names(firefox_headers) <= kondor_hints
    assert all(firefox_headers[name] == "" for name in hint_names(firefox_headers))


def test_cross_site_frame_reports_the_first_party_identity(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    tab.identity.choose(useragents.FIREFOX)
    outer = browser.open_page(browser.server.url("/outer"))
    assert outer.title == f"{useragents.FIREFOX_AGENT}|frame"


def test_chrome_identity_removes_only_the_kondor_token(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    tab.identity.choose(useragents.CHROME)
    browser.reload(tab)
    assert "Chrome/" in browser.last_header("user-agent")
    assert "Kondor/" not in browser.last_header("user-agent")
    assert tab.title.endswith("|hints")


def test_another_site_keeps_the_default_identity(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    tab.identity.choose(useragents.FIREFOX)
    other = QUrl(browser.server.url().toString().replace("127.0.0.1", "localhost"))
    browser.open_page(other)
    assert "Kondor/" in browser.last_header("user-agent")


def test_choosing_kondor_removes_the_identity(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url())
    tab.identity.choose(useragents.FIREFOX)
    tab.identity.choose(useragents.KONDOR)
    browser.reload(tab)
    assert "Kondor/" in browser.last_header("user-agent")
    assert SiteSettings.instance().hostsWithUserAgent() == []


def test_private_tab_changes_nothing_on_disk(browser: Browser) -> None:
    tab = browser.open_page(browser.server.url(), is_private=True)
    tab.identity.choose(useragents.FIREFOX)
    browser.reload(tab)
    assert browser.last_header("user-agent") == useragents.FIREFOX_AGENT
    assert SiteSettings.instance().hostsWithUserAgent() == []
