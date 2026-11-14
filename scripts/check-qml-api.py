#!/usr/bin/env python3
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPOSITORY))

from qmlapi.compare import compare_all  # noqa: E402
from qmlapi.headerparser import parse_header  # noqa: E402
from qmlapi.model import ClassApi  # noqa: E402
from qmlapi.pythonside import python_classes  # noqa: E402


def cpp_classes(repository: Path) -> dict[str, ClassApi]:
    classes: dict[str, ClassApi] = {}
    for header in sorted((repository / "src").rglob("*.h")):
        classes.update(parse_header(header.read_text(encoding="utf-8")))
    return classes


def main() -> int:
    cpp = cpp_classes(REPOSITORY)
    python = python_classes(REPOSITORY)
    problems = compare_all(cpp, python)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"{len(python)} classes checked, {len(cpp) - len(python)} C++ classes not ported yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
