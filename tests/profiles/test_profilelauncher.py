import sys

import pytest

from kondor.profiles import profilelauncher
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.profilelauncher import open_profile_window, profile_launch_command
from kondor.profiles.registry.profileregistry import ProfileRegistry


def test_launch_command_runs_the_module_for_the_profile() -> None:
    program, arguments = profile_launch_command("ab12cd34")

    assert program == sys.executable
    assert arguments == ["-P", "-m", "kondor", "--profile", "ab12cd34"]


def test_launch_command_keeps_the_rest_of_the_command_line() -> None:
    _, arguments = profile_launch_command("ab12cd34", ["--private", "kde.org"])

    assert arguments[-2:] == ["--private", "kde.org"]


def test_active_profile_counts_as_running() -> None:
    assert profilelauncher.is_running(ActiveProfile.id())


def test_other_profile_without_a_socket_is_not_running() -> None:
    assert not profilelauncher.is_running("ffffffff")


def test_unknown_profile_opens_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(profilelauncher, "start_process", started.append)

    open_profile_window("ffffffff")

    assert started == []


def test_stopped_profile_is_started_as_a_process(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(profilelauncher, "start_process", started.append)
    work = ProfileRegistry().add("Work", "flag")

    open_profile_window(work.id)

    assert started == [work.id]


def test_running_profile_gets_a_forwarded_new_window(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[str] = []
    monkeypatch.setattr(profilelauncher, "start_process", started.append)
    monkeypatch.setattr(profilelauncher, "forward_new_window", lambda profile_id: True)
    work = ProfileRegistry().add("Work", "flag")

    open_profile_window(work.id)

    assert started == []
