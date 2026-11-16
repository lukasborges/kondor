from pytestqt.qtbot import QtBot

from kondor.browser.tabs.features.tabsleep import TabSleep

SECONDS_IDLE = 90.0


def test_set_sleeping_notifies_only_on_a_change(qapp: object, qtbot: QtBot) -> None:
    sleep = TabSleep()
    with qtbot.waitSignal(sleep.sleepingChanged, timeout=100):
        sleep.setSleeping(True)
    with qtbot.assertNotEmitted(sleep.sleepingChanged):
        sleep.setSleeping(True)
    assert sleep.sleeping


def test_put_to_sleep_emits_sleep_requested(qapp: object, qtbot: QtBot) -> None:
    sleep = TabSleep()
    with qtbot.waitSignal(sleep.sleepRequested, timeout=100):
        sleep.putToSleep()


def test_request_idle_sleep_emits_idle_sleep_requested(qapp: object, qtbot: QtBot) -> None:
    sleep = TabSleep()
    with qtbot.waitSignal(sleep.idleSleepRequested, timeout=100):
        sleep.requestIdleSleep()


def test_active_tab_has_no_inactive_seconds(qapp: object) -> None:
    sleep = TabSleep()
    sleep.mark_active()
    assert sleep.inactive_seconds(1000.0) == 0.0


def test_inactive_seconds_grow_after_mark_inactive(qapp: object) -> None:
    sleep = TabSleep()
    sleep.mark_inactive(100.0)
    assert sleep.inactive_seconds(100.0 + SECONDS_IDLE) == SECONDS_IDLE
