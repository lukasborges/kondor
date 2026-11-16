import pytest
from PySide6.QtCore import QMetaObject, QObject
from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.core.settings.settings import Settings
from tests.qmlsupport import error_text, load_component
from tests.settings.settingswindowharness import SettingsWindowHarness

pytestmark = pytest.mark.no_qt_log

PERFORMANCE_TAB = 3
DEFAULT_MINUTES = 30
DEFAULT_INDEX = 1
SLEEP_OPTIONS = {"tabSleepEnabled": False, "tabSleepMinutes": 120}
TAB_QML = """
import QtQuick
import Kondor
Item {
    function turnSleepOff() { draft.tabSleepEnabled = false }
    GeneralPerformanceTab { draft: SettingsDraft { id: draft } }
}
"""
KEPT_COMPONENTS: list[QQmlComponent] = []


def performance_tab(engine: QQmlEngine) -> QObject:
    component = load_component(engine, TAB_QML)
    created = component.create()
    assert created is not None, error_text(component)
    KEPT_COMPONENTS.append(component)
    return created


def open_performance_tab(harness: SettingsWindowHarness) -> None:
    assert harness.show_exposed()
    harness.window.setProperty("generalTab", PERFORMANCE_TAB)


def test_performance_tab_shows_the_defaults(kondor_engine: QQmlEngine) -> None:
    tab = performance_tab(kondor_engine)
    assert tab.findChild(QObject, "sleepCheck").property("checked") is True
    assert tab.findChild(QObject, "sleepAfterCombo").property("currentIndex") == DEFAULT_INDEX


def test_combo_box_is_disabled_when_the_check_box_is_off(kondor_engine: QQmlEngine) -> None:
    tab = performance_tab(kondor_engine)
    QMetaObject.invokeMethod(tab, "turnSleepOff")
    assert tab.findChild(QObject, "sleepAfterCombo").property("enabled") is False


def test_apply_writes_both_options(settings_window: SettingsWindowHarness) -> None:
    open_performance_tab(settings_window)
    for name, value in SLEEP_OPTIONS.items():
        settings_window.pending().setProperty(name, value)
    settings_window.invoke("applyChanges")
    for name, value in SLEEP_OPTIONS.items():
        assert Settings.instance().property(name) == value


def test_defaults_restore_both_options(settings_window: SettingsWindowHarness) -> None:
    open_performance_tab(settings_window)
    draft = settings_window.pending()
    for name, value in SLEEP_OPTIONS.items():
        draft.setProperty(name, value)
    settings_window.invoke("restoreDefaults")
    assert draft.property("tabSleepEnabled") is True
    assert draft.property("tabSleepMinutes") == DEFAULT_MINUTES
