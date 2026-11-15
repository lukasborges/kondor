import signal
import sys

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from kondor.app.commandline.commandline import CommandLine, parse_command_line
from kondor.app.instance.singleinstance import SingleInstance
from kondor.app.remotecontrol import remotecontrolstartup
from kondor.app.startup.appidentity import set_up_identity
from kondor.app.startup.appstartup import (
    forwards_to_running_instance,
    open_windows,
    shut_down,
    start_browser,
)
from kondor.app.startup.environment import prepare_environment
from kondor.app.startup.messagehandler import install_message_handler
from kondor.app.startup.stagedbuild import load_staged_resources, staged_build_directory


def run_browser(app: QApplication, single_instance: SingleInstance) -> int:
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(staged_build_directory() / "qml"))
    status = app.exec() if open_windows(engine, single_instance) else 1
    shut_down(engine)
    return status


def start_application() -> QApplication | None:
    prepare_environment()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    if not load_staged_resources(staged_build_directory()):
        return None
    set_up_identity()
    return app


def startup_failure(single_instance: SingleInstance, command_line: CommandLine) -> int | None:
    status = remotecontrolstartup.check_option(command_line)
    if status is not None:
        return status
    is_running = single_instance.has_running_instance()
    return remotecontrolstartup.check_running_instance(command_line, is_running)


def launch(app: QApplication, single_instance: SingleInstance, command_line: CommandLine) -> int:
    failure = startup_failure(single_instance, command_line)
    if failure is not None:
        return failure
    if forwards_to_running_instance(single_instance, command_line):
        return 0
    failure = remotecontrolstartup.start_remote_control(command_line)
    if failure is not None:
        return failure
    start_browser(app, command_line)
    return run_browser(app, single_instance)


def main() -> int:
    install_message_handler()
    app = start_application()
    if app is None:
        return 1
    return launch(app, SingleInstance(), parse_command_line(app))


if __name__ == "__main__":
    sys.exit(main())
