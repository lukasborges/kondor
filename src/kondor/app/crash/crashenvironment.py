import os
import platform

from kondor.app.aboutinfo import AboutInfo
from kondor.app.remotecontrol import mcpcommand
from kondor.app.remotecontrol.remotecontrol import RemoteControl


def application_lines() -> list[str]:
    about = AboutInfo.instance()
    remote = "on" if RemoteControl.instance().is_active() else "off"
    return [
        f"Kondor: {about.application_version()} ({mcpcommand.install_type(os.environ)})",
        f"Qt: {about.qt_runtime_version()}",
        f"Chromium: {about.chromium_version()}",
        f"Remote control: {remote}",
    ]


def system_lines() -> list[str]:
    about = AboutInfo.instance()
    return [
        f"Python: {platform.python_version()}",
        f"Windowing system: {about.windowing_system()}",
        f"Operating system: {about.operating_system()}",
        f"Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', 'unknown')}",
    ]


def environment_lines() -> list[str]:
    return [*application_lines(), *system_lines()]
