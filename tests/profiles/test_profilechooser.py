import os
import subprocess
import sys
from pathlib import Path

CHOOSER_SCRIPT = """
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.startup.profilechooser import ask_for_profile

app = QApplication(["kondor"])
ProfileRegistry().add("Work", "flag")
QTimer.singleShot(2000, lambda: [w.close() for w in QGuiApplication.topLevelWindows()])
print("chosen:", ask_for_profile(app))
"""
REPOSITORY = Path(__file__).resolve().parents[2]
TIMEOUT_SECONDS = 60


def run_chooser_in_fresh_process(home: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        **os.environ,
        "PYTHONPATH": str(REPOSITORY / "src"),
        "QT_QPA_PLATFORM": "offscreen",
        "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_DATA_HOME": str(home / "data"),
        "XDG_CACHE_HOME": str(home / "cache"),
    }
    return subprocess.run(
        [sys.executable, "-c", CHOOSER_SCRIPT],
        env=environment,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        check=False,
    )


def test_chooser_loads_in_a_fresh_process_and_returns_after_closing(tmp_path: Path) -> None:
    result = run_chooser_in_fresh_process(tmp_path)

    assert "chosen: None" in result.stdout, result.stderr
