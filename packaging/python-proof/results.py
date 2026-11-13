CHECKS = ("webengine", "style", "module", "interceptor", "dbus")
TIMEOUT_SECONDS = 30


class Results:
    def __init__(self) -> None:
        self._failures: dict[str, str | None] = {}

    def record(self, name: str, failure: str | None) -> None:
        self._failures.setdefault(name, failure)

    def is_complete(self) -> bool:
        return all(name in self._failures for name in CHECKS)

    def passed(self) -> bool:
        return self.is_complete() and not any(self._failures.values())

    def lines(self) -> list[str]:
        return [self._line(name) for name in CHECKS]

    def _line(self, name: str) -> str:
        if name not in self._failures:
            return f"FAIL {name}: timeout"
        failure = self._failures[name]
        return f"PASS {name}" if failure is None else f"FAIL {name}: {failure}"

    def summary(self) -> str:
        if self.passed():
            return "PROOF OK"
        return "FAIL" if self.is_complete() else "FAIL timeout"
