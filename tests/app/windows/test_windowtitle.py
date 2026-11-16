from collections.abc import Iterator

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from tests.qmlsupport import error_text, load_component

WINDOW_QML = """
import QtQuick
import Kondor

WindowTitle {
    tab: QtObject { %s }
    isPrivateWindow: %s
}
"""
NEW_TAB = "property bool newTabPage: true; property bool isPrivate: %s; property string title: ''"
PAGE = (
    "property bool newTabPage: false; property bool isPrivate: %s; property string title: 'DM test'"
)
KEPT_COMPONENTS: list[QQmlComponent] = []


@pytest.fixture(autouse=True)
def application_name(kondor_types: None) -> Iterator[None]:
    previous = QGuiApplication.applicationDisplayName()
    QGuiApplication.setApplicationDisplayName("Kondor Browser")
    yield
    QGuiApplication.setApplicationDisplayName(previous)


def title_text(engine: QQmlEngine, tab: str, private: bool) -> object:
    flag = str(private).lower()
    component = load_component(engine, WINDOW_QML % (tab % flag, flag))
    KEPT_COMPONENTS.append(component)
    holder = component.create()
    assert holder is not None, error_text(component)
    return holder.property("text")


def test_private_new_tab_title_names_the_application_once(kondor_engine: QQmlEngine) -> None:
    expected = "New Private Tab — Private Browsing — Kondor Browser"
    assert title_text(kondor_engine, NEW_TAB, True) == expected


def test_private_page_title_names_the_application_once(kondor_engine: QQmlEngine) -> None:
    expected = "DM test — Private Browsing — Kondor Browser"
    assert title_text(kondor_engine, PAGE, True) == expected


def test_normal_new_tab_title_is_unchanged(kondor_engine: QQmlEngine) -> None:
    assert title_text(kondor_engine, NEW_TAB, False) == "New Tab — Kondor Browser"


def test_normal_page_title_is_unchanged(kondor_engine: QQmlEngine) -> None:
    assert title_text(kondor_engine, PAGE, False) == "DM test — Kondor Browser"
