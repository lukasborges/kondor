import re
from typing import NamedTuple

VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)$")
ENGINE_RECORD_NAME = "bergamot-translator"
BERGAMOT_MAJOR_VERSION = 3
MODEL_MAJOR_VERSION_MIN = 1
MODEL_MAJOR_VERSION_MAX = 2
SHA256_LENGTH = 64


class FileRecord(NamedTuple):
    name: str
    version: tuple[int, int]
    hash: str
    size: int
    location: str


class ModelRecord(NamedTuple):
    source: str
    target: str
    file_type: str
    file: FileRecord


def parse_version(text: object) -> tuple[int, int] | None:
    match = VERSION_PATTERN.match(text) if isinstance(text, str) else None
    return (int(match.group(1)), int(match.group(2))) if match else None


def is_published(raw: dict[str, object]) -> bool:
    return not raw.get("filter_expression")


def is_valid_attachment(attachment: object) -> bool:
    if not isinstance(attachment, dict):
        return False
    hash_ok = isinstance(attachment.get("hash"), str) and len(attachment["hash"]) == SHA256_LENGTH
    return hash_ok and isinstance(attachment.get("size"), int) and bool(attachment.get("location"))


def parse_file(raw: dict[str, object]) -> FileRecord | None:
    version = parse_version(raw.get("version"))
    attachment = raw.get("attachment")
    if version is None or not is_published(raw) or not is_valid_attachment(attachment):
        return None
    assert isinstance(attachment, dict)
    name = str(attachment.get("filename") or raw.get("name") or "")
    return FileRecord(name, version, attachment["hash"], attachment["size"], attachment["location"])


def parse_model(raw: dict[str, object]) -> ModelRecord | None:
    file = parse_file(raw)
    source, target, file_type = raw.get("fromLang"), raw.get("toLang"), raw.get("fileType")
    if file is None or "variant" in raw:
        return None
    if not all(isinstance(value, str) and value for value in (source, target, file_type)):
        return None
    return ModelRecord(str(source), str(target), str(file_type), file)


def parse_engine(raw: dict[str, object]) -> FileRecord | None:
    return parse_file(raw) if raw.get("name") == ENGINE_RECORD_NAME else None
