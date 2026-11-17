import sys
from collections.abc import Callable

from kondor.app.commandline.commandline import CommandLine
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.profilelauncher import start_process
from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.userprofile import ASK_EVERY_TIME, DEFAULT_ID

Chooser = Callable[[], str | None]


def report_unknown_profile(name: str) -> None:
    sys.stderr.write(f'Kondor: no profile named "{name}"\n')


def named_profile_id(name: str, registry: ProfileRegistry) -> str | None:
    found = registry.find(name)
    return None if found is None else found.id


def ask_which_profile(chooser: Chooser, arguments: list[str]) -> int:
    picked = chooser()
    if picked is not None:
        start_process(picked, arguments)
    return 0


def profile_without_asking(command_line: CommandLine, registry: ProfileRegistry) -> str | None:
    if len(registry.profiles()) == 1:
        return DEFAULT_ID
    startup = registry.startup_profile_id()
    if startup != ASK_EVERY_TIME:
        return startup
    return registry.last_used_id() if command_line.arguments else None


def select_named_profile(name: str, registry: ProfileRegistry) -> int | None:
    profile_id = named_profile_id(name, registry)
    if profile_id is None:
        report_unknown_profile(name)
        return 1
    ActiveProfile.select(profile_id)
    return None


def select_profile(command_line: CommandLine, chooser: Chooser, arguments: list[str]) -> int | None:
    registry = ProfileRegistry()
    if command_line.profile is not None:
        return select_named_profile(command_line.profile, registry)
    profile_id = profile_without_asking(command_line, registry)
    if profile_id is None:
        return ask_which_profile(chooser, arguments)
    ActiveProfile.select(profile_id)
    return None
