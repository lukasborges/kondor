import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.conftest import (
    CHROMIUM_FLAGS_VARIABLE,
    NO_DESKTOP_SERVICES,
    NO_GPU_FLAG,
    NO_KWALLET_VARIABLE,
    SANDBOX_VARIABLE,
)

pytestmark = pytest.mark.no_qt_log
REPOSITORY = Path(__file__).resolve().parents[2]
FORBIDDEN_OUTPUT = (
    "ReferenceError",
    "TypeError",
    "Cannot assign",
    "is not a type",
    "Kondor: cannot",
)
STARTUP_SECONDS = 10
SOCKET_SECONDS = 15
FORWARD_SECONDS = 5


def isolated_environment(home: Path) -> dict[str, str]:
    environment = dict(os.environ) | NO_DESKTOP_SERVICES
    environment.update(
        {
            "XDG_CONFIG_HOME": str(home / "config"),
            "XDG_DATA_HOME": str(home / "data"),
            "XDG_CACHE_HOME": str(home / "cache"),
            "XDG_STATE_HOME": str(home / "state"),
            "PYTHONPATH": str(REPOSITORY / "src"),
            "QT_QPA_PLATFORM": "offscreen",
            SANDBOX_VARIABLE: "1",
            CHROMIUM_FLAGS_VARIABLE: NO_GPU_FLAG,
            NO_KWALLET_VARIABLE: "1",
        }
    )
    return environment


def start_kondor(environment: dict[str, str], *arguments: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", "kondor", *arguments],
        cwd=REPOSITORY,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def run_kondor(environment: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "kondor", *arguments],
        cwd=REPOSITORY,
        env=environment,
        capture_output=True,
        text=True,
        timeout=STARTUP_SECONDS,
        check=False,
    )


def stop(process: subprocess.Popen[str]) -> str:
    process.terminate()
    try:
        return process.communicate(timeout=STARTUP_SECONDS)[1]
    except subprocess.TimeoutExpired:
        process.kill()
        return process.communicate()[1]


@pytest.fixture
def environment(tmp_path: Path) -> Iterator[dict[str, str]]:
    with tempfile.TemporaryDirectory(prefix="kondor-") as short_home:
        yield isolated_environment(tmp_path) | {"XDG_RUNTIME_DIR": short_home}


@pytest.fixture
def running(environment: dict[str, str]) -> Iterator[list[subprocess.Popen[str]]]:
    processes: list[subprocess.Popen[str]] = []
    yield processes
    for process in processes:
        stop(process)


def test_version_option_prints_the_version(environment: dict[str, str]) -> None:
    result = run_kondor(environment, "--version")

    assert result.returncode == 0
    assert "Kondor 0.3.3" in result.stdout


def test_help_lists_the_options(environment: dict[str, str]) -> None:
    result = run_kondor(environment, "--help")

    assert result.returncode == 0
    assert result.stdout.startswith("Usage: kondor [options] [urls...]")
    for option in ("--private", "--new-window", "--new-instance", "--load-extension <dir>"):
        assert option in result.stdout


def test_app_starts_without_qml_errors(
    environment: dict[str, str], running: list[subprocess.Popen[str]]
) -> None:
    process = start_kondor(environment, "--new-instance", "about:blank")
    running.append(process)
    time.sleep(STARTUP_SECONDS)

    assert process.poll() is None
    errors = stop(process)
    assert not [word for word in FORBIDDEN_OUTPUT if word in errors], errors


SERVER_NAME_CODE = """
from PySide6.QtCore import QCoreApplication
from kondor.app.instance.singleinstance import SingleInstance
app = QCoreApplication([])
QCoreApplication.setOrganizationName("KDE")
QCoreApplication.setApplicationName("Kondor")
print(SingleInstance.server_name())
"""


def socket_exists(environment: dict[str, str]) -> bool:
    name = subprocess.run(
        [sys.executable, "-c", SERVER_NAME_CODE],
        cwd=REPOSITORY,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(name).exists()


def wait_for_socket(environment: dict[str, str]) -> None:
    deadline = time.monotonic() + SOCKET_SECONDS
    while time.monotonic() < deadline:
        if socket_exists(environment):
            return
        time.sleep(0.5)
    pytest.fail("the first instance never listened")


def test_second_launch_forwards_to_the_first(
    environment: dict[str, str], running: list[subprocess.Popen[str]]
) -> None:
    running.append(start_kondor(environment))
    wait_for_socket(environment)

    second = subprocess.run(
        [sys.executable, "-m", "kondor", "https://kde.org"],
        cwd=REPOSITORY,
        env=environment,
        capture_output=True,
        text=True,
        timeout=FORWARD_SECONDS,
        check=False,
    )

    assert second.returncode == 0
