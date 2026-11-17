import sys
from dataclasses import dataclass

from PySide6.QtCore import QCommandLineOption, QCommandLineParser

from kondor.profiles.registry.profileregistry import ProfileRegistry
from kondor.profiles.userprofile import ASK_EVERY_TIME, DEFAULT_ID

INVALID_ARGUMENT_STATUS = 2


@dataclass(frozen=True)
class McpOptions:
    profile: str | None


def parse(arguments: list[str]) -> McpOptions | None:
    parser = QCommandLineParser()
    parser.addOption(QCommandLineOption(["mcp"], "serve MCP"))
    parser.addOption(QCommandLineOption(["profile"], "profile name", "name"))
    if not parser.parse(["kondor", *arguments]) or parser.positionalArguments():
        sys.stderr.write("Kondor: --mcp only accepts --profile <name>\n")
        return None
    return McpOptions(parser.value("profile") if parser.isSet("profile") else None)


def unattended_profile_id(registry: ProfileRegistry) -> str:
    if len(registry.profiles()) == 1:
        return DEFAULT_ID
    startup = registry.startup_profile_id()
    return registry.last_used_id() if startup == ASK_EVERY_TIME else startup


def profile_id_for(name: str | None) -> str | None:
    registry = ProfileRegistry()
    if name is None:
        return unattended_profile_id(registry)
    found = registry.find(name)
    if found is None:
        sys.stderr.write(f'Kondor: no profile named "{name}"\n')
        return None
    return found.id
