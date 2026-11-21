import re
from dataclasses import dataclass
from urllib.parse import quote

from kondor.app.crash.crashenvironment import environment_lines

ISSUE_ADDRESS = "https://github.com/lukasborges/kondor-browser/issues/new"
MAX_ADDRESS_LENGTH = 8000
CLIPBOARD_NOTE = "The crash report was copied to the clipboard. Paste it here."
FAULT_PATTERN = re.compile(r"Fatal Python error: (.+)")


@dataclass(frozen=True)
class CrashReport:
    crash: str
    actions: str
    version: str

    def signal_name(self) -> str:
        found = FAULT_PATTERN.search(self.crash)
        return found.group(1).strip() if found else "Unknown signal"

    def title(self) -> str:
        return f"Crash: {self.signal_name()} in Kondor {self.version}"

    def body(self) -> str:
        return self.body_with(self.details())

    def short_body(self) -> str:
        return self.body_with(CLIPBOARD_NOTE)

    def body_with(self, details: str) -> str:
        environment = "\n".join(environment_lines())
        return (
            f"### What were you doing?\n\n\n### Environment\n\n{environment}\n\n{details}".strip()
            + "\n"
        )

    def details(self) -> str:
        return f"### Last actions\n\n{fenced(self.actions)}\n\n### Crash\n\n{fenced(self.crash)}"

    def address_for(self, body: str) -> str:
        parameters = {"labels": "bug", "title": self.title(), "body": body}
        query = "&".join(f"{key}={quote(value, safe='')}" for key, value in parameters.items())
        return f"{ISSUE_ADDRESS}?{query}"

    def is_too_long(self) -> bool:
        return len(self.address_for(self.body())) > MAX_ADDRESS_LENGTH

    def address(self) -> str:
        return self.address_for(self.short_body() if self.is_too_long() else self.body())


def fenced(text: str) -> str:
    return f"```\n{text}\n```"
