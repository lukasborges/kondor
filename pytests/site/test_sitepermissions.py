import pytest
from PySide6.QtCore import QUrl

from pytests.site.sitepermissionsharness import PermissionFixture, PermissionState, PermissionType

pytestmark = pytest.mark.no_qt_log

FIRST_ANSWER = 2
SECOND_ANSWER = 3


@pytest.fixture
def fixture(qapp: object) -> PermissionFixture:
    return PermissionFixture()


def test_answers_queued_permissions_in_order(fixture: PermissionFixture) -> None:
    origin = QUrl("https://queue.example")
    changes: list[int] = []
    fixture.tab.permissions.pendingChanged.connect(lambda: changes.append(len(changes) + 1))
    fixture.enqueue(origin, PermissionType.Geolocation)
    fixture.enqueue(origin, PermissionType.Notifications)
    assert len(changes) == 1
    assert fixture.pending_type() == PermissionType.Geolocation
    fixture.tab.permissions.answer(True)
    assert len(changes) == FIRST_ANSWER
    assert fixture.state_of(origin, PermissionType.Geolocation) == PermissionState.Granted
    assert fixture.pending_type() == PermissionType.Notifications
    fixture.tab.permissions.answer(False)
    assert len(changes) == SECOND_ANSWER
    assert fixture.state_of(origin, PermissionType.Notifications) == PermissionState.Denied
    assert not fixture.has_pending()


def test_navigating_away_denies_pending_permissions(fixture: PermissionFixture) -> None:
    origin = QUrl("https://leave.example")
    fixture.tab.setUrl(origin)
    fixture.enqueue_geolocation(origin)
    fixture.tab.setUrl(QUrl("https://other.example/"))
    assert fixture.geolocation_state(origin) == PermissionState.Denied
    assert not fixture.has_pending()


def test_navigating_within_same_origin_keeps_pending_permissions(
    fixture: PermissionFixture,
) -> None:
    origin = QUrl("https://stay.example")
    fixture.tab.setUrl(QUrl("https://stay.example/meet"))
    fixture.enqueue_geolocation(origin)
    fixture.tab.setUrl(QUrl("https://stay.example/meet#room"))
    assert fixture.has_pending()
    fixture.tab.setUrl(QUrl("https://stay.example/meet/room"))
    assert fixture.has_pending()
    assert fixture.geolocation_state(origin) == PermissionState.Ask


def test_navigating_to_another_origin_denies_pending_permissions(
    fixture: PermissionFixture,
) -> None:
    origin = QUrl("https://stay.example")
    fixture.tab.setUrl(QUrl("https://stay.example/meet"))
    fixture.enqueue_geolocation(origin)
    fixture.tab.setUrl(QUrl("https://elsewhere.example/"))
    assert fixture.geolocation_state(origin) == PermissionState.Denied
    assert not fixture.has_pending()
