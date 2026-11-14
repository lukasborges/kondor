from kondor.passwords.importing.importinfo import ImportInfo

COUNT_KEY = "count"
FILE_NAME_KEY = "fileName"


class ImportOutcome:
    def __init__(self) -> None:
        self._result: ImportInfo = {}
        self._is_notified = False
        self._is_page_open = False

    def record(self, written: int, file_name: str) -> None:
        self._result = {COUNT_KEY: written, FILE_NAME_KEY: file_name}
        self._is_notified = False

    def set_page_open(self, is_open: bool) -> None:
        self._is_page_open = is_open

    def take(self) -> ImportInfo:
        result, self._result = self._result, {}
        return result

    def claim_notification(self) -> ImportInfo:
        if not self._is_claimable():
            return {}
        self._is_notified = True
        return dict(self._result)

    def _is_claimable(self) -> bool:
        is_success = int(self._result.get(COUNT_KEY, 0)) >= 0
        is_pending = not self._is_notified and not self._is_page_open
        return bool(self._result) and is_pending and is_success
