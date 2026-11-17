import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.app.mcp.test_stdioserver import REPOSITORY, run_mcp

START_SECONDS = 90
PAGE = "data:text/html,<button onclick=\"document.title='clicked'\">Go</button>"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def is_listening(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


@pytest.fixture
def browser_port(tmp_path: Path) -> Iterator[int]:
    port = free_port()
    environment = {
        **os.environ,
        "PYTHONPATH": str(REPOSITORY / "src"),
        "QT_QPA_PLATFORM": "offscreen",
        "QTWEBENGINE_DISABLE_SANDBOX": "1",
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
    }
    command = [sys.executable, "-m", "kondor", "--remote-control", str(port)]
    process = subprocess.Popen(
        command, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    deadline = time.monotonic() + START_SECONDS
    while not is_listening(port) and time.monotonic() < deadline:
        time.sleep(0.5)
    yield port
    process.terminate()
    process.wait(timeout=30)


def call(request_id: int, name: str, arguments: dict[str, str]) -> str:
    params = {"name": name, "arguments": arguments}
    return json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": params}
    )


def test_controls_a_page_of_a_running_browser(tmp_path: Path, browser_port: int) -> None:
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        call(2, "navigate", {"url": PAGE}),
        call(3, "snapshot", {}),
        call(4, "click", {"uid": "0"}),
        call(5, "evaluate", {"expression": "document.title"}),
    ]

    completed = run_mcp([], lines, tmp_path)

    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert 'button "Go"' in responses[2]["result"]["content"][0]["text"]
    assert responses[4]["result"]["content"][0]["text"] == '"clicked"'
