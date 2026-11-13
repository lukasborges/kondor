import os
from typing import Iterable, List

from .files import ROOTS

MAX_FOLDER_FILES = 10
MAX_FOLDER_DEPTH = 2
IGNORED_FOLDER = "tests/data"


def is_in_scope(folder: str) -> bool:
    top = folder.split("/")[0]
    return top in ROOTS and folder != IGNORED_FOLDER and not folder.startswith(IGNORED_FOLDER + "/")


def folder_depth(folder: str) -> int:
    return max(len(folder.split("/")) - 2, 0)


def all_folders(root: str) -> List[str]:
    found = []
    for top in ROOTS:
        for directory, _, _ in os.walk(os.path.join(root, top)):
            found.append(os.path.relpath(directory, root))
    return sorted(folder for folder in found if is_in_scope(folder))


def folders_of(paths: Iterable[str]) -> List[str]:
    return sorted({os.path.dirname(path) for path in paths if is_in_scope(os.path.dirname(path))})


def count_files(root: str, folder: str) -> int:
    entries = os.listdir(os.path.join(root, folder))
    return sum(1 for name in entries if os.path.isfile(os.path.join(root, folder, name)))


def folder_problems(root: str, folders: Iterable[str]) -> List[str]:
    problems = []
    for folder in folders:
        if not os.path.isdir(os.path.join(root, folder)):
            continue
        problems += describe_folder(root, folder)
    return problems


def describe_folder(root: str, folder: str) -> List[str]:
    depth = folder_depth(folder)
    files = count_files(root, folder)
    checks = (("folder files", files, MAX_FOLDER_FILES), ("folder depth", depth, MAX_FOLDER_DEPTH))
    return ["%s/: %s: %d > %d" % (folder, rule, value, limit) for rule, value, limit in checks if value > limit]
