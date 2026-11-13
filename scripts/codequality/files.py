import os
import subprocess
from typing import List, Set

ROOTS = ("src", "qml", "tests", "kondor", "pytests")
SUFFIXES = (".cpp", ".h", ".js", ".qml", ".py")
IGNORED_PREFIXES = ("tests/data/", "pytests/data/")


def is_checked(path: str) -> bool:
    in_scope = path.split("/")[0] in ROOTS and path.endswith(SUFFIXES)
    return in_scope and "__pycache__" not in path.split("/") and not path.startswith(IGNORED_PREFIXES)


def all_files(root: str) -> List[str]:
    found = []
    for top in ROOTS:
        for directory, _, names in os.walk(os.path.join(root, top)):
            found += [os.path.relpath(os.path.join(directory, name), root) for name in names]
    return sorted(path for path in found if is_checked(path))


def git_lines(root: str, arguments: List[str]) -> List[str]:
    result = subprocess.run(["git", "-C", root] + arguments, capture_output=True, text=True, check=True)
    return result.stdout.split()


def changed_files(root: str, ref: str) -> List[str]:
    changed = git_lines(root, ["diff", "--name-only", ref])
    untracked = git_lines(root, ["ls-files", "--others", "--exclude-standard"])
    return sorted(path for path in set(changed + untracked) if is_checked(path))


def read_source(root: str, path: str) -> str:
    full_path = os.path.join(root, path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, encoding="utf-8") as handle:
        return handle.read()

