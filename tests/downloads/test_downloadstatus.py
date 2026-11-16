from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QLocale, QMetaObject, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from kondor.downloads.downloadmanager import DownloadManager

MEGABYTE = 1000 * 1000
State = DownloadManager.State


class Case(NamedTuple):
    name: str
    state: int
    is_paused: bool
    received: int
    total: int
    speed: str
    reason: str
    text: str


CASES = (
    Case("requested", State.Requested, False, 0, 0, "", "", "Waiting for confirmation…"),
    Case(
        "progressWithTotalAndSpeed",
        State.InProgress,
        False,
        MEGABYTE,
        4 * MEGABYTE,
        "1 MB/s",
        "",
        "%R of %T — 1 MB/s",
    ),
    Case("progressWithTotal", State.InProgress, False, MEGABYTE, 4 * MEGABYTE, "", "", "%R of %T"),
    Case(
        "progressWithSpeed",
        State.InProgress,
        False,
        MEGABYTE,
        0,
        "1 MB/s",
        "",
        "%R downloaded — 1 MB/s",
    ),
    Case(
        "progressWithoutTotalOrSpeed",
        State.InProgress,
        False,
        MEGABYTE,
        0,
        "",
        "",
        "%R downloaded",
    ),
    Case(
        "pausedWithTotal",
        State.InProgress,
        True,
        MEGABYTE,
        4 * MEGABYTE,
        "",
        "",
        "Paused — %R of %T",
    ),
    Case("pausedWithoutTotal", State.InProgress, True, MEGABYTE, 0, "", "", "Paused — %R"),
    Case("completed", State.Completed, False, MEGABYTE, MEGABYTE, "", "", "Completed — %R"),
    Case("canceled", State.Cancelled, False, 0, 0, "", "", "Canceled"),
    Case(
        "failedWithReason",
        State.Interrupted,
        False,
        0,
        0,
        "",
        "Network failed",
        "Failed — Network failed",
    ),
    Case("failedWithoutReason", State.Interrupted, False, 0, 0, "", "", "Failed"),
)


def expected_text(pattern: str) -> str:
    received = QLocale().formattedDataSize(MEGABYTE)
    total = QLocale().formattedDataSize(4 * MEGABYTE)
    return pattern.replace("%R", received).replace("%T", total)


def download_map(case: Case) -> dict[str, object]:
    return {
        "state": int(case.state),
        "isPaused": case.is_paused,
        "receivedBytes": case.received,
        "totalBytes": case.total,
        "speedText": case.speed,
        "interruptReasonString": case.reason,
    }


@pytest.fixture(scope="module")
def download_status(kondor_engine: QQmlEngine, staged_build: Path) -> Iterator[QObject]:
    path = staged_build / "qml" / "Kondor" / "downloads" / "DownloadStatus.qml"
    component = QQmlComponent(kondor_engine, QUrl.fromLocalFile(str(path)))
    status = component.create()
    assert status is not None, component.errors()
    yield status
    status.deleteLater()


@pytest.mark.parametrize("case", CASES, ids=[case.name for case in CASES])
def test_describes_every_state(case: Case, download_status: QObject) -> None:
    text = QMetaObject.invokeMethod(
        download_status, "text", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", download_map(case))
    )
    assert text == expected_text(case.text)
