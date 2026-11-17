import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlEngine
from PySide6.QtTest import QTest

from kondor.profiles.registry.profileregistry import ProfileRegistry
from tests.profiles.windowhost import create_kept
from tests.qmlsupport import captured_messages

pytestmark = pytest.mark.no_qt_log
DIALOG_HOST = """
import QtQuick.Controls
import Kondor
ApplicationWindow {
    width: 400
    height: 300
    visible: true
    property string savedAsNew: ""
    ProfileDialog {
        objectName: "dialog"
        onProfileSaved: (profileId, isNew) => savedAsNew += isNew ? "new;" : "edit;"
    }
}
"""


def open_dialog_for_new(engine: QQmlEngine) -> QObject:
    window = create_kept(engine, DIALOG_HOST)
    call(window.findChild(QObject, "dialog"), "openForNew")
    QTest.qWait(50)
    return window


def call(target: QObject, method: str, *arguments: object) -> None:
    QMetaObject.invokeMethod(target, method, Qt.ConnectionType.DirectConnection, *arguments)


def confirm(window: QObject) -> None:
    call(window.findChild(QObject, "dialog"), "confirm")


def test_dialog_creates_the_typed_profile(kondor_engine: QQmlEngine) -> None:
    window = open_dialog_for_new(kondor_engine)
    window.findChild(QObject, "nameField").setProperty("text", "Work")

    confirm(window)

    assert [profile.name for profile in ProfileRegistry().profiles()] == ["Default", "Work"]


def test_dialog_reports_a_created_profile_as_new(kondor_engine: QQmlEngine) -> None:
    window = open_dialog_for_new(kondor_engine)
    window.findChild(QObject, "nameField").setProperty("text", "Work")

    confirm(window)

    assert window.property("savedAsNew") == "new;"


def test_dialog_reports_an_edited_profile_as_not_new(kondor_engine: QQmlEngine) -> None:
    window = open_dialog_for_new(kondor_engine)
    dialog = window.findChild(QObject, "dialog")
    window.findChild(QObject, "nameField").setProperty("text", "Work")
    confirm(window)

    call(
        dialog,
        "openForEdit",
        Q_ARG("QVariant", {"id": dialog.property("profileId"), "name": "Work", "iconName": "flag"}),
    )
    confirm(window)

    assert window.property("savedAsNew") == "new;edit;"


def test_dialog_refuses_an_empty_name(kondor_engine: QQmlEngine) -> None:
    window = open_dialog_for_new(kondor_engine)

    confirm(window)

    assert len(ProfileRegistry().profiles()) == 1


def test_dialog_refuses_a_duplicate_name_and_says_why(kondor_engine: QQmlEngine) -> None:
    window = open_dialog_for_new(kondor_engine)
    window.findChild(QObject, "nameField").setProperty("text", "default")

    confirm(window)

    assert len(ProfileRegistry().profiles()) == 1
    assert window.findChild(QObject, "dialog").property("showsNameError") is True


def test_manage_window_loads_without_errors(kondor_engine: QQmlEngine) -> None:
    ProfileRegistry().add("Work", "flag")
    with captured_messages() as messages:
        window = create_kept(kondor_engine, "import Kondor\nManageProfilesWindow {}")
        window.property("width")
        call(window, "showWindow")
        QTest.qWait(100)

    assert [message for message in messages if "rror" in message or "undefined" in message] == []


def test_chooser_starts_without_a_choice(kondor_engine: QQmlEngine) -> None:
    window = create_kept(kondor_engine, "import Kondor\nProfileChooserWindow {}")

    assert window.property("chosenProfileId") == ""


def test_chooser_remembers_the_chosen_profile(kondor_engine: QQmlEngine) -> None:
    window = create_kept(kondor_engine, "import Kondor\nProfileChooserWindow {}")

    call(window, "choose", Q_ARG("QVariant", {"id": "abc"}))

    assert window.property("chosenProfileId") == "abc"
