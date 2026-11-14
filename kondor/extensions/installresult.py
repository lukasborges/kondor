from dataclasses import dataclass


@dataclass
class InstallResult:
    is_installed: bool = False
    needs_review: bool = False
    error: str = ""

    def is_refused(self) -> bool:
        return bool(self.error)
