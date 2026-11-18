import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[3]
SCENARIO = Path(__file__).with_name("pointerscenario.py")
SCRIPT = REPOSITORY / "src" / "kondor" / "browser" / "pointer" / "agentpointer.js"
MARKER = "RESULT"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def counts(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, int]]:
    profile = tmp_path_factory.mktemp("scenario")
    environment = {
        **os.environ,
        "PYTHONPATH": str(REPOSITORY / "src"),
        "QT_QPA_PLATFORM": "offscreen",
        "QTWEBENGINE_DISABLE_SANDBOX": "1",
        "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
        "XDG_CONFIG_HOME": str(profile / "config"),
        "XDG_DATA_HOME": str(profile / "data"),
        "XDG_CACHE_HOME": str(profile / "cache"),
    }
    command = [sys.executable, str(SCENARIO), str(free_port()), str(SCRIPT)]
    completed = subprocess.run(
        command, env=environment, capture_output=True, text=True, timeout=120, check=False
    )
    lines = [line for line in completed.stdout.splitlines() if line.startswith(MARKER)]
    assert lines, completed.stdout + completed.stderr
    return json.loads(lines[-1][len(MARKER) :])  # type: ignore[no-any-return]


def test_a_real_press_after_the_mouse_rested_shows_no_pointer(
    counts: dict[str, dict[str, int]],
) -> None:
    assert counts["real_press"] == {"moves": 0, "presses": 0}


def test_a_real_click_on_a_busy_page_that_shifts_the_layout_shows_no_pointer(
    counts: dict[str, dict[str, int]],
) -> None:
    assert counts["real_press_shifting_layout"] == {"moves": 0, "presses": 0}


def test_a_cdp_move_to_a_new_point_shows_the_pointer(counts: dict[str, dict[str, int]]) -> None:
    assert counts["cdp_move"]["moves"] >= 1


def test_a_scripted_click_shows_no_pointer(counts: dict[str, dict[str, int]]) -> None:
    assert counts["scripted_click"] == {"moves": 0, "presses": 0}


def test_enter_on_a_focused_button_shows_no_pointer(counts: dict[str, dict[str, int]]) -> None:
    assert counts["cdp_enter"] == {"moves": 0, "presses": 0}


def test_a_cdp_mouse_click_still_shows_the_pointer(counts: dict[str, dict[str, int]]) -> None:
    assert counts["cdp_click"]["moves"] >= 1
    assert counts["cdp_click"]["presses"] == 1
