import sys

from PySide6.QtCore import qWarning

from kondor.app.commandline.commandline import CommandLine
from kondor.app.remotecontrol import remotecontrolenvironment, remotecontrolport
from kondor.app.remotecontrol.remotecontrol import RemoteControl
from kondor.core.settings.settings import Settings

INVALID_ARGUMENT_STATUS = 2
ALREADY_RUNNING_STATUS = 1


def print_error(message: str) -> None:
    print(f"Kondor: {message}", file=sys.stderr)


def option_port(command_line: CommandLine) -> int | None:
    text = command_line.remote_control_port
    return None if text is None else remotecontrolport.parse_port(text)


def is_option_invalid(command_line: CommandLine) -> bool:
    return command_line.remote_control_port is not None and option_port(command_line) is None


def decided_port(command_line: CommandLine) -> int | None:
    settings = Settings.instance()
    return remotecontrolport.requested_port(
        option_port(command_line),
        bool(settings.property("remoteControlEnabled")),
        int(settings.property("remoteControlPort")),
    )


def usable_port(command_line: CommandLine) -> int | None:
    port = decided_port(command_line)
    if port is None or remotecontrolport.is_port_free(port):
        return port
    print_error(f"port {port} is in use; remote control is off")
    return None


def apply_environment(port: int | None, is_requested_on_command_line: bool) -> None:
    if port is None:
        remotecontrolenvironment.disable_debugging()
    else:
        remotecontrolenvironment.enable_debugging(port)
    RemoteControl.instance().set_port(port, is_requested_on_command_line)


def check_option(command_line: CommandLine) -> int | None:
    if not is_option_invalid(command_line):
        return None
    print_error("--remote-control needs a port from 1024 to 65535")
    return INVALID_ARGUMENT_STATUS


def check_private(command_line: CommandLine) -> int | None:
    if not (command_line.is_private and RemoteControl.instance().is_active()):
        return None
    print_error("private browsing is unavailable while remote control is on")
    return INVALID_ARGUMENT_STATUS


def check_running_instance(command_line: CommandLine, is_running: bool) -> int | None:
    if command_line.remote_control_port is None or command_line.new_instance or not is_running:
        return None
    print_error("already running; quit it before starting with --remote-control")
    return ALREADY_RUNNING_STATUS


def start_remote_control(command_line: CommandLine) -> int | None:
    apply_environment(usable_port(command_line), option_port(command_line) is not None)
    return check_private(command_line)


def warn_private_refused() -> None:
    qWarning("Kondor: private browsing is unavailable while remote control is on")
