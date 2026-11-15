from pytestqt.qtbot import QtBot

from kondor.browser.tabs.features.tabsitereload import TabSiteReload


def test_toggle_is_pending_and_names_the_extension(qapp: object) -> None:
    reload = TabSiteReload()
    reload.recordToggle("dark", "Dark Mode", True)
    assert reload.isPending
    assert reload.extensionName == "Dark Mode"


def test_toggling_back_clears_the_change(qapp: object) -> None:
    reload = TabSiteReload()
    reload.recordToggle("dark", "Dark Mode", True)
    reload.recordToggle("dark", "Dark Mode", False)
    assert not reload.isPending
    assert reload.extensionName == ""


def test_will_run_follows_the_last_toggle(qapp: object) -> None:
    reload = TabSiteReload()
    reload.recordToggle("dark", "Dark Mode", True)
    assert reload.willRun
    reload.recordToggle("speed", "Speed", False)
    assert not reload.willRun


def test_dismiss_clears_and_notifies_once(qapp: object, qtbot: QtBot) -> None:
    reload = TabSiteReload()
    reload.recordToggle("dark", "Dark Mode", True)
    with qtbot.waitSignal(reload.changed, timeout=0):
        reload.dismiss()
    with qtbot.assertNotEmitted(reload.changed):
        reload.dismiss()
    assert not reload.isPending
