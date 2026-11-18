import os

_launch_environment: dict[str, str] = {}


def remember_launch_environment() -> None:
    _launch_environment.clear()
    _launch_environment.update(os.environ)


def launch_environment() -> dict[str, str]:
    return dict(_launch_environment) if _launch_environment else dict(os.environ)
