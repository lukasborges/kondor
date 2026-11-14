from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject
from PySide6.QtQml import QJSValue, QQmlComponent, QQmlEngine
from pytestqt.qtbot import QtBot

from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.extensionsharness import (
    apply_settings,
    install_sample,
    sample_package,
    write_file,
)
from pytests.qmlsupport import error_text, load_component

SETTINGS_DIALOG_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    ExtensionSettingsDialog { id: dialog; objectName: "dialog" }
}
"""
SCHEMA_SIZE = 4
INSTALL_DIALOG_QML = """import QtQuick
import QtQuick.Controls
import Kondor
ApplicationWindow {
    visible: true
    InstallExtensionDialog { id: dialog; objectName: "dialog"; parent: Overlay.overlay }
}
"""


class DialogHost:
    def __init__(self, engine: QQmlEngine) -> None:
        self._engine = engine
        self._window: QObject | None = None
        self._component: QQmlComponent | None = None

    def open(self, source: str) -> QObject:
        self._component = load_component(self._engine, source)
        self._window = self._component.create()
        assert self._window is not None, error_text(self._component)
        QQmlEngine.setObjectOwnership(self._window, QQmlEngine.ObjectOwnership.CppOwnership)
        dialog = self._window.findChild(QObject, "dialog")
        assert dialog is not None
        return dialog

    def close(self) -> None:
        if self._window is not None:
            self._window.deleteLater()
            self._window = None


@pytest.fixture
def host(kondor_engine: QQmlEngine, work: str) -> Iterator[DialogHost]:
    dialog_host = DialogHost(kondor_engine)
    yield dialog_host
    dialog_host.close()


def js_property(dialog: QObject, name: str) -> Any:
    value = dialog.property(name)
    return value.toVariant() if isinstance(value, QJSValue) else value


def manager() -> ExtensionManager:
    return ExtensionManager.instance()


def greeting() -> str:
    return str(manager().settingValues("sample")["greeting"])


def set_value(dialog: QObject, key: str, value: str) -> None:
    QMetaObject.invokeMethod(dialog, "setValue", Q_ARG("QVariant", key), Q_ARG("QVariant", value))


def open_settings_for_sample(host: DialogHost) -> QObject:
    dialog = host.open(SETTINGS_DIALOG_QML)
    QMetaObject.invokeMethod(dialog, "openFor", Q_ARG("QVariant", "sample"))
    return dialog


def test_configure_dialog_writes_values_on_accept(host: DialogHost, work: str) -> None:
    assert install_sample(work)
    dialog = open_settings_for_sample(host)
    assert js_property(dialog, "values")["greeting"] == "hello"
    assert len(js_property(dialog, "schema")) == SCHEMA_SIZE
    set_value(dialog, "greeting", "ola")
    dialog.setProperty("privateAllowed", True)
    assert greeting() == "hello"
    QMetaObject.invokeMethod(dialog, "accept")
    assert greeting() == "ola"
    assert manager().data(manager().index(0, 0), ExtensionManager.Role.PrivateAllowedRole) is True


def test_restore_defaults_stays_pending(host: DialogHost, work: str) -> None:
    assert install_sample(work)
    apply_settings("sample", {"greeting": "ola"})
    dialog = open_settings_for_sample(host)
    QMetaObject.invokeMethod(dialog, "restoreDefaults")
    assert js_property(dialog, "values")["greeting"] == "hello"
    assert greeting() == "ola"


def test_install_dialog_shows_pending_install(host: DialogHost, work: str, qtbot: QtBot) -> None:
    dialog = host.open(INSTALL_DIALOG_QML)
    assert not dialog.property("visible")
    manager().inspectFile(sample_package(work))
    assert dialog.property("isValid")
    qtbot.waitUntil(lambda: bool(dialog.property("visible")))
    assert not dialog.property("replacing")


def test_closing_the_install_dialog_drops_the_pending_install(
    host: DialogHost, work: str, qtbot: QtBot
) -> None:
    dialog = host.open(INSTALL_DIALOG_QML)
    manager().inspectFile(sample_package(work))
    qtbot.waitUntil(lambda: bool(dialog.property("visible")))
    QMetaObject.invokeMethod(dialog, "close")
    qtbot.waitUntil(lambda: manager().pendingInstall == {})


def test_not_an_extension_shows_only_the_error(host: DialogHost, work: str, qtbot: QtBot) -> None:
    dialog = host.open(INSTALL_DIALOG_QML)
    assert write_file(f"{work}/bad.kondorext", b"nope")
    manager().inspectFile(f"{work}/bad.kondorext")
    assert not dialog.property("isValid")
    assert dialog.property("hasInfo")
    qtbot.waitUntil(lambda: bool(dialog.property("visible")))
    manager().cancelInstall()
