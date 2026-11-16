import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROBE = Path(__file__).with_name("selectpopupprobe.py")
PROBE_TIMEOUT = 90
X11_ENVIRONMENT = {
    "QT_QPA_PLATFORM": "xcb",
    "QTWEBENGINE_DISABLE_SANDBOX": "1",
    "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu",
}


def run_probe_on_x11() -> str:
    result = subprocess.run(
        ["xvfb-run", "-a", sys.executable, str(PROBE)],
        env={**os.environ, **X11_ENVIRONMENT},
        capture_output=True,
        text=True,
        timeout=PROBE_TIMEOUT,
        check=False,
    )
    return result.stdout.strip() or result.stderr


@pytest.mark.skipif(shutil.which("xvfb-run") is None, reason="xvfb-run is not installed")
def test_mouse_click_on_a_select_option_changes_the_page_value() -> None:
    assert run_probe_on_x11().splitlines()[-1] == "title=b"
