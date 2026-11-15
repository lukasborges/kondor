import os
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_HINT = "pyside6-tools"
LIBEXEC_DIRECTORIES = ("/usr/lib64/qt6/libexec", "/usr/lib/qt6/libexec", "/app/libexec")
QT_EQUIVALENTS = {"pyside6-rcc": "rcc", "pyside6-lrelease": "lrelease"}


class MissingToolError(Exception):
    pass


def locate(name: str) -> str | None:
    search_path = os.pathsep.join([os.environ.get("PATH", ""), *LIBEXEC_DIRECTORIES])
    return shutil.which(name, path=search_path)


def find_tool(name: str) -> str:
    for candidate in (name, QT_EQUIVALENTS.get(name)):
        found = candidate and locate(candidate)
        if found:
            return found
    raise MissingToolError(f"{name} not found: install the Fedora package {PACKAGE_HINT}")


def run_tool(name: str, arguments: list[str | Path]) -> None:
    command = [find_tool(name), *map(str, arguments)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stdout + result.stderr, file=sys.stderr)
        raise SystemExit(f"{name} failed with exit code {result.returncode}")
