import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlEngine
from PySide6.QtWebEngineCore import QWebEnginePermission

from tests.qmlsupport import error_text, load_component
from tests.site.sitepermissionsharness import PermissionFixture, PermissionType

pytestmark = pytest.mark.no_qt_log

READER_QML = """import QtQuick
import Kondor
QtObject {
    property var tab: null
    property var pending: tab ? tab.permissions.pending : null
    property string type: pending ? pending.permissionType : ""
    property string origin: pending ? pending.origin : ""
}
"""
ENQUEUER_QML = """import QtQuick
import Kondor
QtObject {
    function enqueueInto(tab, permission) { tab.permissions.enqueue(permission) }
}
"""
KEPT_COMPONENTS: list[object] = []
ORIGIN = QUrl("https://meet.example")


@pytest.fixture
def fixture(qapp: object) -> PermissionFixture:
    return PermissionFixture()


def create_kept(engine: QQmlEngine, source: str, properties: dict[str, object]) -> QObject:
    component = load_component(engine, source)
    created = component.createWithInitialProperties(properties)
    assert created is not None, error_text(component)
    KEPT_COMPONENTS.append(component)
    return created


def test_pending_is_readable_from_qml(
    kondor_engine: QQmlEngine, fixture: PermissionFixture
) -> None:
    fixture.enqueue_geolocation(ORIGIN)
    reader = create_kept(kondor_engine, READER_QML, {"tab": fixture.tab})
    assert reader.property("type") == str(PermissionType.Geolocation.value)
    assert QUrl(reader.property("origin")) == ORIGIN


def test_enqueue_from_qml_reaches_the_queue(
    kondor_engine: QQmlEngine, fixture: PermissionFixture
) -> None:
    enqueuer = create_kept(kondor_engine, ENQUEUER_QML, {})
    permission = fixture.query(ORIGIN, PermissionType.Notifications)
    assert fixture.has_pending() is False
    QMetaObject.invokeMethod(
        enqueuer,
        "enqueueInto",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", fixture.tab),
        Q_ARG("QVariant", permission),
    )
    assert fixture.pending_type() == PermissionType.Notifications


def test_invalid_permissions_are_ignored(fixture: PermissionFixture) -> None:
    fixture.tab.permissions.enqueue(QWebEnginePermission())
    assert not fixture.has_pending()
