from pytestqt.qtbot import QtBot

from kondor.browser.tabs.features.tabextensionitems import TabExtensionItems


def test_set_checked_notifies_only_on_change(qapp: object, qtbot: QtBot) -> None:
    items = TabExtensionItems()
    with qtbot.waitSignal(items.changed, timeout=0):
        items.setChecked("ext", "item", True)
    with qtbot.assertNotEmitted(items.changed):
        items.setChecked("ext", "item", True)
    assert items.isChecked("ext", "item")


def test_trigger_flips_a_checkable_item(qapp: object, qtbot: QtBot) -> None:
    items = TabExtensionItems()
    with qtbot.waitSignal(items.triggered, timeout=0) as first:
        items.trigger("ext", "item", True)
    assert first.args == ["ext", "item", True]
    with qtbot.waitSignal(items.triggered, timeout=0) as second:
        items.trigger("ext", "item", True)
    assert second.args == ["ext", "item", False]


def test_trigger_of_a_plain_item_is_not_checked(qapp: object, qtbot: QtBot) -> None:
    items = TabExtensionItems()
    with qtbot.waitSignal(items.triggered, timeout=0) as signal:
        items.trigger("ext", "item", False)
    assert signal.args == ["ext", "item", False]
    assert not items.isChecked("ext", "item")
