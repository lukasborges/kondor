import argparse
import os
import sys
from typing import List, Optional

from . import baseline as bl
from .files import all_files, changed_files, read_source
from .folders import all_folders, folder_problems, folders_of
from .rules import Violation, check_source

DEFAULT_BASELINE = "scripts/code-quality-baseline.json"


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Code limits checker")
    parser.add_argument("--changed", metavar="REF", help="check only files that differ from REF")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--init-baseline", action="store_true")
    parser.add_argument("--root", default=os.getcwd())
    parser.add_argument("--baseline", default=None)
    return parser.parse_args(argv)


def collect_violations(root: str, paths: List[str]) -> List[Violation]:
    violations: List[Violation] = []
    for path in paths:
        violations += check_source(path, read_source(root, path))
    return violations


def baseline_path(arguments: argparse.Namespace) -> str:
    return arguments.baseline or os.path.join(arguments.root, DEFAULT_BASELINE)


def initialize(arguments: argparse.Namespace) -> int:
    target = baseline_path(arguments)
    if not bl.can_initialize(target):
        print("%s already exists: --init-baseline only creates it" % target, file=sys.stderr)
        return 1
    violations = collect_violations(arguments.root, all_files(arguments.root))
    bl.save_baseline(target, bl.build_baseline(violations))
    return 0


def update(arguments: argparse.Namespace) -> int:
    target = baseline_path(arguments)
    current = bl.load_baseline(target)
    violations = collect_violations(arguments.root, all_files(arguments.root))
    problems = [p for p in bl.find_problems(violations, current, None) if "fixed:" not in p]
    if problems:
        print("\n".join(problems + ["--update-baseline never adds entries or raises values"]))
        return 1
    bl.save_baseline(target, bl.lowered_baseline(violations, current))
    return 0


def scope_of(arguments: argparse.Namespace):
    if arguments.changed is None:
        return all_files(arguments.root), None
    paths = changed_files(arguments.root, arguments.changed)
    return paths, set(paths)


def folders_in_scope(arguments: argparse.Namespace, paths: List[str]) -> List[str]:
    return all_folders(arguments.root) if arguments.changed is None else folders_of(paths)


def check(arguments: argparse.Namespace) -> int:
    paths, scope = scope_of(arguments)
    problems = bl.find_problems(collect_violations(arguments.root, paths),
                                bl.load_baseline(baseline_path(arguments)), scope)
    problems += folder_problems(arguments.root, folders_in_scope(arguments, paths))
    print("\n".join(problems))
    return 1 if problems else 0


def run(argv: Optional[List[str]] = None) -> int:
    arguments = parse_arguments(sys.argv[1:] if argv is None else argv)
    if arguments.init_baseline:
        return initialize(arguments)
    return update(arguments) if arguments.update_baseline else check(arguments)
