from typing import NamedTuple

import pytest
from PySide6.QtCore import QSettings, QUrl

from kondor.browser.zoommanager import ZoomManager

KDE_ZOOM_KEY = "SiteZoom/kde.org"
ZOOMED_IN = 1.25


class Step(NamedTuple):
    current: float
    direction: int
    expected: float


@pytest.fixture
def zoom(qapp: object) -> ZoomManager:
    QSettings("KDE", "Kondor").remove("SiteZoom")
    return ZoomManager.instance()


def has_kde_zoom_key() -> bool:
    return bool(QSettings("KDE", "Kondor").contains(KDE_ZOOM_KEY))


def test_host_of(zoom: ZoomManager) -> None:
    assert zoom.hostOf(QUrl("https://KDE.org/a?b")) == "kde.org"
    assert zoom.hostOf(QUrl("about:blank")) == ""
    assert zoom.hostOf(QUrl("file:///tmp/a.html")) == ""


def test_save_and_reset(zoom: ZoomManager) -> None:
    changes: list[tuple[str, float]] = []
    zoom.zoomChanged.connect(lambda host, factor: changes.append((host, factor)))
    assert zoom.zoomFor("kde.org") == 1.0
    zoom.setZoomFor("kde.org", ZOOMED_IN)
    assert zoom.zoomFor("kde.org") == ZOOMED_IN
    assert zoom.zoomFor("example.com") == 1.0
    assert has_kde_zoom_key()
    zoom.setZoomFor("kde.org", ZOOMED_IN)
    assert len(changes) == 1
    zoom.setZoomFor("kde.org", 1.0)
    assert not has_kde_zoom_key()
    assert changes == [("kde.org", ZOOMED_IN), ("kde.org", 1.0)]


STEPS = (
    Step(1.0, 1, 1.1),
    Step(1.1, 1, 1.25),
    Step(1.0, -1, 0.9),
    Step(5.0, 1, 5.0),
    Step(0.3, -1, 0.3),
    Step(1.2, 1, 1.25),
    Step(1.2, -1, 1.1),
)


@pytest.mark.parametrize("row", STEPS)
def test_step_levels(zoom: ZoomManager, row: Step) -> None:
    assert zoom.step(row.current, row.direction) == row.expected
