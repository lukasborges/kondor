import pytest
from PySide6.QtCore import QUrl

from kondor.app.commandline.commandline import CommandLine
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.startup import profilechoice
from kondor.profiles.startup.profilechoice import select_profile
from kondor.profiles.userprofile import ASK_EVERY_TIME, DEFAULT_ID


class RecordingChooser:
    def __init__(self, picked: str | None) -> None:
        self.picked = picked
        self.was_shown = False

    def __call__(self) -> str | None:
        self.was_shown = True
        return self.picked


@pytest.fixture
def launched(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, list[str]]]:
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(profilechoice, "start_process", lambda *args: calls.append(args))
    return calls


def add_work() -> str:
    return ProfileRegistry().add("Work", "flag").id


def test_option_selects_a_profile_by_name_without_regard_to_case() -> None:
    work = add_work()
    chooser = RecordingChooser(None)

    assert select_profile(CommandLine(profile="WORK"), chooser, []) is None
    assert ActiveProfile.id() == work
    assert not chooser.was_shown


def test_option_selects_a_profile_by_id() -> None:
    work = add_work()

    assert select_profile(CommandLine(profile=work), RecordingChooser(None), []) is None
    assert ActiveProfile.id() == work


def test_unknown_option_value_reports_and_fails(capsys: pytest.CaptureFixture[str]) -> None:
    add_work()

    assert select_profile(CommandLine(profile="nobody"), RecordingChooser(None), []) == 1
    assert capsys.readouterr().err == 'Kondor: no profile named "nobody"\n'


def test_single_profile_is_used_without_asking() -> None:
    ProfileRegistry().set_startup_profile_id(ASK_EVERY_TIME)
    chooser = RecordingChooser(None)

    assert select_profile(CommandLine(), chooser, []) is None
    assert ActiveProfile.id() == DEFAULT_ID
    assert not chooser.was_shown


def test_startup_profile_id_is_used() -> None:
    work = add_work()
    ProfileRegistry().set_startup_profile_id(work)

    assert select_profile(CommandLine(), RecordingChooser(None), []) is None
    assert ActiveProfile.id() == work


def test_removed_startup_profile_counts_as_default() -> None:
    work = add_work()
    registry = ProfileRegistry()
    registry.add("Other", "globe")
    registry.set_startup_profile_id(work)
    registry.remove(work)

    assert select_profile(CommandLine(), RecordingChooser(None), []) is None
    assert ActiveProfile.id() == DEFAULT_ID


def test_links_go_to_the_last_used_profile_without_asking() -> None:
    work = add_work()
    registry = ProfileRegistry()
    registry.set_startup_profile_id(ASK_EVERY_TIME)
    registry.set_last_used_id(work)
    chooser = RecordingChooser(None)
    command_line = CommandLine(urls=[QUrl("https://kde.org")])

    assert select_profile(command_line, chooser, []) is None
    assert ActiveProfile.id() == work
    assert not chooser.was_shown


def test_ask_every_time_starts_the_picked_profile_and_quits(
    launched: list[tuple[str, list[str]]],
) -> None:
    work = add_work()
    ProfileRegistry().set_startup_profile_id(ASK_EVERY_TIME)

    assert select_profile(CommandLine(), RecordingChooser(work), ["--private"]) == 0
    assert launched == [(work, ["--private"])]
    assert ActiveProfile.id() == DEFAULT_ID


def test_closing_the_chooser_starts_nothing(launched: list[tuple[str, list[str]]]) -> None:
    add_work()
    ProfileRegistry().set_startup_profile_id(ASK_EVERY_TIME)

    assert select_profile(CommandLine(), RecordingChooser(None), []) == 0
    assert launched == []
