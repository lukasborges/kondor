from dataclasses import dataclass, field

from PySide6.QtCore import QCommandLineOption, QCommandLineParser, QCoreApplication, QUrl

from kondor.app.commandline.startupurl import startup_urls_for_arguments

EXTENSION_HELP = (
    "Load an unpacked extension (developer option). Repeatable; "
    "not forwarded to a running instance, use with --new-instance"
)
FLAGS = (
    ("private", "open URLs in a private tab"),
    ("new-window", "open the URLs in a new window of the running instance"),
    ("new-instance", "start a separate process instead of reusing the running one"),
)


@dataclass
class CommandLine:
    urls: list[QUrl] = field(default_factory=list)
    is_private: bool = False
    new_window: bool = False
    new_instance: bool = False
    extension_directories: list[str] = field(default_factory=list)


def add_flags(parser: QCommandLineParser) -> None:
    for name, description in FLAGS:
        parser.addOption(QCommandLineOption([name], description))


def add_extension_option(parser: QCommandLineParser) -> None:
    parser.addOption(QCommandLineOption(["load-extension"], EXTENSION_HELP, "dir"))


def describe(parser: QCommandLineParser) -> None:
    parser.setApplicationDescription("Kondor web browser")
    parser.addHelpOption()
    parser.addVersionOption()
    add_flags(parser)
    add_extension_option(parser)
    parser.addPositionalArgument("urls", "URLs or files to open", "[urls...]")


def read(parser: QCommandLineParser) -> CommandLine:
    return CommandLine(
        urls=startup_urls_for_arguments(parser.positionalArguments()),
        is_private=parser.isSet("private"),
        new_window=parser.isSet("new-window"),
        new_instance=parser.isSet("new-instance"),
        extension_directories=parser.values("load-extension"),
    )


def parse_arguments(arguments: list[str]) -> CommandLine:
    parser = QCommandLineParser()
    describe(parser)
    parser.process(arguments)
    return read(parser)


def parse_command_line(app: QCoreApplication) -> CommandLine:
    return parse_arguments(app.arguments())
