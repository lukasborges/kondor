import sys
from dataclasses import dataclass, field

from PySide6.QtCore import QCommandLineOption, QCommandLineParser, QCoreApplication, QUrl

from kondor.app.commandline.startupurl import startup_urls_for_arguments

PROGRAM_NAME = "kondor"
EXTENSION_HELP = (
    "Load an unpacked extension (developer option). Repeatable; "
    "not forwarded to a running instance, use with --new-instance"
)
PROFILE_HELP = "open a window of the profile with this name"
REMOTE_CONTROL_HELP = "turn on remote control for this run, on 127.0.0.1:<port>"
FLAGS = (
    ("private", "open URLs in a private tab"),
    ("new-window", "open the URLs in a new window of the running instance"),
    ("new-instance", "start a separate process instead of reusing the running one"),
    ("mcp", "serve the Model Context Protocol on stdin and stdout for AI agents"),
)


@dataclass
class CommandLine:
    arguments: list[str] = field(default_factory=list)
    urls: list[QUrl] = field(default_factory=list)
    is_private: bool = False
    new_window: bool = False
    new_instance: bool = False
    extension_directories: list[str] = field(default_factory=list)
    remote_control_port: str | None = None
    profile: str | None = None
    restore_session: bool = False


def add_flags(parser: QCommandLineParser) -> None:
    for name, description in FLAGS:
        parser.addOption(QCommandLineOption([name], description))


def add_extension_option(parser: QCommandLineParser) -> None:
    parser.addOption(QCommandLineOption(["load-extension"], EXTENSION_HELP, "dir"))


def add_remote_control_option(parser: QCommandLineParser) -> None:
    parser.addOption(QCommandLineOption(["remote-control"], REMOTE_CONTROL_HELP, "port"))


def add_profile_option(parser: QCommandLineParser) -> None:
    parser.addOption(QCommandLineOption(["profile"], PROFILE_HELP, "name"))


def add_restore_session_option(parser: QCommandLineParser) -> None:
    option = QCommandLineOption(["restore-session"], "restore the saved session")
    option.setFlags(QCommandLineOption.Flag.HiddenFromHelp)
    parser.addOption(option)


def describe(parser: QCommandLineParser) -> None:
    parser.setApplicationDescription("Kondor web browser")
    parser.addHelpOption()
    parser.addVersionOption()
    add_flags(parser)
    add_extension_option(parser)
    add_remote_control_option(parser)
    add_profile_option(parser)
    add_restore_session_option(parser)
    parser.addPositionalArgument("urls", "URLs or files to open", "[urls...]")


def remote_control_value(parser: QCommandLineParser) -> str | None:
    return parser.value("remote-control") if parser.isSet("remote-control") else None


def profile_value(parser: QCommandLineParser) -> str | None:
    return parser.value("profile") if parser.isSet("profile") else None


def read(parser: QCommandLineParser) -> CommandLine:
    return CommandLine(
        arguments=parser.positionalArguments(),
        is_private=parser.isSet("private"),
        new_window=parser.isSet("new-window"),
        new_instance=parser.isSet("new-instance"),
        extension_directories=parser.values("load-extension"),
        remote_control_port=remote_control_value(parser),
        profile=profile_value(parser),
        restore_session=parser.isSet("restore-session"),
    )


def help_text(parser: QCommandLineParser) -> str:
    _, _, options = parser.helpText().partition(" [options]")
    return f"Usage: {PROGRAM_NAME} [options]{options}"


def show_help_and_exit_when_requested(parser: QCommandLineParser, arguments: list[str]) -> None:
    parser.parse(arguments)
    if not parser.isSet("help"):
        return
    sys.stdout.write(help_text(parser))
    sys.exit(0)


def parse_arguments(arguments: list[str]) -> CommandLine:
    parser = QCommandLineParser()
    describe(parser)
    show_help_and_exit_when_requested(parser, arguments)
    parser.process(arguments)
    return read(parser)


def parse_command_line(app: QCoreApplication) -> CommandLine:
    return parse_arguments([PROGRAM_NAME, *app.arguments()[1:]])


def resolve_urls(command_line: CommandLine) -> None:
    command_line.urls = startup_urls_for_arguments(command_line.arguments)
