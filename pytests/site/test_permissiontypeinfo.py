from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtWebEngineCore import QWebEnginePermission

Type = QWebEnginePermission.PermissionType
UNKNOWN_TYPE = 9999
SITE = "site.example"


class Expectation(NamedTuple):
    name: str
    type: int
    icon: str
    label: str
    sentence: str


def wants(what: str) -> str:
    return f"<b>{SITE}</b> wants to {what}."


EXPECTATIONS = (
    Expectation("microphone", Type.MediaAudioCapture.value, "audio-input-microphone",
                "Microphone", wants("use your <b>microphone</b>")),
    Expectation("camera", Type.MediaVideoCapture.value, "camera-web", "Camera",
                wants("use your <b>camera</b>")),
    Expectation("cameraAndMicrophone", Type.MediaAudioVideoCapture.value, "camera-web",
                "Camera and Microphone", wants("use your <b>camera</b> and <b>microphone</b>")),
    Expectation("screen", Type.DesktopVideoCapture.value, "video-display", "Screen",
                wants("share your <b>screen</b>")),
    Expectation("screenAndMicrophone", Type.DesktopAudioVideoCapture.value, "video-display",
                "Screen and Microphone", wants("share your <b>screen</b> and <b>microphone</b>")),
    Expectation("pointerLock", Type.MouseLock.value, "input-mouse", "Pointer Lock",
                wants("lock your <b>pointer</b>")),
    Expectation("notifications", Type.Notifications.value, "preferences-desktop-notification",
                "Notifications", wants("show you <b>notifications</b>")),
    Expectation("location", Type.Geolocation.value, "mark-location", "Location",
                wants("know your <b>location</b>")),
    Expectation("clipboard", Type.ClipboardReadWrite.value, "edit-paste", "Clipboard",
                wants("read your <b>clipboard</b>")),
    Expectation("localFonts", Type.LocalFontsAccess.value, "preferences-desktop-font",
                "Local Fonts", wants("use your <b>local fonts</b>")),
    Expectation("unknown", UNKNOWN_TYPE, "security-high", "Permission",
                f"<b>{SITE}</b> is requesting a <b>permission</b>."),
)


@pytest.fixture(scope="module")
def info(kondor_engine: QQmlEngine, staged_build: Path) -> Iterator[QObject]:
    path = staged_build / "qml" / "Kondor" / "site" / "PermissionTypeInfo.qml"
    component = QQmlComponent(kondor_engine, QUrl.fromLocalFile(str(path)))
    created = component.create()
    assert created is not None, component.errors()
    yield created
    created.deleteLater()


def call(info: QObject, method: str, *arguments: object) -> object:
    values = [Q_ARG("QVariant", argument) for argument in arguments]
    return QMetaObject.invokeMethod(info, method, Q_RETURN_ARG("QVariant"), *values)


@pytest.mark.parametrize("row", EXPECTATIONS, ids=[row.name for row in EXPECTATIONS])
def test_every_type_has_icon_label_and_sentence(info: QObject, row: Expectation) -> None:
    assert call(info, "iconFor", row.type) == row.icon
    assert call(info, "labelFor", row.type) == row.label
    assert call(info, "sentenceFor", row.type, SITE) == row.sentence


def test_host_comes_from_the_origin(info: QObject) -> None:
    assert call(info, "hostFor", "https://meet.jit.si/room") == "meet.jit.si"
