from collections.abc import Iterator

import pytest
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow

from kondor.browser.profile.profilemanager import ProfileManager
from kondor.browser.responsive.devices import DEVICES
from kondor.browser.tabs.tab import Tab
from tests.qmlsupport import error_text, load_component, release

SCENE_QML = """
import QtQuick
import Kondor

ResponsiveToolBar { width: 800; tab: testTab }
"""


@pytest.fixture
def toolbar_and_tab(kondor_engine: QQmlEngine) -> Iterator[tuple[QQuickItem, Tab]]:
    tab = Tab(ProfileManager.instance().defaultProfile())
    kondor_engine.rootContext().setContextProperty("testTab", tab)
    component = load_component(kondor_engine, SCENE_QML)
    created = component.create()
    assert created is not None, error_text(component)
    window = QQuickWindow()
    created.setParentItem(window.contentItem())
    yield created, tab
    window.close()
    release(created)
    release(window, component, tab)


def test_toolbar_lists_responsive_and_every_device(
    toolbar_and_tab: tuple[QQuickItem, Tab],
) -> None:
    toolbar, _ = toolbar_and_tab
    assert toolbar.property("devices").property("length").toInt() == len(DEVICES) + 1


def test_toolbar_starts_with_the_free_size_entry(
    toolbar_and_tab: tuple[QQuickItem, Tab],
) -> None:
    toolbar, _ = toolbar_and_tab
    assert toolbar.property("devices").property(0).property("key").toString() == "responsive"
