import os

DEBUGGING_VARIABLE = "QTWEBENGINE_REMOTE_DEBUGGING"
FLAGS_VARIABLE = "QTWEBENGINE_CHROMIUM_FLAGS"
LOCAL_HOST = "127.0.0.1"


def local_address(port: int) -> str:
    return f"{LOCAL_HOST}:{port}"


def allow_origins_flag(port: int) -> str:
    return f"--remote-allow-origins=http://{local_address(port)}"


def enable_debugging(port: int) -> None:
    os.environ[DEBUGGING_VARIABLE] = local_address(port)
    flags = os.environ.get(FLAGS_VARIABLE, "")
    os.environ[FLAGS_VARIABLE] = f"{flags} {allow_origins_flag(port)}".strip()


def disable_debugging() -> None:
    os.environ.pop(DEBUGGING_VARIABLE, None)
