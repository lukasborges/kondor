import re

from .resources import ResourceGroup, entries_of

BLOCK = re.compile(r"qt_add_resources\(\s*kondor\s+\"[^\"]*\"(?P<body>.*?)\n\)", re.S)
PREFIX = re.compile(r"PREFIX\s+\"([^\"]*)\"")
BASE = re.compile(r"BASE\s+\"\$\{CMAKE_SOURCE_DIR\}/([^\"]*)\"")
FILES = re.compile(r"FILES\s+(.*)", re.S)


def parse_group(body: str) -> ResourceGroup:
    prefix = PREFIX.search(body)
    base = BASE.search(body)
    files = FILES.search(body)
    assert prefix and files
    base_directory = base.group(1) if base else ""
    return ResourceGroup(prefix.group(1), base_directory, tuple(files.group(1).split()))


def cmake_resource_entries(cmake_text: str) -> list[tuple[str, str]]:
    groups = [parse_group(match.group("body")) for match in BLOCK.finditer(cmake_text)]
    return sorted(entry for group in groups for entry in entries_of(group))
