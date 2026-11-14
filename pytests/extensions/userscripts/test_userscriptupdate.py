from collections.abc import Iterator

import pytest
from pytestqt.qtbot import QtBot

from kondor.core.settings.settings import Settings
from kondor.extensions.catalog.extensioncatalog import ExtensionCatalog
from kondor.extensions.extensionmanager import ExtensionManager
from pytests.extensions.pageserver import PageServer

WAIT_MILLISECONDS = 10000
SCRIPT = (
    "// ==UserScript==\n// @name Served\n// @namespace test\n// @version {version}\n"
    "// @match *://127.0.0.1/*\n{extra}\n// @updateURL {meta}\n// @downloadURL {script}\n"
    "// ==/UserScript==\nvoid 0;\n"
)


@pytest.fixture
def server(work: str) -> Iterator[PageServer]:
    yield PageServer({})


def script_text(server: PageServer, version: str, extra: str = "") -> bytes:
    meta, script = server.url("/s.meta.js").toString(), server.url("/s.user.js").toString()
    return SCRIPT.format(version=version, extra=extra, meta=meta, script=script).encode()


def install_from_server(qtbot: QtBot, server: PageServer) -> None:
    server.bodies["/s.user.js"] = script_text(server, "1.0")
    manager = ExtensionManager.instance()
    manager.inspectUserScript(server.url("/s.user.js"))
    qtbot.waitUntil(lambda: bool(manager.pendingInstall.get("valid")), timeout=WAIT_MILLISECONDS)
    manager.confirmInstall()
    Settings.instance().setProperty("extensionsAutoUpdate", True)


def publish(server: PageServer, text: bytes) -> None:
    server.bodies["/s.meta.js"] = text
    server.bodies["/s.user.js"] = text
    ExtensionCatalog.instance().check_for_updates()


def first_id() -> str:
    manager = ExtensionManager.instance()
    return str(manager.data(manager.index(0, 0), ExtensionManager.Role.IdRole))


def test_silent_update_keeps_access(qtbot: QtBot, server: PageServer) -> None:
    install_from_server(qtbot, server)
    publish(server, script_text(server, "1.1"))
    manager = ExtensionManager.instance()
    qtbot.waitUntil(
        lambda: manager.installedVersion(first_id()) == "1.1.0", timeout=WAIT_MILLISECONDS
    )


def test_broader_update_needs_review(qtbot: QtBot, server: PageServer) -> None:
    install_from_server(qtbot, server)
    publish(server, script_text(server, "1.2", "// @match *://localhost/*"))
    manager = ExtensionManager.instance()
    role = ExtensionManager.Role.UpdateNeedsReviewRole
    qtbot.waitUntil(
        lambda: bool(manager.data(manager.index(0, 0), role)), timeout=WAIT_MILLISECONDS
    )
    assert manager.installedVersion(first_id()) == "1.0.0"
