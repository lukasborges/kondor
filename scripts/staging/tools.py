import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_HINT = "pyside6-tools"


class MissingToolError(Exception):
    pass


def find_tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise MissingToolError(f"{name} not found: install the Fedora package {PACKAGE_HINT}")
    return found


def run_tool(name: str, arguments: list[str | Path]) -> None:
    command = [find_tool(name), *map(str, arguments)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stdout + result.stderr, file=sys.stderr)
        raise SystemExit(f"{name} failed with exit code {result.returncode}")
