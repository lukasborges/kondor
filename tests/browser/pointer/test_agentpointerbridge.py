import time

import pytest
from pytestqt.qtbot import QtBot

from kondor.browser.pointer.agentpointerbridge import AgentPointerBridge
from kondor.browser.pointer.realinputclock import CLOCK


@pytest.fixture
def bridge(qapp: object) -> AgentPointerBridge:
    CLOCK.forget()
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


def later(monkeypatch: pytest.MonkeyPatch, seconds: float) -> None:
    moment = time.monotonic() + seconds
    monkeypatch.setattr(time, "monotonic", lambda: moment)


def test_ignores_a_move_right_after_real_input(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    CLOCK.note_activity()
    with qtbot.assertNotEmitted(bridge.agentMoved):
        bridge.receive_report("pointermove", 1, 2)


def test_ignores_a_move_600_ms_after_real_input(
    bridge: AgentPointerBridge, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    CLOCK.note_activity()
    later(monkeypatch, 0.6)
    with qtbot.assertNotEmitted(bridge.agentMoved):
        bridge.receive_report("pointermove", 1, 2)


def test_shows_a_move_1500_ms_after_real_input(
    bridge: AgentPointerBridge, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    CLOCK.note_activity()
    later(monkeypatch, 1.5)
    with qtbot.waitSignal(bridge.agentMoved):
        bridge.receive_report("pointermove", 1, 2)


def test_ignores_the_press_report_that_arrives_500_ms_late(
    bridge: AgentPointerBridge, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    CLOCK.note_press()
    later(monkeypatch, 0.5)
    with qtbot.assertNotEmitted(bridge.agentMoved), qtbot.assertNotEmitted(bridge.agentPressed):
        bridge.receive_report("pointerdown", 1, 2)


def test_pairs_each_real_press_with_one_report(bridge: AgentPointerBridge, qtbot: QtBot) -> None:
    CLOCK.note_press()
    CLOCK.note_press()
    bridge.receive_report("pointerdown", 1, 2)
    bridge.receive_report("pointerdown", 1, 2)
    with qtbot.waitSignal(bridge.agentPressed):
        bridge.receive_report("pointerdown", 3, 4)


def test_drops_real_presses_older_than_2_seconds(
    bridge: AgentPointerBridge, qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    CLOCK.note_press()
    later(monkeypatch, 2.5)
    with qtbot.waitSignal(bridge.agentPressed):
        bridge.receive_report("pointerdown", 1, 2)
