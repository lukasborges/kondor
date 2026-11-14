from collections.abc import Iterator

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from pytestqt.qtbot import QtBot

from kondor.browser.profile.profilemanager import ProfileManager
from pytests.qmlsupport import error_text, load_component
from pytests.site.sitepermissionsharness import (
    PermissionFixture,
    PermissionState,
    PermissionType,
    grant_geolocation,
)

pytestmark = pytest.mark.no_qt_log

PERMISSION_BAR_QML = "import QtQuick\nimport Kondor\nPermissionBar {}\n"
TEXT_FINDER_QML = """import QtQuick
QtObject {
    function texts(root) {
        const own = root.text !== undefined ? [root.text] : []
        return own.concat(root.children.map(texts)).join(" ")
    }
}
"""
DIALOG_QML = "import QtQuick\nimport Kondor\nSitePermissionsDialog {}\n"
ORIGIN = QUrl("https://meet.example")
KEPT_COMPONENTS: list[QObject] = []


@pytest.fixture
def fixture(qapp: object) -> PermissionFixture:
    return PermissionFixture()


def create_kept(
    engine: QQmlEngine, source: str, properties: dict[str, object] | None = None
) -> QObject:
    component = load_component(engine, source)
    created = component.createWithInitialProperties(properties or {})
    assert created is not None, error_text(component)
    QQmlEngine.setObjectOwnership(created, QQmlEngine.ObjectOwnership.CppOwnership)
    KEPT_COMPONENTS.append(component)
    return created


def all_texts(engine: QQmlEngine, root: QObject) -> str:
    finder = create_kept(engine, TEXT_FINDER_QML)
    holder = Q_ARG("QVariant", root)
    result = Q_RETURN_ARG("QVariant")
    connection = Qt.ConnectionType.DirectConnection
    return str(QMetaObject.invokeMethod(finder, "texts", connection, result, holder))


def rows_of(window: QQuickWindow) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = window.property("rows").toVariant()
    return rows


def permission_bar(engine: QQmlEngine, fixture: PermissionFixture) -> QQuickItem:
    return create_kept(engine, PERMISSION_BAR_QML, {"tab": fixture.tab})


@pytest.fixture
def dialog(kondor_engine: QQmlEngine) -> Iterator[QQuickWindow]:
    window = create_kept(kondor_engine, DIALOG_QML)
    QMetaObject.invokeMethod(window, "showWindow")
    yield window
    window.close()


def test_request_bar_shows_the_pending_permission(
    kondor_engine: QQmlEngine, fixture: PermissionFixture
) -> None:
    fixture.enqueue_geolocation(ORIGIN)
    bar = permission_bar(kondor_engine, fixture)
    assert bar.property("visible") is True
    text = all_texts(kondor_engine, bar)
    assert "meet.example" in text
    assert "location" in text


def test_answering_the_request_bar_grants_and_hides_it(
    kondor_engine: QQmlEngine, fixture: PermissionFixture
) -> None:
    fixture.enqueue_geolocation(ORIGIN)
    bar = permission_bar(kondor_engine, fixture)
    fixture.tab.permissions.answer(True)
    assert bar.property("visible") is False
    assert fixture.geolocation_state(ORIGIN) == PermissionState.Granted


def test_dialog_lists_decisions(qtbot: QtBot, dialog: QQuickWindow) -> None:
    grant_geolocation(QUrl("https://permissions.example"))
    QMetaObject.invokeMethod(dialog, "reload")
    assert dialog.isVisible()
    rows = rows_of(dialog)
    assert len(rows) == 1
    assert rows[0]["site"] == "permissions.example"
    assert rows[0]["perm"] == "Location"
    assert rows[0]["granted"] is True


def test_dialog_revokes_decisions(dialog: QQuickWindow) -> None:
    origin = QUrl("https://permissions.example")
    grant_geolocation(origin)
    QMetaObject.invokeMethod(dialog, "reload")
    permission = rows_of(dialog)[0]["permission"]
    assert permission.isValid()
    QMetaObject.invokeMethod(
        dialog, "revoke", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", permission)
    )
    assert rows_of(dialog) == []
    profile = ProfileManager.instance().defaultProfile()
    assert (
        profile.queryPermission(origin, PermissionType.Geolocation).state() == PermissionState.Ask
    )
