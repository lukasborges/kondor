from pathlib import Path

from kondor.app.remotecontrol import mcpcommand

PYTHON = "/usr/bin/python3"


def words(environment: dict[str, str], on_path: str | None = None) -> list[str]:
    return mcpcommand.program_words(environment, lambda name: on_path, PYTHON)


def test_runs_through_flatpak() -> None:
    result = words({"FLATPAK_ID": "io.github.lukasborges.Kondor"})

    assert mcpcommand.command_text([*result, "--mcp"]) == (
        "flatpak run io.github.lukasborges.Kondor --mcp"
    )


def test_quotes_an_appimage_path_with_spaces() -> None:
    result = words({"APPIMAGE": "/home/me/My Apps/Kondor.AppImage"})

    assert mcpcommand.command_text([*result, "--mcp"]) == '"/home/me/My Apps/Kondor.AppImage" --mcp'


def test_uses_kondor_on_the_path_when_it_belongs_to_this_installation(tmp_path: Path) -> None:
    assert words({}, "/usr/bin/kondor") == ["kondor"]


def test_runs_the_module_for_a_source_checkout() -> None:
    assert words({}, None) == [PYTHON, "-m", "kondor"]


def test_ignores_a_kondor_on_the_path_from_another_installation() -> None:
    assert words({}, "/opt/other/bin/kondor") == [PYTHON, "-m", "kondor"]


def test_adds_the_profile_option() -> None:
    assert mcpcommand.profile_words("Work") == ["--profile", "Work"]
    assert mcpcommand.profile_words(None) == []


def test_starts_the_in_sandbox_program_for_a_flatpak() -> None:
    result = mcpcommand.start_words(
        {"FLATPAK_ID": "io.github.lukasborges.Kondor"}, lambda name: None, PYTHON
    )

    assert result == ["kondor"]


def test_starts_the_appimage_itself() -> None:
    result = mcpcommand.start_words({"APPIMAGE": "/a/K.AppImage"}, lambda name: None, PYTHON)

    assert result == ["/a/K.AppImage"]
