import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_qt_log
REPOSITORY = Path(__file__).resolve().parents[3]
WEB_ENGINE_SECONDS = 15


def empty_profile_environment(home: Path, runtime: str) -> dict[str, str]:
    folders = {"XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data", "XDG_CACHE_HOME": "cache"}
    environment = {name: str(home / folder) for name, folder in folders.items()}
    return {
        **os.environ,
        **environment,
        "XDG_RUNTIME_DIR": runtime,
        "PYTHONPATH": str(REPOSITORY / "src"),
        "QT_QPA_PLATFORM": "offscreen",
    }


def has_child_process(process: subprocess.Popen[bytes]) -> bool:
    children = Path(f"/proc/{process.pid}/task/{process.pid}/children")
    return children.exists() and bool(children.read_text().strip())


def starts_web_engine(process: subprocess.Popen[bytes]) -> bool:
    deadline = time.monotonic() + WEB_ENGINE_SECONDS
    while time.monotonic() < deadline:
        if has_child_process(process):
            return True
        time.sleep(0.5)
    return False


def test_window_opens_with_an_empty_qml_cache(tmp_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="kondor-") as runtime:
        process = subprocess.Popen(
            [sys.executable, "-m", "kondor", "--new-instance", "about:blank"],
            cwd=REPOSITORY,
            env=empty_profile_environment(tmp_path, runtime),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            assert starts_web_engine(process), "startup hung before the window opened"
        finally:
            process.kill()
            process.wait()
