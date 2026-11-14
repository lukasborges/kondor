from collections.abc import Callable, Iterator
from typing import Any

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager

from kondor.extensions.userscripts.userscriptdownload import UserScriptDownload
from pytests.extensions.pageserver import PageServer

MAX_BYTES = 5 * 1024 * 1024
SCRIPT = (
    b"// ==UserScript==\n// @name N\n// @match *://*/*\n"
    b"// @require lib.js\n// @require /two.js\n// ==/UserScript==\nmain();\n"
)
BODIES = {"/a.user.js": SCRIPT, "/lib.js": b"one();", "/two.js": b"two();"}


@pytest.fixture
def network(qapp: object) -> Iterator[QNetworkAccessManager]:
    manager = QNetworkAccessManager()
    yield manager
    manager.deleteLater()


def run_download(
    qtbot: Any, task: UserScriptDownload, start: Callable[[], None]
) -> tuple[Any, str]:
    with qtbot.waitSignal(task.finished, timeout=10000) as blocker:
        start()
    return blocker.args[0], blocker.args[1]


def download(qtbot: Any, network: QNetworkAccessManager, url: QUrl) -> tuple[Any, str]:
    task = UserScriptDownload(network, None)
    return run_download(qtbot, task, lambda: task.start(url))


def download_metadata(qtbot: Any, network: QNetworkAccessManager, url: QUrl) -> tuple[Any, str]:
    task = UserScriptDownload(network, None)
    return run_download(qtbot, task, lambda: task.start_metadata_only(url))


def test_fetches_the_script_and_its_requirements_in_order(
    qtbot: Any, network: QNetworkAccessManager
) -> None:
    server = PageServer(BODIES)
    source, error = download(qtbot, network, server.url("/a.user.js"))
    assert error == ""
    assert source.script == SCRIPT
    assert source.required_scripts == [b"one();", b"two();"]
    assert server.requests == ["/a.user.js", "/lib.js", "/two.js"]


def test_metadata_only_skips_requirements(qtbot: Any, network: QNetworkAccessManager) -> None:
    server = PageServer(BODIES)
    source, error = download_metadata(qtbot, network, server.url("/a.user.js"))
    assert error == ""
    assert source.metadata.name == "N"
    assert source.required_scripts == []
    assert server.requests == ["/a.user.js"]


def test_unsupported_scheme_fails(qtbot: Any, network: QNetworkAccessManager) -> None:
    _source, error = download(qtbot, network, QUrl("ftp://example.com/a.user.js"))
    assert error == "Unsupported address: ftp://example.com/a.user.js"


def test_oversized_script_fails(qtbot: Any, network: QNetworkAccessManager) -> None:
    server = PageServer({"/big.user.js": SCRIPT + b"x" * (MAX_BYTES + 1)})
    _source, error = download(qtbot, network, server.url("/big.user.js"))
    assert error == "The script is larger than 5 MiB"
