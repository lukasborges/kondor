import pytest
from PySide6.QtCore import Qt
from PySide6.QtQml import QQmlEngine

from kondor.browser.favicons.faviconimageprovider import FaviconImageProvider
from kondor.browser.favicons.faviconstore import FaviconStore
from kondor.core.database import sql
from tests.browser.test_faviconstore import make_image
from tests.qmlsupport import captured_messages, load_component

SITE_ICON_QML = """
import Kondor

SiteIcon { pageUrl: "%s" }
"""
PROVIDER_WARNING = "Failed to get image from provider"


@pytest.fixture
def icons(qapp: object, kondor_engine: QQmlEngine) -> FaviconStore:
    assert sql.run("DELETE FROM favicons") is not None
    kondor_engine.addImageProvider("kondor-favicon", FaviconImageProvider())
    return FaviconStore.instance()


def provider_warnings(engine: QQmlEngine, url: str) -> list[str]:
    component = load_component(engine, SITE_ICON_QML % url)
    with captured_messages() as messages:
        assert component.create() is not None
    return [message for message in messages if PROVIDER_WARNING in message]


def test_does_not_ask_the_provider_for_a_host_without_an_icon(
    icons: FaviconStore, kondor_engine: QQmlEngine
) -> None:
    assert provider_warnings(kondor_engine, "https://example.org/") == []
    assert provider_warnings(kondor_engine, "") == []


def test_asks_the_provider_for_a_host_with_an_icon(
    icons: FaviconStore, kondor_engine: QQmlEngine
) -> None:
    icons.store_image("kde.org", make_image(Qt.GlobalColor.red))
    component = load_component(kondor_engine, SITE_ICON_QML % "https://kde.org/")
    icon = component.create()
    assert icon is not None
    assert icon.property("hasStoredIcon") is True
