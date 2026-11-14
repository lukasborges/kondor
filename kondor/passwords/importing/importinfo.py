from PySide6.QtCore import QUrl

from kondor.passwords.csvimport.importtypes import Error, Result
from kondor.passwords.csvimport.passwordimport import format_name
from kondor.passwords.csvimport.passwordimportplan import ImportSummary

ImportInfo = dict[str, str | int]

COUNT_KEYS = (
    "newCount",
    "identicalCount",
    "conflictCount",
    "conflictSites",
    "skippedNoSite",
    "skippedNoCredentials",
    "skippedNotLogin",
)
ERROR_NAMES = {Error.NONE: "", Error.NOT_PASSWORD_EXPORT: "notPasswordExport", Error.EMPTY: "empty"}


def empty_import_info(file: QUrl) -> ImportInfo:
    info: ImportInfo = {"fileName": file.fileName(), "format": "", "error": ""}
    info.update(dict.fromkeys(COUNT_KEYS, 0))
    return info


def import_failure(file: QUrl, error: str) -> ImportInfo:
    return {**empty_import_info(file), "error": error}


def import_error_name(error: Error) -> str:
    return ERROR_NAMES[error]


def summary_counts(summary: ImportSummary) -> ImportInfo:
    return {
        "newCount": summary.new_count,
        "identicalCount": summary.identical_count,
        "conflictCount": summary.conflict_count,
        "conflictSites": summary.conflict_sites,
    }


def skipped_counts(parsed: Result) -> ImportInfo:
    return {
        "skippedNoSite": parsed.skipped_no_site,
        "skippedNoCredentials": parsed.skipped_no_credentials,
        "skippedNotLogin": parsed.skipped_not_login,
    }


def import_result(file: QUrl, parsed: Result, summary: ImportSummary) -> ImportInfo:
    info = {**empty_import_info(file), "format": format_name(parsed.format)}
    return {**info, **summary_counts(summary), **skipped_counts(parsed)}
