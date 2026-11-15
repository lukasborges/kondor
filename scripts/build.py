#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from staging.dictionaries import DEFAULT_LANGUAGES  # noqa: E402
from staging.install import install  # noqa: E402
from staging.qmlmodule import DuplicateBaseNameError  # noqa: E402
from staging.stage import stage  # noqa: E402
from staging.tools import MissingToolError  # noqa: E402

REPOSITORY = Path(__file__).resolve().parent.parent


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage the QML module and resources")
    parser.add_argument("--out", type=Path, default=REPOSITORY / "build" / "python")
    parser.add_argument("--install", type=Path, metavar="PREFIX")
    parser.add_argument("--spellcheck-languages", default=",".join(DEFAULT_LANGUAGES))
    return parser.parse_args()


def build(arguments: argparse.Namespace) -> None:
    out_dir = arguments.out.resolve()
    stage(REPOSITORY, out_dir, tuple(arguments.spellcheck_languages.split(",")))
    if arguments.install:
        install(REPOSITORY, out_dir, arguments.install.resolve())


def main() -> int:
    try:
        build(parse_arguments())
    except (MissingToolError, DuplicateBaseNameError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
