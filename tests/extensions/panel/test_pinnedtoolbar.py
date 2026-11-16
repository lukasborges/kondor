from collections.abc import Iterator

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.extensions.extensionmanager import ExtensionManager
from tests.extensions.panel.panelitems import (
    click_center_of,
)
from tests.extensions.panel.toolbarharness import (
    SAMPLE,
    ToolBar,
    can_recolor_named_icons,
    has_red_pixel,
)

pytestmark = pytest.mark.no_qt_log


@pytest.fixture(scope="module", autouse=True)
def accessibility() -> None:
    QAccessible.setActive(True)


@pytest.fixture
def toolbar(qtbot: QtBot, work: str, kondor_engine: QQmlEngine) -> Iterator[ToolBar]:
    tool_bar = ToolBar(qtbot, kondor_engine, work)
    yield tool_bar
    tool_bar.close()


def test_pinned_extension_shows_visible_button(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is not None)
    button = toolbar.button()
    assert button.width() > 0
    assert button.height() > 0


def test_unpin_removes_button(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is not None)
    ExtensionManager.instance().setPinned(SAMPLE, False)
    toolbar.qtbot.waitUntil(lambda: toolbar.button() is None)


def test_pinned_button_opens_panel_on_extension(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    click_center_of(toolbar.wait_for_pinned_button())
    panel = toolbar.window.findChild(QObject, "extensionsPanel")
    assert panel is not None
    toolbar.qtbot.waitUntil(lambda: panel.property("currentId") == SAMPLE)


def test_pinned_file_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.pin()
    toolbar.verify_icon_fits_box(toolbar.wait_for_pinned_button())


def test_pinned_theme_icon_button_has_extensions_button_width(toolbar: ToolBar) -> None:
    toolbar.install_theme_icon_sample()
    toolbar.show()
    toolbar.pin()
    button = toolbar.wait_for_pinned_button()
    assert button.width() == toolbar.named("extensionsButton").width()


def test_pinned_theme_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.install_theme_icon_sample()
    toolbar.show()
    toolbar.pin()
    toolbar.verify_icon_fits_box(toolbar.wait_for_pinned_button())


def test_extensions_button_icon_fits_tool_bar_icon_box(toolbar: ToolBar) -> None:
    toolbar.show()
    toolbar.verify_icon_fits_box(toolbar.named("extensionsButton"))


def test_extensions_button_bundled_icon_follows_text_color(toolbar: ToolBar) -> None:
    if not can_recolor_named_icons():
        pytest.skip("platform theme does not recolor named icons (no KIconEngine)")
    toolbar.show()
    button = toolbar.named("extensionsButton")
    toolbar.qtbot.waitUntil(lambda: has_red_pixel(button))
