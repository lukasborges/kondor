import pytest

from kondor.app.commandline.startupargs import StartupArgs
from kondor.app.windows.windowlaunch import should_restore_session

pytestmark = pytest.mark.usefixtures("qapp")


def test_restores_session_when_restart_asks_for_it() -> None:
    StartupArgs.instance().set_restore_session(True)
    try:
        assert should_restore_session()
    finally:
        StartupArgs.instance().set_restore_session(False)
