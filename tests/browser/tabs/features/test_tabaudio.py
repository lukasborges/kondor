from pytestqt.qtbot import QtBot

from kondor.browser.tabs.features.tabaudio import TabAudio


def test_set_audible_notifies_only_on_a_change(qapp: object, qtbot: QtBot) -> None:
    audio = TabAudio()
    with qtbot.waitSignal(audio.audibleChanged, timeout=100):
        audio.setAudible(True)
    with qtbot.assertNotEmitted(audio.audibleChanged):
        audio.setAudible(True)
    assert audio.isAudible


def test_set_muted_notifies_only_on_a_change(qapp: object, qtbot: QtBot) -> None:
    audio = TabAudio()
    with qtbot.waitSignal(audio.mutedChanged, timeout=100):
        audio.setMuted(True)
    with qtbot.assertNotEmitted(audio.mutedChanged):
        audio.setMuted(True)
    assert audio.isMuted


def test_toggle_muted_only_requests(qapp: object, qtbot: QtBot) -> None:
    audio = TabAudio()
    with qtbot.waitSignal(audio.mutedToggleRequested, timeout=100):
        audio.toggleMuted()
    assert not audio.isMuted
