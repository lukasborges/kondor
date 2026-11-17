import shutil
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.registry.profileregistry import ProfileRegistry

FindOnPath = Callable[[str], str | None]


def is_this_installation(program: str | None, python: str) -> bool:
    if program is None:
        return False
    return Path(program).resolve().parent == Path(python).parent


def program_words(
    environment: Mapping[str, str], find_on_path: FindOnPath, python: str
) -> list[str]:
    if environment.get("FLATPAK_ID"):
        return ["flatpak", "run", environment["FLATPAK_ID"]]
    return start_words(environment, find_on_path, python)


def start_words(
    environment: Mapping[str, str], find_on_path: FindOnPath, python: str
) -> list[str]:
    if environment.get("FLATPAK_ID"):
        return ["kondor"]
    if environment.get("APPIMAGE"):
        return [environment["APPIMAGE"]]
    if is_this_installation(find_on_path("kondor"), python):
        return ["kondor"]
    return [python, "-m", "kondor"]


def profile_words(profile_name: str | None) -> list[str]:
    return [] if profile_name is None else ["--profile", profile_name]


def quoted(word: str) -> str:
    return f'"{word}"' if " " in word else word


def command_text(words: list[str]) -> str:
    return " ".join(quoted(word) for word in words)


def active_profile_name() -> str | None:
    if ActiveProfile.is_default():
        return None
    found = ProfileRegistry().find(ActiveProfile.id())
    return None if found is None else found.name


def launch_words(environment: Mapping[str, str]) -> list[str]:
    words = start_words(environment, shutil.which, sys.executable)
    return [*words, *profile_words(active_profile_name())]


def mcp_words(environment: Mapping[str, str]) -> list[str]:
    words = program_words(environment, shutil.which, sys.executable)
    return [*words, *profile_words(active_profile_name()), "--mcp"]
