import os
import sys

from PySide6.QtCore import QProcess, qWarning

from kondor.app.instance.singleinstance import SingleInstance, server_name_for
from kondor.app.instance.singleinstancemessage import SingleInstanceMessage
from kondor.app.windows.windowmanager import WindowManager
from kondor.profiles.activeprofile import ActiveProfile
from kondor.profiles.registry.profileregistry import ProfileRegistry


def profile_launch_command(
    profile_id: str, extra_arguments: list[str] | None = None
) -> tuple[str, list[str]]:
    arguments = ["-P", "-m", "kondor", "--profile", profile_id, *(extra_arguments or [])]
    return sys.executable, arguments


def is_running(profile_id: str) -> bool:
    if profile_id == ActiveProfile.id():
        return True
    return SingleInstance(server_name_for(profile_id)).has_running_instance()


def new_window_message() -> SingleInstanceMessage:
    token = os.environ.get("XDG_ACTIVATION_TOKEN", "").encode("utf-8")
    return SingleInstanceMessage(new_window=True, activation_token=token)


def open_in_this_process() -> None:
    WindowManager.instance().newWindow()


def forward_new_window(profile_id: str) -> bool:
    return SingleInstance(server_name_for(profile_id)).send_message(new_window_message())


def start_process(profile_id: str, extra_arguments: list[str] | None = None) -> None:
    program, arguments = profile_launch_command(profile_id, extra_arguments)
    QProcess.startDetached(program, arguments)


def open_profile_window(profile_id: str) -> None:
    if ProfileRegistry().find(profile_id) is None:
        qWarning(f"Kondor: cannot open a window of the unknown profile {profile_id}")
    elif profile_id == ActiveProfile.id():
        open_in_this_process()
    elif not forward_new_window(profile_id):
        start_process(profile_id)
