import pytest
from PySide6.QtCore import QUrl

from kondor.app.commandline.commandline import CommandLine, parse_arguments, resolve_urls
from kondor.core.settings.settings import Settings

pytestmark = pytest.mark.usefixtures("qapp")


def test_flags_and_resolved_url() -> None:
    parsed = parse_arguments(["kondor", "--private", "--new-window", "kde.org"])

    assert parsed.is_private
    assert parsed.new_window
    assert not parsed.new_instance
    assert parsed.arguments == ["kde.org"]
    assert parsed.urls == []


def test_urls_are_resolved_on_request() -> None:
    parsed = parse_arguments(["kondor", "kde.org"])

    resolve_urls(parsed)

    assert parsed.urls == [QUrl("https://kde.org")]


def test_parsing_does_not_build_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Settings, "_instance", None)

    parse_arguments(["kondor", "kde.org"])

    assert Settings._instance is None


def test_load_extension_values_keep_their_order() -> None:
    arguments = ["kondor", "--load-extension", "/one", "--load-extension", "/two"]

    assert parse_arguments(arguments).extension_directories == ["/one", "/two"]


def test_new_instance_alone() -> None:
    parsed = parse_arguments(["kondor", "--new-instance"])

    assert parsed == CommandLine(new_instance=True)


def test_remote_control_port_is_kept_as_typed() -> None:
    assert parse_arguments(["kondor", "--remote-control", "9333"]).remote_control_port == "9333"


def test_remote_control_is_unset_by_default() -> None:
    assert parse_arguments(["kondor"]).remote_control_port is None


def test_profile_option_keeps_the_name_as_typed() -> None:
    assert parse_arguments(["kondor", "--profile", "Work"]).profile == "Work"


def test_profile_is_unset_by_default() -> None:
    assert parse_arguments(["kondor"]).profile is None
