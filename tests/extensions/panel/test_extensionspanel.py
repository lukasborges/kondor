import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QKeySequence
from PySide6.QtQuick import QQuickItem
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile

from kondor.browser.tabs.tab import Tab
from kondor.extensions.extensionmanager import ExtensionManager
from tests.extensions.extensionsharness import (
    allow_in_private_windows,
    apply_settings,
    install_named,
    install_plain,
    install_sample,
)
from tests.extensions.panel.panelfixture import PanelFixture, install_keyed
from tests.extensions.panel.panelitems import (
    accessible_description_of,
    accessible_name_of,
    click_center_of,
)

pytestmark = pytest.mark.no_qt_log

SAMPLE = "sample"
ROW_COUNT = 2


def native_text(sequence: str) -> str:
    return QKeySequence(sequence).toString(QKeySequence.SequenceFormat.NativeText)


def manager() -> ExtensionManager:
    return ExtensionManager.instance()


def test_list_shows_one_row_per_extension(panel: PanelFixture) -> None:
    assert install_sample(panel.work)
    assert install_named(panel.work, "alpha", "Alpha")
    panel.open_panel()
    assert panel.item("panelExtensionList").property("count") == ROW_COUNT
    panel.wait_for(lambda: panel.row_at(0))
    assert accessible_name_of(panel.row_at(0)) == "Alpha"


def test_row_is_dimmed_when_off_on_site(panel: PanelFixture) -> None:
    assert install_sample(panel.work)
    panel.open_panel()
    manager().setSiteEnabled(SAMPLE, panel.tab.url, False)
    panel.wait_for(lambda: panel.row_at(0))
    row = panel.row_at(0)
    panel.wait_for(lambda: panel.probe.parts_enabled(row)[:2] == [False, False])
    assert row.isEnabled()
    assert accessible_name_of(row) == "Sample Extension, off on www.example.com"


def test_row_opens_actions(panel: PanelFixture) -> None:
    panel.open_panel()
    panel.wait_for(lambda: panel.row_at(0))
    row = panel.row_at(0)
    click_center_of(row)
    assert panel.current_id() == SAMPLE
    assert panel.item_with_text(panel.item("backButton").parentItem(), "Sample Extension")


def test_back_returns_to_list_and_focuses_row(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    click_center_of(panel.item("backButton"))
    assert panel.current_id() == ""
    panel.wait_for(lambda: panel.row_at(0) and panel.row_at(0).hasActiveFocus())


def test_action_keeps_panel_open(panel: PanelFixture) -> None:
    assert install_plain(panel.work)
    panel.open_panel("plain")
    triggers: list[tuple[object, ...]] = []
    panel.tab.extensionItems.triggered.connect(lambda *args: triggers.append(args))
    action = panel.item_with_text(panel.actions_root(), "Go Now")
    assert action is not None
    click_center_of(action)
    assert len(triggers) == 1
    assert panel.panel.property("opened")


def test_checkable_action_shows_state(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    box = panel.item_with_text(panel.actions_root(), "Toggle Mark")
    assert box is not None
    assert box.property("checked")
    panel.tab.extensionItems.setChecked(SAMPLE, "toggle", False)
    panel.wait_for(lambda: not box.property("checked"))


def test_run_on_site_switch_shows_reload_bar(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    reloads: list[bool] = []
    panel.tab.reloadRequested.connect(lambda: reloads.append(True))
    panel.toggle_run_on_site()
    assert not reloads
    assert not manager().siteEnabled(SAMPLE, panel.tab.url)
    assert panel.item("bar").isVisible()
    message = "Sample Extension will stop running on this site after reloading."
    assert panel.item_with_text(panel.item("bar"), message)


def test_private_tab_has_no_site_switch(panel: PanelFixture) -> None:
    assert install_sample(panel.work)
    allow_in_private_windows(SAMPLE)
    profile = QQuickWebEngineProfile()
    panel.make_tab(Tab(profile))
    panel.open_panel(SAMPLE)
    assert not panel.item("siteSwitch").isVisible()


def test_host_is_hidden_on_non_web_page(panel: PanelFixture) -> None:
    panel.open_panel()
    assert panel.panel.property("host") == "www.example.com"
    panel.tab.setUrl(QUrl("about:newtab"))
    assert panel.panel.property("host") == ""


def test_open_at_shows_actions(panel: PanelFixture) -> None:
    panel.open_panel(SAMPLE)
    assert panel.current_id() == SAMPLE
    assert panel.item("backButton").isVisible()


def test_action_row_shows_shortcut(panel: PanelFixture) -> None:
    assert install_keyed(panel.work)
    panel.open_panel("keyed")
    assert panel.item_with_text(panel.actions_root(), native_text("S"))


def test_checkable_row_shows_shortcut(panel: PanelFixture) -> None:
    assert install_keyed(panel.work)
    panel.open_panel("keyed")
    box = panel.item_with_text(panel.actions_root(), "Mark")
    assert isinstance(box, QQuickItem)
    assert accessible_description_of(box) == native_text("S")


def test_shortcut_follows_changed_setting(panel: PanelFixture) -> None:
    assert install_keyed(panel.work)
    panel.open_panel("keyed")
    apply_settings("keyed", {"keyGo": "Shift+F"})
    text = native_text("Shift+F")
    panel.wait_for(lambda: panel.item_with_text(panel.actions_root(), text))
