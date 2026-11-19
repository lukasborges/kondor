from collections.abc import Iterable

from kondor.translate.catalog.records import (
    BERGAMOT_MAJOR_VERSION,
    MODEL_MAJOR_VERSION_MAX,
    MODEL_MAJOR_VERSION_MIN,
    FileRecord,
    ModelRecord,
    parse_engine,
    parse_model,
)

Pair = tuple[str, str]
PairFiles = dict[str, FileRecord]
REQUIRED_FILES = ("model", "lex")


def select_engine(raw_records: Iterable[dict[str, object]]) -> FileRecord | None:
    engines = [file for raw in raw_records if (file := parse_engine(raw)) is not None]
    matching = [file for file in engines if file.version[0] == BERGAMOT_MAJOR_VERSION]
    return max(matching, key=lambda file: file.version, default=None)


def is_supported_model(record: ModelRecord) -> bool:
    return MODEL_MAJOR_VERSION_MIN <= record.file.version[0] <= MODEL_MAJOR_VERSION_MAX


def is_newer(candidate: FileRecord, current: FileRecord | None) -> bool:
    return current is None or candidate.version > current.version


def has_vocabulary(files: PairFiles) -> bool:
    return "vocab" in files or ("srcvocab" in files and "trgvocab" in files)


def is_complete(files: PairFiles) -> bool:
    return all(kind in files for kind in REQUIRED_FILES) and has_vocabulary(files)


def newest_files(records: Iterable[ModelRecord]) -> dict[Pair, PairFiles]:
    pairs: dict[Pair, PairFiles] = {}
    for record in records:
        files = pairs.setdefault((record.source, record.target), {})
        if is_newer(record.file, files.get(record.file_type)):
            files[record.file_type] = record.file
    return pairs


def select_models(raw_records: Iterable[dict[str, object]]) -> dict[Pair, PairFiles]:
    parsed = (parse_model(raw) for raw in raw_records)
    supported = [record for record in parsed if record is not None and is_supported_model(record)]
    return {pair: files for pair, files in newest_files(supported).items() if is_complete(files)}
