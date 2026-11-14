#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from staging.qmlmodule import DuplicateBaseNameError  # noqa: E402
from staging.stage import stage  # noqa: E402
from staging.tools import MissingToolError  # noqa: E402

REPOSITORY = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage the QML module and resources")
    parser.add_argument("--out", type=Path, default=REPOSITORY / "build" / "python")
    arguments = parser.parse_args()
    try:
        stage(REPOSITORY, arguments.out.resolve())
    except (MissingToolError, DuplicateBaseNameError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
