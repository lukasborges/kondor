from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.bridge.extensionpageharness import PageHost
from pytests.extensions.extensionsharness import remove_every_extension
from pytests.extensions.pageserver import DEFAULT_PAGE, PageServer


@pytest.fixture
def work(kondor_types: None, staged_resources: None, tmp_path: Path) -> Iterator[str]:
    ExtensionManager.instance().set_locale("en")
    yield str(tmp_path)
    remove_every_extension()


@pytest.fixture(autouse=True)
def offline_catalog(work: str, tmp_path: Path) -> Iterator[None]:
    ExtensionCatalog.instance().set_catalog_url(QUrl.fromLocalFile(str(tmp_path / "none.json")))
    yield
    ExtensionCatalog.instance().set_catalog_url(QUrl())


@pytest.fixture(scope="module")
def registered_profiles(
    kondor_types: None, staged_resources: None
) -> Iterator[QQuickWebEngineProfile]:
    profiles = ProfileManager.instance()
    manager = ExtensionManager.instance()
    profiles.profileCreated.connect(manager.register_profile)
    normal = profiles.defaultProfile()
    manager.register_profile(normal)
    yield normal
    profiles.profileCreated.disconnect(manager.register_profile)


@pytest.fixture
def page_server() -> Iterator[PageServer]:
    yield PageServer(default_body=DEFAULT_PAGE)


@pytest.fixture
def page_host(
    qtbot: QtBot, page_server: PageServer, registered_profiles: QQuickWebEngineProfile
) -> Iterator[PageHost]:
    host = PageHost(qtbot, page_server, registered_profiles)
    yield host
    host.close()
