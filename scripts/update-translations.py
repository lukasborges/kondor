#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
SOURCE_PATTERNS = (("src/kondor", "*.py"), ("qml", "*.qml"), ("qml", "*.js"))


def source_files() -> list[str]:
    found = [
        path for folder, pattern in SOURCE_PATTERNS for path in (REPOSITORY / folder).rglob(pattern)
    ]
    return sorted(str(path.relative_to(REPOSITORY)) for path in found)


ENGLISH_CATALOG = "i18n/kondor_en.ts"
ENGLISH_OPTIONS = ["-no-obsolete", "-pluralonly", "-target-language", "en"]


def translation_files() -> list[str]:
    found = sorted(
        str(path.relative_to(REPOSITORY)) for path in (REPOSITORY / "i18n").glob("kondor_*.ts")
    )
    return [name for name in found if name != ENGLISH_CATALOG]


def update_command(options: list[str], catalogs: list[str]) -> list[str]:
    return ["pyside6-lupdate", *options, "-locations", "none", *source_files(), "-ts", *catalogs]


def run(command: list[str]) -> int:
    return subprocess.run(command, cwd=REPOSITORY, check=False).returncode


def main() -> int:
    others = run(update_command(["-no-obsolete"], translation_files()))
    english = run(update_command(ENGLISH_OPTIONS, [ENGLISH_CATALOG]))
    return max(others, english)


if __name__ == "__main__":
    sys.exit(main())
