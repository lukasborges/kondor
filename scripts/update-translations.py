#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
SOURCE_PATTERNS = (("kondor", "*.py"), ("qml", "*.qml"), ("qml", "*.js"))


def source_files() -> list[str]:
    found = [
        path for folder, pattern in SOURCE_PATTERNS for path in (REPOSITORY / folder).rglob(pattern)
    ]
    return sorted(str(path.relative_to(REPOSITORY)) for path in found)


def translation_files() -> list[str]:
    return sorted(
        str(path.relative_to(REPOSITORY)) for path in (REPOSITORY / "i18n").glob("kondor_*.ts")
    )


def main() -> int:
    command = [
        "pyside6-lupdate",
        "-no-obsolete",
        "-locations",
        "none",
        *source_files(),
        "-ts",
        *translation_files(),
    ]
    return subprocess.run(command, cwd=REPOSITORY, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
