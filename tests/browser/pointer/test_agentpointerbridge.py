import time

import pytest
from pytestqt.qtbot import QtBot

from kondor.browser.pointer.agentpointerbridge import AgentPointerBridge
from kondor.browser.pointer.realinputclock import CLOCK


@pytest.fixture
def bridge(qapp: object) -> AgentPointerBridge:
    return AgentPointerBridge()


def test_reports_the_agent_move(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    with qtbot.waitSignal(bridge.agentMoved) as moved:
        bridge.receive_report("pointermove", 10, 20)
    assert moved.args == [10, 20]


def test_a_click_moves_then_presses(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    with qtbot.waitSignals([bridge.agentMoved, bridge.agentPressed], order="strict"):
        bridge.receive_report("pointerdown", 5, 6)


def test_a_release_does_not_press(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    with qtbot.assertNotEmitted(bridge.agentPressed):
        bridge.receive_report("pointerup", 5, 6)


def test_ignores_events_right_after_real_input(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    CLOCK.note()
    with qtbot.assertNotEmitted(bridge.agentMoved):
        bridge.receive_report("pointermove", 1, 2)


def test_accepts_events_after_the_real_input_window(
    bridge: AgentPointerBridge, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    CLOCK.note()
    later = time.monotonic() + 1
    monkeypatch.setattr(time, "monotonic", lambda: later)
    with qtbot.waitSignal(bridge.agentMoved):
        bridge.receive_report("pointermove", 1, 2)
