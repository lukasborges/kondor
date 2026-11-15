from collections.abc import Iterator

import pytest

from kondor.app.remotecontrol.remotecontrol import RemoteControl


@pytest.fixture
def remote_control() -> Iterator[RemoteControl]:
    control = RemoteControl.instance()
    control.set_port(None)
    yield control
    control.set_port(None)
